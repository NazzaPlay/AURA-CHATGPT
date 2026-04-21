from __future__ import annotations

from dataclasses import dataclass


def _clamp_score(value: float) -> float:
    return round(max(min(value, 1.0), 0.0), 3)


@dataclass(frozen=True)
class RoutingScore:
    efficiency_score: float
    stability_score: float
    quality_score: float
    reusability_score: float
    global_routing_score: float


def calculate_efficiency_score(
    *,
    expected_gain: float,
    estimated_cost: float,
    estimated_latency: float,
    budget_violation_count: int = 0,
) -> float:
    latency_penalty = estimated_latency / 1000.0 if estimated_latency > 10.0 else estimated_latency
    budget_penalty = min(budget_violation_count * 0.08, 0.24)
    return _clamp_score(
        (expected_gain * 2.8)
        - (estimated_cost * 0.45)
        - (latency_penalty * 0.2)
        - budget_penalty
    )


def calculate_stability_score(
    *,
    success_count: int,
    failure_count: int,
    fallback_frequency: int = 0,
    recent_conflict_load: int = 0,
    stable_activation_streak: int = 0,
) -> float:
    total = success_count + failure_count
    if total <= 0:
        return 0.0

    streak_bonus = min(stable_activation_streak * 0.06, 0.18)
    fallback_penalty = min(fallback_frequency * 0.08, 0.24)
    conflict_penalty = min(recent_conflict_load * 0.04, 0.12)
    return _clamp_score(
        ((success_count + 1) / (total + 1))
        + streak_bonus
        - fallback_penalty
        - conflict_penalty
    )


def calculate_quality_score(
    *,
    expected_gain: float,
    quality_delta: float,
    verification_delta: float,
    consistency_delta: float,
    baseline_win_count: int = 0,
    fallback_frequency: int = 0,
) -> float:
    return _clamp_score(
        (expected_gain * 1.4)
        + (quality_delta * 0.5)
        + (verification_delta * 0.35)
        + (consistency_delta * 0.35)
        - min(baseline_win_count * 0.06, 0.18)
        - min(fallback_frequency * 0.05, 0.2)
    )


def calculate_reusability_score(
    *,
    activation_frequency: int,
    activated_components: tuple[str, ...],
) -> float:
    diversity_bonus = min(len(set(activated_components)) / 3.0, 1.0)
    reuse_bonus = min(activation_frequency / 5.0, 1.0)
    return _clamp_score((diversity_bonus * 0.6) + (reuse_bonus * 0.4))


def build_routing_score(
    *,
    expected_gain: float,
    estimated_cost: float,
    estimated_latency: float,
    success_count: int,
    failure_count: int,
    quality_delta: float,
    verification_delta: float,
    consistency_delta: float,
    activation_frequency: int,
    activated_components: tuple[str, ...],
    baseline_win_count: int = 0,
    fallback_frequency: int = 0,
    recent_conflict_load: int = 0,
    stable_activation_streak: int = 0,
    confidence_progress: float = 0.0,
    budget_violation_count: int = 0,
) -> RoutingScore:
    efficiency_score = calculate_efficiency_score(
        expected_gain=expected_gain,
        estimated_cost=estimated_cost,
        estimated_latency=estimated_latency,
        budget_violation_count=budget_violation_count,
    )
    stability_score = calculate_stability_score(
        success_count=success_count,
        failure_count=failure_count,
        fallback_frequency=fallback_frequency,
        recent_conflict_load=recent_conflict_load,
        stable_activation_streak=stable_activation_streak,
    )
    quality_score = calculate_quality_score(
        expected_gain=expected_gain,
        quality_delta=quality_delta,
        verification_delta=verification_delta,
        consistency_delta=consistency_delta,
        baseline_win_count=baseline_win_count,
        fallback_frequency=fallback_frequency,
    )
    reusability_score = calculate_reusability_score(
        activation_frequency=activation_frequency,
        activated_components=activated_components,
    )
    global_routing_score = _clamp_score(
        (efficiency_score * 0.36)
        + (stability_score * 0.31)
        + (quality_score * 0.2)
        + (reusability_score * 0.08)
        + min(max(confidence_progress, 0.0), 1.0) * 0.05
        - min(fallback_frequency * 0.03, 0.12)
    )

    return RoutingScore(
        efficiency_score=efficiency_score,
        stability_score=stability_score,
        quality_score=quality_score,
        reusability_score=reusability_score,
        global_routing_score=global_routing_score,
    )
