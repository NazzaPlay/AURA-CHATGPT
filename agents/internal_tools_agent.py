from __future__ import annotations

import copy
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from config import is_runner_runnable

from .text_matching import (
    build_normalized_command_family,
    matches_normalized_command,
    normalize_command_variants,
    normalize_internal_text,
)
from .consistency_agent import (
    CONSISTENCY_FRAME_ASSERTION,
    CONSISTENCY_FRAME_CONFIDENCE,
    CONSISTENCY_FRAME_CONTEXT_TENSION,
    CONSISTENCY_FRAME_DEPENDENCY,
    CONSISTENCY_FRAME_EVIDENCE,
    analyze_consistency_query,
    build_consistency_response as build_structured_consistency_response,
    evaluate_consistency,
)
from .feasibility_agent import (
    FEASIBILITY_FRAME_CONTRADICTION,
    FEASIBILITY_FRAME_GENERAL,
    FEASIBILITY_FRAME_LIMITS,
    FEASIBILITY_FRAME_REALISM,
    analyze_feasibility_query,
    build_feasibility_response as build_structured_feasibility_response,
    evaluate_feasibility,
    looks_like_feasibility_statement,
)

if TYPE_CHECKING:
    from .capabilities_registry import CapabilityContext, CapabilityExecution
    from .internal_actions_registry import InternalActionDefinition
    from .internal_tools_registry import InternalToolDefinition, InternalToolInvocation


TOOLS_CATALOG_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que tools internas tienes",
        "que tools internas reales tienes",
        "que herramientas internas tienes",
        "que herramientas internas reales tienes",
        "muestra tus tools internas",
        "muestrame tus tools internas",
        "mostra tus tools internas",
        "mostrame tus tools internas",
        "muestra tus herramientas internas",
        "muestrame tus herramientas internas",
        "mostra tus herramientas internas",
        "mostrame tus herramientas internas",
        "mostrame las tools disponibles",
        "muestrame las tools disponibles",
        "mostra las tools disponibles",
        "muestra las tools disponibles",
        "mostrame las herramientas disponibles",
        "muestrame las herramientas disponibles",
    }
)
TOOLS_DIAGNOSTIC_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz un diagnostico interno",
    }
)
TOOLS_GENERAL_DIAGNOSTIC_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz un diagnostico general",
    }
)
TOOLS_FULL_DIAGNOSTIC_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz un diagnostico completo",
    }
)
TOOLS_SITUATIONAL_STATUS_QUERY_COMMANDS = normalize_command_variants(
    {
        "resume tu estado actual",
        "como estas ahora",
        "cual es tu estado actual",
    }
)
TOOLS_QUICK_CHECK_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz un chequeo rapido",
    }
)
TOOLS_GENERAL_CHECK_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz un chequeo general",
    }
)
TOOLS_SYSTEM_CHECK_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz un chequeo del sistema",
    }
)
TOOLS_PRIORITY_NOW_QUERY_COMMANDS = normalize_command_variants(
    {
        "que es lo mas importante ahora",
    }
)
TOOLS_DOMINANT_LIMITATION_QUERY_COMMANDS = normalize_command_variants(
    {
        "cual es tu principal limitacion",
        "cual es tu mayor problema ahora",
    }
)
TOOLS_DOMINANT_STRENGTH_QUERY_COMMANDS = normalize_command_variants(
    {
        "cual es tu principal fortaleza",
        "cual es tu mejor capacidad ahora",
    }
)
TOOLS_WORK_READINESS_QUERY_COMMANDS = normalize_command_variants(
    {
        "como estas para trabajar",
        "estas lista para trabajar",
        "estas listo para trabajar",
        "revisa si estas lista",
        "revisa si estas listo",
        "que tan lista estas",
        "que tan listo estas",
    }
)
TOOLS_READINESS_GAP_QUERY_COMMANDS = normalize_command_variants(
    {
        "que te falta para trabajar",
    }
)
TOOLS_LIMITATIONS_OVERVIEW_QUERY_COMMANDS = normalize_command_variants(
    {
        "que limitaciones tienes ahora",
    }
)
TOOLS_MEMORY_AND_STATE_REVIEW_QUERY_COMMANDS = normalize_command_variants(
    {
        "revisa tu memoria y estado",
    }
)
TOOLS_INTERNAL_REVIEW_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz una revision interna",
        "haz una revision general",
    }
)
TOOLS_OPERATIONAL_REVIEW_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz una revision operativa",
    }
)
TOOLS_PRACTICAL_REVIEW_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz una revision practica",
    }
)
TOOLS_COMPLETE_REVIEW_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz una revision completa",
    }
)
TOOLS_CONTEXTUAL_HELP_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que puedes hacer ahora segun tu estado",
        "como puedes ayudar ahora",
        "como me puedes ayudar ahora mismo",
        "que puedes hacer en tu estado actual",
    }
)
TOOLS_STRATEGIC_FOCUS_NOW_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que conviene hacer ahora",
        "cual es tu foco recomendado",
    }
)
TOOLS_STRATEGIC_PRIORITY_NOW_QUERY_COMMANDS = build_normalized_command_family(
    {
        "en que deberiamos enfocarnos",
        "que priorizarias ahora",
        "cual seria tu prioridad",
    }
)
TOOLS_STRATEGIC_ENTRY_STEP_QUERY_COMMANDS = build_normalized_command_family(
    {
        "cual seria el siguiente paso",
        "cual es el mejor siguiente paso",
        "que deberia revisar primero",
        "si quiero avanzar ahora por donde empiezo",
    }
)
TOOLS_STRATEGIC_EXPLAINED_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que me recomiendas hacer ahora",
        "como conviene avanzar ahora",
        "cual es tu recomendacion ahora",
    }
)
TOOLS_STRATEGIC_UTILITY_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que es lo mas util ahora",
    }
)
TOOLS_STRATEGIC_FIRST_MOVE_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que harias ahora",
        "que harias primero",
        "si quiero avanzar rapido que harias",
        "cual seria tu mejor movimiento ahora",
    }
)
TOOLS_STRATEGIC_FOLLOWUP_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que harias despues",
    }
)
TOOLS_STRATEGIC_RECOVERY_PLAY_QUERY_COMMANDS = build_normalized_command_family(
    {
        "si estuvieras limitada que harias primero",
    }
)
TOOLS_STRATEGIC_EXPLOIT_PLAY_QUERY_COMMANDS = build_normalized_command_family(
    {
        "si estuvieras lista que aprovecharias",
    }
)
TOOLS_STRATEGIC_PAIRED_MOVES_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que harias primero y despues",
        "que harias ahora y que despues",
    }
)
TOOLS_STRATEGIC_MICRO_PLAN_QUERY_COMMANDS = build_normalized_command_family(
    {
        "armame un plan corto",
        "cual seria un plan breve",
        "como conviene encarar esto",
        "cual seria tu mini plan",
        "si quiero avanzar ahora como lo harias",
        "ordename los siguientes pasos",
        "cual es tu secuencia recomendada",
    }
)
TOOLS_STRATEGIC_LATER_MOVE_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que dejo para mas tarde",
    }
)

TOOLS_MODE_CATALOG = "catalog"
TOOLS_MODE_CONTEXTUAL_HELP = "contextual_help"
TOOLS_MODE_STRATEGIC_GUIDANCE = "strategic_guidance"
TOOLS_MODE_DIAGNOSTIC = "diagnostic"
TOOLS_MODE_GENERAL_DIAGNOSTIC = "general_diagnostic"
TOOLS_MODE_FULL_DIAGNOSTIC = "full_diagnostic"
TOOLS_MODE_SITUATIONAL_STATUS = "situational_status"
TOOLS_MODE_QUICK_CHECK = "quick_check"
TOOLS_MODE_GENERAL_CHECK = "general_check"
TOOLS_MODE_SYSTEM_CHECK = "system_check"
TOOLS_MODE_PRIORITY_NOW = "priority_now"
TOOLS_MODE_DOMINANT_LIMITATION = "dominant_limitation"
TOOLS_MODE_DOMINANT_STRENGTH = "dominant_strength"
TOOLS_MODE_WORK_READINESS = "work_readiness"
TOOLS_MODE_READINESS_GAP = "readiness_gap"
TOOLS_MODE_LIMITATIONS_OVERVIEW = "limitations_overview"
TOOLS_MODE_MEMORY_AND_STATE_REVIEW = "memory_state_review"
TOOLS_MODE_OPERATIONAL_REVIEW = "operational_review"
TOOLS_MODE_PRACTICAL_REVIEW = "practical_review"
TOOLS_MODE_INTERNAL_REVIEW = "internal_review"
TOOLS_MODE_COMPLETE_REVIEW = "complete_review"
TOOLS_MODE_FEASIBILITY = "feasibility_evaluation"
TOOLS_MODE_CONSISTENCY = "consistency_evaluation"

STRATEGY_QUERY_STYLE_DIRECT_FOCUS = "direct_focus"
STRATEGY_QUERY_STYLE_NEXT_STEP = "next_step"
STRATEGY_QUERY_STYLE_EXPLAINED = "explained"
STRATEGY_QUERY_STYLE_UTILITY = "utility"
STRATEGY_QUERY_STYLE_DEFAULT = STRATEGY_QUERY_STYLE_DIRECT_FOCUS

ADVICE_FRAME_CATALOG = "catalog"
ADVICE_FRAME_FOCUS_NOW = "focus_now"
ADVICE_FRAME_PRIORITY_NOW = "priority_now"
ADVICE_FRAME_EXPLAINED_NOW = "explained_now"
ADVICE_FRAME_ENTRY_STEP = "entry_step"
ADVICE_FRAME_HIGHEST_VALUE = "highest_value"
ADVICE_FRAME_HELP_NOW = "help_now"
ADVICE_FRAME_FIRST_MOVE = "first_move"
ADVICE_FRAME_FOLLOWUP_MOVE = "followup_move"
ADVICE_FRAME_PAIRED_MOVES = "paired_moves"
ADVICE_FRAME_MICRO_PLAN = "micro_plan"
ADVICE_FRAME_LATER_MOVE = "later_move"
ADVICE_FRAME_RECOVERY_PLAY = "recovery_play"
ADVICE_FRAME_EXPLOIT_PLAY = "exploit_play"
ADVICE_FRAME_FEASIBILITY = "feasibility_check"
ADVICE_FRAME_CONTRADICTION = "contradiction_check"
ADVICE_FRAME_REALISM = "realism_check"
ADVICE_FRAME_LIMITS = "limits_check"
ADVICE_FRAME_CONFIDENCE = "confidence_check"
ADVICE_FRAME_ASSERTION = "assertion_check"
ADVICE_FRAME_DEPENDENCY = "dependency_check"
ADVICE_FRAME_EVIDENCE = "evidence_check"
ADVICE_FRAME_CONTEXT_TENSION = "context_tension_check"
ADVICE_FRAME_READINESS = "readiness_status"
ADVICE_FRAME_LIMITATION = "limitation_status"
ADVICE_FRAME_STRENGTH = "strength_status"
ADVICE_FRAME_REVIEW = "review_summary"
ADVICE_FRAME_DIAGNOSTIC = "diagnostic_summary"

SITUATIONAL_PROFILE_RECOVERY = "recovery_mode"
SITUATIONAL_PROFILE_MAINTENANCE = "maintenance_mode"
SITUATIONAL_PROFILE_READINESS = "readiness_mode"
SITUATIONAL_PROFILE_EXPLOIT = "exploit_available_mode"
SITUATIONAL_PROFILE_REVIEW = "review_mode"
SITUATIONAL_PROFILE_BLOCKED = "blocked_mode"
SITUATIONAL_PROFILE_GUIDANCE = "guidance_mode"

MOMENT_PROFILE_READY_TO_ADVANCE = "ready_to_advance"
MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY = "blocked_needs_recovery"
MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST = "usable_but_review_first"
MOMENT_PROFILE_MAINTAIN_BEFORE_ADVANCING = "maintain_before_advancing"
MOMENT_PROFILE_INTERNAL_ONLY = "internal_only_mode"
MOMENT_PROFILE_EXPLOIT_NOW = "exploit_now"


@dataclass(frozen=True)
class InternalToolsQuery:
    scope: str = "all"
    mode: str = TOOLS_MODE_CATALOG
    style: str = STRATEGY_QUERY_STYLE_DEFAULT
    advice_frame: str | None = None
    forced_profile: str | None = None
    feasibility_frame: str | None = None
    consistency_frame: str | None = None


@dataclass(frozen=True)
class AdaptiveSequenceSignals:
    readiness_status: str | None = None
    priority_focus: str | None = None
    dominant_limitation: str | None = None
    dominant_strength: str | None = None
    recommendation_level: str | None = None
    contextual_mode: str | None = None
    diagnostic_scope: str | None = None
    readiness_reason: str | None = None
    suggested_next_step: str | None = None
    main_help_scope: str | None = None
    strategic_mode: str | None = None
    recommended_focus: str | None = None
    recommended_action: str | None = None
    next_step_type: str | None = None
    readiness_path: str | None = None
    limitation_severity: str | None = None
    recommendation_style: str | None = None
    recommendation_priority: str | None = None
    recommendation_basis: str | None = None
    decision_focus: str | None = None
    actionability_level: str | None = None
    advice_scope: str | None = None
    situational_profile: str | None = None
    advice_frame: str | None = None
    recommended_order: tuple[str, ...] | None = None
    blocker_type: str | None = None
    opportunity_focus: str | None = None
    recovery_strategy: str | None = None
    exploitation_path: str | None = None
    moment_profile: str | None = None
    next_move_chain: tuple[str, ...] | None = None
    move_priority: str | None = None
    move_count: int | None = None
    guidance_mode: str | None = None
    followup_trigger: str | None = None
    sequence_confidence: str | None = None
    momentum_type: str | None = None
    micro_plan: tuple[str, ...] | None = None
    plan_horizon: str | None = None
    now_step: str | None = None
    next_step: str | None = None
    later_step: str | None = None
    planning_mode: str | None = None
    sequence_depth: int | None = None
    plan_confidence: str | None = None
    followup_priority: str | None = None
    feasibility_status: str | None = None
    feasibility_reason: str | None = None
    feasibility_scope: str | None = None
    contradiction_detected: bool | None = None
    uncertainty_level: str | None = None
    realism_level: str | None = None
    conditions_required: tuple[str, ...] | None = None
    feasibility_frame: str | None = None
    viability_basis: str | None = None
    primary_constraint: str | None = None
    plausibility_mode: str | None = None
    confidence_level: str | None = None
    consistency_status: str | None = None
    consistency_reason: str | None = None
    evidence_sufficiency: str | None = None
    claim_strength: str | None = None
    ambiguity_detected: bool | None = None
    assumption_load: str | None = None
    required_evidence: tuple[str, ...] | None = None
    certainty_frame: str | None = None
    revision_trigger: str | None = None
    contextual_tension: str | None = None
    recent_context_conflict: bool | None = None
    judgment_mode: str | None = None


def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def _dedupe_items(items: list[str]) -> list[str]:
    unique_items: list[str] = []
    seen: set[str] = set()

    for item in items:
        normalized_item = item.strip()
        key = normalized_item.casefold()
        if not normalized_item or key in seen:
            continue

        seen.add(key)
        unique_items.append(normalized_item)

    return unique_items


def _pluralize(word: str, count: int) -> str:
    if count == 1:
        return f"1 {word}"

    return f"{count} {word}s"


def _clean_text(text: str) -> str:
    compact = " ".join(str(text).split())
    compact = re.sub(r"\s+([.,;:!?])", r"\1", compact)
    return compact.strip(" .;:,!?")


def _compose_sentences(*parts: str) -> str:
    cleaned_parts = [_clean_text(part) for part in parts if _clean_text(part)]
    if not cleaned_parts:
        return ""

    return ". ".join(cleaned_parts) + "."


