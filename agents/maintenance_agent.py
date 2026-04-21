import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memory_store import load_memory, save_memory

from .memory_agent import KNOWN_PREFERENCE_CORRECTIONS, migrate_memory
from .system_state_agent import (
    SYSTEM_TARGET_LOADED_MEMORY,
    SYSTEM_TARGET_STATE,
    SystemStateCommand,
    execute_system_state_command,
)
from .text_matching import (
    matches_normalized_command,
    normalize_command_variants,
    normalize_internal_text,
)


MAINTENANCE_TARGET_VALIDATE_CONFIG = "validate_config"
MAINTENANCE_TARGET_REVIEW_MEMORY = "review_memory"
MAINTENANCE_TARGET_RELOAD_MEMORY = "reload_memory"
MAINTENANCE_TARGET_CLEAN_MEMORY = "clean_memory"
MAINTENANCE_TARGET_SHOW_LAST_LOG = "show_last_log"
MAINTENANCE_TARGET_SUMMARIZE_LAST_LOG = "summarize_last_log"
MAINTENANCE_TARGET_SUMMARIZE_LAST_TURN = "summarize_last_turn"
MAINTENANCE_TARGET_CORRECT_PREFERENCES = "correct_preferences"
MAINTENANCE_TARGET_ROUTING_PAUSE = "routing_pause"
MAINTENANCE_TARGET_ROUTING_RESUME = "routing_resume"
MAINTENANCE_TARGET_ROUTING_MARK_WATCH = "routing_mark_watch"
MAINTENANCE_TARGET_ROUTING_CLEAR_WATCH = "routing_clear_watch"
MAINTENANCE_TARGET_ROUTING_ACK_ALERT = "routing_ack_alert"
MAINTENANCE_TARGET_ROUTING_RESOLVE_ALERT = "routing_resolve_alert"

VALIDATE_CONFIG_COMMANDS = normalize_command_variants({"valida tu configuracion"})
REVIEW_MEMORY_COMMANDS = normalize_command_variants(
    {"revisa tu memoria", "revisa memoria", "revisa la memoria"}
)
RELOAD_MEMORY_COMMANDS = normalize_command_variants(
    {"recarga tu memoria", "recarga memoria", "recarga la memoria"}
)
CLEAN_MEMORY_COMMANDS = normalize_command_variants(
    {"limpia tu memoria", "limpia memoria", "limpia la memoria"}
)
SHOW_LAST_LOG_COMMANDS = normalize_command_variants(
    {
        "muestrame el ultimo log",
        "mostra el ultimo log",
        "mostrame el ultimo log",
        "muestra el ultimo log",
        "muestrame tu ultimo log",
        "mostra tu ultimo log",
        "mostrame tu ultimo log",
        "muestra tu ultimo log",
    }
)
SUMMARIZE_LAST_LOG_COMMANDS = normalize_command_variants(
    {
        "resume el ultimo log",
        "resume tu ultimo log",
    }
)
SUMMARIZE_LAST_TURN_COMMANDS = normalize_command_variants(
    {
        "resume el ultimo turno",
        "resume tu ultimo turno",
        "muestra el ultimo turno",
        "muestra tu ultimo turno",
        "muestrame el ultimo turno",
        "muestrame tu ultimo turno",
        "mostra el ultimo turno",
        "mostra tu ultimo turno",
        "mostrame el ultimo turno",
        "mostrame tu ultimo turno",
    }
)
CORRECT_PREFERENCES_COMMANDS = normalize_command_variants({"corrige preferencias guardadas"})


def get_default_routing_registry():
    from backend.app.routing_neuron.core.runtime import get_default_routing_registry as runtime_get_default_routing_registry

    return runtime_get_default_routing_registry()


def set_default_routing_registry(registry):
    from backend.app.routing_neuron.core.runtime import set_default_routing_registry as runtime_set_default_routing_registry

    return runtime_set_default_routing_registry(registry)

