"""Canonical observer entrypoints for Routing Neuron V1.x."""

from __future__ import annotations

from dataclasses import dataclass, replace

from agents.routing_neuron_registry import (
    MIN_ACTIVE_FREQUENCY,
    MIN_ACTIVE_ROUTING_SCORE,
    ROUTING_STATE_OBSERVED_PATTERN,
    ROUTING_STATE_ACTIVE,
    ROUTING_STATE_PAUSED,
    ROUTING_TYPE_CONTROL,
    ROUTING_TYPE_SELECTION,
    ROUTING_TYPE_TRANSFORMATION,
    EvidenceRecord,
    ObservedPattern,
    RoutingNeuronCandidate,
    RoutingNeuronRegistry,
    build_evidence_record,
    register_routing_neuron_candidate,
    should_birth_routing_neuron,
)
from agents.routing_scorer import build_routing_score


@dataclass(frozen=True)
class RoutingObservationSeed:
    activation_rule: str
    routing_condition: str
    intermediate_transform: str | None = None


def build_task_signature(
    *,
    task_type: str,
    intent: str,
    route_action: str | None,
) -> str:
    return f"{task_type}:{intent}:{route_action or 'model'}"


def infer_neuron_type(
    *,
    baseline_route: str,
    evaluated_route: str,
    intermediate_transform: str | None,
) -> str:
    if intermediate_transform:
        return ROUTING_TYPE_TRANSFORMATION

    if baseline_route != evaluated_route:
        if baseline_route == "primary_then_critic" and evaluated_route == "primary_only":
            return ROUTING_TYPE_CONTROL
        return ROUTING_TYPE_SELECTION

    return ROUTING_TYPE_SELECTION


def resolve_runtime_observation_seed(
    *,
    task_signature: str,
    task_type: str,
    risk_profile: str,
    baseline_route: str,
    evaluated_route: str,
    runtime_influence: str | None,
    prompt_transform: str | None,
    critic_used: bool,
    verification_outcome: str | None,
) -> RoutingObservationSeed:
    if (
        runtime_influence is None
        and prompt_transform is None
        and baseline_route == "primary_then_critic"
        and evaluated_route == "primary_then_critic"
        and task_type == "technical_reasoning"
        and risk_profile in {"low", "medium"}
        and critic_used
        and verification_outcome == "verified"
    ):
        return RoutingObservationSeed(
            activation_rule="prefer_primary_only_when_verified",
            routing_condition=f"{task_type} {risk_profile} skip_critic critic_optional verified",
            intermediate_transform=None,
        )

    return RoutingObservationSeed(
        activation_rule=runtime_influence or "baseline_observation",
        routing_condition=task_signature,
        intermediate_transform=prompt_transform,
    )


def _pattern_key(
    *,
    task_signature: str,
    neuron_type: str,
    activated_components: tuple[str, ...],
) -> str:
    component_key = "+".join(sorted(activated_components))
    return f"pattern:{neuron_type}:{task_signature}:{component_key}"


def _calculate_expected_gain(evidence: EvidenceRecord) -> float:
    latency_gain = max(-evidence.latency_delta, 0.0) / 250.0
    cost_gain = max(-evidence.cost_delta, 0.0)
    quality_gain = max(evidence.quality_delta, 0.0)
    verification_gain = max(evidence.verification_delta, 0.0)
    consistency_gain = max(evidence.consistency_delta, 0.0)
    raw = (
        latency_gain
        + (cost_gain * 0.6)
        + (quality_gain * 0.7)
        + (verification_gain * 0.5)
        + (consistency_gain * 0.5)
    )
    return round(raw, 3)


def record_routing_evidence(
    registry: RoutingNeuronRegistry,
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
) -> tuple[RoutingNeuronRegistry, EvidenceRecord]:
    evidence = build_evidence_record(
        task_signature=task_signature,
        session_id=session_id,
        task_profile=task_profile,
        risk_profile=risk_profile,
        budget_profile=budget_profile,
        baseline_route=baseline_route,
        recent_route=recent_route,
        evaluated_route=evaluated_route,
        activated_components=activated_components,
        latency_ms=latency_ms,
        latency_delta=latency_delta,
        cost_delta=cost_delta,
        quality_delta=quality_delta,
        verification_delta=verification_delta,
        consistency_delta=consistency_delta,
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
        existing_registry=registry,
    )
    return registry.register_evidence(evidence), evidence


