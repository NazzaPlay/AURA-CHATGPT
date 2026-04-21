"""Administrative state views for Routing Neuron V1."""

from __future__ import annotations

from dataclasses import dataclass

from agents.routing_maintenance import RoutingLaunchDossier, RoutingRepertoireSnapshot


@dataclass(frozen=True)
class CodexControlAdminState:
    registry_path: str
    registry_version: str
    schema_version: str
    entry_count: int
    latest_run_id: str | None
    latest_timestamp: str | None
    latest_version: str | None
    latest_status: str | None
    latest_work_type: str | None
    latest_requested_scope: str | None
    latest_summary: str | None
    latest_checkpoint: str | None
    latest_checkpoint_short: str | None
    latest_checkpoint_long: str | None
    latest_tests_status: str | None
    latest_smokes_status: str | None
    latest_runtime_health: str | None
    latest_test_health: str | None
    latest_risk: str | None
    latest_next_step: str | None
    latest_open_debts: tuple[str, ...]
    latest_files_modified_count: int
    latest_files_created_count: int
    latest_modules_touched: tuple[str, ...]
    latest_contracts_affected: tuple[str, ...]
    latest_known_good: str | None
    latest_known_weakness: str | None
    latest_version_closed_for_scope: str | None
    latest_review_artifacts_needed: tuple[str, ...]
    latest_fallback_patterns: tuple[str, ...]
    latest_degradation_patterns: tuple[str, ...]
    latest_critic_patterns: tuple[str, ...]
    latest_router_patterns: tuple[str, ...]
    latest_long_tail_failures: tuple[str, ...]
    latest_rn_recent_outcomes: tuple[str, ...]
    latest_rn_recommendations: tuple[str, ...]
    latest_rn_attention_points: tuple[str, ...]
    latest_production_models: tuple[str, ...]
    latest_candidate_models: tuple[str, ...]
    latest_lab_models: tuple[str, ...]
    latest_do_not_promote_notes: tuple[str, ...]


@dataclass(frozen=True)
class RoutingLifecycleCounter:
    state: str
    count: int


@dataclass(frozen=True)
class RoutingScoreAxis:
    axis: str
    description: str
    visibility: str


@dataclass(frozen=True)
class RoutingSubsystemFootprint:
    canonical_modules: tuple[str, ...]
    legacy_compat_modules: tuple[str, ...]
    tactical_extensions: tuple[str, ...]


@dataclass(frozen=True)
class RoutingNeuronSealStatus:
    v1_sealed: bool
    structural_status: str
    operational_validation_status: str
    subsystem_present: bool
    score_axes_present: bool
    runtime_governance_present: bool
    offline_maintenance_present: bool
    admin_surface_present: bool
    provider_trace_clean: bool
    tactical_cutover_only: bool
    represented_states: tuple[str, ...]
    sealed_scope: tuple[str, ...]
    partial_scope: tuple[str, ...]
    v1x_debts: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    gaps: tuple[str, ...]


@dataclass(frozen=True)
class RoutingRuntimeStatus:
    total_decisions: int
    considered_decisions: int
    selected_decisions: int
    applied_decisions: int
    selected_not_applied_decisions: int
    blocked_decisions: int
    fallback_decisions: int
    degraded_decisions: int
    suggested_only_decisions: int
    no_signal_decisions: int
    no_candidate_decisions: int
    paused_decisions: int
    cooldown_decisions: int
    history_window_limit: int
    observability_status: str
    validation_status: str
    considered_neurons: tuple[str, ...]
    applied_neurons: tuple[str, ...]
    blocked_neurons: tuple[str, ...]
    frequent_barriers: tuple[str, ...]
    frequent_fallbacks: tuple[str, ...]
    frequent_outcomes: tuple[str, ...]
    recent_conflicts: tuple[str, ...]
    recent_decisions: tuple[str, ...]
    recent_paths: tuple[str, ...]
    recent_outcomes: tuple[str, ...]
    recent_applied_influences: tuple[str, ...]


@dataclass(frozen=True)
class RoutingNeuronAdminState:
    snapshot: RoutingRepertoireSnapshot
    dossier: RoutingLaunchDossier
    lifecycle_counts: tuple[RoutingLifecycleCounter, ...]
    score_axes: tuple[RoutingScoreAxis, ...]
    runtime_status: RoutingRuntimeStatus
    codex_control: CodexControlAdminState
    footprint: RoutingSubsystemFootprint
    seal_status: RoutingNeuronSealStatus


__all__ = [
    "CodexControlAdminState",
    "RoutingLifecycleCounter",
    "RoutingNeuronAdminState",
    "RoutingNeuronSealStatus",
    "RoutingRuntimeStatus",
    "RoutingScoreAxis",
    "RoutingSubsystemFootprint",
]
