"""Administrative repertoire and seal-status views for Routing Neuron V1."""

from __future__ import annotations

from collections import Counter

from ..control import build_codex_control_status
from ..core.maintenance import build_routing_launch_dossier, build_routing_repertoire_snapshot
from ..core.runtime import (
    ROUTING_RUNTIME_HISTORY_LIMIT,
    ROUTING_RUNTIME_OBSERVABILITY_BLOCKED_ONLY,
    ROUTING_RUNTIME_OBSERVABILITY_LOW_SAMPLE,
    ROUTING_RUNTIME_OBSERVABILITY_NO_HISTORY,
    ROUTING_RUNTIME_OBSERVABILITY_OBSERVED,
    ROUTING_RUNTIME_OBSERVABILITY_ONLY_NO_SIGNAL,
    count_blocked_runtime_decisions,
    count_degraded_runtime_decisions,
    count_fallback_runtime_decisions,
    count_no_candidate_runtime_decisions,
    count_selected_not_applied_runtime_decisions,
    get_default_routing_registry,
    resolve_runtime_decision_path,
    resolve_runtime_observability_status,
    resolve_runtime_validation_status,
)
from ..schemas.admin_state import (
    CodexControlAdminState,
    RoutingLifecycleCounter,
    RoutingNeuronAdminState,
    RoutingNeuronSealStatus,
    RoutingRuntimeStatus,
    RoutingScoreAxis,
    RoutingSubsystemFootprint,
)
from ..schemas.routing_neuron import (
    ROUTING_LIFECYCLE_STATES,
    ROUTING_PRIMARY_SCORE_AXES,
    derive_lifecycle_state,
)


_CANONICAL_MODULES = (
    "backend.app.routing_neuron.core.observer",
    "backend.app.routing_neuron.core.registry",
    "backend.app.routing_neuron.core.scorer",
    "backend.app.routing_neuron.core.runtime",
    "backend.app.routing_neuron.core.governor",
    "backend.app.routing_neuron.core.maintenance",
    "backend.app.routing_neuron.core.promoter",
    "backend.app.routing_neuron.schemas.routing_neuron",
    "backend.app.routing_neuron.schemas.evidence",
    "backend.app.routing_neuron.schemas.session_summary",
    "backend.app.routing_neuron.schemas.admin_state",
    "backend.app.routing_neuron.admin.repertoire",
    "backend.app.routing_neuron.admin.alerts",
    "backend.app.routing_neuron.admin.actions",
)

_LEGACY_COMPAT_MODULES = (
    "agents.routing_observer",
    "agents.routing_neuron_registry",
    "agents.routing_scorer",
    "agents.routing_runtime",
    "agents.routing_maintenance",
)

_TACTICAL_EXTENSIONS = (
    "shortlist",
    "bridge",
    "rehearsal",
    "cutover",
    "launch_dossier",
    "codex_control_registry",
    "administrative_memory",
)

_SCORE_AXIS_DESCRIPTIONS = {
    "efficiency_score": "resume ahorro o ventaja operativa relativa frente a baseline.",
    "stability_score": "resume repetibilidad y resistencia a deriva o fallback.",
    "quality_score": "resume mejora o no degradacion relevante de calidad.",
    "reusability_score": "resume reutilizacion potencial del patron en mas de un contexto.",
    "global_routing_score": "agrega los ejes madre para priorizacion operativa.",
}


_SEALED_SCOPE = (
    "observation_and_evidence",
    "score_axes_and_global_score",
    "limited_runtime_governance",
    "offline_maintenance",
    "admin_repertoire",
    "controlled_structural_recommendation",
)

_PARTIAL_SCOPE = (
    "legacy_registry_and_maintenance_backplane",
    "extended_lifecycle_states_are_partly_derived",
    "admin_query_rendering_still_partly_shared_with_system_state_agent",
)

_V1X_DEBTS = (
    "migrate_registry_and_maintenance_to_canonical_namespace",
    "finish_extracting_checkpoint_and_runtime_admin_renderers",
    "decide_runtime_record_retention_or_light_persistence",
)

_OUT_OF_SCOPE = (
    "structural_promotions_beyond_specialized_prompt",
    "training_lora_distillation_micro_model",
    "ui_panel",
    "heavy_persistence_layer",
)


def _format_ranked_counts(counter: Counter[str], *, limit: int = 3) -> tuple[str, ...]:
    return tuple(
        f"{label} x{count}"
        for label, count in counter.most_common(limit)
        if label
    )


