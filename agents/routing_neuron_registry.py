"""Legacy Routing Neuron registry backplane for AURA compatibility.

Canonical semantics now live under ``backend.app.routing_neuron``.
This module remains as a compatibility surface while V1.x keeps the
historic registry structures available to older agents and maintenance code.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone


PROMOTION_STAGE_SPECIALIZED_PROMPT = "specialized_prompt"
PROMOTION_STAGE_ADAPTER = "adapter"
PROMOTION_STAGE_LORA = "lora"
PROMOTION_STAGE_DISTILLATION = "distillation"
PROMOTION_STAGE_MICRO_MODEL = "micro_model"

PROMOTION_STAGES = (
    PROMOTION_STAGE_SPECIALIZED_PROMPT,
    PROMOTION_STAGE_ADAPTER,
    PROMOTION_STAGE_LORA,
    PROMOTION_STAGE_DISTILLATION,
    PROMOTION_STAGE_MICRO_MODEL,
)

ROUTING_STATE_OBSERVED_PATTERN = "observed_pattern"
ROUTING_STATE_CANDIDATE = "candidate"
ROUTING_STATE_ACTIVE = "active"
ROUTING_STATE_PAUSED = "paused"

ROUTING_NEURON_STATES = (
    ROUTING_STATE_OBSERVED_PATTERN,
    ROUTING_STATE_CANDIDATE,
    ROUTING_STATE_ACTIVE,
    ROUTING_STATE_PAUSED,
)

ROUTING_TYPE_SELECTION = "selection"
ROUTING_TYPE_TRANSFORMATION = "transformation"
ROUTING_TYPE_CONTROL = "control"

ROUTING_NEURON_TYPES = (
    ROUTING_TYPE_SELECTION,
    ROUTING_TYPE_TRANSFORMATION,
    ROUTING_TYPE_CONTROL,
)

ROUTING_CONFIDENCE_EARLY_SIGNAL = "early_signal"
ROUTING_CONFIDENCE_CONFIRMED_PATTERN = "confirmed_pattern"
ROUTING_CONFIDENCE_SUSTAINED_VALUE = "sustained_value"

ROUTING_CONFIDENCE_TIERS = (
    ROUTING_CONFIDENCE_EARLY_SIGNAL,
    ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
    ROUTING_CONFIDENCE_SUSTAINED_VALUE,
)

ROUTING_STABILITY_OBSERVING = "observing"
ROUTING_STABILITY_STABLE = "stable"
ROUTING_STABILITY_FRAGILE = "fragile"
ROUTING_STABILITY_IMPROVING = "improving"
ROUTING_STABILITY_DEGRADING = "degrading"

ROUTING_STABILITY_LABELS = (
    ROUTING_STABILITY_OBSERVING,
    ROUTING_STABILITY_STABLE,
    ROUTING_STABILITY_FRAGILE,
    ROUTING_STABILITY_IMPROVING,
    ROUTING_STABILITY_DEGRADING,
)

ROUTING_READINESS_NOT_READY = "not_ready"
ROUTING_READINESS_WATCH = "watch"
ROUTING_READINESS_EMERGING = "emerging"
ROUTING_READINESS_NEAR_READY = "near_ready"

ROUTING_READINESS_BANDS = (
    ROUTING_READINESS_NOT_READY,
    ROUTING_READINESS_WATCH,
    ROUTING_READINESS_EMERGING,
    ROUTING_READINESS_NEAR_READY,
)

ROUTING_CURATION_USEFUL = "useful_consistent"
ROUTING_CURATION_PROMISING = "promising_observed"
ROUTING_CURATION_NOISY = "noisy"
ROUTING_CURATION_DISCARDABLE = "discardable_temporary"

ROUTING_CURATION_STATUSES = (
    ROUTING_CURATION_USEFUL,
    ROUTING_CURATION_PROMISING,
    ROUTING_CURATION_NOISY,
    ROUTING_CURATION_DISCARDABLE,
)

ROUTING_SELECTION_OBSERVED_ONLY = "observed_only"
ROUTING_SELECTION_SHORTLISTED = "shortlisted"
ROUTING_SELECTION_HOLD = "hold"
ROUTING_SELECTION_DISCARDABLE = "discardable"

ROUTING_SELECTION_STATUSES = (
    ROUTING_SELECTION_OBSERVED_ONLY,
    ROUTING_SELECTION_SHORTLISTED,
    ROUTING_SELECTION_HOLD,
    ROUTING_SELECTION_DISCARDABLE,
)

ROUTING_INFLUENCE_NOT_READY = "not_ready"
ROUTING_INFLUENCE_EMERGING = "emerging"
ROUTING_INFLUENCE_SHORTLIST_READY = "shortlist_ready"
ROUTING_INFLUENCE_BRIDGE_WATCH = "bridge_watch"

ROUTING_INFLUENCE_READINESS_STATES = (
    ROUTING_INFLUENCE_NOT_READY,
    ROUTING_INFLUENCE_EMERGING,
    ROUTING_INFLUENCE_SHORTLIST_READY,
    ROUTING_INFLUENCE_BRIDGE_WATCH,
)

ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED = "not_considered"
ROUTING_BRIDGE_PREFLIGHT_CANDIDATE = "candidate"
ROUTING_BRIDGE_PREFLIGHT_READY = "preflight_ready"
ROUTING_BRIDGE_PREFLIGHT_BLOCKED = "blocked"
ROUTING_BRIDGE_PREFLIGHT_DEFERRED = "deferred"

ROUTING_BRIDGE_PREFLIGHT_STATUSES = (
    ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED,
    ROUTING_BRIDGE_PREFLIGHT_CANDIDATE,
    ROUTING_BRIDGE_PREFLIGHT_READY,
    ROUTING_BRIDGE_PREFLIGHT_BLOCKED,
    ROUTING_BRIDGE_PREFLIGHT_DEFERRED,
)

ROUTING_REHEARSAL_NOT_IN_REHEARSAL = "not_in_rehearsal"
ROUTING_REHEARSAL_CANDIDATE = "rehearsal_candidate"
ROUTING_REHEARSAL_READY = "rehearsal_ready"
ROUTING_REHEARSAL_BLOCKED = "rehearsal_blocked"
ROUTING_REHEARSAL_DEFERRED = "rehearsal_deferred"

ROUTING_REHEARSAL_STATUSES = (
    ROUTING_REHEARSAL_NOT_IN_REHEARSAL,
    ROUTING_REHEARSAL_CANDIDATE,
    ROUTING_REHEARSAL_READY,
    ROUTING_REHEARSAL_BLOCKED,
    ROUTING_REHEARSAL_DEFERRED,
)

ROUTING_CUTOVER_NOT_READY = "not_ready"
ROUTING_CUTOVER_WATCH = "watch"
ROUTING_CUTOVER_NEAR_GO = "near_go"
ROUTING_CUTOVER_GO_CANDIDATE = "go_candidate"
ROUTING_CUTOVER_BLOCKED = "blocked"

ROUTING_CUTOVER_READINESS_BANDS = (
    ROUTING_CUTOVER_NOT_READY,
    ROUTING_CUTOVER_WATCH,
    ROUTING_CUTOVER_NEAR_GO,
    ROUTING_CUTOVER_GO_CANDIDATE,
    ROUTING_CUTOVER_BLOCKED,
)

ROUTING_LAUNCH_NONE = "none"
ROUTING_LAUNCH_APPROVED = "approved"
ROUTING_LAUNCH_SUPPORT_ONLY = "support_only"
ROUTING_LAUNCH_HOLD = "hold"
ROUTING_LAUNCH_REJECTED = "rejected"

ROUTING_LAUNCH_STATUSES = (
    ROUTING_LAUNCH_NONE,
    ROUTING_LAUNCH_APPROVED,
    ROUTING_LAUNCH_SUPPORT_ONLY,
    ROUTING_LAUNCH_HOLD,
    ROUTING_LAUNCH_REJECTED,
)

ROUTING_ROLE_NONE = "none"
ROUTING_ROLE_ROUTER_SUPPORT = "router_support"
ROUTING_ROLE_PRIMARY_SUPPORT = "primary_support"
ROUTING_ROLE_CRITIC_SUPPORT = "critic_support"
ROUTING_ROLE_SAFETY_CHECK = "safety_check"
ROUTING_ROLE_MIGRATION_GUARD = "migration_guard"
ROUTING_ROLE_CONTEXT_FILTER = "context_filter"

ROUTING_LAUNCH_ROLES = (
    ROUTING_ROLE_NONE,
    ROUTING_ROLE_ROUTER_SUPPORT,
    ROUTING_ROLE_PRIMARY_SUPPORT,
    ROUTING_ROLE_CRITIC_SUPPORT,
    ROUTING_ROLE_SAFETY_CHECK,
    ROUTING_ROLE_MIGRATION_GUARD,
    ROUTING_ROLE_CONTEXT_FILTER,
)

ROUTING_STACK_FIT_SMOLLM2 = "smollm2_router_micro_expert"
ROUTING_STACK_FIT_GRANITE = "granite_primary_conversational"
ROUTING_STACK_FIT_OLMO = "olmo_critic_verifier"
ROUTING_STACK_FIT_NEUTRAL = "neutral"

ROUTING_STACK_FIT_LABELS = (
    ROUTING_STACK_FIT_SMOLLM2,
    ROUTING_STACK_FIT_GRANITE,
    ROUTING_STACK_FIT_OLMO,
    ROUTING_STACK_FIT_NEUTRAL,
)

ROUTING_REVIEW_PRIORITY_NONE = "none"
ROUTING_REVIEW_PRIORITY_LOW = "low"
ROUTING_REVIEW_PRIORITY_MEDIUM = "medium"
ROUTING_REVIEW_PRIORITY_HIGH = "high"

ROUTING_REVIEW_PRIORITIES = (
    ROUTING_REVIEW_PRIORITY_NONE,
    ROUTING_REVIEW_PRIORITY_LOW,
    ROUTING_REVIEW_PRIORITY_MEDIUM,
    ROUTING_REVIEW_PRIORITY_HIGH,
)

REVIEW_STATUS_NONE = "none"
REVIEW_STATUS_OPEN = "open"
REVIEW_STATUS_WATCH = "watch"
REVIEW_STATUS_RESOLVED = "resolved"
REVIEW_STATUS_STALE = "stale"
REVIEW_STATUS_REOPENED = "reopened"

REVIEW_STATUSES = (
    REVIEW_STATUS_NONE,
    REVIEW_STATUS_OPEN,
    REVIEW_STATUS_WATCH,
    REVIEW_STATUS_RESOLVED,
    REVIEW_STATUS_STALE,
    REVIEW_STATUS_REOPENED,
)

ALERT_STATUS_NONE = "none"
ALERT_STATUS_OPEN = "open"
ALERT_STATUS_ACKNOWLEDGED = "acknowledged"
ALERT_STATUS_RESOLVED = "resolved"
ALERT_STATUS_REOPENED = "reopened"

ALERT_STATUSES = (
    ALERT_STATUS_NONE,
    ALERT_STATUS_OPEN,
    ALERT_STATUS_ACKNOWLEDGED,
    ALERT_STATUS_RESOLVED,
    ALERT_STATUS_REOPENED,
)

ACTION_OUTCOME_PENDING_OBSERVATION = "pending_observation"
ACTION_OUTCOME_HELPED = "helped"
ACTION_OUTCOME_NO_CLEAR_CHANGE = "no_clear_change"
ACTION_OUTCOME_WORSENED = "worsened"

ACTION_OUTCOMES = (
    ACTION_OUTCOME_PENDING_OBSERVATION,
    ACTION_OUTCOME_HELPED,
    ACTION_OUTCOME_NO_CLEAR_CHANGE,
    ACTION_OUTCOME_WORSENED,
)

RUNTIME_INFLUENCE_SKIP_CRITIC = "skip_critic"
RUNTIME_INFLUENCE_KEEP_BASELINE = "keep_baseline"
RUNTIME_INFLUENCE_APPLY_TRANSFORM = "apply_transform"

MIN_COACTIVATED_COMPONENTS = 2
MIN_ACTIVATION_FREQUENCY = 2
MIN_EXPECTED_GAIN = 0.05
MAX_ACCEPTABLE_COST = 1.0
MIN_GLOBAL_ROUTING_SCORE = 0.55
MIN_ACTIVE_ROUTING_SCORE = 0.65
MIN_ACTIVE_FREQUENCY = 3
DEFAULT_COOLDOWN_TURNS = 2
ROUTING_RUNTIME_HISTORY_LIMIT = 96


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_record_id(prefix: str, sequence: int, signature: str) -> str:
    compact_signature = (
        signature.lower()
        .replace(" ", "_")
        .replace(":", "_")
        .replace("/", "_")
        .replace("|", "_")
    )
    compact_signature = compact_signature[:48] or "generic"
    return f"{prefix}:{sequence}:{compact_signature}"


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    observed_pattern_id: str | None
    neuron_id: str | None
    timestamp: str
    session_id: str
    task_signature: str
    task_profile: str
    risk_profile: str
    budget_profile: str
    baseline_route: str
    recent_route: str
    evaluated_route: str
    activated_components: tuple[str, ...]
    latency_ms: float
    latency_delta: float
    cost_delta: float
    quality_delta: float
    verification_delta: float
    consistency_delta: float
    success_label: str
    outcome_summary: str
    notes: str | None = None
    routing_neuron_considered: bool = False
    considered_neuron_ids: tuple[str, ...] = ()
    routing_neuron_selected: bool = False
    routing_neuron_decision: str | None = None
    routing_neuron_influence: str | None = None
    routing_neuron_barriers_checked: tuple[str, ...] = ()
    routing_neuron_barriers_blocked: tuple[str, ...] = ()
    routing_neuron_conflict: str | None = None
    routing_neuron_conflict_resolution: str | None = None
    routing_neuron_fallback_reason: str | None = None
    routing_neuron_outcome_label: str | None = None
    routing_neuron_decision_path: str | None = None


@dataclass(frozen=True)
class ObservedPattern:
    pattern_id: str
    state: str
    neuron_type: str
    task_signature: str
    activation_rule: str
    routing_condition: str
    intermediate_transform: str | None
    activated_components: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    activation_frequency: int
    success_history: tuple[str, ...]
    failure_history: tuple[str, ...]
    expected_gain: float
    estimated_cost: float
    estimated_latency: float
    last_seen_at: str


@dataclass(frozen=True)
class RoutingNeuronCandidate:
    neuron_id: str
    neuron_state: str
    neuron_type: str
    task_signature: str
    activation_rule: str
    routing_condition: str
    intermediate_transform: str | None
    success_history: tuple[str, ...]
    failure_history: tuple[str, ...]
    expected_gain: float
    estimated_cost: float
    estimated_latency: float
    activation_frequency: int
    promotion_score: float
    promotion_stage: str
    activated_components: tuple[str, ...]
    efficiency_score: float = 0.0
    stability_score: float = 0.0
    quality_score: float = 0.0
    reusability_score: float = 0.0
    global_routing_score: float = 0.0
    last_used_at: str | None = None
    times_applied: int = 0
    cooldown_turns_remaining: int = 0
    paused_reason: str | None = None
    stability_label: str = ROUTING_STABILITY_OBSERVING
    confidence_tier: str = ROUTING_CONFIDENCE_EARLY_SIGNAL
    successful_activations: int = 0
    failed_activations: int = 0
    baseline_win_count: int = 0
    recent_fallback_count: int = 0
    stable_activation_streak: int = 0
    promotion_ready_signal: bool = False
    readiness_band: str = ROUTING_READINESS_NOT_READY
    readiness_reason: str | None = None
    curation_status: str = ROUTING_CURATION_PROMISING
    curation_reason: str | None = None
    selection_status: str = ROUTING_SELECTION_OBSERVED_ONLY
    selection_reason: str | None = None
    influence_readiness: str = ROUTING_INFLUENCE_NOT_READY
    influence_reason: str | None = None
    bridge_preflight_status: str = ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED
    bridge_priority: str = ROUTING_REVIEW_PRIORITY_NONE
    bridge_rationale: str | None = None
    bridge_blockers: tuple[str, ...] = ()
    conceptual_role_fit: tuple[str, ...] = ()
    conceptual_fit_reason: str | None = None
    bridge_rehearsal_status: str = ROUTING_REHEARSAL_NOT_IN_REHEARSAL
    rehearsal_priority: str = ROUTING_REVIEW_PRIORITY_NONE
    rehearsal_rationale: str | None = None
    rehearsal_blockers: tuple[str, ...] = ()
    cutover_readiness: str = ROUTING_CUTOVER_NOT_READY
    cutover_rationale: str | None = None
    rollback_concerns: tuple[str, ...] = ()
    launch_status: str = ROUTING_LAUNCH_NONE
    launch_rationale: str | None = None
    cutover_role: str = ROUTING_ROLE_NONE
    cutover_role_reason: str | None = None
    activation_order: int | None = None
    activation_order_reason: str | None = None
    dependency_hints: tuple[str, ...] = ()
    rollback_triggers: tuple[str, ...] = ()
    fallback_target: str | None = None
    safe_reversion: str | None = None
    no_go_conditions: tuple[str, ...] = ()
    discardable_flag: bool = False
    watch_status: bool = False
    watch_reason: str | None = None
    review_priority: str = ROUTING_REVIEW_PRIORITY_NONE
    review_reason: str | None = None
    review_status: str = REVIEW_STATUS_NONE
    alert_status: str = ALERT_STATUS_NONE
    action_outcome: str | None = None
    action_outcome_reason: str | None = None
    review_cycles: int = 0
    alert_cycles: int = 0
    action_suggestion: str | None = None
    recent_conflict_count: int = 0
    last_decision: str | None = None
    last_admin_action: str | None = None
    last_admin_reason: str | None = None
    alerts: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoutingPromotionRecommendation:
    neuron_id: str
    recommended_stage: str
    reason: str
    confidence: str


@dataclass(frozen=True)
class SessionRoutingSummary:
    session_id: str
    detected_patterns: tuple[str, ...]
    activated_routes: tuple[str, ...]
    compared_routes: tuple[str, ...]
    conflicts: tuple[str, ...]
    emerging_candidates: tuple[str, ...]
    review_opportunities: tuple[str, ...]
    gains_summary: str
    applied_neurons: tuple[str, ...] = ()
    paused_neurons: tuple[str, ...] = ()
    cooldown_neurons: tuple[str, ...] = ()
    baseline_preferred_cases: tuple[str, ...] = ()
    useful_neurons: tuple[str, ...] = ()
    fragile_neurons: tuple[str, ...] = ()
    fallback_cases: tuple[str, ...] = ()
    promotion_ready_neurons: tuple[str, ...] = ()
    watch_neurons: tuple[str, ...] = ()
    review_queue_neurons: tuple[str, ...] = ()
    admin_actions: tuple[str, ...] = ()
    resolved_neurons: tuple[str, ...] = ()
    stale_neurons: tuple[str, ...] = ()
    reopened_neurons: tuple[str, ...] = ()
    action_outcomes: tuple[str, ...] = ()
    shortlisted_neurons: tuple[str, ...] = ()
    discarded_neurons: tuple[str, ...] = ()
    bridge_ready_neurons: tuple[str, ...] = ()
    bridge_candidate_neurons: tuple[str, ...] = ()
    bridge_blocked_neurons: tuple[str, ...] = ()
    bridge_deferred_neurons: tuple[str, ...] = ()
    rehearsal_ready_neurons: tuple[str, ...] = ()
    rehearsal_candidate_neurons: tuple[str, ...] = ()
    rehearsal_blocked_neurons: tuple[str, ...] = ()
    rehearsal_deferred_neurons: tuple[str, ...] = ()
    cutover_near_go_neurons: tuple[str, ...] = ()
    cutover_go_candidate_neurons: tuple[str, ...] = ()
    approved_neurons: tuple[str, ...] = ()
    support_only_neurons: tuple[str, ...] = ()
    hold_neurons: tuple[str, ...] = ()
    rejected_neurons: tuple[str, ...] = ()
    considered_neurons: tuple[str, ...] = ()
    blocked_neurons: tuple[str, ...] = ()
    blocked_barriers: tuple[str, ...] = ()
    runtime_decisions: tuple[str, ...] = ()
    fallback_reasons: tuple[str, ...] = ()
    frequent_runtime_barriers: tuple[str, ...] = ()
    frequent_runtime_fallbacks: tuple[str, ...] = ()
    frequent_runtime_outcomes: tuple[str, ...] = ()
    recent_runtime_decisions: tuple[str, ...] = ()
    recent_runtime_outcomes: tuple[str, ...] = ()
    total_runtime_decisions: int = 0
    considered_runtime_decisions: int = 0
    selected_runtime_decisions: int = 0
    applied_runtime_decisions: int = 0
    selected_not_applied_runtime_decisions: int = 0
    blocked_runtime_decisions: int = 0
    no_signal_runtime_decisions: int = 0
    fallback_runtime_decisions: int = 0
    degraded_runtime_decisions: int = 0
    runtime_presence_status: str = "runtime_ready_but_no_history"
    runtime_validation_status: str = "runtime_validation_in_progress"
    recent_applied_influences: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoutingRuntimeRecord:
    record_id: str
    timestamp: str
    session_id: str
    task_signature: str
    considered: bool
    considered_ids: tuple[str, ...]
    selected: bool
    selected_id: str | None
    selected_state: str | None
    selected_type: str | None
    influence: str | None
    barriers_checked: tuple[str, ...]
    barriers_blocked: tuple[str, ...]
    conflict: str | None
    conflict_resolution: str | None
    fallback_reason: str | None
    decision: str
    applied: bool
    outcome_label: str | None
    trace: tuple[str, ...]
    decision_path: str | None = None
    outcome_summary: str | None = None


@dataclass(frozen=True)
class RoutingAdminAction:
    action_id: str
    timestamp: str
    neuron_id: str
    action_type: str
    reason: str
    outcome: str | None = None
    review_status: str | None = None
    alert_status: str | None = None


@dataclass(frozen=True)
class RoutingNeuronRegistry:
    observed_patterns: dict[str, ObservedPattern]
    candidates: dict[str, RoutingNeuronCandidate]
    active: dict[str, RoutingNeuronCandidate]
    evidence_records: dict[str, EvidenceRecord]
    session_summaries: dict[str, SessionRoutingSummary]
    promotion_recommendations: dict[str, RoutingPromotionRecommendation]
    conflict_log: tuple[str, ...]
    alerts: tuple[str, ...]
    admin_log: tuple[RoutingAdminAction, ...]
    runtime_records: tuple[RoutingRuntimeRecord, ...]

    def register_observed_pattern(
        self,
        pattern: ObservedPattern,
    ) -> "RoutingNeuronRegistry":
        updated = dict(self.observed_patterns)
        updated[pattern.pattern_id] = pattern
        return replace(self, observed_patterns=updated)

    def register_candidate(
        self,
        candidate: RoutingNeuronCandidate,
    ) -> "RoutingNeuronRegistry":
        updated = dict(self.candidates)
        updated[candidate.neuron_id] = candidate
        updated_active = dict(self.active)
        if candidate.neuron_id in updated_active and candidate.neuron_state == ROUTING_STATE_ACTIVE:
            updated_active[candidate.neuron_id] = candidate
        elif candidate.neuron_id in updated_active and candidate.neuron_state != ROUTING_STATE_ACTIVE:
            updated_active.pop(candidate.neuron_id, None)
        return replace(self, candidates=updated, active=updated_active)

    def activate_candidate(self, neuron_id: str) -> "RoutingNeuronRegistry":
        candidate = self.candidates.get(neuron_id)
        if candidate is None:
            return self

        updated_candidate = replace(
            candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            paused_reason=None,
            readiness_reason=None,
            last_decision="activated",
        )
        updated_active = dict(self.active)
        updated_active[neuron_id] = updated_candidate
        updated_candidates = dict(self.candidates)
        updated_candidates[neuron_id] = updated_candidate
        return replace(
            self,
            candidates=updated_candidates,
            active=updated_active,
        )

    def pause_candidate(
        self,
        neuron_id: str,
        reason: str,
    ) -> "RoutingNeuronRegistry":
        candidate = self.candidates.get(neuron_id)
        if candidate is None:
            return self

        paused_candidate = replace(
            candidate,
            neuron_state=ROUTING_STATE_PAUSED,
            paused_reason=reason,
            promotion_ready_signal=False,
            readiness_band=ROUTING_READINESS_NOT_READY,
            readiness_reason=reason,
            review_status=REVIEW_STATUS_OPEN,
            review_reason=reason,
            action_outcome=ACTION_OUTCOME_PENDING_OBSERVATION,
            action_outcome_reason="la pausa necesita observación posterior",
            last_decision="paused",
        )
        updated_candidates = dict(self.candidates)
        updated_candidates[neuron_id] = paused_candidate
        updated_active = dict(self.active)
        updated_active.pop(neuron_id, None)
        return replace(self, candidates=updated_candidates, active=updated_active)

    def set_candidate_cooldown(
        self,
        neuron_id: str,
        turns: int,
        reason: str | None = None,
    ) -> "RoutingNeuronRegistry":
        candidate = self.candidates.get(neuron_id)
        if candidate is None:
            return self

        updated_candidate = replace(
            candidate,
            cooldown_turns_remaining=max(turns, 0),
            promotion_ready_signal=False,
            readiness_band=ROUTING_READINESS_NOT_READY,
            readiness_reason=reason,
            last_decision="cooldown",
            alerts=(
                candidate.alerts
                if reason is None
                else candidate.alerts + (reason,)
            ),
        )
        return self.register_candidate(updated_candidate)

    def list_paused(self) -> tuple[RoutingNeuronCandidate, ...]:
        return tuple(
            candidate
            for candidate in self.candidates.values()
            if candidate.neuron_state == ROUTING_STATE_PAUSED
        )

    def register_evidence(self, evidence: EvidenceRecord) -> "RoutingNeuronRegistry":
        updated = dict(self.evidence_records)
        updated[evidence.evidence_id] = evidence
        return replace(self, evidence_records=updated)

    def register_session_summary(
        self,
        summary: SessionRoutingSummary,
    ) -> "RoutingNeuronRegistry":
        updated = dict(self.session_summaries)
        updated[summary.session_id] = summary
        return replace(self, session_summaries=updated)

    def register_recommendation(
        self,
        recommendation: RoutingPromotionRecommendation,
    ) -> "RoutingNeuronRegistry":
        updated = dict(self.promotion_recommendations)
        updated[recommendation.neuron_id] = recommendation
        return replace(self, promotion_recommendations=updated)

    def append_conflict(self, conflict: str) -> "RoutingNeuronRegistry":
        return replace(self, conflict_log=self.conflict_log + (conflict,))

    def append_alert(self, alert: str) -> "RoutingNeuronRegistry":
        return replace(self, alerts=self.alerts + (alert,))

    def _append_admin_action(
        self,
        neuron_id: str,
        action_type: str,
        reason: str,
        *,
        outcome: str | None = ACTION_OUTCOME_PENDING_OBSERVATION,
        review_status: str | None = None,
        alert_status: str | None = None,
    ) -> "RoutingNeuronRegistry":
        action = RoutingAdminAction(
            action_id=_build_record_id("admin", len(self.admin_log) + 1, neuron_id),
            timestamp=_utc_now_iso(),
            neuron_id=neuron_id,
            action_type=action_type,
            reason=reason,
            outcome=outcome,
            review_status=review_status,
            alert_status=alert_status,
        )
        return replace(self, admin_log=self.admin_log + (action,))

    def update_last_admin_action_state(
        self,
        neuron_id: str,
        *,
        outcome: str | None = None,
        review_status: str | None = None,
        alert_status: str | None = None,
    ) -> "RoutingNeuronRegistry":
        actions = list(self.admin_log)
        for index in range(len(actions) - 1, -1, -1):
            action = actions[index]
            if action.neuron_id != neuron_id:
                continue
            actions[index] = replace(
                action,
                outcome=outcome if outcome is not None else action.outcome,
                review_status=(
                    review_status if review_status is not None else action.review_status
                ),
                alert_status=(
                    alert_status if alert_status is not None else action.alert_status
                ),
            )
            return replace(self, admin_log=tuple(actions))
        return self

    def pause_candidate_administratively(
        self,
        neuron_id: str,
        reason: str,
    ) -> "RoutingNeuronRegistry":
        candidate = self.candidates.get(neuron_id)
        if candidate is None:
            return self

        paused_candidate = replace(
            candidate,
            neuron_state=ROUTING_STATE_PAUSED,
            paused_reason=reason,
            promotion_ready_signal=False,
            readiness_band=ROUTING_READINESS_NOT_READY,
            readiness_reason=reason,
            review_status=REVIEW_STATUS_OPEN,
            review_reason=reason,
            action_outcome=ACTION_OUTCOME_PENDING_OBSERVATION,
            action_outcome_reason="la pausa administrativa necesita observación posterior",
            last_decision="admin_paused",
            last_admin_action="pause",
            last_admin_reason=reason,
        )
        updated_candidates = dict(self.candidates)
        updated_candidates[neuron_id] = paused_candidate
        updated_active = dict(self.active)
        updated_active.pop(neuron_id, None)
        updated_registry = replace(
            self,
            candidates=updated_candidates,
            active=updated_active,
        )
        return updated_registry._append_admin_action(
            neuron_id,
            "pause",
            reason,
            review_status=paused_candidate.review_status,
            alert_status=paused_candidate.alert_status,
        )

    def resume_candidate(
        self,
        neuron_id: str,
        reason: str,
    ) -> "RoutingNeuronRegistry":
        candidate = self.candidates.get(neuron_id)
        if candidate is None:
            return self

        resumed_state = (
            ROUTING_STATE_ACTIVE
            if candidate.global_routing_score >= MIN_GLOBAL_ROUTING_SCORE
            else ROUTING_STATE_CANDIDATE
        )
        resumed_candidate = replace(
            candidate,
            neuron_state=resumed_state,
            paused_reason=None,
            review_status=(
                REVIEW_STATUS_OPEN
                if candidate.review_status in {
                    REVIEW_STATUS_OPEN,
                    REVIEW_STATUS_STALE,
                    REVIEW_STATUS_REOPENED,
                }
                else candidate.review_status
            ),
            action_outcome=ACTION_OUTCOME_PENDING_OBSERVATION,
            action_outcome_reason="la reanudación necesita observación posterior",
            last_decision="admin_resumed",
            last_admin_action="resume",
            last_admin_reason=reason,
        )
        updated_candidates = dict(self.candidates)
        updated_candidates[neuron_id] = resumed_candidate
        updated_active = dict(self.active)
        if resumed_state == ROUTING_STATE_ACTIVE:
            updated_active[neuron_id] = resumed_candidate
        else:
            updated_active.pop(neuron_id, None)
        updated_registry = replace(
            self,
            candidates=updated_candidates,
            active=updated_active,
        )
        return updated_registry._append_admin_action(
            neuron_id,
            "resume",
            reason,
            review_status=resumed_candidate.review_status,
            alert_status=resumed_candidate.alert_status,
        )

    def mark_watch(
        self,
        neuron_id: str,
        reason: str,
    ) -> "RoutingNeuronRegistry":
        candidate = self.candidates.get(neuron_id)
        if candidate is None:
            return self

        watched_candidate = replace(
            candidate,
            watch_status=True,
            watch_reason=reason,
            review_status=(
                REVIEW_STATUS_STALE
                if candidate.review_status == REVIEW_STATUS_STALE
                else REVIEW_STATUS_WATCH
            ),
            review_reason=reason,
            action_outcome=ACTION_OUTCOME_PENDING_OBSERVATION,
            action_outcome_reason="el seguimiento necesita más observación",
            last_decision="watch_marked",
            last_admin_action="mark_watch",
            last_admin_reason=reason,
        )
        updated_registry = self.register_candidate(watched_candidate)
        return updated_registry._append_admin_action(
            neuron_id,
            "mark_watch",
            reason,
            review_status=watched_candidate.review_status,
            alert_status=watched_candidate.alert_status,
        )

    def clear_watch(
        self,
        neuron_id: str,
        reason: str,
    ) -> "RoutingNeuronRegistry":
        candidate = self.candidates.get(neuron_id)
        if candidate is None:
            return self

        cleared_candidate = replace(
            candidate,
            watch_status=False,
            watch_reason=None,
            review_status=REVIEW_STATUS_RESOLVED,
            review_reason=reason,
            action_outcome=ACTION_OUTCOME_PENDING_OBSERVATION,
            action_outcome_reason="el cierre de seguimiento todavía debe confirmarse",
            last_decision="watch_cleared",
            last_admin_action="clear_watch",
            last_admin_reason=reason,
        )
        updated_registry = self.register_candidate(cleared_candidate)
        return updated_registry._append_admin_action(
            neuron_id,
            "clear_watch",
            reason,
            review_status=cleared_candidate.review_status,
            alert_status=cleared_candidate.alert_status,
        )

    def acknowledge_alert(
        self,
        neuron_id: str,
        reason: str,
    ) -> "RoutingNeuronRegistry":
        candidate = self.candidates.get(neuron_id)
        if candidate is None:
            return self

        acknowledged_candidate = replace(
            candidate,
            alert_status=ALERT_STATUS_ACKNOWLEDGED,
            action_outcome=ACTION_OUTCOME_PENDING_OBSERVATION,
            action_outcome_reason="la alerta fue reconocida pero sigue bajo observación",
            last_decision="alert_acknowledged",
            last_admin_action="acknowledge_alert",
            last_admin_reason=reason,
        )
        updated_registry = self.register_candidate(acknowledged_candidate)
        return updated_registry._append_admin_action(
            neuron_id,
            "acknowledge_alert",
            reason,
            review_status=acknowledged_candidate.review_status,
            alert_status=acknowledged_candidate.alert_status,
        )

    def resolve_alert(
        self,
        neuron_id: str,
        reason: str,
    ) -> "RoutingNeuronRegistry":
        candidate = self.candidates.get(neuron_id)
        if candidate is None:
            return self

        resolved_candidate = replace(
            candidate,
            alerts=(),
            alert_status=ALERT_STATUS_RESOLVED,
            action_outcome=ACTION_OUTCOME_PENDING_OBSERVATION,
            action_outcome_reason="la resolución de alerta debe confirmarse",
            last_decision="alert_resolved",
            last_admin_action="resolve_alert",
            last_admin_reason=reason,
        )
        updated_registry = self.register_candidate(resolved_candidate)
        filtered_alerts = tuple(
            alert
            for alert in updated_registry.alerts
            if not alert.startswith(f"{neuron_id}:")
        )
        updated_registry = replace(updated_registry, alerts=filtered_alerts)
        return updated_registry._append_admin_action(
            neuron_id,
            "resolve_alert",
            reason,
            review_status=resolved_candidate.review_status,
            alert_status=resolved_candidate.alert_status,
        )

    def list_observed_patterns(self) -> tuple[ObservedPattern, ...]:
        return tuple(self.observed_patterns.values())

    def list_candidates(self) -> tuple[RoutingNeuronCandidate, ...]:
        return tuple(self.candidates.values())

    def list_active(self) -> tuple[RoutingNeuronCandidate, ...]:
        return tuple(self.active.values())

    def list_evidence(self) -> tuple[EvidenceRecord, ...]:
        return tuple(self.evidence_records.values())

    def list_recommendations(self) -> tuple[RoutingPromotionRecommendation, ...]:
        return tuple(self.promotion_recommendations.values())

    def list_watch(self) -> tuple[RoutingNeuronCandidate, ...]:
        return tuple(
            candidate
            for candidate in self.candidates.values()
            if candidate.watch_status
        )

    def list_admin_actions(self) -> tuple[RoutingAdminAction, ...]:
        return self.admin_log

    def append_runtime_record(
        self,
        record: RoutingRuntimeRecord,
    ) -> "RoutingNeuronRegistry":
        updated_records = (self.runtime_records + (record,))[-ROUTING_RUNTIME_HISTORY_LIMIT:]
        return replace(self, runtime_records=updated_records)

    def list_runtime_records(self) -> tuple[RoutingRuntimeRecord, ...]:
        return self.runtime_records


def build_empty_routing_neuron_registry() -> RoutingNeuronRegistry:
    return RoutingNeuronRegistry(
        observed_patterns={},
        candidates={},
        active={},
        evidence_records={},
        session_summaries={},
        promotion_recommendations={},
        conflict_log=(),
        alerts=(),
        admin_log=(),
        runtime_records=(),
    )


def calculate_promotion_score(
    *,
    expected_gain: float,
    activation_frequency: int,
    success_count: int,
    failure_count: int,
    estimated_cost: float,
    estimated_latency: float,
) -> float:
    latency_penalty = (
        estimated_latency / 1000.0 if estimated_latency > 10.0 else estimated_latency
    )
    raw_score = (
        (expected_gain * 100.0)
        + (activation_frequency * 4.0)
        + (success_count * 3.0)
        - (failure_count * 2.0)
        - (estimated_cost * 20.0)
        - (latency_penalty * 2.0)
    )
    return round(max(raw_score, 0.0), 3)


def should_birth_routing_neuron(
    *,
    activated_components: tuple[str, ...],
    activation_frequency: int,
    expected_gain: float,
    estimated_cost: float,
    duplicate_exists: bool = False,
) -> bool:
    return (
        len(activated_components) >= MIN_COACTIVATED_COMPONENTS
        and activation_frequency >= MIN_ACTIVATION_FREQUENCY
        and expected_gain >= MIN_EXPECTED_GAIN
        and estimated_cost <= MAX_ACCEPTABLE_COST
        and not duplicate_exists
    )


def build_evidence_record(
    *,
    task_signature: str,
    session_id: str,
    task_profile: str,
    risk_profile: str,
    budget_profile: str,
    baseline_route: str,
    recent_route: str,
    evaluated_route: str,
    activated_components: tuple[str, ...],
    latency_ms: float,
    latency_delta: float,
    cost_delta: float,
    quality_delta: float,
    verification_delta: float,
    consistency_delta: float,
    success_label: str,
    outcome_summary: str,
    notes: str | None = None,
    routing_neuron_considered: bool = False,
    considered_neuron_ids: tuple[str, ...] = (),
    routing_neuron_selected: bool = False,
    routing_neuron_decision: str | None = None,
    routing_neuron_influence: str | None = None,
    routing_neuron_barriers_checked: tuple[str, ...] = (),
    routing_neuron_barriers_blocked: tuple[str, ...] = (),
    routing_neuron_conflict: str | None = None,
    routing_neuron_conflict_resolution: str | None = None,
    routing_neuron_fallback_reason: str | None = None,
    routing_neuron_outcome_label: str | None = None,
    routing_neuron_decision_path: str | None = None,
    observed_pattern_id: str | None = None,
    neuron_id: str | None = None,
    existing_registry: RoutingNeuronRegistry | None = None,
) -> EvidenceRecord:
    sequence = (len(existing_registry.evidence_records) if existing_registry else 0) + 1
    return EvidenceRecord(
        evidence_id=_build_record_id("evidence", sequence, task_signature),
        observed_pattern_id=observed_pattern_id,
        neuron_id=neuron_id,
        timestamp=_utc_now_iso(),
        session_id=session_id,
        task_signature=task_signature,
        task_profile=task_profile,
        risk_profile=risk_profile,
        budget_profile=budget_profile,
        baseline_route=baseline_route,
        recent_route=recent_route,
        evaluated_route=evaluated_route,
        activated_components=activated_components,
        latency_ms=round(float(latency_ms), 3),
        latency_delta=round(float(latency_delta), 3),
        cost_delta=round(float(cost_delta), 3),
        quality_delta=round(float(quality_delta), 3),
        verification_delta=round(float(verification_delta), 3),
        consistency_delta=round(float(consistency_delta), 3),
        success_label=success_label,
        outcome_summary=outcome_summary,
        notes=notes,
        routing_neuron_considered=routing_neuron_considered,
        considered_neuron_ids=considered_neuron_ids,
        routing_neuron_selected=routing_neuron_selected,
        routing_neuron_decision=routing_neuron_decision,
        routing_neuron_influence=routing_neuron_influence,
        routing_neuron_barriers_checked=routing_neuron_barriers_checked,
        routing_neuron_barriers_blocked=routing_neuron_barriers_blocked,
        routing_neuron_conflict=routing_neuron_conflict,
        routing_neuron_conflict_resolution=routing_neuron_conflict_resolution,
        routing_neuron_fallback_reason=routing_neuron_fallback_reason,
        routing_neuron_outcome_label=routing_neuron_outcome_label,
        routing_neuron_decision_path=routing_neuron_decision_path,
    )


def register_routing_neuron_candidate(
    *,
    task_signature: str,
    activated_components: tuple[str, ...],
    activation_rule: str,
    routing_condition: str,
    intermediate_transform: str | None,
    success_history: tuple[str, ...],
    failure_history: tuple[str, ...],
    expected_gain: float,
    estimated_cost: float,
    estimated_latency: float,
    neuron_type: str = ROUTING_TYPE_SELECTION,
) -> RoutingNeuronCandidate | None:
    activation_frequency = len(success_history) + len(failure_history)
    if not should_birth_routing_neuron(
        activated_components=activated_components,
        activation_frequency=activation_frequency,
        expected_gain=expected_gain,
        estimated_cost=estimated_cost,
    ):
        return None

    success_count = len(success_history)
    failure_count = len(failure_history)
    activation_bonus = min(activation_frequency / 4.0, 1.0)
    efficiency_score = round(max(min(expected_gain * 2.5 + activation_bonus - (estimated_cost * 0.5), 1.0), 0.0), 3)
    stability_score = round(max(min((success_count + 1) / (activation_frequency + 1), 1.0), 0.0), 3)
    quality_score = round(max(min((expected_gain * 1.8) + (success_count * 0.08) - (failure_count * 0.12), 1.0), 0.0), 3)
    reusability_score = round(max(min((len(set(activated_components)) / 3.0) + (activation_bonus * 0.4), 1.0), 0.0), 3)
    global_routing_score = round(
        min(
            (efficiency_score * 0.4)
            + (stability_score * 0.3)
            + (quality_score * 0.2)
            + (reusability_score * 0.1),
            1.0,
        ),
        3,
    )

    return RoutingNeuronCandidate(
        neuron_id=_build_record_id("rn", activation_frequency, task_signature),
        neuron_state=ROUTING_STATE_CANDIDATE,
        neuron_type=neuron_type,
        task_signature=task_signature,
        activation_rule=activation_rule,
        routing_condition=routing_condition,
        intermediate_transform=intermediate_transform,
        success_history=success_history,
        failure_history=failure_history,
        expected_gain=expected_gain,
        estimated_cost=estimated_cost,
        estimated_latency=estimated_latency,
        activation_frequency=activation_frequency,
        promotion_score=calculate_promotion_score(
            expected_gain=expected_gain,
            activation_frequency=activation_frequency,
            success_count=success_count,
            failure_count=failure_count,
            estimated_cost=estimated_cost,
            estimated_latency=estimated_latency,
        ),
        promotion_stage=PROMOTION_STAGE_SPECIALIZED_PROMPT,
        activated_components=activated_components,
        efficiency_score=efficiency_score,
        stability_score=stability_score,
        quality_score=quality_score,
        reusability_score=reusability_score,
        global_routing_score=global_routing_score,
        last_used_at=None,
        times_applied=0,
        cooldown_turns_remaining=0,
        paused_reason=None,
        stability_label="observing",
        confidence_tier=ROUTING_CONFIDENCE_EARLY_SIGNAL,
        successful_activations=0,
        failed_activations=0,
        baseline_win_count=0,
        recent_fallback_count=0,
        stable_activation_streak=0,
        promotion_ready_signal=False,
        readiness_band=ROUTING_READINESS_NOT_READY,
        readiness_reason=None,
        recent_conflict_count=0,
        last_decision="candidate_created",
        alerts=(),
    )


def promote_routing_neuron(candidate: RoutingNeuronCandidate) -> RoutingNeuronCandidate:
    try:
        current_index = PROMOTION_STAGES.index(candidate.promotion_stage)
    except ValueError:
        current_index = 0

    next_index = min(current_index + 1, len(PROMOTION_STAGES) - 1)
    return replace(candidate, promotion_stage=PROMOTION_STAGES[next_index])
