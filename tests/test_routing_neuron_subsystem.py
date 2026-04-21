import unittest
from dataclasses import replace
from pathlib import Path

from backend.app import routing_neuron
from backend.app.routing_neuron.admin.repertoire import build_admin_state
from backend.app.routing_neuron.core.governor import build_governance_snapshot
from backend.app.routing_neuron.core.observer import (
    activate_runtime_ready_candidates,
    resolve_runtime_observation_seed,
)
from backend.app.routing_neuron.core.promoter import describe_promotion_path
from backend.app.routing_neuron.core.runtime import (
    ROUTING_RUNTIME_APPLIED,
    ROUTING_RUNTIME_HISTORY_LIMIT,
    ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH,
    ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED,
    ROUTING_RUNTIME_PATH_SELECTED_BLOCKED,
    RoutingRuntimeDecision,
    record_runtime_outcome,
)
from backend.app.routing_neuron.schemas.routing_neuron import (
    ROUTING_DERIVED_ADMIN_STATES,
    ROUTING_LIFECYCLE_OBSERVED_PATTERN,
    ROUTING_LIFECYCLE_PROMOTION_READY,
    ROUTING_LIFECYCLE_PROMOTED,
    ROUTING_LIFECYCLE_RETIRED,
    ROUTING_LIFECYCLE_STABILIZED,
    ROUTING_PRIMARY_SCORE_AXES,
    ROUTING_RUNTIME_BASE_STATES,
    derive_activation_barriers,
    derive_lifecycle_state,
    derive_side_state,
)
from agents.routing_neuron_registry import (
    PROMOTION_STAGE_ADAPTER,
    ROUTING_SELECTION_HOLD,
    ROUTING_STATE_ACTIVE,
    ROUTING_STABILITY_FRAGILE,
    ROUTING_STABILITY_STABLE,
    ROUTING_CONFIDENCE_SUSTAINED_VALUE,
    build_empty_routing_neuron_registry,
    register_routing_neuron_candidate,
)