def _build_runtime_status(registry) -> RoutingRuntimeStatus:
    records = registry.runtime_records
    decision_counter = Counter(record.decision for record in records)
    barrier_counter = Counter(
        barrier
        for record in records
        for barrier in record.barriers_blocked
    )
    fallback_counter = Counter(
        record.fallback_reason
        for record in records
        if record.fallback_reason
    )
    outcome_counter = Counter(
        record.outcome_label or "unknown"
        for record in records
    )
    fallback_decisions = count_fallback_runtime_decisions(records)
    blocked_decisions = count_blocked_runtime_decisions(records)
    degraded_decisions = count_degraded_runtime_decisions(records)
    selected_not_applied_decisions = count_selected_not_applied_runtime_decisions(records)
    no_candidate_decisions = count_no_candidate_runtime_decisions(records)
    considered_neurons = tuple(
        sorted(
            {
                neuron_id
                for record in records
                for neuron_id in record.considered_ids
            }
        )
    )
    applied_neurons = tuple(
        sorted(
            {
                record.selected_id
                for record in records
                if record.applied and record.selected_id is not None
            }
        )
    )
    blocked_neurons = tuple(
        sorted(
            {
                record.selected_id
                for record in records
                if record.selected_id is not None
                and record.decision in {"blocked_by_barrier", "paused", "cooldown"}
            }
        )
    )
    recent_conflicts = tuple(
        record.conflict
        for record in records[-5:]
        if record.conflict is not None
    )
    recent_decisions = tuple(
        f"{record.decision}:{record.selected_id or 'baseline'}:{record.selected_state or 'none'}"
        for record in records[-5:]
    )
    recent_paths = tuple(
        record.decision_path or resolve_runtime_decision_path(record)
        for record in records[-5:]
    )
    recent_outcomes = tuple(
        f"{record.outcome_label or 'unknown'}:{record.decision}"
        for record in records[-5:]
    )
    recent_applied_influences = tuple(
        f"{record.influence or 'none'}:{record.outcome_label or 'unknown'}"
        for record in records[-5:]
        if record.applied
    )
    observability_status = resolve_runtime_observability_status(
        total_decisions=len(records),
        applied_decisions=sum(1 for record in records if record.applied),
        blocked_decisions=blocked_decisions,
        fallback_decisions=fallback_decisions,
        no_signal_decisions=decision_counter.get("no_signal", 0),
    )
    validation_status = resolve_runtime_validation_status(observability_status)

    return RoutingRuntimeStatus(
        total_decisions=len(records),
        considered_decisions=sum(1 for record in records if record.considered),
        selected_decisions=sum(1 for record in records if record.selected),
        applied_decisions=sum(1 for record in records if record.applied),
        selected_not_applied_decisions=selected_not_applied_decisions,
        blocked_decisions=blocked_decisions,
        fallback_decisions=fallback_decisions,
        degraded_decisions=degraded_decisions,
        suggested_only_decisions=decision_counter.get("suggested_only", 0),
        no_signal_decisions=decision_counter.get("no_signal", 0),
        no_candidate_decisions=no_candidate_decisions,
        paused_decisions=decision_counter.get("paused", 0),
        cooldown_decisions=decision_counter.get("cooldown", 0),
        history_window_limit=ROUTING_RUNTIME_HISTORY_LIMIT,
        observability_status=observability_status,
        validation_status=validation_status,
        considered_neurons=considered_neurons,
        applied_neurons=applied_neurons,
        blocked_neurons=blocked_neurons,
        frequent_barriers=_format_ranked_counts(barrier_counter),
        frequent_fallbacks=_format_ranked_counts(fallback_counter),
        frequent_outcomes=_format_ranked_counts(outcome_counter),
        recent_conflicts=recent_conflicts,
        recent_decisions=recent_decisions,
        recent_paths=recent_paths,
        recent_outcomes=recent_outcomes,
        recent_applied_influences=recent_applied_influences,
    )


def _build_seal_gaps(snapshot, runtime_status: RoutingRuntimeStatus) -> tuple[str, ...]:
    gaps: list[str] = []

    if runtime_status.observability_status == ROUTING_RUNTIME_OBSERVABILITY_NO_HISTORY:
        gaps.append("no_runtime_history_observed_yet")
    elif runtime_status.observability_status == ROUTING_RUNTIME_OBSERVABILITY_ONLY_NO_SIGNAL:
        gaps.append("weak_runtime_signal_only_so_far")
    elif runtime_status.observability_status == ROUTING_RUNTIME_OBSERVABILITY_BLOCKED_ONLY:
        gaps.append("baseline_or_blocked_runtime_only_so_far")
    elif runtime_status.observability_status == ROUTING_RUNTIME_OBSERVABILITY_LOW_SAMPLE:
        gaps.append("applied_runtime_still_low_sample")

    if snapshot.entries and not snapshot.active_ids:
        gaps.append("no_active_runtime_routes_observed_yet")

    return tuple(gaps)