def observe_routing_pattern(
    registry: RoutingNeuronRegistry,
    evidence: EvidenceRecord,
    *,
    activation_rule: str,
    routing_condition: str,
    intermediate_transform: str | None = None,
) -> tuple[RoutingNeuronRegistry, ObservedPattern]:
    neuron_type = infer_neuron_type(
        baseline_route=evidence.baseline_route,
        evaluated_route=evidence.evaluated_route,
        intermediate_transform=intermediate_transform,
    )
    pattern_id = _pattern_key(
        task_signature=evidence.task_signature,
        neuron_type=neuron_type,
        activated_components=evidence.activated_components,
    )
    existing = registry.observed_patterns.get(pattern_id)

    if existing is None:
        success_history = (
            (evidence.evidence_id,)
            if "success" in evidence.success_label or "improved" in evidence.success_label
            else ()
        )
        failure_history = (
            (evidence.evidence_id,)
            if evidence.success_label in {"fallback", "degraded", "failed"}
            else ()
        )
        pattern = ObservedPattern(
            pattern_id=pattern_id,
            state=ROUTING_STATE_OBSERVED_PATTERN,
            neuron_type=neuron_type,
            task_signature=evidence.task_signature,
            activation_rule=activation_rule,
            routing_condition=routing_condition,
            intermediate_transform=intermediate_transform,
            activated_components=evidence.activated_components,
            evidence_ids=(evidence.evidence_id,),
            activation_frequency=1,
            success_history=success_history,
            failure_history=failure_history,
            expected_gain=_calculate_expected_gain(evidence),
            estimated_cost=max(evidence.cost_delta, 0.0),
            estimated_latency=evidence.latency_ms,
            last_seen_at=evidence.timestamp,
        )
        return registry.register_observed_pattern(pattern), pattern

    success_history = existing.success_history
    failure_history = existing.failure_history
    if "success" in evidence.success_label or "improved" in evidence.success_label:
        success_history = success_history + (evidence.evidence_id,)
    elif evidence.success_label in {"fallback", "degraded", "failed"}:
        failure_history = failure_history + (evidence.evidence_id,)

    activation_frequency = existing.activation_frequency + 1
    expected_gain = round(
        ((existing.expected_gain * existing.activation_frequency) + _calculate_expected_gain(evidence))
        / activation_frequency,
        3,
    )
    estimated_cost = round(
        ((existing.estimated_cost * existing.activation_frequency) + max(evidence.cost_delta, 0.0))
        / activation_frequency,
        3,
    )
    estimated_latency = round(
        ((existing.estimated_latency * existing.activation_frequency) + evidence.latency_ms)
        / activation_frequency,
        3,
    )
    pattern = replace(
        existing,
        evidence_ids=existing.evidence_ids + (evidence.evidence_id,),
        activation_frequency=activation_frequency,
        success_history=success_history,
        failure_history=failure_history,
        expected_gain=expected_gain,
        estimated_cost=estimated_cost,
        estimated_latency=estimated_latency,
        last_seen_at=evidence.timestamp,
    )
    return registry.register_observed_pattern(pattern), pattern


def maybe_birth_candidate_from_pattern(
    registry: RoutingNeuronRegistry,
    pattern: ObservedPattern,
) -> tuple[RoutingNeuronRegistry, RoutingNeuronCandidate | None]:
    matching_candidate = next(
        (
            candidate
            for candidate in registry.candidates.values()
            if candidate.task_signature == pattern.task_signature
            and candidate.activated_components == pattern.activated_components
            and candidate.neuron_type == pattern.neuron_type
        ),
        None,
    )
    if matching_candidate is not None:
        score = build_routing_score(
            expected_gain=pattern.expected_gain,
            estimated_cost=pattern.estimated_cost,
            estimated_latency=pattern.estimated_latency,
            success_count=len(pattern.success_history),
            failure_count=len(pattern.failure_history),
            quality_delta=pattern.expected_gain,
            verification_delta=0.0,
            consistency_delta=0.0,
            activation_frequency=pattern.activation_frequency,
            activated_components=pattern.activated_components,
        )
        refreshed = replace(
            matching_candidate,
            success_history=pattern.success_history,
            failure_history=pattern.failure_history,
            expected_gain=pattern.expected_gain,
            estimated_cost=pattern.estimated_cost,
            estimated_latency=pattern.estimated_latency,
            activation_frequency=pattern.activation_frequency,
            efficiency_score=score.efficiency_score,
            stability_score=score.stability_score,
            quality_score=score.quality_score,
            reusability_score=score.reusability_score,
            global_routing_score=score.global_routing_score,
        )
        refreshed_registry = registry.register_candidate(refreshed)
        if refreshed.neuron_id in refreshed_registry.active:
            updated_active = dict(refreshed_registry.active)
            updated_active[refreshed.neuron_id] = refreshed
            refreshed_registry = replace(refreshed_registry, active=updated_active)
        return refreshed_registry, refreshed

    duplicate_exists = any(
        candidate.task_signature == pattern.task_signature
        and candidate.activated_components == pattern.activated_components
        and candidate.neuron_type == pattern.neuron_type
        for candidate in registry.active.values()
    )
    if not should_birth_routing_neuron(
        activated_components=pattern.activated_components,
        activation_frequency=pattern.activation_frequency,
        expected_gain=pattern.expected_gain,
        estimated_cost=pattern.estimated_cost,
        duplicate_exists=duplicate_exists,
    ):
        return registry, None

    candidate = register_routing_neuron_candidate(
        task_signature=pattern.task_signature,
        activated_components=pattern.activated_components,
        activation_rule=pattern.activation_rule,
        routing_condition=pattern.routing_condition,
        intermediate_transform=pattern.intermediate_transform,
        success_history=pattern.success_history,
        failure_history=pattern.failure_history,
        expected_gain=pattern.expected_gain,
        estimated_cost=pattern.estimated_cost,
        estimated_latency=pattern.estimated_latency,
        neuron_type=pattern.neuron_type,
    )
    if candidate is None:
        return registry, None

    score = build_routing_score(
        expected_gain=pattern.expected_gain,
        estimated_cost=pattern.estimated_cost,
        estimated_latency=pattern.estimated_latency,
        success_count=len(pattern.success_history),
        failure_count=len(pattern.failure_history),
        quality_delta=pattern.expected_gain,
        verification_delta=0.0,
        consistency_delta=0.0,
        activation_frequency=pattern.activation_frequency,
        activated_components=pattern.activated_components,
    )
    enriched = replace(
        candidate,
        efficiency_score=score.efficiency_score,
        stability_score=score.stability_score,
        quality_score=score.quality_score,
        reusability_score=score.reusability_score,
        global_routing_score=score.global_routing_score,
    )
    return registry.register_candidate(enriched), enriched


