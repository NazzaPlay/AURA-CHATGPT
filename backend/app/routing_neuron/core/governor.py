"""Runtime governance helpers for Routing Neuron V1."""

from __future__ import annotations

from dataclasses import dataclass

from .runtime import RoutingRuntimeDecision


@dataclass(frozen=True)
class RoutingGovernanceSnapshot:
    decision: str
    decision_path: str | None
    applied: bool
    considered: bool
    considered_ids: tuple[str, ...]
    selected: bool
    influence: str | None
    barrier_reason: str | None
    barriers_checked: tuple[str, ...]
    barriers_blocked: tuple[str, ...]
    fallback_mode: str
    conflict: str | None
    conflict_resolution: str | None
    outcome_label: str | None
    alerts: tuple[str, ...]
    trace: tuple[str, ...]


def extract_barrier_reason(runtime_decision: RoutingRuntimeDecision) -> str | None:
    if runtime_decision.barriers_blocked:
        return runtime_decision.barriers_blocked[0]
    for item in runtime_decision.trace:
        if item.startswith("routing_neuron:barrier:"):
            return item.split("routing_neuron:barrier:", 1)[1]
    return runtime_decision.fallback_reason


def build_governance_snapshot(
    runtime_decision: RoutingRuntimeDecision,
) -> RoutingGovernanceSnapshot:
    fallback_mode = "baseline"
    if runtime_decision.decision == "applied":
        fallback_mode = "none"
    elif runtime_decision.decision == "paused":
        fallback_mode = "paused_route"
    elif runtime_decision.decision == "cooldown":
        fallback_mode = "cooldown_baseline"

    return RoutingGovernanceSnapshot(
        decision=runtime_decision.decision,
        decision_path=runtime_decision.decision_path,
        applied=runtime_decision.applied,
        considered=runtime_decision.considered,
        considered_ids=runtime_decision.considered_ids,
        selected=runtime_decision.selected,
        influence=runtime_decision.influence,
        barrier_reason=extract_barrier_reason(runtime_decision),
        barriers_checked=runtime_decision.barriers_checked,
        barriers_blocked=runtime_decision.barriers_blocked,
        fallback_mode=fallback_mode,
        conflict=runtime_decision.conflict,
        conflict_resolution=runtime_decision.conflict_resolution,
        outcome_label=runtime_decision.outcome_label,
        alerts=runtime_decision.alerts,
        trace=runtime_decision.trace,
    )