def build_admin_state(registry=None) -> RoutingNeuronAdminState:
    resolved_registry = registry or get_default_routing_registry()
    snapshot = build_routing_repertoire_snapshot(resolved_registry)
    dossier = build_routing_launch_dossier(resolved_registry)
    runtime_status = _build_runtime_status(resolved_registry)
    codex_control_status = build_codex_control_status()

    lifecycle_counter = Counter(derive_lifecycle_state(entry) for entry in snapshot.entries)
    lifecycle_counts = tuple(
        RoutingLifecycleCounter(state=state, count=lifecycle_counter.get(state, 0))
        for state in ROUTING_LIFECYCLE_STATES
    )

    seal_status = RoutingNeuronSealStatus(
        v1_sealed=True,
        structural_status="sealed_structurally",
        operational_validation_status=runtime_status.validation_status,
        subsystem_present=True,
        score_axes_present=True,
        runtime_governance_present=True,
        offline_maintenance_present=True,
        admin_surface_present=True,
        provider_trace_clean=True,
        tactical_cutover_only=False,
        represented_states=ROUTING_LIFECYCLE_STATES,
        sealed_scope=_SEALED_SCOPE,
        partial_scope=_PARTIAL_SCOPE,
        v1x_debts=_V1X_DEBTS,
        out_of_scope=_OUT_OF_SCOPE,
        gaps=_build_seal_gaps(snapshot, runtime_status),
    )

    score_axes = tuple(
        RoutingScoreAxis(
            axis=axis,
            description=_SCORE_AXIS_DESCRIPTIONS[axis],
            visibility="admin",
        )
        for axis in ROUTING_PRIMARY_SCORE_AXES
    )

    footprint = RoutingSubsystemFootprint(
        canonical_modules=_CANONICAL_MODULES,
        legacy_compat_modules=_LEGACY_COMPAT_MODULES,
        tactical_extensions=_TACTICAL_EXTENSIONS,
    )
    codex_control = CodexControlAdminState(
        registry_path=codex_control_status.registry_path,
        registry_version=codex_control_status.registry_version,
        schema_version=codex_control_status.schema_version,
        entry_count=codex_control_status.entry_count,
        latest_run_id=codex_control_status.latest_run_id,
        latest_timestamp=codex_control_status.latest_timestamp,
        latest_version=codex_control_status.latest_version,
        latest_status=codex_control_status.latest_status,
        latest_work_type=codex_control_status.latest_work_type,
        latest_requested_scope=codex_control_status.latest_requested_scope,
        latest_summary=codex_control_status.latest_summary,
        latest_checkpoint=codex_control_status.latest_checkpoint,
        latest_checkpoint_short=codex_control_status.latest_checkpoint_short,
        latest_checkpoint_long=codex_control_status.latest_checkpoint_long,
        latest_tests_status=codex_control_status.latest_tests_status,
        latest_smokes_status=codex_control_status.latest_smokes_status,
        latest_runtime_health=codex_control_status.latest_runtime_health,
        latest_test_health=codex_control_status.latest_test_health,
        latest_risk=codex_control_status.latest_risk,
        latest_next_step=codex_control_status.latest_next_step,
        latest_open_debts=codex_control_status.latest_open_debts,
        latest_files_modified_count=codex_control_status.latest_files_modified_count,
        latest_files_created_count=codex_control_status.latest_files_created_count,
        latest_modules_touched=codex_control_status.latest_modules_touched,
        latest_contracts_affected=codex_control_status.latest_contracts_affected,
        latest_known_good=codex_control_status.latest_known_good,
        latest_known_weakness=codex_control_status.latest_known_weakness,
        latest_version_closed_for_scope=codex_control_status.latest_version_closed_for_scope,
        latest_review_artifacts_needed=codex_control_status.latest_review_artifacts_needed,
        latest_fallback_patterns=codex_control_status.latest_fallback_patterns,
        latest_degradation_patterns=codex_control_status.latest_degradation_patterns,
        latest_critic_patterns=codex_control_status.latest_critic_patterns,
        latest_router_patterns=codex_control_status.latest_router_patterns,
        latest_long_tail_failures=codex_control_status.latest_long_tail_failures,
        latest_rn_recent_outcomes=codex_control_status.latest_rn_recent_outcomes,
        latest_rn_recommendations=codex_control_status.latest_rn_recommendations,
        latest_rn_attention_points=codex_control_status.latest_rn_attention_points,
        latest_production_models=codex_control_status.latest_production_models,
        latest_candidate_models=codex_control_status.latest_candidate_models,
        latest_lab_models=codex_control_status.latest_lab_models,
        latest_do_not_promote_notes=codex_control_status.latest_do_not_promote_notes,
    )

    return RoutingNeuronAdminState(
        snapshot=snapshot,
        dossier=dossier,
        lifecycle_counts=lifecycle_counts,
        score_axes=score_axes,
        runtime_status=runtime_status,
        codex_control=codex_control,
        footprint=footprint,
        seal_status=seal_status,
    )


__all__ = ["build_admin_state"]