def _strip_summary_prefix(text: str) -> str:
    cleaned = _clean_text(text)
    cleaned = re.sub(
        r"^Resumen del último turno[.:]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^Resumen del último log\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned


def _path_exists(path_value: str) -> bool:
    if not path_value:
        return False

    return Path(path_value).expanduser().exists()


def _llama_status_text(llama_path: str) -> str:
    if not _path_exists(llama_path):
        return "no disponible"

    if is_runner_runnable(llama_path):
        return "disponible"

    return "existe, pero no es ejecutable"


def _model_status_text(model_path: str) -> str:
    if _path_exists(model_path):
        return "disponible"

    return "no disponible"


def _build_memory_brief(memory: dict[str, object]) -> str:
    parts: list[str] = []

    if memory.get("name"):
        parts.append("nombre")

    if memory.get("work"):
        parts.append("trabajo")

    interests = memory.get("interests")
    if isinstance(interests, list) and interests:
        parts.append(_pluralize("gusto", len(interests)))

    preferences = memory.get("preferences")
    if isinstance(preferences, list) and preferences:
        parts.append(_pluralize("preferencia", len(preferences)))

    if not parts:
        return "memoria vacía"

    return f"memoria cargada con {_format_items(parts)}"


def _build_memory_review_hint(memory: dict[str, object]) -> str:
    from .memory_agent import KNOWN_PREFERENCE_CORRECTIONS, migrate_memory
    from .text_matching import normalize_internal_text

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
            return "veo una corrección segura posible en preferencias"

    preview = copy.deepcopy(memory)
    if migrate_memory(preview):
        return "veo ajustes seguros de saneamiento pendientes"

    return "no veo cambios seguros pendientes"


def _build_core_status_line(context: CapabilityContext) -> str:
    model_name = Path(context.model_path).name or context.model_path
    model_status = _model_status_text(context.model_path)
    llama_status = _llama_status_text(context.llama_path)

    return (
        f"AURA V{context.aura_version}; modelo {model_name} {model_status}; "
        f"llama-cli {llama_status}"
    )


def _build_overall_health(context: CapabilityContext) -> str:
    model_status = _model_status_text(context.model_path)
    llama_status = _llama_status_text(context.llama_path)

    if model_status == "disponible" and llama_status == "disponible":
        return "operativo"

    if model_status != "disponible":
        return "limitado por modelo"

    if llama_status != "disponible":
        return "limitado por llama-cli"

    return "con chequeos pendientes"


def _build_availability_brief(context: CapabilityContext) -> str:
    return _format_items(
        [
            f"modelo {_model_status_text(context.model_path)}",
            f"llama-cli {_llama_status_text(context.llama_path)}",
        ]
    )


def _resolve_readiness_status(context: CapabilityContext) -> str:
    if _model_status_text(context.model_path) != "disponible":
        return "limited_model"

    if _llama_status_text(context.llama_path) != "disponible":
        return "limited_runtime"

    if "no veo cambios seguros pendientes" not in _build_memory_review_hint(context.memory):
        return "partially_ready"

    return "ready"


def _build_readiness_status(context: CapabilityContext) -> str:
    status = _resolve_readiness_status(context)
    if status == "ready":
        return "lista para trabajar"
    if status == "partially_ready":
        return "parcialmente lista"
    if status == "limited_model":
        return "limitada por el modelo"
    if status == "limited_runtime":
        return "limitada por llama-cli"
    return "todavía con limitaciones"


def _resolve_priority_focus_key(context: CapabilityContext) -> str:
    readiness_status = _resolve_readiness_status(context)
    if readiness_status == "limited_model":
        return "model_availability"
    if readiness_status == "limited_runtime":
        return "runtime_availability"
    if readiness_status == "partially_ready":
        return "memory_sanitization"
    if _build_memory_brief(context.memory) == "memoria vacía":
        return "memory_coverage"
    return "core_readiness"


def _build_priority_focus(context: CapabilityContext) -> str:
    priority_focus = _resolve_priority_focus_key(context)
    if priority_focus == "model_availability":
        return "el modelo local es el principal bloqueo"
    if priority_focus == "runtime_availability":
        return "llama-cli es el principal bloqueo"
    if priority_focus == "memory_sanitization":
        return "hay saneamiento de memoria pendiente"
    if priority_focus == "memory_coverage":
        return "la memoria útil todavía es baja o vacía"
    return "el núcleo está listo para trabajar"


def _resolve_dominant_limitation_key(context: CapabilityContext) -> str:
    if _model_status_text(context.model_path) != "disponible":
        return "model_unavailable"

    if _llama_status_text(context.llama_path) != "disponible":
        return "runtime_unavailable"

    review_hint = _build_memory_review_hint(context.memory)
    if "no veo cambios seguros pendientes" not in review_hint:
        return "memory_needs_sanitization"

    if _build_memory_brief(context.memory) == "memoria vacía":
        return "memory_empty"

    return "core_only_scope"


def _build_dominant_limitation_text(context: CapabilityContext) -> str:
    limitation_key = _resolve_dominant_limitation_key(context)
    if limitation_key == "model_unavailable":
        return "el modelo local no está disponible"
    if limitation_key == "runtime_unavailable":
        return "llama-cli no está listo"
    if limitation_key == "memory_needs_sanitization":
        return "hay saneamiento seguro pendiente en memoria"
    if limitation_key == "memory_empty":
        return "la memoria útil todavía es baja o vacía"
    return "solo opero dentro del núcleo, sin sistema operativo ni tools externas"


def _resolve_dominant_strength_key(context: CapabilityContext) -> str:
    if (
        _model_status_text(context.model_path) == "disponible"
        and _llama_status_text(context.llama_path) == "disponible"
    ):
        return "runtime_ready"

    if _model_status_text(context.model_path) == "disponible":
        return "model_configured"

    if _build_memory_brief(context.memory) != "memoria vacía":
        return "memory_context_available"

    return "internal_tooling_available"


def _build_dominant_strength_text(context: CapabilityContext) -> str:
    strength_key = _resolve_dominant_strength_key(context)
    if strength_key == "runtime_ready":
        return "modelo local y llama-cli están disponibles"
    if strength_key == "model_configured":
        return "el modelo está configurado aunque el runtime no esté completo"
    if strength_key == "memory_context_available":
        return "tengo memoria útil cargada para trabajar"
    return "sigo teniendo tools internas del núcleo para revisar y orientar"


def _resolve_recommendation_level(context: CapabilityContext) -> str:
    readiness_status = _resolve_readiness_status(context)
    if readiness_status in {"limited_model", "limited_runtime"}:
        return "required"
    if readiness_status == "partially_ready":
        return "suggested"
    if _build_memory_brief(context.memory) == "memoria vacía":
        return "optional"
    return "low"


def _resolve_readiness_reason_key(context: CapabilityContext) -> str:
    readiness_status = _resolve_readiness_status(context)
    if readiness_status == "limited_model":
        return "model_unavailable"
    if readiness_status == "limited_runtime":
        return "runtime_unavailable"
    if readiness_status == "partially_ready":
        return "memory_sanitization_pending"
    return "core_ready"


def _resolve_main_help_scope_key(context: CapabilityContext) -> str:
    readiness_status = _resolve_readiness_status(context)
    if readiness_status == "ready":
        return "full_internal_support"
    if readiness_status == "partially_ready":
        return "core_internal_support"
    return "diagnostic_support"


def _build_main_help_scope_text(context: CapabilityContext) -> str:
    main_help_scope = _resolve_main_help_scope_key(context)
    if main_help_scope == "full_internal_support":
        return "diagnósticos, revisiones, memoria, estado interno y mantenimiento; además, respuestas con el modelo local"
    if main_help_scope == "core_internal_support":
        return "diagnósticos, memoria, estado interno y mantenimiento"
    return "diagnóstico, estado interno y mantenimiento"


def _build_strengths_brief(context: CapabilityContext) -> str:
    strengths: list[str] = []
    strengths.append(_build_dominant_strength_text(context))
    if (
        _model_status_text(context.model_path) == "disponible"
        and _llama_status_text(context.llama_path) == "disponible"
    ):
        strengths.append("diagnósticos y revisiones internas disponibles")
    if _build_memory_brief(context.memory) != "memoria vacía":
        strengths.append(_build_memory_brief(context.memory))

    return _format_items(_dedupe_items(strengths)) or "sin fortalezas internas destacables ahora"


def _build_now_can_help_with(context: CapabilityContext) -> str:
    available_help = [_build_main_help_scope_text(context), "catálogos internos del sistema"]
    return _format_items(_dedupe_items(available_help))


def _build_limitation_text(context: CapabilityContext) -> str:
    return _build_dominant_limitation_text(context)


def _build_scope_boundary_text() -> str:
    return "solo opero dentro del núcleo, sin sistema operativo ni tools externas"


def _build_surface_limitation_text(
    context: CapabilityContext,
    *,
    include_scope_boundary: bool = False,
) -> str | None:
    limitation_key = _resolve_dominant_limitation_key(context)
    limitation_text = _build_dominant_limitation_text(context)

    if limitation_key == "core_only_scope":
        return limitation_text if include_scope_boundary else None

    if include_scope_boundary:
        return f"{limitation_text}; {_build_scope_boundary_text()}"

    return limitation_text


def _build_readiness_text(context: CapabilityContext) -> str:
    readiness_status = _resolve_readiness_status(context)
    if readiness_status == "ready":
        return "sí, estoy lista para trabajar dentro del núcleo"
    if readiness_status == "partially_ready":
        return "sí, pero todavía tengo un ajuste menor pendiente dentro del núcleo"

    return "todavía no estoy completamente lista para trabajar"


def _build_next_step_hint(context: CapabilityContext) -> str:
    if _model_status_text(context.model_path) != "disponible":
        return "validar la ruta y disponibilidad del modelo local"

    if _llama_status_text(context.llama_path) != "disponible":
        return "validar la ruta y permisos de llama-cli"

    review_hint = _build_memory_review_hint(context.memory)
    if "no veo cambios seguros pendientes" not in review_hint:
        return "abrir una revisión de memoria y estado"

    if _build_memory_brief(context.memory) == "memoria vacía":
        return "abrir un chequeo general"

    return "abrir una revisión práctica"


def _resolve_query_forced_profile(context: CapabilityContext | None) -> str | None:
    if context is None or context.tools_query is None:
        return None

    return context.tools_query.forced_profile


def _resolve_query_feasibility_frame(
    context: CapabilityContext | None,
) -> str | None:
    if context is None or context.tools_query is None:
        return None

    return context.tools_query.feasibility_frame


def _resolve_query_consistency_frame(
    context: CapabilityContext | None,
) -> str | None:
    if context is None or context.tools_query is None:
        return None

    return context.tools_query.consistency_frame


def _resolve_query_advice_frame(
    sequence_name: str | None,
    context: CapabilityContext | None,
) -> str | None:
    if context is not None and context.tools_query is not None and context.tools_query.advice_frame:
        return context.tools_query.advice_frame

    if context is None:
        return None

    from .internal_sequences_registry import (
        SEQUENCE_COMPLETE_REVIEW,
        SEQUENCE_CONSISTENCY_EVALUATION,
        SEQUENCE_CONTEXTUAL_HELP,
        SEQUENCE_DOMINANT_LIMITATION,
        SEQUENCE_DOMINANT_STRENGTH,
        SEQUENCE_FEASIBILITY_EVALUATION,
        SEQUENCE_INTERNAL_REVIEW,
        SEQUENCE_LIMITATIONS_OVERVIEW,
        SEQUENCE_MEMORY_STATE_REVIEW,
        SEQUENCE_OPERATIONAL_REVIEW,
        SEQUENCE_PRACTICAL_REVIEW,
        SEQUENCE_PRIORITY_NOW,
        SEQUENCE_READINESS_GAP,
        SEQUENCE_STRATEGIC_GUIDANCE,
        SEQUENCE_SITUATIONAL_STATUS,
        SEQUENCE_WORK_READINESS,
    )

    if sequence_name == SEQUENCE_CONTEXTUAL_HELP:
        return ADVICE_FRAME_HELP_NOW
    if sequence_name == SEQUENCE_STRATEGIC_GUIDANCE:
        return ADVICE_FRAME_FOCUS_NOW
    if sequence_name == SEQUENCE_FEASIBILITY_EVALUATION:
        feasibility_frame = _resolve_query_feasibility_frame(context)
        if feasibility_frame == FEASIBILITY_FRAME_CONTRADICTION:
            return ADVICE_FRAME_CONTRADICTION
        if feasibility_frame == FEASIBILITY_FRAME_REALISM:
            return ADVICE_FRAME_REALISM
        if feasibility_frame == FEASIBILITY_FRAME_LIMITS:
            return ADVICE_FRAME_LIMITS
        return ADVICE_FRAME_FEASIBILITY
    if sequence_name == SEQUENCE_CONSISTENCY_EVALUATION:
        consistency_frame = _resolve_query_consistency_frame(context)
        if consistency_frame == CONSISTENCY_FRAME_ASSERTION:
            return ADVICE_FRAME_ASSERTION
        if consistency_frame == CONSISTENCY_FRAME_DEPENDENCY:
            return ADVICE_FRAME_DEPENDENCY
        if consistency_frame == CONSISTENCY_FRAME_EVIDENCE:
            return ADVICE_FRAME_EVIDENCE
        if consistency_frame == CONSISTENCY_FRAME_CONTEXT_TENSION:
            return ADVICE_FRAME_CONTEXT_TENSION
        return ADVICE_FRAME_CONFIDENCE
    if sequence_name in {SEQUENCE_WORK_READINESS, SEQUENCE_READINESS_GAP}:
        return ADVICE_FRAME_READINESS
    if sequence_name in {SEQUENCE_LIMITATIONS_OVERVIEW, SEQUENCE_DOMINANT_LIMITATION}:
        return ADVICE_FRAME_LIMITATION
    if sequence_name == SEQUENCE_DOMINANT_STRENGTH:
        return ADVICE_FRAME_STRENGTH
    if sequence_name in {
        SEQUENCE_MEMORY_STATE_REVIEW,
        SEQUENCE_PRACTICAL_REVIEW,
        SEQUENCE_OPERATIONAL_REVIEW,
        SEQUENCE_INTERNAL_REVIEW,
        SEQUENCE_COMPLETE_REVIEW,
    }:
        return ADVICE_FRAME_REVIEW
    if sequence_name in {SEQUENCE_PRIORITY_NOW, SEQUENCE_SITUATIONAL_STATUS}:
        return ADVICE_FRAME_PRIORITY_NOW
    return ADVICE_FRAME_DIAGNOSTIC


def _resolve_recommended_focus_key(context: CapabilityContext) -> str:
    forced_profile = _resolve_query_forced_profile(context)
    readiness_status = _resolve_readiness_status(context)
    priority_focus = _resolve_priority_focus_key(context)

    if forced_profile == SITUATIONAL_PROFILE_RECOVERY:
        if readiness_status == "limited_model":
            return "model_recovery"
        if readiness_status == "limited_runtime":
            return "runtime_recovery"
        return "recovery_scan"
    if forced_profile == SITUATIONAL_PROFILE_EXPLOIT:
        return "practical_review"
    if readiness_status == "limited_model":
        return "model_recovery"
    if readiness_status == "limited_runtime":
        return "runtime_recovery"
    if readiness_status == "partially_ready":
        return "memory_state_review"
    if priority_focus == "memory_coverage":
        return "general_check"
    return "practical_review"


def _build_recommended_focus_text(context: CapabilityContext) -> str:
    focus_key = _resolve_recommended_focus_key(context)

    if focus_key == "model_recovery":
        return "recuperar el modelo local"
    if focus_key == "runtime_recovery":
        return "recuperar llama-cli"
    if focus_key == "recovery_scan":
        return "ubicar rápido el bloqueo del runtime local"
    if focus_key == "memory_state_review":
        return "ordenar memoria y estado"
    if focus_key == "general_check":
        return "un chequeo general del núcleo"
    return "una revisión práctica"


def _resolve_recommended_action(context: CapabilityContext) -> str:
    focus_key = _resolve_recommended_focus_key(context)

    if focus_key in {"model_recovery", "runtime_recovery", "recovery_scan"}:
        return "valida tu configuracion"
    if focus_key == "memory_state_review":
        return "revisa tu memoria y estado"
    if focus_key == "general_check":
        return "haz un chequeo general"
    return "haz una revision practica"


def _resolve_recommended_order(context: CapabilityContext) -> tuple[str, ...]:
    focus_key = _resolve_recommended_focus_key(context)

    if focus_key in {"model_recovery", "runtime_recovery", "recovery_scan"}:
        return ("valida tu configuracion", "que estado tienes")
    if focus_key == "memory_state_review":
        return ("revisa tu memoria y estado", "haz una revision practica")
    if focus_key == "general_check":
        return ("haz un chequeo general", "haz una revision practica")
    return ("haz una revision practica", "haz un chequeo general")


def _resolve_next_move_chain(context: CapabilityContext) -> tuple[str, ...]:
    return _resolve_recommended_order(context)[:3]


def _resolve_later_step(context: CapabilityContext) -> str | None:
    focus_key = _resolve_recommended_focus_key(context)

    if focus_key in {"model_recovery", "runtime_recovery", "recovery_scan"}:
        return "haz una revision practica"
    if focus_key == "memory_state_review":
        return "haz un chequeo general"
    return "haz una revision interna"


def _resolve_micro_plan(context: CapabilityContext) -> tuple[str, ...]:
    steps = list(_resolve_next_move_chain(context))
    later_step = _resolve_later_step(context)

    if later_step and later_step not in steps:
        steps.append(later_step)

    return tuple(steps[:3])


def _build_actionable_next_step(context: CapabilityContext) -> str:
    recommended_order = _resolve_recommended_order(context)
    if not recommended_order:
        return ""

    if len(recommended_order) == 1:
        return f'empieza por "{recommended_order[0]}"'

    return (
        f'empieza por "{recommended_order[0]}"; '
        f'después, si hace falta, sigue con "{recommended_order[1]}"'
    )


def _resolve_next_step_type(context: CapabilityContext) -> str:
    focus_key = _resolve_recommended_focus_key(context)

    if focus_key in {"model_recovery", "runtime_recovery", "recovery_scan"}:
        return "maintenance"
    if focus_key == "general_check":
        return "diagnostic"
    return "review"


def _resolve_readiness_path(context: CapabilityContext) -> str:
    focus_key = _resolve_recommended_focus_key(context)
    readiness_status = _resolve_readiness_status(context)

    if focus_key == "recovery_scan":
        return "runtime_validation_path"
    if readiness_status == "limited_model":
        return "model_recovery_path"
    if readiness_status == "limited_runtime":
        return "runtime_recovery_path"
    if readiness_status == "partially_ready":
        return "memory_stabilization_path"
    return "core_advancement_path"


def _resolve_limitation_severity(context: CapabilityContext) -> str:
    dominant_limitation = _resolve_dominant_limitation_key(context)

    if dominant_limitation in {"model_unavailable", "runtime_unavailable"}:
        return "blocking"
    if dominant_limitation in {"memory_needs_sanitization", "memory_empty"}:
        return "moderate"
    return "low"


def _build_strategic_reason(context: CapabilityContext) -> str:
    focus_key = _resolve_recommended_focus_key(context)

    if focus_key == "model_recovery":
        return "sin el modelo local se corta la parte asistida por runtime"
    if focus_key == "runtime_recovery":
        return "sin llama-cli no puedo usar el runtime local"
    if focus_key == "recovery_scan":
        return "si el núcleo quedara limitado, conviene ubicar primero si falla el modelo o el runtime"
    if focus_key == "memory_state_review":
        return "hay saneamiento seguro pendiente y conviene ordenarlo antes de seguir"
    if focus_key == "general_check":
        return "la memoria útil todavía es baja y conviene abrir primero el panorama"
    return "el núcleo ya está utilizable y conviene capitalizarlo con un paso de trabajo claro"


def _resolve_diagnostic_scope(sequence_name: str | None) -> str | None:
    from .internal_sequences_registry import (
        SEQUENCE_COMPLETE_REVIEW,
        SEQUENCE_CONSISTENCY_EVALUATION,
        SEQUENCE_FEASIBILITY_EVALUATION,
        SEQUENCE_FULL_DIAGNOSTIC,
        SEQUENCE_GENERAL_CHECK,
        SEQUENCE_GENERAL_DIAGNOSTIC,
        SEQUENCE_OPERATIONAL_REVIEW,
        SEQUENCE_PRACTICAL_REVIEW,
        SEQUENCE_STRATEGIC_GUIDANCE,
    )

    if sequence_name is None:
        return None

    if sequence_name in {SEQUENCE_FULL_DIAGNOSTIC, SEQUENCE_COMPLETE_REVIEW}:
        return "full"
    if sequence_name in {
        SEQUENCE_GENERAL_DIAGNOSTIC,
        SEQUENCE_GENERAL_CHECK,
        SEQUENCE_OPERATIONAL_REVIEW,
        SEQUENCE_PRACTICAL_REVIEW,
        SEQUENCE_STRATEGIC_GUIDANCE,
        SEQUENCE_FEASIBILITY_EVALUATION,
        SEQUENCE_CONSISTENCY_EVALUATION,
    }:
        return "general"
    return "compact"


def _resolve_strategy_query_style(context: CapabilityContext | None) -> str:
    advice_frame = _resolve_query_advice_frame(None, context)

    if advice_frame in {
        ADVICE_FRAME_ENTRY_STEP,
        ADVICE_FRAME_FOLLOWUP_MOVE,
        ADVICE_FRAME_PAIRED_MOVES,
        ADVICE_FRAME_MICRO_PLAN,
        ADVICE_FRAME_LATER_MOVE,
    }:
        return STRATEGY_QUERY_STYLE_NEXT_STEP
    if advice_frame in {
        ADVICE_FRAME_FEASIBILITY,
        ADVICE_FRAME_CONTRADICTION,
        ADVICE_FRAME_REALISM,
        ADVICE_FRAME_LIMITS,
        ADVICE_FRAME_CONFIDENCE,
        ADVICE_FRAME_ASSERTION,
        ADVICE_FRAME_DEPENDENCY,
        ADVICE_FRAME_EVIDENCE,
        ADVICE_FRAME_CONTEXT_TENSION,
    }:
        return STRATEGY_QUERY_STYLE_EXPLAINED
    if advice_frame == ADVICE_FRAME_EXPLAINED_NOW:
        return STRATEGY_QUERY_STYLE_EXPLAINED
    if advice_frame == ADVICE_FRAME_HIGHEST_VALUE:
        return STRATEGY_QUERY_STYLE_UTILITY
    return STRATEGY_QUERY_STYLE_DIRECT_FOCUS


def _resolve_contextual_mode(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str:
    from .internal_sequences_registry import (
        SEQUENCE_COMPLETE_REVIEW,
        SEQUENCE_CONSISTENCY_EVALUATION,
        SEQUENCE_CONTEXTUAL_HELP,
        SEQUENCE_DOMINANT_LIMITATION,
        SEQUENCE_DOMINANT_STRENGTH,
        SEQUENCE_INTERNAL_REVIEW,
        SEQUENCE_LIMITATIONS_OVERVIEW,
        SEQUENCE_MEMORY_STATE_REVIEW,
        SEQUENCE_OPERATIONAL_REVIEW,
        SEQUENCE_PRACTICAL_REVIEW,
        SEQUENCE_PRIORITY_NOW,
        SEQUENCE_FEASIBILITY_EVALUATION,
        SEQUENCE_READINESS_GAP,
        SEQUENCE_STRATEGIC_GUIDANCE,
        SEQUENCE_SITUATIONAL_STATUS,
        SEQUENCE_WORK_READINESS,
    )

    readiness_status = _resolve_readiness_status(context)

    if sequence_name == SEQUENCE_CONTEXTUAL_HELP:
        return "actionable_help"
    if sequence_name == SEQUENCE_STRATEGIC_GUIDANCE:
        return "strategic_output"
    if sequence_name == SEQUENCE_FEASIBILITY_EVALUATION:
        return "feasibility_evaluation"
    if sequence_name == SEQUENCE_CONSISTENCY_EVALUATION:
        return "consistency_evaluation"
    if sequence_name in {SEQUENCE_WORK_READINESS, SEQUENCE_READINESS_GAP}:
        return "readiness"
    if sequence_name in {SEQUENCE_LIMITATIONS_OVERVIEW, SEQUENCE_DOMINANT_LIMITATION}:
        return "limitation_focus"
    if sequence_name == SEQUENCE_DOMINANT_STRENGTH:
        return "strength_focus"
    if sequence_name in {
        SEQUENCE_MEMORY_STATE_REVIEW,
        SEQUENCE_OPERATIONAL_REVIEW,
        SEQUENCE_INTERNAL_REVIEW,
        SEQUENCE_COMPLETE_REVIEW,
    }:
        return "review"
    if sequence_name == SEQUENCE_PRACTICAL_REVIEW:
        return "actionable_help"
    if readiness_status in {"limited_model", "limited_runtime"}:
        return "limitation_focus"
    if sequence_name in {SEQUENCE_SITUATIONAL_STATUS, SEQUENCE_PRIORITY_NOW}:
        if readiness_status == "ready":
            return "strength_focus"
        return "readiness"
    return "diagnostic"


def _resolve_situational_profile(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str:
    forced_profile = _resolve_query_forced_profile(context)
    if forced_profile:
        return forced_profile

    contextual_mode = _resolve_contextual_mode(sequence_name, context)
    readiness_status = _resolve_readiness_status(context)
    dominant_limitation = _resolve_dominant_limitation_key(context)

    if contextual_mode == "readiness":
        return SITUATIONAL_PROFILE_READINESS
    if contextual_mode == "review":
        return SITUATIONAL_PROFILE_REVIEW
    if contextual_mode == "actionable_help":
        return SITUATIONAL_PROFILE_GUIDANCE
    if contextual_mode == "feasibility_evaluation":
        return SITUATIONAL_PROFILE_GUIDANCE
    if contextual_mode == "strength_focus":
        return (
            SITUATIONAL_PROFILE_EXPLOIT
            if readiness_status == "ready"
            else SITUATIONAL_PROFILE_READINESS
        )
    if contextual_mode == "limitation_focus":
        if dominant_limitation in {"model_unavailable", "runtime_unavailable"}:
            return SITUATIONAL_PROFILE_BLOCKED
        if dominant_limitation in {"memory_needs_sanitization", "memory_empty"}:
            return SITUATIONAL_PROFILE_MAINTENANCE
        return SITUATIONAL_PROFILE_READINESS
    if contextual_mode == "strategic_output":
        if readiness_status in {"limited_model", "limited_runtime"}:
            return SITUATIONAL_PROFILE_RECOVERY
        if readiness_status == "partially_ready" or dominant_limitation == "memory_empty":
            return SITUATIONAL_PROFILE_MAINTENANCE
        return SITUATIONAL_PROFILE_EXPLOIT
    if readiness_status in {"limited_model", "limited_runtime"}:
        return SITUATIONAL_PROFILE_BLOCKED
    if readiness_status == "partially_ready":
        return SITUATIONAL_PROFILE_MAINTENANCE
    return SITUATIONAL_PROFILE_GUIDANCE


def _resolve_moment_profile(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    advice_frame = _resolve_query_advice_frame(sequence_name, context)
    situational_profile = _resolve_situational_profile(sequence_name, context)
    readiness_status = _resolve_readiness_status(context)
    dominant_limitation = _resolve_dominant_limitation_key(context)

    if advice_frame == ADVICE_FRAME_EXPLOIT_PLAY:
        return MOMENT_PROFILE_EXPLOIT_NOW
    if advice_frame == ADVICE_FRAME_RECOVERY_PLAY or situational_profile in {
        SITUATIONAL_PROFILE_RECOVERY,
        SITUATIONAL_PROFILE_BLOCKED,
    }:
        return MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY
    if readiness_status == "partially_ready":
        return MOMENT_PROFILE_MAINTAIN_BEFORE_ADVANCING
    if dominant_limitation == "memory_empty" or situational_profile == SITUATIONAL_PROFILE_REVIEW:
        return MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST
    if situational_profile == SITUATIONAL_PROFILE_GUIDANCE and dominant_limitation == "core_only_scope":
        return MOMENT_PROFILE_INTERNAL_ONLY
    if situational_profile == SITUATIONAL_PROFILE_EXPLOIT and advice_frame in {
        ADVICE_FRAME_ENTRY_STEP,
        ADVICE_FRAME_FIRST_MOVE,
        ADVICE_FRAME_FOLLOWUP_MOVE,
    }:
        return MOMENT_PROFILE_READY_TO_ADVANCE
    if situational_profile == SITUATIONAL_PROFILE_EXPLOIT:
        return MOMENT_PROFILE_EXPLOIT_NOW
    return MOMENT_PROFILE_READY_TO_ADVANCE


def _resolve_adaptive_mode(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str:
    contextual_mode = _resolve_contextual_mode(sequence_name, context)
    if contextual_mode == "actionable_help":
        return "guidance_adaptive"
    if contextual_mode == "strategic_output":
        return "strategy_adaptive"
    if contextual_mode == "readiness":
        return "readiness_adaptive"
    if contextual_mode == "limitation_focus":
        return "constraint_first"
    if contextual_mode == "strength_focus":
        return "strength_first"
    if contextual_mode == "review":
        return "review_adaptive"
    if sequence_name is None:
        readiness_status = _resolve_readiness_status(context)
        if readiness_status in {"limited_model", "limited_runtime"}:
            return "constraint_first"
        if readiness_status == "partially_ready":
            return "maintenance_first"
        return "ready_first"
    return "priority_adaptive"


def _resolve_strategic_mode(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str:
    situational_profile = _resolve_situational_profile(sequence_name, context)
    advice_frame = _resolve_query_advice_frame(sequence_name, context)

    if advice_frame in {
        ADVICE_FRAME_FEASIBILITY,
        ADVICE_FRAME_CONTRADICTION,
        ADVICE_FRAME_REALISM,
        ADVICE_FRAME_LIMITS,
    }:
        return "feasibility_evaluation"
    if advice_frame in {
        ADVICE_FRAME_CONFIDENCE,
        ADVICE_FRAME_ASSERTION,
        ADVICE_FRAME_DEPENDENCY,
        ADVICE_FRAME_EVIDENCE,
        ADVICE_FRAME_CONTEXT_TENSION,
    }:
        return "consistency_evaluation"
    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return "micro_plan_guidance"
    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return "paired_move_guidance"
    if advice_frame == ADVICE_FRAME_LATER_MOVE:
        return "deferred_followup"
    if advice_frame == ADVICE_FRAME_FOLLOWUP_MOVE:
        return "followup_guidance"
    if situational_profile == SITUATIONAL_PROFILE_RECOVERY:
        return "recover_then_advance"
    if situational_profile == SITUATIONAL_PROFILE_BLOCKED:
        return "blocked_assessment"
    if situational_profile == SITUATIONAL_PROFILE_MAINTENANCE:
        return "stabilize_then_advance"
    if situational_profile == SITUATIONAL_PROFILE_READINESS:
        return "readiness_assessment"
    if situational_profile == SITUATIONAL_PROFILE_REVIEW:
        return "review_guidance"
    if situational_profile == SITUATIONAL_PROFILE_GUIDANCE:
        return "guided_help"
    if advice_frame == ADVICE_FRAME_HIGHEST_VALUE:
        return "utility_first"
    if advice_frame == ADVICE_FRAME_ENTRY_STEP:
        return "stepwise_guidance"
    if advice_frame == ADVICE_FRAME_FIRST_MOVE:
        return "decisive_opening"
    if advice_frame == ADVICE_FRAME_EXPLAINED_NOW:
        return "explained_guidance"
    if advice_frame == ADVICE_FRAME_PRIORITY_NOW:
        return "priority_commitment"
    if advice_frame == ADVICE_FRAME_EXPLOIT_PLAY:
        return "exploit_available"
    return "advance_now"


def _resolve_recommendation_style(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    situational_profile = _resolve_situational_profile(sequence_name, context)
    advice_frame = _resolve_query_advice_frame(sequence_name, context)

    if advice_frame in {
        ADVICE_FRAME_FEASIBILITY,
        ADVICE_FRAME_CONTRADICTION,
        ADVICE_FRAME_REALISM,
        ADVICE_FRAME_LIMITS,
    }:
        return "feasibility_compact"
    if advice_frame in {
        ADVICE_FRAME_CONFIDENCE,
        ADVICE_FRAME_ASSERTION,
        ADVICE_FRAME_DEPENDENCY,
        ADVICE_FRAME_EVIDENCE,
        ADVICE_FRAME_CONTEXT_TENSION,
    }:
        return "consistency_compact"
    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return "micro_plan_compact"
    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return "paired_moves_compact"
    if advice_frame == ADVICE_FRAME_LATER_MOVE:
        return "later_followup_compact"
    if advice_frame == ADVICE_FRAME_FOLLOWUP_MOVE:
        return "followup_chain"
    if situational_profile == SITUATIONAL_PROFILE_RECOVERY:
        return "recovery_first"
    if situational_profile == SITUATIONAL_PROFILE_BLOCKED:
        return "blocked_compact"
    if situational_profile == SITUATIONAL_PROFILE_MAINTENANCE:
        return "maintenance_compact"
    if situational_profile == SITUATIONAL_PROFILE_READINESS:
        return "readiness_guided"
    if situational_profile == SITUATIONAL_PROFILE_REVIEW:
        return "review_guided"
    if situational_profile == SITUATIONAL_PROFILE_GUIDANCE:
        return "action_guided"
    if advice_frame == ADVICE_FRAME_PRIORITY_NOW:
        return "priority_compact"
    if advice_frame == ADVICE_FRAME_EXPLAINED_NOW:
        return "explained_compact"
    if advice_frame == ADVICE_FRAME_ENTRY_STEP:
        return "entry_step"
    if advice_frame == ADVICE_FRAME_HIGHEST_VALUE:
        return "utility_first"
    if advice_frame == ADVICE_FRAME_FIRST_MOVE:
        return "decisive_move"
    if advice_frame == ADVICE_FRAME_EXPLOIT_PLAY:
        return "exploit_first"
    return "focus_compact"


def _resolve_blocker_type(context: CapabilityContext) -> str | None:
    dominant_limitation = _resolve_dominant_limitation_key(context)
    forced_profile = _resolve_query_forced_profile(context)

    if forced_profile == SITUATIONAL_PROFILE_RECOVERY and dominant_limitation == "core_only_scope":
        return "runtime_or_model"
    if dominant_limitation == "model_unavailable":
        return "model"
    if dominant_limitation == "runtime_unavailable":
        return "runtime"
    if dominant_limitation == "memory_needs_sanitization":
        return "memory_sanitization"
    if dominant_limitation == "memory_empty":
        return "memory_coverage"
    return None


def _resolve_opportunity_focus(context: CapabilityContext) -> str | None:
    focus_key = _resolve_recommended_focus_key(context)
    strength_key = _resolve_dominant_strength_key(context)

    if focus_key == "practical_review":
        return "practical_review"
    if focus_key == "general_check":
        return "situational_scan"
    if strength_key == "runtime_ready":
        return "full_internal_support"
    if strength_key == "memory_context_available":
        return "memory_context"
    if strength_key == "model_configured":
        return "model_configured"
    return "internal_diagnostics"


def _resolve_recovery_strategy(context: CapabilityContext) -> str | None:
    focus_key = _resolve_recommended_focus_key(context)

    if focus_key == "model_recovery":
        return "restore_model"
    if focus_key == "runtime_recovery":
        return "restore_runtime"
    if focus_key == "recovery_scan":
        return "validate_local_runtime"
    if focus_key == "memory_state_review":
        return "stabilize_memory_state"
    return None


def _resolve_exploitation_path(context: CapabilityContext) -> str | None:
    focus_key = _resolve_recommended_focus_key(context)

    if focus_key == "general_check":
        return "general_check_then_practical_review"
    if focus_key == "practical_review":
        return "practical_review_then_general_check"
    if _resolve_main_help_scope_key(context) == "full_internal_support":
        return "use_internal_reviews_and_model"
    return "use_internal_diagnostics"


def _resolve_recommendation_priority(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    situational_profile = _resolve_situational_profile(sequence_name, context)
    advice_frame = _resolve_query_advice_frame(sequence_name, context)

    if advice_frame in {
        ADVICE_FRAME_FEASIBILITY,
        ADVICE_FRAME_CONTRADICTION,
        ADVICE_FRAME_REALISM,
        ADVICE_FRAME_LIMITS,
    }:
        return "feasibility_assessment"
    if advice_frame in {
        ADVICE_FRAME_CONFIDENCE,
        ADVICE_FRAME_ASSERTION,
        ADVICE_FRAME_DEPENDENCY,
        ADVICE_FRAME_EVIDENCE,
        ADVICE_FRAME_CONTEXT_TENSION,
    }:
        return "consistency_calibration"
    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return "sequenced_plan"
    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return "sequenced_entry"
    if advice_frame == ADVICE_FRAME_LATER_MOVE:
        return "optional_followup"
    if advice_frame == ADVICE_FRAME_FOLLOWUP_MOVE:
        return "sequenced_followup"
    if situational_profile in {SITUATIONAL_PROFILE_RECOVERY, SITUATIONAL_PROFILE_BLOCKED}:
        return "blocking_recovery"
    if situational_profile == SITUATIONAL_PROFILE_MAINTENANCE:
        return "stabilization"
    if advice_frame == ADVICE_FRAME_HIGHEST_VALUE:
        return "value_capture"
    if advice_frame in {ADVICE_FRAME_ENTRY_STEP, ADVICE_FRAME_FIRST_MOVE}:
        return "fast_entry"
    if advice_frame == ADVICE_FRAME_PRIORITY_NOW:
        return "single_priority"
    return "guided_execution"


def _resolve_recommendation_basis(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    advice_frame = _resolve_query_advice_frame(sequence_name, context)
    blocker_type = _resolve_blocker_type(context)
    situational_profile = _resolve_situational_profile(sequence_name, context)

    if advice_frame in {
        ADVICE_FRAME_CONFIDENCE,
        ADVICE_FRAME_ASSERTION,
        ADVICE_FRAME_DEPENDENCY,
        ADVICE_FRAME_EVIDENCE,
        ADVICE_FRAME_CONTEXT_TENSION,
    }:
        return "judgment_trace"
    if blocker_type == "model":
        return "model_availability"
    if blocker_type == "runtime":
        return "runtime_availability"
    if blocker_type == "memory_sanitization":
        return "memory_sanitization"
    if blocker_type == "memory_coverage":
        return "memory_coverage"
    if situational_profile == SITUATIONAL_PROFILE_EXPLOIT:
        return "core_readiness"
    return "situational_context"


def _resolve_decision_focus(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    advice_frame = _resolve_query_advice_frame(sequence_name, context)

    if advice_frame == ADVICE_FRAME_FEASIBILITY:
        return "feasibility"
    if advice_frame == ADVICE_FRAME_CONTRADICTION:
        return "contradiction"
    if advice_frame == ADVICE_FRAME_REALISM:
        return "realism"
    if advice_frame == ADVICE_FRAME_LIMITS:
        return "limits"
    if advice_frame == ADVICE_FRAME_CONFIDENCE:
        return "confidence"
    if advice_frame == ADVICE_FRAME_ASSERTION:
        return "assertion"
    if advice_frame == ADVICE_FRAME_DEPENDENCY:
        return "dependency"
    if advice_frame == ADVICE_FRAME_EVIDENCE:
        return "evidence"
    if advice_frame == ADVICE_FRAME_CONTEXT_TENSION:
        return "context_tension"
    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return "micro_plan"
    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return "paired_moves"
    if advice_frame == ADVICE_FRAME_LATER_MOVE:
        return "later_followup"
    if advice_frame == ADVICE_FRAME_FOLLOWUP_MOVE:
        return "followup_move"
    if advice_frame == ADVICE_FRAME_HELP_NOW:
        return "available_help"
    if advice_frame == ADVICE_FRAME_READINESS:
        return "readiness"
    if advice_frame == ADVICE_FRAME_LIMITATION:
        return "constraint"
    if advice_frame == ADVICE_FRAME_STRENGTH:
        return "capability"
    if advice_frame == ADVICE_FRAME_REVIEW:
        return "review"
    if advice_frame == ADVICE_FRAME_ENTRY_STEP:
        return "entry_step"
    if advice_frame == ADVICE_FRAME_HIGHEST_VALUE:
        return "highest_value"
    if advice_frame == ADVICE_FRAME_EXPLAINED_NOW:
        return "guided_recommendation"
    if advice_frame == ADVICE_FRAME_FIRST_MOVE:
        return "decisive_opening"
    if advice_frame == ADVICE_FRAME_RECOVERY_PLAY:
        return "recovery"
    if advice_frame == ADVICE_FRAME_EXPLOIT_PLAY:
        return "opportunity"
    if advice_frame == ADVICE_FRAME_PRIORITY_NOW:
        return "priority_focus"
    if advice_frame == ADVICE_FRAME_FOCUS_NOW:
        return "priority_focus"
    return "diagnostic"


def _resolve_actionability_level(context: CapabilityContext) -> str | None:
    readiness_status = _resolve_readiness_status(context)

    if readiness_status in {"limited_model", "limited_runtime"}:
        return "blocking"
    if readiness_status == "partially_ready":
        return "guided"
    if _build_memory_brief(context.memory) == "memoria vacía":
        return "medium"
    return "high"


def _resolve_advice_scope(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    advice_frame = _resolve_query_advice_frame(sequence_name, context)

    if advice_frame in {
        ADVICE_FRAME_FEASIBILITY,
        ADVICE_FRAME_CONTRADICTION,
        ADVICE_FRAME_REALISM,
        ADVICE_FRAME_LIMITS,
    }:
        return "feasibility_evaluation"
    if advice_frame in {
        ADVICE_FRAME_CONFIDENCE,
        ADVICE_FRAME_ASSERTION,
        ADVICE_FRAME_DEPENDENCY,
        ADVICE_FRAME_EVIDENCE,
        ADVICE_FRAME_CONTEXT_TENSION,
    }:
        return "consistency_evaluation"
    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return "micro_plan"
    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return "two_step_plan"
    if advice_frame == ADVICE_FRAME_LATER_MOVE:
        return "later_optional"
    if advice_frame == ADVICE_FRAME_FOLLOWUP_MOVE:
        return "next_move_chain"
    if advice_frame == ADVICE_FRAME_ENTRY_STEP:
        return "single_step"
    if advice_frame == ADVICE_FRAME_EXPLAINED_NOW:
        return "explained_recommendation"
    if advice_frame == ADVICE_FRAME_HIGHEST_VALUE:
        return "highest_value"
    if advice_frame == ADVICE_FRAME_FIRST_MOVE:
        return "decisive_move"
    if advice_frame == ADVICE_FRAME_RECOVERY_PLAY:
        return "recovery_strategy"
    if advice_frame == ADVICE_FRAME_EXPLOIT_PLAY:
        return "exploitation_strategy"
    if advice_frame == ADVICE_FRAME_HELP_NOW:
        return "help_translation"
    if advice_frame == ADVICE_FRAME_READINESS:
        return "readiness_guidance"
    if advice_frame == ADVICE_FRAME_REVIEW:
        return "prioritized_review"
    if advice_frame == ADVICE_FRAME_LIMITATION:
        return "constraint_guidance"
    if advice_frame == ADVICE_FRAME_STRENGTH:
        return "capability_guidance"
    if advice_frame in {ADVICE_FRAME_FOCUS_NOW, ADVICE_FRAME_PRIORITY_NOW}:
        return "focused_guidance"
    return "diagnostic_guidance"


def _resolve_guidance_mode(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    advice_frame = _resolve_query_advice_frame(sequence_name, context)
    contextual_mode = _resolve_contextual_mode(sequence_name, context)

    if advice_frame in {
        ADVICE_FRAME_FEASIBILITY,
        ADVICE_FRAME_CONTRADICTION,
        ADVICE_FRAME_REALISM,
        ADVICE_FRAME_LIMITS,
    }:
        return "feasibility_guidance"
    if advice_frame in {
        ADVICE_FRAME_CONFIDENCE,
        ADVICE_FRAME_ASSERTION,
        ADVICE_FRAME_DEPENDENCY,
        ADVICE_FRAME_EVIDENCE,
        ADVICE_FRAME_CONTEXT_TENSION,
    }:
        return "consistency_guidance"
    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return "micro_plan_guidance"
    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return "sequence_guidance"
    if advice_frame == ADVICE_FRAME_LATER_MOVE:
        return "later_guidance"
    if advice_frame == ADVICE_FRAME_FOLLOWUP_MOVE:
        return "followup_guidance"
    if advice_frame in {ADVICE_FRAME_ENTRY_STEP, ADVICE_FRAME_FIRST_MOVE}:
        return "chain_guidance"
    if contextual_mode in {"readiness", "actionable_help"}:
        return "availability_guidance"
    if contextual_mode == "review":
        return "review_guidance"
    if contextual_mode == "strategic_output":
        return "moment_aware_guidance"
    if contextual_mode == "limitation_focus":
        return "constraint_guidance"
    if contextual_mode == "strength_focus":
        return "strength_guidance"
    return "status_guidance"


def _resolve_followup_trigger(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    blocker_type = _resolve_blocker_type(context)
    moment_profile = _resolve_moment_profile(sequence_name, context)

    if blocker_type in {"model", "runtime", "runtime_or_model"}:
        return "after_recovery_validation"
    if moment_profile == MOMENT_PROFILE_MAINTAIN_BEFORE_ADVANCING:
        return "after_state_stabilization"
    if moment_profile == MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST:
        return "if_initial_scan_confirms_gap"
    if moment_profile == MOMENT_PROFILE_INTERNAL_ONLY:
        return "when_internal_scope_is_enough"
    return "if_more_panorama_needed"


def _resolve_sequence_confidence(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    del sequence_name

    if _resolve_query_forced_profile(context):
        return "medium"
    if _resolve_blocker_type(context) in {"model", "runtime"}:
        return "high"
    if _resolve_readiness_status(context) in {"ready", "partially_ready"}:
        return "high"
    return "medium"


def _resolve_momentum_type(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    moment_profile = _resolve_moment_profile(sequence_name, context)

    if moment_profile == MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY:
        return "recover"
    if moment_profile == MOMENT_PROFILE_MAINTAIN_BEFORE_ADVANCING:
        return "maintain"
    if moment_profile == MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST:
        return "review"
    if moment_profile == MOMENT_PROFILE_INTERNAL_ONLY:
        return "bounded_internal"
    if moment_profile == MOMENT_PROFILE_EXPLOIT_NOW:
        return "exploit"
    return "advance"


def _resolve_plan_horizon(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    advice_frame = _resolve_query_advice_frame(sequence_name, context)

    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return "now_next_later"
    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return "now_next"
    if advice_frame == ADVICE_FRAME_FOLLOWUP_MOVE:
        return "next"
    if advice_frame == ADVICE_FRAME_LATER_MOVE:
        return "later"
    return "now"


def _resolve_planning_mode(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    advice_frame = _resolve_query_advice_frame(sequence_name, context)

    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return "micro_plan"
    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return "two_step_plan"
    if advice_frame == ADVICE_FRAME_FOLLOWUP_MOVE:
        return "followup_only"
    if advice_frame == ADVICE_FRAME_LATER_MOVE:
        return "later_optional"
    if advice_frame in {ADVICE_FRAME_ENTRY_STEP, ADVICE_FRAME_FIRST_MOVE}:
        return "single_move"
    return "guided_now"


def _resolve_followup_priority(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    blocker_type = _resolve_blocker_type(context)
    moment_profile = _resolve_moment_profile(sequence_name, context)

    if blocker_type in {"model", "runtime", "runtime_or_model"}:
        return "required"
    if moment_profile in {
        MOMENT_PROFILE_MAINTAIN_BEFORE_ADVANCING,
        MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST,
    }:
        return "suggested"
    return "optional"


def _resolve_sequence_depth(
    sequence_name: str | None,
    context: CapabilityContext,
) -> int | None:
    advice_frame = _resolve_query_advice_frame(sequence_name, context)
    micro_plan = _resolve_micro_plan(context)

    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return len(micro_plan)
    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return min(2, len(micro_plan))
    return 1 if micro_plan else None


def _resolve_plan_confidence(
    sequence_name: str | None,
    context: CapabilityContext,
) -> str | None:
    return _resolve_sequence_confidence(sequence_name, context)


def _evaluate_feasibility_for_context(
    context: CapabilityContext,
) -> object:
    return evaluate_feasibility(
        context.user_input_raw,
        conversation=context.conversation,
        preferred_frame=_resolve_query_feasibility_frame(context),
    )


def _evaluate_consistency_for_context(
    context: CapabilityContext,
    feasibility_evaluation: object | None = None,
) -> object:
    return evaluate_consistency(
        context.user_input_raw,
        conversation=context.conversation,
        feasibility_evaluation=feasibility_evaluation,
        preferred_frame=_resolve_query_consistency_frame(context),
    )


def _build_feasibility_adaptive_signals(
    context: CapabilityContext,
) -> AdaptiveSequenceSignals:
    feasibility_evaluation = _evaluate_feasibility_for_context(context)
    consistency_evaluation = _evaluate_consistency_for_context(
        context,
        feasibility_evaluation=feasibility_evaluation,
    )

    advice_frame = ADVICE_FRAME_FEASIBILITY
    if feasibility_evaluation.frame == FEASIBILITY_FRAME_CONTRADICTION:
        advice_frame = ADVICE_FRAME_CONTRADICTION
    elif feasibility_evaluation.frame == FEASIBILITY_FRAME_REALISM:
        advice_frame = ADVICE_FRAME_REALISM
    elif feasibility_evaluation.frame == FEASIBILITY_FRAME_LIMITS:
        advice_frame = ADVICE_FRAME_LIMITS

    decision_focus = "feasibility"
    if advice_frame == ADVICE_FRAME_CONTRADICTION:
        decision_focus = "contradiction"
    elif advice_frame == ADVICE_FRAME_REALISM:
        decision_focus = "realism"
    elif advice_frame == ADVICE_FRAME_LIMITS:
        decision_focus = "limits"

    suggested_next_step = None
    if feasibility_evaluation.conditions_required:
        suggested_next_step = feasibility_evaluation.conditions_required[0]
    elif feasibility_evaluation.reformulation:
        suggested_next_step = feasibility_evaluation.reformulation
    elif consistency_evaluation.required_evidence:
        suggested_next_step = consistency_evaluation.required_evidence[0]

    return AdaptiveSequenceSignals(
        contextual_mode="feasibility_evaluation",
        diagnostic_scope="general",
        strategic_mode="feasibility_evaluation",
        recommendation_style="feasibility_compact",
        recommendation_priority="feasibility_assessment",
        recommendation_basis="judgment_trace",
        decision_focus=decision_focus,
        advice_scope="feasibility_evaluation",
        guidance_mode="feasibility_guidance",
        advice_frame=advice_frame,
        suggested_next_step=suggested_next_step,
        feasibility_status=feasibility_evaluation.status,
        feasibility_reason=feasibility_evaluation.reason,
        feasibility_scope=feasibility_evaluation.scope,
        contradiction_detected=feasibility_evaluation.contradiction_detected,
        uncertainty_level=feasibility_evaluation.uncertainty_level,
        realism_level=feasibility_evaluation.realism_level,
        conditions_required=feasibility_evaluation.conditions_required,
        feasibility_frame=feasibility_evaluation.frame,
        viability_basis=feasibility_evaluation.viability_basis,
        primary_constraint=feasibility_evaluation.primary_constraint,
        plausibility_mode=feasibility_evaluation.plausibility_mode,
        confidence_level=consistency_evaluation.confidence_level,
        consistency_status=consistency_evaluation.consistency_status,
        consistency_reason=consistency_evaluation.consistency_reason,
        evidence_sufficiency=consistency_evaluation.evidence_sufficiency,
        claim_strength=consistency_evaluation.claim_strength,
        ambiguity_detected=consistency_evaluation.ambiguity_detected,
        assumption_load=consistency_evaluation.assumption_load,
        required_evidence=consistency_evaluation.required_evidence,
        certainty_frame=consistency_evaluation.certainty_frame,
        revision_trigger=consistency_evaluation.revision_trigger,
        contextual_tension=consistency_evaluation.contextual_tension,
        recent_context_conflict=consistency_evaluation.recent_context_conflict,
        judgment_mode=consistency_evaluation.judgment_mode,
    )


def _build_consistency_adaptive_signals(
    context: CapabilityContext,
) -> AdaptiveSequenceSignals:
    consistency_evaluation = _evaluate_consistency_for_context(context)
    feasibility_evaluation = consistency_evaluation.feasibility

    advice_frame = ADVICE_FRAME_CONFIDENCE
    if consistency_evaluation.certainty_frame == CONSISTENCY_FRAME_ASSERTION:
        advice_frame = ADVICE_FRAME_ASSERTION
    elif consistency_evaluation.certainty_frame == CONSISTENCY_FRAME_DEPENDENCY:
        advice_frame = ADVICE_FRAME_DEPENDENCY
    elif consistency_evaluation.certainty_frame == CONSISTENCY_FRAME_EVIDENCE:
        advice_frame = ADVICE_FRAME_EVIDENCE
    elif consistency_evaluation.certainty_frame == CONSISTENCY_FRAME_CONTEXT_TENSION:
        advice_frame = ADVICE_FRAME_CONTEXT_TENSION

    decision_focus = "confidence"
    if advice_frame == ADVICE_FRAME_ASSERTION:
        decision_focus = "assertion"
    elif advice_frame == ADVICE_FRAME_DEPENDENCY:
        decision_focus = "dependency"
    elif advice_frame == ADVICE_FRAME_EVIDENCE:
        decision_focus = "evidence"
    elif advice_frame == ADVICE_FRAME_CONTEXT_TENSION:
        decision_focus = "context_tension"

    suggested_next_step = None
    if consistency_evaluation.required_evidence:
        suggested_next_step = consistency_evaluation.required_evidence[0]
    elif feasibility_evaluation.conditions_required:
        suggested_next_step = feasibility_evaluation.conditions_required[0]
    elif consistency_evaluation.contextual_tension:
        suggested_next_step = "aclarar qué premisa pesa más"

    return AdaptiveSequenceSignals(
        contextual_mode="consistency_evaluation",
        diagnostic_scope="general",
        strategic_mode="consistency_evaluation",
        recommendation_style="consistency_compact",
        recommendation_priority="consistency_calibration",
        recommendation_basis="judgment_trace",
        decision_focus=decision_focus,
        advice_scope="consistency_evaluation",
        guidance_mode="consistency_guidance",
        advice_frame=advice_frame,
        suggested_next_step=suggested_next_step,
        feasibility_status=feasibility_evaluation.status,
        feasibility_reason=feasibility_evaluation.reason,
        feasibility_scope=feasibility_evaluation.scope,
        contradiction_detected=feasibility_evaluation.contradiction_detected,
        uncertainty_level=feasibility_evaluation.uncertainty_level,
        realism_level=feasibility_evaluation.realism_level,
        conditions_required=feasibility_evaluation.conditions_required,
        feasibility_frame=feasibility_evaluation.frame,
        viability_basis=feasibility_evaluation.viability_basis,
        primary_constraint=feasibility_evaluation.primary_constraint,
        plausibility_mode=feasibility_evaluation.plausibility_mode,
        confidence_level=consistency_evaluation.confidence_level,
        consistency_status=consistency_evaluation.consistency_status,
        consistency_reason=consistency_evaluation.consistency_reason,
        evidence_sufficiency=consistency_evaluation.evidence_sufficiency,
        claim_strength=consistency_evaluation.claim_strength,
        ambiguity_detected=consistency_evaluation.ambiguity_detected,
        assumption_load=consistency_evaluation.assumption_load,
        required_evidence=consistency_evaluation.required_evidence,
        certainty_frame=consistency_evaluation.certainty_frame,
        revision_trigger=consistency_evaluation.revision_trigger,
        contextual_tension=consistency_evaluation.contextual_tension,
        recent_context_conflict=consistency_evaluation.recent_context_conflict,
        judgment_mode=consistency_evaluation.judgment_mode,
    )


def resolve_contextual_response_signals(
    sequence_name: str | None,
    context: CapabilityContext | None,
) -> AdaptiveSequenceSignals:
    if context is None:
        return AdaptiveSequenceSignals()

    if sequence_name is None and getattr(context.behavior_plan, "intent", None) == "feasibility_evaluation":
        return _build_feasibility_adaptive_signals(context)

    if sequence_name is None and getattr(context.behavior_plan, "intent", None) == "consistency_evaluation":
        return _build_consistency_adaptive_signals(context)

    if sequence_name is None:
        return AdaptiveSequenceSignals()

    contextual_mode = _resolve_contextual_mode(sequence_name, context)
    if contextual_mode == "feasibility_evaluation":
        return _build_feasibility_adaptive_signals(context)
    if contextual_mode == "consistency_evaluation":
        return _build_consistency_adaptive_signals(context)

    situational_profile = _resolve_situational_profile(sequence_name, context)
    advice_frame = _resolve_query_advice_frame(sequence_name, context)
    limitation_severity = _resolve_limitation_severity(context)
    blocker_type = _resolve_blocker_type(context)
    planning_enabled = contextual_mode not in {"feasibility_evaluation", "consistency_evaluation"}
    next_move_chain = _resolve_next_move_chain(context) if planning_enabled else None
    moment_profile = _resolve_moment_profile(sequence_name, context) if planning_enabled else None
    micro_plan = _resolve_micro_plan(context) if planning_enabled else ()
    suggested_next_step = (
        _build_actionable_next_step(context)
        if contextual_mode
        in {
            "actionable_help",
            "strategic_output",
            "readiness",
            "limitation_focus",
            "strength_focus",
        }
        else _build_next_step_hint(context)
    )
    return AdaptiveSequenceSignals(
        readiness_status=_resolve_readiness_status(context),
        priority_focus=_resolve_priority_focus_key(context),
        dominant_limitation=_resolve_dominant_limitation_key(context),
        dominant_strength=_resolve_dominant_strength_key(context),
        recommendation_level=_resolve_recommendation_level(context),
        contextual_mode=contextual_mode,
        diagnostic_scope=_resolve_diagnostic_scope(sequence_name),
        readiness_reason=_resolve_readiness_reason_key(context),
        suggested_next_step=suggested_next_step,
        main_help_scope=_resolve_main_help_scope_key(context),
        strategic_mode=_resolve_strategic_mode(sequence_name, context),
        recommended_focus=_resolve_recommended_focus_key(context),
        recommended_action=_resolve_recommended_action(context),
        next_step_type=_resolve_next_step_type(context),
        readiness_path=_resolve_readiness_path(context),
        limitation_severity=limitation_severity,
        recommendation_style=_resolve_recommendation_style(sequence_name, context),
        recommendation_priority=_resolve_recommendation_priority(sequence_name, context),
        recommendation_basis=_resolve_recommendation_basis(sequence_name, context),
        decision_focus=_resolve_decision_focus(sequence_name, context),
        actionability_level=_resolve_actionability_level(context),
        advice_scope=_resolve_advice_scope(sequence_name, context),
        situational_profile=situational_profile,
        advice_frame=advice_frame,
        recommended_order=_resolve_recommended_order(context) if planning_enabled else None,
        moment_profile=moment_profile,
        next_move_chain=next_move_chain,
        move_priority=next_move_chain[0] if next_move_chain else None,
        move_count=len(next_move_chain) if next_move_chain else None,
        guidance_mode=_resolve_guidance_mode(sequence_name, context),
        followup_trigger=(
            _resolve_followup_trigger(sequence_name, context) if planning_enabled else None
        ),
        sequence_confidence=(
            _resolve_sequence_confidence(sequence_name, context) if planning_enabled else None
        ),
        momentum_type=(
            _resolve_momentum_type(sequence_name, context) if planning_enabled else None
        ),
        micro_plan=micro_plan,
        plan_horizon=(
            _resolve_plan_horizon(sequence_name, context) if planning_enabled else None
        ),
        now_step=micro_plan[0] if micro_plan else None,
        next_step=micro_plan[1] if len(micro_plan) > 1 else None,
        later_step=micro_plan[2] if len(micro_plan) > 2 else None,
        planning_mode=(
            _resolve_planning_mode(sequence_name, context) if planning_enabled else None
        ),
        sequence_depth=(
            _resolve_sequence_depth(sequence_name, context) if planning_enabled else None
        ),
        plan_confidence=(
            _resolve_plan_confidence(sequence_name, context) if planning_enabled else None
        ),
        followup_priority=(
            _resolve_followup_priority(sequence_name, context) if planning_enabled else None
        ),
        feasibility_status=None,
        feasibility_reason=None,
        feasibility_scope=None,
        contradiction_detected=None,
        uncertainty_level=None,
        realism_level=None,
        conditions_required=None,
        feasibility_frame=None,
        viability_basis=None,
        primary_constraint=None,
        plausibility_mode=None,
        confidence_level=None,
        consistency_status=None,
        consistency_reason=None,
        evidence_sufficiency=None,
        claim_strength=None,
        ambiguity_detected=None,
        assumption_load=None,
        required_evidence=None,
        certainty_frame=None,
        revision_trigger=None,
        contextual_tension=None,
        recent_context_conflict=None,
        judgment_mode=None,
        blocker_type=(
            blocker_type
            if limitation_severity != "low"
            or advice_frame == ADVICE_FRAME_RECOVERY_PLAY
            else None
        ),
        opportunity_focus=(
            _resolve_opportunity_focus(context)
            if situational_profile
            in {
                SITUATIONAL_PROFILE_EXPLOIT,
                SITUATIONAL_PROFILE_GUIDANCE,
                SITUATIONAL_PROFILE_REVIEW,
            }
            else None
        ),
        recovery_strategy=(
            _resolve_recovery_strategy(context)
            if situational_profile in {SITUATIONAL_PROFILE_RECOVERY, SITUATIONAL_PROFILE_MAINTENANCE}
            else None
        ),
        exploitation_path=(
            _resolve_exploitation_path(context)
            if situational_profile == SITUATIONAL_PROFILE_EXPLOIT
            or advice_frame == ADVICE_FRAME_EXPLOIT_PLAY
            else None
        ),
    )


def resolve_adaptive_sequence_signals(
    sequence_name: str | None,
    context: CapabilityContext | None,
) -> AdaptiveSequenceSignals:
    return resolve_contextual_response_signals(sequence_name, context)


def _build_recent_activity_summary(context: CapabilityContext) -> str:
    from .maintenance_agent import (
        MAINTENANCE_TARGET_SUMMARIZE_LAST_LOG,
        MAINTENANCE_TARGET_SUMMARIZE_LAST_TURN,
        MaintenanceCommand,
        execute_maintenance_command,
    )

    summaries: list[str] = []

    turn_summary = execute_maintenance_command(
        MaintenanceCommand(target=MAINTENANCE_TARGET_SUMMARIZE_LAST_TURN),
        conversation=context.conversation,
        memory=context.memory,
        memory_file=context.memory_file,
        log_file=context.log_file,
        aura_version=context.aura_version,
        model_path=context.model_path,
        llama_path=context.llama_path,
    )
    if not turn_summary.startswith("Todavía no tengo"):
        turn_snapshot = _strip_summary_prefix(turn_summary)
        turn_snapshot = re.split(
            r"\.\s+Yo:\s*",
            turn_snapshot,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        summaries.append(f"turno reciente: {turn_snapshot}")

    log_summary = execute_maintenance_command(
        MaintenanceCommand(target=MAINTENANCE_TARGET_SUMMARIZE_LAST_LOG),
        conversation=context.conversation,
        memory=context.memory,
        memory_file=context.memory_file,
        log_file=context.log_file,
        aura_version=context.aura_version,
        model_path=context.model_path,
        llama_path=context.llama_path,
    )
    if not log_summary.startswith("Todavía no tengo"):
        log_snapshot = _strip_summary_prefix(log_summary)
        log_snapshot = re.split(
            r"\.\s+(?:Tú|Yo):\s*",
            log_snapshot,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        summaries.append(f"log reciente: {log_snapshot}")

    if not summaries:
        return "sin actividad reciente disponible"

    return "; ".join(summaries[:2])


def _build_goal_response(
    title: str,
    status: str,
    focus: str | None = None,
    limitation: str | None = None,
    next_step: str | None = None,
    focus_label: str = "Importante",
    adaptive_mode: str = "balanced",
    contextual_mode: str = "diagnostic",
) -> str:
    parts = [f"{title}: {status}"]
    focus_part = f"{focus_label}: {focus}" if focus else ""
    limitation_part = f"Limitación principal: {limitation}" if limitation else ""
    next_step_part = f"Siguiente paso: {next_step}" if next_step else ""

    if contextual_mode == "actionable_help":
        parts.extend([focus_part, next_step_part, limitation_part])
    elif contextual_mode == "strategic_output":
        parts.extend([focus_part, next_step_part, limitation_part])
    elif contextual_mode == "strength_focus":
        parts.extend([focus_part, next_step_part, limitation_part])
    elif contextual_mode == "limitation_focus":
        parts.extend([focus_part, next_step_part, limitation_part])
    elif contextual_mode == "review":
        parts.extend([focus_part, limitation_part, next_step_part])
    elif adaptive_mode == "constraint_first":
        parts.extend([limitation_part, focus_part, next_step_part])
    elif adaptive_mode == "guidance_adaptive":
        parts.extend([focus_part, next_step_part, limitation_part])
    elif adaptive_mode == "strength_first":
        parts.extend([focus_part, limitation_part, next_step_part])
    else:
        parts.extend([focus_part, limitation_part, next_step_part])

    return _compose_sentences(*parts)


def analyze_internal_tools_query(user_input: str) -> InternalToolsQuery | None:
    consistency_query = analyze_consistency_query(user_input)
    if consistency_query is not None:
        advice_frame = ADVICE_FRAME_CONFIDENCE
        if consistency_query.frame == CONSISTENCY_FRAME_ASSERTION:
            advice_frame = ADVICE_FRAME_ASSERTION
        elif consistency_query.frame == CONSISTENCY_FRAME_DEPENDENCY:
            advice_frame = ADVICE_FRAME_DEPENDENCY
        elif consistency_query.frame == CONSISTENCY_FRAME_EVIDENCE:
            advice_frame = ADVICE_FRAME_EVIDENCE
        elif consistency_query.frame == CONSISTENCY_FRAME_CONTEXT_TENSION:
            advice_frame = ADVICE_FRAME_CONTEXT_TENSION

        return InternalToolsQuery(
            mode=TOOLS_MODE_CONSISTENCY,
            style=STRATEGY_QUERY_STYLE_EXPLAINED,
            advice_frame=advice_frame,
            consistency_frame=consistency_query.frame,
        )

    feasibility_query = analyze_feasibility_query(user_input)
    if feasibility_query is not None:
        advice_frame = ADVICE_FRAME_FEASIBILITY
        if feasibility_query.frame == FEASIBILITY_FRAME_CONTRADICTION:
            advice_frame = ADVICE_FRAME_CONTRADICTION
        elif feasibility_query.frame == FEASIBILITY_FRAME_REALISM:
            advice_frame = ADVICE_FRAME_REALISM
        elif feasibility_query.frame == FEASIBILITY_FRAME_LIMITS:
            advice_frame = ADVICE_FRAME_LIMITS

        return InternalToolsQuery(
            mode=TOOLS_MODE_FEASIBILITY,
            style=STRATEGY_QUERY_STYLE_EXPLAINED,
            advice_frame=advice_frame,
            feasibility_frame=feasibility_query.frame,
        )

    if looks_like_feasibility_statement(user_input):
        return InternalToolsQuery(
            mode=TOOLS_MODE_FEASIBILITY,
            style=STRATEGY_QUERY_STYLE_EXPLAINED,
            advice_frame=ADVICE_FRAME_FEASIBILITY,
            feasibility_frame=FEASIBILITY_FRAME_GENERAL,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_RECOVERY_PLAY_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_NEXT_STEP,
            advice_frame=ADVICE_FRAME_RECOVERY_PLAY,
            forced_profile=SITUATIONAL_PROFILE_RECOVERY,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_EXPLOIT_PLAY_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_DIRECT_FOCUS,
            advice_frame=ADVICE_FRAME_EXPLOIT_PLAY,
            forced_profile=SITUATIONAL_PROFILE_EXPLOIT,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_FIRST_MOVE_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_DIRECT_FOCUS,
            advice_frame=ADVICE_FRAME_FIRST_MOVE,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_PAIRED_MOVES_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_NEXT_STEP,
            advice_frame=ADVICE_FRAME_PAIRED_MOVES,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_MICRO_PLAN_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_NEXT_STEP,
            advice_frame=ADVICE_FRAME_MICRO_PLAN,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_FOLLOWUP_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_NEXT_STEP,
            advice_frame=ADVICE_FRAME_FOLLOWUP_MOVE,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_LATER_MOVE_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_NEXT_STEP,
            advice_frame=ADVICE_FRAME_LATER_MOVE,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_ENTRY_STEP_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_NEXT_STEP,
            advice_frame=ADVICE_FRAME_ENTRY_STEP,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_EXPLAINED_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_EXPLAINED,
            advice_frame=ADVICE_FRAME_EXPLAINED_NOW,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_UTILITY_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_UTILITY,
            advice_frame=ADVICE_FRAME_HIGHEST_VALUE,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_PRIORITY_NOW_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_DIRECT_FOCUS,
            advice_frame=ADVICE_FRAME_PRIORITY_NOW,
        )

    if matches_normalized_command(user_input, TOOLS_STRATEGIC_FOCUS_NOW_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
            style=STRATEGY_QUERY_STYLE_DIRECT_FOCUS,
            advice_frame=ADVICE_FRAME_FOCUS_NOW,
        )

    if matches_normalized_command(user_input, TOOLS_CONTEXTUAL_HELP_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_CONTEXTUAL_HELP,
            advice_frame=ADVICE_FRAME_HELP_NOW,
        )

    if matches_normalized_command(user_input, TOOLS_DOMINANT_STRENGTH_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_DOMINANT_STRENGTH,
            advice_frame=ADVICE_FRAME_STRENGTH,
        )

    if matches_normalized_command(user_input, TOOLS_DOMINANT_LIMITATION_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_DOMINANT_LIMITATION,
            advice_frame=ADVICE_FRAME_LIMITATION,
        )

    if matches_normalized_command(user_input, TOOLS_PRIORITY_NOW_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_PRIORITY_NOW,
            advice_frame=ADVICE_FRAME_PRIORITY_NOW,
        )

    if matches_normalized_command(user_input, TOOLS_COMPLETE_REVIEW_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_COMPLETE_REVIEW,
            advice_frame=ADVICE_FRAME_REVIEW,
        )

    if matches_normalized_command(user_input, TOOLS_OPERATIONAL_REVIEW_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_OPERATIONAL_REVIEW,
            advice_frame=ADVICE_FRAME_REVIEW,
        )

    if matches_normalized_command(user_input, TOOLS_PRACTICAL_REVIEW_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_PRACTICAL_REVIEW,
            advice_frame=ADVICE_FRAME_REVIEW,
        )

    if matches_normalized_command(user_input, TOOLS_INTERNAL_REVIEW_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_INTERNAL_REVIEW,
            advice_frame=ADVICE_FRAME_REVIEW,
        )

    if matches_normalized_command(
        user_input,
        TOOLS_MEMORY_AND_STATE_REVIEW_QUERY_COMMANDS,
    ):
        return InternalToolsQuery(
            mode=TOOLS_MODE_MEMORY_AND_STATE_REVIEW,
            advice_frame=ADVICE_FRAME_REVIEW,
        )

    if matches_normalized_command(user_input, TOOLS_LIMITATIONS_OVERVIEW_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_LIMITATIONS_OVERVIEW,
            advice_frame=ADVICE_FRAME_LIMITATION,
        )

    if matches_normalized_command(user_input, TOOLS_READINESS_GAP_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_READINESS_GAP,
            advice_frame=ADVICE_FRAME_READINESS,
        )

    if matches_normalized_command(user_input, TOOLS_WORK_READINESS_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_WORK_READINESS,
            advice_frame=ADVICE_FRAME_READINESS,
        )

    if matches_normalized_command(user_input, TOOLS_SYSTEM_CHECK_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_SYSTEM_CHECK,
            advice_frame=ADVICE_FRAME_DIAGNOSTIC,
        )

    if matches_normalized_command(user_input, TOOLS_GENERAL_CHECK_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_GENERAL_CHECK,
            advice_frame=ADVICE_FRAME_DIAGNOSTIC,
        )

    if matches_normalized_command(user_input, TOOLS_GENERAL_DIAGNOSTIC_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_GENERAL_DIAGNOSTIC,
            advice_frame=ADVICE_FRAME_DIAGNOSTIC,
        )

    if matches_normalized_command(user_input, TOOLS_FULL_DIAGNOSTIC_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_FULL_DIAGNOSTIC,
            advice_frame=ADVICE_FRAME_DIAGNOSTIC,
        )

    if matches_normalized_command(user_input, TOOLS_QUICK_CHECK_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_QUICK_CHECK,
            advice_frame=ADVICE_FRAME_DIAGNOSTIC,
        )

    if matches_normalized_command(user_input, TOOLS_SITUATIONAL_STATUS_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_SITUATIONAL_STATUS,
            advice_frame=ADVICE_FRAME_DIAGNOSTIC,
        )

    if matches_normalized_command(user_input, TOOLS_DIAGNOSTIC_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_DIAGNOSTIC,
            advice_frame=ADVICE_FRAME_DIAGNOSTIC,
        )

    if matches_normalized_command(user_input, TOOLS_CATALOG_QUERY_COMMANDS):
        return InternalToolsQuery(
            mode=TOOLS_MODE_CATALOG,
            advice_frame=ADVICE_FRAME_CATALOG,
        )

    return None


def _collect_tool_examples() -> list[str]:
    from .internal_actions_registry import get_internal_actions_for_tool
    from .internal_tools_registry import get_internal_tools_in_order

    examples: list[str] = []
    available_examples: list[str] = []

    for tool_definition in get_internal_tools_in_order():
        for action_definition in get_internal_actions_for_tool(tool_definition.name):
            for example in action_definition.examples:
                if example and example not in available_examples:
                    available_examples.append(example)

    preferred_examples = [
        "que conviene hacer ahora",
        "armame un plan corto",
        "que tools internas tienes",
    ]

    for example in preferred_examples:
        if example in available_examples and example not in examples:
            examples.append(example)
        if len(examples) >= 3:
            return examples

    for example in available_examples:
        if example not in examples:
            examples.append(example)
        if len(examples) >= 3:
            return examples

    return examples


def _collect_sequence_labels(limit: int = 4) -> list[str]:
    from .internal_sequences_registry import get_internal_sequences_in_order

    preferred_labels = {
        "diagnóstico general",
        "chequeo general",
        "revisión operativa",
        "foco recomendado",
    }
    labels: list[str] = []

    for sequence_definition in get_internal_sequences_in_order():
        if sequence_definition.label in preferred_labels:
            labels.append(sequence_definition.label)
        if len(labels) >= limit:
            break

    return _dedupe_items(labels)


def _build_catalog_response(context: CapabilityContext | None = None) -> str:
    from .internal_actions_registry import get_internal_actions_for_tool
    from .internal_tools_registry import (
        TOOL_COMPOSITE_DIAGNOSTICS,
        TOOL_COMPOSITE_REVIEWS,
        TOOL_HELP_CATALOGS,
        TOOL_LOCAL_MODEL_RUNTIME,
        TOOL_MAINTENANCE_CONSOLE,
        TOOL_SESSION_CONTROL,
        TOOL_SYSTEM_STATE_READER,
        TOOL_USER_MEMORY,
        get_internal_tools_in_order,
    )

    available_tools = {
        tool_definition.name: tool_definition
        for tool_definition in get_internal_tools_in_order()
        if get_internal_actions_for_tool(tool_definition.name)
    }

    if not available_tools:
        return "No tengo tools internas registradas ahora."

    base_groups: list[str] = []
    composite_groups: list[str] = []
    support_groups: list[str] = []

    if TOOL_HELP_CATALOGS in available_tools:
        base_groups.append("catálogos y ayuda")
    if TOOL_USER_MEMORY in available_tools:
        base_groups.append("memoria")
    if TOOL_SYSTEM_STATE_READER in available_tools:
        base_groups.append("estado")
    if TOOL_MAINTENANCE_CONSOLE in available_tools:
        base_groups.append("mantenimiento")

    if TOOL_COMPOSITE_DIAGNOSTICS in available_tools:
        composite_groups.append("diagnósticos")
    if TOOL_COMPOSITE_REVIEWS in available_tools:
        composite_groups.append("revisión estratégica")

    if TOOL_LOCAL_MODEL_RUNTIME in available_tools:
        support_groups.append("modelo local")
    if TOOL_SESSION_CONTROL in available_tools:
        support_groups.append("cierre de sesión")

    visible_groups = _dedupe_items(base_groups + composite_groups + support_groups)
    parts: list[str] = []
    if visible_groups:
        parts.append(
            "Tengo herramientas internas de "
            f"{_format_items(visible_groups)}"
        )

    examples = _collect_tool_examples()
    if context is not None:
        current_query = normalize_internal_text(context.user_input_raw)
        examples = [
            example
            for example in examples
            if normalize_internal_text(example) != current_query
        ]
    if examples:
        example_text = _format_items([f'"{example}"' for example in examples[:2]])
        parts.append(f"Si quieres ir directo, prueba {example_text}")

    return _compose_sentences(*parts)


def _secondary_limitation_text(
    context: CapabilityContext,
    primary_text: str | None = None,
    *,
    include_scope_boundary: bool = False,
) -> str | None:
    limitation_text = _build_surface_limitation_text(
        context,
        include_scope_boundary=include_scope_boundary,
    )
    if not limitation_text:
        return None
    if primary_text and _clean_text(primary_text) in _clean_text(limitation_text):
        return None
    return limitation_text


def _resolve_recommended_order_parts(context: CapabilityContext) -> list[str]:
    return list(_resolve_recommended_order(context))


def _build_primary_action_text(context: CapabilityContext) -> str:
    recommended_order = _resolve_recommended_order_parts(context)
    if recommended_order:
        return recommended_order[0]

    return _resolve_recommended_action(context)


def _build_secondary_action_text(context: CapabilityContext) -> str | None:
    recommended_order = _resolve_recommended_order_parts(context)
    if len(recommended_order) > 1:
        return recommended_order[1]

    return None


def _build_compact_action_sentence(
    context: CapabilityContext,
    *,
    prefix: str = "Empieza por",
    mention_follow_up: bool = False,
) -> str:
    primary_action = _build_primary_action_text(context)
    secondary_action = _build_secondary_action_text(context)

    if mention_follow_up and secondary_action:
        return (
            f'{prefix} "{primary_action}" y deja "{secondary_action}" '
            "como segundo paso"
        )

    return f'{prefix} "{primary_action}"'


def _build_followup_action_sentence(
    context: CapabilityContext,
    *,
    prefix: str = "Después iría a",
) -> str | None:
    secondary_action = _build_secondary_action_text(context)
    if not secondary_action:
        return None

    return f'{prefix} "{secondary_action}"'


def _build_followup_reason_text(context: CapabilityContext) -> str:
    followup_trigger = _resolve_followup_trigger("strategic_guidance_sequence", context)

    if followup_trigger == "after_recovery_validation":
        return "para confirmar si el bloqueo sigue en el modelo o en llama-cli"
    if followup_trigger == "after_state_stabilization":
        return "cuando memoria y estado ya queden ordenados"
    if followup_trigger == "if_initial_scan_confirms_gap":
        return "si el primer barrido confirma que todavía falta panorama"
    if followup_trigger == "when_internal_scope_is_enough":
        return "mientras siga alcanzando con el margen interno del núcleo"
    return "si todavía hace falta más panorama"


def _build_later_reason_text(context: CapabilityContext) -> str:
    moment_profile = _resolve_moment_profile("strategic_guidance_sequence", context)

    if moment_profile == MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY:
        return "solo cuando el frente de recuperación ya quede validado"
    if moment_profile == MOMENT_PROFILE_MAINTAIN_BEFORE_ADVANCING:
        return "solo si después de ordenar memoria todavía hace falta abrir panorama"
    if moment_profile == MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST:
        return "solo si después del barrido inicial sigue quedando una duda"
    return "solo si después de avanzar aparece una duda nueva"


def _build_micro_plan_line(
    context: CapabilityContext,
    *,
    include_next: bool = True,
    include_later: bool = True,
    label: str = "Plan corto",
) -> str:
    micro_plan = _resolve_micro_plan(context)
    if not micro_plan:
        return ""

    parts: list[str] = []
    parts.append(f'ahora "{micro_plan[0]}"')
    if include_next and len(micro_plan) > 1:
        parts.append(f'después "{micro_plan[1]}"')
    if include_later and len(micro_plan) > 2:
        parts.append(f'más tarde, solo si hace falta, "{micro_plan[2]}"')

    return f"{label}: {'; '.join(parts)}"


def build_internal_diagnostic_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude construir el diagnóstico interno ahora."

    return _compose_sentences(
        f"Diagnóstico interno: {_build_overall_health(context)}",
        f"Punto clave: {_build_priority_focus(context)}",
        f"Memoria: {_build_memory_brief(context.memory)}",
    )


def build_general_diagnostic_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude construir el diagnóstico general ahora."

    return _compose_sentences(
        f"Diagnóstico general: {_build_readiness_status(context)}",
        f"Prioridad real: {_build_priority_focus(context)}",
        _build_compact_action_sentence(context, mention_follow_up=False),
    )


def build_full_diagnostic_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude construir el diagnóstico completo ahora."

    return _compose_sentences(
        f"Diagnóstico completo: {_build_readiness_status(context)}",
        f"Base técnica: {_build_core_status_line(context)}",
        f"Ruta sugerida: {_build_next_step_hint(context)}",
    )


def build_situational_status_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude resumir mi estado actual ahora."

    if _resolve_readiness_status(context) == "ready":
        return _compose_sentences(
            f"Estado actual: {_build_readiness_status(context)}",
            f"Fortaleza dominante: {_build_dominant_strength_text(context)}",
            _build_compact_action_sentence(context, mention_follow_up=False),
        )

    return _compose_sentences(
        f"Estado actual: {_build_readiness_status(context)}",
        f"Principal límite: {_build_dominant_limitation_text(context)}",
        f"Siguiente foco: {_build_next_step_hint(context)}",
    )


def build_quick_check_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude hacer el chequeo rápido ahora."

    return _compose_sentences(
        f"Chequeo rápido: {_build_readiness_status(context)}",
        f"Prioridad inmediata: {_build_priority_focus(context)}",
        f"Siguiente paso: {_build_next_step_hint(context)}",
    )


def build_general_check_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude hacer el chequeo general ahora."

    return _compose_sentences(
        f"Chequeo general: {_build_overall_health(context)}",
        f"Disponibilidad: {_build_availability_brief(context)}",
        f"Prioridad: {_build_priority_focus(context)}",
    )


def build_system_check_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude hacer el chequeo del sistema ahora."

    return _compose_sentences(
        f"Chequeo del sistema: {_build_overall_health(context)}",
        f"Base técnica: {_build_core_status_line(context)}",
        f"Memoria: {_build_memory_brief(context.memory)}",
    )


def build_priority_now_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude identificar la prioridad actual ahora."

    if _resolve_readiness_status(context) == "ready":
        return _compose_sentences(
            f"Lo más importante ahora es aprovechar que {_build_dominant_strength_text(context)}",
            f"Eso abre { _build_recommended_focus_text(context) }",
            _build_compact_action_sentence(context, mention_follow_up=True),
        )

    return _compose_sentences(
        f"Lo más importante ahora es resolver {_build_dominant_limitation_text(context)}",
        f"Eso pesa más que abrir nuevas revisiones porque {_build_strategic_reason(context)}",
        _build_compact_action_sentence(context, mention_follow_up=False),
    )


def build_dominant_limitation_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude identificar la limitación principal ahora."

    limitation = _build_surface_limitation_text(
        context,
        include_scope_boundary=True,
    ) or _build_scope_boundary_text()
    return _compose_sentences(
        f"Limitación principal: {limitation}",
        f"Impacto inmediato: {_build_priority_focus(context)}",
        _build_compact_action_sentence(context, mention_follow_up=False),
    )


def build_dominant_strength_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude identificar la fortaleza principal ahora."

    strength = _build_dominant_strength_text(context)
    return _compose_sentences(
        f"Fortaleza principal: {strength}",
        f"Ahora la ventaja real es {_build_main_help_scope_text(context)}",
        _build_compact_action_sentence(context, mention_follow_up=True),
    )


def build_work_readiness_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude revisar si estoy lista para trabajar ahora."

    readiness_reason = _resolve_readiness_reason_key(context)
    if readiness_reason == "core_ready":
        reason_text = "la base del runtime ya está disponible"
    elif readiness_reason == "memory_sanitization_pending":
        reason_text = "queda un ajuste menor de memoria antes de avanzar con más orden"
    elif readiness_reason == "model_unavailable":
        reason_text = "falta el modelo local"
    else:
        reason_text = "llama-cli todavía no está listo"

    return _compose_sentences(
        f"Preparación para trabajar: {_build_readiness_status(context)}",
        f"Motivo principal: {reason_text}",
        _build_compact_action_sentence(context, mention_follow_up=False),
    )


def build_readiness_gap_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude revisar qué me falta para trabajar ahora."

    readiness_status = _resolve_readiness_status(context)
    if readiness_status == "ready":
        gap = "no me falta nada crítico"
    elif readiness_status == "partially_ready":
        gap = "me falta resolver un chequeo menor de memoria"
    elif readiness_status == "limited_model":
        gap = "me falta el modelo local"
    else:
        gap = "me falta dejar listo llama-cli"

    return _compose_sentences(
        f"Brecha para trabajar: {gap}",
        f"Estado actual: {_build_readiness_status(context)}",
        _build_compact_action_sentence(context, mention_follow_up=False),
    )


def build_limitations_overview_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude resumir mis limitaciones actuales ahora."

    limitation = _build_surface_limitation_text(
        context,
        include_scope_boundary=True,
    ) or _build_scope_boundary_text()
    return _compose_sentences(
        f"Limitaciones actuales: {limitation}",
        f"Estado base: {_build_readiness_status(context)}",
        _build_compact_action_sentence(context, mention_follow_up=False),
    )


def build_contextual_help_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude orientar cómo ayudarte ahora."

    primary_action = _build_primary_action_text(context)
    secondary_action = _build_secondary_action_text(context)
    return _compose_sentences(
        f"Ayuda disponible ahora: {_build_main_help_scope_text(context)}",
        (
            f'Lo más directo es "{primary_action}"'
            + (
                f'; si hace falta más panorama, sigue con "{secondary_action}"'
                if secondary_action
                else ""
            )
        ),
    )


def build_feasibility_response(
    context: CapabilityContext | None,
    query: InternalToolsQuery | None = None,
) -> str:
    if context is None:
        return "No pude evaluar la viabilidad ahora."

    evaluation = evaluate_feasibility(
        context.user_input_raw,
        conversation=context.conversation,
        preferred_frame=(
            query.feasibility_frame
            if query is not None
            else _resolve_query_feasibility_frame(context)
        ),
    )
    return build_structured_feasibility_response(evaluation)


def build_consistency_response(
    context: CapabilityContext | None,
    query: InternalToolsQuery | None = None,
) -> str:
    if context is None:
        return "No pude calibrar ese juicio ahora."

    preferred_frame = (
        query.consistency_frame
        if query is not None
        else _resolve_query_consistency_frame(context)
    )
    evaluation = evaluate_consistency(
        context.user_input_raw,
        conversation=context.conversation,
        preferred_frame=preferred_frame,
    )
    return build_structured_consistency_response(evaluation)


def build_strategic_guidance_response(
    context: CapabilityContext | None,
    query: InternalToolsQuery | None = None,
) -> str:
    if context is None:
        return "No pude construir una recomendación estratégica ahora."

    query = query or context.tools_query or InternalToolsQuery(
        mode=TOOLS_MODE_STRATEGIC_GUIDANCE,
        style=STRATEGY_QUERY_STYLE_DEFAULT,
        advice_frame=ADVICE_FRAME_FOCUS_NOW,
    )
    advice_frame = query.advice_frame or ADVICE_FRAME_FOCUS_NOW
    situational_profile = _resolve_situational_profile(
        "strategic_guidance_sequence",
        context,
    )
    moment_profile = _resolve_moment_profile("strategic_guidance_sequence", context)
    recommended_focus = _build_recommended_focus_text(context)
    recommended_reason = _build_strategic_reason(context)
    limitation_text = _build_surface_limitation_text(
        context,
        include_scope_boundary=advice_frame in {
            ADVICE_FRAME_RECOVERY_PLAY,
            ADVICE_FRAME_PRIORITY_NOW,
        },
    ) or _build_scope_boundary_text()
    strength_text = _build_dominant_strength_text(context)
    main_help = _build_main_help_scope_text(context)
    primary_action = _build_primary_action_text(context)
    micro_plan = _resolve_micro_plan(context)
    now_step = micro_plan[0] if micro_plan else primary_action
    next_step = micro_plan[1] if len(micro_plan) > 1 else _build_secondary_action_text(context)
    later_step = micro_plan[2] if len(micro_plan) > 2 else _resolve_later_step(context)
    followup_reason = _build_followup_reason_text(context)
    later_reason = _build_later_reason_text(context)

    if advice_frame == ADVICE_FRAME_RECOVERY_PLAY:
        recovery_target = (
            "si falla el modelo o falla llama-cli"
            if _resolve_blocker_type(context) == "runtime_or_model"
            else limitation_text
        )
        return _compose_sentences(
            f'Si quedara limitada, empezaría por "{primary_action}"',
            f"Buscaría ubicar rápido {recovery_target}",
        )

    if advice_frame == ADVICE_FRAME_EXPLOIT_PLAY:
        return _compose_sentences(
            f"Si estuviera lista, aprovecharía que {strength_text}",
            f'Iría primero por "{now_step}"',
        )

    if advice_frame == ADVICE_FRAME_MICRO_PLAN:
        return _compose_sentences(
            _build_micro_plan_line(context),
            f"Lo ordeno así porque {recommended_reason}",
        )

    if advice_frame == ADVICE_FRAME_PAIRED_MOVES:
        return _compose_sentences(
            _build_micro_plan_line(
                context,
                include_later=False,
                label="Secuencia recomendada",
            ),
            f"Con eso cubro {recommended_focus} sin abrir demasiados frentes",
        )

    if advice_frame == ADVICE_FRAME_LATER_MOVE:
        deferred_step = later_step or next_step or now_step
        return _compose_sentences(
            f'Para más tarde dejaría "{deferred_step}"',
            later_reason,
        )

    if advice_frame == ADVICE_FRAME_FOLLOWUP_MOVE:
        followup_action = next_step or now_step
        followup_tail = (
            f"Lo usaría {followup_reason}"
            if followup_reason.startswith("para ")
            else f"Lo dejaría {followup_reason}"
        )
        return _compose_sentences(
            f'Después abriría "{followup_action}"',
            followup_tail,
        )

    if situational_profile in {SITUATIONAL_PROFILE_RECOVERY, SITUATIONAL_PROFILE_BLOCKED}:
        if advice_frame == ADVICE_FRAME_ENTRY_STEP:
            return _compose_sentences(
                f'Primer paso: "{primary_action}"',
                f"Bloqueo dominante: {limitation_text}",
            )
        if advice_frame == ADVICE_FRAME_EXPLAINED_NOW:
            return _compose_sentences(
                f"Te recomendaría {recommended_focus}",
                f"El bloqueo real hoy es {limitation_text}",
            )
        return _compose_sentences(
            f"Ahora conviene priorizar {recommended_focus}",
            f'Empieza por "{primary_action}"',
        )

    if situational_profile == SITUATIONAL_PROFILE_MAINTENANCE:
        if advice_frame == ADVICE_FRAME_ENTRY_STEP:
            return _compose_sentences(
                f'Empezaría por "{primary_action}"',
                "Eso ordena el núcleo antes de empujar más",
            )
        return _compose_sentences(
            f"Ahora conviene estabilizar {recommended_focus}",
            f'Empieza por "{primary_action}"',
        )

    if advice_frame == ADVICE_FRAME_PRIORITY_NOW:
        return _compose_sentences(
            f"Mi prioridad ahora sería {recommended_focus}",
            f'No abriría otro frente antes de "{primary_action}"',
        )

    if advice_frame == ADVICE_FRAME_EXPLAINED_NOW:
        basis_text = (
            f"La base para hacerlo es que {strength_text}"
            if moment_profile in {MOMENT_PROFILE_EXPLOIT_NOW, MOMENT_PROFILE_READY_TO_ADVANCE}
            else f"La base para hacerlo es que {recommended_reason}"
        )
        return _compose_sentences(
            f"Te recomendaría {recommended_focus}",
            basis_text,
        )

    if advice_frame == ADVICE_FRAME_ENTRY_STEP:
        unlock_text = (
            "Eso me deja una recuperación validada"
            if moment_profile == MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY
            else (
                "Eso ordena primero el núcleo antes de empujar más"
                if moment_profile in {
                    MOMENT_PROFILE_MAINTAIN_BEFORE_ADVANCING,
                    MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST,
                }
                else f"Eso deja encaminado el foco recomendado: {recommended_focus}"
            )
        )
        return _compose_sentences(
            f'Primer paso: "{primary_action}"',
            unlock_text,
        )

    if advice_frame == ADVICE_FRAME_HIGHEST_VALUE:
        value_basis = (
            f"Lo más valioso ahora es destrabar {limitation_text}"
            if moment_profile == MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY
            else f"Lo más útil ahora es aprovechar que {strength_text}"
        )
        return _compose_sentences(
            value_basis,
            f'Por eso iría por "{now_step}"',
        )

    if advice_frame == ADVICE_FRAME_FIRST_MOVE:
        return _compose_sentences(
            f'Yo haría "{now_step}" primero',
            (
                "Con eso resuelvo antes el frente que hoy más pesa"
                if moment_profile == MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY
                else f"Con eso dejo encaminado el foco principal: {recommended_focus}"
            ),
        )

    headline = (
        f"Ahora vale más aprovechar {recommended_focus}"
        if moment_profile == MOMENT_PROFILE_EXPLOIT_NOW
        else (
            f"Ahora ya podemos avanzar con {recommended_focus}"
            if moment_profile == MOMENT_PROFILE_READY_TO_ADVANCE
            else (
                f"Ahora conviene abrir {recommended_focus} antes de empujar más"
                if moment_profile == MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST
                else f"Conviene enfocarnos en {recommended_focus}"
            )
        )
    )
    return _compose_sentences(
        headline,
        f'Empieza por "{now_step}"'
        + (
            f'; si hace falta más panorama, sigue con "{next_step}"'
            if next_step
            else ""
        ),
    )


def build_memory_and_state_review_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude revisar memoria y estado ahora."

    return _compose_sentences(
        f"Revisión de memoria y estado: {_build_readiness_status(context)}",
        f"Prioridad de memoria: {_build_memory_review_hint(context.memory)}",
        _build_compact_action_sentence(context, mention_follow_up=False),
    )


def build_practical_review_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude hacer la revisión práctica ahora."

    return _compose_sentences(
        f"Revisión práctica: {_build_readiness_status(context)}",
        f"Ahora conviene usar {_build_main_help_scope_text(context)}",
        _build_compact_action_sentence(context, mention_follow_up=True),
    )


def build_operational_review_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude hacer la revisión operativa ahora."

    return _compose_sentences(
        f"Revisión operativa: {_build_readiness_status(context)}",
        f"Prioridad operativa: {_build_priority_focus(context)}",
        f"Mantenimiento sugerido: {_build_memory_review_hint(context.memory)}",
    )


def build_internal_review_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude hacer la revisión interna ahora."

    return _compose_sentences(
        f"Revisión interna: {_build_overall_health(context)}",
        f"Fortaleza dominante: {_build_dominant_strength_text(context)}",
        f"Actividad reciente: {_build_recent_activity_summary(context)}",
    )


def build_complete_review_response(context: CapabilityContext | None) -> str:
    if context is None:
        return "No pude hacer la revisión completa ahora."

    return _compose_sentences(
        f"Revisión completa: {_build_readiness_status(context)}",
        f"Prioridad: {_build_priority_focus(context)}",
        f"Fortaleza y actividad: {_build_dominant_strength_text(context)}; {_build_recent_activity_summary(context)}",
    )


def build_internal_sequence_response(
    sequence_name: str | None,
    context: CapabilityContext | None,
) -> str:
    from .internal_sequences_registry import (
        SEQUENCE_COMPLETE_REVIEW,
        SEQUENCE_CONSISTENCY_EVALUATION,
        SEQUENCE_CONTEXTUAL_HELP,
        SEQUENCE_DOMINANT_LIMITATION,
        SEQUENCE_DOMINANT_STRENGTH,
        SEQUENCE_FEASIBILITY_EVALUATION,
        SEQUENCE_FULL_DIAGNOSTIC,
        SEQUENCE_GENERAL_CHECK,
        SEQUENCE_GENERAL_DIAGNOSTIC,
        SEQUENCE_INTERNAL_DIAGNOSTIC,
        SEQUENCE_INTERNAL_REVIEW,
        SEQUENCE_LIMITATIONS_OVERVIEW,
        SEQUENCE_MEMORY_STATE_REVIEW,
        SEQUENCE_OPERATIONAL_REVIEW,
        SEQUENCE_PRACTICAL_REVIEW,
        SEQUENCE_PRIORITY_NOW,
        SEQUENCE_QUICK_CHECK,
        SEQUENCE_READINESS_GAP,
        SEQUENCE_STRATEGIC_GUIDANCE,
        SEQUENCE_SITUATIONAL_STATUS,
        SEQUENCE_SYSTEM_CHECK,
        SEQUENCE_WORK_READINESS,
    )

    if sequence_name == SEQUENCE_INTERNAL_DIAGNOSTIC:
        return build_internal_diagnostic_response(context)

    if sequence_name == SEQUENCE_GENERAL_DIAGNOSTIC:
        return build_general_diagnostic_response(context)

    if sequence_name == SEQUENCE_FULL_DIAGNOSTIC:
        return build_full_diagnostic_response(context)

    if sequence_name == SEQUENCE_SITUATIONAL_STATUS:
        return build_situational_status_response(context)

    if sequence_name == SEQUENCE_QUICK_CHECK:
        return build_quick_check_response(context)

    if sequence_name == SEQUENCE_GENERAL_CHECK:
        return build_general_check_response(context)

    if sequence_name == SEQUENCE_SYSTEM_CHECK:
        return build_system_check_response(context)

    if sequence_name == SEQUENCE_PRIORITY_NOW:
        return build_priority_now_response(context)

    if sequence_name == SEQUENCE_DOMINANT_LIMITATION:
        return build_dominant_limitation_response(context)

    if sequence_name == SEQUENCE_DOMINANT_STRENGTH:
        return build_dominant_strength_response(context)

    if sequence_name == SEQUENCE_WORK_READINESS:
        return build_work_readiness_response(context)

    if sequence_name == SEQUENCE_READINESS_GAP:
        return build_readiness_gap_response(context)

    if sequence_name == SEQUENCE_LIMITATIONS_OVERVIEW:
        return build_limitations_overview_response(context)

    if sequence_name == SEQUENCE_CONTEXTUAL_HELP:
        return build_contextual_help_response(context)

    if sequence_name == SEQUENCE_STRATEGIC_GUIDANCE:
        query = context.tools_query if context is not None else None
        return build_strategic_guidance_response(context, query=query)

    if sequence_name == SEQUENCE_FEASIBILITY_EVALUATION:
        query = context.tools_query if context is not None else None
        return build_feasibility_response(context, query=query)

    if sequence_name == SEQUENCE_CONSISTENCY_EVALUATION:
        query = context.tools_query if context is not None else None
        return build_consistency_response(context, query=query)

    if sequence_name == SEQUENCE_MEMORY_STATE_REVIEW:
        return build_memory_and_state_review_response(context)

    if sequence_name == SEQUENCE_PRACTICAL_REVIEW:
        return build_practical_review_response(context)

    if sequence_name == SEQUENCE_OPERATIONAL_REVIEW:
        return build_operational_review_response(context)

    if sequence_name == SEQUENCE_INTERNAL_REVIEW:
        return build_internal_review_response(context)

    if sequence_name == SEQUENCE_COMPLETE_REVIEW:
        return build_complete_review_response(context)

    return "No pude ejecutar esa secuencia interna ahora."


def build_internal_tools_response(
    query: InternalToolsQuery | None = None,
    context: CapabilityContext | None = None,
) -> str:
    query = query or InternalToolsQuery()

    if query.mode == TOOLS_MODE_STRATEGIC_GUIDANCE:
        return build_strategic_guidance_response(context, query=query)

    if query.mode == TOOLS_MODE_FEASIBILITY:
        return build_feasibility_response(context, query=query)

    if query.mode == TOOLS_MODE_CONSISTENCY:
        return build_consistency_response(context, query=query)

    if query.mode == TOOLS_MODE_CONTEXTUAL_HELP:
        return build_contextual_help_response(context)

    if query.mode == TOOLS_MODE_DIAGNOSTIC:
        return build_internal_diagnostic_response(context)

    if query.mode == TOOLS_MODE_GENERAL_DIAGNOSTIC:
        return build_general_diagnostic_response(context)

    if query.mode == TOOLS_MODE_FULL_DIAGNOSTIC:
        return build_full_diagnostic_response(context)

    if query.mode == TOOLS_MODE_SITUATIONAL_STATUS:
        return build_situational_status_response(context)

    if query.mode == TOOLS_MODE_QUICK_CHECK:
        return build_quick_check_response(context)

    if query.mode == TOOLS_MODE_GENERAL_CHECK:
        return build_general_check_response(context)

    if query.mode == TOOLS_MODE_SYSTEM_CHECK:
        return build_system_check_response(context)

    if query.mode == TOOLS_MODE_PRIORITY_NOW:
        return build_priority_now_response(context)

    if query.mode == TOOLS_MODE_DOMINANT_LIMITATION:
        return build_dominant_limitation_response(context)

    if query.mode == TOOLS_MODE_DOMINANT_STRENGTH:
        return build_dominant_strength_response(context)

    if query.mode == TOOLS_MODE_WORK_READINESS:
        return build_work_readiness_response(context)

    if query.mode == TOOLS_MODE_READINESS_GAP:
        return build_readiness_gap_response(context)

    if query.mode == TOOLS_MODE_LIMITATIONS_OVERVIEW:
        return build_limitations_overview_response(context)

    if query.mode == TOOLS_MODE_MEMORY_AND_STATE_REVIEW:
        return build_memory_and_state_review_response(context)

    if query.mode == TOOLS_MODE_PRACTICAL_REVIEW:
        return build_practical_review_response(context)

    if query.mode == TOOLS_MODE_OPERATIONAL_REVIEW:
        return build_operational_review_response(context)

    if query.mode == TOOLS_MODE_INTERNAL_REVIEW:
        return build_internal_review_response(context)

    if query.mode == TOOLS_MODE_COMPLETE_REVIEW:
        return build_complete_review_response(context)

    return _build_catalog_response(context)


def build_internal_tool_invocation(
    capability: str,
    context: CapabilityContext,
    action_definition: InternalActionDefinition,
    tool_definition: InternalToolDefinition,
) -> InternalToolInvocation:
    from .internal_tools_registry import InternalToolInvocation
    from .internal_sequences_registry import get_internal_sequence_definition

    sequence_name = action_definition.sequence_name
    sequence_definition = (
        get_internal_sequence_definition(sequence_name)
        if sequence_name is not None
        else None
    )
    adaptive_signals = resolve_adaptive_sequence_signals(sequence_name, context)

    return InternalToolInvocation(
        tool_definition=tool_definition,
        capability=capability,
        action_name=action_definition.name,
        action_category=action_definition.category,
        action_description=action_definition.description,
        action_examples=action_definition.examples,
        context=context,
        sequence_name=sequence_name,
        sequence_kind=sequence_definition.kind if sequence_definition is not None else None,
        sequence_goal=sequence_definition.goal if sequence_definition is not None else None,
        summary_mode=sequence_definition.summary_mode if sequence_definition is not None else None,
        adaptive_mode=(
            sequence_definition.adaptive_mode if sequence_definition is not None else None
        ),
        readiness_status=adaptive_signals.readiness_status,
        priority_focus=adaptive_signals.priority_focus,
        dominant_limitation=adaptive_signals.dominant_limitation,
        dominant_strength=adaptive_signals.dominant_strength,
        recommendation_level=adaptive_signals.recommendation_level,
        contextual_mode=adaptive_signals.contextual_mode,
        diagnostic_scope=adaptive_signals.diagnostic_scope,
        readiness_reason=adaptive_signals.readiness_reason,
        suggested_next_step=adaptive_signals.suggested_next_step,
        main_help_scope=adaptive_signals.main_help_scope,
        strategic_mode=adaptive_signals.strategic_mode,
        recommended_focus=adaptive_signals.recommended_focus,
        recommended_action=adaptive_signals.recommended_action,
        next_step_type=adaptive_signals.next_step_type,
        readiness_path=adaptive_signals.readiness_path,
        limitation_severity=adaptive_signals.limitation_severity,
        recommendation_style=adaptive_signals.recommendation_style,
        recommendation_priority=adaptive_signals.recommendation_priority,
        recommendation_basis=adaptive_signals.recommendation_basis,
        decision_focus=adaptive_signals.decision_focus,
        actionability_level=adaptive_signals.actionability_level,
        advice_scope=adaptive_signals.advice_scope,
        situational_profile=adaptive_signals.situational_profile,
        advice_frame=adaptive_signals.advice_frame,
        recommended_order=adaptive_signals.recommended_order,
        blocker_type=adaptive_signals.blocker_type,
        opportunity_focus=adaptive_signals.opportunity_focus,
        recovery_strategy=adaptive_signals.recovery_strategy,
        exploitation_path=adaptive_signals.exploitation_path,
        moment_profile=adaptive_signals.moment_profile,
        next_move_chain=adaptive_signals.next_move_chain,
        move_priority=adaptive_signals.move_priority,
        move_count=adaptive_signals.move_count,
        guidance_mode=adaptive_signals.guidance_mode,
        followup_trigger=adaptive_signals.followup_trigger,
        sequence_confidence=adaptive_signals.sequence_confidence,
        momentum_type=adaptive_signals.momentum_type,
        micro_plan=adaptive_signals.micro_plan,
        plan_horizon=adaptive_signals.plan_horizon,
        now_step=adaptive_signals.now_step,
        next_step=adaptive_signals.next_step,
        later_step=adaptive_signals.later_step,
        planning_mode=adaptive_signals.planning_mode,
        sequence_depth=adaptive_signals.sequence_depth,
        plan_confidence=adaptive_signals.plan_confidence,
        followup_priority=adaptive_signals.followup_priority,
        feasibility_status=adaptive_signals.feasibility_status,
        feasibility_reason=adaptive_signals.feasibility_reason,
        feasibility_scope=adaptive_signals.feasibility_scope,
        contradiction_detected=adaptive_signals.contradiction_detected,
        uncertainty_level=adaptive_signals.uncertainty_level,
        realism_level=adaptive_signals.realism_level,
        conditions_required=adaptive_signals.conditions_required,
        feasibility_frame=adaptive_signals.feasibility_frame,
        viability_basis=adaptive_signals.viability_basis,
        primary_constraint=adaptive_signals.primary_constraint,
        plausibility_mode=adaptive_signals.plausibility_mode,
        confidence_level=adaptive_signals.confidence_level,
        consistency_status=adaptive_signals.consistency_status,
        consistency_reason=adaptive_signals.consistency_reason,
        evidence_sufficiency=adaptive_signals.evidence_sufficiency,
        claim_strength=adaptive_signals.claim_strength,
        ambiguity_detected=adaptive_signals.ambiguity_detected,
        assumption_load=adaptive_signals.assumption_load,
        required_evidence=adaptive_signals.required_evidence,
        certainty_frame=adaptive_signals.certainty_frame,
        revision_trigger=adaptive_signals.revision_trigger,
        contextual_tension=adaptive_signals.contextual_tension,
        recent_context_conflict=adaptive_signals.recent_context_conflict,
        judgment_mode=adaptive_signals.judgment_mode,
    )


def execute_internal_tool(
    capability: str,
    context: CapabilityContext,
    action_definition: InternalActionDefinition,
    tool_definition: InternalToolDefinition,
) -> CapabilityExecution:
    invocation = build_internal_tool_invocation(
        capability=capability,
        context=context,
        action_definition=action_definition,
        tool_definition=tool_definition,
    )
    return tool_definition.handler(invocation)
