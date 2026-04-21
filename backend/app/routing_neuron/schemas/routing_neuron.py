"""Canonical schema helpers for Routing Neuron V1 lifecycle and semantics."""

from __future__ import annotations

from typing import Any

from agents.routing_neuron_registry import (
    PROMOTION_STAGES,
    PROMOTION_STAGE_SPECIALIZED_PROMPT,
    RoutingNeuronCandidate,
    RoutingPromotionRecommendation,
    ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
    ROUTING_CONFIDENCE_EARLY_SIGNAL,
    ROUTING_CONFIDENCE_SUSTAINED_VALUE,
)


ROUTING_LIFECYCLE_OBSERVED_PATTERN = "observed_pattern"
ROUTING_LIFECYCLE_CANDIDATE = "candidate"
ROUTING_LIFECYCLE_ACTIVE = "active"
ROUTING_LIFECYCLE_STABILIZED = "stabilized"
ROUTING_LIFECYCLE_PROMOTION_READY = "promotion_ready"
ROUTING_LIFECYCLE_PROMOTED = "promoted"
ROUTING_LIFECYCLE_PAUSED = "paused"
ROUTING_LIFECYCLE_RETIRED = "retired"

ROUTING_RUNTIME_BASE_STATES = (
    ROUTING_LIFECYCLE_OBSERVED_PATTERN,
    ROUTING_LIFECYCLE_CANDIDATE,
    ROUTING_LIFECYCLE_ACTIVE,
    ROUTING_LIFECYCLE_PAUSED,
)

ROUTING_DERIVED_ADMIN_STATES = (
    ROUTING_LIFECYCLE_STABILIZED,
    ROUTING_LIFECYCLE_PROMOTION_READY,
    ROUTING_LIFECYCLE_PROMOTED,
    ROUTING_LIFECYCLE_RETIRED,
)

ROUTING_LIFECYCLE_STATES = (
    ROUTING_LIFECYCLE_OBSERVED_PATTERN,
    ROUTING_LIFECYCLE_CANDIDATE,
    ROUTING_LIFECYCLE_ACTIVE,
    ROUTING_LIFECYCLE_STABILIZED,
    ROUTING_LIFECYCLE_PROMOTION_READY,
    ROUTING_LIFECYCLE_PROMOTED,
    ROUTING_LIFECYCLE_PAUSED,
    ROUTING_LIFECYCLE_RETIRED,
)

ROUTING_SIDE_STATES = (
    "paused",
    "retired",
    "demoted",
)

ROUTING_PRIMARY_SCORE_AXES = (
    "efficiency_score",
    "stability_score",
    "quality_score",
    "reusability_score",
    "global_routing_score",
)

ROUTING_SECONDARY_SIGNAL_LABELS = (
    "confidence_tier",
    "stability_label",
    "readiness_band",
    "influence_readiness",
)


def normalize_neuron_type_label(neuron_type: str | None) -> str:
    return {
        "selection": "Selection",
        "transformation": "Transformation",
        "control": "Control",
    }.get(neuron_type or "", neuron_type or "Unknown")


def normalize_confidence_label(confidence_tier: str | None) -> str:
    return {
        ROUTING_CONFIDENCE_EARLY_SIGNAL: "señal temprana",
        ROUTING_CONFIDENCE_CONFIRMED_PATTERN: "patrón confirmado",
        ROUTING_CONFIDENCE_SUSTAINED_VALUE: "confianza estable",
    }.get(confidence_tier or "", confidence_tier or "sin señal")


def derive_lifecycle_state(subject: Any) -> str:
    if getattr(subject, "discardable_flag", False) or getattr(subject, "launch_status", None) == "rejected":
        return ROUTING_LIFECYCLE_RETIRED

    if getattr(subject, "neuron_state", None) == "paused":
        return ROUTING_LIFECYCLE_PAUSED

    if (
        getattr(subject, "promotion_stage", None)
        and getattr(subject, "promotion_stage", None) != PROMOTION_STAGE_SPECIALIZED_PROMPT
    ):
        return ROUTING_LIFECYCLE_PROMOTED

    if getattr(subject, "promotion_ready_signal", False) or getattr(subject, "readiness_band", None) == "near_ready":
        return ROUTING_LIFECYCLE_PROMOTION_READY

    if (
        getattr(subject, "neuron_state", None) == "active"
        and getattr(subject, "confidence_tier", None) == ROUTING_CONFIDENCE_SUSTAINED_VALUE
        and getattr(subject, "stability_label", None) in {"stable", "improving"}
    ):
        return ROUTING_LIFECYCLE_STABILIZED

    if getattr(subject, "neuron_state", None) == "active":
        return ROUTING_LIFECYCLE_ACTIVE

    if getattr(subject, "neuron_state", None) == "candidate":
        return ROUTING_LIFECYCLE_CANDIDATE

    return ROUTING_LIFECYCLE_OBSERVED_PATTERN


def derive_side_state(subject: Any) -> str | None:
    if derive_lifecycle_state(subject) == ROUTING_LIFECYCLE_PAUSED:
        return "paused"

    if derive_lifecycle_state(subject) == ROUTING_LIFECYCLE_RETIRED:
        return "retired"

    if (
        getattr(subject, "stability_label", None) in {"fragile", "degrading"}
        and getattr(subject, "selection_status", None) in {"hold", "discardable"}
    ):
        return "demoted"

    return None


def derive_activation_barriers(subject: Any) -> tuple[str, ...]:
    barriers: list[str] = []

    if getattr(subject, "neuron_state", None) != "active":
        barriers.append("state")

    if getattr(subject, "estimated_cost", 0.0) > 0.65:
        barriers.append("budget")

    if getattr(subject, "selection_status", None) in {"observed_only", "hold"}:
        barriers.append("context")

    if getattr(subject, "recent_conflict_count", 0) > 0:
        barriers.append("competitive")

    if getattr(subject, "stability_label", None) in {"fragile", "degrading"}:
        barriers.append("stability")

    if len(getattr(subject, "activated_components", ())) >= 3 or getattr(subject, "dependency_hints", ()):
        barriers.append("composition")

    if getattr(subject, "recent_fallback_count", 0) > 0 or getattr(subject, "fallback_target", None):
        barriers.append("fallback")

    return tuple(barriers)


__all__ = [
    "PROMOTION_STAGES",
    "RoutingNeuronCandidate",
    "RoutingPromotionRecommendation",
    "ROUTING_DERIVED_ADMIN_STATES",
    "ROUTING_LIFECYCLE_ACTIVE",
    "ROUTING_LIFECYCLE_CANDIDATE",
    "ROUTING_LIFECYCLE_OBSERVED_PATTERN",
    "ROUTING_LIFECYCLE_PAUSED",
    "ROUTING_LIFECYCLE_PROMOTION_READY",
    "ROUTING_LIFECYCLE_PROMOTED",
    "ROUTING_LIFECYCLE_RETIRED",
    "ROUTING_LIFECYCLE_STABILIZED",
    "ROUTING_LIFECYCLE_STATES",
    "ROUTING_PRIMARY_SCORE_AXES",
    "ROUTING_RUNTIME_BASE_STATES",
    "ROUTING_SECONDARY_SIGNAL_LABELS",
    "ROUTING_SIDE_STATES",
    "derive_activation_barriers",
    "derive_lifecycle_state",
    "derive_side_state",
    "normalize_confidence_label",
    "normalize_neuron_type_label",
]
