from __future__ import annotations

from dataclasses import dataclass

from .model_registry import ModelPolicyEntry, ModelRegistry


@dataclass(frozen=True)
class BenchmarkTarget:
    model_id: str
    family: str
    role_target: str | None
    runtime_backend: str | None
    artifact_format: str | None
    device_tier: str | None
    policy_status: str
    catalog_track: str | None
    available_in_bank: bool | None
    governance_lane: str | None
    benchmark_readiness: str | None
    benchmark_priority: str | None


@dataclass(frozen=True)
class BenchmarkSnapshot:
    model_id: str
    latency_ms: float | None
    memory_mb: float | None
    stability_score: float | None
    conversational_quality: float | None
    consistency_score: float | None
    critic_utility: float | None
    micro_expert_utility: float | None


@dataclass(frozen=True)
class BenchmarkAssessment:
    model_id: str
    stable_enough: bool
    mini_pc_ready: bool
    critic_ready: bool
    micro_expert_ready: bool


@dataclass(frozen=True)
class BenchmarkPreparationSnapshot:
    ready_now: tuple[str, ...]
    watchlist: tuple[str, ...]
    blocked: tuple[str, ...]
    active_core: tuple[str, ...]


def build_benchmark_targets(registry: ModelRegistry) -> tuple[BenchmarkTarget, ...]:
    return tuple(_policy_to_target(entry) for entry in registry.list_model_policies())


def _policy_to_target(entry: ModelPolicyEntry) -> BenchmarkTarget:
    return BenchmarkTarget(
        model_id=entry.model_id,
        family=entry.family,
        role_target=entry.role,
        runtime_backend=entry.runtime_backend,
        artifact_format=entry.artifact_format,
        device_tier=entry.device_tier,
        policy_status=entry.policy_status,
        catalog_track=entry.catalog_track,
        available_in_bank=entry.available_in_bank,
        governance_lane=entry.governance_lane,
        benchmark_readiness=entry.benchmark_readiness,
        benchmark_priority=entry.benchmark_priority,
    )


def assess_benchmark_snapshot(snapshot: BenchmarkSnapshot) -> BenchmarkAssessment:
    stable_enough = (snapshot.stability_score or 0.0) >= 0.75
    mini_pc_ready = stable_enough and (snapshot.memory_mb or 99999.0) <= 4096.0
    critic_ready = stable_enough and (snapshot.critic_utility or 0.0) >= 0.7
    micro_expert_ready = stable_enough and (snapshot.micro_expert_utility or 0.0) >= 0.7

    return BenchmarkAssessment(
        model_id=snapshot.model_id,
        stable_enough=stable_enough,
        mini_pc_ready=mini_pc_ready,
        critic_ready=critic_ready,
        micro_expert_ready=micro_expert_ready,
    )


def build_benchmark_preparation_snapshot(
    registry: ModelRegistry,
) -> BenchmarkPreparationSnapshot:
    targets = build_benchmark_targets(registry)
    ready_now = tuple(
        target.model_id
        for target in targets
        if target.benchmark_readiness in {"ready_for_benchmark", "benchmark_ready"}
    )
    watchlist = tuple(
        target.model_id
        for target in targets
        if target.benchmark_readiness in {"exploratory_only", "in_rotation"}
    )
    blocked = tuple(
        target.model_id
        for target in targets
        if target.benchmark_readiness in {
            "blocked_pending_backend",
            "blocked_pending_instruct",
            "needs_triage",
        }
    )
    active_core = tuple(
        target.model_id
        for target in targets
        if target.catalog_track == "production"
    )

    return BenchmarkPreparationSnapshot(
        ready_now=ready_now,
        watchlist=watchlist,
        blocked=blocked,
        active_core=active_core,
    )
