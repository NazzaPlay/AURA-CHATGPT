"""Observable replay helpers for Routing Neuron V1.x surfaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH = "no_candidate_match"
ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE = "candidate_seen_no_active_match"
ROUTING_RUNTIME_PATH_SELECTED_PAUSED = "selected_paused"
ROUTING_RUNTIME_PATH_SELECTED_COOLDOWN = "selected_cooldown"
ROUTING_RUNTIME_PATH_SELECTED_BLOCKED = "selected_blocked"
ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED = "selected_not_applied"
ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED = "selected_and_applied"


@dataclass(frozen=True)
class ObservableRoutingTurn:
    decision: str | None
    decision_path: str | None
    applied: bool
    considered: bool
    considered_ids: tuple[str, ...]
    selected: bool
    neuron_id: str | None
    neuron_state: str | None
    influence: str | None
    fallback_reason: str | None
    outcome_label: str | None
    barriers_blocked: tuple[str, ...]
    provider_result_status: str | None
    fallback_used: bool


@dataclass(frozen=True)
class ObservableRoutingSummary:
    source_mode: str
    source_label: str
    total_decisions: int
    considered_decisions: int
    selected_decisions: int
    applied_decisions: int
    selected_not_applied_decisions: int
    blocked_decisions: int
    fallback_decisions: int
    degraded_decisions: int
    no_signal_decisions: int
    no_candidate_decisions: int
    recent_paths: tuple[str, ...]
    recent_outcomes: tuple[str, ...]
    recent_applied_influences: tuple[str, ...]
    recent_activity: tuple[str, ...]


def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _normalize_text_tuple(value: Any) -> tuple[str, ...]:
    if value in (None, "", False):
        return ()

    if isinstance(value, (list, tuple, set)):
        return tuple(
            text
            for item in value
            if (text := _normalize_optional_text(item)) is not None
        )

    text = _normalize_optional_text(value)
    return (text,) if text is not None else ()


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "si", "sí"}

    return bool(value)


def _resolve_visible_log_path(log_file: str | None) -> Path | None:
    if not log_file:
        return None

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


def _iter_visible_log_paths(log_file: str | None) -> tuple[Path, ...]:
    resolved_log_path = _resolve_visible_log_path(log_file)
    if resolved_log_path is None:
        return ()

    current_log_path = Path(log_file) if log_file else None
    log_dir = resolved_log_path.parent
    ordered_candidates: list[Path] = []
    seen: set[Path] = set()

    if current_log_path is not None and current_log_path.exists():
        ordered_candidates.append(current_log_path)
        seen.add(current_log_path)

    if resolved_log_path.exists() and resolved_log_path not in seen:
        ordered_candidates.append(resolved_log_path)
        seen.add(resolved_log_path)

    for candidate in sorted(
        log_dir.glob("session_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    ):
        if candidate in seen:
            continue
        ordered_candidates.append(candidate)
        seen.add(candidate)

    return tuple(ordered_candidates)


def build_observable_routing_turn(metadata: Any) -> ObservableRoutingTurn | None:
    if not isinstance(metadata, dict):
        return None

    decision = _normalize_optional_text(metadata.get("routing_neuron_decision"))
    decision_path = _normalize_optional_text(metadata.get("routing_neuron_decision_path"))
    applied = _normalize_bool(metadata.get("routing_neuron_applied"))
    considered = _normalize_bool(metadata.get("routing_neuron_considered"))
    considered_ids = _normalize_text_tuple(metadata.get("routing_neuron_considered_ids"))
    selected = _normalize_bool(metadata.get("routing_neuron_selected"))
    neuron_id = _normalize_optional_text(metadata.get("routing_neuron_id"))
    neuron_state = _normalize_optional_text(metadata.get("routing_neuron_state"))
    influence = _normalize_optional_text(metadata.get("routing_neuron_influence"))
    fallback_reason = _normalize_optional_text(metadata.get("routing_neuron_fallback_reason"))
    outcome_label = _normalize_optional_text(metadata.get("routing_neuron_outcome_label"))
    barriers_blocked = _normalize_text_tuple(metadata.get("routing_neuron_barriers_blocked"))
    provider_result_status = _normalize_optional_text(metadata.get("provider_result_status"))
    fallback_used = _normalize_bool(metadata.get("fallback_used"))

    if not any(
        (
            decision,
            decision_path,
            applied,
            considered,
            considered_ids,
            selected,
            neuron_id,
            influence,
            fallback_reason,
            outcome_label,
            barriers_blocked,
            provider_result_status,
            fallback_used,
        )
    ):
        return None

    return ObservableRoutingTurn(
        decision=decision,
        decision_path=decision_path,
        applied=applied,
        considered=considered,
        considered_ids=considered_ids,
        selected=selected,
        neuron_id=neuron_id,
        neuron_state=neuron_state,
        influence=influence,
        fallback_reason=fallback_reason,
        outcome_label=outcome_label,
        barriers_blocked=barriers_blocked,
        provider_result_status=provider_result_status,
        fallback_used=fallback_used,
    )


def extract_observable_routing_turns(messages: list[dict[str, Any]]) -> tuple[ObservableRoutingTurn, ...]:
    turns: list[ObservableRoutingTurn] = []

    for message in messages:
        if message.get("role") != "aura":
            continue

        turn = build_observable_routing_turn(message.get("metadata"))
        if turn is not None:
            turns.append(turn)

    return tuple(turns)


def describe_observable_considered_scope(turn: ObservableRoutingTurn) -> str | None:
    if not turn.considered:
        return None

    if turn.considered_ids:
        if len(turn.considered_ids) == 1:
            return f"considerada {turn.considered_ids[0]}"
        return f"consideradas {_format_items(list(turn.considered_ids[:3]))}"

    if turn.decision_path == ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH:
        return "considerada globalmente sin candidata coincidente"

    if turn.decision_path == ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE:
        return "considerada con candidata vista, pero no activa"

    return "considerada sin candidata aplicable"


def describe_observable_routing_turn(turn: ObservableRoutingTurn) -> str:
    lead = "applied" if turn.applied else (turn.decision or "observed")
    details: list[str] = []

    if turn.decision_path:
        details.append(f"path {visible_decision_path_label(turn.decision_path)}")
    if turn.influence:
        details.append(f"influencia {turn.influence}")
    considered_scope = describe_observable_considered_scope(turn)
    if considered_scope:
        details.append(considered_scope)
    if turn.selected and turn.neuron_id:
        details.append(f"selección {turn.neuron_id}")
    elif turn.neuron_id and turn.neuron_state:
        details.append(f"neurona {turn.neuron_id} ({turn.neuron_state})")
    if turn.barriers_blocked:
        details.append(f"barriers {_format_items(list(turn.barriers_blocked))}")
    if turn.fallback_reason:
        details.append(f"fallback {turn.fallback_reason}")
    if turn.outcome_label:
        details.append(f"outcome {turn.outcome_label}")

    if not details:
        return lead

    return f"{lead} ({', '.join(details)})"


def is_observable_degraded(turn: ObservableRoutingTurn) -> bool:
    if turn.provider_result_status in {"error", "unavailable"}:
        return True

    outcome_label = (turn.outcome_label or "").casefold()
    return outcome_label.startswith("fallback_")


def summarize_observable_routing_turns(
    turns: tuple[ObservableRoutingTurn, ...],
    *,
    source_mode: str,
    source_label: str,
) -> ObservableRoutingSummary:
    recent_turns = turns[-3:]
    selected_not_applied_paths = {
        ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED,
    }
    blocked_paths = {
        ROUTING_RUNTIME_PATH_SELECTED_BLOCKED,
        ROUTING_RUNTIME_PATH_SELECTED_PAUSED,
        ROUTING_RUNTIME_PATH_SELECTED_COOLDOWN,
    }

    return ObservableRoutingSummary(
        source_mode=source_mode,
        source_label=source_label,
        total_decisions=len(turns),
        considered_decisions=sum(1 for turn in turns if turn.considered),
        selected_decisions=sum(1 for turn in turns if turn.selected),
        applied_decisions=sum(1 for turn in turns if turn.applied),
        selected_not_applied_decisions=sum(
            1
            for turn in turns
            if turn.decision_path in selected_not_applied_paths
        ),
        blocked_decisions=sum(
            1
            for turn in turns
            if turn.decision_path in blocked_paths
            or bool(turn.barriers_blocked)
            or turn.decision == "blocked_by_barrier"
        ),
        fallback_decisions=sum(1 for turn in turns if turn.fallback_reason is not None),
        degraded_decisions=sum(1 for turn in turns if is_observable_degraded(turn)),
        no_signal_decisions=sum(1 for turn in turns if turn.decision == "no_signal"),
        no_candidate_decisions=sum(
            1
            for turn in turns
            if turn.decision_path == ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH
        ),
        recent_paths=tuple(
            turn.decision_path
            for turn in recent_turns
            if turn.decision_path is not None
        ),
        recent_outcomes=tuple(
            f"{turn.outcome_label or 'unknown'}:{turn.decision or 'unknown'}"
            for turn in recent_turns
        ),
        recent_applied_influences=tuple(
            f"{turn.influence or 'none'}:{turn.outcome_label or 'unknown'}"
            for turn in recent_turns
            if turn.applied
        ),
        recent_activity=tuple(
            describe_observable_routing_turn(turn)
            for turn in recent_turns
        ),
    )


def load_observable_routing_summary(
    conversation: list[dict[str, Any]] | None,
    log_file: str | None,
) -> ObservableRoutingSummary | None:
    if conversation:
        turns = extract_observable_routing_turns(conversation)
        if turns:
            return summarize_observable_routing_turns(
                turns,
                source_mode="conversation",
                source_label="la sesión actual",
            )

    current_log_path = Path(log_file) if log_file else None
    for log_path in _iter_visible_log_paths(log_file):
        try:
            with open(log_path, "r", encoding="utf-8") as handle:
                messages = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(messages, list):
            continue

        turns = extract_observable_routing_turns(messages)
        if not turns:
            continue

        is_current_log = current_log_path is not None and log_path == current_log_path and log_path.exists()
        source_mode = "current_log" if is_current_log else "last_session_log"
        source_label = (
            f"la sesión registrada {log_path.name}"
            if is_current_log
            else f"la última sesión registrada ({log_path.name})"
        )
        return summarize_observable_routing_turns(
            turns,
            source_mode=source_mode,
            source_label=source_label,
        )

    return None


def visible_decision_path_label(path: str) -> str:
    return {
        ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH: "sin candidata coincidente (no_candidate_match)",
        ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE: "candidata vista pero no activa (candidate_seen_no_active_match)",
        ROUTING_RUNTIME_PATH_SELECTED_BLOCKED: "seleccionada bloqueada (selected_blocked)",
        ROUTING_RUNTIME_PATH_SELECTED_PAUSED: "seleccionada pausada (selected_paused)",
        ROUTING_RUNTIME_PATH_SELECTED_COOLDOWN: "seleccionada en cooldown (selected_cooldown)",
        ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED: "seleccionada sin aplicar (selected_not_applied)",
        ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED: "seleccionada y aplicada (selected_and_applied)",
    }.get(path, path)


def format_visible_decision_paths(paths: tuple[str, ...]) -> str:
    return _format_items([visible_decision_path_label(path) for path in paths])


def resolve_observable_activity_label(summary: ObservableRoutingSummary) -> str:
    if summary.applied_decisions > 0:
        if summary.total_decisions <= 2:
            return "actividad aplicada visible con muestra baja"
        return "actividad aplicada visible"

    if summary.blocked_decisions > 0 or summary.selected_not_applied_decisions > 0:
        return "actividad visible sin aplicar cambios"

    if summary.no_signal_decisions > 0 or summary.no_candidate_decisions > 0:
        return "señal débil visible"

    if summary.fallback_decisions > 0 or summary.degraded_decisions > 0:
        return "actividad fallback visible"

    return "traza visible"


def resolve_observable_source_phrase(summary: ObservableRoutingSummary) -> str:
    if summary.source_mode == "conversation":
        return "de la sesión actual"

    if summary.source_mode == "current_log":
        return "recuperada del log actual"

    return "recuperada de la última sesión registrada"


def format_observable_runtime_prefix(summary: ObservableRoutingSummary) -> str:
    return (
        "sin historial runtime en memoria, con "
        f"{resolve_observable_activity_label(summary)} "
        f"{resolve_observable_source_phrase(summary)}"
    )


def format_observable_runtime_shadow(
    summary: ObservableRoutingSummary,
    *,
    include_source_label: bool = True,
) -> str:
    parts: list[str] = []

    if include_source_label:
        parts.append(f"traza visible de {summary.source_label}")

    parts.append(
        f"observó {summary.total_decisions}, "
        f"influyó {summary.applied_decisions}, "
        f"consideradas {summary.considered_decisions}, "
        f"seleccionadas {summary.selected_decisions}, "
        f"seleccionadas sin aplicar {summary.selected_not_applied_decisions}, "
        f"bloqueadas {summary.blocked_decisions}, "
        f"fallback {summary.fallback_decisions}, "
        f"degradado {summary.degraded_decisions}, "
        f"no_signal {summary.no_signal_decisions}, "
        f"sin candidata {summary.no_candidate_decisions}"
    )

    text = "; ".join(parts)

    if summary.recent_applied_influences:
        text += f", applied recientes {_format_items(list(summary.recent_applied_influences[:3]))}"
    if summary.recent_paths:
        text += f", rutas recientes {format_visible_decision_paths(summary.recent_paths[:3])}"
    if summary.recent_outcomes:
        text += f", recientes {_format_items(list(summary.recent_outcomes[:3]))}"
    if summary.recent_activity:
        text += f", actividad {_format_items(list(summary.recent_activity[-2:]))}"

    return text


def format_observable_recent_decisions(summary: ObservableRoutingSummary) -> str:
    if summary.recent_activity:
        return _format_items(list(summary.recent_activity[-2:]))

    if summary.recent_paths:
        return format_visible_decision_paths(summary.recent_paths[:3])

    return format_observable_runtime_shadow(summary)


__all__ = [
    "ObservableRoutingSummary",
    "ObservableRoutingTurn",
    "format_observable_recent_decisions",
    "format_observable_runtime_prefix",
    "format_observable_runtime_shadow",
    "format_visible_decision_paths",
    "load_observable_routing_summary",
    "resolve_observable_activity_label",
    "resolve_observable_source_phrase",
    "visible_decision_path_label",
]
