"""Canonical rendering helpers for Routing Neuron admin and visible surfaces."""

from __future__ import annotations

from typing import Any

from .observable import (
    ObservableRoutingSummary,
    format_observable_runtime_prefix,
    format_observable_runtime_shadow,
    format_visible_decision_paths,
)


def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def runtime_observability_label(status: str, runtime_status: Any | None = None) -> str:
    if status == "runtime_ready_but_no_history":
        return "runtime preparado, todavía sin historial reciente"

    if status == "only_no_signal_seen":
        if runtime_status is not None and runtime_status.no_candidate_decisions >= runtime_status.total_decisions:
            return "señal débil observada, sin candidatas coincidentes recientes"
        return "señal débil observada, todavía sin influencia aplicable"

    if status == "blocked_or_baseline_only":
        if runtime_status is not None:
            blocked = getattr(runtime_status, "blocked_decisions", 0)
            selected_not_applied = getattr(runtime_status, "selected_not_applied_decisions", 0)
            if blocked > 0 and selected_not_applied == blocked:
                return "actividad bloqueada observada, sin aplicar cambios"
            if selected_not_applied > 0 and blocked == 0:
                return "actividad baseline-only observada, sin aplicar cambios"
            if selected_not_applied > 0 or blocked > 0:
                return "actividad sin aplicación observada, entre baseline y bloqueos"
        return "actividad sin aplicación observada"

    return {
        "healthy_but_low_sample": "actividad aplicada observada con muestra baja",
        "applied_activity_observed": "actividad aplicada observada",
    }.get(status, status)


def runtime_validation_label(status: str) -> str:
    return {
        "runtime_validation_in_progress": "validación operativa en progreso",
        "baseline_only_validation": "validación operativa sin intervención aplicada todavía",
        "runtime_validation_low_sample": "validación operativa con muestra baja",
        "runtime_behavior_observed": "validación operativa con intervención ya observada",
    }.get(status, status)


def runtime_validation_state_text(status: str) -> str:
    return {
        "runtime_validation_in_progress": "en progreso",
        "baseline_only_validation": "sin intervención aplicada todavía",
        "runtime_validation_low_sample": "con muestra baja",
        "runtime_behavior_observed": "ya observada con intervención",
    }.get(status, status.replace("_", " "))


def runtime_history_mode_label(
    runtime_status: Any,
    observable_summary: ObservableRoutingSummary | None = None,
) -> str:
    if getattr(runtime_status, "total_decisions", 0) > 0:
        return "historial runtime vivo en memoria"

    if observable_summary is None:
        return "sin historial runtime ni replay visible"

    if observable_summary.source_mode == "conversation":
        return "traza visible de la sesión actual"

    if observable_summary.source_mode == "current_log":
        return "replay visible del log actual"

    return "replay visible de la última sesión útil"


def format_runtime_status(
    runtime_status: Any,
    observable_summary: ObservableRoutingSummary | None = None,
    *,
    compact: bool = False,
) -> str:
    if runtime_status.total_decisions == 0 and observable_summary is not None:
        return (
            f"{format_observable_runtime_prefix(observable_summary)}; "
            f"{format_observable_runtime_shadow(observable_summary, include_source_label=False)}"
        )

    summary = (
        f"{runtime_observability_label(runtime_status.observability_status, runtime_status)}, "
        f"{runtime_validation_label(runtime_status.validation_status)}"
    )

    if runtime_status.total_decisions == 0:
        return summary

    if compact:
        summary += (
            f"; ventana runtime {runtime_status.total_decisions}/{runtime_status.history_window_limit}, "
            f"influyó {runtime_status.applied_decisions}, "
            f"applied {runtime_status.applied_decisions}, "
            f"fallback {runtime_status.fallback_decisions}, "
            f"bloqueadas {runtime_status.blocked_decisions}, "
            f"no_signal {runtime_status.no_signal_decisions}"
        )
        if runtime_status.recent_paths:
            summary += (
                ", rutas "
                f"{format_visible_decision_paths(runtime_status.recent_paths[-2:])}"
            )
        if runtime_status.recent_applied_influences:
            summary += (
                ", applied recientes "
                f"{_format_items(list(runtime_status.recent_applied_influences[-2:]))}"
            )
        if runtime_status.recent_outcomes:
            summary += f", recientes {_format_items(list(runtime_status.recent_outcomes[-2:]))}"
        return summary

    summary += (
        f"; ventana runtime {runtime_status.total_decisions}/{runtime_status.history_window_limit}, "
        f"observó {runtime_status.total_decisions}, "
        f"influyó {runtime_status.applied_decisions}, "
        f"consideradas {runtime_status.considered_decisions}, "
        f"seleccionadas {runtime_status.selected_decisions}, "
        f"seleccionadas sin aplicar {runtime_status.selected_not_applied_decisions}, "
        f"bloqueadas {runtime_status.blocked_decisions}, "
        f"fallback {runtime_status.fallback_decisions}, "
        f"degradado {runtime_status.degraded_decisions}, "
        f"no_signal {runtime_status.no_signal_decisions}, "
        f"sin candidata {runtime_status.no_candidate_decisions}, "
        f"paused {runtime_status.paused_decisions}, "
        f"cooldown {runtime_status.cooldown_decisions}"
    )
    if runtime_status.frequent_barriers:
        summary += f", barreras {_format_items(list(runtime_status.frequent_barriers))}"
    if runtime_status.frequent_fallbacks:
        summary += f", fallbacks {_format_items(list(runtime_status.frequent_fallbacks))}"
    if runtime_status.frequent_outcomes:
        summary += f", outcomes {_format_items(list(runtime_status.frequent_outcomes))}"
    if runtime_status.recent_applied_influences:
        summary += f", applied recientes {_format_items(list(runtime_status.recent_applied_influences[-3:]))}"
    if runtime_status.recent_paths:
        summary += f", rutas recientes {format_visible_decision_paths(runtime_status.recent_paths[-3:])}"
    if runtime_status.recent_outcomes:
        summary += f", recientes {_format_items(list(runtime_status.recent_outcomes[-3:]))}"
    return summary


__all__ = [
    "format_runtime_status",
    "runtime_history_mode_label",
    "runtime_observability_label",
    "runtime_validation_label",
    "runtime_validation_state_text",
]