def activate_runtime_ready_candidates(
    registry: RoutingNeuronRegistry,
) -> RoutingNeuronRegistry:
    updated_registry = registry
    for candidate in registry.candidates.values():
        if candidate.neuron_state in {ROUTING_STATE_ACTIVE, ROUTING_STATE_PAUSED}:
            continue

        # Verified low-risk technical passes are a safe on-ramp for the first
        # observable skip_critic path, even before the general score threshold.
        verified_skip_critic_ready = (
            candidate.activation_frequency >= 2
            and candidate.stability_score >= 0.75
            and candidate.global_routing_score >= 0.4
            and candidate.recent_fallback_count == 0
            and "prefer_primary_only_when_verified" in candidate.activation_rule.casefold()
            and "skip_critic" in candidate.routing_condition.casefold()
        )

        if (
            candidate.activation_frequency >= MIN_ACTIVE_FREQUENCY
            and candidate.global_routing_score >= MIN_ACTIVE_ROUTING_SCORE
            and candidate.stability_score >= 0.55
            and candidate.cooldown_turns_remaining <= 0
        ) or verified_skip_critic_ready:
            updated_registry = updated_registry.activate_candidate(candidate.neuron_id)

    return updated_registry


def ingest_routing_observation(
    registry: RoutingNeuronRegistry,
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
    activation_rule: str,
    routing_condition: str,
    intermediate_transform: str | None = None,
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
) -> tuple[RoutingNeuronRegistry, EvidenceRecord, ObservedPattern, RoutingNeuronCandidate | None]:
    registry, evidence = record_routing_evidence(
        registry,
        task_signature=task_signature,
        session_id=session_id,
        task_profile=task_profile,
        risk_profile=risk_profile,
        budget_profile=budget_profile,
        baseline_route=baseline_route,
        recent_route=recent_route,
        evaluated_route=evaluated_route,
        activated_components=activated_components,
        latency_ms=latency_ms,
        latency_delta=latency_delta,
        cost_delta=cost_delta,
        quality_delta=quality_delta,
        verification_delta=verification_delta,
        consistency_delta=consistency_delta,
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
    registry, pattern = observe_routing_pattern(
        registry,
        evidence,
        activation_rule=activation_rule,
        routing_condition=routing_condition,
        intermediate_transform=intermediate_transform,
    )
    updated_evidence = replace(evidence, observed_pattern_id=pattern.pattern_id)
    registry = registry.register_evidence(updated_evidence)
    registry, candidate = maybe_birth_candidate_from_pattern(registry, pattern)
    if candidate is not None:
        updated_evidence = replace(updated_evidence, neuron_id=candidate.neuron_id)
        registry = registry.register_evidence(updated_evidence)
    registry = activate_runtime_ready_candidates(registry)
    return registry, updated_evidence, pattern, candidate


__all__ = [
    "EvidenceRecord",
    "ObservedPattern",
    "RoutingNeuronCandidate",
    "RoutingNeuronRegistry",
    "RoutingObservationSeed",
    "activate_runtime_ready_candidates",
    "build_task_signature",
    "infer_neuron_type",
    "ingest_routing_observation",
    "maybe_birth_candidate_from_pattern",
    "observe_routing_pattern",
    "record_routing_evidence",
    "resolve_runtime_observation_seed",
]