@dataclass(frozen=True)
class MaintenanceCommand:
    target: str
    neuron_id: str | None = None
    reason: str | None = None


ROUTING_PAUSE_RE = re.compile(
    r"^\s*pausa(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)(?:\s+por\s+(?P<reason>.+))?\s*$",
    re.IGNORECASE,
)
ROUTING_RESUME_RE = re.compile(
    r"^\s*(?:reanuda|resume)(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)(?:\s+por\s+(?P<reason>.+))?\s*$",
    re.IGNORECASE,
)
ROUTING_MARK_WATCH_RE = re.compile(
    r"^\s*marca(?:\s+en)?\s+watch(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)(?:\s+por\s+(?P<reason>.+))?\s*$",
    re.IGNORECASE,
)
ROUTING_CLEAR_WATCH_RE = re.compile(
    r"^\s*(?:quita|saca|borra)(?:\s+de)?\s+watch(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)(?:\s+por\s+(?P<reason>.+))?\s*$",
    re.IGNORECASE,
)
ROUTING_ACK_ALERT_RE = re.compile(
    r"^\s*reconoce\s+alerta(?:\s+de(?:\s+la)?)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)(?:\s+por\s+(?P<reason>.+))?\s*$",
    re.IGNORECASE,
)
ROUTING_RESOLVE_ALERT_RE = re.compile(
    r"^\s*(?:resuelve|cierra)\s+alerta(?:\s+de(?:\s+la)?)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)(?:\s+por\s+(?P<reason>.+))?\s*$",
    re.IGNORECASE,
)


def _clean_summary_text(text: str) -> str:
    compact = " ".join(str(text).split())
    compact = re.sub(r"^(?:Usuario|AURA):\s*", "", compact, flags=re.IGNORECASE)
    compact = re.sub(r"\.{4,}", "...", compact)
    compact = re.sub(r"\s+([.,;:!?])", r"\1", compact)
    return compact.strip(" .;:,!?")


