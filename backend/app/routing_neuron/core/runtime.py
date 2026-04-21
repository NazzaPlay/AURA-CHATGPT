"""Canonical runtime entrypoints for Routing Neuron V1.x."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from agents.routing_neuron_registry import (
    MIN_GLOBAL_ROUTING_SCORE,
    ROUTING_CONFIDENCE_EARLY_SIGNAL,
    ROUTING_STATE_ACTIVE,
    ROUTING_STATE_PAUSED,
    ROUTING_TYPE_CONTROL,
    ROUTING_TYPE_SELECTION,
    ROUTING_TYPE_TRANSFORMATION,
    ROUTING_RUNTIME_HISTORY_LIMIT,
    RUNTIME_INFLUENCE_APPLY_TRANSFORM,
    RUNTIME_INFLUENCE_KEEP_BASELINE,
    RUNTIME_INFLUENCE_SKIP_CRITIC,
    RoutingNeuronCandidate,
    RoutingNeuronRegistry,
    RoutingRuntimeRecord,
    build_empty_routing_neuron_registry,
)

if TYPE_CHECKING:
    from agents.routing_policy import RoutingDecision


ROUTING_RUNTIME_NO_SIGNAL = "no_signal"
ROUTING_RUNTIME_SUGGESTED_ONLY = "suggested_only"
ROUTING_RUNTIME_APPLIED = "applied"
ROUTING_RUNTIME_BLOCKED = "blocked_by_barrier"
ROUTING_RUNTIME_PAUSED = "paused"
ROUTING_RUNTIME_COOLDOWN = "cooldown"
ROUTING_RUNTIME_FALLBACK = "fallback_to_baseline"

ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH = "no_candidate_match"
ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE = "candidate_seen_no_active_match"
ROUTING_RUNTIME_PATH_SELECTED_PAUSED = "selected_paused"
ROUTING_RUNTIME_PATH_SELECTED_COOLDOWN = "selected_cooldown"
ROUTING_RUNTIME_PATH_SELECTED_BLOCKED = "selected_blocked"
ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED = "selected_not_applied"
ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED = "selected_and_applied"

ROUTING_RUNTIME_OBSERVABILITY_NO_HISTORY = "runtime_ready_but_no_history"
ROUTING_RUNTIME_OBSERVABILITY_ONLY_NO_SIGNAL = "only_no_signal_seen"
ROUTING_RUNTIME_OBSERVABILITY_BLOCKED_ONLY = "blocked_or_baseline_only"
ROUTING_RUNTIME_OBSERVABILITY_LOW_SAMPLE = "healthy_but_low_sample"
ROUTING_RUNTIME_OBSERVABILITY_OBSERVED = "applied_activity_observed"

ROUTING_RUNTIME_VALIDATION_IN_PROGRESS = "runtime_validation_in_progress"
ROUTING_RUNTIME_VALIDATION_BASELINE_ONLY = "baseline_only_validation"
ROUTING_RUNTIME_VALIDATION_LOW_SAMPLE = "runtime_validation_low_sample"
ROUTING_RUNTIME_VALIDATION_OBSERVED = "runtime_behavior_observed"

ROUTING_ACTIVATION_BARRIER_STATE = "state"
ROUTING_ACTIVATION_BARRIER_BUDGET = "budget"
ROUTING_ACTIVATION_BARRIER_CONTEXT = "context"
ROUTING_ACTIVATION_BARRIER_COMPETITIVE = "competitive"
ROUTING_ACTIVATION_BARRIER_STABILITY = "stability"
ROUTING_ACTIVATION_BARRIER_COMPOSITION = "composition"
ROUTING_ACTIVATION_BARRIER_FALLBACK = "fallback"
ROUTING_ACTIVATION_BARRIER_COOLDOWN = "cooldown"

ROUTING_ACTIVATION_BARRIERS = (
    ROUTING_ACTIVATION_BARRIER_STATE,
    ROUTING_ACTIVATION_BARRIER_BUDGET,
    ROUTING_ACTIVATION_BARRIER_CONTEXT,
    ROUTING_ACTIVATION_BARRIER_COMPETITIVE,
    ROUTING_ACTIVATION_BARRIER_STABILITY,
    ROUTING_ACTIVATION_BARRIER_COMPOSITION,
    ROUTING_ACTIVATION_BARRIER_FALLBACK,
)

_BARRIER_REASON_SUFFIXES = {
    ROUTING_ACTIVATION_BARRIER_STATE: "state_barrier",
    ROUTING_ACTIVATION_BARRIER_BUDGET: "budget_barrier",
    ROUTING_ACTIVATION_BARRIER_CONTEXT: "context_barrier",
    ROUTING_ACTIVATION_BARRIER_COMPETITIVE: "competitive_barrier",
    ROUTING_ACTIVATION_BARRIER_STABILITY: "stability_barrier",
    ROUTING_ACTIVATION_BARRIER_COMPOSITION: "composition_barrier",
    ROUTING_ACTIVATION_BARRIER_FALLBACK: "fallback_barrier",
    ROUTING_ACTIVATION_BARRIER_COOLDOWN: "cooldown_active",
}

_CONFLICT_RESOLUTION_RULE = "highest_global_score_then_activation_frequency_then_efficiency"


@dataclass(frozen=True)
class RoutingRuntimeDecision:
    applied: bool
    decision: str
    neuron_id: str | None
    neuron_state: str | None
    neuron_type: str | None
    influence: str | None
    prompt_transform: str | None
    updated_routing_decision: str | None
    updated_gateway_mode: str | None
    trace: tuple[str, ...]
    conflict: str | None = None
    fallback_reason: str | None = None
    alerts: tuple[str, ...] = ()
    registry_snapshot: RoutingNeuronRegistry | None = None
    considered: bool = False
    considered_ids: tuple[str, ...] = ()
    selected: bool = False
    barriers_checked: tuple[str, ...] = ()
    barriers_blocked: tuple[str, ...] = ()
    conflict_resolution: str | None = None
    outcome_label: str | None = None
    decision_path: str | None = None


_DEFAULT_ROUTING_REGISTRY = build_empty_routing_neuron_registry()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_runtime_record_id(sequence: int, task_signature: str) -> str:
    compact_signature = (
        task_signature.lower()
        .replace(" ", "_")
        .replace(":", "_")
        .replace("/", "_")
        .replace("|", "_")
    )
    compact_signature = compact_signature[:48] or "runtime"
    return f"runtime:{sequence}:{compact_signature}"


def _next_runtime_record_sequence(runtime_registry: RoutingNeuronRegistry) -> int:
    if not runtime_registry.runtime_records:
        return 1

    last_record_id = runtime_registry.runtime_records[-1].record_id
    try:
        _, sequence, _ = last_record_id.split(":", 2)
        return int(sequence) + 1
    except (ValueError, TypeError):
        return len(runtime_registry.runtime_records) + 1


def count_blocked_runtime_decisions(records: tuple[RoutingRuntimeRecord, ...]) -> int:
    return sum(
        1
        for record in records
        if record.decision in {
            ROUTING_RUNTIME_BLOCKED,
            ROUTING_RUNTIME_PAUSED,
            ROUTING_RUNTIME_COOLDOWN,
        }
    )


def count_fallback_runtime_decisions(records: tuple[RoutingRuntimeRecord, ...]) -> int:
    return sum(
        1
        for record in records
        if record.fallback_reason is not None
        or record.decision in {
            ROUTING_RUNTIME_SUGGESTED_ONLY,
            ROUTING_RUNTIME_BLOCKED,
            ROUTING_RUNTIME_NO_SIGNAL,
            ROUTING_RUNTIME_PAUSED,
            ROUTING_RUNTIME_COOLDOWN,
            ROUTING_RUNTIME_FALLBACK,
        }
    )


def count_degraded_runtime_decisions(records: tuple[RoutingRuntimeRecord, ...]) -> int:
    return sum(
        1
        for record in records
        if record.outcome_label in {"fallback_no_provider", "fallback_runtime_error"}
    )


def resolve_runtime_decision_path(subject: RoutingRuntimeDecision | RoutingRuntimeRecord) -> str:
    decision = getattr(subject, "decision", None)
    applied = bool(getattr(subject, "applied", False))
    selected = bool(getattr(subject, "selected", False))
    considered_ids = tuple(getattr(subject, "considered_ids", ()) or ())
    fallback_reason = getattr(subject, "fallback_reason", None)

    if applied:
        return ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED

    if decision == ROUTING_RUNTIME_PAUSED:
        return ROUTING_RUNTIME_PATH_SELECTED_PAUSED

    if decision == ROUTING_RUNTIME_COOLDOWN:
        return ROUTING_RUNTIME_PATH_SELECTED_COOLDOWN

    if decision == ROUTING_RUNTIME_BLOCKED:
        return ROUTING_RUNTIME_PATH_SELECTED_BLOCKED

    if decision == ROUTING_RUNTIME_SUGGESTED_ONLY and selected:
        return ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED

    if decision == ROUTING_RUNTIME_NO_SIGNAL and fallback_reason == "no_match" and not considered_ids:
        return ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH

    if decision == ROUTING_RUNTIME_NO_SIGNAL and fallback_reason == "no_active_match":
        return ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE

    if selected:
        return ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED

    if considered_ids:
        return ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE

    return ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH


def count_selected_not_applied_runtime_decisions(records: tuple[RoutingRuntimeRecord, ...]) -> int:
    return sum(
        1
        for record in records
        if not record.applied
        and resolve_runtime_decision_path(record)
        in {
            ROUTING_RUNTIME_PATH_SELECTED_PAUSED,
            ROUTING_RUNTIME_PATH_SELECTED_COOLDOWN,
            ROUTING_RUNTIME_PATH_SELECTED_BLOCKED,
            ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED,
        }
    )


def count_no_candidate_runtime_decisions(records: tuple[RoutingRuntimeRecord, ...]) -> int:
    return sum(
        1
        for record in records
        if resolve_runtime_decision_path(record) == ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH
    )


def resolve_runtime_observability_status(
    *,
    total_decisions: int,
    applied_decisions: int,
    blocked_decisions: int,
    fallback_decisions: int,
    no_signal_decisions: int,
) -> str:
    if total_decisions == 0:
        return ROUTING_RUNTIME_OBSERVABILITY_NO_HISTORY

    if applied_decisions == 0 and no_signal_decisions == total_decisions:
        return ROUTING_RUNTIME_OBSERVABILITY_ONLY_NO_SIGNAL

    if applied_decisions == 0 and fallback_decisions == total_decisions:
        return ROUTING_RUNTIME_OBSERVABILITY_BLOCKED_ONLY

    if applied_decisions > 0 and total_decisions < 5:
        return ROUTING_RUNTIME_OBSERVABILITY_LOW_SAMPLE

    if applied_decisions > 0:
        return ROUTING_RUNTIME_OBSERVABILITY_OBSERVED

    if blocked_decisions > 0:
        return ROUTING_RUNTIME_OBSERVABILITY_BLOCKED_ONLY

    return ROUTING_RUNTIME_OBSERVABILITY_ONLY_NO_SIGNAL


def resolve_runtime_validation_status(observability_status: str) -> str:
    return {
        ROUTING_RUNTIME_OBSERVABILITY_NO_HISTORY: ROUTING_RUNTIME_VALIDATION_IN_PROGRESS,
        ROUTING_RUNTIME_OBSERVABILITY_ONLY_NO_SIGNAL: ROUTING_RUNTIME_VALIDATION_BASELINE_ONLY,
        ROUTING_RUNTIME_OBSERVABILITY_BLOCKED_ONLY: ROUTING_RUNTIME_VALIDATION_BASELINE_ONLY,
        ROUTING_RUNTIME_OBSERVABILITY_LOW_SAMPLE: ROUTING_RUNTIME_VALIDATION_LOW_SAMPLE,
        ROUTING_RUNTIME_OBSERVABILITY_OBSERVED: ROUTING_RUNTIME_VALIDATION_OBSERVED,
    }[observability_status]


def get_default_routing_registry() -> RoutingNeuronRegistry:
    return _DEFAULT_ROUTING_REGISTRY


def set_default_routing_registry(registry: RoutingNeuronRegistry) -> RoutingNeuronRegistry:
    global _DEFAULT_ROUTING_REGISTRY
    _DEFAULT_ROUTING_REGISTRY = registry
    return _DEFAULT_ROUTING_REGISTRY


def reset_default_routing_registry() -> RoutingNeuronRegistry:
    return set_default_routing_registry(build_empty_routing_neuron_registry())


def _matches_context(
    neuron: RoutingNeuronCandidate,
    *,
    task_signature: str,
    task_type: str,
    route_action: str | None,
    risk_profile: str,
) -> bool:
    if neuron.task_signature == task_signature:
        return True

    routing_condition = neuron.routing_condition.casefold()
    return any(
        token and token in routing_condition
        for token in (
            task_type.casefold(),
            (route_action or "").casefold(),
            risk_profile.casefold(),
        )
    )


def _evaluate_barriers(
    neuron: RoutingNeuronCandidate,
    *,
    task_signature: str,
    task_type: str,
    route_action: str | None,
    risk_profile: str,
    budget_profile: str,
    routing: "RoutingDecision",
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    checked = ROUTING_ACTIVATION_BARRIERS
    blocked: list[str] = []
    # A verified skip_critic seed can run earlier than the generic score gate
    # once repeated clean critic passes have already de-risked the pattern.
    verified_skip_critic_ready = (
        neuron.activation_frequency >= 2
        and neuron.stability_score >= 0.75
        and neuron.global_routing_score >= 0.4
        and neuron.recent_fallback_count == 0
        and "prefer_primary_only_when_verified" in neuron.activation_rule.casefold()
        and "skip_critic" in neuron.routing_condition.casefold()
        and risk_profile in {"low", "medium"}
        and routing.routing_decision == "primary_then_critic"
    )

    if neuron.neuron_state != ROUTING_STATE_ACTIVE:
        blocked.append(ROUTING_ACTIVATION_BARRIER_STATE)

    if (
        not verified_skip_critic_ready
        and (
        neuron.global_routing_score < MIN_GLOBAL_ROUTING_SCORE
        or neuron.stability_score < 0.5
        or (
            neuron.confidence_tier == ROUTING_CONFIDENCE_EARLY_SIGNAL
            and neuron.global_routing_score < 0.65
        )
        )
    ):
        blocked.append(ROUTING_ACTIVATION_BARRIER_STABILITY)

    if not _matches_context(
        neuron,
        task_signature=task_signature,
        task_type=task_type,
        route_action=route_action,
        risk_profile=risk_profile,
    ):
        blocked.append(ROUTING_ACTIVATION_BARRIER_CONTEXT)

    if budget_profile == "tight" and neuron.estimated_cost > 0.65:
        blocked.append(ROUTING_ACTIVATION_BARRIER_BUDGET)

    if neuron.recent_conflict_count >= 3:
        blocked.append(ROUTING_ACTIVATION_BARRIER_COMPETITIVE)

    if (
        len(neuron.activated_components) >= 3
        and routing.routing_decision == "primary_then_critic"
    ) or (
        neuron.dependency_hints and budget_profile == "tight"
    ):
        blocked.append(ROUTING_ACTIVATION_BARRIER_COMPOSITION)

    if routing.routing_decision not in {"primary_only", "primary_then_critic"}:
        blocked.append(ROUTING_ACTIVATION_BARRIER_FALLBACK)

    return checked, tuple(dict.fromkeys(blocked))


def _fallback_reason_for_barriers(
    neuron_id: str,
    blocked_barriers: tuple[str, ...],
) -> str:
    if not blocked_barriers:
        return "no_match"
    primary_barrier = blocked_barriers[0]
    suffix = _BARRIER_REASON_SUFFIXES.get(primary_barrier, f"{primary_barrier}_barrier")
    if suffix == "cooldown_active":
        return suffix
    return f"{neuron_id}:{suffix}"


def _resolve_runtime_effect(
    neuron: RoutingNeuronCandidate,
    *,
    risk_profile: str,
    routing: "RoutingDecision",
) -> tuple[bool, str | None, str | None, str | None]:
    condition = neuron.routing_condition.casefold()
    activation_rule = neuron.activation_rule.casefold()

    if neuron.neuron_type in {ROUTING_TYPE_SELECTION, ROUTING_TYPE_CONTROL}:
        should_skip_critic = any(
            token in condition or token in activation_rule
            for token in (
                "skip_critic",
                "prefer_primary_only",
                "critic_optional",
            )
        )
        if (
            should_skip_critic
            and routing.routing_decision == "primary_then_critic"
            and risk_profile != "high"
        ):
            return True, RUNTIME_INFLUENCE_SKIP_CRITIC, "primary_only", None

        return False, RUNTIME_INFLUENCE_KEEP_BASELINE, None, None

    if neuron.neuron_type == ROUTING_TYPE_TRANSFORMATION and neuron.intermediate_transform:
        return True, RUNTIME_INFLUENCE_APPLY_TRANSFORM, None, neuron.intermediate_transform

    return False, None, None, None


def _update_candidate_snapshot(
    registry: RoutingNeuronRegistry,
    candidate: RoutingNeuronCandidate,
) -> RoutingNeuronRegistry:
    return registry.register_candidate(candidate)


def _build_considered_trace(considered_ids: tuple[str, ...]) -> str:
    if not considered_ids:
        return "routing_neuron:considered:none"
    return f"routing_neuron:considered:{','.join(considered_ids)}"


def _build_barrier_trace(
    *,
    checked: tuple[str, ...],
    blocked: tuple[str, ...],
) -> tuple[str, ...]:
    trace = ()
    if checked:
        trace += (f"routing_neuron:barriers_checked:{','.join(checked)}",)
    if blocked:
        trace += (f"routing_neuron:barriers_blocked:{','.join(blocked)}",)
    return trace


def apply_routing_runtime(
    routing: "RoutingDecision",
    *,
    task_signature: str,
    task_type: str,
    route_action: str | None,
    risk_profile: str,
    budget_profile: str,
    registry: RoutingNeuronRegistry | None = None,
) -> RoutingRuntimeDecision:
    runtime_registry = registry or get_default_routing_registry()
    matching_candidates = [
        candidate
        for candidate in runtime_registry.candidates.values()
        if _matches_context(
            candidate,
            task_signature=task_signature,
            task_type=task_type,
            route_action=route_action,
            risk_profile=risk_profile,
        )
    ]
    considered_ids = tuple(candidate.neuron_id for candidate in matching_candidates)

    if not matching_candidates:
        return RoutingRuntimeDecision(
            applied=False,
            decision=ROUTING_RUNTIME_NO_SIGNAL,
            neuron_id=None,
            neuron_state=None,
            neuron_type=None,
            influence=None,
            prompt_transform=None,
            updated_routing_decision=None,
            updated_gateway_mode=None,
            trace=(
                "routing_neuron:decision:no_signal",
                _build_considered_trace(()),
                "routing_neuron:no_candidate_match",
                "routing_neuron:fallback:baseline",
            ),
            alerts=(),
            registry_snapshot=runtime_registry,
            considered=True,
            considered_ids=(),
            selected=False,
            barriers_checked=(),
            barriers_blocked=(),
            fallback_reason="no_match",
            decision_path=ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH,
        )

    active_candidates = [
        candidate
        for candidate in matching_candidates
        if candidate.neuron_state == ROUTING_STATE_ACTIVE
    ]
    paused_candidates = [
        candidate
        for candidate in matching_candidates
        if candidate.neuron_state == ROUTING_STATE_PAUSED
    ]
    if not active_candidates and paused_candidates:
        selected_paused = sorted(
            paused_candidates,
            key=lambda candidate: candidate.global_routing_score,
            reverse=True,
        )[0]
        blocked = (ROUTING_ACTIVATION_BARRIER_STATE,)
        return RoutingRuntimeDecision(
            applied=False,
            decision=ROUTING_RUNTIME_PAUSED,
            neuron_id=selected_paused.neuron_id,
            neuron_state=selected_paused.neuron_state,
            neuron_type=selected_paused.neuron_type,
            influence=None,
            prompt_transform=selected_paused.intermediate_transform,
            updated_routing_decision=None,
            updated_gateway_mode=None,
            trace=(
                "routing_neuron:decision:paused",
                _build_considered_trace(considered_ids),
                f"routing_neuron:selected:{selected_paused.neuron_id}",
                f"routing_neuron:state:{selected_paused.neuron_state}",
            )
            + _build_barrier_trace(checked=(ROUTING_ACTIVATION_BARRIER_STATE,), blocked=blocked)
            + (
                "routing_neuron:paused",
                "routing_neuron:fallback:baseline",
            ),
            fallback_reason=selected_paused.paused_reason or "paused",
            alerts=selected_paused.alerts,
            registry_snapshot=runtime_registry,
            considered=True,
            considered_ids=considered_ids,
            selected=True,
            barriers_checked=(ROUTING_ACTIVATION_BARRIER_STATE,),
            barriers_blocked=blocked,
            decision_path=ROUTING_RUNTIME_PATH_SELECTED_PAUSED,
        )

    if not active_candidates:
        return RoutingRuntimeDecision(
            applied=False,
            decision=ROUTING_RUNTIME_NO_SIGNAL,
            neuron_id=None,
            neuron_state=None,
            neuron_type=None,
            influence=None,
            prompt_transform=None,
            updated_routing_decision=None,
            updated_gateway_mode=None,
            trace=(
                "routing_neuron:decision:no_signal",
                _build_considered_trace(considered_ids),
                "routing_neuron:no_active_match",
                "routing_neuron:fallback:baseline",
            ),
            alerts=(),
            registry_snapshot=runtime_registry,
            considered=True,
            considered_ids=considered_ids,
            selected=False,
            barriers_checked=(ROUTING_ACTIVATION_BARRIER_STATE,),
            barriers_blocked=(ROUTING_ACTIVATION_BARRIER_STATE,),
            fallback_reason="no_active_match",
            decision_path=ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE,
        )

    active_ready = [
        candidate
        for candidate in active_candidates
        if candidate.cooldown_turns_remaining <= 0
    ]
    cooldown_candidates = [
        candidate
        for candidate in active_candidates
        if candidate.cooldown_turns_remaining > 0
    ]
    if not active_ready and cooldown_candidates:
        selected_cooldown = sorted(
            cooldown_candidates,
            key=lambda candidate: candidate.global_routing_score,
            reverse=True,
        )[0]
        cooled_candidate = replace(
            selected_cooldown,
            cooldown_turns_remaining=max(selected_cooldown.cooldown_turns_remaining - 1, 0),
            last_decision="cooldown",
        )
        updated_registry = _update_candidate_snapshot(runtime_registry, cooled_candidate)
        blocked = (ROUTING_ACTIVATION_BARRIER_COOLDOWN,)
        return RoutingRuntimeDecision(
            applied=False,
            decision=ROUTING_RUNTIME_COOLDOWN,
            neuron_id=selected_cooldown.neuron_id,
            neuron_state=selected_cooldown.neuron_state,
            neuron_type=selected_cooldown.neuron_type,
            influence=None,
            prompt_transform=selected_cooldown.intermediate_transform,
            updated_routing_decision=None,
            updated_gateway_mode=None,
            trace=(
                "routing_neuron:decision:cooldown",
                _build_considered_trace(considered_ids),
                f"routing_neuron:selected:{selected_cooldown.neuron_id}",
                f"routing_neuron:cooldown:{selected_cooldown.cooldown_turns_remaining}",
                "routing_neuron:barriers_blocked:cooldown",
                "routing_neuron:fallback:baseline",
            ),
            fallback_reason="cooldown_active",
            alerts=selected_cooldown.alerts,
            registry_snapshot=updated_registry,
            considered=True,
            considered_ids=considered_ids,
            selected=True,
            barriers_checked=(ROUTING_ACTIVATION_BARRIER_COOLDOWN,),
            barriers_blocked=blocked,
            decision_path=ROUTING_RUNTIME_PATH_SELECTED_COOLDOWN,
        )

    eligible: list[RoutingNeuronCandidate] = []
    blocked_evaluations: list[tuple[RoutingNeuronCandidate, tuple[str, ...], tuple[str, ...]]] = []

    for neuron in active_ready:
        checked, blocked = _evaluate_barriers(
            neuron,
            task_signature=task_signature,
            task_type=task_type,
            route_action=route_action,
            risk_profile=risk_profile,
            budget_profile=budget_profile,
            routing=routing,
        )
        if blocked:
            blocked_evaluations.append((neuron, checked, blocked))
        else:
            eligible.append(neuron)

    if not eligible:
        selected_blocked, checked, blocked = sorted(
            blocked_evaluations,
            key=lambda item: (
                item[0].global_routing_score,
                item[0].activation_frequency,
                item[0].efficiency_score,
            ),
            reverse=True,
        )[0]
        fallback_reason = _fallback_reason_for_barriers(selected_blocked.neuron_id, blocked)
        barrier_trace = _build_barrier_trace(checked=checked, blocked=blocked)
        legacy_barrier_item = ()
        if blocked:
            legacy_barrier_item = (
                f"routing_neuron:barrier:{_fallback_reason_for_barriers(selected_blocked.neuron_id, blocked)}",
            )
        return RoutingRuntimeDecision(
            applied=False,
            decision=ROUTING_RUNTIME_BLOCKED,
            neuron_id=selected_blocked.neuron_id,
            neuron_state=selected_blocked.neuron_state,
            neuron_type=selected_blocked.neuron_type,
            influence=None,
            prompt_transform=None,
            updated_routing_decision=None,
            updated_gateway_mode=None,
            trace=(
                "routing_neuron:decision:blocked",
                _build_considered_trace(considered_ids),
                f"routing_neuron:selected:{selected_blocked.neuron_id}",
                f"routing_neuron:state:{selected_blocked.neuron_state}",
                "routing_neuron:baseline",
                "routing_neuron:fallback:baseline",
            )
            + barrier_trace
            + legacy_barrier_item,
            fallback_reason=fallback_reason,
            alerts=selected_blocked.alerts,
            registry_snapshot=runtime_registry,
            considered=True,
            considered_ids=considered_ids,
            selected=True,
            barriers_checked=checked,
            barriers_blocked=blocked,
            decision_path=ROUTING_RUNTIME_PATH_SELECTED_BLOCKED,
        )

    ordered = sorted(
        eligible,
        key=lambda neuron: (
            neuron.global_routing_score,
            neuron.activation_frequency,
            neuron.efficiency_score,
        ),
        reverse=True,
    )
    selected = ordered[0]
    checked, blocked = _evaluate_barriers(
        selected,
        task_signature=task_signature,
        task_type=task_type,
        route_action=route_action,
        risk_profile=risk_profile,
        budget_profile=budget_profile,
        routing=routing,
    )
    conflict = None
    conflict_resolution = None

    if len(ordered) > 1:
        losing_ids = ",".join(neuron.neuron_id for neuron in ordered[1:])
        conflict = f"{selected.neuron_id}>{losing_ids}"
        conflict_resolution = _CONFLICT_RESOLUTION_RULE
        updated_registry = runtime_registry
        updated_registry = _update_candidate_snapshot(
            updated_registry,
            replace(
                selected,
                recent_conflict_count=selected.recent_conflict_count + 1,
            ),
        )
        for losing_neuron in ordered[1:]:
            updated_registry = _update_candidate_snapshot(
                updated_registry,
                replace(
                    losing_neuron,
                    recent_conflict_count=losing_neuron.recent_conflict_count + 1,
                ),
            )
        runtime_registry = updated_registry

    applied, influence, updated_route, prompt_transform = _resolve_runtime_effect(
        selected,
        risk_profile=risk_profile,
        routing=routing,
    )

    trace = (
        f"routing_neuron:decision:{ROUTING_RUNTIME_SUGGESTED_ONLY if not applied else ROUTING_RUNTIME_APPLIED}",
        _build_considered_trace(considered_ids),
        f"routing_neuron:selected:{selected.neuron_id}",
        f"routing_neuron:type:{selected.neuron_type}",
        f"routing_neuron:state:{selected.neuron_state}",
    ) + _build_barrier_trace(checked=checked, blocked=blocked)
    if conflict:
        trace = trace + (
            f"routing_neuron:conflict:{conflict}",
            f"routing_neuron:conflict_resolution:{conflict_resolution}",
        )

    if not applied:
        return RoutingRuntimeDecision(
            applied=False,
            decision=ROUTING_RUNTIME_SUGGESTED_ONLY,
            neuron_id=selected.neuron_id,
            neuron_state=selected.neuron_state,
            neuron_type=selected.neuron_type,
            influence=influence,
            prompt_transform=prompt_transform,
            updated_routing_decision=None,
            updated_gateway_mode=None,
            trace=trace + ("routing_neuron:baseline", "routing_neuron:fallback:baseline"),
            conflict=conflict,
            fallback_reason="no_runtime_effect",
            alerts=selected.alerts,
            registry_snapshot=runtime_registry,
            considered=True,
            considered_ids=considered_ids,
            selected=True,
            barriers_checked=checked,
            barriers_blocked=(),
            conflict_resolution=conflict_resolution,
            decision_path=ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED,
        )

    updated_gateway_mode = updated_route if updated_route is not None else routing.gateway_mode
    updated_selected = replace(
        selected,
        times_applied=selected.times_applied + 1,
        last_used_at=selected.last_used_at,
        last_decision=ROUTING_RUNTIME_APPLIED,
    )
    updated_registry = _update_candidate_snapshot(runtime_registry, updated_selected)
    return RoutingRuntimeDecision(
        applied=True,
        decision=ROUTING_RUNTIME_APPLIED,
        neuron_id=selected.neuron_id,
        neuron_state=selected.neuron_state,
        neuron_type=selected.neuron_type,
        influence=influence,
        prompt_transform=prompt_transform,
        updated_routing_decision=updated_route,
        updated_gateway_mode=updated_gateway_mode,
        trace=trace + (f"routing_neuron:influence:{influence}",),
        conflict=conflict,
        fallback_reason=None,
        alerts=selected.alerts,
        registry_snapshot=updated_registry,
        considered=True,
        considered_ids=considered_ids,
        selected=True,
        barriers_checked=checked,
        barriers_blocked=(),
        conflict_resolution=conflict_resolution,
        decision_path=ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED,
    )


def record_runtime_outcome(
    registry: RoutingNeuronRegistry,
    runtime_decision: RoutingRuntimeDecision,
    *,
    session_id: str,
    task_signature: str,
    outcome_label: str,
    outcome_summary: str | None = None,
) -> RoutingNeuronRegistry:
    runtime_registry = runtime_decision.registry_snapshot or registry
    record = RoutingRuntimeRecord(
        record_id=_build_runtime_record_id(
            _next_runtime_record_sequence(runtime_registry),
            task_signature,
        ),
        timestamp=_utc_now_iso(),
        session_id=session_id,
        task_signature=task_signature,
        considered=runtime_decision.considered,
        considered_ids=runtime_decision.considered_ids,
        selected=runtime_decision.selected,
        selected_id=runtime_decision.neuron_id,
        selected_state=runtime_decision.neuron_state,
        selected_type=runtime_decision.neuron_type,
        influence=runtime_decision.influence,
        barriers_checked=runtime_decision.barriers_checked,
        barriers_blocked=runtime_decision.barriers_blocked,
        conflict=runtime_decision.conflict,
        conflict_resolution=runtime_decision.conflict_resolution,
        fallback_reason=runtime_decision.fallback_reason,
        decision=runtime_decision.decision,
        applied=runtime_decision.applied,
        outcome_label=outcome_label,
        trace=runtime_decision.trace,
        decision_path=runtime_decision.decision_path or resolve_runtime_decision_path(runtime_decision),
        outcome_summary=(outcome_summary[:160] if outcome_summary else None),
    )
    return runtime_registry.append_runtime_record(record)


def apply_runtime_to_routing_decision(
    routing: "RoutingDecision",
    runtime_decision: RoutingRuntimeDecision,
) -> "RoutingDecision":
    if not runtime_decision.applied or runtime_decision.updated_routing_decision is None:
        return routing

    if runtime_decision.updated_routing_decision == "primary_only":
        return replace(
            routing,
            routing_decision="primary_only",
            critic_requested=False,
            critic_used=False,
            critic_provider=None,
            critic_role=None,
            critic_available=None,
            gateway_mode=runtime_decision.updated_gateway_mode or "primary_only",
        )

    return replace(
        routing,
        routing_decision=runtime_decision.updated_routing_decision,
        gateway_mode=runtime_decision.updated_gateway_mode or routing.gateway_mode,
    )


__all__ = [
    "ROUTING_ACTIVATION_BARRIER_BUDGET",
    "ROUTING_ACTIVATION_BARRIER_COMPETITIVE",
    "ROUTING_ACTIVATION_BARRIER_COMPOSITION",
    "ROUTING_ACTIVATION_BARRIER_CONTEXT",
    "ROUTING_ACTIVATION_BARRIER_COOLDOWN",
    "ROUTING_ACTIVATION_BARRIER_FALLBACK",
    "ROUTING_ACTIVATION_BARRIER_STABILITY",
    "ROUTING_ACTIVATION_BARRIER_STATE",
    "ROUTING_ACTIVATION_BARRIERS",
    "ROUTING_RUNTIME_APPLIED",
    "ROUTING_RUNTIME_BLOCKED",
    "ROUTING_RUNTIME_COOLDOWN",
    "ROUTING_RUNTIME_FALLBACK",
    "ROUTING_RUNTIME_HISTORY_LIMIT",
    "ROUTING_RUNTIME_NO_SIGNAL",
    "ROUTING_RUNTIME_OBSERVABILITY_BLOCKED_ONLY",
    "ROUTING_RUNTIME_OBSERVABILITY_LOW_SAMPLE",
    "ROUTING_RUNTIME_OBSERVABILITY_NO_HISTORY",
    "ROUTING_RUNTIME_OBSERVABILITY_OBSERVED",
    "ROUTING_RUNTIME_OBSERVABILITY_ONLY_NO_SIGNAL",
    "ROUTING_RUNTIME_PAUSED",
    "ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE",
    "ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH",
    "ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED",
    "ROUTING_RUNTIME_PATH_SELECTED_BLOCKED",
    "ROUTING_RUNTIME_PATH_SELECTED_COOLDOWN",
    "ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED",
    "ROUTING_RUNTIME_PATH_SELECTED_PAUSED",
    "ROUTING_RUNTIME_SUGGESTED_ONLY",
    "ROUTING_RUNTIME_VALIDATION_BASELINE_ONLY",
    "ROUTING_RUNTIME_VALIDATION_IN_PROGRESS",
    "ROUTING_RUNTIME_VALIDATION_LOW_SAMPLE",
    "ROUTING_RUNTIME_VALIDATION_OBSERVED",
    "RoutingRuntimeDecision",
    "apply_routing_runtime",
    "apply_runtime_to_routing_decision",
    "count_blocked_runtime_decisions",
    "count_degraded_runtime_decisions",
    "count_fallback_runtime_decisions",
    "count_no_candidate_runtime_decisions",
    "count_selected_not_applied_runtime_decisions",
    "get_default_routing_registry",
    "record_runtime_outcome",
    "resolve_runtime_decision_path",
    "resolve_runtime_observability_status",
    "resolve_runtime_validation_status",
    "reset_default_routing_registry",
    "set_default_routing_registry",
]
