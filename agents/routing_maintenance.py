"""Legacy Routing Neuron maintenance backplane for AURA compatibility.

The canonical runtime, observer, admin rendering, and observable replay logic
live under ``backend.app.routing_neuron``. This module still hosts the
historical maintenance and repertoire structures while V1.x incrementally
reduces legacy coupling without breaking current AURA integrations.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace

from backend.app.routing_neuron.admin.observable import visible_decision_path_label

from .routing_neuron_registry import (
    ACTION_OUTCOME_HELPED,
    ACTION_OUTCOME_NO_CLEAR_CHANGE,
    ACTION_OUTCOME_PENDING_OBSERVATION,
    ACTION_OUTCOME_WORSENED,
    ALERT_STATUS_ACKNOWLEDGED,
    ALERT_STATUS_NONE,
    ALERT_STATUS_OPEN,
    ALERT_STATUS_REOPENED,
    ALERT_STATUS_RESOLVED,
    DEFAULT_COOLDOWN_TURNS,
    MIN_ACTIVE_FREQUENCY,
    MIN_ACTIVE_ROUTING_SCORE,
    PROMOTION_STAGE_ADAPTER,
    PROMOTION_STAGE_MICRO_MODEL,
    PROMOTION_STAGE_SPECIALIZED_PROMPT,
    ROUTING_BRIDGE_PREFLIGHT_BLOCKED,
    ROUTING_BRIDGE_PREFLIGHT_CANDIDATE,
    ROUTING_BRIDGE_PREFLIGHT_DEFERRED,
    ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED,
    ROUTING_BRIDGE_PREFLIGHT_READY,
    ROUTING_CUTOVER_BLOCKED,
    ROUTING_CUTOVER_GO_CANDIDATE,
    ROUTING_CUTOVER_NEAR_GO,
    ROUTING_CUTOVER_NOT_READY,
    ROUTING_CUTOVER_WATCH,
    ROUTING_LAUNCH_APPROVED,
    ROUTING_LAUNCH_HOLD,
    ROUTING_LAUNCH_NONE,
    ROUTING_LAUNCH_REJECTED,
    ROUTING_LAUNCH_SUPPORT_ONLY,
    ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
    ROUTING_CONFIDENCE_EARLY_SIGNAL,
    ROUTING_CONFIDENCE_SUSTAINED_VALUE,
    ROUTING_CURATION_DISCARDABLE,
    ROUTING_CURATION_NOISY,
    ROUTING_CURATION_PROMISING,
    ROUTING_CURATION_USEFUL,
    ROUTING_INFLUENCE_BRIDGE_WATCH,
    ROUTING_INFLUENCE_EMERGING,
    ROUTING_INFLUENCE_NOT_READY,
    ROUTING_INFLUENCE_SHORTLIST_READY,
    ROUTING_READINESS_EMERGING,
    ROUTING_READINESS_NEAR_READY,
    ROUTING_READINESS_NOT_READY,
    ROUTING_READINESS_WATCH,
    ROUTING_REHEARSAL_BLOCKED,
    ROUTING_REHEARSAL_CANDIDATE,
    ROUTING_REHEARSAL_DEFERRED,
    ROUTING_REHEARSAL_NOT_IN_REHEARSAL,
    ROUTING_REHEARSAL_READY,
    ROUTING_REVIEW_PRIORITY_HIGH,
    ROUTING_REVIEW_PRIORITY_LOW,
    ROUTING_REVIEW_PRIORITY_MEDIUM,
    ROUTING_REVIEW_PRIORITY_NONE,
    ROUTING_ROLE_CONTEXT_FILTER,
    ROUTING_ROLE_CRITIC_SUPPORT,
    ROUTING_ROLE_MIGRATION_GUARD,
    ROUTING_ROLE_NONE,
    ROUTING_ROLE_PRIMARY_SUPPORT,
    ROUTING_ROLE_ROUTER_SUPPORT,
    ROUTING_ROLE_SAFETY_CHECK,
    REVIEW_STATUS_NONE,
    REVIEW_STATUS_OPEN,
    REVIEW_STATUS_REOPENED,
    REVIEW_STATUS_RESOLVED,
    REVIEW_STATUS_STALE,
    REVIEW_STATUS_WATCH,
    ROUTING_SELECTION_DISCARDABLE,
    ROUTING_SELECTION_HOLD,
    ROUTING_SELECTION_OBSERVED_ONLY,
    ROUTING_SELECTION_SHORTLISTED,
    ROUTING_STACK_FIT_GRANITE,
    ROUTING_STACK_FIT_NEUTRAL,
    ROUTING_STACK_FIT_OLMO,
    ROUTING_STACK_FIT_SMOLLM2,
    ROUTING_STATE_ACTIVE,
    ROUTING_STATE_PAUSED,
    ROUTING_STABILITY_DEGRADING,
    ROUTING_STABILITY_FRAGILE,
    ROUTING_STABILITY_IMPROVING,
    ROUTING_STABILITY_OBSERVING,
    ROUTING_STABILITY_STABLE,
    ROUTING_TYPE_CONTROL,
    ROUTING_TYPE_SELECTION,
    ROUTING_TYPE_TRANSFORMATION,
    ROUTING_RUNTIME_HISTORY_LIMIT,
    RoutingNeuronCandidate,
    RoutingNeuronRegistry,
    RoutingPromotionRecommendation,
    SessionRoutingSummary,
)
from .routing_scorer import build_routing_score


ROUTING_RUNTIME_OBSERVABILITY_NO_HISTORY = "runtime_ready_but_no_history"
ROUTING_RUNTIME_OBSERVABILITY_ONLY_NO_SIGNAL = "only_no_signal_seen"
ROUTING_RUNTIME_OBSERVABILITY_BLOCKED_ONLY = "blocked_or_baseline_only"
ROUTING_RUNTIME_OBSERVABILITY_LOW_SAMPLE = "healthy_but_low_sample"
ROUTING_RUNTIME_OBSERVABILITY_OBSERVED = "applied_activity_observed"

ROUTING_RUNTIME_VALIDATION_IN_PROGRESS = "runtime_validation_in_progress"
ROUTING_RUNTIME_VALIDATION_BASELINE_ONLY = "baseline_only_validation"
ROUTING_RUNTIME_VALIDATION_LOW_SAMPLE = "runtime_validation_low_sample"
ROUTING_RUNTIME_VALIDATION_OBSERVED = "runtime_behavior_observed"


@dataclass(frozen=True)
class RoutingRepertoireEntry:
    neuron_id: str
    neuron_state: str
    neuron_type: str
    promotion_stage: str
    activated_components: tuple[str, ...]
    estimated_cost: float
    efficiency_score: float
    stability_score: float
    quality_score: float
    reusability_score: float
    global_routing_score: float
    confidence_tier: str
    stability_label: str
    trend_label: str
    cooldown_turns_remaining: int
    successful_activations: int
    failed_activations: int
    baseline_win_count: int
    recent_fallback_count: int
    stable_activation_streak: int
    recent_conflict_count: int
    times_applied: int
    last_decision: str | None
    last_used_at: str | None
    alerts: tuple[str, ...]
    promotion_ready_signal: bool
    readiness_band: str
    readiness_reason: str | None
    curation_status: str
    curation_reason: str | None
    selection_status: str
    selection_reason: str | None
    influence_readiness: str
    influence_reason: str | None
    bridge_preflight_status: str
    bridge_priority: str
    bridge_rationale: str | None
    bridge_blockers: tuple[str, ...]
    conceptual_role_fit: tuple[str, ...]
    conceptual_fit_reason: str | None
    bridge_rehearsal_status: str
    rehearsal_priority: str
    rehearsal_rationale: str | None
    rehearsal_blockers: tuple[str, ...]
    cutover_readiness: str
    cutover_rationale: str | None
    rollback_concerns: tuple[str, ...]
    launch_status: str
    launch_rationale: str | None
    cutover_role: str
    cutover_role_reason: str | None
    activation_order: int | None
    activation_order_reason: str | None
    dependency_hints: tuple[str, ...]
    rollback_triggers: tuple[str, ...]
    fallback_target: str | None
    safe_reversion: str | None
    no_go_conditions: tuple[str, ...]
    watch_status: bool
    watch_reason: str | None
    review_priority: str
    review_reason: str | None
    review_status: str
    alert_status: str
    action_outcome: str | None
    action_outcome_reason: str | None
    stale_flag: bool
    discardable_flag: bool
    action_suggestion: str | None
    last_admin_action: str | None
    last_admin_reason: str | None
    recommendation_stage: str | None


@dataclass(frozen=True)
class RoutingRepertoireSnapshot:
    observed_patterns: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    active_ids: tuple[str, ...]
    paused_ids: tuple[str, ...]
    activation_count: int
    alerts: tuple[str, ...]
    recommendation_ids: tuple[str, ...]
    recent_conflicts: tuple[str, ...]
    entries: tuple[RoutingRepertoireEntry, ...]
    recent_activity: tuple[str, ...]
    runtime_record_count: int
    runtime_considered_count: int
    runtime_selected_count: int
    runtime_applied_count: int
    runtime_selected_not_applied_count: int
    runtime_blocked_count: int
    runtime_fallback_count: int
    runtime_degraded_count: int
    runtime_no_signal_count: int
    runtime_no_candidate_count: int
    runtime_paused_count: int
    runtime_cooldown_count: int
    runtime_history_window_limit: int
    runtime_observability_status: str
    runtime_validation_status: str
    runtime_considered_ids: tuple[str, ...]
    runtime_applied_ids: tuple[str, ...]
    runtime_blocked_ids: tuple[str, ...]
    runtime_barrier_hotspots: tuple[str, ...]
    runtime_fallback_hotspots: tuple[str, ...]
    runtime_outcome_hotspots: tuple[str, ...]
    runtime_recent_decisions: tuple[str, ...]
    runtime_recent_paths: tuple[str, ...]
    runtime_recent_outcomes: tuple[str, ...]
    runtime_recent_applied_influences: tuple[str, ...]
    top_score_ids: tuple[str, ...]
    top_confidence_ids: tuple[str, ...]
    top_stability_ids: tuple[str, ...]
    alerted_ids: tuple[str, ...]
    cooldown_ids: tuple[str, ...]
    readiness_ids: tuple[str, ...]
    watch_ids: tuple[str, ...]
    review_queue_ids: tuple[str, ...]
    recent_admin_actions: tuple[str, ...]
    open_review_ids: tuple[str, ...]
    resolved_review_ids: tuple[str, ...]
    stale_ids: tuple[str, ...]
    reopened_ids: tuple[str, ...]
    reopened_alert_ids: tuple[str, ...]
    helped_ids: tuple[str, ...]
    useful_ids: tuple[str, ...]
    shortlist_ids: tuple[str, ...]
    observed_only_ids: tuple[str, ...]
    discardable_ids: tuple[str, ...]
    bridge_ready_ids: tuple[str, ...]
    bridge_slate_ids: tuple[str, ...]
    bridge_blocked_ids: tuple[str, ...]
    bridge_deferred_ids: tuple[str, ...]
    rehearsal_ready_ids: tuple[str, ...]
    rehearsal_slate_ids: tuple[str, ...]
    rehearsal_blocked_ids: tuple[str, ...]
    rehearsal_deferred_ids: tuple[str, ...]
    cutover_near_go_ids: tuple[str, ...]
    cutover_go_candidate_ids: tuple[str, ...]
    rollback_risk_ids: tuple[str, ...]
    stack_fit_ids: tuple[str, ...]
    approved_ids: tuple[str, ...]
    support_only_ids: tuple[str, ...]
    hold_ids: tuple[str, ...]
    rejected_ids: tuple[str, ...]
    launch_slate_ids: tuple[str, ...]
    activation_order_ids: tuple[str, ...]


@dataclass(frozen=True)
class RoutingLaunchDossierEntry:
    neuron_id: str
    neuron_type: str
    promotion_stage: str
    launch_status: str
    launch_rationale: str | None
    cutover_role: str
    cutover_role_reason: str | None
    activation_order: int | None
    activation_order_reason: str | None
    dependency_hints: tuple[str, ...]
    rollback_triggers: tuple[str, ...]
    fallback_target: str | None
    safe_reversion: str | None
    no_go_conditions: tuple[str, ...]
    bridge_preflight_status: str
    bridge_rehearsal_status: str
    cutover_readiness: str
    conceptual_role_fit: tuple[str, ...]
    rollback_concerns: tuple[str, ...]
    global_routing_score: float
    confidence_tier: str
    stability_label: str


@dataclass(frozen=True)
class RoutingLaunchDossier:
    entries: tuple[RoutingLaunchDossierEntry, ...]
    approved_ids: tuple[str, ...]
    support_only_ids: tuple[str, ...]
    hold_ids: tuple[str, ...]
    rejected_ids: tuple[str, ...]
    activation_order_ids: tuple[str, ...]
    residual_blockers: tuple[str, ...]
    dependency_map: tuple[str, ...]
    rollback_plan_summary: tuple[str, ...]
    package_recommendation: str
    package_rationale: str


@dataclass(frozen=True)
class RoutingMaintenanceReport:
    registry: RoutingNeuronRegistry
    updated_sessions: tuple[str, ...]
    activated_candidates: tuple[str, ...]
    paused_candidates: tuple[str, ...]
    cooldown_candidates: tuple[str, ...]
    promotion_ready_candidates: tuple[str, ...]
    recommendation_ids: tuple[str, ...]
    alerts: tuple[str, ...]
    watch_ids: tuple[str, ...]
    review_queue_ids: tuple[str, ...]
    resolved_review_ids: tuple[str, ...]
    stale_ids: tuple[str, ...]
    shortlist_ids: tuple[str, ...]
    discardable_ids: tuple[str, ...]
    bridge_ready_ids: tuple[str, ...]
    bridge_slate_ids: tuple[str, ...]
    bridge_blocked_ids: tuple[str, ...]
    bridge_deferred_ids: tuple[str, ...]
    rehearsal_ready_ids: tuple[str, ...]
    rehearsal_slate_ids: tuple[str, ...]
    rehearsal_blocked_ids: tuple[str, ...]
    rehearsal_deferred_ids: tuple[str, ...]
    cutover_near_go_ids: tuple[str, ...]
    cutover_go_candidate_ids: tuple[str, ...]
    rollback_risk_ids: tuple[str, ...]
    approved_ids: tuple[str, ...]
    support_only_ids: tuple[str, ...]
    hold_ids: tuple[str, ...]
    rejected_ids: tuple[str, ...]
    launch_dossier: RoutingLaunchDossier


_ROLE_ORDER_PRIORITY = {
    ROUTING_ROLE_MIGRATION_GUARD: 1,
    ROUTING_ROLE_ROUTER_SUPPORT: 2,
    ROUTING_ROLE_CONTEXT_FILTER: 3,
    ROUTING_ROLE_PRIMARY_SUPPORT: 4,
    ROUTING_ROLE_SAFETY_CHECK: 5,
    ROUTING_ROLE_CRITIC_SUPPORT: 6,
    ROUTING_ROLE_NONE: 99,
}

_LAUNCH_STATUS_PRIORITY = {
    ROUTING_LAUNCH_APPROVED: 0,
    ROUTING_LAUNCH_SUPPORT_ONLY: 1,
    ROUTING_LAUNCH_HOLD: 2,
    ROUTING_LAUNCH_REJECTED: 3,
    ROUTING_LAUNCH_NONE: 9,
}


def _candidate_records(
    registry: RoutingNeuronRegistry,
    candidate: RoutingNeuronCandidate,
) -> tuple:
    merged_records = {
        evidence.evidence_id: evidence
        for evidence in registry.evidence_records.values()
        if evidence.task_signature == candidate.task_signature
        and evidence.activated_components == candidate.activated_components
    }
    for evidence in registry.evidence_records.values():
        if evidence.neuron_id == candidate.neuron_id:
            merged_records[evidence.evidence_id] = evidence

    return tuple(sorted(merged_records.values(), key=lambda evidence: evidence.timestamp))


def _stable_activation_streak(records: tuple) -> int:
    streak = 0
    for evidence in reversed(records):
        if evidence.success_label in {"improved", "stable_success"}:
            streak += 1
            continue
        break
    return streak


def _build_candidate_history(
    registry: RoutingNeuronRegistry,
    candidate: RoutingNeuronCandidate,
) -> dict[str, int]:
    records = _candidate_records(registry, candidate)
    successful_activations = sum(
        1 for evidence in records if evidence.success_label in {"improved", "stable_success"}
    )
    failed_activations = sum(
        1 for evidence in records if evidence.success_label in {"fallback", "degraded", "failed"}
    )
    baseline_win_count = sum(
        1
        for evidence in records
        if evidence.evaluated_route == evidence.baseline_route
        and evidence.success_label in {"baseline_kept", "fallback"}
    )
    recent_fallback_count = sum(
        1
        for evidence in records
        if evidence.success_label in {"fallback", "degraded", "failed"}
    )
    budget_violation_count = sum(
        1
        for evidence in records
        if evidence.budget_profile == "tight" and evidence.cost_delta > 0.0
    )
    fallback_frequency = recent_fallback_count
    stable_activation_streak = _stable_activation_streak(records)
    return {
        "record_count": len(records),
        "successful_activations": successful_activations,
        "failed_activations": failed_activations,
        "baseline_win_count": baseline_win_count,
        "recent_fallback_count": recent_fallback_count,
        "budget_violation_count": budget_violation_count,
        "fallback_frequency": fallback_frequency,
        "stable_activation_streak": stable_activation_streak,
    }


def _resolve_confidence_tier(
    candidate: RoutingNeuronCandidate,
    history: dict[str, int],
) -> tuple[str, float]:
    record_count = history["record_count"]
    successes = history["successful_activations"]
    failures = history["failed_activations"]
    baseline_wins = history["baseline_win_count"]
    if (
        record_count >= 5
        and successes >= 4
        and failures <= 1
        and baseline_wins <= 1
        and candidate.global_routing_score >= 0.77
    ):
        return ROUTING_CONFIDENCE_SUSTAINED_VALUE, 0.9

    if (
        record_count >= 3
        and successes >= 2
        and failures <= 1
        and candidate.global_routing_score >= 0.62
    ):
        return ROUTING_CONFIDENCE_CONFIRMED_PATTERN, 0.62

    return ROUTING_CONFIDENCE_EARLY_SIGNAL, 0.28


def _resolve_stability_label(
    candidate: RoutingNeuronCandidate,
    history: dict[str, int],
) -> str:
    if candidate.neuron_state == ROUTING_STATE_PAUSED:
        return ROUTING_STABILITY_FRAGILE

    if (
        candidate.cooldown_turns_remaining > 0
        or history["recent_fallback_count"] >= max(2, history["successful_activations"])
        or history["baseline_win_count"] > history["successful_activations"]
    ):
        return ROUTING_STABILITY_DEGRADING

    if (
        history["record_count"] >= 5
        and history["successful_activations"] >= 4
        and history["recent_fallback_count"] <= 1
        and candidate.global_routing_score >= 0.75
    ):
        return ROUTING_STABILITY_STABLE

    if (
        history["stable_activation_streak"] >= 2
        and history["successful_activations"] > history["recent_fallback_count"]
        and candidate.global_routing_score >= 0.58
    ):
        return ROUTING_STABILITY_IMPROVING

    if history["failed_activations"] > history["successful_activations"]:
        return ROUTING_STABILITY_FRAGILE

    return ROUTING_STABILITY_OBSERVING


def _resolve_trend_label(candidate: RoutingNeuronCandidate) -> str:
    if candidate.stability_label == ROUTING_STABILITY_IMPROVING:
        return "up"
    if candidate.stability_label in {ROUTING_STABILITY_DEGRADING, ROUTING_STABILITY_FRAGILE}:
        return "down"
    if candidate.stability_label == ROUTING_STABILITY_STABLE:
        return "steady"
    return "watch"


def _resolve_review_priority(candidate: RoutingNeuronCandidate) -> tuple[str, str | None]:
    if candidate.neuron_state == ROUTING_STATE_PAUSED and candidate.alerts:
        return ROUTING_REVIEW_PRIORITY_HIGH, "pausada con alertas abiertas"

    if candidate.readiness_band == ROUTING_READINESS_NEAR_READY:
        return ROUTING_REVIEW_PRIORITY_HIGH, "readiness alta con valor sostenido"

    if (
        candidate.global_routing_score >= 0.72
        and candidate.stability_label in {ROUTING_STABILITY_DEGRADING, ROUTING_STABILITY_FRAGILE}
    ):
        return ROUTING_REVIEW_PRIORITY_HIGH, "degradación reciente sobre una neurona valiosa"

    if candidate.watch_status:
        return ROUTING_REVIEW_PRIORITY_MEDIUM, candidate.watch_reason or "seguimiento administrativo manual"

    if candidate.readiness_band == ROUTING_READINESS_EMERGING:
        return ROUTING_REVIEW_PRIORITY_MEDIUM, "readiness emergente que ya merece revisión humana"

    if candidate.recent_conflict_count >= 2 or candidate.recent_fallback_count >= 2:
        return ROUTING_REVIEW_PRIORITY_MEDIUM, "conflictos o fallbacks recientes piden revisión"

    if candidate.alerts or candidate.readiness_band == ROUTING_READINESS_WATCH:
        return ROUTING_REVIEW_PRIORITY_LOW, "seguir observando antes de intervenir"

    return ROUTING_REVIEW_PRIORITY_NONE, None


def _resolve_review_status(
    candidate: RoutingNeuronCandidate,
    review_priority: str,
) -> tuple[str, str | None, int]:
    needs_review = (
        candidate.watch_status
        or candidate.neuron_state == ROUTING_STATE_PAUSED
        or review_priority in {
            ROUTING_REVIEW_PRIORITY_HIGH,
            ROUTING_REVIEW_PRIORITY_MEDIUM,
        }
        or bool(candidate.alerts)
        or candidate.alert_status == ALERT_STATUS_ACKNOWLEDGED
    )
    previous_status = candidate.review_status

    if needs_review:
        review_cycles = candidate.review_cycles + 1
        status = (
            REVIEW_STATUS_WATCH
            if candidate.watch_status
            and review_priority not in {ROUTING_REVIEW_PRIORITY_HIGH}
            and candidate.neuron_state != ROUTING_STATE_PAUSED
            else REVIEW_STATUS_OPEN
        )
        if previous_status == REVIEW_STATUS_RESOLVED:
            status = REVIEW_STATUS_REOPENED
        elif review_cycles >= 3:
            status = REVIEW_STATUS_STALE

        reason = (
            candidate.review_reason
            or candidate.watch_reason
            or candidate.paused_reason
            or candidate.readiness_reason
        )
        return status, reason, review_cycles

    if previous_status in {
        REVIEW_STATUS_OPEN,
        REVIEW_STATUS_WATCH,
        REVIEW_STATUS_STALE,
        REVIEW_STATUS_REOPENED,
        REVIEW_STATUS_RESOLVED,
    } or candidate.last_admin_action in {
        "clear_watch",
        "resume",
        "pause",
        "mark_watch",
    }:
        return REVIEW_STATUS_RESOLVED, candidate.last_admin_reason or candidate.readiness_reason, 0

    return REVIEW_STATUS_NONE, candidate.review_reason, 0


def _resolve_alert_status(candidate: RoutingNeuronCandidate) -> tuple[str, int]:
    previous_status = candidate.alert_status
    has_alerts = bool(candidate.alerts)

    if has_alerts:
        alert_cycles = candidate.alert_cycles + 1
        if previous_status == ALERT_STATUS_RESOLVED:
            return ALERT_STATUS_REOPENED, alert_cycles
        if previous_status == ALERT_STATUS_ACKNOWLEDGED or candidate.last_admin_action == "acknowledge_alert":
            return ALERT_STATUS_ACKNOWLEDGED, alert_cycles
        return ALERT_STATUS_OPEN, alert_cycles

    if previous_status in {
        ALERT_STATUS_OPEN,
        ALERT_STATUS_ACKNOWLEDGED,
        ALERT_STATUS_REOPENED,
        ALERT_STATUS_RESOLVED,
    } or candidate.last_admin_action == "resolve_alert":
        return ALERT_STATUS_RESOLVED, 0

    return ALERT_STATUS_NONE, 0


def _resolve_action_outcome(
    candidate: RoutingNeuronCandidate,
    *,
    review_status: str,
    alert_status: str,
    review_cycles: int,
    alert_cycles: int,
) -> tuple[str | None, str | None]:
    if candidate.last_admin_action is None:
        return candidate.action_outcome, candidate.action_outcome_reason

    if review_status == REVIEW_STATUS_RESOLVED or alert_status == ALERT_STATUS_RESOLVED:
        return ACTION_OUTCOME_HELPED, "la acción ayudó a cerrar o estabilizar el item"

    if review_status == REVIEW_STATUS_REOPENED or alert_status == ALERT_STATUS_REOPENED:
        return ACTION_OUTCOME_WORSENED, "la señal volvió a aparecer después de la acción"

    if review_status == REVIEW_STATUS_STALE or (
        alert_status == ALERT_STATUS_ACKNOWLEDGED and alert_cycles >= 2
    ):
        return ACTION_OUTCOME_NO_CLEAR_CHANGE, "la acción no produjo un cambio claro todavía"

    if review_cycles > 0 or alert_cycles > 0:
        return ACTION_OUTCOME_PENDING_OBSERVATION, "todavía falta más observación para juzgar el efecto"

    return candidate.action_outcome, candidate.action_outcome_reason


def _resolve_curation_status(candidate: RoutingNeuronCandidate) -> tuple[str, str]:
    if (
        candidate.review_status == REVIEW_STATUS_STALE
        or candidate.cooldown_turns_remaining > 0
        or candidate.action_outcome == ACTION_OUTCOME_WORSENED
    ):
        return (
            ROUTING_CURATION_DISCARDABLE,
            "ya acumula ruido o desgaste suficiente como para salir del foco principal",
        )

    if (
        candidate.neuron_state == ROUTING_STATE_PAUSED
        or candidate.alert_status in {ALERT_STATUS_OPEN, ALERT_STATUS_REOPENED}
        or candidate.recent_fallback_count >= 2
        or candidate.recent_conflict_count >= 2
        or candidate.baseline_win_count > max(candidate.successful_activations, 1)
        or candidate.global_routing_score < 0.48
    ):
        return (
            ROUTING_CURATION_NOISY,
            "todavía mete más ruido operativo del que compensa",
        )

    if (
        candidate.global_routing_score >= 0.77
        and candidate.confidence_tier == ROUTING_CONFIDENCE_SUSTAINED_VALUE
        and candidate.stability_label in {ROUTING_STABILITY_STABLE, ROUTING_STABILITY_IMPROVING}
        and candidate.successful_activations >= 3
        and candidate.recent_fallback_count <= 1
        and candidate.recent_conflict_count <= 1
        and candidate.alert_status in {ALERT_STATUS_NONE, ALERT_STATUS_RESOLVED}
        and candidate.review_status in {REVIEW_STATUS_NONE, REVIEW_STATUS_RESOLVED}
    ):
        return (
            ROUTING_CURATION_USEFUL,
            "ya muestra valor sostenido, buena higiene administrativa y poco ruido frente a baseline",
        )

    return (
        ROUTING_CURATION_PROMISING,
        "ya tiene señales útiles, pero todavía necesita más observación antes de entrar en foco fuerte",
    )


def _resolve_influence_readiness(candidate: RoutingNeuronCandidate) -> tuple[str, str]:
    if (
        candidate.curation_status in {ROUTING_CURATION_NOISY, ROUTING_CURATION_DISCARDABLE}
        or candidate.neuron_state == ROUTING_STATE_PAUSED
        or candidate.cooldown_turns_remaining > 0
    ):
        return (
            ROUTING_INFLUENCE_NOT_READY,
            "todavía no conviene empujar influencia adicional",
        )

    if (
        candidate.curation_status == ROUTING_CURATION_USEFUL
        and candidate.readiness_band == ROUTING_READINESS_NEAR_READY
        and candidate.action_outcome in {None, ACTION_OUTCOME_HELPED, ACTION_OUTCOME_PENDING_OBSERVATION}
        and candidate.alert_status in {ALERT_STATUS_NONE, ALERT_STATUS_RESOLVED}
        and candidate.review_status in {REVIEW_STATUS_NONE, REVIEW_STATUS_RESOLVED}
    ):
        return (
            ROUTING_INFLUENCE_BRIDGE_WATCH,
            "ya merece entrar al puente conceptual hacia V0.39, aunque todavía sin promoción real",
        )

    if (
        candidate.curation_status == ROUTING_CURATION_USEFUL
        and candidate.readiness_band in {ROUTING_READINESS_EMERGING, ROUTING_READINESS_NEAR_READY}
    ):
        return (
            ROUTING_INFLUENCE_SHORTLIST_READY,
            "ya merece shortlist operativa por valor sostenido y baja fricción",
        )

    return (
        ROUTING_INFLUENCE_EMERGING,
        "todavía conviene mantenerla como señal útil en observación",
    )


def _resolve_selection_status(candidate: RoutingNeuronCandidate) -> tuple[str, str, bool]:
    if candidate.curation_status == ROUTING_CURATION_DISCARDABLE:
        return (
            ROUTING_SELECTION_DISCARDABLE,
            "conviene sacarla del foco principal hasta que muestre señal nueva",
            True,
        )

    if candidate.curation_status == ROUTING_CURATION_NOISY:
        return (
            ROUTING_SELECTION_HOLD,
            "sigue abierta o visible, pero no merece shortlist todavía",
            False,
        )

    if candidate.influence_readiness in {
        ROUTING_INFLUENCE_SHORTLIST_READY,
        ROUTING_INFLUENCE_BRIDGE_WATCH,
    }:
        return (
            ROUTING_SELECTION_SHORTLISTED,
            "entró en shortlist por valor sostenido, bajo ruido y señal de influencia útil",
            False,
        )

    return (
        ROUTING_SELECTION_OBSERVED_ONLY,
        "todavía conviene observarla antes de meterla en shortlist operativa",
        False,
    )


def _resolve_conceptual_role_fit(candidate: RoutingNeuronCandidate) -> tuple[tuple[str, ...], str]:
    fits: list[str] = []
    reasons: list[str] = []

    if (
        candidate.neuron_type in {ROUTING_TYPE_SELECTION, ROUTING_TYPE_TRANSFORMATION}
        or "skip_critic" in candidate.routing_condition
        or candidate.intermediate_transform is not None
    ):
        fits.append(ROUTING_STACK_FIT_SMOLLM2)
        reasons.append("encaja como router o micro expert liviano")

    if (
        candidate.neuron_type == ROUTING_TYPE_CONTROL
        or "primary" in candidate.activated_components
    ) and (
        candidate.global_routing_score >= 0.58 or candidate.expected_gain >= 0.12
    ):
        fits.append(ROUTING_STACK_FIT_GRANITE)
        reasons.append("aporta criterio útil sobre el flujo primary conversacional")

    if (
        "critic" in candidate.activated_components
        or "critic" in candidate.routing_condition
        or "verification" in candidate.task_signature
        or "verifier" in candidate.task_signature
    ) and (
        candidate.global_routing_score >= 0.58
        or candidate.review_priority in {
            ROUTING_REVIEW_PRIORITY_LOW,
            ROUTING_REVIEW_PRIORITY_MEDIUM,
            ROUTING_REVIEW_PRIORITY_HIGH,
        }
    ):
        fits.append(ROUTING_STACK_FIT_OLMO)
        reasons.append("muestra afinidad con verificación o control crítico")

    if not fits:
        return (
            (ROUTING_STACK_FIT_NEUTRAL,),
            "todavía no se ve un mapeo claro al stack verde",
        )

    unique_fits = tuple(dict.fromkeys(fits))
    unique_reasons = tuple(dict.fromkeys(reasons))
    return unique_fits, " / ".join(unique_reasons)


def _resolve_bridge_preflight(
    candidate: RoutingNeuronCandidate,
) -> tuple[str, str, tuple[str, ...], str]:
    blockers: list[str] = []
    gaps: list[str] = []

    if candidate.curation_status == ROUTING_CURATION_DISCARDABLE:
        return (
            ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED,
            "todavía no tiene base suficiente para entrar en el preflight del puente",
            ("valor operativo insuficiente",),
            ROUTING_REVIEW_PRIORITY_NONE,
        )

    if candidate.neuron_state == ROUTING_STATE_PAUSED or candidate.cooldown_turns_remaining > 0:
        blockers.append("inestabilidad o pausa")
    if candidate.alert_status in {ALERT_STATUS_OPEN, ALERT_STATUS_REOPENED, ALERT_STATUS_ACKNOWLEDGED}:
        blockers.append("alertas recientes")
    if candidate.review_status in {REVIEW_STATUS_OPEN, REVIEW_STATUS_STALE, REVIEW_STATUS_REOPENED}:
        blockers.append("revisión todavía abierta")
    if candidate.recent_fallback_count >= 2:
        blockers.append("demasiados fallbacks recientes")
    if candidate.recent_conflict_count >= 2:
        blockers.append("demasiados conflictos recientes")
    if candidate.baseline_win_count > max(candidate.successful_activations, 1):
        gaps.append("baseline todavía gana demasiado")
    if candidate.confidence_tier == ROUTING_CONFIDENCE_EARLY_SIGNAL or candidate.successful_activations < 3:
        gaps.append("evidencia insuficiente")
    if candidate.conceptual_role_fit == (ROUTING_STACK_FIT_NEUTRAL,):
        blockers.append("mapeo débil al stack verde")

    if candidate.selection_status == ROUTING_SELECTION_SHORTLISTED:
        if not blockers and not gaps and candidate.influence_readiness == ROUTING_INFLUENCE_BRIDGE_WATCH:
            return (
                ROUTING_BRIDGE_PREFLIGHT_READY,
                "ya puede entrar a la bridge slate: valor sostenido, poco ruido y fit claro al stack verde",
                (),
                ROUTING_REVIEW_PRIORITY_HIGH,
            )
        if not blockers:
            rationale = "ya merece ensayo de puente, pero todavía falta cerrar algunos gaps antes del bridge slate fuerte"
            return (
                ROUTING_BRIDGE_PREFLIGHT_CANDIDATE,
                rationale,
                tuple(dict.fromkeys(gaps)),
                ROUTING_REVIEW_PRIORITY_HIGH
                if candidate.influence_readiness in {
                    ROUTING_INFLUENCE_SHORTLIST_READY,
                    ROUTING_INFLUENCE_BRIDGE_WATCH,
                }
                else ROUTING_REVIEW_PRIORITY_MEDIUM,
            )
        return (
            ROUTING_BRIDGE_PREFLIGHT_BLOCKED,
            "sirve para shortlist general, pero el puente queda bloqueado hasta cerrar ruido o riesgos",
            tuple(dict.fromkeys(blockers + gaps)),
            ROUTING_REVIEW_PRIORITY_HIGH if candidate.curation_status == ROUTING_CURATION_USEFUL else ROUTING_REVIEW_PRIORITY_MEDIUM,
        )

    if candidate.selection_status == ROUTING_SELECTION_OBSERVED_ONLY and candidate.curation_status in {
        ROUTING_CURATION_PROMISING,
        ROUTING_CURATION_USEFUL,
    }:
        return (
            ROUTING_BRIDGE_PREFLIGHT_DEFERRED,
            "todavía tiene valor general, pero no merece puente hasta consolidar shortlist y evidencia",
            tuple(dict.fromkeys(gaps or ("todavía fuera de shortlist general",))),
            ROUTING_REVIEW_PRIORITY_MEDIUM if candidate.curation_status == ROUTING_CURATION_USEFUL else ROUTING_REVIEW_PRIORITY_LOW,
        )

    if candidate.selection_status == ROUTING_SELECTION_HOLD:
        return (
            ROUTING_BRIDGE_PREFLIGHT_BLOCKED,
            "la neurona quedó en hold: todavía conviene limpiar ruido antes de considerar el puente",
            tuple(dict.fromkeys(blockers or ("todavía no supera la curación básica",))),
            ROUTING_REVIEW_PRIORITY_LOW,
        )

    return (
        ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED,
        "todavía no conviene meterla en el preflight del puente",
        tuple(dict.fromkeys(blockers + gaps)),
        ROUTING_REVIEW_PRIORITY_NONE,
    )


def _resolve_rollback_concerns(candidate: RoutingNeuronCandidate) -> tuple[str, ...]:
    concerns: list[str] = []

    if candidate.confidence_tier == ROUTING_CONFIDENCE_EARLY_SIGNAL or candidate.successful_activations < 4:
        concerns.append("evidencia todavía escasa")
    if candidate.stability_label in {ROUTING_STABILITY_DEGRADING, ROUTING_STABILITY_FRAGILE}:
        concerns.append("fragilidad operativa")
    if candidate.baseline_win_count >= max(2, candidate.successful_activations // 2 + 1):
        concerns.append("dependencia excesiva del baseline actual")
    if candidate.recent_fallback_count >= 2:
        concerns.append("demasiados fallbacks recientes")
    if candidate.recent_conflict_count >= 2:
        concerns.append("carga alta de conflictos")
    if candidate.alert_status in {ALERT_STATUS_OPEN, ALERT_STATUS_ACKNOWLEDGED, ALERT_STATUS_REOPENED}:
        concerns.append("ruido administrativo todavía abierto")
    if candidate.review_status in {REVIEW_STATUS_OPEN, REVIEW_STATUS_STALE, REVIEW_STATUS_REOPENED}:
        concerns.append("revisión todavía inestable")
    if candidate.conceptual_role_fit == (ROUTING_STACK_FIT_NEUTRAL,):
        concerns.append("fit conceptual ambiguo")
    if candidate.expected_gain < 0.16:
        concerns.append("valor poco portable fuera del contexto actual")

    return tuple(dict.fromkeys(concerns))


def _resolve_bridge_rehearsal(
    candidate: RoutingNeuronCandidate,
) -> tuple[str, str, tuple[str, ...], str]:
    blockers: list[str] = list(candidate.bridge_blockers)
    gaps: list[str] = []

    if candidate.selection_status == ROUTING_SELECTION_DISCARDABLE:
        return (
            ROUTING_REHEARSAL_NOT_IN_REHEARSAL,
            "todavía no tiene base suficiente para entrar al rehearsal del puente",
            ("fuera de shortlist general",),
            ROUTING_REVIEW_PRIORITY_NONE,
        )

    if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_BLOCKED:
        return (
            ROUTING_REHEARSAL_BLOCKED,
            "el rehearsal queda bloqueado mientras el preflight siga con riesgos abiertos",
            tuple(dict.fromkeys(blockers or ("preflight todavía bloqueado",))),
            ROUTING_REVIEW_PRIORITY_HIGH,
        )

    if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED:
        return (
            ROUTING_REHEARSAL_NOT_IN_REHEARSAL,
            "todavía no corresponde meterla en rehearsal",
            tuple(dict.fromkeys(blockers)),
            ROUTING_REVIEW_PRIORITY_NONE,
        )

    if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_DEFERRED:
        gaps.extend(candidate.bridge_blockers or ("todavía fuera de bridge slate",))
        return (
            ROUTING_REHEARSAL_DEFERRED,
            "todavía conviene consolidar evidencia y shortlist antes del rehearsal",
            tuple(dict.fromkeys(gaps)),
            ROUTING_REVIEW_PRIORITY_MEDIUM,
        )

    if candidate.confidence_tier != ROUTING_CONFIDENCE_SUSTAINED_VALUE:
        gaps.append("confianza todavía no sostenida")
    if candidate.successful_activations < 4:
        gaps.append("todavía faltan activaciones útiles")
    if candidate.stability_label not in {ROUTING_STABILITY_STABLE, ROUTING_STABILITY_IMPROVING}:
        blockers.append("estabilidad todavía insuficiente")
    if candidate.action_outcome == ACTION_OUTCOME_WORSENED:
        blockers.append("la última acción administrativa empeoró la señal")
    if candidate.action_outcome == ACTION_OUTCOME_NO_CLEAR_CHANGE:
        gaps.append("la última acción todavía no mostró impacto claro")
    if candidate.conceptual_role_fit == (ROUTING_STACK_FIT_NEUTRAL,):
        blockers.append("fit conceptual todavía ambiguo")

    if not blockers and not gaps and candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_READY:
        return (
            ROUTING_REHEARSAL_READY,
            "ya puede entrar a rehearsal: el preflight es robusto y la señal se sostiene con poco ruido",
            (),
            ROUTING_REVIEW_PRIORITY_HIGH,
        )

    if not blockers:
        return (
            ROUTING_REHEARSAL_CANDIDATE,
            "merece rehearsal, pero todavía falta cerrar algunos gaps antes del ensayo fuerte",
            tuple(dict.fromkeys(gaps)),
            ROUTING_REVIEW_PRIORITY_HIGH
            if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_READY
            else ROUTING_REVIEW_PRIORITY_MEDIUM,
        )

    return (
        ROUTING_REHEARSAL_BLOCKED,
        "la neurona sirve para puente general, pero rehearsal sigue bloqueado hasta limpiar riesgos",
        tuple(dict.fromkeys(blockers + gaps)),
        ROUTING_REVIEW_PRIORITY_HIGH,
    )


def _resolve_cutover_readiness(
    candidate: RoutingNeuronCandidate,
) -> tuple[str, str, tuple[str, ...]]:
    risks = list(candidate.rollback_concerns)

    if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_DEFERRED:
        return (
            ROUTING_CUTOVER_WATCH,
            "todavía conviene observarla para cutover, pero primero debe fortalecer el rehearsal",
            tuple(dict.fromkeys(risks)),
        )

    if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_BLOCKED:
        return (
            ROUTING_CUTOVER_BLOCKED,
            "el go/no-go sigue bloqueado porque rehearsal todavía no está limpio",
            tuple(dict.fromkeys(risks or candidate.rehearsal_blockers or ("rehearsal todavía bloqueado",))),
        )

    if candidate.selection_status != ROUTING_SELECTION_SHORTLISTED:
        return (
            ROUTING_CUTOVER_NOT_READY,
            "todavía no corresponde hablar de cutover porque la neurona ni siquiera consolidó shortlist operativa",
            tuple(dict.fromkeys(risks)),
        )

    if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_READY:
        if (
            candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_READY
            and candidate.confidence_tier == ROUTING_CONFIDENCE_SUSTAINED_VALUE
            and candidate.stability_label == ROUTING_STABILITY_STABLE
            and candidate.global_routing_score >= 0.84
            and candidate.successful_activations >= 5
            and candidate.recent_fallback_count == 0
            and candidate.recent_conflict_count <= 1
            and candidate.alert_status in {ALERT_STATUS_NONE, ALERT_STATUS_RESOLVED}
            and candidate.review_status in {REVIEW_STATUS_NONE, REVIEW_STATUS_RESOLVED}
            and len(risks) <= 1
        ):
            return (
                ROUTING_CUTOVER_GO_CANDIDATE,
                "ya merece un go/no-go administrativo favorable: rehearsal sólido, poco ruido y riesgos controlados",
                tuple(dict.fromkeys(risks)),
            )
        return (
            ROUTING_CUTOVER_NEAR_GO,
            "ya está cerca de un go administrativo, pero todavía conviene cerrar algunos riesgos antes del cutover",
            tuple(dict.fromkeys(risks)),
        )

    if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_CANDIDATE:
        return (
            ROUTING_CUTOVER_WATCH,
            "ya merece seguimiento serio para cutover, pero todavía le falta cerrar rehearsal",
            tuple(dict.fromkeys(risks)),
        )

    return (
        ROUTING_CUTOVER_NOT_READY,
        "todavía no tiene base suficiente para una evaluación de go/no-go",
        tuple(dict.fromkeys(risks)),
    )


def _resolve_cutover_role(candidate: RoutingNeuronCandidate) -> tuple[str, str]:
    if candidate.selection_status == ROUTING_SELECTION_DISCARDABLE:
        return ROUTING_ROLE_NONE, "todavía no conviene asignarle un rol de cutover"

    if candidate.neuron_type == ROUTING_TYPE_TRANSFORMATION or candidate.intermediate_transform is not None:
        return (
            ROUTING_ROLE_CONTEXT_FILTER,
            "aporta una transformación o filtro previo útil para un cutover controlado",
        )

    if (
        ROUTING_STACK_FIT_OLMO in candidate.conceptual_role_fit
        and (
            candidate.alert_status in {ALERT_STATUS_OPEN, ALERT_STATUS_ACKNOWLEDGED, ALERT_STATUS_REOPENED}
            or candidate.review_priority == ROUTING_REVIEW_PRIORITY_HIGH
            or candidate.review_status in {REVIEW_STATUS_OPEN, REVIEW_STATUS_REOPENED, REVIEW_STATUS_STALE}
        )
    ):
        return (
            ROUTING_ROLE_MIGRATION_GUARD,
            "sirve mejor como guardia administrativa mientras el puente todavía necesita control",
        )

    if ROUTING_STACK_FIT_SMOLLM2 in candidate.conceptual_role_fit:
        return (
            ROUTING_ROLE_ROUTER_SUPPORT,
            "encaja como apoyo de routing liviano o micro expert del stack verde",
        )

    if (
        ROUTING_STACK_FIT_OLMO in candidate.conceptual_role_fit
        and (
            "critic" in candidate.activated_components
            or "verification" in candidate.task_signature
            or "verifier" in candidate.task_signature
        )
    ):
        return (
            ROUTING_ROLE_CRITIC_SUPPORT,
            "aporta señal útil como apoyo critic o verifier del cutover",
        )

    if ROUTING_STACK_FIT_GRANITE in candidate.conceptual_role_fit:
        return (
            ROUTING_ROLE_PRIMARY_SUPPORT,
            "encaja como apoyo del flujo primary conversacional para la ola inicial",
        )

    if ROUTING_STACK_FIT_OLMO in candidate.conceptual_role_fit:
        return (
            ROUTING_ROLE_SAFETY_CHECK,
            "sirve como chequeo de seguridad o consistencia alrededor del cambio",
        )

    return ROUTING_ROLE_NONE, "todavía no se ve un rol claro para el cutover"


def _resolve_dependency_hints(candidate: RoutingNeuronCandidate, role: str) -> tuple[str, ...]:
    hints: list[str] = []

    if role == ROUTING_ROLE_ROUTER_SUPPORT:
        hints.append("requires migration_guard baseline checks")
    elif role == ROUTING_ROLE_PRIMARY_SUPPORT:
        hints.append("requires migration_guard baseline checks")
        if candidate.intermediate_transform is not None:
            hints.append("benefits from context_filter warmup")
    elif role == ROUTING_ROLE_CRITIC_SUPPORT:
        hints.append("depends on router_support signal quality")
    elif role == ROUTING_ROLE_SAFETY_CHECK:
        hints.append("pairs with migration_guard review")
    elif role == ROUTING_ROLE_CONTEXT_FILTER:
        hints.append("should enter before primary_support")

    return tuple(dict.fromkeys(hints))


def _resolve_launch_status(
    candidate: RoutingNeuronCandidate,
    role: str,
) -> tuple[str, str, tuple[str, ...]]:
    blockers = list(candidate.rehearsal_blockers) + list(candidate.bridge_blockers)
    blockers = list(dict.fromkeys(blockers))
    no_go_conditions = list(candidate.rollback_concerns) + blockers

    if candidate.selection_status == ROUTING_SELECTION_DISCARDABLE:
        no_go_conditions.append("valor operativo insuficiente para esta ola")
        return (
            ROUTING_LAUNCH_REJECTED,
            "queda fuera del paquete final porque sigue siendo demasiado ruidosa o poco portable",
            tuple(dict.fromkeys(no_go_conditions)),
        )

    if candidate.cutover_readiness == ROUTING_CUTOVER_BLOCKED:
        if candidate.selection_status == ROUTING_SELECTION_SHORTLISTED:
            no_go_conditions.append("cutover readiness blocked")
            return (
                ROUTING_LAUNCH_HOLD,
                "tiene valor validado, pero queda en hold hasta cerrar blockers y ruido administrativo",
                tuple(dict.fromkeys(no_go_conditions)),
            )
        no_go_conditions.append("cutover readiness blocked")
        return (
            ROUTING_LAUNCH_REJECTED,
            "no conviene meterla en la ola final mientras siga bloqueada y fuera del foco principal",
            tuple(dict.fromkeys(no_go_conditions)),
        )

    if candidate.cutover_readiness == ROUTING_CUTOVER_GO_CANDIDATE:
        if role in {
            ROUTING_ROLE_MIGRATION_GUARD,
            ROUTING_ROLE_ROUTER_SUPPORT,
            ROUTING_ROLE_PRIMARY_SUPPORT,
        } and len(candidate.rollback_concerns) <= 1:
            return (
                ROUTING_LAUNCH_APPROVED,
                "ya puede entrar al paquete final de cutover con rol claro y riesgos controlados",
                tuple(dict.fromkeys(no_go_conditions)),
            )
        return (
            ROUTING_LAUNCH_SUPPORT_ONLY,
            "ya sirve para acompañar el cutover, pero conviene usarla como apoyo y no como pieza núcleo",
            tuple(dict.fromkeys(no_go_conditions)),
        )

    if candidate.cutover_readiness == ROUTING_CUTOVER_NEAR_GO:
        if role in {
            ROUTING_ROLE_CONTEXT_FILTER,
            ROUTING_ROLE_CRITIC_SUPPORT,
            ROUTING_ROLE_SAFETY_CHECK,
        } and len(candidate.rollback_concerns) <= 2:
            return (
                ROUTING_LAUNCH_SUPPORT_ONLY,
                "ya aporta valor como apoyo del cutover, aunque todavía no conviene ponerla en el núcleo",
                tuple(dict.fromkeys(no_go_conditions)),
            )
        if not no_go_conditions:
            no_go_conditions.append("close_cutover_gaps")
        return (
            ROUTING_LAUNCH_HOLD,
            "ya está cerca del go, pero todavía faltan señales o limpieza para aprobarla en la ola final",
            tuple(dict.fromkeys(no_go_conditions)),
        )

    if candidate.cutover_readiness == ROUTING_CUTOVER_WATCH:
        no_go_conditions.append("cutover still in watch")
        return (
            ROUTING_LAUNCH_HOLD,
            "todavía conviene mantenerla en watch antes de decidir si entra al paquete final",
            tuple(dict.fromkeys(no_go_conditions)),
        )

    if candidate.selection_status == ROUTING_SELECTION_SHORTLISTED:
        no_go_conditions.append("launch role not mature enough")
        return (
            ROUTING_LAUNCH_HOLD,
            "tiene valor general, pero todavía no ofrece una base suficientemente limpia para decisión final",
            tuple(dict.fromkeys(no_go_conditions)),
        )

    no_go_conditions.append("launch packet not justified")
    return (
        ROUTING_LAUNCH_REJECTED,
        "por ahora sirve como observación o rehearsal, pero no para el paquete final de V0.39",
        tuple(dict.fromkeys(no_go_conditions)),
    )


def _resolve_rollback_plan(
    candidate: RoutingNeuronCandidate,
    launch_status: str,
) -> tuple[tuple[str, ...], str | None, str | None, tuple[str, ...]]:
    triggers: list[str] = list(candidate.rollback_concerns)
    no_go_conditions: list[str] = list(candidate.rehearsal_blockers) + list(candidate.bridge_blockers)

    if candidate.recent_conflict_count > 0:
        triggers.append("conflict spike after launch")
    if candidate.recent_fallback_count > 0:
        triggers.append("fallback spike after launch")
    if candidate.baseline_win_count > max(candidate.successful_activations, 1):
        triggers.append("baseline outperforms proposed packet")
    if candidate.alert_status in {ALERT_STATUS_OPEN, ALERT_STATUS_ACKNOWLEDGED, ALERT_STATUS_REOPENED}:
        triggers.append("administrative alerts reopen")
    if candidate.cutover_readiness == ROUTING_CUTOVER_BLOCKED:
        no_go_conditions.append("cutover readiness blocked")
    if candidate.bridge_rehearsal_status in {
        ROUTING_REHEARSAL_BLOCKED,
        ROUTING_REHEARSAL_DEFERRED,
    }:
        no_go_conditions.append(candidate.bridge_rehearsal_status.replace("_", " "))

    if not triggers and launch_status in {ROUTING_LAUNCH_APPROVED, ROUTING_LAUNCH_SUPPORT_ONLY}:
        triggers.append("quality drift after launch")

    fallback_target = (
        "baseline_primary_then_critic"
        if "critic" in candidate.activated_components
        else "baseline_primary_only"
    )
    safe_reversion = (
        f"volver a {fallback_target} y sacar {candidate.neuron_id} del cutover packet"
        if launch_status != ROUTING_LAUNCH_REJECTED
        else f"mantener {fallback_target} y dejar {candidate.neuron_id} fuera de esta ola"
    )

    return (
        tuple(dict.fromkeys(triggers)),
        fallback_target,
        safe_reversion,
        tuple(dict.fromkeys(no_go_conditions)),
    )


def _assign_launch_activation_order(
    candidates: dict[str, RoutingNeuronCandidate],
) -> dict[str, RoutingNeuronCandidate]:
    ordered_launch_ids = [
        candidate.neuron_id
        for candidate in sorted(
            candidates.values(),
            key=lambda candidate: (
                _LAUNCH_STATUS_PRIORITY.get(candidate.launch_status, 9),
                _ROLE_ORDER_PRIORITY.get(candidate.cutover_role, 99),
                -candidate.global_routing_score,
                candidate.neuron_id,
            ),
        )
        if candidate.launch_status in {
            ROUTING_LAUNCH_APPROVED,
            ROUTING_LAUNCH_SUPPORT_ONLY,
        }
    ]

    updated = dict(candidates)
    for order_index, neuron_id in enumerate(ordered_launch_ids, start=1):
        candidate = updated[neuron_id]
        order_reason = (
            "entra primero dentro del núcleo aprobado del cutover"
            if candidate.launch_status == ROUTING_LAUNCH_APPROVED and order_index == 1
            else (
                "entra después del núcleo aprobado porque cumple un rol de apoyo"
                if candidate.launch_status == ROUTING_LAUNCH_SUPPORT_ONLY
                else "entra según prioridad relativa del paquete final"
            )
        )
        updated[neuron_id] = replace(
            candidate,
            activation_order=order_index,
            activation_order_reason=order_reason,
        )

    for neuron_id, candidate in tuple(updated.items()):
        if candidate.launch_status in {ROUTING_LAUNCH_HOLD, ROUTING_LAUNCH_REJECTED, ROUTING_LAUNCH_NONE}:
            updated[neuron_id] = replace(
                candidate,
                activation_order=None,
                activation_order_reason=None,
            )

    return updated


def _resolve_action_suggestion(candidate: RoutingNeuronCandidate) -> str:
    if candidate.launch_status == ROUTING_LAUNCH_APPROVED:
        return "prepare_launch_dossier"

    if candidate.launch_status == ROUTING_LAUNCH_SUPPORT_ONLY:
        return "prepare_support_cutover"

    if candidate.launch_status == ROUTING_LAUNCH_HOLD:
        return "hold_for_cutover_review"

    if candidate.launch_status == ROUTING_LAUNCH_REJECTED:
        return "exclude_from_cutover_wave"

    if candidate.cutover_readiness == ROUTING_CUTOVER_GO_CANDIDATE:
        return "prepare_go_no_go_review"

    if candidate.cutover_readiness == ROUTING_CUTOVER_NEAR_GO:
        return "close_cutover_gaps"

    if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_READY:
        return "keep_rehearsal_slate"

    if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_CANDIDATE:
        return "review_rehearsal_candidate"

    if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_BLOCKED:
        return "resolve_rehearsal_blockers"

    if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_DEFERRED:
        return "collect_rehearsal_evidence"

    if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_READY:
        return "keep_bridge_slate"

    if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_CANDIDATE:
        return "review_bridge_candidate"

    if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_BLOCKED:
        return "resolve_bridge_blockers"

    if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_DEFERRED:
        return "collect_more_bridge_evidence"

    if candidate.review_status == REVIEW_STATUS_STALE:
        return "reassess_or_close_review"

    if candidate.review_status == REVIEW_STATUS_REOPENED or candidate.alert_status == ALERT_STATUS_REOPENED:
        return "prioritize_review"

    if candidate.review_status == REVIEW_STATUS_RESOLVED and candidate.alert_status in {
        ALERT_STATUS_NONE,
        ALERT_STATUS_RESOLVED,
    }:
        return "no_action_needed"

    if candidate.alert_status == ALERT_STATUS_ACKNOWLEDGED:
        return "verify_alert_resolution"

    if candidate.selection_status == ROUTING_SELECTION_SHORTLISTED:
        if candidate.influence_readiness == ROUTING_INFLUENCE_BRIDGE_WATCH:
            return "review_bridge_readiness"
        return "keep_in_shortlist"

    if candidate.selection_status == ROUTING_SELECTION_DISCARDABLE:
        return "deprioritize_temporarily"

    if candidate.selection_status == ROUTING_SELECTION_HOLD:
        return "hold_without_selection"

    if candidate.neuron_state == ROUTING_STATE_PAUSED:
        return "review_pause_reason"

    if candidate.readiness_band == ROUTING_READINESS_NEAR_READY:
        return "review_readiness"

    if candidate.watch_status:
        return "follow_up_watch"

    if candidate.cooldown_turns_remaining > 0:
        return "respect_cooldown"

    if candidate.alerts:
        return "acknowledge_and_monitor"

    if candidate.readiness_band == ROUTING_READINESS_EMERGING:
        return "mark_watch"

    if candidate.stability_label in {ROUTING_STABILITY_DEGRADING, ROUTING_STABILITY_FRAGILE}:
        return "keep_baseline_and_monitor"

    return "keep_observing"


def _should_flag_promotion_readiness(candidate: RoutingNeuronCandidate) -> bool:
    return (
        candidate.neuron_state != ROUTING_STATE_PAUSED
        and candidate.cooldown_turns_remaining == 0
        and candidate.confidence_tier == ROUTING_CONFIDENCE_SUSTAINED_VALUE
        and candidate.stability_label in {ROUTING_STABILITY_STABLE, ROUTING_STABILITY_IMPROVING}
        and candidate.global_routing_score >= 0.77
        and candidate.successful_activations >= 4
    )


def _resolve_readiness_band(candidate: RoutingNeuronCandidate) -> tuple[str, str]:
    if candidate.neuron_state == ROUTING_STATE_PAUSED:
        return ROUTING_READINESS_NOT_READY, "pausada por inestabilidad o revisión"

    if candidate.cooldown_turns_remaining > 0:
        return ROUTING_READINESS_NOT_READY, "en cooldown por sobreuso o señal débil"

    if candidate.stability_label in {ROUTING_STABILITY_FRAGILE, ROUTING_STABILITY_DEGRADING}:
        return ROUTING_READINESS_NOT_READY, "todavía arrastra ruido operativo"

    if (
        candidate.promotion_ready_signal
        and candidate.global_routing_score >= 0.77
        and candidate.baseline_win_count <= 1
        and candidate.recent_fallback_count == 0
        and candidate.recent_conflict_count <= 1
    ):
        return ROUTING_READINESS_NEAR_READY, "valor sostenido con poco ruido frente a baseline"

    if (
        candidate.confidence_tier in {
            ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
            ROUTING_CONFIDENCE_SUSTAINED_VALUE,
        }
        and candidate.global_routing_score >= 0.68
        and candidate.successful_activations >= 2
    ):
        return ROUTING_READINESS_EMERGING, "ya muestra señal útil repetida y estable"

    return ROUTING_READINESS_WATCH, "todavía conviene seguir observando antes de empujar promoción"


def _build_session_summary(
    session_id: str,
    registry: RoutingNeuronRegistry,
) -> SessionRoutingSummary | None:
    records = tuple(
        evidence
        for evidence in registry.evidence_records.values()
        if evidence.session_id == session_id
    )
    if not records:
        return None
    session_runtime_records = tuple(
        record
        for record in registry.runtime_records
        if record.session_id == session_id
    )

    detected_patterns = tuple(
        sorted(
            {
                evidence.observed_pattern_id
                for evidence in records
                if evidence.observed_pattern_id is not None
            }
        )
    )
    compared_routes = tuple(
        sorted(
            {
                f"{evidence.baseline_route}->{evidence.evaluated_route}"
                for evidence in records
            }
        )
    )
    activated_routes = tuple(sorted({evidence.evaluated_route for evidence in records}))
    emerging_candidates = tuple(
        sorted(
            {
                evidence.neuron_id
                for evidence in records
                if evidence.neuron_id is not None and evidence.neuron_id in registry.candidates
            }
        )
    )
    considered_neurons = tuple(
        sorted(
            {
                neuron_id
                for evidence in records
                for neuron_id in evidence.considered_neuron_ids
            }
        )
    )
    gains = round(
        sum(
            evidence.quality_delta
            + evidence.verification_delta
            + evidence.consistency_delta
            - max(evidence.cost_delta, 0.0)
            for evidence in records
        ),
        3,
    )
    review_opportunities = tuple(
        sorted(
            {
                evidence.outcome_summary
                for evidence in records
                if evidence.success_label in {"fallback", "degraded", "failed"}
            }
        )
    )
    applied_neurons = tuple(
        sorted(
            {
                evidence.neuron_id
                for evidence in records
                if evidence.neuron_id is not None
                and evidence.success_label in {"improved", "stable_success"}
            }
        )
    )
    useful_neurons = tuple(
        sorted(
            neuron_id
            for neuron_id in applied_neurons
            if neuron_id is not None
            and neuron_id in registry.candidates
            and registry.candidates[neuron_id].global_routing_score >= 0.65
        )
    )
    paused_neurons = tuple(
        sorted(
            candidate.neuron_id for candidate in registry.list_paused()
        )
    )
    cooldown_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.cooldown_turns_remaining > 0
        )
    )
    baseline_preferred_cases = tuple(
        sorted(
            evidence.outcome_summary
            for evidence in records
            if evidence.success_label in {"baseline_kept", "fallback"}
        )
    )
    fragile_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.stability_label in {ROUTING_STABILITY_FRAGILE, ROUTING_STABILITY_DEGRADING}
        )
    )
    fallback_cases = tuple(
        sorted(
            evidence.outcome_summary
            for evidence in records
            if evidence.success_label in {"fallback", "degraded", "failed"}
        )
    )
    blocked_neurons = tuple(
        sorted(
            {
                evidence.neuron_id
                for evidence in records
                if evidence.neuron_id is not None
                and evidence.routing_neuron_barriers_blocked
            }
        )
    )
    blocked_barriers = tuple(
        sorted(
            {
                barrier
                for evidence in records
                for barrier in evidence.routing_neuron_barriers_blocked
            }
        )
    )
    runtime_decisions = tuple(
        sorted(
            {
                evidence.routing_neuron_decision
                for evidence in records
                if evidence.routing_neuron_decision is not None
            }
        )
    )
    fallback_reasons = tuple(
        sorted(
            {
                evidence.routing_neuron_fallback_reason
                for evidence in records
                if evidence.routing_neuron_fallback_reason is not None
            }
        )
    )
    session_runtime_decision_counter = Counter(
        record.decision for record in session_runtime_records
    )
    session_runtime_barrier_counter = Counter(
        barrier
        for record in session_runtime_records
        for barrier in record.barriers_blocked
    )
    session_runtime_fallback_counter = Counter(
        record.fallback_reason
        for record in session_runtime_records
        if record.fallback_reason
    )
    session_runtime_outcome_counter = Counter(
        record.outcome_label or "unknown"
        for record in session_runtime_records
    )
    blocked_runtime_decisions = _count_blocked_runtime_decisions(session_runtime_records)
    fallback_runtime_decisions = _count_fallback_runtime_decisions(session_runtime_records)
    degraded_runtime_decisions = _count_degraded_runtime_decisions(session_runtime_records)
    selected_not_applied_runtime_decisions = _count_selected_not_applied_runtime_decisions(
        tuple(session_runtime_records)
    )
    runtime_presence_status = _resolve_runtime_observability_status(
        total_decisions=len(session_runtime_records),
        applied_decisions=sum(1 for record in session_runtime_records if record.applied),
        blocked_decisions=blocked_runtime_decisions,
        fallback_decisions=fallback_runtime_decisions,
        no_signal_decisions=session_runtime_decision_counter.get("no_signal", 0),
    )
    runtime_validation_status = _resolve_runtime_validation_status(runtime_presence_status)
    frequent_runtime_barriers = _format_ranked_runtime_counts(session_runtime_barrier_counter)
    frequent_runtime_fallbacks = _format_ranked_runtime_counts(session_runtime_fallback_counter)
    frequent_runtime_outcomes = _format_ranked_runtime_counts(session_runtime_outcome_counter)
    recent_runtime_decisions = tuple(
        f"{record.decision}:{record.selected_id or 'baseline'}:{record.selected_state or 'none'}"
        for record in session_runtime_records[-5:]
    )
    recent_runtime_outcomes = tuple(
        f"{record.outcome_label or 'unknown'}:{record.decision}"
        for record in session_runtime_records[-5:]
    )
    recent_applied_influences = tuple(
        f"{record.influence or 'none'}:{record.outcome_label or 'unknown'}"
        for record in session_runtime_records[-5:]
        if record.applied
    )
    promotion_ready_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.readiness_band in {ROUTING_READINESS_EMERGING, ROUTING_READINESS_NEAR_READY}
        )
    )
    resolved_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.review_status == REVIEW_STATUS_RESOLVED
        )
    )
    stale_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.review_status == REVIEW_STATUS_STALE
        )
    )
    reopened_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.review_status == REVIEW_STATUS_REOPENED
            or candidate.alert_status == ALERT_STATUS_REOPENED
        )
    )
    watch_neurons = tuple(sorted(candidate.neuron_id for candidate in registry.list_watch()))
    review_queue_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.review_priority in {
                ROUTING_REVIEW_PRIORITY_HIGH,
                ROUTING_REVIEW_PRIORITY_MEDIUM,
            }
        )
    )
    admin_actions = tuple(
        f"{action.action_type}:{action.neuron_id}:{action.reason}"
        for action in registry.list_admin_actions()[-3:]
    )
    action_outcomes = tuple(
        sorted(
            f"{candidate.neuron_id}:{candidate.action_outcome}"
            for candidate in registry.candidates.values()
            if candidate.action_outcome is not None
        )
    )
    shortlisted_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.selection_status == ROUTING_SELECTION_SHORTLISTED
        )
    )
    discarded_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.discardable_flag
        )
    )
    bridge_ready_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_READY
        )
    )
    bridge_candidate_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_CANDIDATE
        )
    )
    bridge_blocked_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_BLOCKED
        )
    )
    bridge_deferred_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_DEFERRED
        )
    )
    rehearsal_ready_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_READY
        )
    )
    rehearsal_candidate_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_CANDIDATE
        )
    )
    rehearsal_blocked_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_BLOCKED
        )
    )
    rehearsal_deferred_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.bridge_rehearsal_status == ROUTING_REHEARSAL_DEFERRED
        )
    )
    cutover_near_go_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.cutover_readiness == ROUTING_CUTOVER_NEAR_GO
        )
    )
    cutover_go_candidate_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.cutover_readiness == ROUTING_CUTOVER_GO_CANDIDATE
        )
    )
    approved_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.launch_status == ROUTING_LAUNCH_APPROVED
        )
    )
    support_only_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.launch_status == ROUTING_LAUNCH_SUPPORT_ONLY
        )
    )
    hold_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.launch_status == ROUTING_LAUNCH_HOLD
        )
    )
    rejected_neurons = tuple(
        sorted(
            candidate.neuron_id
            for candidate in registry.candidates.values()
            if candidate.launch_status == ROUTING_LAUNCH_REJECTED
        )
    )
    conflicts = tuple(
        conflict
        for conflict in registry.conflict_log
        if session_id in conflict or any(conflict.endswith(candidate_id) for candidate_id in emerging_candidates)
    )
    baseline_wins = len(baseline_preferred_cases)
    return SessionRoutingSummary(
        session_id=session_id,
        detected_patterns=detected_patterns,
        activated_routes=activated_routes,
        compared_routes=compared_routes,
        conflicts=conflicts,
        emerging_candidates=emerging_candidates,
        review_opportunities=review_opportunities,
        applied_neurons=applied_neurons,
        paused_neurons=paused_neurons,
        cooldown_neurons=cooldown_neurons,
        baseline_preferred_cases=baseline_preferred_cases,
        useful_neurons=useful_neurons,
        fragile_neurons=fragile_neurons,
        fallback_cases=fallback_cases,
        promotion_ready_neurons=promotion_ready_neurons,
        considered_neurons=considered_neurons,
        blocked_neurons=blocked_neurons,
        blocked_barriers=blocked_barriers,
        runtime_decisions=runtime_decisions,
        fallback_reasons=fallback_reasons,
        frequent_runtime_barriers=frequent_runtime_barriers,
        frequent_runtime_fallbacks=frequent_runtime_fallbacks,
        frequent_runtime_outcomes=frequent_runtime_outcomes,
        recent_runtime_decisions=recent_runtime_decisions,
        recent_runtime_outcomes=recent_runtime_outcomes,
        total_runtime_decisions=len(session_runtime_records),
        considered_runtime_decisions=sum(1 for record in session_runtime_records if record.considered),
        selected_runtime_decisions=sum(1 for record in session_runtime_records if record.selected),
        applied_runtime_decisions=sum(1 for record in session_runtime_records if record.applied),
        selected_not_applied_runtime_decisions=selected_not_applied_runtime_decisions,
        blocked_runtime_decisions=blocked_runtime_decisions,
        no_signal_runtime_decisions=session_runtime_decision_counter.get("no_signal", 0),
        fallback_runtime_decisions=fallback_runtime_decisions,
        degraded_runtime_decisions=degraded_runtime_decisions,
        runtime_presence_status=runtime_presence_status,
        runtime_validation_status=runtime_validation_status,
        recent_applied_influences=recent_applied_influences,
        watch_neurons=watch_neurons,
        review_queue_neurons=review_queue_neurons,
        admin_actions=admin_actions,
        resolved_neurons=resolved_neurons,
        stale_neurons=stale_neurons,
        reopened_neurons=reopened_neurons,
        action_outcomes=action_outcomes,
        shortlisted_neurons=shortlisted_neurons,
        discarded_neurons=discarded_neurons,
        bridge_ready_neurons=bridge_ready_neurons,
        bridge_candidate_neurons=bridge_candidate_neurons,
        bridge_blocked_neurons=bridge_blocked_neurons,
        bridge_deferred_neurons=bridge_deferred_neurons,
        rehearsal_ready_neurons=rehearsal_ready_neurons,
        rehearsal_candidate_neurons=rehearsal_candidate_neurons,
        rehearsal_blocked_neurons=rehearsal_blocked_neurons,
        rehearsal_deferred_neurons=rehearsal_deferred_neurons,
        cutover_near_go_neurons=cutover_near_go_neurons,
        cutover_go_candidate_neurons=cutover_go_candidate_neurons,
        approved_neurons=approved_neurons,
        support_only_neurons=support_only_neurons,
        hold_neurons=hold_neurons,
        rejected_neurons=rejected_neurons,
        gains_summary=f"ganancia operativa neta {gains}; baseline mejor {baseline_wins} veces",
    )


def refresh_routing_session_summary(
    registry: RoutingNeuronRegistry,
    session_id: str,
) -> RoutingNeuronRegistry:
    summary = _build_session_summary(session_id, registry)
    if summary is None:
        return registry
    return registry.register_session_summary(summary)


def _refresh_candidate_scores(
    candidate: RoutingNeuronCandidate,
    history: dict[str, int],
) -> RoutingNeuronCandidate:
    confidence_tier, confidence_progress = _resolve_confidence_tier(candidate, history)
    stability_label = _resolve_stability_label(candidate, history)
    score = build_routing_score(
        expected_gain=candidate.expected_gain,
        estimated_cost=candidate.estimated_cost,
        estimated_latency=candidate.estimated_latency,
        success_count=len(candidate.success_history),
        failure_count=len(candidate.failure_history),
        quality_delta=candidate.expected_gain,
        verification_delta=0.0,
        consistency_delta=0.0,
        activation_frequency=candidate.activation_frequency,
        activated_components=candidate.activated_components,
        baseline_win_count=history["baseline_win_count"],
        fallback_frequency=history["fallback_frequency"],
        recent_conflict_load=candidate.recent_conflict_count,
        stable_activation_streak=history["stable_activation_streak"],
        confidence_progress=confidence_progress,
        budget_violation_count=history["budget_violation_count"],
    )
    return replace(
        candidate,
        efficiency_score=score.efficiency_score,
        stability_score=score.stability_score,
        quality_score=score.quality_score,
        reusability_score=score.reusability_score,
        global_routing_score=score.global_routing_score,
        stability_label=stability_label,
        confidence_tier=confidence_tier,
        successful_activations=history["successful_activations"],
        failed_activations=history["failed_activations"],
        baseline_win_count=history["baseline_win_count"],
        recent_fallback_count=history["recent_fallback_count"],
        stable_activation_streak=history["stable_activation_streak"],
    )


def _build_recommendation(candidate: RoutingNeuronCandidate) -> RoutingPromotionRecommendation | None:
    if candidate.neuron_state == ROUTING_STATE_PAUSED:
        return None

    if candidate.cooldown_turns_remaining > 0:
        return None

    if candidate.stability_label in {ROUTING_STABILITY_FRAGILE, ROUTING_STABILITY_DEGRADING}:
        return None

    if (
        candidate.promotion_stage == PROMOTION_STAGE_MICRO_MODEL
        and candidate.readiness_band == ROUTING_READINESS_NEAR_READY
        and candidate.global_routing_score >= 0.9
        and candidate.successful_activations >= 6
    ):
        return RoutingPromotionRecommendation(
            neuron_id=candidate.neuron_id,
            recommended_stage=PROMOTION_STAGE_MICRO_MODEL,
            reason="la neurona ya muestra valor sostenido, estabilidad alta y señal clara de promoción futura",
            confidence="high",
        )

    if (
        candidate.promotion_stage == PROMOTION_STAGE_ADAPTER
        and candidate.readiness_band in {ROUTING_READINESS_EMERGING, ROUTING_READINESS_NEAR_READY}
        and candidate.confidence_tier == ROUTING_CONFIDENCE_SUSTAINED_VALUE
        and candidate.global_routing_score >= 0.78
        and candidate.successful_activations >= 4
    ):
        return RoutingPromotionRecommendation(
            neuron_id=candidate.neuron_id,
            recommended_stage=PROMOTION_STAGE_ADAPTER,
            reason="el patrón ya muestra valor sostenido frente a baseline y merece evaluación estructural controlada",
            confidence="high",
        )

    if (
        candidate.promotion_stage == PROMOTION_STAGE_SPECIALIZED_PROMPT
        and candidate.confidence_tier in {
            ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
            ROUTING_CONFIDENCE_SUSTAINED_VALUE,
        }
        and candidate.readiness_band in {ROUTING_READINESS_WATCH, ROUTING_READINESS_EMERGING, ROUTING_READINESS_NEAR_READY}
        and candidate.global_routing_score >= 0.65
        and candidate.successful_activations >= 2
    ):
        return RoutingPromotionRecommendation(
            neuron_id=candidate.neuron_id,
            recommended_stage=PROMOTION_STAGE_SPECIALIZED_PROMPT,
            reason="la primera promoción fuerte por defecto sigue siendo specialized_prompt: la neurona ya tiene señal útil, reversible y eficiente",
            confidence="medium",
        )

    return None


def _build_repertoire_entry(
    candidate: RoutingNeuronCandidate,
    recommendation: RoutingPromotionRecommendation | None,
    latest_admin_action=None,
) -> RoutingRepertoireEntry:
    review_priority, review_reason = _resolve_review_priority(candidate)
    if candidate.review_priority != ROUTING_REVIEW_PRIORITY_NONE:
        review_priority = candidate.review_priority
        review_reason = candidate.review_reason

    action_suggestion = candidate.action_suggestion or _resolve_action_suggestion(candidate)
    action_outcome = (
        latest_admin_action.outcome
        if latest_admin_action is not None and latest_admin_action.outcome is not None
        else candidate.action_outcome
    )
    if latest_admin_action is not None and latest_admin_action.review_status is not None:
        review_status = latest_admin_action.review_status
    else:
        review_status = candidate.review_status
    if latest_admin_action is not None and latest_admin_action.alert_status is not None:
        alert_status = latest_admin_action.alert_status
    else:
        alert_status = candidate.alert_status
    return RoutingRepertoireEntry(
        neuron_id=candidate.neuron_id,
        neuron_state=candidate.neuron_state,
        neuron_type=candidate.neuron_type,
        promotion_stage=candidate.promotion_stage,
        activated_components=candidate.activated_components,
        estimated_cost=candidate.estimated_cost,
        efficiency_score=candidate.efficiency_score,
        stability_score=candidate.stability_score,
        quality_score=candidate.quality_score,
        reusability_score=candidate.reusability_score,
        global_routing_score=candidate.global_routing_score,
        confidence_tier=candidate.confidence_tier,
        stability_label=candidate.stability_label,
        trend_label=_resolve_trend_label(candidate),
        cooldown_turns_remaining=candidate.cooldown_turns_remaining,
        successful_activations=candidate.successful_activations,
        failed_activations=candidate.failed_activations,
        baseline_win_count=candidate.baseline_win_count,
        recent_fallback_count=candidate.recent_fallback_count,
        stable_activation_streak=candidate.stable_activation_streak,
        recent_conflict_count=candidate.recent_conflict_count,
        times_applied=candidate.times_applied,
        last_decision=candidate.last_decision,
        last_used_at=candidate.last_used_at,
        alerts=candidate.alerts,
        promotion_ready_signal=candidate.promotion_ready_signal,
        readiness_band=candidate.readiness_band,
        readiness_reason=candidate.readiness_reason,
        curation_status=candidate.curation_status,
        curation_reason=candidate.curation_reason,
        selection_status=candidate.selection_status,
        selection_reason=candidate.selection_reason,
        influence_readiness=candidate.influence_readiness,
        influence_reason=candidate.influence_reason,
        bridge_preflight_status=candidate.bridge_preflight_status,
        bridge_priority=candidate.bridge_priority,
        bridge_rationale=candidate.bridge_rationale,
        bridge_blockers=candidate.bridge_blockers,
        conceptual_role_fit=candidate.conceptual_role_fit,
        conceptual_fit_reason=candidate.conceptual_fit_reason,
        bridge_rehearsal_status=candidate.bridge_rehearsal_status,
        rehearsal_priority=candidate.rehearsal_priority,
        rehearsal_rationale=candidate.rehearsal_rationale,
        rehearsal_blockers=candidate.rehearsal_blockers,
        cutover_readiness=candidate.cutover_readiness,
        cutover_rationale=candidate.cutover_rationale,
        rollback_concerns=candidate.rollback_concerns,
        launch_status=candidate.launch_status,
        launch_rationale=candidate.launch_rationale,
        cutover_role=candidate.cutover_role,
        cutover_role_reason=candidate.cutover_role_reason,
        activation_order=candidate.activation_order,
        activation_order_reason=candidate.activation_order_reason,
        dependency_hints=candidate.dependency_hints,
        rollback_triggers=candidate.rollback_triggers,
        fallback_target=candidate.fallback_target,
        safe_reversion=candidate.safe_reversion,
        no_go_conditions=candidate.no_go_conditions,
        watch_status=candidate.watch_status,
        watch_reason=candidate.watch_reason,
        review_priority=review_priority,
        review_reason=review_reason,
        review_status=review_status,
        alert_status=alert_status,
        action_outcome=action_outcome,
        action_outcome_reason=candidate.action_outcome_reason,
        stale_flag=(
            review_status == REVIEW_STATUS_STALE
            or (
                alert_status == ALERT_STATUS_ACKNOWLEDGED
                and candidate.alert_cycles >= 2
            )
        ),
        discardable_flag=candidate.discardable_flag,
        action_suggestion=action_suggestion,
        last_admin_action=candidate.last_admin_action,
        last_admin_reason=candidate.last_admin_reason,
        recommendation_stage=(
            recommendation.recommended_stage
            if recommendation is not None
            else None
        ),
    )


def _format_ranked_runtime_counts(counter: Counter[str], *, limit: int = 3) -> tuple[str, ...]:
    return tuple(
        f"{label} x{count}"
        for label, count in counter.most_common(limit)
        if label
    )


def _runtime_core():
    from backend.app.routing_neuron.core import runtime as runtime_core

    return runtime_core


def _count_blocked_runtime_decisions(records) -> int:
    return _runtime_core().count_blocked_runtime_decisions(tuple(records))


def _count_fallback_runtime_decisions(records) -> int:
    return _runtime_core().count_fallback_runtime_decisions(tuple(records))


def _count_degraded_runtime_decisions(records) -> int:
    return _runtime_core().count_degraded_runtime_decisions(tuple(records))


def _resolve_runtime_observability_status(
    *,
    total_decisions: int,
    applied_decisions: int,
    blocked_decisions: int,
    fallback_decisions: int,
    no_signal_decisions: int,
) -> str:
    return _runtime_core().resolve_runtime_observability_status(
        total_decisions=total_decisions,
        applied_decisions=applied_decisions,
        blocked_decisions=blocked_decisions,
        fallback_decisions=fallback_decisions,
        no_signal_decisions=no_signal_decisions,
    )


def _resolve_runtime_validation_status(observability_status: str) -> str:
    return _runtime_core().resolve_runtime_validation_status(observability_status)


def _resolve_runtime_decision_path(record) -> str:
    return _runtime_core().resolve_runtime_decision_path(record)


def _count_selected_not_applied_runtime_decisions(records) -> int:
    return _runtime_core().count_selected_not_applied_runtime_decisions(tuple(records))


def _count_no_candidate_runtime_decisions(records) -> int:
    return _runtime_core().count_no_candidate_runtime_decisions(tuple(records))


def _build_runtime_recent_activity(registry: RoutingNeuronRegistry) -> tuple[str, ...]:
    if not registry.runtime_records:
        return ()
    return tuple(
        (
            f"{record.selected_id or 'baseline'} "
            f"(path {visible_decision_path_label(record.decision_path or _resolve_runtime_decision_path(record))}, "
            f"decision {record.decision}, influence {record.influence or 'none'}, state {record.selected_state or 'none'}, "
            f"barriers {','.join(record.barriers_blocked) or 'none'}, "
            f"fallback {record.fallback_reason or 'none'}, "
            f"outcome {record.outcome_label or 'unknown'}"
            + (
                f", resumen {record.outcome_summary}"
                if record.outcome_summary
                else ""
            )
            + ")"
        )
        for record in registry.runtime_records[-3:]
    )


def build_routing_repertoire_snapshot(
    registry: RoutingNeuronRegistry,
) -> RoutingRepertoireSnapshot:
    activation_count = sum(candidate.activation_frequency for candidate in registry.active.values())
    runtime_decision_counter = Counter(record.decision for record in registry.runtime_records)
    runtime_barrier_counter = Counter(
        barrier
        for record in registry.runtime_records
        for barrier in record.barriers_blocked
    )
    runtime_fallback_counter = Counter(
        record.fallback_reason
        for record in registry.runtime_records
        if record.fallback_reason
    )
    runtime_outcome_counter = Counter(
        record.outcome_label or "unknown"
        for record in registry.runtime_records
    )
    runtime_blocked_count = _count_blocked_runtime_decisions(registry.runtime_records)
    runtime_fallback_count = _count_fallback_runtime_decisions(registry.runtime_records)
    runtime_degraded_count = _count_degraded_runtime_decisions(registry.runtime_records)
    runtime_selected_not_applied_count = _count_selected_not_applied_runtime_decisions(
        registry.runtime_records
    )
    runtime_no_candidate_count = _count_no_candidate_runtime_decisions(
        registry.runtime_records
    )
    runtime_observability_status = _resolve_runtime_observability_status(
        total_decisions=len(registry.runtime_records),
        applied_decisions=sum(1 for record in registry.runtime_records if record.applied),
        blocked_decisions=runtime_blocked_count,
        fallback_decisions=runtime_fallback_count,
        no_signal_decisions=runtime_decision_counter.get("no_signal", 0),
    )
    runtime_validation_status = _resolve_runtime_validation_status(runtime_observability_status)
    runtime_considered_ids = tuple(
        sorted(
            {
                neuron_id
                for record in registry.runtime_records
                for neuron_id in record.considered_ids
            }
        )
    )
    runtime_applied_ids = tuple(
        sorted(
            {
                record.selected_id
                for record in registry.runtime_records
                if record.applied and record.selected_id is not None
            }
        )
    )
    runtime_blocked_ids = tuple(
        sorted(
            {
                record.selected_id
                for record in registry.runtime_records
                if record.selected_id is not None
                and record.decision in {
                    "blocked_by_barrier",
                    "paused",
                    "cooldown",
                }
            }
        )
    )
    latest_admin_actions = {
        action.neuron_id: action
        for action in registry.admin_log
    }
    latest_admin_outcomes = {
        action.neuron_id: action.outcome
        for action in registry.admin_log
    }
    entries = tuple(
        sorted(
            (
                _build_repertoire_entry(
                    candidate,
                    registry.promotion_recommendations.get(candidate.neuron_id),
                    latest_admin_actions.get(candidate.neuron_id),
                )
                for candidate in registry.candidates.values()
            ),
            key=lambda entry: (
                entry.neuron_state != ROUTING_STATE_ACTIVE,
                entry.launch_status != ROUTING_LAUNCH_APPROVED,
                entry.launch_status != ROUTING_LAUNCH_SUPPORT_ONLY,
                entry.cutover_readiness != ROUTING_CUTOVER_GO_CANDIDATE,
                entry.bridge_rehearsal_status != ROUTING_REHEARSAL_READY,
                entry.selection_status != ROUTING_SELECTION_SHORTLISTED,
                entry.bridge_preflight_status != ROUTING_BRIDGE_PREFLIGHT_READY,
                entry.influence_readiness != ROUTING_INFLUENCE_BRIDGE_WATCH,
                not entry.promotion_ready_signal,
                -entry.global_routing_score,
                entry.neuron_id,
            ),
        )
    )
    recent_activity = _build_runtime_recent_activity(registry)
    if not recent_activity:
        recent_activity = tuple(
            f"{entry.neuron_id} ({entry.neuron_state}, {entry.confidence_tier}, {entry.stability_label}, readiness {entry.readiness_band}, seleccion {entry.selection_status}, puente {entry.bridge_preflight_status}, rehearsal {entry.bridge_rehearsal_status}, cutover {entry.cutover_readiness}, launch {entry.launch_status}, role {entry.cutover_role}, influence {entry.influence_readiness}, review {entry.review_status}, alerta {entry.alert_status}, score {entry.global_routing_score})"
            for entry in entries[:3]
        )
    if not recent_activity and registry.observed_patterns:
        recent_activity = tuple(
            f"{pattern.pattern_id} ({pattern.state}, {pattern.neuron_type}, freq {pattern.activation_frequency})"
            for pattern in tuple(sorted(registry.observed_patterns.values(), key=lambda item: item.last_seen_at, reverse=True))[:2]
        )
    return RoutingRepertoireSnapshot(
        observed_patterns=tuple(sorted(registry.observed_patterns.keys())),
        candidate_ids=tuple(sorted(registry.candidates.keys())),
        active_ids=tuple(sorted(registry.active.keys())),
        paused_ids=tuple(sorted(candidate.neuron_id for candidate in registry.list_paused())),
        activation_count=activation_count,
        alerts=registry.alerts,
        recommendation_ids=tuple(sorted(registry.promotion_recommendations.keys())),
        recent_conflicts=registry.conflict_log[-5:],
        entries=entries,
        recent_activity=recent_activity,
        runtime_record_count=len(registry.runtime_records),
        runtime_considered_count=sum(1 for record in registry.runtime_records if record.considered),
        runtime_selected_count=sum(1 for record in registry.runtime_records if record.selected),
        runtime_applied_count=sum(1 for record in registry.runtime_records if record.applied),
        runtime_selected_not_applied_count=runtime_selected_not_applied_count,
        runtime_blocked_count=runtime_blocked_count,
        runtime_fallback_count=runtime_fallback_count,
        runtime_degraded_count=runtime_degraded_count,
        runtime_no_signal_count=runtime_decision_counter.get("no_signal", 0),
        runtime_no_candidate_count=runtime_no_candidate_count,
        runtime_paused_count=runtime_decision_counter.get("paused", 0),
        runtime_cooldown_count=runtime_decision_counter.get("cooldown", 0),
        runtime_history_window_limit=ROUTING_RUNTIME_HISTORY_LIMIT,
        runtime_observability_status=runtime_observability_status,
        runtime_validation_status=runtime_validation_status,
        runtime_considered_ids=runtime_considered_ids,
        runtime_applied_ids=runtime_applied_ids,
        runtime_blocked_ids=runtime_blocked_ids,
        runtime_barrier_hotspots=_format_ranked_runtime_counts(runtime_barrier_counter),
        runtime_fallback_hotspots=_format_ranked_runtime_counts(runtime_fallback_counter),
        runtime_outcome_hotspots=_format_ranked_runtime_counts(runtime_outcome_counter),
        runtime_recent_decisions=tuple(
            f"{record.decision}:{record.selected_id or 'baseline'}:{record.selected_state or 'none'}"
            for record in registry.runtime_records[-5:]
        ),
        runtime_recent_paths=tuple(
            record.decision_path or _resolve_runtime_decision_path(record)
            for record in registry.runtime_records[-5:]
        ),
        runtime_recent_outcomes=tuple(
            f"{record.outcome_label or 'unknown'}:{record.decision}"
            for record in registry.runtime_records[-5:]
        ),
        runtime_recent_applied_influences=tuple(
            f"{record.influence or 'none'}:{record.outcome_label or 'unknown'}"
            for record in registry.runtime_records[-5:]
            if record.applied
        ),
        top_score_ids=tuple(entry.neuron_id for entry in sorted(entries, key=lambda entry: entry.global_routing_score, reverse=True)[:3]),
        top_confidence_ids=tuple(
            entry.neuron_id
            for entry in sorted(
                entries,
                key=lambda entry: (
                    entry.confidence_tier == ROUTING_CONFIDENCE_SUSTAINED_VALUE,
                    entry.confidence_tier == ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
                    entry.global_routing_score,
                ),
                reverse=True,
            )[:3]
        ),
        top_stability_ids=tuple(
            entry.neuron_id
            for entry in sorted(
                entries,
                key=lambda entry: (
                    entry.stability_label in {ROUTING_STABILITY_STABLE, ROUTING_STABILITY_IMPROVING},
                    -entry.recent_fallback_count,
                    entry.global_routing_score,
                ),
                reverse=True,
            )[:3]
        ),
        alerted_ids=tuple(entry.neuron_id for entry in entries if entry.alerts),
        cooldown_ids=tuple(entry.neuron_id for entry in entries if entry.cooldown_turns_remaining > 0),
        readiness_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.readiness_band in {ROUTING_READINESS_EMERGING, ROUTING_READINESS_NEAR_READY}
        ),
        watch_ids=tuple(entry.neuron_id for entry in entries if entry.watch_status),
        review_queue_ids=tuple(
            entry.neuron_id
            for entry in sorted(
                entries,
                key=lambda entry: (
                    entry.review_priority == ROUTING_REVIEW_PRIORITY_HIGH,
                    entry.review_priority == ROUTING_REVIEW_PRIORITY_MEDIUM,
                    entry.readiness_band == ROUTING_READINESS_NEAR_READY,
                    entry.global_routing_score,
                ),
                reverse=True,
            )
            if entry.review_priority in {
                ROUTING_REVIEW_PRIORITY_HIGH,
                ROUTING_REVIEW_PRIORITY_MEDIUM,
            }
        ),
        recent_admin_actions=tuple(
            f"{action.action_type}:{action.neuron_id}:{action.reason}:{action.outcome or 'pending'}"
            for action in registry.admin_log[-5:]
        ),
        open_review_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.review_status in {REVIEW_STATUS_OPEN, REVIEW_STATUS_WATCH}
        ),
        resolved_review_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.review_status == REVIEW_STATUS_RESOLVED
        ),
        stale_ids=tuple(entry.neuron_id for entry in entries if entry.stale_flag),
        reopened_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.review_status == REVIEW_STATUS_REOPENED
        ),
        reopened_alert_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.alert_status == ALERT_STATUS_REOPENED
        ),
        helped_ids=tuple(
            entry.neuron_id
            for entry in entries
            if (
                entry.action_outcome == ACTION_OUTCOME_HELPED
                or latest_admin_outcomes.get(entry.neuron_id) == ACTION_OUTCOME_HELPED
            )
        ),
        useful_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.curation_status == ROUTING_CURATION_USEFUL
        ),
        shortlist_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.selection_status == ROUTING_SELECTION_SHORTLISTED
        ),
        observed_only_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.selection_status == ROUTING_SELECTION_OBSERVED_ONLY
        ),
        discardable_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.discardable_flag or entry.selection_status == ROUTING_SELECTION_DISCARDABLE
        ),
        bridge_ready_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_READY
        ),
        bridge_slate_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.bridge_preflight_status in {
                ROUTING_BRIDGE_PREFLIGHT_CANDIDATE,
                ROUTING_BRIDGE_PREFLIGHT_READY,
            }
        ),
        bridge_blocked_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_BLOCKED
        ),
        bridge_deferred_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_DEFERRED
        ),
        rehearsal_ready_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.bridge_rehearsal_status == ROUTING_REHEARSAL_READY
        ),
        rehearsal_slate_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.bridge_rehearsal_status in {
                ROUTING_REHEARSAL_CANDIDATE,
                ROUTING_REHEARSAL_READY,
            }
        ),
        rehearsal_blocked_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.bridge_rehearsal_status == ROUTING_REHEARSAL_BLOCKED
        ),
        rehearsal_deferred_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.bridge_rehearsal_status == ROUTING_REHEARSAL_DEFERRED
        ),
        cutover_near_go_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.cutover_readiness == ROUTING_CUTOVER_NEAR_GO
        ),
        cutover_go_candidate_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.cutover_readiness == ROUTING_CUTOVER_GO_CANDIDATE
        ),
        rollback_risk_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.rollback_concerns
        ),
        stack_fit_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.conceptual_role_fit != (ROUTING_STACK_FIT_NEUTRAL,)
        ),
        approved_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.launch_status == ROUTING_LAUNCH_APPROVED
        ),
        support_only_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.launch_status == ROUTING_LAUNCH_SUPPORT_ONLY
        ),
        hold_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.launch_status == ROUTING_LAUNCH_HOLD
        ),
        rejected_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.launch_status == ROUTING_LAUNCH_REJECTED
        ),
        launch_slate_ids=tuple(
            entry.neuron_id
            for entry in entries
            if entry.launch_status in {
                ROUTING_LAUNCH_APPROVED,
                ROUTING_LAUNCH_SUPPORT_ONLY,
                ROUTING_LAUNCH_HOLD,
            }
        ),
        activation_order_ids=tuple(
            entry.neuron_id
            for entry in sorted(
                (entry for entry in entries if entry.activation_order is not None),
                key=lambda entry: (entry.activation_order or 999, entry.neuron_id),
            )
        ),
    )


def build_routing_launch_dossier(
    registry: RoutingNeuronRegistry,
) -> RoutingLaunchDossier:
    snapshot = build_routing_repertoire_snapshot(registry)
    launch_entries = tuple(
        sorted(
            (
                RoutingLaunchDossierEntry(
                    neuron_id=entry.neuron_id,
                    neuron_type=entry.neuron_type,
                    promotion_stage=entry.promotion_stage,
                    launch_status=entry.launch_status,
                    launch_rationale=entry.launch_rationale,
                    cutover_role=entry.cutover_role,
                    cutover_role_reason=entry.cutover_role_reason,
                    activation_order=entry.activation_order,
                    activation_order_reason=entry.activation_order_reason,
                    dependency_hints=entry.dependency_hints,
                    rollback_triggers=entry.rollback_triggers,
                    fallback_target=entry.fallback_target,
                    safe_reversion=entry.safe_reversion,
                    no_go_conditions=entry.no_go_conditions,
                    bridge_preflight_status=entry.bridge_preflight_status,
                    bridge_rehearsal_status=entry.bridge_rehearsal_status,
                    cutover_readiness=entry.cutover_readiness,
                    conceptual_role_fit=entry.conceptual_role_fit,
                    rollback_concerns=entry.rollback_concerns,
                    global_routing_score=entry.global_routing_score,
                    confidence_tier=entry.confidence_tier,
                    stability_label=entry.stability_label,
                )
                for entry in snapshot.entries
                if entry.launch_status != ROUTING_LAUNCH_NONE
            ),
            key=lambda entry: (
                _LAUNCH_STATUS_PRIORITY.get(entry.launch_status, 9),
                entry.activation_order if entry.activation_order is not None else 999,
                -entry.global_routing_score,
                entry.neuron_id,
            ),
        )
    )

    approved_ids = tuple(
        entry.neuron_id for entry in launch_entries if entry.launch_status == ROUTING_LAUNCH_APPROVED
    )
    support_only_ids = tuple(
        entry.neuron_id
        for entry in launch_entries
        if entry.launch_status == ROUTING_LAUNCH_SUPPORT_ONLY
    )
    hold_ids = tuple(
        entry.neuron_id for entry in launch_entries if entry.launch_status == ROUTING_LAUNCH_HOLD
    )
    rejected_ids = tuple(
        entry.neuron_id
        for entry in launch_entries
        if entry.launch_status == ROUTING_LAUNCH_REJECTED
    )
    activation_order_ids = tuple(
        entry.neuron_id
        for entry in launch_entries
        if entry.activation_order is not None
    )
    residual_blockers = tuple(
        dict.fromkeys(
            blocker
            for entry in launch_entries
            if entry.launch_status in {ROUTING_LAUNCH_HOLD, ROUTING_LAUNCH_REJECTED}
            for blocker in entry.no_go_conditions
        )
    )
    dependency_map = tuple(
        f"{entry.neuron_id}:{', '.join(entry.dependency_hints)}"
        for entry in launch_entries
        if entry.dependency_hints
    )
    rollback_plan_summary = tuple(
        f"{entry.neuron_id}: triggers {', '.join(entry.rollback_triggers)}; fallback {entry.fallback_target or 'sin fallback'}"
        for entry in launch_entries
        if entry.rollback_triggers or entry.fallback_target
    )

    if approved_ids and not hold_ids and len(residual_blockers) <= 1:
        package_recommendation = "go_candidate"
        package_rationale = (
            "ya existe un núcleo administrativo aprobable para V0.39 con pocos blockers residuales"
        )
    elif approved_ids:
        package_recommendation = "conditional_go"
        package_rationale = (
            "ya existe base aprobada, pero todavía conviene entrar con hold/support y rollback explícito"
        )
    elif support_only_ids or hold_ids:
        package_recommendation = "hold"
        package_rationale = (
            "todavía no hay núcleo aprobado suficiente; conviene mantener el paquete en preparación"
        )
    else:
        package_recommendation = "no_go"
        package_rationale = (
            "todavía no hay una slate final limpia para sostener el cambio hacia V0.39"
        )

    return RoutingLaunchDossier(
        entries=launch_entries,
        approved_ids=approved_ids,
        support_only_ids=support_only_ids,
        hold_ids=hold_ids,
        rejected_ids=rejected_ids,
        activation_order_ids=activation_order_ids,
        residual_blockers=residual_blockers,
        dependency_map=dependency_map,
        rollback_plan_summary=rollback_plan_summary,
        package_recommendation=package_recommendation,
        package_rationale=package_rationale,
    )


def run_routing_maintenance(
    registry: RoutingNeuronRegistry,
) -> RoutingMaintenanceReport:
    updated_registry = replace(registry, promotion_recommendations={})
    activated_candidates: list[str] = []
    paused_candidates: list[str] = []
    cooldown_candidates: list[str] = []
    promotion_ready_candidates: list[str] = []
    recommendation_ids: list[str] = []
    alerts: list[str] = []
    watch_ids: list[str] = []
    review_queue_ids: list[str] = []
    resolved_review_ids: list[str] = []
    stale_ids: list[str] = []
    shortlist_ids: list[str] = []
    discardable_ids: list[str] = []
    bridge_ready_ids: list[str] = []
    bridge_slate_ids: list[str] = []
    bridge_blocked_ids: list[str] = []
    bridge_deferred_ids: list[str] = []
    rehearsal_ready_ids: list[str] = []
    rehearsal_slate_ids: list[str] = []
    rehearsal_blocked_ids: list[str] = []
    rehearsal_deferred_ids: list[str] = []
    cutover_near_go_ids: list[str] = []
    cutover_go_candidate_ids: list[str] = []
    rollback_risk_ids: list[str] = []

    refreshed_candidates: dict[str, RoutingNeuronCandidate] = {}
    for neuron_id, candidate in registry.candidates.items():
        history = _build_candidate_history(registry, candidate)
        refreshed = _refresh_candidate_scores(candidate, history)

        if (
            refreshed.neuron_state != ROUTING_STATE_ACTIVE
            and refreshed.neuron_state != ROUTING_STATE_PAUSED
            and refreshed.activation_frequency >= MIN_ACTIVE_FREQUENCY
            and refreshed.global_routing_score >= MIN_ACTIVE_ROUTING_SCORE
            and refreshed.stability_score >= 0.55
            and refreshed.cooldown_turns_remaining == 0
        ):
            refreshed = replace(refreshed, neuron_state=ROUTING_STATE_ACTIVE)
            activated_candidates.append(neuron_id)

        if (
            refreshed.times_applied >= 3
            and (
                refreshed.expected_gain < 0.18
                or refreshed.baseline_win_count > refreshed.successful_activations
            )
        ):
            refreshed = replace(
                refreshed,
                cooldown_turns_remaining=max(refreshed.cooldown_turns_remaining, DEFAULT_COOLDOWN_TURNS),
                last_decision="cooldown",
                stability_label=ROUTING_STABILITY_DEGRADING,
                promotion_ready_signal=False,
                alerts=tuple(dict.fromkeys(refreshed.alerts + ("overuse_detected",))),
            )
            cooldown_candidates.append(neuron_id)

        if (
            len(refreshed.failure_history) > len(refreshed.success_history)
            or refreshed.stability_label == ROUTING_STABILITY_FRAGILE
        ):
            refreshed = replace(
                refreshed,
                neuron_state=ROUTING_STATE_PAUSED,
                paused_reason="fragility_detected",
                last_decision="paused",
                stability_label=ROUTING_STABILITY_FRAGILE,
                promotion_ready_signal=False,
                alerts=tuple(dict.fromkeys(refreshed.alerts + ("fragility_detected",))),
            )
            paused_candidates.append(neuron_id)

        refreshed = replace(
            refreshed,
            promotion_ready_signal=_should_flag_promotion_readiness(refreshed),
        )
        readiness_band, readiness_reason = _resolve_readiness_band(refreshed)
        review_priority, review_reason = _resolve_review_priority(refreshed)
        review_status, resolved_review_reason, review_cycles = _resolve_review_status(
            refreshed,
            review_priority,
        )
        alert_status, alert_cycles = _resolve_alert_status(refreshed)
        action_outcome, action_outcome_reason = _resolve_action_outcome(
            refreshed,
            review_status=review_status,
            alert_status=alert_status,
            review_cycles=review_cycles,
            alert_cycles=alert_cycles,
        )
        watch_status = refreshed.watch_status
        watch_reason = refreshed.watch_reason
        if review_status == REVIEW_STATUS_RESOLVED:
            watch_status = False
            watch_reason = None
        elif (
            not watch_status
            and review_priority in {
                ROUTING_REVIEW_PRIORITY_HIGH,
                ROUTING_REVIEW_PRIORITY_MEDIUM,
            }
        ):
            watch_status = True
            watch_reason = review_reason or readiness_reason

        refreshed = replace(
            refreshed,
            readiness_band=readiness_band,
            readiness_reason=readiness_reason,
            review_priority=review_priority,
            review_reason=review_reason or resolved_review_reason,
            review_status=review_status,
            alert_status=alert_status,
            action_outcome=action_outcome,
            action_outcome_reason=action_outcome_reason,
            review_cycles=review_cycles,
            alert_cycles=alert_cycles,
            watch_status=watch_status,
            watch_reason=watch_reason,
        )
        curation_status, curation_reason = _resolve_curation_status(refreshed)
        refreshed = replace(
            refreshed,
            curation_status=curation_status,
            curation_reason=curation_reason,
        )
        influence_readiness, influence_reason = _resolve_influence_readiness(refreshed)
        refreshed = replace(
            refreshed,
            influence_readiness=influence_readiness,
            influence_reason=influence_reason,
        )
        selection_status, selection_reason, discardable_flag = _resolve_selection_status(refreshed)
        refreshed = replace(
            refreshed,
            selection_status=selection_status,
            selection_reason=selection_reason,
            discardable_flag=discardable_flag,
        )
        conceptual_role_fit, conceptual_fit_reason = _resolve_conceptual_role_fit(refreshed)
        refreshed = replace(
            refreshed,
            conceptual_role_fit=conceptual_role_fit,
            conceptual_fit_reason=conceptual_fit_reason,
        )
        bridge_preflight_status, bridge_rationale, bridge_blockers, bridge_priority = _resolve_bridge_preflight(refreshed)
        refreshed = replace(
            refreshed,
            bridge_preflight_status=bridge_preflight_status,
            bridge_rationale=bridge_rationale,
            bridge_blockers=bridge_blockers,
            bridge_priority=bridge_priority,
        )
        refreshed = replace(
            refreshed,
            rollback_concerns=_resolve_rollback_concerns(refreshed),
        )
        rehearsal_status, rehearsal_rationale, rehearsal_blockers, rehearsal_priority = _resolve_bridge_rehearsal(refreshed)
        refreshed = replace(
            refreshed,
            bridge_rehearsal_status=rehearsal_status,
            rehearsal_rationale=rehearsal_rationale,
            rehearsal_blockers=rehearsal_blockers,
            rehearsal_priority=rehearsal_priority,
        )
        cutover_readiness, cutover_rationale, cutover_risks = _resolve_cutover_readiness(refreshed)
        refreshed = replace(
            refreshed,
            cutover_readiness=cutover_readiness,
            cutover_rationale=cutover_rationale,
            rollback_concerns=cutover_risks,
        )
        cutover_role, cutover_role_reason = _resolve_cutover_role(refreshed)
        launch_status, launch_rationale, launch_no_go_conditions = _resolve_launch_status(
            refreshed,
            cutover_role,
        )
        rollback_triggers, fallback_target, safe_reversion, no_go_conditions = _resolve_rollback_plan(
            refreshed,
            launch_status,
        )
        refreshed = replace(
            refreshed,
            launch_status=launch_status,
            launch_rationale=launch_rationale,
            cutover_role=cutover_role,
            cutover_role_reason=cutover_role_reason,
            dependency_hints=_resolve_dependency_hints(refreshed, cutover_role),
            rollback_triggers=rollback_triggers,
            fallback_target=fallback_target,
            safe_reversion=safe_reversion,
            no_go_conditions=tuple(dict.fromkeys(launch_no_go_conditions + no_go_conditions)),
        )
        refreshed = replace(
            refreshed,
            action_suggestion=_resolve_action_suggestion(refreshed),
        )
        updated_registry = updated_registry.update_last_admin_action_state(
            neuron_id,
            outcome=action_outcome,
            review_status=review_status,
            alert_status=alert_status,
        )
        if refreshed.readiness_band in {ROUTING_READINESS_EMERGING, ROUTING_READINESS_NEAR_READY}:
            promotion_ready_candidates.append(neuron_id)
        if refreshed.watch_status:
            watch_ids.append(neuron_id)
        if refreshed.review_priority in {
            ROUTING_REVIEW_PRIORITY_HIGH,
            ROUTING_REVIEW_PRIORITY_MEDIUM,
        }:
            review_queue_ids.append(neuron_id)
        if refreshed.review_status == REVIEW_STATUS_RESOLVED:
            resolved_review_ids.append(neuron_id)
        if (
            refreshed.review_status == REVIEW_STATUS_STALE
            or (
                refreshed.alert_status == ALERT_STATUS_ACKNOWLEDGED
                and refreshed.alert_cycles >= 2
            )
        ):
            stale_ids.append(neuron_id)
        if refreshed.selection_status == ROUTING_SELECTION_SHORTLISTED:
            shortlist_ids.append(neuron_id)
        if refreshed.discardable_flag:
            discardable_ids.append(neuron_id)
        if refreshed.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_READY:
            bridge_ready_ids.append(neuron_id)
        if refreshed.bridge_preflight_status in {
            ROUTING_BRIDGE_PREFLIGHT_CANDIDATE,
            ROUTING_BRIDGE_PREFLIGHT_READY,
        }:
            bridge_slate_ids.append(neuron_id)
        if refreshed.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_BLOCKED:
            bridge_blocked_ids.append(neuron_id)
        if refreshed.bridge_preflight_status == ROUTING_BRIDGE_PREFLIGHT_DEFERRED:
            bridge_deferred_ids.append(neuron_id)
        if refreshed.bridge_rehearsal_status == ROUTING_REHEARSAL_READY:
            rehearsal_ready_ids.append(neuron_id)
        if refreshed.bridge_rehearsal_status in {
            ROUTING_REHEARSAL_CANDIDATE,
            ROUTING_REHEARSAL_READY,
        }:
            rehearsal_slate_ids.append(neuron_id)
        if refreshed.bridge_rehearsal_status == ROUTING_REHEARSAL_BLOCKED:
            rehearsal_blocked_ids.append(neuron_id)
        if refreshed.bridge_rehearsal_status == ROUTING_REHEARSAL_DEFERRED:
            rehearsal_deferred_ids.append(neuron_id)
        if refreshed.cutover_readiness == ROUTING_CUTOVER_NEAR_GO:
            cutover_near_go_ids.append(neuron_id)
        if refreshed.cutover_readiness == ROUTING_CUTOVER_GO_CANDIDATE:
            cutover_go_candidate_ids.append(neuron_id)
        if refreshed.rollback_concerns:
            rollback_risk_ids.append(neuron_id)
        if refreshed.alerts:
            for alert in refreshed.alerts:
                alerts.append(
                    alert if ":" in alert else f"{neuron_id}:{alert}"
                )
        if refreshed.cooldown_turns_remaining > 0:
            alerts.append(f"{neuron_id}:cooldown")
        if refreshed.neuron_state == ROUTING_STATE_PAUSED and refreshed.paused_reason:
            alerts.append(f"{neuron_id}:inestable")

        recommendation = _build_recommendation(refreshed)
        if recommendation is not None:
            recommendation_ids.append(recommendation.neuron_id)
            updated_registry = updated_registry.register_recommendation(recommendation)

        refreshed_candidates[neuron_id] = refreshed

    refreshed_candidates = _assign_launch_activation_order(refreshed_candidates)
    updated_registry = replace(updated_registry, candidates=refreshed_candidates)
    updated_active = {
        neuron_id: candidate
        for neuron_id, candidate in refreshed_candidates.items()
        if candidate.neuron_state == ROUTING_STATE_ACTIVE
    }
    updated_registry = replace(updated_registry, active=updated_active)

    session_ids = tuple(sorted({evidence.session_id for evidence in updated_registry.evidence_records.values()}))
    updated_sessions: list[str] = []
    for session_id in session_ids:
        summary = _build_session_summary(session_id, updated_registry)
        if summary is not None:
            updated_registry = updated_registry.register_session_summary(summary)
            updated_sessions.append(session_id)

    if alerts:
        updated_registry = replace(updated_registry, alerts=tuple(dict.fromkeys(alerts)))

    launch_dossier = build_routing_launch_dossier(updated_registry)

    return RoutingMaintenanceReport(
        registry=updated_registry,
        updated_sessions=tuple(updated_sessions),
        activated_candidates=tuple(activated_candidates),
        paused_candidates=tuple(paused_candidates),
        cooldown_candidates=tuple(cooldown_candidates),
        promotion_ready_candidates=tuple(promotion_ready_candidates),
        recommendation_ids=tuple(recommendation_ids),
        alerts=updated_registry.alerts,
        watch_ids=tuple(dict.fromkeys(watch_ids)),
        review_queue_ids=tuple(dict.fromkeys(review_queue_ids)),
        resolved_review_ids=tuple(dict.fromkeys(resolved_review_ids)),
        stale_ids=tuple(dict.fromkeys(stale_ids)),
        shortlist_ids=tuple(dict.fromkeys(shortlist_ids)),
        discardable_ids=tuple(dict.fromkeys(discardable_ids)),
        bridge_ready_ids=tuple(dict.fromkeys(bridge_ready_ids)),
        bridge_slate_ids=tuple(dict.fromkeys(bridge_slate_ids)),
        bridge_blocked_ids=tuple(dict.fromkeys(bridge_blocked_ids)),
        bridge_deferred_ids=tuple(dict.fromkeys(bridge_deferred_ids)),
        rehearsal_ready_ids=tuple(dict.fromkeys(rehearsal_ready_ids)),
        rehearsal_slate_ids=tuple(dict.fromkeys(rehearsal_slate_ids)),
        rehearsal_blocked_ids=tuple(dict.fromkeys(rehearsal_blocked_ids)),
        rehearsal_deferred_ids=tuple(dict.fromkeys(rehearsal_deferred_ids)),
        cutover_near_go_ids=tuple(dict.fromkeys(cutover_near_go_ids)),
        cutover_go_candidate_ids=tuple(dict.fromkeys(cutover_go_candidate_ids)),
        rollback_risk_ids=tuple(dict.fromkeys(rollback_risk_ids)),
        approved_ids=launch_dossier.approved_ids,
        support_only_ids=launch_dossier.support_only_ids,
        hold_ids=launch_dossier.hold_ids,
        rejected_ids=launch_dossier.rejected_ids,
        launch_dossier=launch_dossier,
    )