def _strip_nested_exchange(text: str) -> str:
    compact = _clean_summary_text(text)
    compact = re.split(
        r"\s+(?:Tú|Yo|Usuario|AURA):\s*",
        compact,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return compact.strip(" .;:,!?")


TRUNCATION_BOUNDARY_RE = re.compile(r'[.!?;:](?:["»”\')\]]+)?')
DANGLING_SUMMARY_WORDS = {
    "a",
    "al",
    "asi",
    "aun",
    "con",
    "como",
    "de",
    "del",
    "despues",
    "donde",
    "el",
    "en",
    "es",
    "esta",
    "este",
    "esto",
    "haz",
    "la",
    "las",
    "lo",
    "los",
    "mas",
    "mi",
    "más",
    "o",
    "para",
    "pero",
    "por",
    "que",
    "si",
    "sin",
    "su",
    "sus",
    "tu",
    "un",
    "una",
    "uno",
    "unos",
    "unas",
    "y",
}


def _trim_dangling_summary_tail(text: str) -> str:
    trimmed = text.rstrip()

    while trimmed:
        parts = trimmed.split()
        if not parts:
            return ""

        last_token = parts[-1].strip(' "\'“”‘’()[]{}.,;:!?')
        normalized_last_token = normalize_internal_text(last_token)
        if normalized_last_token in DANGLING_SUMMARY_WORDS:
            trimmed = " ".join(parts[:-1]).rstrip()
            continue

        break

    return trimmed.rstrip(" .;:,!?")


def _truncate_text(text: str, limit: int = 120) -> str:
    compact = _strip_nested_exchange(text)
    if len(compact) <= limit:
        return compact

    cutoff_limit = max(limit - 3, 1)
    cutoff = compact[:cutoff_limit].rstrip()
    minimum_boundary = max(int(limit * 0.45), 24)
    boundary_candidates = [
        match.end()
        for match in TRUNCATION_BOUNDARY_RE.finditer(cutoff)
        if match.end() >= minimum_boundary
    ]

    if boundary_candidates:
        clean_boundary = _trim_dangling_summary_tail(
            cutoff[: boundary_candidates[-1]]
        )
        if clean_boundary:
            return clean_boundary + "..."

    if cutoff.count('"') % 2 == 1:
        cutoff = cutoff.rsplit('"', 1)[0].rstrip()

    if " " in cutoff:
        cutoff = cutoff.rsplit(" ", 1)[0]

    clean_cutoff = _trim_dangling_summary_tail(cutoff)
    if not clean_cutoff:
        clean_cutoff = _trim_dangling_summary_tail(compact[:cutoff_limit])

    return clean_cutoff.rstrip(" .;:,!?") + "..."


def _compose_summary(*parts: str) -> str:
    cleaned_parts = []
    for part in parts:
        cleaned_part = _clean_summary_text(part)
        if cleaned_part:
            cleaned_parts.append(cleaned_part)

    if not cleaned_parts:
        return ""

    return ". ".join(cleaned_parts) + "."


def _dedupe_items(items: list[str]) -> list[str]:
    unique_items: list[str] = []
    seen: set[str] = set()

    for item in items:
        key = item.casefold()
        if key in seen:
            continue

        seen.add(key)
        unique_items.append(item)

    return unique_items


def _build_memory_loaded_response(memory: dict[str, Any]) -> str:
    return execute_system_state_command(
        SystemStateCommand(target=SYSTEM_TARGET_LOADED_MEMORY),
        memory=memory,
        aura_version="",
        model_path="",
        llama_path="",
    )


def _build_state_response(
    memory: dict[str, Any],
    aura_version: str,
    model_path: str,
    llama_path: str,
    conversation: list[dict[str, Any]] | None = None,
    log_file: str | None = None,
) -> str:
    return execute_system_state_command(
        SystemStateCommand(target=SYSTEM_TARGET_STATE),
        memory=memory,
        aura_version=aura_version,
        model_path=model_path,
        llama_path=llama_path,
        conversation=conversation,
        log_file=log_file,
    )


def _preview_safe_memory_cleanup(memory: dict[str, Any]) -> bool:
    preview = copy.deepcopy(memory)
    return migrate_memory(preview)


def _collect_preference_corrections(memory: dict[str, Any]) -> list[tuple[str, str]]:
    corrections: list[tuple[str, str]] = []

    preferences = memory.get("preferences", [])
    if not isinstance(preferences, list):
        preferences = [preferences]

    for raw_item in preferences:
        item = str(raw_item).strip()
        if not item:
            continue

        normalized_item = normalize_internal_text(item)
        corrected_item = KNOWN_PREFERENCE_CORRECTIONS.get(normalized_item)
        if corrected_item and corrected_item != item:
            corrections.append((item, corrected_item))

    return corrections


def _apply_known_preference_corrections(memory: dict[str, Any]) -> bool:
    preferences = memory.get("preferences", [])
    if not isinstance(preferences, list):
        preferences = [preferences]

    updated_preferences: list[str] = []

    for raw_item in preferences:
        item = str(raw_item).strip()
        if not item:
            continue

        normalized_item = normalize_internal_text(item)
        corrected_item = KNOWN_PREFERENCE_CORRECTIONS.get(normalized_item, item)
        updated_preferences.append(corrected_item)

    updated_preferences = _dedupe_items(updated_preferences)
    changed = updated_preferences != memory.get("preferences", [])

    if changed:
        memory["preferences"] = updated_preferences

    return changed


def analyze_maintenance_command(user_input: str) -> MaintenanceCommand | None:
    for pattern, target, default_reason in (
        (ROUTING_PAUSE_RE, MAINTENANCE_TARGET_ROUTING_PAUSE, "revision_manual"),
        (ROUTING_RESUME_RE, MAINTENANCE_TARGET_ROUTING_RESUME, "reanudar_revision"),
        (ROUTING_MARK_WATCH_RE, MAINTENANCE_TARGET_ROUTING_MARK_WATCH, "seguimiento_manual"),
        (ROUTING_CLEAR_WATCH_RE, MAINTENANCE_TARGET_ROUTING_CLEAR_WATCH, "seguimiento_cerrado"),
        (ROUTING_ACK_ALERT_RE, MAINTENANCE_TARGET_ROUTING_ACK_ALERT, "alerta_revisada"),
        (ROUTING_RESOLVE_ALERT_RE, MAINTENANCE_TARGET_ROUTING_RESOLVE_ALERT, "alerta_resuelta"),
    ):
        match = pattern.match(user_input)
        if match:
            return MaintenanceCommand(
                target=target,
                neuron_id=match.group("neuron_id"),
                reason=(match.group("reason") or default_reason).strip(),
            )

    if matches_normalized_command(user_input, VALIDATE_CONFIG_COMMANDS):
        return MaintenanceCommand(target=MAINTENANCE_TARGET_VALIDATE_CONFIG)

    if matches_normalized_command(user_input, REVIEW_MEMORY_COMMANDS):
        return MaintenanceCommand(target=MAINTENANCE_TARGET_REVIEW_MEMORY)

    if matches_normalized_command(user_input, RELOAD_MEMORY_COMMANDS):
        return MaintenanceCommand(target=MAINTENANCE_TARGET_RELOAD_MEMORY)

    if matches_normalized_command(user_input, CLEAN_MEMORY_COMMANDS):
        return MaintenanceCommand(target=MAINTENANCE_TARGET_CLEAN_MEMORY)

    if matches_normalized_command(user_input, SHOW_LAST_LOG_COMMANDS):
        return MaintenanceCommand(target=MAINTENANCE_TARGET_SHOW_LAST_LOG)

    if matches_normalized_command(user_input, SUMMARIZE_LAST_LOG_COMMANDS):
        return MaintenanceCommand(target=MAINTENANCE_TARGET_SUMMARIZE_LAST_LOG)

    if matches_normalized_command(user_input, SUMMARIZE_LAST_TURN_COMMANDS):
        return MaintenanceCommand(target=MAINTENANCE_TARGET_SUMMARIZE_LAST_TURN)

    if matches_normalized_command(user_input, CORRECT_PREFERENCES_COMMANDS):
        return MaintenanceCommand(target=MAINTENANCE_TARGET_CORRECT_PREFERENCES)

    return None


def _review_memory(memory: dict[str, Any]) -> str:
    summary = _build_memory_loaded_response(memory)
    pending_cleanup = _preview_safe_memory_cleanup(memory)
    preference_corrections = _collect_preference_corrections(memory)

    if preference_corrections:
        return f"{summary} Detecté una corrección segura posible en preferencias."

    if pending_cleanup:
        return f"{summary} Veo ajustes simples de saneamiento pendientes."

    return f"{summary} No veo cambios seguros pendientes."


def _reload_memory(memory: dict[str, Any], memory_file: str) -> str:
    reloaded_memory = load_memory(memory_file)
    changed_by_migration = migrate_memory(reloaded_memory)

    if changed_by_migration:
        save_memory(reloaded_memory, memory_file)

    memory.clear()
    memory.update(reloaded_memory)

    return f"Recargué la memoria desde disco. {_build_memory_loaded_response(memory)}"


def _clean_memory(memory: dict[str, Any], memory_file: str) -> str:
    changed = migrate_memory(memory)

    if not changed:
        return "No encontré cambios seguros para aplicar en la memoria."

    save_memory(memory, memory_file)
    return f"Limpié la memoria. {_build_memory_loaded_response(memory)}"


def _correct_preferences(memory: dict[str, Any], memory_file: str) -> str:
    if not memory.get("preferences"):
        return "No tengo preferencias guardadas para corregir."

    changed = _apply_known_preference_corrections(memory)
    changed = migrate_memory(memory) or changed

    if not changed:
        return "No encontré correcciones seguras para aplicar en preferencias."

    save_memory(memory, memory_file)
    return (
        "Corregí las preferencias guardadas. "
        f"{_build_memory_loaded_response(memory)}"
    )


def _resolve_last_log_path(log_file: str) -> Path | None:
    current_log_path = Path(log_file)
    if current_log_path.exists():
        return current_log_path

    log_dir = current_log_path.parent
    candidates = sorted(
        log_dir.glob("session_*.json"),
        key=lambda path: path.stat().st_mtime,
    )
    if not candidates:
        return None

    return candidates[-1]


def _extract_last_exchange(messages: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    last_aura_index = -1

    for index in range(len(messages) - 1, -1, -1):
        if messages[index].get("role") == "aura":
            last_aura_index = index
            break

    if last_aura_index == -1:
        return None, None

    last_aura_content = str(messages[last_aura_index].get("content", "")).strip()

    for index in range(last_aura_index - 1, -1, -1):
        if messages[index].get("role") == "user":
            last_user_content = str(messages[index].get("content", "")).strip()
            return last_user_content or None, last_aura_content or None

    return None, last_aura_content or None


def _show_last_log(log_file: str) -> str:
    last_log_path = _resolve_last_log_path(log_file)
    if last_log_path is None:
        return "Todavía no tengo logs guardados."

    try:
        with open(last_log_path, "r", encoding="utf-8") as f:
            messages = json.load(f)
    except (OSError, json.JSONDecodeError):
        return "No pude leer el último log."

    if not isinstance(messages, list):
        return "El último log no tiene un formato válido."

    if not messages:
        return f"El último log es {last_log_path.name} y está vacío."

    last_user, last_aura = _extract_last_exchange(messages)
    message_count = len(messages)

    if last_user and last_aura:
        return _compose_summary(
            f"Último log: {last_log_path.name}, {message_count} mensajes",
            f"Tú: {_truncate_text(last_user, limit=80)}",
            f"Yo: {_truncate_text(last_aura, limit=80)}",
        )

    return _compose_summary(f"Último log: {last_log_path.name}, {message_count} mensajes")


def _summarize_last_log(log_file: str) -> str:
    last_log_path = _resolve_last_log_path(log_file)
    if last_log_path is None:
        return "Todavía no tengo logs guardados."

    try:
        with open(last_log_path, "r", encoding="utf-8") as f:
            messages = json.load(f)
    except (OSError, json.JSONDecodeError):
        return "No pude leer el último log."

    if not isinstance(messages, list):
        return "El último log no tiene un formato válido."

    if not messages:
        return f"El último log es {last_log_path.name} y está vacío."

    last_user, last_aura = _extract_last_exchange(messages)
    message_count = len(messages)

    if last_user and last_aura:
        return _compose_summary(
            f"Resumen del último log {last_log_path.name}, {message_count} mensajes",
            f"Tú: {_truncate_text(last_user, limit=70)}",
            f"Yo: {_truncate_text(last_aura, limit=70)}",
        )

    return _compose_summary(
        f"Resumen del último log {last_log_path.name}, {message_count} mensajes"
    )


def _summarize_last_turn(conversation: list[dict[str, Any]]) -> str:
    messages = conversation[:-1] if conversation and conversation[-1].get("role") == "user" else conversation
    last_user, last_aura = _extract_last_exchange(messages)

    if last_user and last_aura:
        return _compose_summary(
            "Resumen del último turno",
            f"Tú: {_truncate_text(last_user, limit=70)}",
            f"Yo: {_truncate_text(last_aura, limit=70)}",
        )

    return "Todavía no tengo un turno anterior para resumir."


def execute_maintenance_command(
    command: MaintenanceCommand,
    conversation: list[dict[str, Any]],
    memory: dict[str, Any],
    memory_file: str,
    log_file: str,
    aura_version: str,
    model_path: str,
    llama_path: str,
) -> str:
    if command.target in {
        MAINTENANCE_TARGET_ROUTING_PAUSE,
        MAINTENANCE_TARGET_ROUTING_RESUME,
        MAINTENANCE_TARGET_ROUTING_MARK_WATCH,
        MAINTENANCE_TARGET_ROUTING_CLEAR_WATCH,
        MAINTENANCE_TARGET_ROUTING_ACK_ALERT,
        MAINTENANCE_TARGET_ROUTING_RESOLVE_ALERT,
    }:
        registry = get_default_routing_registry()
        neuron_id = command.neuron_id or ""
        reason = command.reason or "sin_motivo"

        if command.target == MAINTENANCE_TARGET_ROUTING_PAUSE:
            updated_registry = registry.pause_candidate_administratively(neuron_id, reason)
            if updated_registry is registry:
                return f"No encontré la neurona {neuron_id} para pausarla."
            set_default_routing_registry(updated_registry)
            return f"Pausé la neurona {neuron_id}. Motivo: {reason}."

        if command.target == MAINTENANCE_TARGET_ROUTING_RESUME:
            updated_registry = registry.resume_candidate(neuron_id, reason)
            if updated_registry is registry:
                return f"No encontré la neurona {neuron_id} para reanudarla."
            set_default_routing_registry(updated_registry)
            return f"Reanudé la neurona {neuron_id}. Motivo: {reason}."

        if command.target == MAINTENANCE_TARGET_ROUTING_MARK_WATCH:
            updated_registry = registry.mark_watch(neuron_id, reason)
            if updated_registry is registry:
                return f"No encontré la neurona {neuron_id} para marcarla en watch."
            set_default_routing_registry(updated_registry)
            return f"Marqué en watch la neurona {neuron_id}. Motivo: {reason}."

        if command.target == MAINTENANCE_TARGET_ROUTING_CLEAR_WATCH:
            updated_registry = registry.clear_watch(neuron_id, reason)
            if updated_registry is registry:
                return f"No encontré la neurona {neuron_id} para quitarla de watch."
            set_default_routing_registry(updated_registry)
            return f"Quité de watch la neurona {neuron_id}. Motivo: {reason}."

        if command.target == MAINTENANCE_TARGET_ROUTING_ACK_ALERT:
            updated_registry = registry.acknowledge_alert(neuron_id, reason)
            if updated_registry is registry:
                return f"No encontré la neurona {neuron_id} para reconocer su alerta."
            set_default_routing_registry(updated_registry)
            return f"Reconocí la alerta de la neurona {neuron_id}. Motivo: {reason}."

        if command.target == MAINTENANCE_TARGET_ROUTING_RESOLVE_ALERT:
            updated_registry = registry.resolve_alert(neuron_id, reason)
            if updated_registry is registry:
                return f"No encontré la neurona {neuron_id} para resolver su alerta."
            set_default_routing_registry(updated_registry)
            return f"Resolví la alerta de la neurona {neuron_id}. Motivo: {reason}."

    if command.target == MAINTENANCE_TARGET_VALIDATE_CONFIG:
        return _build_state_response(
            memory,
            aura_version,
            model_path,
            llama_path,
            conversation=conversation,
            log_file=log_file,
        )

    if command.target == MAINTENANCE_TARGET_REVIEW_MEMORY:
        return _review_memory(memory)

    if command.target == MAINTENANCE_TARGET_RELOAD_MEMORY:
        return _reload_memory(memory, memory_file)

    if command.target == MAINTENANCE_TARGET_CLEAN_MEMORY:
        return _clean_memory(memory, memory_file)

    if command.target == MAINTENANCE_TARGET_SHOW_LAST_LOG:
        return _show_last_log(log_file)

    if command.target == MAINTENANCE_TARGET_SUMMARIZE_LAST_LOG:
        return _summarize_last_log(log_file)

    if command.target == MAINTENANCE_TARGET_SUMMARIZE_LAST_TURN:
        return _summarize_last_turn(conversation)

    if command.target == MAINTENANCE_TARGET_CORRECT_PREFERENCES:
        return _correct_preferences(memory, memory_file)

    return "No pude ejecutar ese mantenimiento interno."