class RoutingNeuronSubsystemTest(unittest.TestCase):
    def _build_candidate(self):
        candidate = register_routing_neuron_candidate(
            task_signature="technical_api_recovery",
            activated_components=("granite", "olmo"),
            activation_rule="prefer_primary_only_when_verified",
            routing_condition="technical verification critic_optional",
            intermediate_transform=None,
            success_history=("ok", "ok", "ok"),
            failure_history=(),
            expected_gain=0.32,
            estimated_cost=0.18,
            estimated_latency=0.24,
        )
        self.assertIsNotNone(candidate)
        return candidate

    def test_canonical_package_exports_expected_entrypoints(self):
        self.assertTrue(hasattr(routing_neuron, "build_admin_state"))
        self.assertTrue(hasattr(routing_neuron, "build_governance_snapshot"))
        self.assertTrue(hasattr(routing_neuron, "list_recent_admin_actions"))
        self.assertTrue(hasattr(routing_neuron, "resolve_next_promotion_stage"))

    def test_subsystem_structure_contains_expected_directories_and_tracking_files(self):
        root = Path("backend/app/routing_neuron")
        self.assertTrue(root.exists())
        for folder in ("blueprint", "core", "schemas", "admin"):
            self.assertTrue((root / folder).is_dir(), folder)
        for relative_path in (
            "blueprint/routing_neuron_v1.md",
            "blueprint/routing_neuron_checkpoint.md",
            "blueprint/routing_neuron_changelog.md",
            "blueprint/routing_neuron_roadmap.md",
            "admin/observable.py",
            "admin/rendering.py",
        ):
            self.assertTrue((root / relative_path).exists(), relative_path)

    def test_runtime_observation_seed_can_prepare_future_skip_critic_path(self):
        seed = resolve_runtime_observation_seed(
            task_signature="technical_reasoning:technical_explain:model",
            task_type="technical_reasoning",
            risk_profile="medium",
            baseline_route="primary_then_critic",
            evaluated_route="primary_then_critic",
            runtime_influence=None,
            prompt_transform=None,
            critic_used=True,
            verification_outcome="verified",
        )

        self.assertEqual(seed.activation_rule, "prefer_primary_only_when_verified")
        self.assertIn("skip_critic", seed.routing_condition)

    def test_runtime_ready_candidates_can_activate_without_full_maintenance_pass(self):
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_verified",
            routing_condition="technical_reasoning medium skip_critic critic_optional verified",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.18,
            estimated_cost=0.1,
            estimated_latency=70.0,
            neuron_type="selection",
        )
        self.assertIsNotNone(candidate)
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)

        activated = activate_runtime_ready_candidates(registry)

        self.assertIn(candidate.neuron_id, activated.active)
        self.assertEqual(activated.active[candidate.neuron_id].neuron_state, ROUTING_STATE_ACTIVE)

    def test_admin_state_marks_v1_sealed_without_cutover_only_identity(self):
        admin_state = build_admin_state(build_empty_routing_neuron_registry())

        self.assertTrue(admin_state.seal_status.v1_sealed)
        self.assertEqual(admin_state.seal_status.structural_status, "sealed_structurally")
        self.assertEqual(
            admin_state.seal_status.operational_validation_status,
            "runtime_validation_in_progress",
        )
        self.assertTrue(admin_state.seal_status.subsystem_present)
        self.assertTrue(admin_state.seal_status.score_axes_present)
        self.assertFalse(admin_state.seal_status.tactical_cutover_only)
        self.assertIn("no_runtime_history_observed_yet", admin_state.seal_status.gaps)
        self.assertIn("observed_pattern", admin_state.seal_status.represented_states)
        self.assertIn("promoted", admin_state.seal_status.represented_states)
        self.assertIn("score_axes_and_global_score", admin_state.seal_status.sealed_scope)
        self.assertIn("legacy_registry_and_maintenance_backplane", admin_state.seal_status.partial_scope)
        self.assertIn("extended_lifecycle_states_are_partly_derived", admin_state.seal_status.partial_scope)
        self.assertIn(
            "migrate_registry_and_maintenance_to_canonical_namespace",
            admin_state.seal_status.v1x_debts,
        )
        self.assertIn("ui_panel", admin_state.seal_status.out_of_scope)
        self.assertEqual(tuple(axis.axis for axis in admin_state.score_axes), ROUTING_PRIMARY_SCORE_AXES)
        self.assertEqual(admin_state.runtime_status.total_decisions, 0)
        self.assertEqual(admin_state.runtime_status.history_window_limit, ROUTING_RUNTIME_HISTORY_LIMIT)
        self.assertEqual(admin_state.runtime_status.degraded_decisions, 0)
        self.assertEqual(
            admin_state.runtime_status.observability_status,
            "runtime_ready_but_no_history",
        )
        self.assertEqual(
            admin_state.runtime_status.validation_status,
            "runtime_validation_in_progress",
        )

    def test_v11_runtime_is_canonical_and_legacy_paths_are_wrappers(self):
        canonical_runtime = Path("backend/app/routing_neuron/core/runtime.py").read_text(encoding="utf-8")
        canonical_observer = Path("backend/app/routing_neuron/core/observer.py").read_text(encoding="utf-8")
        legacy_runtime = Path("agents/routing_runtime.py").read_text(encoding="utf-8")
        legacy_observer = Path("agents/routing_observer.py").read_text(encoding="utf-8")

        self.assertIn("def apply_routing_runtime(", canonical_runtime)
        self.assertNotIn("from agents.routing_runtime import *", canonical_runtime)
        self.assertIn("def ingest_routing_observation(", canonical_observer)
        self.assertNotIn("from agents.routing_observer import *", canonical_observer)
        self.assertIn("backend.app.routing_neuron.core.runtime", legacy_runtime)
        self.assertIn("backend.app.routing_neuron.core.observer", legacy_observer)

    def test_admin_state_exposes_runtime_status_with_barriers_and_recent_decisions(self):
        decision = RoutingRuntimeDecision(
            applied=False,
            decision="blocked_by_barrier",
            neuron_id="rn:test",
            neuron_state=ROUTING_STATE_ACTIVE,
            neuron_type="control",
            influence=None,
            prompt_transform=None,
            updated_routing_decision=None,
            updated_gateway_mode=None,
            trace=("routing_neuron:decision:blocked",),
            conflict="rn:test>rn:alt",
            fallback_reason="rn:test:budget_barrier",
            alerts=("budget_guard",),
            considered=True,
            considered_ids=("rn:test", "rn:alt"),
            selected=True,
            barriers_checked=("state", "budget"),
            barriers_blocked=("budget",),
            conflict_resolution="highest_global_score_then_activation_frequency_then_efficiency",
        )
        registry = record_runtime_outcome(
            build_empty_routing_neuron_registry(),
            decision,
            session_id="session-runtime",
            task_signature="technical_api_recovery",
            outcome_label="baseline_kept",
        )

        admin_state = build_admin_state(registry)

        self.assertEqual(admin_state.runtime_status.total_decisions, 1)
        self.assertEqual(admin_state.runtime_status.considered_decisions, 1)
        self.assertEqual(admin_state.runtime_status.selected_decisions, 1)
        self.assertEqual(admin_state.runtime_status.blocked_decisions, 1)
        self.assertEqual(admin_state.runtime_status.fallback_decisions, 1)
        self.assertEqual(admin_state.runtime_status.degraded_decisions, 0)
        self.assertEqual(
            admin_state.runtime_status.observability_status,
            "blocked_or_baseline_only",
        )
        self.assertEqual(
            admin_state.runtime_status.validation_status,
            "baseline_only_validation",
        )
        self.assertIn("rn:test", admin_state.runtime_status.considered_neurons)
        self.assertIn("rn:test", admin_state.runtime_status.blocked_neurons)
        self.assertIn("budget x1", admin_state.runtime_status.frequent_barriers)
        self.assertIn("rn:test:budget_barrier x1", admin_state.runtime_status.frequent_fallbacks)
        self.assertIn("baseline_kept x1", admin_state.runtime_status.frequent_outcomes)
        self.assertIn("rn:test>rn:alt", admin_state.runtime_status.recent_conflicts)
        self.assertIn("blocked_by_barrier:rn:test:active", admin_state.runtime_status.recent_decisions)
        self.assertEqual(admin_state.runtime_status.selected_not_applied_decisions, 1)
        self.assertIn(ROUTING_RUNTIME_PATH_SELECTED_BLOCKED, admin_state.runtime_status.recent_paths)

    def test_admin_state_marks_applied_runtime_as_low_sample_until_history_grows(self):
        decision = RoutingRuntimeDecision(
            applied=True,
            decision=ROUTING_RUNTIME_APPLIED,
            neuron_id="rn:applied",
            neuron_state=ROUTING_STATE_ACTIVE,
            neuron_type="selection",
            influence="skip_critic",
            prompt_transform=None,
            updated_routing_decision="primary_only",
            updated_gateway_mode=None,
            trace=("routing_neuron:decision:applied",),
            considered=True,
            considered_ids=("rn:applied",),
            selected=True,
            barriers_checked=("state", "budget", "context"),
            barriers_blocked=(),
        )
        registry = record_runtime_outcome(
            build_empty_routing_neuron_registry(),
            decision,
            session_id="session-applied",
            task_signature="technical_api_recovery",
            outcome_label="improved",
        )

        admin_state = build_admin_state(registry)

        self.assertEqual(admin_state.runtime_status.total_decisions, 1)
        self.assertEqual(admin_state.runtime_status.applied_decisions, 1)
        self.assertEqual(admin_state.runtime_status.fallback_decisions, 0)
        self.assertEqual(
            admin_state.runtime_status.observability_status,
            "healthy_but_low_sample",
        )
        self.assertEqual(
            admin_state.runtime_status.validation_status,
            "runtime_validation_low_sample",
        )
        self.assertIn("applied_runtime_still_low_sample", admin_state.seal_status.gaps)
        self.assertIn("improved x1", admin_state.runtime_status.frequent_outcomes)
        self.assertEqual(admin_state.runtime_status.selected_not_applied_decisions, 0)
        self.assertIn("skip_critic:improved", admin_state.runtime_status.recent_applied_influences)

    def test_runtime_record_retention_uses_rolling_window(self):
        registry = build_empty_routing_neuron_registry()
        for index in range(ROUTING_RUNTIME_HISTORY_LIMIT + 5):
            decision = RoutingRuntimeDecision(
                applied=False,
                decision="no_signal",
                neuron_id=None,
                neuron_state=None,
                neuron_type=None,
                influence=None,
                prompt_transform=None,
                updated_routing_decision=None,
                updated_gateway_mode=None,
                trace=("routing_neuron:decision:no_signal",),
                considered=True,
                considered_ids=(),
                selected=False,
                barriers_checked=(),
                barriers_blocked=(),
                fallback_reason="no_match",
            )
            registry = record_runtime_outcome(
                registry,
                decision,
                session_id="session-window",
                task_signature=f"task-{index}",
                outcome_label="fallback_no_provider",
                outcome_summary=f"iteracion {index}",
            )

        self.assertEqual(len(registry.runtime_records), ROUTING_RUNTIME_HISTORY_LIMIT)
        self.assertEqual(registry.runtime_records[-1].outcome_summary, f"iteracion {ROUTING_RUNTIME_HISTORY_LIMIT + 4}")
        self.assertEqual(registry.runtime_records[-1].decision_path, ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH)

    def test_admin_state_accumulates_mixed_runtime_history_and_recent_outcomes(self):
        registry = build_empty_routing_neuron_registry()
        registry = record_runtime_outcome(
            registry,
            RoutingRuntimeDecision(
                applied=False,
                decision="no_signal",
                neuron_id=None,
                neuron_state=None,
                neuron_type=None,
                influence=None,
                prompt_transform=None,
                updated_routing_decision=None,
                updated_gateway_mode=None,
                trace=("routing_neuron:decision:no_signal",),
                fallback_reason="no_match",
                considered=True,
                considered_ids=(),
                selected=False,
                barriers_checked=(),
                barriers_blocked=(),
            ),
            session_id="session-mixed",
            task_signature="simple_greeting",
            outcome_label="fallback_runtime_error",
            outcome_summary="model_missing",
        )
        registry = record_runtime_outcome(
            registry,
            RoutingRuntimeDecision(
                applied=False,
                decision="blocked_by_barrier",
                neuron_id="rn:blocked",
                neuron_state=ROUTING_STATE_ACTIVE,
                neuron_type="control",
                influence=None,
                prompt_transform=None,
                updated_routing_decision=None,
                updated_gateway_mode=None,
                trace=("routing_neuron:decision:blocked",),
                fallback_reason="rn:blocked:budget_barrier",
                considered=True,
                considered_ids=("rn:blocked",),
                selected=True,
                barriers_checked=("state", "budget"),
                barriers_blocked=("budget",),
            ),
            session_id="session-mixed",
            task_signature="technical_api_recovery",
            outcome_label="baseline_kept",
            outcome_summary="budget_guard",
        )
        registry = record_runtime_outcome(
            registry,
            RoutingRuntimeDecision(
                applied=True,
                decision=ROUTING_RUNTIME_APPLIED,
                neuron_id="rn:applied",
                neuron_state=ROUTING_STATE_ACTIVE,
                neuron_type="selection",
                influence="skip_critic",
                prompt_transform=None,
                updated_routing_decision="primary_only",
                updated_gateway_mode=None,
                trace=("routing_neuron:decision:applied",),
                considered=True,
                considered_ids=("rn:applied",),
                selected=True,
                barriers_checked=("state", "budget", "context"),
                barriers_blocked=(),
            ),
            session_id="session-mixed",
            task_signature="technical_api_recovery",
            outcome_label="improved",
            outcome_summary="critic_skipped_cleanly",
        )

        admin_state = build_admin_state(registry)

        self.assertEqual(admin_state.runtime_status.total_decisions, 3)
        self.assertEqual(admin_state.runtime_status.considered_decisions, 3)
        self.assertEqual(admin_state.runtime_status.selected_decisions, 2)
        self.assertEqual(admin_state.runtime_status.applied_decisions, 1)
        self.assertEqual(admin_state.runtime_status.blocked_decisions, 1)
        self.assertEqual(admin_state.runtime_status.fallback_decisions, 2)
        self.assertEqual(admin_state.runtime_status.degraded_decisions, 1)
        self.assertEqual(admin_state.runtime_status.no_signal_decisions, 1)
        self.assertEqual(
            admin_state.runtime_status.observability_status,
            "healthy_but_low_sample",
        )
        self.assertEqual(
            admin_state.runtime_status.validation_status,
            "runtime_validation_low_sample",
        )
        self.assertEqual(admin_state.runtime_status.selected_not_applied_decisions, 1)
        self.assertEqual(admin_state.runtime_status.no_candidate_decisions, 1)
        self.assertIn("budget x1", admin_state.runtime_status.frequent_barriers)
        self.assertIn("no_match x1", admin_state.runtime_status.frequent_fallbacks)
        self.assertIn("fallback_runtime_error x1", admin_state.runtime_status.frequent_outcomes)
        self.assertIn("improved:applied", admin_state.runtime_status.recent_outcomes)
        self.assertIn(ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED, admin_state.runtime_status.recent_paths)
        self.assertIn("rn:blocked", admin_state.runtime_status.blocked_neurons)
        self.assertIn("rn:applied", admin_state.runtime_status.applied_neurons)

    def test_governance_snapshot_exposes_barriers_conflict_and_fallback_mode(self):
        decision = RoutingRuntimeDecision(
            applied=False,
            decision="cooldown",
            neuron_id="rn:cooldown",
            neuron_state=ROUTING_STATE_ACTIVE,
            neuron_type="control",
            influence=None,
            prompt_transform=None,
            updated_routing_decision=None,
            updated_gateway_mode=None,
            trace=("routing_neuron:decision:cooldown",),
            conflict=None,
            fallback_reason="cooldown_active",
            alerts=("cooldown_guard",),
            considered=True,
            considered_ids=("rn:cooldown",),
            selected=True,
            barriers_checked=("cooldown",),
            barriers_blocked=("cooldown",),
        )

        snapshot = build_governance_snapshot(decision)

        self.assertEqual(snapshot.decision, "cooldown")
        self.assertFalse(snapshot.applied)
        self.assertTrue(snapshot.considered)
        self.assertEqual(snapshot.considered_ids, ("rn:cooldown",))
        self.assertTrue(snapshot.selected)
        self.assertEqual(snapshot.barrier_reason, "cooldown")
        self.assertEqual(snapshot.barriers_blocked, ("cooldown",))
        self.assertEqual(snapshot.fallback_mode, "cooldown_baseline")
        self.assertEqual(snapshot.alerts, ("cooldown_guard",))

    def test_lifecycle_helpers_cover_stabilized_promotion_ready_promoted_and_retired(self):
        candidate = self._build_candidate()
        observed = replace(candidate, neuron_state="observed_pattern")
        stabilized = replace(
            candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            confidence_tier=ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            stability_label=ROUTING_STABILITY_STABLE,
        )
        promotion_ready = replace(
            stabilized,
            promotion_ready_signal=True,
            readiness_band="near_ready",
        )
        promoted = replace(stabilized, promotion_stage=PROMOTION_STAGE_ADAPTER)
        retired = replace(candidate, launch_status="rejected")
        demoted = replace(
            candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            stability_label=ROUTING_STABILITY_FRAGILE,
            selection_status=ROUTING_SELECTION_HOLD,
            estimated_cost=0.82,
            recent_conflict_count=1,
            activated_components=("granite", "olmo", "smollm2"),
            fallback_target="baseline_route",
        )

        self.assertEqual(derive_lifecycle_state(observed), ROUTING_LIFECYCLE_OBSERVED_PATTERN)
        self.assertEqual(derive_lifecycle_state(stabilized), ROUTING_LIFECYCLE_STABILIZED)
        self.assertEqual(derive_lifecycle_state(promotion_ready), ROUTING_LIFECYCLE_PROMOTION_READY)
        self.assertEqual(derive_lifecycle_state(promoted), ROUTING_LIFECYCLE_PROMOTED)
        self.assertEqual(derive_lifecycle_state(retired), ROUTING_LIFECYCLE_RETIRED)
        self.assertEqual(derive_side_state(demoted), "demoted")
        self.assertEqual(
            derive_activation_barriers(demoted),
            ("budget", "context", "competitive", "stability", "composition", "fallback"),
        )

    def test_blueprint_tracking_files_exist_and_promotion_path_starts_at_specialized_prompt(self):
        blueprint_root = Path("backend/app/routing_neuron/blueprint")
        for relative_path in (
            "routing_neuron_v1.md",
            "routing_neuron_checkpoint.md",
            "routing_neuron_changelog.md",
            "routing_neuron_roadmap.md",
        ):
            self.assertTrue((blueprint_root / relative_path).exists(), relative_path)

        candidate = self._build_candidate()
        path = describe_promotion_path(candidate)
        self.assertEqual(path.current_stage, "specialized_prompt")
        self.assertEqual(path.next_stage, "adapter")
        self.assertTrue(path.reversible_default)

        blueprint = (blueprint_root / "routing_neuron_v1.md").read_text(encoding="utf-8")
        checkpoint = (blueprint_root / "routing_neuron_checkpoint.md").read_text(encoding="utf-8")
        roadmap = (blueprint_root / "routing_neuron_roadmap.md").read_text(encoding="utf-8")
        self.assertIn("score", blueprint)
        self.assertIn("runtime limitado", blueprint)
        self.assertIn("sellado estructural", blueprint)
        self.assertIn("No definen la identidad de Routing Neuron V1", blueprint)
        self.assertIn("compatibilidad legacy", checkpoint)
        self.assertIn("validacion operativa en progreso", checkpoint)
        self.assertIn("no identidad central", roadmap)
        self.assertIn("historial operativo observado", roadmap)

    def test_runtime_and_derived_states_are_explicitly_separated(self):
        self.assertEqual(
            ROUTING_RUNTIME_BASE_STATES,
            ("observed_pattern", "candidate", "active", "paused"),
        )
        self.assertEqual(
            ROUTING_DERIVED_ADMIN_STATES,
            ("stabilized", "promotion_ready", "promoted", "retired"),
        )


if __name__ == "__main__":
    unittest.main()
