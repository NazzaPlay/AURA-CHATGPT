import copy
import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from agents.behavior_agent import BehaviorPlan, classify_user_intent
from agents.capabilities_registry import (
    CAPABILITY_HEURISTIC_RESPONSE,
    CapabilityContext,
)
from agents.critic_layer import plan_critic
from agents.consistency_agent import (
    CONSISTENCY_STATUS_CONDITIONAL,
    CONSISTENCY_STATUS_CONFLICTED,
    CONSISTENCY_STATUS_TENSION_DETECTED,
    CONSISTENCY_STATUS_UNCERTAIN,
)
from agents.core_agent import execute_turn, prepare_turn
from agents.fallback_manager import build_fallback_response
from agents.feasibility_agent import (
    FEASIBILITY_STATUS_CONTRADICTORY,
    FEASIBILITY_STATUS_NOT_FEASIBLE,
    FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS,
    FEASIBILITY_STATUS_UNCERTAIN,
)
from agents.model_gateway import invoke_model_gateway
from agents.model_benchmark import (
    build_benchmark_preparation_snapshot,
    BenchmarkSnapshot,
    assess_benchmark_snapshot,
    build_benchmark_targets,
)
from agents.model_registry import (
    ARTIFACT_FORMAT_GGUF,
    MODEL_POLICY_ACTIVE_GREEN,
    MODEL_POLICY_ALLOWLIST,
    MODEL_POLICY_TRANSITIONAL_FALLBACK,
    ROLE_CRITIC,
    ROLE_MICRO_EXPERT_ROUTER,
    ROLE_PRIMARY,
    RUNTIME_BACKEND_LLAMA_CPP,
    STACK_HEALTH_DEGRADED,
    STACK_HEALTH_HEALTHY,
    STACK_HEALTH_MISSING_MODELS,
    STACK_HEALTH_PARTIAL_STACK,
    build_default_model_registry,
    build_model_bank_governance_snapshot,
    build_stack_health_snapshot,
)
from backend.app.routing_neuron.control import (
    build_codex_control_status,
    ensure_codex_control_registry,
    load_codex_control_registry,
    update_codex_control_registry,
)
from agents.routing_maintenance import (
    RoutingRepertoireEntry,
    build_routing_launch_dossier,
    build_routing_repertoire_snapshot,
    run_routing_maintenance,
)
from agents.routing_observer import ingest_routing_observation
from agents.routing_neuron_registry import (
    ACTION_OUTCOME_HELPED,
    ACTION_OUTCOME_NO_CLEAR_CHANGE,
    ALERT_STATUS_ACKNOWLEDGED,
    ALERT_STATUS_REOPENED,
    ALERT_STATUS_RESOLVED,
    PROMOTION_STAGE_ADAPTER,
    PROMOTION_STAGE_SPECIALIZED_PROMPT,
    PROMOTION_STAGES,
    REVIEW_STATUS_OPEN,
    REVIEW_STATUS_RESOLVED,
    REVIEW_STATUS_STALE,
    REVIEW_STATUS_WATCH,
    ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
    ROUTING_CONFIDENCE_EARLY_SIGNAL,
    ROUTING_CONFIDENCE_SUSTAINED_VALUE,
    ROUTING_BRIDGE_PREFLIGHT_BLOCKED,
    ROUTING_BRIDGE_PREFLIGHT_CANDIDATE,
    ROUTING_BRIDGE_PREFLIGHT_DEFERRED,
    ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED,
    ROUTING_BRIDGE_PREFLIGHT_READY,
    ROUTING_CURATION_DISCARDABLE,
    ROUTING_CURATION_PROMISING,
    ROUTING_CURATION_USEFUL,
    ROUTING_INFLUENCE_BRIDGE_WATCH,
    ROUTING_INFLUENCE_EMERGING,
    ROUTING_INFLUENCE_SHORTLIST_READY,
    ROUTING_CUTOVER_BLOCKED,
    ROUTING_CUTOVER_GO_CANDIDATE,
    ROUTING_CUTOVER_NEAR_GO,
    ROUTING_CUTOVER_NOT_READY,
    ROUTING_CUTOVER_WATCH,
    ROUTING_LAUNCH_APPROVED,
    ROUTING_LAUNCH_HOLD,
    ROUTING_LAUNCH_REJECTED,
    ROUTING_LAUNCH_SUPPORT_ONLY,
    ROUTING_READINESS_EMERGING,
    ROUTING_READINESS_NEAR_READY,
    ROUTING_READINESS_NOT_READY,
    ROUTING_REHEARSAL_BLOCKED,
    ROUTING_REHEARSAL_CANDIDATE,
    ROUTING_REHEARSAL_DEFERRED,
    ROUTING_REHEARSAL_NOT_IN_REHEARSAL,
    ROUTING_REHEARSAL_READY,
    ROUTING_REVIEW_PRIORITY_HIGH,
    ROUTING_REVIEW_PRIORITY_MEDIUM,
    ROUTING_ROLE_CONTEXT_FILTER,
    ROUTING_ROLE_MIGRATION_GUARD,
    ROUTING_ROLE_ROUTER_SUPPORT,
    ROUTING_SELECTION_DISCARDABLE,
    ROUTING_SELECTION_OBSERVED_ONLY,
    ROUTING_SELECTION_SHORTLISTED,
    ROUTING_STACK_FIT_GRANITE,
    ROUTING_STACK_FIT_NEUTRAL,
    ROUTING_STACK_FIT_OLMO,
    ROUTING_STACK_FIT_SMOLLM2,
    ROUTING_STATE_ACTIVE,
    ROUTING_STATE_CANDIDATE,
    ROUTING_STATE_OBSERVED_PATTERN,
    ROUTING_STATE_PAUSED,
    ROUTING_STABILITY_DEGRADING,
    ROUTING_STABILITY_FRAGILE,
    ROUTING_STABILITY_IMPROVING,
    ROUTING_STABILITY_OBSERVING,
    ROUTING_STABILITY_STABLE,
    RoutingPromotionRecommendation,
    ROUTING_TYPE_CONTROL,
    ROUTING_TYPE_SELECTION,
    ROUTING_TYPE_TRANSFORMATION,
    build_evidence_record,
    build_empty_routing_neuron_registry,
    promote_routing_neuron,
    register_routing_neuron_candidate,
)
from agents.response_agent import execute_model_response
from agents.routing_policy import decide_routing
from agents.routing_runtime import (
    apply_routing_runtime,
    get_default_routing_registry,
    reset_default_routing_registry,
    ROUTING_RUNTIME_APPLIED,
    ROUTING_RUNTIME_BLOCKED,
    ROUTING_RUNTIME_COOLDOWN,
    ROUTING_RUNTIME_NO_SIGNAL,
    ROUTING_RUNTIME_PAUSED,
    ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE,
    ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH,
    ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED,
    ROUTING_RUNTIME_PATH_SELECTED_BLOCKED,
    ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED,
    ROUTING_RUNTIME_SUGGESTED_ONLY,
    set_default_routing_registry,
)
from agents.response_composer import (
    COMPOSITION_MODE_PROVIDER_PRIMARY,
    COMPOSITION_MODE_PROVIDER_PRIMARY_WITH_CRITIC,
    COMPOSITION_MODE_FALLBACK_SAFE,
    VERIFICATION_OUTCOME_VERIFIED,
)
from agents.runtime_quality import (
    QUALITY_STATUS_OFF_TOPIC,
    QUALITY_STATUS_PLACEHOLDER,
    assess_runtime_quality,
)
from agents.internal_sequences_registry import (
    SEQUENCE_CONSISTENCY_EVALUATION,
    SEQUENCE_FEASIBILITY_EVALUATION,
    SEQUENCE_STRATEGIC_GUIDANCE,
)
from agents.internal_actions_registry import ACTION_HEURISTIC_RESPONSE, ACTION_SYSTEM_STATE
from agents.internal_tools_registry import TOOL_RESPONSE_HEURISTICS, TOOL_SYSTEM_STATE_READER
from agents.router_agent import ROUTE_HEURISTIC_RESPONSE, ROUTE_MODEL, ROUTE_SYSTEM_STATE
from agents.task_classifier import (
    TASK_TYPE_CHAT_RESPONSE,
    TASK_TYPE_NO_MODEL_NEEDED,
    TASK_TYPE_TECHNICAL_REASONING,
    classify_task,
)
from agents.internal_tools_agent import (
    ADVICE_FRAME_CONTRADICTION,
    ADVICE_FRAME_ASSERTION,
    ADVICE_FRAME_CONTEXT_TENSION,
    ADVICE_FRAME_CONFIDENCE,
    ADVICE_FRAME_DEPENDENCY,
    ADVICE_FRAME_ENTRY_STEP,
    ADVICE_FRAME_EVIDENCE,
    ADVICE_FRAME_EXPLOIT_PLAY,
    ADVICE_FRAME_EXPLAINED_NOW,
    ADVICE_FRAME_FEASIBILITY,
    ADVICE_FRAME_FIRST_MOVE,
    ADVICE_FRAME_FOLLOWUP_MOVE,
    ADVICE_FRAME_FOCUS_NOW,
    ADVICE_FRAME_HELP_NOW,
    ADVICE_FRAME_HIGHEST_VALUE,
    ADVICE_FRAME_LIMITS,
    ADVICE_FRAME_LATER_MOVE,
    ADVICE_FRAME_MICRO_PLAN,
    ADVICE_FRAME_PAIRED_MOVES,
    ADVICE_FRAME_PRIORITY_NOW,
    ADVICE_FRAME_REALISM,
    ADVICE_FRAME_RECOVERY_PLAY,
    MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY,
    MOMENT_PROFILE_EXPLOIT_NOW,
    MOMENT_PROFILE_MAINTAIN_BEFORE_ADVANCING,
    MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST,
    SITUATIONAL_PROFILE_EXPLOIT,
    SITUATIONAL_PROFILE_MAINTENANCE,
    SITUATIONAL_PROFILE_RECOVERY,
    analyze_internal_tools_query,
    resolve_contextual_response_signals,
)
from config import (
    AURA_VERSION,
    CRITIC_MODEL_NAME,
    PRIMARY_MODEL_NAME,
    ROUTER_MODEL_NAME,
    TRANSITIONAL_FALLBACK_MODEL_NAME,
)
from providers import (
    LOCAL_CRITIC_PROVIDER_ID,
    LOCAL_PRIMARY_PROVIDER_ID,
    LOCAL_PROVIDER_CRITIC_ROLE,
    LOCAL_PROVIDER_ROUTER_ROLE,
    LOCAL_ROUTER_PROVIDER_ID,
    LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
    PROVIDER_RESULT_SUCCESS,
)
from model_runner import _extract_response


def _build_fake_codex_registry() -> dict:
    """Registry fake en memoria para tests system_state sin tocar disco."""
    return {
        "registry_version": "1.3",
        "schema_version": "codex_control_registry.v1.3",
        "latest": {
            "run_id": "codex-v0394",
            "version_target": "0.39.6",
            "timestamp": "2026-04-28T00:00:00Z",
            "status": "completed",
            "work_type": "consolidation",
            "requested_scope": "test scope H3",
            "summary": "resumen fake para test system_state",
            "tests_status": "ok",
            "smokes_status": "ok",
            "files_modified_count": 1,
            "files_created_count": 1,
            "modules_touched": ["agents.system_state_agent"],
            "contracts_affected": ["codex_control_registry_schema"],
        },
        "entries": [{
            "run_id": "codex-v0394",
            "version_target": "0.39.6",
            "timestamp": "2026-04-28T00:00:00Z",
            "status": "completed",
            "work_type": "consolidation",
            "requested_scope": "test scope H3",
            "summary": "resumen fake para test system_state",
            "files_modified": ["agents/system_state_agent.py"],
            "files_created": ["backend/app/routing_neuron/control/codex_control_registry.json"],
            "files_deleted": [],
            "files_moved": [],
            "modules_touched": ["agents.system_state_agent"],
            "contracts_affected": ["codex_control_registry_schema"],
            "tests_run": [],
            "tests_result": {"status": "ok", "summary": "ok"},
            "smokes_run": [],
            "smokes_result": {"status": "ok", "summary": "ok"},
            "checkpoint_short": "checkpoint fake H3.9B2",
            "open_debts": ["long tail tecnico abierto"],
            "aura_changes": [],
            "rn_changes": [],
            "model_bank_changes": [],
            "next_recommended_step": "benchmark serio sobre candidatos inmediatos",
            "rn_recent_outcomes": [],
            "rn_recommendations": [],
            "rn_attention_points": [],
            "known_good": "zona estable fake",
            "known_weakness": "debilidad fake",
        }],
        "latest_open_debts": ["long tail tecnico abierto"],
        "latest_known_good": "zona estable fake",
        "latest_known_weakness": "debilidad fake",
        "latest_version_closed_for_scope": "0.39.6",
        "latest_runtime_health": "watch",
        "latest_test_health": "ok",
        "latest_risk": "medium",
        "latest_checkpoint": "checkpoint fake",
        "latest_checkpoint_short": "checkpoint fake",
        "latest_next_step": "benchmark serio sobre candidatos inmediatos",
        "latest_review_artifacts_needed": ["codex_control_registry.json"],
        "known_issues": {"latest_long_tail_failures": []},
        "runtime_patterns": {
            "fallback_patterns": [],
            "degradation_patterns": [],
            "critic_patterns": [],
            "router_patterns": [],
        },
        "model_bank": {
            "production_models": ["Granite 3.0 1B-A400M-Instruct", "OLMo-2-0425-1B-Instruct"],
            "candidate_models": [],
            "lab_models": [],
            "blocked_models": [],
            "do_not_promote_notes": [],
        },
    }


def build_codex_control_status_from_fake_for_tests() -> "CodexControlStatus":
    """Construye un CodexControlStatus desde el fake registry para tests."""
    from backend.app.routing_neuron.control import CodexControlStatus

    fake = _build_fake_codex_registry()
    latest = fake.get("latest", {})
    entries = fake.get("entries", [])
    entry = entries[0] if entries else {}
    runtime_patterns = fake.get("runtime_patterns", {})
    model_bank = fake.get("model_bank", {})

    return CodexControlStatus(
        registry_path="fake",
        registry_version=fake.get("registry_version", "1.3"),
        schema_version=fake.get("schema_version", "codex_control_registry.v1.3"),
        entry_count=len(entries),
        latest_run_id=latest.get("run_id"),
        latest_timestamp=latest.get("timestamp"),
        latest_version=latest.get("version_target"),
        latest_status=latest.get("status"),
        latest_work_type=latest.get("work_type"),
        latest_requested_scope=latest.get("requested_scope"),
        latest_summary="Codex registry fake: completed V0.39.6, health watch, risk medium",
        latest_checkpoint="checkpoint fake H3.9D",
        latest_checkpoint_short="checkpoint fake H3.9D",
        latest_checkpoint_long="checkpoint fake H3.9D",
        latest_tests_status=latest.get("tests_status"),
        latest_smokes_status=latest.get("smokes_status"),
        latest_runtime_health=fake.get("latest_runtime_health"),
        latest_test_health=fake.get("latest_test_health"),
        latest_risk=fake.get("latest_risk"),
        latest_next_step=fake.get("latest_next_step"),
        latest_open_debts=tuple(fake.get("latest_open_debts", [])),
        latest_files_modified_count=latest.get("files_modified_count", 0),
        latest_files_created_count=latest.get("files_created_count", 0),
        latest_modules_touched=tuple(latest.get("modules_touched", [])),
        latest_contracts_affected=tuple(latest.get("contracts_affected", [])),
        latest_known_good=fake.get("latest_known_good"),
        latest_known_weakness=fake.get("latest_known_weakness"),
        latest_version_closed_for_scope=fake.get("latest_version_closed_for_scope"),
        latest_review_artifacts_needed=tuple(fake.get("latest_review_artifacts_needed", [])),
        latest_fallback_patterns=tuple(runtime_patterns.get("fallback_patterns", [])),
        latest_degradation_patterns=tuple(runtime_patterns.get("degradation_patterns", [])),
        latest_critic_patterns=tuple(runtime_patterns.get("critic_patterns", [])),
        latest_router_patterns=tuple(runtime_patterns.get("router_patterns", [])),
        latest_long_tail_failures=tuple(fake.get("known_issues", {}).get("latest_long_tail_failures", [])),
        latest_rn_recent_outcomes=tuple(entry.get("rn_recent_outcomes", [])),
        latest_rn_recommendations=tuple(entry.get("rn_recommendations", [])),
        latest_rn_attention_points=tuple(entry.get("rn_attention_points", [])),
        latest_production_models=tuple(model_bank.get("production_models", [])),
        latest_candidate_models=tuple(model_bank.get("candidate_models", [])),
        latest_lab_models=tuple(model_bank.get("lab_models", [])),
        latest_do_not_promote_notes=tuple(model_bank.get("do_not_promote_notes", [])),
    )


@contextmanager
def _codex_registry_mocks():
    """Context manager que mockea TODOS los caminos de side effect del registry real."""
    fake = _build_fake_codex_registry()
    fake_status = build_codex_control_status_from_fake_for_tests()
    fake_status_summary = "Codex registry fake: completed V0.39.6, health watch, risk medium"
    fake_checkpoint_summary = "checkpoint fake H3.9D"
    patches = [
        # Originales
        patch("agents.system_state_agent.load_codex_control_registry", return_value=fake),
        patch("backend.app.routing_neuron.control.registry.load_codex_control_registry", return_value=fake),
        # Nuevos — build_codex_control_status (usando side_effect con helper)
        patch("backend.app.routing_neuron.admin.repertoire.build_codex_control_status", side_effect=lambda *args, **kwargs: build_codex_control_status_from_fake_for_tests()),
        patch("backend.app.routing_neuron.control.registry.build_codex_control_status", side_effect=lambda *args, **kwargs: build_codex_control_status_from_fake_for_tests()),
        # Nuevos — summarize_codex_control_status
        patch("agents.system_state_agent.summarize_codex_control_status", return_value=fake_status_summary),
        patch("backend.app.routing_neuron.control.registry.summarize_codex_control_status", return_value=fake_status_summary),
        # Nuevos — summarize_codex_latest_checkpoint
        patch("agents.system_state_agent.summarize_codex_latest_checkpoint", return_value=fake_checkpoint_summary),
        patch("backend.app.routing_neuron.control.registry.summarize_codex_latest_checkpoint", return_value=fake_checkpoint_summary),
    ]
    for p in patches:
        p.start()
    try:
        yield
    finally:
        for p in patches:
            p.stop()


class AuraV036CoreTest(unittest.TestCase):
    def setUp(self) -> None:
        reset_default_routing_registry()

    def _prepare_runtime(
        self,
        root: Path,
        *,
        model_available: bool = True,
        runtime_mode: str = "exec",
        runtime_output: str | None = None,
        runtime_script: str | None = None,
    ) -> tuple[str, str]:
        root.mkdir(parents=True, exist_ok=True)
        model_path = root / "model.gguf"
        llama_path = root / "llama-cli"

        if model_available:
            model_path.write_text("model", encoding="utf-8")

        if runtime_mode != "missing":
            if os.name == "nt" and runtime_mode != "exec":
                if runtime_script is not None:
                    llama_path.write_text(
                        f"disabled_windows_stub\n{runtime_script}",
                        encoding="utf-8",
                    )
                elif runtime_output is not None:
                    llama_path.write_text(
                        f"disabled_windows_stub\n{runtime_output}\n",
                        encoding="utf-8",
                    )
                else:
                    llama_path.write_text("disabled_windows_stub\n", encoding="utf-8")
            elif runtime_script is not None:
                llama_path.write_text(runtime_script, encoding="utf-8")
            elif runtime_output is not None:
                escaped_output = runtime_output.replace("\\", "\\\\").replace('"', '\\"')
                llama_path.write_text(
                    f'#!/bin/sh\nprintf "%s\\n" "{escaped_output}"\n',
                    encoding="utf-8",
                )
            else:
                llama_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            if runtime_mode == "exec":
                llama_path.chmod(0o755)
            else:
                llama_path.chmod(0o644)

        return str(model_path), str(llama_path)

    def _build_multistack_runtime_script(
        self,
        *,
        granite_output: str = "Idea breve: usa auth estable y rollback probado antes de producción.",
        critic_output: str = "VERIFICADA: sin conflicto claro.",
        router_output: str = "foco breve: responde directo y practico",
        qwen_output: str = "Idea breve: si entras en fallback, mantén una ruta segura y verifica auth antes del deploy.",
    ) -> str:
        return (
            "#!/bin/sh\n"
            "prompt=\"\"\n"
            "model=\"\"\n"
            "while [ \"$#\" -gt 0 ]; do\n"
            "  case \"$1\" in\n"
            "    -p) prompt=\"$2\"; shift 2 ;;\n"
            "    -m) model=\"$2\"; shift 2 ;;\n"
            "    *) shift ;;\n"
            "  esac\n"
            "done\n"
            "case \"$model\" in\n"
            f"  *\"{CRITIC_MODEL_NAME}\"*|*\"OLMo\"*) printf \"%s\\n\" \"{critic_output}\" ;;\n"
            f"  *\"{ROUTER_MODEL_NAME}\"*|*\"smollm2\"*|*\"SmolLM2\"*) printf \"%s\\n\" \"{router_output}\" ;;\n"
            f"  *\"{TRANSITIONAL_FALLBACK_MODEL_NAME}\"*|*\"qwen2\"*) printf \"%s\\n\" \"{qwen_output}\" ;;\n"
            f"  *\"{PRIMARY_MODEL_NAME}\"*|*\"granite\"*|*\"Granite\"*) printf \"%s\\n\" \"{granite_output}\" ;;\n"
            f"  *\"Verificador:\"*) printf \"%s\\n\" \"{critic_output}\" ;;\n"
            "  *) printf \"%s\\n\" \"respuesta generica\" ;;\n"
            "esac\n"
        )

    def _prepare_multistack_runtime(
        self,
        root: Path,
        *,
        missing_models: tuple[str, ...] = (),
        granite_output: str = "Idea breve: usa auth estable y rollback probado antes de producción.",
        critic_output: str = "VERIFICADA: sin conflicto claro.",
        router_output: str = "foco breve: responde directo y practico",
        qwen_output: str = "Idea breve: si entras en fallback, mantén una ruta segura y verifica auth antes del deploy.",
    ) -> dict[str, str]:
        root.mkdir(parents=True, exist_ok=True)
        llama_path = root / "llama-cli"
        llama_path.write_text(
            self._build_multistack_runtime_script(
                granite_output=granite_output,
                critic_output=critic_output,
                router_output=router_output,
                qwen_output=qwen_output,
            ),
            encoding="utf-8",
        )
        llama_path.chmod(0o755)

        paths = {
            "primary": root / PRIMARY_MODEL_NAME,
            "critic": root / CRITIC_MODEL_NAME,
            "router": root / ROUTER_MODEL_NAME,
            "fallback": root / TRANSITIONAL_FALLBACK_MODEL_NAME,
            "llama": llama_path,
        }
        for key, path in paths.items():
            if key == "llama":
                continue
            if key in missing_models:
                continue
            path.write_text("model", encoding="utf-8")

        return {key: str(path) for key, path in paths.items()}

    def _run_turn(
        self,
        user_input: str,
        *,
        memory: dict | None = None,
        model_available: bool = True,
        runtime_mode: str = "exec",
        runtime_output: str | None = None,
        runtime_script: str | None = None,
        conversation: list[dict] | None = None,
        routing_registry=None,
    ):
        reset_default_routing_registry()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            model_path, llama_path = self._prepare_runtime(
                root,
                model_available=model_available,
                runtime_mode=runtime_mode,
                runtime_output=runtime_output,
                runtime_script=runtime_script,
            )
            memory_state = copy.deepcopy(memory or {})
            memory_file = root / "memory.json"
            memory_file.write_text(
                json.dumps(memory_state, ensure_ascii=False),
                encoding="utf-8",
            )
            log_file = root / "session.json"
            conversation_state = copy.deepcopy(conversation or [])
            if routing_registry is not None:
                set_default_routing_registry(routing_registry)

            turn_plan = prepare_turn(
                user_input,
                conversation=conversation_state,
                memory=memory_state,
            )
            self.assertIsNotNone(turn_plan)

            return execute_turn(
                turn_plan,
                conversation=conversation_state,
                memory=memory_state,
                memory_file=str(memory_file),
                log_file=str(log_file),
                llama_path=llama_path,
                model_path=model_path,
                aura_version=AURA_VERSION,
            )

    def _run_turn_sequence(
        self,
        queries: list[str] | tuple[str, ...],
        *,
        memory: dict | None = None,
        model_available: bool = True,
        runtime_mode: str = "exec",
        runtime_output: str | None = None,
        runtime_script: str | None = None,
        routing_registry=None,
    ) -> list:
        reset_default_routing_registry()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            model_path, llama_path = self._prepare_runtime(
                root,
                model_available=model_available,
                runtime_mode=runtime_mode,
                runtime_output=runtime_output,
                runtime_script=runtime_script,
            )
            memory_state = copy.deepcopy(memory or {})
            memory_file = root / "memory.json"
            memory_file.write_text(
                json.dumps(memory_state, ensure_ascii=False),
                encoding="utf-8",
            )
            log_file = root / "session.json"
            conversation_state: list[dict] = []
            results = []
            if routing_registry is not None:
                set_default_routing_registry(routing_registry)

            for query in queries:
                turn_plan = prepare_turn(
                    query,
                    conversation=conversation_state,
                    memory=memory_state,
                )
                self.assertIsNotNone(turn_plan)
                result = execute_turn(
                    turn_plan,
                    conversation=conversation_state,
                    memory=memory_state,
                    memory_file=str(memory_file),
                    log_file=str(log_file),
                    llama_path=llama_path,
                    model_path=model_path,
                    aura_version=AURA_VERSION,
                )
                results.append(result)

            return results

    def _run_turn_with_multistack(
        self,
        user_input: str,
        *,
        memory: dict | None = None,
        conversation: list[dict] | None = None,
        routing_registry=None,
        missing_models: tuple[str, ...] = (),
        granite_output: str = "Idea breve: usa auth estable y rollback probado antes de producción.",
        critic_output: str = "VERIFICADA: sin conflicto claro.",
        router_output: str = "foco breve: responde directo y practico",
        qwen_output: str = "Idea breve: si entras en fallback, mantén una ruta segura y verifica auth antes del deploy.",
    ):
        reset_default_routing_registry()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                missing_models=missing_models,
                granite_output=granite_output,
                critic_output=critic_output,
                router_output=router_output,
                qwen_output=qwen_output,
            )
            memory_state = copy.deepcopy(memory or {})
            memory_file = root / "memory.json"
            memory_file.write_text(
                json.dumps(memory_state, ensure_ascii=False),
                encoding="utf-8",
            )
            log_file = root / "session.json"
            conversation_state = copy.deepcopy(conversation or [])
            if routing_registry is not None:
                set_default_routing_registry(routing_registry)

            turn_plan = prepare_turn(
                user_input,
                conversation=conversation_state,
                memory=memory_state,
            )
            self.assertIsNotNone(turn_plan)

            return execute_turn(
                turn_plan,
                conversation=conversation_state,
                memory=memory_state,
                memory_file=str(memory_file),
                log_file=str(log_file),
                llama_path=stack["llama"],
                model_path=stack["primary"],
                aura_version=AURA_VERSION,
            )

    def _seed_improved_evidence(
        self,
        registry,
        candidate,
        *,
        count: int,
        prefix: str,
        latency_ms: float = 68.0,
        latency_delta: float = -16.0,
        cost_delta: float = -0.03,
        quality_delta: float = 0.18,
        verification_delta: float = 0.07,
        consistency_delta: float = 0.04,
        evaluated_route: str = "primary_only",
    ):
        updated_registry = registry
        for index in range(count):
            evidence = build_evidence_record(
                task_signature=candidate.task_signature,
                session_id=f"{prefix}-{index}",
                task_profile="technical_reasoning",
                risk_profile="low",
                budget_profile="normal",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route=evaluated_route,
                activated_components=candidate.activated_components,
                latency_ms=latency_ms,
                latency_delta=latency_delta,
                cost_delta=cost_delta,
                quality_delta=quality_delta,
                verification_delta=verification_delta,
                consistency_delta=consistency_delta,
                success_label="improved",
                outcome_summary=f"{prefix} {index}",
                neuron_id=candidate.neuron_id,
                existing_registry=updated_registry,
            )
            updated_registry = updated_registry.register_evidence(evidence)

        return updated_registry

    def _build_launch_test_report(self):
        approved_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:launch_approved:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=tuple(f"ok-{index}" for index in range(1, 9)),
            failure_history=(),
            expected_gain=0.34,
            estimated_cost=0.05,
            estimated_latency=45.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        support_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:launch_support:model",
            activated_components=("primary", "memory"),
            activation_rule="compact_context_before_answer",
            routing_condition="compact_context_before_answer",
            intermediate_transform="compacta el contexto antes de responder",
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6", "ok-7"),
            failure_history=(),
            expected_gain=0.31,
            estimated_cost=0.06,
            estimated_latency=50.0,
            neuron_type=ROUTING_TYPE_TRANSFORMATION,
        )
        hold_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:launch_hold:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6"),
            failure_history=(),
            expected_gain=0.29,
            estimated_cost=0.07,
            estimated_latency=52.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        rejected_candidate = register_routing_neuron_candidate(
            task_signature="maintenance_routing:launch_rejected:model",
            activated_components=("memory", "maintenance"),
            activation_rule="summarize_recent_logs",
            routing_condition="observe_recent_context",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2"),
            failure_history=(),
            expected_gain=0.09,
            estimated_cost=0.12,
            estimated_latency=71.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(approved_candidate)
        self.assertIsNotNone(support_candidate)
        self.assertIsNotNone(hold_candidate)
        self.assertIsNotNone(rejected_candidate)

        registry = build_empty_routing_neuron_registry()
        for candidate in (
            replace(approved_candidate, neuron_state=ROUTING_STATE_ACTIVE),
            replace(support_candidate, neuron_state=ROUTING_STATE_ACTIVE),
            replace(hold_candidate, neuron_state=ROUTING_STATE_ACTIVE),
            replace(rejected_candidate, neuron_state=ROUTING_STATE_CANDIDATE),
        ):
            registry = registry.register_candidate(candidate)
        registry = replace(
            registry,
            active={
                approved_candidate.neuron_id: replace(approved_candidate, neuron_state=ROUTING_STATE_ACTIVE),
                support_candidate.neuron_id: replace(support_candidate, neuron_state=ROUTING_STATE_ACTIVE),
                hold_candidate.neuron_id: replace(hold_candidate, neuron_state=ROUTING_STATE_ACTIVE),
            },
        )

        registry = self._seed_improved_evidence(
            registry,
            approved_candidate,
            count=7,
            prefix="launch-approved",
            latency_ms=62.0,
            latency_delta=-20.0,
            cost_delta=-0.05,
            quality_delta=0.26,
            verification_delta=0.09,
            consistency_delta=0.06,
        )
        registry = self._seed_improved_evidence(
            registry,
            support_candidate,
            count=6,
            prefix="launch-support",
            latency_ms=60.0,
            latency_delta=-14.0,
            cost_delta=-0.03,
            quality_delta=0.23,
            verification_delta=0.07,
            consistency_delta=0.04,
        )
        registry = self._seed_improved_evidence(
            registry,
            hold_candidate,
            count=6,
            prefix="launch-hold",
            latency_ms=64.0,
            latency_delta=-15.0,
            cost_delta=-0.03,
            quality_delta=0.21,
            verification_delta=0.07,
            consistency_delta=0.05,
        )

        report = run_routing_maintenance(registry)
        return (
            report,
            report.registry.candidates[approved_candidate.neuron_id],
            report.registry.candidates[support_candidate.neuron_id],
            report.registry.candidates[hold_candidate.neuron_id],
            report.registry.candidates[rejected_candidate.neuron_id],
        )

    def _make_context(
        self,
        root: Path,
        query_text: str,
        *,
        memory: dict | None = None,
        model_available: bool = True,
        runtime_mode: str = "exec",
        runtime_output: str | None = None,
        runtime_script: str | None = None,
    ) -> CapabilityContext:
        model_path, llama_path = self._prepare_runtime(
            root,
            model_available=model_available,
            runtime_mode=runtime_mode,
            runtime_output=runtime_output,
            runtime_script=runtime_script,
        )
        memory_state = copy.deepcopy(memory or {})
        memory_state.setdefault("name", "")
        memory_state.setdefault("work", "")
        memory_state.setdefault("interests", [])
        memory_state.setdefault("preferences", [])
        tools_query = analyze_internal_tools_query(query_text)
        self.assertIsNotNone(tools_query)

        return CapabilityContext(
            user_input_raw=query_text,
            conversation=[],
            memory=memory_state,
            memory_file=str(root / "memory.json"),
            log_file=str(root / "session.json"),
            llama_path=llama_path,
            model_path=model_path,
            aura_version=AURA_VERSION,
            behavior_plan=BehaviorPlan(intent="tools_command"),
            route_action="internal_tools",
            tools_query=tools_query,
        )

    def _build_dual_provider_runtime_script(
        self,
        *,
        primary_output: str = "respuesta principal",
        critic_output: str = "VERIFICADA: sin conflicto claro.",
    ) -> str:
        return (
            "#!/bin/sh\n"
            "prompt=\"\"\n"
            "while [ \"$#\" -gt 0 ]; do\n"
            "  if [ \"$1\" = \"-p\" ]; then\n"
            "    prompt=\"$2\"\n"
            "    break\n"
            "  fi\n"
            "  shift\n"
            "done\n"
            "case \"$prompt\" in\n"
            f"  *\"Tarea del verificador:\"*|*\"Verificador:\"*) printf \"%s\\n\" \"{critic_output}\" ;;\n"
            f"  *) printf \"%s\\n\" \"{primary_output}\" ;;\n"
            "esac\n"
        )

    def test_catalog_queries_resolve_from_code(self) -> None:
        queries = (
            "que tools internas tienes",
            "que herramientas internas tienes",
            "que herramientas internas reales tienes",
        )

        for query in queries:
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                metadata = result.metadata
                self.assertEqual(metadata.intent, "tools_command")
                self.assertEqual(metadata.route, "internal_tools")
                self.assertFalse(metadata.used_model)
                self.assertEqual(metadata.capability, "internal_tools_catalog")
                self.assertEqual(metadata.action, "internal_tools_catalog")
                self.assertEqual(metadata.tool, "help_catalogs")
                self.assertEqual(metadata.tool_kind, "base")
                self.assertIn("herramientas internas", result.response)
                self.assertNotIn("composite_reviews", result.response)
                self.assertNotIn("composite_diagnostics", result.response)

    def test_readiness_and_diagnostic_queries_keep_internal_route(self) -> None:
        expected = {
            "estas lista para trabajar": (
                "internal_tools_work_readiness",
                "work_readiness_sequence",
            ),
            "que te falta para trabajar": (
                "internal_tools_readiness_gap",
                "readiness_gap_sequence",
            ),
            "que limitaciones tienes ahora": (
                "internal_tools_limitations_overview",
                "limitations_overview_sequence",
            ),
            "cual es tu estado actual": (
                "internal_tools_situational_status",
                "situational_status_sequence",
            ),
            "que es lo mas importante ahora": (
                "internal_tools_priority_now",
                "priority_now_sequence",
            ),
            "cual es tu principal limitacion": (
                "internal_tools_dominant_limitation",
                "dominant_limitation_sequence",
            ),
            "cual es tu principal fortaleza": (
                "internal_tools_dominant_strength",
                "dominant_strength_sequence",
            ),
        }

        for query, (expected_action, expected_sequence) in expected.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                metadata = result.metadata
                self.assertEqual(metadata.intent, "tools_command")
                self.assertEqual(metadata.route, "internal_tools")
                self.assertFalse(metadata.used_model)
                self.assertEqual(metadata.action, expected_action)
                self.assertEqual(metadata.sequence, expected_sequence)
                self.assertTrue(metadata.readiness_status)
                self.assertTrue(metadata.priority_focus)
                self.assertTrue(result.response)

    def test_strategic_queries_have_distinct_frames_and_text(self) -> None:
        expected_frames = {
            "que conviene hacer ahora": ADVICE_FRAME_FOCUS_NOW,
            "que me recomiendas hacer ahora": ADVICE_FRAME_EXPLAINED_NOW,
            "en que deberiamos enfocarnos": ADVICE_FRAME_PRIORITY_NOW,
            "si quiero avanzar ahora por donde empiezo": ADVICE_FRAME_ENTRY_STEP,
            "que es lo mas util ahora": ADVICE_FRAME_HIGHEST_VALUE,
            "como me puedes ayudar ahora mismo": ADVICE_FRAME_HELP_NOW,
            "que harias primero": ADVICE_FRAME_FIRST_MOVE,
            "que harias despues": ADVICE_FRAME_FOLLOWUP_MOVE,
            "si estuvieras limitada que harias primero": ADVICE_FRAME_RECOVERY_PLAY,
            "si estuvieras lista que aprovecharias": ADVICE_FRAME_EXPLOIT_PLAY,
        }

        responses: dict[str, str] = {}
        for query, expected_frame in expected_frames.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                metadata = result.metadata
                self.assertEqual(metadata.route, "internal_tools")
                self.assertFalse(metadata.used_model)
                self.assertEqual(metadata.advice_frame, expected_frame)
                self.assertTrue(metadata.recommended_order)
                self.assertTrue(metadata.next_move_chain)
                self.assertTrue(metadata.moment_profile)
                self.assertTrue(metadata.move_priority)
                self.assertEqual(metadata.move_count, len(metadata.next_move_chain))
                self.assertTrue(metadata.guidance_mode)
                self.assertTrue(metadata.micro_plan)
                self.assertTrue(metadata.now_step)
                self.assertTrue(metadata.plan_horizon)
                self.assertTrue(metadata.planning_mode)
                self.assertTrue(metadata.plan_confidence)
                responses[expected_frame] = result.response

        self.assertEqual(len(set(responses.values())), len(responses))
        self.assertEqual(
            self._run_turn("que conviene hacer ahora", memory={"name": "Ada"}).metadata.situational_profile,
            SITUATIONAL_PROFILE_EXPLOIT,
        )
        self.assertEqual(
            self._run_turn("que conviene hacer ahora", memory={"name": "Ada"}).metadata.moment_profile,
            MOMENT_PROFILE_EXPLOIT_NOW,
        )
        self.assertEqual(
            self._run_turn("si estuvieras limitada que harias primero", memory={"name": "Ada"}).metadata.situational_profile,
            SITUATIONAL_PROFILE_RECOVERY,
        )
        self.assertEqual(
            self._run_turn("si estuvieras limitada que harias primero", memory={"name": "Ada"}).metadata.moment_profile,
            MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY,
        )
        self.assertEqual(
            self._run_turn("si estuvieras lista que aprovecharias", memory={"name": "Ada"}).metadata.situational_profile,
            SITUATIONAL_PROFILE_EXPLOIT,
        )
        self.assertEqual(
            self._run_turn("que harias despues", memory={"name": "Ada"}).metadata.advice_frame,
            ADVICE_FRAME_FOLLOWUP_MOVE,
        )
        self.assertEqual(
            self._run_turn("que harias despues", memory={"name": "Ada"}).metadata.plan_horizon,
            "next",
        )

    def test_micro_plan_queries_resolve_from_code(self) -> None:
        expected_frames = {
            "que harias ahora": (ADVICE_FRAME_FIRST_MOVE, "now"),
            "que harias primero y despues": (ADVICE_FRAME_PAIRED_MOVES, "now_next"),
            "armame un plan corto": (ADVICE_FRAME_MICRO_PLAN, "now_next_later"),
            "cual seria un plan breve": (ADVICE_FRAME_MICRO_PLAN, "now_next_later"),
            "como conviene encarar esto": (ADVICE_FRAME_MICRO_PLAN, "now_next_later"),
            "cual seria tu mini plan": (ADVICE_FRAME_MICRO_PLAN, "now_next_later"),
            "si quiero avanzar ahora como lo harias": (ADVICE_FRAME_MICRO_PLAN, "now_next_later"),
            "ordename los siguientes pasos": (ADVICE_FRAME_MICRO_PLAN, "now_next_later"),
            "que harias ahora y que despues": (ADVICE_FRAME_PAIRED_MOVES, "now_next"),
            "que dejo para mas tarde": (ADVICE_FRAME_LATER_MOVE, "later"),
            "cual es tu secuencia recomendada": (ADVICE_FRAME_MICRO_PLAN, "now_next_later"),
        }

        responses: dict[str, str] = {}
        for query, (expected_frame, expected_horizon) in expected_frames.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                metadata = result.metadata
                self.assertEqual(metadata.intent, "tools_command")
                self.assertEqual(metadata.route, "internal_tools")
                self.assertFalse(metadata.used_model)
                self.assertEqual(metadata.advice_frame, expected_frame)
                self.assertEqual(metadata.plan_horizon, expected_horizon)
                self.assertTrue(metadata.micro_plan)
                self.assertTrue(metadata.now_step)
                self.assertTrue(metadata.planning_mode)
                self.assertTrue(metadata.sequence_depth)
                self.assertTrue(metadata.plan_confidence)
                self.assertTrue(metadata.followup_priority)
                if expected_horizon in {"now_next", "now_next_later", "next"}:
                    self.assertTrue(metadata.next_step)
                if expected_horizon == "now_next_later":
                    self.assertTrue(metadata.later_step)
                if expected_horizon == "later":
                    self.assertTrue(metadata.later_step)
                responses[f"{expected_frame}:{expected_horizon}"] = result.response

        self.assertEqual(len(set(responses.values())), len(responses))

    def test_feasibility_queries_resolve_from_code(self) -> None:
        expected_frames = {
            "esto es posible?": ADVICE_FRAME_FEASIBILITY,
            "ves alguna contradiccion?": ADVICE_FRAME_CONTRADICTION,
            "te parece realista?": ADVICE_FRAME_REALISM,
            "esto tiene algun limite importante?": ADVICE_FRAME_LIMITS,
        }

        for query, expected_frame in expected_frames.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                metadata = result.metadata
                self.assertEqual(metadata.intent, "feasibility_evaluation")
                self.assertEqual(metadata.route, "internal_tools")
                self.assertFalse(metadata.used_model)
                self.assertEqual(metadata.capability, "internal_tools_active")
                self.assertEqual(metadata.action, "internal_tools_feasibility")
                self.assertEqual(metadata.tool, "composite_reviews")
                self.assertEqual(metadata.sequence, SEQUENCE_FEASIBILITY_EVALUATION)
                self.assertEqual(metadata.advice_frame, expected_frame)
                self.assertTrue(metadata.feasibility_status)
                self.assertTrue(metadata.feasibility_reason)
                self.assertTrue(metadata.feasibility_scope)
                self.assertTrue(metadata.feasibility_frame)
                self.assertTrue(metadata.viability_basis)
                self.assertTrue(result.response)

    def test_feasibility_statements_mark_limits_or_contradictions(self) -> None:
        cases = {
            "quiero correr 7 modelos grandes a la vez en mi pc y que respondan instantaneo": FEASIBILITY_STATUS_NOT_FEASIBLE,
            "quiero que aura use cero recursos pero piense como un servidor enorme": FEASIBILITY_STATUS_CONTRADICTORY,
            "quiero que aura haga todo offline pero que sepa siempre lo ultimo que paso en internet": FEASIBILITY_STATUS_CONTRADICTORY,
            "quiero un sistema ultrarapido, gratis, local, sin hardware potente y con varios modelos grandes activos": FEASIBILITY_STATUS_CONTRADICTORY,
            "quiero que aura haga algo imposible pero sin decirme que no": FEASIBILITY_STATUS_CONTRADICTORY,
        }

        for query, expected_status in cases.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                metadata = result.metadata
                self.assertEqual(metadata.intent, "feasibility_evaluation")
                self.assertEqual(metadata.route, "internal_tools")
                self.assertFalse(metadata.used_model)
                self.assertEqual(metadata.capability, "internal_tools_active")
                self.assertEqual(metadata.action, "internal_tools_feasibility")
                self.assertEqual(metadata.tool, "composite_reviews")
                self.assertEqual(metadata.feasibility_status, expected_status)
                self.assertTrue(metadata.feasibility_reason)
                self.assertTrue(result.response)
                if expected_status == FEASIBILITY_STATUS_CONTRADICTORY:
                    self.assertTrue(metadata.contradiction_detected)

    def test_feasibility_possible_with_conditions_cases(self) -> None:
        queries = (
            "podemos hacer multimodelo mas adelante?",
            "esto seria viable con un modelo principal y otro verificador?",
            "podriamos hacer que aura use otro modelo solo cuando haga falta?",
            "seria posible si primero mejoramos la arquitectura?",
            "esto podria hacerse con mejores recursos?",
            "podriamos hacerlo en V0.36?",
            "esto seria viable si primero encapsulamos providers?",
        )

        for query in queries:
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                metadata = result.metadata
                self.assertEqual(metadata.intent, "feasibility_evaluation")
                self.assertEqual(metadata.route, "internal_tools")
                self.assertFalse(metadata.used_model)
                self.assertEqual(metadata.capability, "internal_tools_active")
                self.assertEqual(metadata.action, "internal_tools_feasibility")
                self.assertEqual(metadata.tool, "composite_reviews")
                self.assertEqual(
                    metadata.feasibility_status,
                    FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS,
                )
                self.assertTrue(metadata.conditions_required)
                self.assertTrue(result.response)

    def test_feasibility_uncertainty_cases(self) -> None:
        queries = (
            "esto seguro funcionaria?",
            "esto seria mejor que cualquier otra opcion?",
            "esto es la mejor arquitectura posible?",
            "esto garantiza que no falle nunca?",
            "esto resolveria todo de una vez?",
        )

        for query in queries:
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                metadata = result.metadata
                self.assertEqual(metadata.intent, "feasibility_evaluation")
                self.assertEqual(metadata.route, "internal_tools")
                self.assertFalse(metadata.used_model)
                self.assertEqual(metadata.capability, "internal_tools_active")
                self.assertEqual(metadata.action, "internal_tools_feasibility")
                self.assertEqual(metadata.tool, "composite_reviews")
                self.assertEqual(metadata.feasibility_status, FEASIBILITY_STATUS_UNCERTAIN)
                self.assertTrue(metadata.uncertainty_level)
                self.assertTrue(result.response)

    def test_feasibility_metadata_stays_trimmed(self) -> None:
        result = self._run_turn(
            "podemos hacer multimodelo mas adelante?",
            memory={"name": "Ada"},
        )
        metadata = result.metadata

        self.assertEqual(metadata.route, "internal_tools")
        self.assertEqual(metadata.intent, "feasibility_evaluation")
        self.assertEqual(metadata.sequence, SEQUENCE_FEASIBILITY_EVALUATION)
        self.assertEqual(metadata.feasibility_status, FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS)
        self.assertIsNone(metadata.recommended_focus)
        self.assertIsNone(metadata.recommended_action)
        self.assertIsNone(metadata.next_step_type)
        self.assertIsNone(metadata.actionability_level)
        self.assertIsNone(metadata.opportunity_focus)
        self.assertIsNone(metadata.next_move_chain)
        self.assertIsNone(metadata.micro_plan)
        self.assertIsNone(metadata.plan_horizon)
        self.assertTrue(metadata.confidence_level)
        self.assertTrue(metadata.consistency_status)

    def test_consistency_queries_resolve_from_code(self) -> None:
        expected_frames = {
            "que tan seguro estas?": ADVICE_FRAME_CONFIDENCE,
            "eso lo afirmarias asi nomas?": ADVICE_FRAME_ASSERTION,
            "esto depende de algo?": ADVICE_FRAME_DEPENDENCY,
            "hay suficiente base?": ADVICE_FRAME_EVIDENCE,
            "ves tension con lo anterior?": ADVICE_FRAME_CONTEXT_TENSION,
        }

        for query, expected_frame in expected_frames.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                metadata = result.metadata
                self.assertEqual(metadata.intent, "consistency_evaluation")
                self.assertEqual(metadata.route, "internal_tools")
                self.assertFalse(metadata.used_model)
                self.assertEqual(metadata.capability, "internal_tools_active")
                self.assertEqual(metadata.action, "internal_tools_consistency")
                self.assertEqual(metadata.tool, "composite_reviews")
                self.assertEqual(metadata.sequence, SEQUENCE_CONSISTENCY_EVALUATION)
                self.assertEqual(metadata.advice_frame, expected_frame)
                self.assertTrue(metadata.confidence_level)
                self.assertTrue(metadata.consistency_status)
                self.assertTrue(metadata.evidence_sufficiency)
                self.assertTrue(metadata.claim_strength)
                self.assertTrue(metadata.certainty_frame)
                self.assertTrue(metadata.judgment_mode)
                self.assertIsNone(metadata.recommended_focus)
                self.assertIsNone(metadata.recommended_action)
                self.assertIsNone(metadata.next_move_chain)
                self.assertIsNone(metadata.micro_plan)
                self.assertTrue(result.response)

    def test_consistency_after_conditional_feasibility(self) -> None:
        results = self._run_turn_sequence(
            [
                "podemos hacer multimodelo mas adelante?",
                "que tan seguro estas?",
                "eso lo afirmarias asi nomas?",
                "esto depende de algo?",
                "hay suficiente base?",
                "que necesitarias para estar mas seguro?",
            ],
            memory={"name": "Ada"},
        )

        first_metadata = results[0].metadata
        self.assertEqual(first_metadata.feasibility_status, FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS)

        confidence_metadata = results[1].metadata
        self.assertEqual(confidence_metadata.intent, "consistency_evaluation")
        self.assertEqual(confidence_metadata.consistency_status, CONSISTENCY_STATUS_CONDITIONAL)
        self.assertEqual(confidence_metadata.confidence_level, "medium")
        self.assertEqual(confidence_metadata.claim_strength, "conditional")
        self.assertTrue(confidence_metadata.required_evidence)
        self.assertIn("confianza", results[1].response.casefold())

        assertion_metadata = results[2].metadata
        self.assertEqual(assertion_metadata.advice_frame, ADVICE_FRAME_ASSERTION)
        self.assertEqual(assertion_metadata.consistency_status, CONSISTENCY_STATUS_CONDITIONAL)
        self.assertIn("afirmaría", results[2].response.casefold())

        dependency_metadata = results[3].metadata
        self.assertEqual(dependency_metadata.consistency_status, CONSISTENCY_STATUS_CONDITIONAL)
        self.assertTrue(dependency_metadata.required_evidence)
        self.assertIn("depende", results[3].response.casefold())

        evidence_metadata = results[4].metadata
        self.assertEqual(evidence_metadata.advice_frame, ADVICE_FRAME_EVIDENCE)
        self.assertIn("base", results[4].response.casefold())

        required_evidence_metadata = results[5].metadata
        self.assertTrue(required_evidence_metadata.required_evidence)
        self.assertIn("necesitar", results[5].response.casefold())

    def test_consistency_detects_recent_context_tension(self) -> None:
        results = self._run_turn_sequence(
            [
                "quiero que todo sea offline",
                "quiero que siempre sepa lo ultimo de internet",
                "ves tension con lo anterior?",
            ],
            memory={"name": "Ada"},
        )

        metadata = results[-1].metadata
        self.assertEqual(metadata.intent, "consistency_evaluation")
        self.assertEqual(metadata.route, "internal_tools")
        self.assertEqual(metadata.sequence, SEQUENCE_CONSISTENCY_EVALUATION)
        self.assertEqual(metadata.consistency_status, CONSISTENCY_STATUS_TENSION_DETECTED)
        self.assertTrue(metadata.recent_context_conflict)
        self.assertTrue(metadata.contextual_tension)
        self.assertIn("tensión", results[-1].response.casefold())

    def test_recent_requirement_tension_does_not_contaminate_unrelated_consistency(self) -> None:
        results = self._run_turn_sequence(
            [
                "quiero que todo sea offline",
                "quiero que siempre sepa lo ultimo de internet",
                "podemos hacer multimodelo mas adelante?",
                "que tan seguro estas?",
            ],
            memory={"name": "Ada"},
        )

        feasibility_metadata = results[2].metadata
        self.assertEqual(
            feasibility_metadata.feasibility_status,
            FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS,
        )

        consistency_metadata = results[3].metadata
        self.assertEqual(consistency_metadata.intent, "consistency_evaluation")
        self.assertEqual(consistency_metadata.consistency_status, CONSISTENCY_STATUS_CONDITIONAL)
        self.assertEqual(consistency_metadata.confidence_level, "medium")
        self.assertFalse(consistency_metadata.recent_context_conflict)
        self.assertFalse(bool(consistency_metadata.contextual_tension))
        self.assertIn("confianza", results[3].response.casefold())

    def test_consistency_marks_strong_conflict_when_judgment_is_firm(self) -> None:
        results = self._run_turn_sequence(
            [
                "quiero que aura haga todo offline pero que sepa siempre lo ultimo que paso en internet",
                "que tan seguro estas?",
                "eso lo afirmarias asi nomas?",
            ],
            memory={"name": "Ada"},
        )

        for result in results[1:]:
            metadata = result.metadata
            self.assertEqual(metadata.intent, "consistency_evaluation")
            self.assertEqual(metadata.consistency_status, CONSISTENCY_STATUS_CONFLICTED)
            self.assertEqual(metadata.confidence_level, "high")
            self.assertEqual(metadata.claim_strength, "firm")
            self.assertFalse(metadata.ambiguity_detected)

        self.assertIn("segura", results[1].response.casefold())
        self.assertIn("afirmaría", results[2].response.casefold())
        self.assertNotEqual(results[1].response, results[2].response)

    def test_contextual_general_turns_use_natural_microcopy(self) -> None:
        results = self._run_turn_sequence(
            [
                "quiero que todo sea offline",
                "quiero que siempre sepa lo ultimo de internet",
            ],
            memory={"name": "Ada"},
        )

        for result in results:
            self.assertFalse(result.metadata.used_model)
            self.assertEqual(result.metadata.route, ROUTE_HEURISTIC_RESPONSE)
            self.assertEqual(result.metadata.capability, CAPABILITY_HEURISTIC_RESPONSE)
            self.assertEqual(result.metadata.action, ACTION_HEURISTIC_RESPONSE)
            self.assertEqual(result.metadata.tool, TOOL_RESPONSE_HEURISTICS)
            self.assertEqual(result.metadata.tool_kind, "base")
            self.assertEqual(result.metadata.task_type, TASK_TYPE_NO_MODEL_NEEDED)
            self.assertEqual(result.metadata.routing_decision, "skip_model")
            self.assertEqual(result.metadata.no_model_reason, "behavior_direct_response")
            self.assertEqual(result.metadata.composition_mode, "heuristic_direct")
            self.assertEqual(result.metadata.provider_attempts, ())
            self.assertIn("route:heuristic_response", result.metadata.route_trace)
            self.assertIn(f"action:{ACTION_HEURISTIC_RESPONSE}", result.metadata.route_trace)
            self.assertIn(f"tool:{TOOL_RESPONSE_HEURISTICS}", result.metadata.route_trace)
            self.assertEqual(result.metadata.provider_trace, ("gateway:no_model",))
            self.assertNotEqual(result.metadata.route, ROUTE_MODEL)
            self.assertNotIn("modelo local no devolvió", result.response.casefold())
            self.assertNotIn("ultimo enfoque en linea", result.response.casefold())

        self.assertIn("offline", results[0].response.casefold())
        self.assertTrue(
            "sincronización" in results[1].response.casefold()
            or "sincronizacion" in results[1].response.casefold()
        )

    def test_direct_behavior_responses_do_not_fake_model_trace(self) -> None:
        results = self._run_turn_sequence(
            [
                "quiero que todo sea offline",
                "que es un prompt",
            ],
            memory={"name": "Ada"},
        )

        for result in results:
            with self.subTest(response=result.response):
                self.assertFalse(result.metadata.used_model)
                self.assertEqual(result.metadata.route, ROUTE_HEURISTIC_RESPONSE)
                self.assertEqual(result.metadata.capability, CAPABILITY_HEURISTIC_RESPONSE)
                self.assertEqual(result.metadata.action, ACTION_HEURISTIC_RESPONSE)
                self.assertEqual(result.metadata.tool, TOOL_RESPONSE_HEURISTICS)

    def test_task_classifier_distinguishes_no_model_and_provider_tasks(self) -> None:
        direct_task = classify_task(
            BehaviorPlan(
                intent="general",
                direct_response="respuesta directa",
            ),
            route_action=ROUTE_HEURISTIC_RESPONSE,
        )
        self.assertEqual(direct_task.task_type, TASK_TYPE_NO_MODEL_NEEDED)
        self.assertTrue(direct_task.no_model_needed)

        technical_task = classify_task(
            BehaviorPlan(intent="technical_explain"),
            route_action=ROUTE_MODEL,
        )
        self.assertEqual(technical_task.task_type, TASK_TYPE_TECHNICAL_REASONING)
        self.assertFalse(technical_task.no_model_needed)
        self.assertTrue(technical_task.critic_requested)
        self.assertEqual(technical_task.critic_role, ROLE_CRITIC)

        chat_task = classify_task(
            BehaviorPlan(intent="open"),
            route_action=ROUTE_MODEL,
        )
        self.assertEqual(chat_task.task_type, TASK_TYPE_CHAT_RESPONSE)
        self.assertFalse(chat_task.no_model_needed)
        self.assertFalse(chat_task.critic_requested)

    def test_task_classifier_gates_critic_by_real_technical_risk(self) -> None:
        simple_technical = classify_task(
            BehaviorPlan(intent="technical_explain"),
            route_action=ROUTE_MODEL,
            conversation=[{"role": "user", "content": "explicame una api"}],
        )
        risky_technical = classify_task(
            BehaviorPlan(intent="technical_explain"),
            route_action=ROUTE_MODEL,
            conversation=[
                {
                    "role": "user",
                    "content": "explicame una api con auth, rollback y riesgo en produccion",
                }
            ],
        )

        self.assertFalse(simple_technical.critic_requested)
        self.assertEqual(simple_technical.risk_profile, "low")
        self.assertTrue(risky_technical.critic_requested)
        self.assertEqual(risky_technical.risk_profile, "medium")

    def test_behavior_keeps_explanatory_auth_prompts_out_of_troubleshoot(self) -> None:
        self.assertEqual(
            classify_user_intent("como funciona oauth en una api"),
            "technical_explain",
        )
        self.assertEqual(
            classify_user_intent("explicame una api con auth, rollback y riesgo en produccion"),
            "technical_explain",
        )
        self.assertEqual(
            classify_user_intent("me falla auth con 401 y rollback roto en staging, que reviso?"),
            "technical_troubleshoot",
        )

    def test_model_registry_and_gateway_wrap_primary_and_critic_providers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output="Idea breve: usa auth estable y rollback probado antes de producción.",
                critic_output="VERIFICADA: sin conflicto claro.",
                router_output="foco breve: responde directo y practico",
                qwen_output="Idea breve: si entras en fallback, mantén una ruta segura y verifica auth antes del deploy.",
            )
            registry = build_default_model_registry(
                stack["llama"],
                stack["primary"],
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )
            primary_provider = registry.get_provider_for_role(ROLE_PRIMARY)
            critic_provider = registry.get_provider_for_role(ROLE_CRITIC)
            router_provider = registry.get_provider_for_role(ROLE_MICRO_EXPERT_ROUTER)
            fallback_provider = registry.get_fallback_provider()

            self.assertIsNotNone(primary_provider)
            self.assertEqual(primary_provider.descriptor.provider_id, LOCAL_PRIMARY_PROVIDER_ID)
            self.assertIn(ROLE_PRIMARY, primary_provider.descriptor.roles_supported)

            self.assertIsNotNone(critic_provider)
            self.assertEqual(critic_provider.descriptor.provider_id, LOCAL_CRITIC_PROVIDER_ID)
            self.assertIn(ROLE_CRITIC, critic_provider.descriptor.roles_supported)
            self.assertEqual(critic_provider.descriptor.runtime_path, stack["llama"])
            self.assertEqual(critic_provider.descriptor.model_path, stack["critic"])

            self.assertIsNotNone(router_provider)
            self.assertEqual(router_provider.descriptor.provider_id, LOCAL_ROUTER_PROVIDER_ID)
            self.assertIn(ROLE_MICRO_EXPERT_ROUTER, router_provider.descriptor.roles_supported)

            self.assertIsNotNone(fallback_provider)
            self.assertEqual(
                fallback_provider.descriptor.provider_id,
                LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
            )
            self.assertIn(ROLE_PRIMARY, fallback_provider.descriptor.roles_supported)

            task = classify_task(BehaviorPlan(intent="open"), route_action=ROUTE_MODEL)
            critic_plan = plan_critic(task.task_type)
            routing = decide_routing(task, registry, critic_plan)
            self.assertEqual(routing.selected_provider, LOCAL_PRIMARY_PROVIDER_ID)
            self.assertTrue(routing.provider_available)
            self.assertFalse(routing.critic_requested)

            gateway_result = invoke_model_gateway(
                prompt="AURA: responde",
                routing_decision=routing,
                registry=registry,
            )
            self.assertEqual(gateway_result.provider_result_status, PROVIDER_RESULT_SUCCESS)
            self.assertEqual(gateway_result.provider_response, "usa auth estable y rollback probado antes de producción.")

    def test_model_registry_formalizes_transitional_and_allowlist_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output=(
                    "Una API expone recursos por HTTP y define contratos claros de entrada y salida."
                ),
                critic_output="VERIFICADA: sin conflicto claro.",
            )
            registry = build_default_model_registry(
                stack["llama"],
                stack["primary"],
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )
            active_primary = registry.get_active_policy_for_role(ROLE_PRIMARY)
            active_critic = registry.get_active_policy_for_role(ROLE_CRITIC)
            active_router = registry.get_active_policy_for_role(ROLE_MICRO_EXPERT_ROUTER)
            fallback_policy = registry.get_transitional_fallback_policy()
            allowlist = registry.list_allowlisted_candidates()

            self.assertIsNotNone(active_primary)
            self.assertEqual(active_primary.policy_status, MODEL_POLICY_ACTIVE_GREEN)
            self.assertEqual(active_primary.provider_id, LOCAL_PRIMARY_PROVIDER_ID)
            self.assertEqual(active_primary.runtime_backend, RUNTIME_BACKEND_LLAMA_CPP)
            self.assertEqual(active_primary.artifact_format, ARTIFACT_FORMAT_GGUF)
            self.assertEqual(active_primary.family, "granite")

            self.assertIsNotNone(active_critic)
            self.assertEqual(active_critic.policy_status, MODEL_POLICY_ACTIVE_GREEN)
            self.assertEqual(active_critic.provider_id, LOCAL_CRITIC_PROVIDER_ID)
            self.assertEqual(active_critic.family, "olmo2")

            self.assertIsNotNone(active_router)
            self.assertEqual(active_router.policy_status, MODEL_POLICY_ACTIVE_GREEN)
            self.assertEqual(active_router.provider_id, LOCAL_ROUTER_PROVIDER_ID)
            self.assertEqual(active_router.role, ROLE_MICRO_EXPERT_ROUTER)

            self.assertIsNotNone(fallback_policy)
            self.assertEqual(
                fallback_policy.policy_status,
                MODEL_POLICY_TRANSITIONAL_FALLBACK,
            )
            self.assertEqual(
                fallback_policy.provider_id,
                LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
            )

            allowlist_by_model = {entry.model_id: entry for entry in allowlist}
            self.assertIn("SmolLM2-360M-Instruct", allowlist_by_model)
            self.assertIn("Granite 3.0 1B-A400M-Instruct", allowlist_by_model)
            self.assertIn("OLMo-2-0425-1B-Instruct", allowlist_by_model)
            self.assertEqual(
                allowlist_by_model["SmolLM2-360M-Instruct"].role,
                ROLE_MICRO_EXPERT_ROUTER,
            )
            self.assertEqual(
                allowlist_by_model["Granite 3.0 1B-A400M-Instruct"].role,
                ROLE_PRIMARY,
            )
            self.assertEqual(
                allowlist_by_model["OLMo-2-0425-1B-Instruct"].role,
                ROLE_CRITIC,
            )
            self.assertTrue(
                all(entry.policy_status == MODEL_POLICY_ALLOWLIST for entry in allowlist)
            )
            self.assertTrue(all(entry.commercial_ok for entry in allowlist))
            self.assertTrue(all(entry.modifiable_ok for entry in allowlist))

    def test_model_registry_separates_production_candidate_and_lab_tracks_from_bank(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output=(
                    "Una API expone recursos por HTTP y define contratos claros de entrada y salida."
                ),
                critic_output="VERIFICADA: sin conflicto claro.",
            )
            for extra_model_name in (
                "gemma-3-1b-it-q4_k_m.gguf",
                "Phi-4-mini-instruct-GGUF-Q3_K_M.gguf",
                "DeepSeek-R1-Distill-Qwen-1.5B-Q3_K_M.gguf",
                "googlegemma-4-E2B-model.safetensors",
                "ai21labs_AI21-Jamba-Reasoning-3B-Q8_0.gguf",
                "350m_test.gguf",
            ):
                (root / extra_model_name).write_text("model", encoding="utf-8")

            registry = build_default_model_registry(
                stack["llama"],
                stack["primary"],
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            production_ids = {entry.model_id for entry in registry.list_production_stack()}
            candidate_ids = {entry.model_id for entry in registry.list_candidate_benchmarks()}
            lab_ids = {entry.model_id for entry in registry.list_lab_models()}

            self.assertIn("Granite 3.0 1B-A400M-Instruct", production_ids)
            self.assertIn("OLMo-2-0425-1B-Instruct", production_ids)
            self.assertIn("SmolLM2-360M-Instruct", production_ids)
            self.assertIn("Qwen2-1.5B-Instruct", production_ids)

            self.assertIn("Gemma 3 1B Instruct", candidate_ids)
            self.assertIn("Phi-4 Mini Instruct", candidate_ids)
            self.assertIn("DeepSeek R1 Distill Qwen 1.5B", candidate_ids)

            self.assertIn("Gemma 4 E2B", lab_ids)
            self.assertIn("AI21 Jamba Reasoning 3B", lab_ids)
            self.assertIn("350m_test", lab_ids)

    def test_model_registry_stack_health_distinguishes_healthy_degraded_partial_and_missing_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            healthy_stack = self._prepare_multistack_runtime(root / "healthy")
            healthy_registry = build_default_model_registry(
                healthy_stack["llama"],
                healthy_stack["primary"],
                critic_llama_path=healthy_stack["llama"],
                critic_model_path=healthy_stack["critic"],
                router_llama_path=healthy_stack["llama"],
                router_model_path=healthy_stack["router"],
                fallback_llama_path=healthy_stack["llama"],
                fallback_model_path=healthy_stack["fallback"],
            )
            healthy_snapshot = build_stack_health_snapshot(healthy_registry)
            self.assertEqual(healthy_snapshot.health, STACK_HEALTH_HEALTHY)
            self.assertFalse(healthy_snapshot.partial_stack)

            degraded_stack = self._prepare_multistack_runtime(
                root / "degraded",
                missing_models=("router",),
            )
            degraded_registry = build_default_model_registry(
                degraded_stack["llama"],
                degraded_stack["primary"],
                critic_llama_path=degraded_stack["llama"],
                critic_model_path=degraded_stack["critic"],
                router_llama_path=degraded_stack["llama"],
                router_model_path=degraded_stack["router"],
                fallback_llama_path=degraded_stack["llama"],
                fallback_model_path=degraded_stack["fallback"],
            )
            degraded_snapshot = build_stack_health_snapshot(degraded_registry)
            self.assertEqual(degraded_snapshot.health, STACK_HEALTH_DEGRADED)
            self.assertIn(ROLE_MICRO_EXPERT_ROUTER, degraded_snapshot.missing_roles)

            partial_stack = self._prepare_multistack_runtime(
                root / "partial",
                missing_models=("critic", "router"),
            )
            partial_registry = build_default_model_registry(
                partial_stack["llama"],
                partial_stack["primary"],
                critic_llama_path=partial_stack["llama"],
                critic_model_path=partial_stack["critic"],
                router_llama_path=partial_stack["llama"],
                router_model_path=partial_stack["router"],
                fallback_llama_path=partial_stack["llama"],
                fallback_model_path=partial_stack["fallback"],
            )
            partial_snapshot = build_stack_health_snapshot(partial_registry)
            self.assertEqual(partial_snapshot.health, STACK_HEALTH_PARTIAL_STACK)
            self.assertTrue(partial_snapshot.partial_stack)

            missing_primary_stack = self._prepare_multistack_runtime(
                root / "missing_primary",
                missing_models=("primary",),
            )
            missing_primary_registry = build_default_model_registry(
                missing_primary_stack["llama"],
                missing_primary_stack["primary"],
                critic_llama_path=missing_primary_stack["llama"],
                critic_model_path=missing_primary_stack["critic"],
                router_llama_path=missing_primary_stack["llama"],
                router_model_path=missing_primary_stack["router"],
                fallback_llama_path=missing_primary_stack["llama"],
                fallback_model_path=missing_primary_stack["fallback"],
            )
            missing_primary_snapshot = build_stack_health_snapshot(missing_primary_registry)
            self.assertEqual(missing_primary_snapshot.health, STACK_HEALTH_MISSING_MODELS)
            self.assertEqual(missing_primary_snapshot.fallback_pressure, "high")

    def test_model_registry_can_discover_sibling_model_when_configured_path_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output=(
                    "Una API expone recursos por HTTP y define contratos claros de entrada y salida."
                ),
                critic_output="VERIFICADA: sin conflicto claro.",
            )
            stale_primary_path = root / "granite-stale-path.gguf"
            registry = build_default_model_registry(
                stack["llama"],
                str(stale_primary_path),
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            primary_descriptor = registry.get_provider_for_role(ROLE_PRIMARY).descriptor
            self.assertTrue(primary_descriptor.availability)
            self.assertEqual(primary_descriptor.model_path, stack["primary"])

    def test_benchmark_harness_builds_targets_for_active_and_allowlist_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
            )
            registry = build_default_model_registry(
                stack["llama"],
                stack["primary"],
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )
            targets = build_benchmark_targets(registry)
            target_ids = {target.model_id for target in targets}

            self.assertIn("Granite 3.0 1B-A400M-Instruct", target_ids)
            self.assertIn("Qwen2-1.5B-Instruct", target_ids)
            self.assertIn("SmolLM2-360M-Instruct", target_ids)
            self.assertIn("Granite 3.0 1B-A400M-Instruct", target_ids)
            self.assertIn("OLMo-2-0425-1B-Instruct", target_ids)

            snapshot = BenchmarkSnapshot(
                model_id="SmolLM2-360M-Instruct",
                latency_ms=120.0,
                memory_mb=900.0,
                stability_score=0.82,
                conversational_quality=0.7,
                consistency_score=0.76,
                critic_utility=0.65,
                micro_expert_utility=0.81,
            )
            assessment = assess_benchmark_snapshot(snapshot)
            self.assertTrue(assessment.stable_enough)
            self.assertTrue(assessment.mini_pc_ready)
            self.assertFalse(assessment.critic_ready)
            self.assertTrue(assessment.micro_expert_ready)

    def test_model_bank_governance_snapshot_marks_ready_blocked_and_active_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output=(
                    "Una API expone recursos por HTTP y define contratos claros de entrada y salida."
                ),
                critic_output="VERIFICADA: sin conflicto claro.",
            )
            for extra_model_name in (
                "gemma-3-1b-it-q4_k_m.gguf",
                "Phi-4-mini-instruct-GGUF-Q3_K_M.gguf",
                "DeepSeek-R1-Distill-Qwen-1.5B-Q3_K_M.gguf",
                "googlegemma-4-E2B-model.safetensors",
            ):
                (root / extra_model_name).write_text("model", encoding="utf-8")

            registry = build_default_model_registry(
                stack["llama"],
                stack["primary"],
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            governance = build_model_bank_governance_snapshot(registry)
            preparation = build_benchmark_preparation_snapshot(registry)

            self.assertIn("Granite 3.0 1B-A400M-Instruct", preparation.active_core)
            self.assertIn("Gemma 3 1B Instruct", preparation.ready_now)
            self.assertIn("Phi-4 Mini Instruct", preparation.ready_now)
            self.assertIn("Gemma 4 E2B", preparation.blocked)
            self.assertIn("Gemma 4 E2B", governance.blocked_ids)
            self.assertGreaterEqual(governance.production_count, 4)
            self.assertGreaterEqual(governance.candidate_count, 3)

    def test_codex_control_registry_can_create_update_and_refresh_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "routing_neuron" / "control" / "codex_control_registry.json"
            ensure_codex_control_registry(registry_path)

            update_codex_control_registry(
                {
                    "run_id": "codex-v03931",
                    "version_target": "0.39.3.1",
                    "work_type": "visible_stability",
                    "requested_scope": "stabilizacion visible basica",
                    "summary": "base visible estable",
                    "files_modified": ["agents/system_state_agent.py"],
                    "tests_run": ["python -m unittest discover -s tests -v"],
                    "tests_result": {"status": "ok", "summary": "124/124 OK"},
                    "smokes_run": ["que estado tienes", "hola"],
                    "smokes_result": {"status": "ok", "summary": "2 rondas limpias"},
                    "checkpoint_short": "system_state y saludos estabilizados",
                    "status": "completed",
                    "next_recommended_step": "cerrar capa tecnica visible",
                },
                path=registry_path,
            )
            update_codex_control_registry(
                {
                    "run_id": "codex-v0394",
                    "version_target": "0.39.6",
                    "work_type": "consolidation",
                    "requested_scope": "rn v1.3 y registro canonico enriquecido",
                    "summary": "registro de Codex integrado en RN con memoria administrativa mas util para estabilizacion y trabajo real",
                    "files_modified": [
                        "agents/system_state_agent.py",
                        "backend/app/routing_neuron/control/registry.py",
                    ],
                    "files_created": [
                        "backend/app/routing_neuron/control/codex_control_registry.json",
                    ],
                    "modules_touched": [
                        "agents.system_state_agent",
                        "backend.app.routing_neuron.control.registry",
                    ],
                    "contracts_affected": [
                        "codex_control_registry_schema",
                        "routing_neuron_admin_state",
                    ],
                    "tests_run": [
                        "python -m compileall agents providers backend tests aura.py config.py main.py model_runner.py memory_store.py",
                        "python -m unittest discover -s tests -v",
                    ],
                    "tests_result": {"status": "ok", "summary": "suite verde"},
                    "smokes_run": ["checkpoint routing neuron", "ultimo trabajo de codex"],
                    "smokes_result": {"status": "ok", "summary": "estado visible coherente"},
                    "tests_passed_count": 129,
                    "tests_failed_count": 0,
                    "runtime_quality_observed": "rescate honesto y registry mas rico",
                    "model_failures_observed": "long tail tecnico abierto sigue bajo observacion",
                    "fallback_patterns": ["fallback_manager_quality_rescue", "transitional_fallback"],
                    "degradation_patterns": ["quality_guard_rescued_by_fallback_manager", "transitional_fallback_active"],
                    "critic_patterns": ["critic_non_visible_feedback"],
                    "router_patterns": ["router_helper_sparse"],
                    "long_tail_failures": ["prompt tecnico abierto cuando cae al modelo"],
                    "production_models": ["Granite 3.0 1B-A400M-Instruct", "OLMo-2-0425-1B-Instruct"],
                    "candidate_models": ["Gemma 3 1B Instruct", "Phi-4 Mini Instruct"],
                    "lab_models": ["Gemma 4 E2B"],
                    "benchmark_readiness": "ready_for_candidates_without_auto_promotion",
                    "blocked_models": ["Gemma 4 E2B"],
                    "promotion_candidates": ["Gemma 3 1B Instruct", "Phi-4 Mini Instruct"],
                    "do_not_promote_notes": ["no mover el core sin benchmark serio"],
                    "rn_operational_state": "administrative_memory_active",
                    "rn_signal_state": "low_signal_no_signal_dominant",
                    "rn_recent_outcomes": ["checkpoint_richer", "state_reads_registry"],
                    "rn_applied_count": 0,
                    "rn_blocked_count": 0,
                    "rn_no_signal_count": 3,
                    "aura_changes": ["estado visible enriquecido", "cli no interactiva mas limpia"],
                    "rn_changes": ["control registry canonico", "checkpoint rn v1.3"],
                    "model_bank_changes": ["gobierno benchmark listo"],
                    "checkpoint_short": "AURA V0.39.6 y RN V1.3 consolidados",
                    "checkpoint_long": "AURA V0.39.6 y RN V1.3 consolidados con control registry enriquecido, memoria administrativa mas util y riesgo visible mas honesto.",
                    "known_good": "registro util como fuente unica de revision",
                    "known_weakness": "long tail tecnico abierto",
                    "review_artifacts_needed": ["codex_control_registry.json"],
                    "open_debts": ["long tail tecnico abierto"],
                    "status": "completed",
                    "next_recommended_step": "benchmark serio sobre candidatos inmediatos",
                },
                path=registry_path,
            )

            registry = load_codex_control_registry(registry_path)
            status = build_codex_control_status(registry_path)

            self.assertEqual(len(registry["entries"]), 2)
            self.assertEqual(registry["schema_version"], "codex_control_registry.v1.3")
            self.assertEqual(registry["latest_version"], "0.39.6")
            self.assertEqual(registry["latest_status"], "completed")
            self.assertEqual(registry["latest_runtime_health"], "watch")
            self.assertEqual(registry["latest_risk"], "medium")
            self.assertEqual(status.latest_run_id, "codex-v0394")
            self.assertEqual(status.latest_version, "0.39.6")
            self.assertEqual(status.latest_tests_status, "ok")
            self.assertEqual(status.latest_smokes_status, "ok")
            self.assertIn("agents.system_state_agent", status.latest_modules_touched)
            self.assertIn("codex_control_registry_schema", status.latest_contracts_affected)
            self.assertEqual(status.latest_known_weakness, "long tail tecnico abierto")
            self.assertIn("long tail tecnico abierto", status.latest_open_debts)
            self.assertIn("fallback_manager_quality_rescue", status.latest_fallback_patterns)
            self.assertIn("quality_guard_rescued_by_fallback_manager", status.latest_degradation_patterns)
            self.assertIn("checkpoint_richer", status.latest_rn_recent_outcomes)
            self.assertIn("Granite 3.0 1B-A400M-Instruct", status.latest_production_models)
            self.assertIn("no mover el core sin benchmark serio", status.latest_do_not_promote_notes)

    def test_model_registry_registers_v039_core_and_fallback_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(root)
            registry = build_default_model_registry(
                stack["llama"],
                stack["primary"],
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertEqual(
                registry.get_provider_for_role(ROLE_PRIMARY).descriptor.model_id,
                "Granite 3.0 1B-A400M-Instruct",
            )
            self.assertEqual(
                registry.get_provider_for_role(ROLE_CRITIC).descriptor.model_id,
                "OLMo-2-0425-1B-Instruct",
            )
            self.assertEqual(
                registry.get_provider_for_role(ROLE_MICRO_EXPERT_ROUTER).descriptor.model_id,
                "SmolLM2-360M-Instruct",
            )
            self.assertEqual(
                registry.get_fallback_provider().descriptor.model_id,
                "Qwen2-1.5B-Instruct",
            )

    def test_router_helper_uses_smollm2_without_becoming_primary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                router_output="foco breve: responde corto y practico",
            )
            execution = execute_model_response(
                conversation=[{"role": "user", "content": "hola aura"}],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="open"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertTrue(execution.used_model)
            self.assertEqual(execution.selected_provider, LOCAL_PRIMARY_PROVIDER_ID)
            self.assertEqual(execution.selected_role, ROLE_PRIMARY)
            self.assertFalse(execution.fallback_used)
            self.assertIn("router:selected:local_router", execution.provider_trace)
            self.assertIn("router:helper_applied", execution.provider_trace)
            self.assertIn("primary:selected:local_primary", execution.provider_trace)

    def test_router_helper_unavailable_falls_back_to_primary_without_breaking(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                missing_models=("router",),
            )
            execution = execute_model_response(
                conversation=[{"role": "user", "content": "hola aura"}],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="open"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertTrue(execution.used_model)
            self.assertEqual(execution.selected_provider, LOCAL_PRIMARY_PROVIDER_ID)
            self.assertFalse(execution.fallback_used)
            self.assertIn("router:selected:local_router", execution.provider_trace)
            self.assertIn("router:status:unavailable", execution.provider_trace)
            self.assertIn("primary:selected:local_primary", execution.provider_trace)

    def test_core_multimodel_cutover_is_not_blocked_by_empty_launch_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(root)
            execution = execute_model_response(
                conversation=[
                    {
                        "role": "user",
                        "content": "explicame una api con auth, rollback y riesgo en produccion",
                    }
                ],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            dossier_result = self._run_turn(
                "muestra el launch dossier",
                memory={"name": "Ada"},
                routing_registry=build_empty_routing_neuron_registry(),
                runtime_script=self._build_multistack_runtime_script(),
            )

            self.assertTrue(execution.used_model)
            self.assertEqual(execution.selected_provider, LOCAL_PRIMARY_PROVIDER_ID)
            self.assertIn(
                "actualmente sin neuronas finalistas",
                dossier_result.response,
            )
            self.assertIn(
                "no bloquea por sí solo el cutover del stack core",
                dossier_result.response,
            )

    def test_routing_neuron_v0_requires_repetition_gain_and_cost_control(self) -> None:
        rejected = register_routing_neuron_candidate(
            task_signature="explain_api+critic",
            activated_components=("primary", "critic"),
            activation_rule="technical_reasoning_and_post_check",
            routing_condition="technical_reasoning",
            intermediate_transform="compact_primary_summary",
            success_history=("ok-1",),
            failure_history=(),
            expected_gain=0.18,
            estimated_cost=0.3,
            estimated_latency=120.0,
        )
        self.assertIsNone(rejected)

        candidate = register_routing_neuron_candidate(
            task_signature="explain_api+critic",
            activated_components=("primary", "critic"),
            activation_rule="technical_reasoning_and_post_check",
            routing_condition="technical_reasoning",
            intermediate_transform="compact_primary_summary",
            success_history=("ok-1", "ok-2"),
            failure_history=(),
            expected_gain=0.18,
            estimated_cost=0.3,
            estimated_latency=120.0,
        )
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.promotion_stage, PROMOTION_STAGE_SPECIALIZED_PROMPT)
        self.assertEqual(candidate.activation_frequency, 2)
        self.assertGreater(candidate.promotion_score, 0.0)
        self.assertEqual(candidate.activated_components, ("primary", "critic"))

        promoted = promote_routing_neuron(candidate)
        self.assertEqual(promoted.promotion_stage, PROMOTION_STAGE_ADAPTER)
        self.assertEqual(
            PROMOTION_STAGES,
            (
                "specialized_prompt",
                "adapter",
                "lora",
                "distillation",
                "micro_model",
            ),
        )

    def test_routing_neuron_observed_patterns_do_not_birth_from_single_signal(self) -> None:
        registry = build_empty_routing_neuron_registry()
        registry, evidence, pattern, candidate = ingest_routing_observation(
            registry,
            task_signature="technical_reasoning:explain:model",
            session_id="session-a",
            task_profile="technical_reasoning",
            risk_profile="low",
            budget_profile="balanced",
            baseline_route="primary_then_critic",
            recent_route="primary_then_critic",
            evaluated_route="primary_only",
            activated_components=("primary", "critic"),
            latency_ms=120.0,
            latency_delta=-45.0,
            cost_delta=-0.18,
            quality_delta=0.04,
            verification_delta=0.03,
            consistency_delta=0.01,
            success_label="improved",
            outcome_summary="ahorro de critic sin pérdida visible",
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
        )
        self.assertEqual(pattern.state, ROUTING_STATE_OBSERVED_PATTERN)
        self.assertEqual(pattern.neuron_type, ROUTING_TYPE_CONTROL)
        self.assertEqual(pattern.activation_frequency, 1)
        self.assertEqual(evidence.observed_pattern_id, pattern.pattern_id)
        self.assertIsNone(candidate)

        registry, _, pattern, candidate = ingest_routing_observation(
            registry,
            task_signature="technical_reasoning:explain:model",
            session_id="session-a",
            task_profile="technical_reasoning",
            risk_profile="low",
            budget_profile="balanced",
            baseline_route="primary_then_critic",
            recent_route="primary_then_critic",
            evaluated_route="primary_only",
            activated_components=("primary", "critic"),
            latency_ms=110.0,
            latency_delta=-48.0,
            cost_delta=-0.2,
            quality_delta=0.05,
            verification_delta=0.04,
            consistency_delta=0.02,
            success_label="improved",
            outcome_summary="segunda mejora consistente",
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
        )
        self.assertEqual(pattern.activation_frequency, 2)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.neuron_state, ROUTING_STATE_CANDIDATE)
        self.assertEqual(candidate.neuron_type, ROUTING_TYPE_CONTROL)
        self.assertGreater(candidate.global_routing_score, 0.0)

    def test_routing_runtime_can_apply_active_neuron_without_polluting_provider_trace(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.2,
            estimated_cost=0.25,
            estimated_latency=90.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(candidate)
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        registry = registry.activate_candidate(candidate.neuron_id)
        set_default_routing_registry(registry)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output="Idea breve: usa auth estable y rollback probado antes de producción.",
                critic_output="VERIFICADA: sin conflicto claro.",
            )
            execution = execute_model_response(
                conversation=[
                    {
                        "role": "user",
                        "content": "explicame una api con auth, rollback y riesgo en produccion",
                    }
                ],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
                session_id="session-runtime",
            )

        self.assertTrue(execution.used_model)
        self.assertEqual(execution.routing_decision, "primary_only")
        self.assertEqual(execution.composition_mode, COMPOSITION_MODE_PROVIDER_PRIMARY)
        self.assertFalse(execution.critic_requested)
        self.assertFalse(execution.critic_used)
        self.assertTrue(execution.routing_neuron_applied)
        self.assertEqual(execution.routing_neuron_decision, ROUTING_RUNTIME_APPLIED)
        self.assertEqual(execution.routing_neuron_id, candidate.neuron_id)
        self.assertEqual(execution.routing_neuron_state, ROUTING_STATE_ACTIVE)
        self.assertEqual(execution.routing_neuron_type, ROUTING_TYPE_CONTROL)
        self.assertEqual(execution.routing_neuron_influence, "skip_critic")
        self.assertEqual(execution.routing_neuron_decision_path, ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED)
        self.assertTrue(execution.routing_neuron_considered)
        self.assertEqual(execution.routing_neuron_considered_ids, (candidate.neuron_id,))
        self.assertTrue(execution.routing_neuron_selected)
        self.assertTrue(execution.routing_neuron_barriers_checked)
        self.assertEqual(execution.routing_neuron_barriers_blocked, ())
        self.assertEqual(execution.routing_neuron_outcome_label, "improved")
        self.assertIn("routing_neuron:selected", " ".join(execution.routing_neuron_trace))
        self.assertNotIn("routing_neuron", " ".join(execution.provider_trace))

        runtime_registry = get_default_routing_registry()
        self.assertTrue(runtime_registry.observed_patterns)
        self.assertTrue(runtime_registry.evidence_records)
        self.assertTrue(runtime_registry.runtime_records)
        self.assertEqual(runtime_registry.runtime_records[-1].decision, ROUTING_RUNTIME_APPLIED)
        self.assertEqual(runtime_registry.runtime_records[-1].outcome_label, "improved")
        self.assertEqual(runtime_registry.runtime_records[-1].decision_path, ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED)

    def test_routing_runtime_keeps_candidate_as_non_influential_signal_until_active(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.2,
            estimated_cost=0.25,
            estimated_latency=90.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(candidate)
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        routing = decide_routing(
            classify_task(BehaviorPlan(intent="technical_explain"), route_action=ROUTE_MODEL),
            build_default_model_registry("runner", "model.gguf"),
            plan_critic(TASK_TYPE_TECHNICAL_REASONING),
        )

        runtime_decision = apply_routing_runtime(
            routing,
            task_signature="technical_reasoning:technical_explain:model",
            task_type="technical_reasoning",
            route_action=ROUTE_MODEL,
            risk_profile="low",
            budget_profile="tight",
            registry=registry,
        )

        self.assertFalse(runtime_decision.applied)
        self.assertEqual(runtime_decision.decision, ROUTING_RUNTIME_NO_SIGNAL)
        self.assertTrue(runtime_decision.considered)
        self.assertEqual(runtime_decision.considered_ids, (candidate.neuron_id,))
        self.assertFalse(runtime_decision.selected)
        self.assertIn("state", runtime_decision.barriers_blocked)
        self.assertEqual(runtime_decision.fallback_reason, "no_active_match")
        self.assertEqual(runtime_decision.decision_path, ROUTING_RUNTIME_PATH_CANDIDATE_SEEN_NO_ACTIVE)

    def test_routing_runtime_without_candidates_still_leaves_a_runtime_signal(self) -> None:
        routing = decide_routing(
            classify_task(BehaviorPlan(intent="technical_explain"), route_action=ROUTE_MODEL),
            build_default_model_registry("runner", "model.gguf"),
            plan_critic(TASK_TYPE_TECHNICAL_REASONING),
        )

        runtime_decision = apply_routing_runtime(
            routing,
            task_signature="technical_reasoning:technical_explain:model",
            task_type="technical_reasoning",
            route_action=ROUTE_MODEL,
            risk_profile="low",
            budget_profile="balanced",
            registry=build_empty_routing_neuron_registry(),
        )

        self.assertFalse(runtime_decision.applied)
        self.assertEqual(runtime_decision.decision, ROUTING_RUNTIME_NO_SIGNAL)
        self.assertTrue(runtime_decision.considered)
        self.assertEqual(runtime_decision.considered_ids, ())
        self.assertFalse(runtime_decision.selected)
        self.assertEqual(runtime_decision.fallback_reason, "no_match")
        self.assertIn("routing_neuron:no_candidate_match", runtime_decision.trace)
        self.assertEqual(runtime_decision.decision_path, ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH)

    def test_routing_runtime_resolves_simple_conflict_and_keeps_baseline_on_barrier(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(root)
            fast_candidate = register_routing_neuron_candidate(
                task_signature="technical_reasoning:technical_explain:model",
                activated_components=("primary", "critic"),
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
                success_history=("ok-1", "ok-2", "ok-3"),
                failure_history=(),
                expected_gain=0.22,
                estimated_cost=0.2,
                estimated_latency=80.0,
                neuron_type=ROUTING_TYPE_CONTROL,
            )
            transform_candidate = register_routing_neuron_candidate(
                task_signature="technical_reasoning:technical_explain:model",
                activated_components=("primary", "critic"),
                activation_rule="compact_before_primary",
                routing_condition="technical_reasoning low",
                intermediate_transform="compacta el contexto antes de responder",
                success_history=("ok-1", "ok-2"),
                failure_history=(),
                expected_gain=0.12,
                estimated_cost=0.15,
                estimated_latency=50.0,
                neuron_type=ROUTING_TYPE_TRANSFORMATION,
            )
            self.assertIsNotNone(fast_candidate)
            self.assertIsNotNone(transform_candidate)
            registry = build_empty_routing_neuron_registry()
            registry = registry.register_candidate(fast_candidate)
            registry = registry.register_candidate(transform_candidate)
            registry = registry.activate_candidate(fast_candidate.neuron_id)
            registry = registry.activate_candidate(transform_candidate.neuron_id)

            routing = decide_routing(
                classify_task(BehaviorPlan(intent="technical_explain"), route_action=ROUTE_MODEL),
                build_default_model_registry(
                    stack["llama"],
                    stack["primary"],
                    critic_llama_path=stack["llama"],
                    critic_model_path=stack["critic"],
                    router_llama_path=stack["llama"],
                    router_model_path=stack["router"],
                    fallback_llama_path=stack["llama"],
                    fallback_model_path=stack["fallback"],
                ),
                plan_critic(TASK_TYPE_TECHNICAL_REASONING),
            )
            runtime_decision = apply_routing_runtime(
                routing,
                task_signature="technical_reasoning:technical_explain:model",
                task_type="technical_reasoning",
                route_action=ROUTE_MODEL,
                risk_profile="low",
                budget_profile="balanced",
                registry=registry,
            )
            self.assertTrue(runtime_decision.applied)
            self.assertEqual(runtime_decision.decision, ROUTING_RUNTIME_APPLIED)
            self.assertEqual(runtime_decision.influence, "skip_critic")
            self.assertTrue(runtime_decision.considered)
            self.assertTrue(runtime_decision.selected)
            self.assertTrue(runtime_decision.conflict)
            self.assertEqual(
                runtime_decision.conflict_resolution,
                "highest_global_score_then_activation_frequency_then_efficiency",
            )

            expensive_candidate = register_routing_neuron_candidate(
                task_signature="technical_reasoning:technical_explain:model",
                activated_components=("primary", "critic"),
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
                success_history=("ok-1", "ok-2", "ok-3"),
                failure_history=(),
                expected_gain=0.18,
                estimated_cost=0.9,
                estimated_latency=80.0,
                neuron_type=ROUTING_TYPE_SELECTION,
            )
            self.assertIsNotNone(expensive_candidate)
            blocked_registry = build_empty_routing_neuron_registry().register_candidate(expensive_candidate)
            blocked_registry = blocked_registry.activate_candidate(expensive_candidate.neuron_id)
            blocked = apply_routing_runtime(
                routing,
                task_signature="technical_reasoning:technical_explain:model",
                task_type="technical_reasoning",
                route_action=ROUTE_MODEL,
                risk_profile="low",
                budget_profile="tight",
                registry=blocked_registry,
            )
            self.assertFalse(blocked.applied)
            self.assertEqual(blocked.decision, ROUTING_RUNTIME_BLOCKED)
            self.assertTrue(blocked.considered)
            self.assertTrue(blocked.selected)
            self.assertIn("budget", blocked.barriers_blocked)
            self.assertEqual(blocked.fallback_reason, f"{expensive_candidate.neuron_id}:budget_barrier")
            self.assertEqual(blocked.decision_path, ROUTING_RUNTIME_PATH_SELECTED_BLOCKED)
        self.assertIn("routing_neuron:decision:blocked", blocked.trace)
        self.assertIn(
            f"routing_neuron:barrier:{expensive_candidate.neuron_id}:budget_barrier",
            blocked.trace,
        )

    def test_routing_maintenance_builds_session_summary_and_promotes_active_recommendations(self) -> None:
        registry = build_empty_routing_neuron_registry()
        for index in range(3):
            registry, _, _, _ = ingest_routing_observation(
                registry,
                task_signature="technical_reasoning:technical_explain:model",
                session_id="session-rn",
                task_profile="technical_reasoning",
                risk_profile="low",
                budget_profile="balanced",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route="primary_only",
                activated_components=("primary", "critic"),
                latency_ms=100.0 - index,
                latency_delta=-40.0,
                cost_delta=-0.15,
                quality_delta=0.04,
                verification_delta=0.03,
                consistency_delta=0.02,
                success_label="improved",
                outcome_summary=f"iteracion {index}",
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
            )

        report = run_routing_maintenance(registry)
        self.assertTrue(report.updated_sessions)
        self.assertTrue(report.recommendation_ids)
        snapshot = build_routing_repertoire_snapshot(report.registry)
        self.assertTrue(snapshot.observed_patterns)
        self.assertTrue(snapshot.candidate_ids)
        self.assertTrue(snapshot.active_ids)
        self.assertFalse(snapshot.paused_ids)
        self.assertTrue(snapshot.recommendation_ids)
        self.assertTrue(report.registry.session_summaries["session-rn"].compared_routes)
        self.assertTrue(report.registry.session_summaries["session-rn"].applied_neurons)
        active_neuron = report.registry.active[snapshot.active_ids[0]]
        self.assertEqual(active_neuron.neuron_state, ROUTING_STATE_ACTIVE)
        self.assertIn(
            active_neuron.stability_label,
            {"stable", "observing", "improving"},
        )

    def test_routing_maintenance_session_summary_keeps_runtime_decisions_barriers_and_fallbacks(self) -> None:
        registry = build_empty_routing_neuron_registry()
        for index in range(2):
            registry, _, _, _ = ingest_routing_observation(
                registry,
                task_signature="technical_reasoning:technical_explain:model",
                session_id="session-runtime-rich",
                task_profile="technical_reasoning",
                risk_profile="low",
                budget_profile="tight",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route="primary_only",
                activated_components=("primary",),
                latency_ms=80.0,
                latency_delta=-20.0,
                cost_delta=-0.1,
                quality_delta=0.01,
                verification_delta=0.0,
                consistency_delta=0.0,
                success_label="baseline_kept",
                outcome_summary=f"iteracion bloqueada {index}",
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
                routing_neuron_considered=True,
                considered_neuron_ids=("rn:test-blocked",),
                routing_neuron_selected=True,
                routing_neuron_decision=ROUTING_RUNTIME_BLOCKED,
                routing_neuron_influence=None,
                routing_neuron_barriers_checked=("state", "budget", "context"),
                routing_neuron_barriers_blocked=("budget",),
                routing_neuron_conflict=None,
                routing_neuron_conflict_resolution=None,
                routing_neuron_fallback_reason="rn:test-blocked:budget_barrier",
                routing_neuron_outcome_label="baseline_kept",
            )

        report = run_routing_maintenance(registry)
        summary = report.registry.session_summaries["session-runtime-rich"]

        self.assertIn("rn:test-blocked", summary.considered_neurons)
        self.assertIn("budget", summary.blocked_barriers)
        self.assertIn(ROUTING_RUNTIME_BLOCKED, summary.runtime_decisions)
        self.assertIn("rn:test-blocked:budget_barrier", summary.fallback_reasons)
        self.assertEqual(summary.total_runtime_decisions, 0)

    def test_routing_runtime_respects_paused_neurons(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=("fail-1",),
            expected_gain=0.19,
            estimated_cost=0.22,
            estimated_latency=95.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(candidate)
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        registry = registry.activate_candidate(candidate.neuron_id)
        registry = registry.pause_candidate(candidate.neuron_id, "manual_pause_for_review")
        routing = decide_routing(
            classify_task(BehaviorPlan(intent="technical_explain"), route_action=ROUTE_MODEL),
            build_default_model_registry("runner", "model.gguf"),
            plan_critic(TASK_TYPE_TECHNICAL_REASONING),
        )
        runtime_decision = apply_routing_runtime(
            routing,
            task_signature="technical_reasoning:technical_explain:model",
            task_type="technical_reasoning",
            route_action=ROUTE_MODEL,
            risk_profile="low",
            budget_profile="balanced",
            registry=registry,
        )
        self.assertFalse(runtime_decision.applied)
        self.assertEqual(runtime_decision.decision, ROUTING_RUNTIME_PAUSED)
        self.assertEqual(runtime_decision.neuron_state, ROUTING_STATE_PAUSED)
        self.assertEqual(runtime_decision.fallback_reason, "manual_pause_for_review")
        self.assertTrue(runtime_decision.considered)
        self.assertTrue(runtime_decision.selected)
        self.assertIn("state", runtime_decision.barriers_blocked)
        self.assertIn("routing_neuron:decision:paused", runtime_decision.trace)

    def test_routing_runtime_respects_cooldown_and_decrements_it(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.2,
            estimated_cost=0.22,
            estimated_latency=80.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(candidate)
        cooled = build_empty_routing_neuron_registry().register_candidate(candidate)
        cooled = cooled.activate_candidate(candidate.neuron_id)
        cooled = cooled.set_candidate_cooldown(candidate.neuron_id, 2, "cooldown_guard")
        routing = decide_routing(
            classify_task(BehaviorPlan(intent="technical_explain"), route_action=ROUTE_MODEL),
            build_default_model_registry("runner", "model.gguf"),
            plan_critic(TASK_TYPE_TECHNICAL_REASONING),
        )
        runtime_decision = apply_routing_runtime(
            routing,
            task_signature="technical_reasoning:technical_explain:model",
            task_type="technical_reasoning",
            route_action=ROUTE_MODEL,
            risk_profile="low",
            budget_profile="balanced",
            registry=cooled,
        )
        self.assertFalse(runtime_decision.applied)
        self.assertEqual(runtime_decision.decision, ROUTING_RUNTIME_COOLDOWN)
        self.assertEqual(runtime_decision.fallback_reason, "cooldown_active")
        self.assertIsNotNone(runtime_decision.registry_snapshot)
        cooled_candidate = runtime_decision.registry_snapshot.candidates[candidate.neuron_id]
        self.assertEqual(cooled_candidate.cooldown_turns_remaining, 1)
        self.assertTrue(runtime_decision.considered)
        self.assertTrue(runtime_decision.selected)
        self.assertIn("cooldown", runtime_decision.barriers_blocked)
        self.assertIn("routing_neuron:decision:cooldown", runtime_decision.trace)

    def test_routing_runtime_can_keep_baseline_as_suggested_only_without_touching_provider_trace(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="observe_without_override",
            routing_condition="technical_reasoning low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.15,
            estimated_cost=0.2,
            estimated_latency=70.0,
            neuron_type=ROUTING_TYPE_SELECTION,
        )
        self.assertIsNotNone(candidate)
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        registry = registry.activate_candidate(candidate.neuron_id)
        set_default_routing_registry(registry)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output=(
                    "Una API expone recursos por HTTP y define contratos claros de entrada y salida."
                ),
                critic_output="VERIFICADA: sin conflicto claro.",
            )
            execution = execute_model_response(
                conversation=[{"role": "user", "content": "explicame una api"}],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
                session_id="session-suggested-only",
            )

        self.assertFalse(execution.routing_neuron_applied)
        self.assertEqual(execution.routing_neuron_decision, ROUTING_RUNTIME_SUGGESTED_ONLY)
        self.assertEqual(execution.routing_neuron_decision_path, ROUTING_RUNTIME_PATH_SELECTED_NOT_APPLIED)
        self.assertTrue(execution.routing_neuron_considered)
        self.assertTrue(execution.routing_neuron_selected)
        self.assertEqual(execution.routing_neuron_barriers_blocked, ())
        self.assertEqual(execution.routing_neuron_fallback_reason, "no_runtime_effect")
        self.assertEqual(execution.routing_neuron_outcome_label, "baseline_kept")
        self.assertIn("routing_neuron:selected", " ".join(execution.routing_neuron_trace))
        self.assertNotIn("routing_neuron", " ".join(execution.provider_trace))

    def test_routing_runtime_blocked_execution_keeps_provider_trace_clean_and_updates_admin_runtime_status(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.18,
            estimated_cost=0.9,
            estimated_latency=80.0,
            neuron_type=ROUTING_TYPE_SELECTION,
        )
        self.assertIsNotNone(candidate)
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        registry = registry.activate_candidate(candidate.neuron_id)
        set_default_routing_registry(registry)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(root)
            execution = execute_model_response(
                conversation=[{"role": "user", "content": "explicame una api"}],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
                session_id="session-budget-blocked",
            )

        self.assertFalse(execution.routing_neuron_applied)
        self.assertEqual(execution.routing_neuron_decision, ROUTING_RUNTIME_BLOCKED)
        self.assertEqual(execution.routing_neuron_decision_path, ROUTING_RUNTIME_PATH_SELECTED_BLOCKED)
        self.assertIn("budget", execution.routing_neuron_barriers_blocked)
        self.assertNotIn("routing_neuron", " ".join(execution.provider_trace))

        runtime_registry = get_default_routing_registry()
        snapshot = build_routing_repertoire_snapshot(runtime_registry)
        self.assertGreaterEqual(snapshot.runtime_record_count, 1)
        self.assertGreaterEqual(snapshot.runtime_blocked_count, 1)
        self.assertGreaterEqual(snapshot.runtime_fallback_count, 1)
        self.assertIn(candidate.neuron_id, snapshot.runtime_blocked_ids)
        self.assertTrue(snapshot.runtime_barrier_hotspots)
        self.assertTrue(snapshot.runtime_recent_outcomes)

    def test_execute_model_response_degraded_mode_refreshes_runtime_history_and_session_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            model_path, llama_path = self._prepare_runtime(
                root,
                model_available=False,
            )
            execution = execute_model_response(
                conversation=[{"role": "user", "content": "hola"}],
                memory={"name": "Ada"},
                llama_path=llama_path,
                model_path=model_path,
                behavior_plan=BehaviorPlan(intent="general"),
                route_action=ROUTE_MODEL,
                session_id="session-degraded-live",
            )

        self.assertFalse(execution.used_model)
        self.assertEqual(execution.routing_neuron_decision, ROUTING_RUNTIME_NO_SIGNAL)
        self.assertTrue(execution.routing_neuron_considered)
        self.assertEqual(execution.routing_neuron_fallback_reason, "no_match")
        self.assertEqual(execution.routing_neuron_decision_path, ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH)
        self.assertNotIn("routing_neuron", " ".join(execution.provider_trace))

        runtime_registry = get_default_routing_registry()
        self.assertTrue(runtime_registry.runtime_records)
        self.assertIn(
            runtime_registry.runtime_records[-1].outcome_label,
            {"fallback_no_provider", "fallback_runtime_error"},
        )
        self.assertTrue(runtime_registry.runtime_records[-1].outcome_summary)
        summary = runtime_registry.session_summaries["session-degraded-live"]
        self.assertEqual(summary.total_runtime_decisions, 1)
        self.assertEqual(summary.no_signal_runtime_decisions, 1)
        self.assertEqual(summary.fallback_runtime_decisions, 1)
        self.assertEqual(summary.degraded_runtime_decisions, 1)
        self.assertEqual(summary.runtime_presence_status, "only_no_signal_seen")
        self.assertEqual(summary.runtime_validation_status, "baseline_only_validation")
        self.assertTrue(summary.recent_runtime_outcomes)
        self.assertIn("no_match x1", summary.frequent_runtime_fallbacks)
        self.assertEqual(summary.selected_not_applied_runtime_decisions, 0)

    def test_routing_maintenance_detects_overuse_and_sets_cooldown(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.1,
            estimated_cost=0.22,
            estimated_latency=90.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(candidate)
        candidate = replace(candidate, times_applied=4)
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        registry = registry.activate_candidate(candidate.neuron_id)
        report = run_routing_maintenance(registry)
        self.assertTrue(report.cooldown_candidates)
        cooled = report.registry.candidates[candidate.neuron_id]
        self.assertGreaterEqual(cooled.cooldown_turns_remaining, 2)
        self.assertIn("overuse_detected", cooled.alerts)
        self.assertIn(f"{candidate.neuron_id}:cooldown", report.alerts)
        self.assertEqual(cooled.stability_label, ROUTING_STABILITY_DEGRADING)
        self.assertFalse(cooled.promotion_ready_signal)

    def test_routing_maintenance_enriches_confidence_and_repertoire_snapshot(self) -> None:
        registry = build_empty_routing_neuron_registry()
        for index in range(6):
            registry, _, _, _ = ingest_routing_observation(
                registry,
                task_signature="technical_reasoning:technical_explain:model",
                session_id="session-history",
                task_profile="technical_reasoning",
                risk_profile="low",
                budget_profile="balanced",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route="primary_only",
                activated_components=("primary", "critic"),
                latency_ms=90.0 - index,
                latency_delta=-35.0,
                cost_delta=-0.12,
                quality_delta=0.05,
                verification_delta=0.03,
                consistency_delta=0.02,
                success_label="improved" if index < 5 else "stable_success",
                outcome_summary=f"historia {index}",
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
            )

        report = run_routing_maintenance(registry)
        snapshot = build_routing_repertoire_snapshot(report.registry)
        self.assertTrue(snapshot.entries)
        top_entry = snapshot.entries[0]
        self.assertIsInstance(top_entry, RoutingRepertoireEntry)
        self.assertIn(
            top_entry.confidence_tier,
            {
                ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
                ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            },
        )
        self.assertIn(
            top_entry.stability_label,
            {
                ROUTING_STABILITY_STABLE,
                ROUTING_STABILITY_IMPROVING,
            },
        )
        self.assertIn(top_entry.trend_label, {"steady", "up"})
        self.assertIn(top_entry.readiness_band, {ROUTING_READINESS_EMERGING, ROUTING_READINESS_NEAR_READY})
        self.assertGreaterEqual(top_entry.successful_activations, 4)
        self.assertGreaterEqual(top_entry.stable_activation_streak, 1)
        self.assertTrue(snapshot.recent_activity)
        self.assertTrue(snapshot.top_score_ids)
        self.assertTrue(snapshot.top_confidence_ids)
        self.assertTrue(snapshot.top_stability_ids)
        self.assertTrue(snapshot.readiness_ids)
        summary = report.registry.session_summaries["session-history"]
        self.assertTrue(summary.useful_neurons)
        self.assertTrue(summary.promotion_ready_neurons or report.recommendation_ids)
        self.assertTrue(report.promotion_ready_candidates or report.recommendation_ids)
        self.assertIn("baseline mejor", summary.gains_summary)

    def test_execute_model_response_can_use_primary_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(root)
            execution = execute_model_response(
                conversation=[{"role": "user", "content": "hola aura"}],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="open"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertTrue(execution.used_model)
            self.assertEqual(execution.selected_provider, LOCAL_PRIMARY_PROVIDER_ID)
            self.assertEqual(execution.selected_role, ROLE_PRIMARY)
            self.assertEqual(execution.provider_result_status, PROVIDER_RESULT_SUCCESS)
            self.assertEqual(execution.routing_decision, "primary_only")
            self.assertEqual(execution.gateway_mode, "router_helper+primary_only")
            self.assertEqual(execution.composition_mode, COMPOSITION_MODE_PROVIDER_PRIMARY)
            self.assertFalse(execution.fallback_used)
            self.assertFalse(execution.critic_requested)
            self.assertFalse(execution.critic_used)
            self.assertFalse(execution.routing_neuron_applied)
            self.assertEqual(execution.routing_neuron_decision, ROUTING_RUNTIME_NO_SIGNAL)
            self.assertIn("routing_neuron:decision:no_signal", execution.routing_neuron_trace)
            self.assertTrue(execution.provider_trace)
            self.assertIn("router:selected:local_router", execution.provider_trace)
            self.assertIn("primary:selected:local_primary", execution.provider_trace)
            self.assertIn("router:helper_applied", execution.provider_trace)

    def test_execute_model_response_can_use_primary_then_critic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output="Idea breve: usa auth estable y rollback probado antes de producción.",
                critic_output="VERIFICADA: sin conflicto claro.",
            )
            execution = execute_model_response(
                conversation=[
                    {
                        "role": "user",
                        "content": "explicame una api con auth, rollback y riesgo en produccion",
                    }
                ],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertTrue(execution.used_model)
            self.assertEqual(execution.selected_provider, LOCAL_PRIMARY_PROVIDER_ID)
            self.assertEqual(execution.selected_role, ROLE_PRIMARY)
            self.assertEqual(execution.critic_provider, LOCAL_CRITIC_PROVIDER_ID)
            self.assertTrue(execution.critic_requested)
            self.assertTrue(execution.critic_used)
            self.assertTrue(execution.critic_available)
            self.assertEqual(execution.critic_result_status, PROVIDER_RESULT_SUCCESS)
            self.assertEqual(execution.routing_decision, "primary_then_critic")
            self.assertEqual(execution.gateway_mode, "primary_then_critic")
            self.assertEqual(
                execution.composition_mode,
                COMPOSITION_MODE_PROVIDER_PRIMARY_WITH_CRITIC,
            )
            self.assertEqual(execution.verification_outcome, VERIFICATION_OUTCOME_VERIFIED)
            self.assertNotIn("verificacion breve", execution.response.casefold())
            self.assertNotIn("verificada", execution.response.casefold())
            self.assertNotIn("ajuste", execution.response.casefold())
            self.assertNotIn("dudosa", execution.response.casefold())
            self.assertFalse(execution.routing_neuron_applied)
            self.assertEqual(execution.routing_neuron_decision, ROUTING_RUNTIME_NO_SIGNAL)
            self.assertIn("routing_neuron:decision:no_signal", execution.routing_neuron_trace)
            self.assertIn("primary:selected:local_primary", execution.provider_trace)
            self.assertIn("critic:selected:local_critic", execution.provider_trace)
            self.assertNotIn("router:selected:local_router", execution.provider_trace)

    def test_v0393_simple_technical_explain_can_stay_primary_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output=(
                    "Una API expone recursos por HTTP y define contratos claros de entrada y salida."
                ),
                critic_output="VERIFICADA: sin conflicto claro.",
            )
            execution = execute_model_response(
                conversation=[{"role": "user", "content": "explicame una api"}],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertTrue(execution.used_model)
            self.assertEqual(execution.selected_provider, LOCAL_PRIMARY_PROVIDER_ID)
            self.assertEqual(execution.routing_decision, "primary_only")
            self.assertFalse(execution.critic_requested)
            self.assertFalse(execution.critic_used)
            self.assertEqual(execution.composition_mode, COMPOSITION_MODE_PROVIDER_PRIMARY)
            self.assertFalse(execution.fallback_used)

    def test_v0393_router_helper_is_sparse_for_longer_open_turns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(root)
            execution = execute_model_response(
                conversation=[
                    {
                        "role": "user",
                        "content": "quiero ordenar tres opciones para mejorar un flujo de trabajo con varios tradeoffs y prioridades",
                    }
                ],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="open"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertTrue(execution.used_model)
            self.assertEqual(execution.routing_decision, "primary_only")
            self.assertEqual(execution.gateway_mode, "primary_only")
            self.assertNotIn("router:selected:local_router", execution.provider_trace)

    def test_model_fallback_records_gateway_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                missing_models=("primary",),
                qwen_output=(
                    "Una API con auth y rollback en produccion necesita autenticacion estable, "
                    "operaciones trazables y un plan de reversion probado antes del deploy."
                ),
            )
            execution = execute_model_response(
                conversation=[
                    {
                        "role": "user",
                        "content": "como funciona una api con auth y rollback en produccion",
                    }
                ],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertTrue(execution.used_model)
            self.assertEqual(
                execution.selected_provider,
                LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
            )
            self.assertTrue(execution.fallback_used)
            self.assertIn("transitional_fallback", execution.gateway_mode)
            self.assertEqual(execution.provider_result_status, PROVIDER_RESULT_SUCCESS)
            self.assertTrue(execution.fallback_reason)
            self.assertTrue(execution.fallback_reason.startswith("transitional_fallback:"))
            self.assertIn("primary:selected:local_primary", execution.provider_trace)
            self.assertIn("fallback:selected:local_transitional_fallback", execution.provider_trace)
            self.assertIn("fallback:used:transitional", execution.provider_trace)
            self.assertIn("fallback:reason:transitional_fallback:", " ".join(execution.provider_trace))
            self.assertEqual(
                execution.composition_mode,
                COMPOSITION_MODE_PROVIDER_PRIMARY_WITH_CRITIC,
            )

    def test_model_runner_strips_leading_inline_prompt_instructions(self) -> None:
        raw_output = (
            "- resumir en una sola l?nea el foco?til para responder - responde con una sola "
            "l?nea breve - no expliques de m?s Resume en una sola l?nea el foco?til para "
            "responder. L?nea de foco: Respondes siempre en espa?ol. ¡Hola! ¿En qué puedo "
            "ayudarte hoy?\n"
        )

        cleaned = _extract_response(raw_output)

        self.assertEqual(cleaned, "¡Hola! ¿En qué puedo ayudarte hoy?")

    def test_model_runner_strips_visible_scaffold_labels(self) -> None:
        raw_output = (
            "Idea breve: JWT es un token firmado. "
            "Explicacion clara: no cifra por si solo. "
            "Pasos o ejemplo: revisa expiracion y firma."
        )

        cleaned = _extract_response(raw_output)

        self.assertIn("jwt es un token firmado", cleaned.casefold())
        self.assertIn("no cifra por si solo", cleaned.casefold())
        self.assertIn("revisa expiracion y firma", cleaned.casefold())
        self.assertNotIn("idea breve", cleaned.casefold())
        self.assertNotIn("explicacion clara", cleaned.casefold())
        self.assertNotIn("pasos o ejemplo", cleaned.casefold())

    def test_prepare_turn_uses_heuristic_route_for_minimal_conversational_health_prompts(self) -> None:
        expectations = {
            "hola": "Hola.",
            "buen dia": "Buen dia.",
            "que tal": "Todo bien.",
            "gracias": "De nada.",
        }

        for query, expected_response in expectations.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                self.assertEqual(result.metadata.route, ROUTE_HEURISTIC_RESPONSE)
                self.assertFalse(result.metadata.used_model)
                self.assertEqual(result.response, expected_response)
                self.assertNotIn("respondes siempre", result.response.casefold())
                self.assertNotIn("linea de foco", result.response.casefold())

    def test_prepare_turn_uses_direct_stable_responses_for_visible_technical_smokes(self) -> None:
        expectations = {
            "que es una API REST": "api rest",
            "que es JWT": "jwt",
            "que es OAuth2": "oauth2",
            "auth vs autorizacion": "autorizacion",
            "diferencia entre auth y autorizacion": "autorizacion",
            "que significa idempotencia": "mismo efecto final",
            "que es rollback en produccion": "rollback",
            "que es una API stateless": "stateless",
            "explicame una api con auth y rollback en produccion": "rollback",
        }

        for query, expected_marker in expectations.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                self.assertEqual(result.metadata.route, ROUTE_HEURISTIC_RESPONSE)
                self.assertFalse(result.metadata.used_model)
                self.assertIn(expected_marker, result.response.casefold())
                self.assertNotIn("respondes siempre", result.response.casefold())
                self.assertNotIn("linea de foco", result.response.casefold())
                self.assertNotIn("plan interno", result.response.casefold())
                self.assertNotIn("idea breve", result.response.casefold())
                self.assertNotIn("explicacion clara", result.response.casefold())
                self.assertNotIn("verificacion breve", result.response.casefold())

    def test_prepare_turn_covers_long_tail_backend_families_without_model(self) -> None:
        expectations = {
            "explicame arquitectura backend con integraciones externas": "integraciones",
            "que significa manejar estados en backend": "transiciones",
            "explicame una api backend con servicios": "contrato",
            "explicame tradeoffs entre cache write-through y write-back en una api con auth": "write-through",
            "que tradeoffs tiene latencia p95 vs p99 en una API": "p95",
            "como balancearias cache, auth y colas en una API con mucho trafico": "colas",
            "como priorizarias versionado, compatibilidad y rollout en una API con clientes externos": "compatibilidad",
            "como disenar un backend multi-tenant con limites por cliente y observabilidad util": "tenant",
            "como migrarias un backend monolitico a servicios sin romper auth ni contratos": "monolito",
        }

        for query, expected_marker in expectations.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"}, model_available=False)
                self.assertEqual(result.metadata.route, ROUTE_HEURISTIC_RESPONSE)
                self.assertFalse(result.metadata.used_model)
                self.assertIn(expected_marker, result.response.casefold())
                self.assertNotIn("respondes siempre", result.response.casefold())
                self.assertNotIn("plan interno", result.response.casefold())
                self.assertNotIn("verificacion breve", result.response.casefold())

    def test_runtime_quality_detects_low_topic_coverage_for_open_technical_prompt(self) -> None:
        assessment = assess_runtime_quality(
            "JWT es un token firmado para transportar identidad.",
            task_type="technical_reasoning",
            fallback_available=True,
            source_text="como balancearias cache, auth y colas en una API con mucho trafico",
        )

        self.assertEqual(assessment.status, QUALITY_STATUS_OFF_TOPIC)
        self.assertEqual(assessment.issue, "off_topic_output")
        self.assertTrue(assessment.retry_with_fallback)

    def test_runtime_quality_detects_low_decision_density_for_action_oriented_prompt(self) -> None:
        assessment = assess_runtime_quality(
            "Auth, contratos y servicios importan en esa migracion.",
            task_type="technical_reasoning",
            fallback_available=True,
            source_text="como migrarias un backend monolitico a servicios sin romper auth ni contratos",
        )

        self.assertEqual(assessment.status, QUALITY_STATUS_PLACEHOLDER)
        self.assertEqual(assessment.issue, "placeholder_output")
        self.assertEqual(assessment.degradation_hint, "runtime_low_decision_density")
        self.assertTrue(assessment.retry_with_fallback)

    def test_runtime_quality_detects_prompt_leak_with_inline_control_bullets(self) -> None:
        assessment = assess_runtime_quality(
            (
                "- responde sin saludo ni pre?mbulo - si es t?cnico, da una idea concreta "
                "temprano - evita respuestas vac?as Resume en una sola l?nea el foco. "
                "Respondes siempre en espa?ol. OAuth sirve para delegar autenticación."
            ),
            task_type="technical_reasoning",
            fallback_available=True,
            source_text="explicame oauth con auth y rollback en produccion",
        )

        self.assertEqual(assessment.status, QUALITY_STATUS_PLACEHOLDER)
        self.assertEqual(assessment.issue, "prompt_leak_output")
        self.assertTrue(assessment.retry_with_fallback)

    def test_runtime_quality_detects_prompt_leak_from_internal_prompt_scaffolding(self) -> None:
        assessment = assess_runtime_quality(
            (
                "Plan interno de respuesta: responde breve. "
                "Formato objetivo para esta respuesta: idea breve, explicacion clara. "
                "OAuth sirve para delegar autenticacion."
            ),
            task_type="technical_reasoning",
            fallback_available=True,
            source_text="explicame oauth con auth y rollback en produccion",
        )

        self.assertEqual(assessment.status, QUALITY_STATUS_PLACEHOLDER)
        self.assertEqual(assessment.issue, "prompt_leak_output")
        self.assertTrue(assessment.retry_with_fallback)

    def test_runtime_quality_detects_critic_leak_output(self) -> None:
        assessment = assess_runtime_quality(
            "AJUSTE: falta precision. Verificacion breve: el texto no responde JWT.",
            task_type="technical_reasoning",
            fallback_available=True,
            source_text="que es JWT",
        )

        self.assertEqual(assessment.status, QUALITY_STATUS_PLACEHOLDER)
        self.assertEqual(assessment.issue, "critic_leak_output")
        self.assertTrue(assessment.retry_with_fallback)

    def test_runtime_quality_detects_ceremonial_short_technical_output(self) -> None:
        assessment = assess_runtime_quality(
            "Claro, te explico: API.",
            task_type="technical_reasoning",
            fallback_available=True,
            source_text="explicame arquitectura backend con integraciones externas",
        )

        self.assertEqual(assessment.status, QUALITY_STATUS_PLACEHOLDER)
        self.assertEqual(assessment.issue, "placeholder_output")
        self.assertTrue(assessment.retry_with_fallback)

    def test_runtime_quality_guard_can_trigger_transitional_fallback_for_placeholder_technical_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output="respuesta granite",
                critic_output="VERIFICADA: sin conflicto claro.",
                qwen_output="Idea breve: usa auth estable y prueba rollback antes del deploy.",
            )
            execution = execute_model_response(
                conversation=[
                    {
                        "role": "user",
                        "content": "explicame una api con auth, rollback y riesgo en produccion",
                    }
                ],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertTrue(execution.used_model)
            self.assertEqual(
                execution.selected_provider,
                LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
            )
            self.assertTrue(execution.fallback_used)
            self.assertEqual(execution.runtime_quality_status, "recovered_by_fallback")
            self.assertEqual(
                execution.degradation_hint,
                "transitional_fallback_active:placeholder_output",
            )
            self.assertEqual(execution.critic_value, VERIFICATION_OUTCOME_VERIFIED)
            self.assertEqual(execution.router_value, "not_needed")
            self.assertEqual(execution.fallback_pressure, "low")
            self.assertIn("quality_guard:trigger:placeholder_output", execution.provider_trace)
            self.assertIn("quality_guard:recovered_by_fallback", execution.provider_trace)
            self.assertIn("fallback:used:transitional", execution.provider_trace)

    def test_runtime_quality_guard_can_trigger_transitional_fallback_for_off_topic_technical_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output=(
                    "Idea breve: el aprendizaje automático estudia cómo un sistema aprende de los datos "
                    "para hacer predicciones."
                ),
                critic_output="VERIFICADA: sin conflicto claro.",
                qwen_output="Idea breve: en una API con auth y rollback, define primero el esquema de autenticación y el plan de reversión.",
            )
            execution = execute_model_response(
                conversation=[
                    {
                        "role": "user",
                        "content": "explicame una api con auth, rollback y riesgo en produccion",
                    }
                ],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertEqual(
                execution.selected_provider,
                LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
            )
            self.assertTrue(execution.fallback_used)
            self.assertEqual(execution.runtime_quality_status, "recovered_by_fallback")
            self.assertEqual(
                execution.degradation_hint,
                "transitional_fallback_active:off_topic_output",
            )
            self.assertIn("quality_guard:trigger:off_topic_output", execution.provider_trace)

    def test_runtime_quality_guard_can_rescue_known_technical_family_with_fallback_manager(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output="respuesta granite",
                critic_output="VERIFICADA: sin conflicto claro.",
                qwen_output="AJUSTE: corta la respuesta. Verificacion breve: sin conflicto claro.",
            )
            execution = execute_model_response(
                conversation=[{"role": "user", "content": "que es JWT"}],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertFalse(execution.used_model)
            self.assertTrue(execution.fallback_used)
            self.assertEqual(execution.runtime_quality_status, "recovered_by_fallback_manager")
            self.assertEqual(
                execution.fallback_reason,
                "stable_technical_rescue:placeholder_output",
            )
            self.assertIn("rescate razonable", execution.response.casefold())
            self.assertIn("jwt", execution.response.casefold())
            self.assertNotIn("respondes siempre", execution.response.casefold())
            self.assertNotIn("verificacion breve", execution.response.casefold())
            self.assertEqual(
                execution.degradation_hint,
                "quality_guard_rescued_by_fallback_manager:placeholder_output",
            )
            self.assertIn(
                "quality_guard:recovered_by_fallback_manager",
                execution.provider_trace,
            )
            self.assertIn("fallback:manager_response", execution.provider_trace)

    def test_runtime_quality_guard_can_rescue_open_technical_prompt_with_contextual_fallback_manager(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(
                root,
                granite_output="JWT es un token firmado para transportar identidad.",
                critic_output="VERIFICADA: sin conflicto claro.",
                qwen_output="respuesta generica",
            )
            execution = execute_model_response(
                conversation=[
                    {
                        "role": "user",
                        "content": "como balancearias cache, auth y colas en una API con mucho trafico",
                    }
                ],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                critic_llama_path=stack["llama"],
                critic_model_path=stack["critic"],
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertFalse(execution.used_model)
            self.assertTrue(execution.fallback_used)
            self.assertEqual(execution.runtime_quality_status, "recovered_by_fallback_manager")
            self.assertEqual(
                execution.fallback_reason,
                "stable_technical_rescue:off_topic_output",
            )
            self.assertIn("rescate razonable", execution.response.casefold())
            self.assertIn("cache", execution.response.casefold())
            self.assertIn("colas", execution.response.casefold())
            self.assertIn("auth", execution.response.casefold())
            self.assertNotIn("verificacion breve", execution.response.casefold())
            self.assertEqual(
                execution.degradation_hint,
                "quality_guard_rescued_by_fallback_manager:off_topic_output",
            )

    def test_turn_metadata_carries_runtime_quality_and_degradation_fields(self) -> None:
        result = self._run_turn_with_multistack(
            "explicame una api con auth, rollback y riesgo en produccion",
            granite_output="respuesta granite",
            critic_output="VERIFICADA: sin conflicto claro.",
            qwen_output="Idea breve: usa auth estable y prueba rollback antes del deploy.",
        )

        self.assertEqual(
            result.metadata.selected_provider,
            LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
        )
        self.assertEqual(result.metadata.runtime_quality_status, "recovered_by_fallback")
        self.assertEqual(
            result.metadata.degradation_hint,
            "transitional_fallback_active:placeholder_output",
        )
        self.assertEqual(result.metadata.critic_value, VERIFICATION_OUTCOME_VERIFIED)
        self.assertEqual(result.metadata.router_value, "not_needed")
        self.assertEqual(result.metadata.fallback_pressure, "low")

    def test_turn_metadata_carries_primary_only_provider_fields(self) -> None:
        result = self._run_turn_with_multistack("hola aura")

        self.assertEqual(result.metadata.route, "model")
        self.assertTrue(result.metadata.used_model)
        self.assertEqual(result.metadata.routing_decision, "primary_only")
        self.assertEqual(result.metadata.selected_provider, LOCAL_PRIMARY_PROVIDER_ID)
        self.assertEqual(result.metadata.selected_role, ROLE_PRIMARY)
        self.assertFalse(result.metadata.critic_requested)
        self.assertFalse(result.metadata.critic_used)
        self.assertEqual(result.metadata.composition_mode, COMPOSITION_MODE_PROVIDER_PRIMARY)
        self.assertEqual(result.metadata.routing_neuron_decision, ROUTING_RUNTIME_NO_SIGNAL)
        self.assertIn("routing:primary_only", result.metadata.route_trace)
        self.assertIn("router:selected:local_router", result.metadata.provider_trace)

    def test_turn_metadata_carries_primary_and_critic_fields(self) -> None:
        result = self._run_turn_with_multistack(
            "explicame una api con auth, rollback y riesgo en produccion"
        )

        self.assertEqual(result.metadata.route, "model")
        self.assertTrue(result.metadata.used_model)
        self.assertEqual(result.metadata.routing_decision, "primary_then_critic")
        self.assertEqual(result.metadata.selected_provider, LOCAL_PRIMARY_PROVIDER_ID)
        self.assertEqual(result.metadata.selected_role, ROLE_PRIMARY)
        self.assertTrue(result.metadata.critic_requested)
        self.assertTrue(result.metadata.critic_used)
        self.assertEqual(result.metadata.critic_provider, LOCAL_CRITIC_PROVIDER_ID)
        self.assertEqual(result.metadata.critic_result_status, PROVIDER_RESULT_SUCCESS)
        self.assertEqual(
            result.metadata.composition_mode,
            COMPOSITION_MODE_PROVIDER_PRIMARY_WITH_CRITIC,
        )
        self.assertEqual(result.metadata.verification_outcome, VERIFICATION_OUTCOME_VERIFIED)
        self.assertEqual(result.metadata.routing_neuron_decision, ROUTING_RUNTIME_NO_SIGNAL)
        self.assertIn("routing:primary_then_critic", result.metadata.route_trace)
        self.assertIn("critic:selected:local_critic", result.metadata.provider_trace)

    def test_critic_unavailable_degrades_to_primary_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(root)
            missing_critic_llama = str(root / "llama-missing")
            execution = execute_model_response(
                conversation=[
                    {
                        "role": "user",
                        "content": "explicame una api con auth, rollback y riesgo en produccion",
                    }
                ],
                memory={"name": "Ada"},
                llama_path=stack["llama"],
                model_path=stack["primary"],
                critic_llama_path=missing_critic_llama,
                critic_model_path=stack["critic"],
                behavior_plan=BehaviorPlan(intent="technical_explain"),
                route_action=ROUTE_MODEL,
                router_llama_path=stack["llama"],
                router_model_path=stack["router"],
                fallback_llama_path=stack["llama"],
                fallback_model_path=stack["fallback"],
            )

            self.assertTrue(execution.used_model)
            self.assertFalse(execution.fallback_used)
            self.assertTrue(execution.critic_requested)
            self.assertFalse(execution.critic_used)
            self.assertEqual(execution.critic_provider, LOCAL_CRITIC_PROVIDER_ID)
            self.assertEqual(execution.critic_result_status, "unavailable")
            self.assertEqual(execution.composition_mode, COMPOSITION_MODE_PROVIDER_PRIMARY)
            self.assertEqual(execution.gateway_mode, "primary_only")
            self.assertIn("critic:selected:local_critic", execution.provider_trace)
            self.assertIn("critic:unavailable", execution.provider_trace)

    def test_maintenance_last_turn_summary_closes_cleanly(self) -> None:
        results = self._run_turn_sequence(
            [
                "armame un plan corto",
                "resume el ultimo turno",
            ],
            memory={"name": "Ada"},
        )

        summary = results[-1].response
        self.assertEqual(results[-1].metadata.route, "maintenance")
        self.assertEqual(results[-1].metadata.task_type, "structured_internal")
        self.assertEqual(results[-1].metadata.routing_decision, "direct_maintenance")
        self.assertEqual(results[-1].metadata.provider_attempts, ())
        self.assertEqual(results[-1].metadata.no_model_reason, "resolved_by_maintenance")
        self.assertNotIn('haz un.', summary.casefold())
        self.assertNotIn('después "haz un.', summary.casefold())
        self.assertNotIn('despues "haz un.', summary.casefold())
        self.assertEqual(summary.count('"') % 2, 0)
        self.assertTrue(summary.endswith("."))

    def test_internal_routes_leave_explicit_no_model_metadata(self) -> None:
        maintenance_result = self._run_turn(
            "resume el ultimo turno",
            memory={"name": "Ada"},
            conversation=[
                {"role": "user", "content": "armame un plan corto"},
                {
                    "role": "aura",
                    "content": (
                        'Plan corto: ahora "haz una revision practica"; '
                        'después "haz un chequeo general".'
                    ),
                },
            ],
        )
        tools_result = self._run_turn("que tools internas tienes", memory={"name": "Ada"})

        self.assertEqual(maintenance_result.metadata.routing_decision, "direct_maintenance")
        self.assertEqual(maintenance_result.metadata.provider_attempts, ())
        self.assertIsNone(maintenance_result.metadata.provider_trace)
        self.assertIsNone(maintenance_result.metadata.gateway_mode)
        self.assertEqual(maintenance_result.metadata.no_model_reason, "resolved_by_maintenance")
        self.assertIn("route:maintenance", maintenance_result.metadata.route_trace)

        self.assertEqual(tools_result.metadata.routing_decision, "direct_internal_tools")
        self.assertEqual(tools_result.metadata.provider_attempts, ())
        self.assertIsNone(tools_result.metadata.provider_trace)
        self.assertIsNone(tools_result.metadata.gateway_mode)
        self.assertEqual(tools_result.metadata.no_model_reason, "resolved_by_internal_tools")
        self.assertIn("route:internal_tools", tools_result.metadata.route_trace)

    def test_central_logic_no_longer_calls_runtime_directly(self) -> None:
        central_files = [
            Path("agents/response_agent.py"),
            Path("agents/core_agent.py"),
            Path("agents/capabilities_registry.py"),
            Path("agents/internal_actions_registry.py"),
            Path("agents/internal_tools_registry.py"),
        ]
        provider_file = Path("providers/local_llama_provider.py")

        for file_path in central_files:
            with self.subTest(file=str(file_path)):
                source = file_path.read_text(encoding="utf-8")
                self.assertNotIn("run_model(", source)

        provider_source = provider_file.read_text(encoding="utf-8")
        self.assertIn("run_model(", provider_source)

    def test_situational_profiles_are_deterministic_across_scenarios(self) -> None:
        scenario_expectations = {
            "ready": (
                {"name": "Ada"},
                True,
                "exec",
                SITUATIONAL_PROFILE_EXPLOIT,
                MOMENT_PROFILE_EXPLOIT_NOW,
                None,
                "practical_review",
                "if_more_panorama_needed",
            ),
            "limited_model": (
                {"name": "Ada"},
                False,
                "exec",
                SITUATIONAL_PROFILE_RECOVERY,
                MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY,
                "model",
                "model_recovery",
                "after_recovery_validation",
            ),
            "limited_runtime": (
                {"name": "Ada"},
                True,
                "nonexec",
                SITUATIONAL_PROFILE_RECOVERY,
                MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY,
                "runtime",
                "runtime_recovery",
                "after_recovery_validation",
            ),
            "partially_ready": (
                {"preferences": ["respuertas claras"]},
                True,
                "exec",
                SITUATIONAL_PROFILE_MAINTENANCE,
                MOMENT_PROFILE_MAINTAIN_BEFORE_ADVANCING,
                "memory_sanitization",
                "memory_state_review",
                "after_state_stabilization",
            ),
            "memory_empty": (
                {},
                True,
                "exec",
                SITUATIONAL_PROFILE_MAINTENANCE,
                MOMENT_PROFILE_USABLE_BUT_REVIEW_FIRST,
                "memory_coverage",
                "general_check",
                "if_initial_scan_confirms_gap",
            ),
        }

        for name, (
            memory,
            model_available,
            runtime_mode,
            expected_profile,
            expected_moment,
            expected_blocker,
            expected_focus,
            expected_trigger,
        ) in scenario_expectations.items():
            with self.subTest(scenario=name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    context = self._make_context(
                        Path(tmpdir),
                        "que conviene hacer ahora",
                        memory=memory,
                        model_available=model_available,
                        runtime_mode=runtime_mode,
                    )
                    signals = resolve_contextual_response_signals(
                        SEQUENCE_STRATEGIC_GUIDANCE,
                        context,
                    )

                self.assertEqual(signals.situational_profile, expected_profile)
                self.assertEqual(signals.moment_profile, expected_moment)
                self.assertEqual(signals.advice_frame, ADVICE_FRAME_FOCUS_NOW)
                self.assertEqual(signals.recommended_focus, expected_focus)
                self.assertEqual(signals.blocker_type, expected_blocker)
                self.assertTrue(signals.recommended_order)
                self.assertEqual(signals.next_move_chain, signals.recommended_order)
                self.assertEqual(signals.move_priority, signals.recommended_order[0])
                self.assertEqual(signals.move_count, len(signals.recommended_order))
                self.assertEqual(signals.followup_trigger, expected_trigger)
                self.assertTrue(signals.guidance_mode)
                self.assertTrue(signals.sequence_confidence)
                self.assertTrue(signals.momentum_type)
                self.assertTrue(signals.micro_plan)
                self.assertTrue(signals.now_step)
                self.assertTrue(signals.next_step)
                self.assertTrue(signals.plan_horizon)
                self.assertTrue(signals.planning_mode)
                self.assertTrue(signals.sequence_depth)
                self.assertTrue(signals.plan_confidence)
                self.assertTrue(signals.followup_priority)

        with tempfile.TemporaryDirectory() as tmpdir:
            recovery_context = self._make_context(
                Path(tmpdir),
                "si estuvieras limitada que harias primero",
                memory={"name": "Ada"},
            )
            recovery_signals = resolve_contextual_response_signals(
                SEQUENCE_STRATEGIC_GUIDANCE,
                recovery_context,
            )
        self.assertEqual(recovery_signals.situational_profile, SITUATIONAL_PROFILE_RECOVERY)
        self.assertEqual(recovery_signals.advice_frame, ADVICE_FRAME_RECOVERY_PLAY)
        self.assertEqual(recovery_signals.blocker_type, "runtime_or_model")
        self.assertEqual(recovery_signals.recovery_strategy, "validate_local_runtime")
        self.assertEqual(recovery_signals.moment_profile, MOMENT_PROFILE_BLOCKED_NEEDS_RECOVERY)
        self.assertEqual(recovery_signals.followup_trigger, "after_recovery_validation")

    def test_layer_queries_stay_differentiated(self) -> None:
        expectations = {
            "que capacidades tienes": "capabilities",
            "que operaciones internas tienes": "operations",
            "que tools internas tienes": "internal_tools",
            "haz un diagnostico interno": "internal_tools",
            "estas lista para trabajar": "internal_tools",
            "que conviene hacer ahora": "internal_tools",
            "armame un plan corto": "internal_tools",
            "esto es posible?": "internal_tools",
            "que tan seguro estas?": "internal_tools",
            "ves alguna contradiccion?": "internal_tools",
            "como me puedes ayudar ahora mismo": "internal_tools",
        }

        responses: list[str] = []
        for query, expected_route in expectations.items():
            with self.subTest(query=query):
                result = self._run_turn(query, memory={"name": "Ada"})
                self.assertEqual(result.metadata.route, expected_route)
                self.assertFalse(result.metadata.used_model)
                responses.append(result.response)

        self.assertEqual(len(set(responses)), len(responses))

    def test_non_regression_queries_keep_original_routes(self) -> None:
        with _codex_registry_mocks():
            expectations = {
                "que sabes de mi": "internal_query",
                "que estado tienes": "system_state",
                "muestrame el ultimo log": "maintenance",
                "resume el ultimo turno": "maintenance",
            }

            for query, expected_route in expectations.items():
                with self.subTest(query=query):
                    result = self._run_turn(query, memory={"name": "Ada"})
                    self.assertEqual(result.metadata.route, expected_route)
                    self.assertFalse(result.metadata.used_model)
                    self.assertTrue(result.response is None or isinstance(result.response, str))

    def test_prepare_turn_strips_windows_bom_from_piped_system_state_query(self) -> None:
        for raw_query in ("\ufeffque estado tienes", "ï»¿que estado tienes"):
            with self.subTest(raw_query=raw_query):
                turn_plan = prepare_turn(
                    raw_query,
                    conversation=[],
                    memory={},
                )

                self.assertIsNotNone(turn_plan)
                self.assertEqual(turn_plan.user_turn.raw, "que estado tienes")
                self.assertEqual(turn_plan.user_turn.text, "que estado tienes")
                self.assertEqual(turn_plan.route_decision.action, ROUTE_SYSTEM_STATE)

    def test_system_state_exposes_primary_and_critic_provider_status(self) -> None:
        with _codex_registry_mocks():
            result = self._run_turn("que estado tienes", memory={"name": "Ada"})
        self.assertEqual(result.metadata.route, "system_state")
        self.assertIn("providers: primary", result.response)
        self.assertIn("local_primary", result.response)
        self.assertIn("local_critic", result.response)
        self.assertIn("local_router", result.response)
        self.assertIn("local_transitional_fallback", result.response)
        self.assertIn("green stack active", result.response)
        self.assertIn("allowlist verde", result.response)
        self.assertIn("Routing Neuron V1", result.response)
        self.assertIn("pausadas", result.response)
        self.assertIn("alertas", result.response)
        self.assertIn("recomendaciones", result.response)
        self.assertIn("readiness", result.response)
        self.assertIn("health", result.response)
        self.assertIn("calibracion V0.39.6", result.response)
        self.assertIn("SmolLM2-360M-Instruct", result.response)
        self.assertIn("Granite 3.0 1B-A400M-Instruct", result.response)
        self.assertIn("OLMo-2-0425-1B-Instruct", result.response)
        self.assertIn("Qwen2-1.5B-Instruct", result.response)

    def test_prepare_turn_keeps_system_state_route_for_repaired_mojibake_query(self) -> None:
        turn_plan = prepare_turn(
            "\u200b\xc2\xbfCual es tu estado?",
            conversation=[],
            memory={},
        )

        self.assertIsNotNone(turn_plan)
        self.assertEqual(turn_plan.user_turn.normalized, "cual es tu estado")
        self.assertEqual(turn_plan.route_decision.action, ROUTE_SYSTEM_STATE)

    def test_system_state_queries_keep_direct_route_for_obvious_equivalents(self) -> None:
        with _codex_registry_mocks():
            for query in (
                "quiero ver el launch dossier",
                "quiero ver actividad reciente de routing neuron",
                "quiero ver el checkpoint routing neuron",
            ):
                with self.subTest(query=query):
                    result = self._run_turn(query, memory={"name": "Ada"})
                    self.assertEqual(result.metadata.route, "system_state")
                    self.assertFalse(result.metadata.used_model)
                    self.assertEqual(result.metadata.no_model_reason, "resolved_by_system_state")

    def test_system_state_surfaces_v0393_stack_health_and_effective_model_paths(self) -> None:
        with _codex_registry_mocks():
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                stack = self._prepare_multistack_runtime(
                    root,
                    missing_models=("router",),
                )
                memory = {"name": "Ada"}
                memory_file = root / "memory.json"
                memory_file.write_text(json.dumps(memory, ensure_ascii=False), encoding="utf-8")
                log_file = root / "session.json"
                stale_primary = str(root / "granite-stale.gguf")

                state_plan = prepare_turn(
                    "que estado tienes",
                    conversation=[],
                    memory=memory,
                )
                state_result = execute_turn(
                    state_plan,
                    conversation=[],
                    memory=memory,
                    memory_file=str(memory_file),
                    log_file=str(log_file),
                    llama_path=stack["llama"],
                    model_path=stale_primary,
                    aura_version=AURA_VERSION,
                )
                path_plan = prepare_turn(
                    "muestra tu ruta de modelo",
                    conversation=[],
                    memory=memory,
                )
                path_result = execute_turn(
                    path_plan,
                    conversation=[],
                    memory=memory,
                    memory_file=str(memory_file),
                    log_file=str(log_file),
                    llama_path=stack["llama"],
                    model_path=stale_primary,
                    aura_version=AURA_VERSION,
                )
                available_plan = prepare_turn(
                    "tienes modelo disponible",
                    conversation=[],
                    memory=memory,
                )
                available_result = execute_turn(
                    available_plan,
                    conversation=[],
                    memory=memory,
                    memory_file=str(memory_file),
                    log_file=str(log_file),
                    llama_path=stack["llama"],
                    model_path=stale_primary,
                    aura_version=AURA_VERSION,
                )

            self.assertIn("health degraded", state_result.response)
            self.assertIn("pressure medium", state_result.response)
            self.assertIn("faltan micro expert router", state_result.response)
            self.assertIn("La ruta configurada del modelo es", path_result.response)
            self.assertIn("La ruta usable detectada ahora es", path_result.response)
            self.assertIn("Sí, el modelo está usable ahora", available_result.response)

    def test_system_state_exposes_routing_neuron_checkpoint_query(self) -> None:
        with _codex_registry_mocks():
            result = self._run_turn("checkpoint routing neuron", memory={"name": "Ada"})

        self.assertEqual(result.metadata.route, "system_state")
        self.assertFalse(result.metadata.used_model)
        self.assertIn("Checkpoint de Routing Neuron V1.3", result.response)
        self.assertIn("Selection", result.response)
        self.assertIn("Transformation", result.response)
        self.assertIn("Control", result.response)
        self.assertIn("Observed Pattern", result.response)
        self.assertIn("specialized_prompt", result.response)
        self.assertIn("fallback", result.response)
        self.assertIn("efficiency_score", result.response)
        self.assertIn("Codex", result.response)
        self.assertTrue(
            "ventana runtime" in result.response
            or "sin historial runtime reciente todavía" in result.response
            or "runtime preparado, todavía sin historial reciente" in result.response
        )
        self.assertIn("validación operativa", result.response)
        self.assertIn("deuda V1.x", result.response)

    def test_system_state_exposes_codex_registry_queries(self) -> None:
        with _codex_registry_mocks():
            latest_result = self._run_turn("ultimo trabajo de codex", memory={"name": "Ada"})
            status_result = self._run_turn("estado del registro de codex", memory={"name": "Ada"})
            changes_result = self._run_turn("que cambio codex", memory={"name": "Ada"})
            debt_result = self._run_turn("ultima deuda de codex", memory={"name": "Ada"})
            version_result = self._run_turn("que version cerro codex", memory={"name": "Ada"})
            pending_result = self._run_turn("que quedo pendiente en codex", memory={"name": "Ada"})

        for result in (
            latest_result,
            status_result,
            changes_result,
            debt_result,
            version_result,
            pending_result,
        ):
            self.assertEqual(result.metadata.route, "system_state")
            self.assertFalse(result.metadata.used_model)

        self.assertIn("Ultimo trabajo de Codex", latest_result.response)
        self.assertIn("V0.39.6", latest_result.response)
        self.assertIn("Estado del registro de Codex", status_result.response)
        self.assertIn("codex_control_registry.json", status_result.response)
        self.assertIn("Cambios del ultimo trabajo de Codex", changes_result.response)
        self.assertIn("Deuda abierta de Codex", debt_result.response)
        self.assertIn("Ultima version cerrada por Codex", version_result.response)
        self.assertIn("Pendiente de Codex", pending_result.response)
        self.assertNotIn("respondes siempre", changes_result.response.casefold())

    def test_system_state_covers_work_assistant_queries_without_model(self) -> None:
        with _codex_registry_mocks():
            expectations = {
                "que tocarias primero": "Yo tocaria primero",
                "como lo dividirias": "Lo dividiria en 3 pasos",
                "que riesgos ves": "Riesgo actual",
                "que quedo debil": "Lo que sigue flojo",
                "que revisarias": "Yo revisaria",
                "que sigue ahora": "siguiente paso recomendado",
                "que parte del sistema tocarias": "Yo tocaria primero",
                "que esta consolidado": "Lo mas consolidado ahora",
                "que no tocarias todavia": "Todavia no tocaria el corazon multimodelo",
                "que modelo usarias para esto": "Granite",
            }

            for query, expected_marker in expectations.items():
                with self.subTest(query=query):
                    result = self._run_turn(query, memory={"name": "Ada"})
                    self.assertEqual(result.metadata.route, "system_state")
                    self.assertFalse(result.metadata.used_model)
                    self.assertEqual(result.metadata.no_model_reason, "resolved_by_system_state")
                    self.assertIn(expected_marker, result.response)

    def test_system_state_model_choice_can_use_recent_context(self) -> None:
        result = self._run_turn(
            "que modelo usarias para esto",
            memory={"name": "Ada"},
            conversation=[
                {"role": "user", "content": "quiero revisar riesgos y consistencia de esta respuesta"},
            ],
        )

        self.assertEqual(result.metadata.route, "system_state")
        self.assertFalse(result.metadata.used_model)
        self.assertIn("OLMo", result.response)
        self.assertIn("critic", result.response.casefold())

    def test_system_state_is_honest_when_routing_neuron_has_no_runtime_history(self) -> None:
        with _codex_registry_mocks():
            empty_registry = build_empty_routing_neuron_registry()

            state_result = self._run_turn(
                "que estado tienes",
                memory={"name": "Ada"},
                routing_registry=empty_registry,
            )
            activity_result = self._run_turn(
                "muestra actividad reciente de routing neuron",
                memory={"name": "Ada"},
                routing_registry=empty_registry,
            )
            checkpoint_result = self._run_turn(
                "checkpoint routing neuron",
                memory={"name": "Ada"},
                routing_registry=empty_registry,
            )

        self.assertIn("runtime preparado, todavía sin historial reciente", state_result.response)
        self.assertIn("validación operativa en progreso", state_result.response)
        self.assertEqual(
            activity_result.response,
            "Routing Neuron V1 todavía no tiene actividad reciente relevante.",
        )
        self.assertIn("sin historial runtime reciente todavía", checkpoint_result.response)

    def test_system_state_can_show_recent_routing_neuron_activity(self) -> None:
        with _codex_registry_mocks():
            results = self._run_turn_sequence(
                [
                    "explicame una api",
                    "explicame una api",
                    "que estado tienes",
                ],
                memory={"name": "Ada"},
                runtime_script=self._build_dual_provider_runtime_script(),
            )
            state_result = results[-1]
            self.assertEqual(state_result.metadata.route, "system_state")
            self.assertIn("Routing Neuron V1", state_result.response)
            self.assertIn("reciente", state_result.response)
            self.assertTrue(
                "candidate" in state_result.response
                or "active" in state_result.response
                or "observed_pattern" in state_result.response
            )

    def test_system_state_surfaces_weak_runtime_signal_after_degraded_turn(self) -> None:
        with _codex_registry_mocks():
            results = self._run_turn_sequence(
                [
                    "hola aura",
                    "que estado tienes",
                    "muestra actividad reciente de routing neuron",
                ],
                memory={"name": "Ada"},
                model_available=False,
            )

            state_result = results[1]
            activity_result = results[2]

            self.assertIn("Routing Neuron V1", state_result.response)
            self.assertIn("señal débil observada", state_result.response)
            self.assertIn("ventana runtime 1/", state_result.response)
            self.assertIn("fallback 1", state_result.response)
            self.assertIn("Actividad reciente de Routing Neuron V1", activity_result.response)
            self.assertTrue(
                "no_signal" in activity_result.response
                or "fallback_no_provider" in activity_result.response
            )

    def test_checkpoint_and_state_reflect_low_sample_runtime_after_applied_turn(self) -> None:
        with _codex_registry_mocks():
            candidate = register_routing_neuron_candidate(
                task_signature="technical_reasoning:technical_explain:model",
                activated_components=("primary", "critic"),
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
                success_history=("ok-1", "ok-2", "ok-3"),
                failure_history=(),
                expected_gain=0.2,
                estimated_cost=0.25,
                estimated_latency=90.0,
                neuron_type=ROUTING_TYPE_CONTROL,
            )
            self.assertIsNotNone(candidate)
            registry = build_empty_routing_neuron_registry().register_candidate(candidate)
            registry = registry.activate_candidate(candidate.neuron_id)
            set_default_routing_registry(registry)

            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                stack = self._prepare_multistack_runtime(
                    root,
                    granite_output="Idea breve: usa auth estable y rollback probado antes de producción.",
                    critic_output="VERIFICADA: sin conflicto claro.",
                )
                execution = execute_model_response(
                    conversation=[
                        {
                            "role": "user",
                            "content": "explicame una api con auth, rollback y riesgo en produccion",
                        }
                    ],
                    memory={"name": "Ada"},
                    llama_path=stack["llama"],
                    model_path=stack["primary"],
                    behavior_plan=BehaviorPlan(intent="technical_explain"),
                    route_action=ROUTE_MODEL,
                    critic_llama_path=stack["llama"],
                    critic_model_path=stack["critic"],
                    router_llama_path=stack["llama"],
                    router_model_path=stack["router"],
                    fallback_llama_path=stack["llama"],
                    fallback_model_path=stack["fallback"],
                    session_id="session-low-sample-state",
                )

            self.assertEqual(execution.routing_neuron_decision, ROUTING_RUNTIME_APPLIED)
            runtime_registry = get_default_routing_registry()

            state_result = self._run_turn(
                "que estado tienes",
                memory={"name": "Ada"},
                routing_registry=runtime_registry,
            )
            checkpoint_result = self._run_turn(
                "checkpoint routing neuron",
                memory={"name": "Ada"},
                routing_registry=runtime_registry,
            )

            self.assertIn("actividad aplicada observada con muestra baja", state_result.response)
            self.assertIn("ventana runtime 1/", state_result.response)
            self.assertIn("influyó 1", state_result.response)
            self.assertIn("actividad aplicada observada con muestra baja", checkpoint_result.response)
            self.assertIn("decisiones recientes applied", checkpoint_result.response)

    def test_live_applied_turn_is_visible_across_state_checkpoint_and_recent_activity(self) -> None:
        with _codex_registry_mocks():
            candidate = register_routing_neuron_candidate(
                task_signature="technical_reasoning:technical_explain:model",
                activated_components=("primary", "critic"),
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
                success_history=("ok-1", "ok-2", "ok-3"),
                failure_history=(),
                expected_gain=0.2,
                estimated_cost=0.25,
                estimated_latency=90.0,
                neuron_type=ROUTING_TYPE_CONTROL,
            )
            self.assertIsNotNone(candidate)
            registry = build_empty_routing_neuron_registry().register_candidate(candidate)
            registry = registry.activate_candidate(candidate.neuron_id)
            set_default_routing_registry(registry)

            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                stack = self._prepare_multistack_runtime(
                    root,
                    granite_output="Idea breve: usa auth estable y rollback probado antes de producción.",
                    critic_output="VERIFICADA: sin conflicto claro.",
                )
                memory = {"name": "Ada"}
                memory_file = root / "memory.json"
                memory_file.write_text(
                    json.dumps(memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                log_file = root / "session_20260401_010000.json"
                conversation: list[dict] = []
                results = []

                for query in (
                    "explicame una api con auth, rollback y riesgo en produccion",
                    "que estado tienes",
                    "checkpoint routing neuron",
                    "muestra actividad reciente de routing neuron",
                ):
                    turn_plan = prepare_turn(
                        query,
                        conversation=conversation,
                        memory=memory,
                    )
                    self.assertIsNotNone(turn_plan)
                    result = execute_turn(
                        turn_plan,
                        conversation=conversation,
                        memory=memory,
                        memory_file=str(memory_file),
                        log_file=str(log_file),
                        llama_path=stack["llama"],
                        model_path=stack["primary"],
                        aura_version=AURA_VERSION,
                    )
                    results.append(result)

            model_result, state_result, checkpoint_result, activity_result = results

            self.assertTrue(model_result.metadata.routing_neuron_applied)
            self.assertEqual(model_result.metadata.routing_neuron_decision_path, ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED)
            self.assertEqual(model_result.metadata.routing_neuron_influence, "skip_critic")
            self.assertIn("actividad aplicada observada con muestra baja", state_result.response)
            self.assertIn("influyó 1", state_result.response)
            self.assertIn("applied recientes skip_critic:improved", state_result.response)
            self.assertIn("decisiones recientes applied", checkpoint_result.response)
            self.assertIn("skip_critic:improved", checkpoint_result.response)
            self.assertIn("Actividad reciente de Routing Neuron V1", activity_result.response)
            self.assertIn("selected_and_applied", activity_result.response)
            self.assertIn("skip_critic", activity_result.response)

    def test_verified_runtime_can_bootstrap_visible_skip_critic_without_manual_seed(self) -> None:
        with _codex_registry_mocks():
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                stack = self._prepare_multistack_runtime(
                    root,
                    granite_output="Idea breve: usa auth estable y rollback probado antes de producción.",
                    critic_output="VERIFICADA: sin conflicto claro.",
                )
                memory = {"name": "Ada"}
                memory_file = root / "memory.json"
                memory_file.write_text(
                    json.dumps(memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                log_file = root / "session_20260402_010000.json"
                conversation: list[dict] = []
                results = []

                for query in (
                    "explicame una api con auth, rollback y riesgo en produccion",
                    "explicame una api con auth, rollback y riesgo en produccion",
                    "explicame una api con auth, rollback y riesgo en produccion",
                    "explicame una api con auth, rollback y riesgo en produccion",
                    "que estado tienes",
                    "checkpoint routing neuron",
                    "muestra actividad reciente de routing neuron",
                ):
                    turn_plan = prepare_turn(
                        query,
                        conversation=conversation,
                        memory=memory,
                    )
                    self.assertIsNotNone(turn_plan)
                    result = execute_turn(
                        turn_plan,
                        conversation=conversation,
                        memory=memory,
                        memory_file=str(memory_file),
                        log_file=str(log_file),
                        llama_path=stack["llama"],
                        model_path=stack["primary"],
                        aura_version=AURA_VERSION,
                    )
                    results.append(result)

            first_result, second_result, third_result, fourth_result, state_result, checkpoint_result, activity_result = results

            self.assertFalse(first_result.metadata.routing_neuron_applied)
            self.assertFalse(second_result.metadata.routing_neuron_applied)
            self.assertTrue(third_result.metadata.routing_neuron_applied)
            self.assertEqual(third_result.metadata.routing_neuron_influence, "skip_critic")
            self.assertEqual(
                third_result.metadata.routing_neuron_decision_path,
                ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED,
            )
            self.assertTrue(fourth_result.metadata.routing_neuron_applied)
            self.assertEqual(fourth_result.metadata.routing_neuron_influence, "skip_critic")
            self.assertEqual(
                fourth_result.metadata.routing_neuron_decision_path,
                ROUTING_RUNTIME_PATH_SELECTED_AND_APPLIED,
            )
            self.assertNotIn("routing_neuron", " ".join(fourth_result.metadata.provider_trace))

            runtime_registry = get_default_routing_registry()
            self.assertTrue(
                any(
                    candidate.neuron_state == ROUTING_STATE_ACTIVE
                    and "skip_critic" in candidate.routing_condition
                    for candidate in runtime_registry.candidates.values()
                )
            )
            self.assertIn("actividad aplicada observada con muestra baja", state_result.response)
            self.assertIn("skip_critic:improved", checkpoint_result.response)
            self.assertIn("selected_and_applied", activity_result.response)
            self.assertIn("skip_critic", activity_result.response)

    def test_system_state_recovers_visible_routing_trace_from_last_session_log(self) -> None:
        with _codex_registry_mocks():
            candidate = register_routing_neuron_candidate(
                task_signature="technical_reasoning:technical_explain:model",
                activated_components=("primary", "critic"),
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
                success_history=("ok-1", "ok-2", "ok-3"),
                failure_history=(),
                expected_gain=0.2,
                estimated_cost=0.25,
                estimated_latency=90.0,
                neuron_type=ROUTING_TYPE_CONTROL,
            )
            self.assertIsNotNone(candidate)

            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                stack = self._prepare_multistack_runtime(
                    root,
                    granite_output="Idea breve: usa auth estable y rollback probado antes de producción.",
                    critic_output="VERIFICADA: sin conflicto claro.",
                )
                registry = build_empty_routing_neuron_registry().register_candidate(candidate)
                registry = registry.activate_candidate(candidate.neuron_id)
                set_default_routing_registry(registry)

                memory = {"name": "Ada"}
                memory_file = root / "memory.json"
                memory_file.write_text(
                    json.dumps(memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                prior_log_file = root / "session_20260401_010000.json"
                conversation: list[dict] = []

                first_plan = prepare_turn(
                    "explicame una api con auth, rollback y riesgo en produccion",
                    conversation=conversation,
                    memory=memory,
                )
                self.assertIsNotNone(first_plan)
                first_result = execute_turn(
                    first_plan,
                    conversation=conversation,
                    memory=memory,
                    memory_file=str(memory_file),
                    log_file=str(prior_log_file),
                    llama_path=stack["llama"],
                    model_path=stack["primary"],
                    aura_version=AURA_VERSION,
                )
                self.assertTrue(first_result.metadata.routing_neuron_applied)
                prior_log_file.write_text(
                    json.dumps(conversation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                reset_default_routing_registry()
                fresh_memory = {"name": "Ada"}
                fresh_memory_file = root / "memory_fresh.json"
                fresh_memory_file.write_text(
                    json.dumps(fresh_memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                fresh_conversation: list[dict] = []
                fresh_log_file = root / "session_20260401_020000.json"
                recovered_results = []

                for query in (
                    "que estado tienes",
                    "checkpoint routing neuron",
                    "muestra actividad reciente de routing neuron",
                ):
                    turn_plan = prepare_turn(
                        query,
                        conversation=fresh_conversation,
                        memory=fresh_memory,
                    )
                    self.assertIsNotNone(turn_plan)
                    result = execute_turn(
                        turn_plan,
                        conversation=fresh_conversation,
                        memory=fresh_memory,
                        memory_file=str(fresh_memory_file),
                        log_file=str(fresh_log_file),
                        llama_path=stack["llama"],
                        model_path=stack["primary"],
                        aura_version=AURA_VERSION,
                    )
                    recovered_results.append(result)

            state_result, checkpoint_result, activity_result = recovered_results

            self.assertIn("sin historial runtime en memoria", state_result.response)
            self.assertIn("actividad aplicada visible con muestra baja recuperada de la última sesión registrada", state_result.response)
            self.assertIn("última sesión registrada", state_result.response)
            self.assertIn("influyó 1", state_result.response)
            self.assertIn("selected_and_applied", state_result.response)
            self.assertIn("sin historial runtime en memoria", checkpoint_result.response)
            self.assertIn("última sesión registrada", checkpoint_result.response)
            self.assertIn("skip_critic", checkpoint_result.response)
            self.assertIn("sin historial runtime en memoria", activity_result.response)
            self.assertIn("replay visible desde la última sesión registrada", activity_result.response)
            self.assertIn("selected_and_applied", activity_result.response)
            self.assertIn("skip_critic", activity_result.response)

    def test_recent_activity_from_session_log_explains_considered_without_candidate_match(self) -> None:
        with _codex_registry_mocks():
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                model_path, llama_path = self._prepare_runtime(
                    root,
                    model_available=False,
                )
                memory = {"name": "Ada"}
                memory_file = root / "memory.json"
                memory_file.write_text(
                    json.dumps(memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                prior_log_file = root / "session_20260401_010000.json"
                conversation: list[dict] = []

                first_plan = prepare_turn(
                    "hola aura",
                    conversation=conversation,
                    memory=memory,
                )
                self.assertIsNotNone(first_plan)
                first_result = execute_turn(
                    first_plan,
                    conversation=conversation,
                    memory=memory,
                    memory_file=str(memory_file),
                    log_file=str(prior_log_file),
                    llama_path=llama_path,
                    model_path=model_path,
                    aura_version=AURA_VERSION,
                )
                self.assertEqual(first_result.metadata.routing_neuron_decision_path, ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH)
                prior_log_file.write_text(
                    json.dumps(conversation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                reset_default_routing_registry()
                fresh_memory = {"name": "Ada"}
                fresh_memory_file = root / "memory_fresh.json"
                fresh_memory_file.write_text(
                    json.dumps(fresh_memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                fresh_conversation: list[dict] = []
                fresh_log_file = root / "session_20260401_020000.json"

                activity_plan = prepare_turn(
                    "muestra actividad reciente de routing neuron",
                    conversation=fresh_conversation,
                    memory=fresh_memory,
                )
                self.assertIsNotNone(activity_plan)
                activity_result = execute_turn(
                    activity_plan,
                    conversation=fresh_conversation,
                    memory=fresh_memory,
                    memory_file=str(fresh_memory_file),
                    log_file=str(fresh_log_file),
                    llama_path=llama_path,
                    model_path=model_path,
                    aura_version=AURA_VERSION,
                )

            self.assertIn("sin historial runtime en memoria", activity_result.response)
            self.assertIn("no_candidate_match", activity_result.response)
            self.assertIn("sin candidata coincidente", activity_result.response)
            self.assertIn("considerada globalmente sin candidata coincidente", activity_result.response)
            self.assertIn("fallback no_match", activity_result.response)

    def test_replay_from_previous_log_survives_after_current_session_writes_non_rn_log(self) -> None:
        with _codex_registry_mocks():
            candidate = register_routing_neuron_candidate(
                task_signature="technical_reasoning:technical_explain:model",
                activated_components=("primary", "critic"),
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
                success_history=("ok-1", "ok-2", "ok-3"),
                failure_history=(),
                expected_gain=0.2,
                estimated_cost=0.25,
                estimated_latency=90.0,
                neuron_type=ROUTING_TYPE_CONTROL,
            )
            self.assertIsNotNone(candidate)

            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                stack = self._prepare_multistack_runtime(
                    root,
                    granite_output="Idea breve: usa auth estable y rollback probado antes de producción.",
                    critic_output="VERIFICADA: sin conflicto claro.",
                )
                registry = build_empty_routing_neuron_registry().register_candidate(candidate)
                registry = registry.activate_candidate(candidate.neuron_id)
                set_default_routing_registry(registry)

                memory = {"name": "Ada"}
                memory_file = root / "memory.json"
                memory_file.write_text(
                    json.dumps(memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                prior_log_file = root / "session_20260401_010000.json"
                prior_conversation: list[dict] = []

                first_plan = prepare_turn(
                    "explicame una api con auth, rollback y riesgo en produccion",
                    conversation=prior_conversation,
                    memory=memory,
                )
                self.assertIsNotNone(first_plan)
                first_result = execute_turn(
                    first_plan,
                    conversation=prior_conversation,
                    memory=memory,
                    memory_file=str(memory_file),
                    log_file=str(prior_log_file),
                    llama_path=stack["llama"],
                    model_path=stack["primary"],
                    aura_version=AURA_VERSION,
                )
                self.assertTrue(first_result.metadata.routing_neuron_applied)
                prior_log_file.write_text(
                    json.dumps(prior_conversation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                reset_default_routing_registry()
                fresh_memory = {"name": "Ada"}
                fresh_memory_file = root / "memory_fresh.json"
                fresh_memory_file.write_text(
                    json.dumps(fresh_memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                current_log_file = root / "session_20260401_020000.json"
                current_conversation: list[dict] = []

                state_plan = prepare_turn(
                    "que estado tienes",
                    conversation=current_conversation,
                    memory=fresh_memory,
                )
                self.assertIsNotNone(state_plan)
                state_result = execute_turn(
                    state_plan,
                    conversation=current_conversation,
                    memory=fresh_memory,
                    memory_file=str(fresh_memory_file),
                    log_file=str(current_log_file),
                    llama_path=stack["llama"],
                    model_path=stack["primary"],
                    aura_version=AURA_VERSION,
                )
                current_log_file.write_text(
                    json.dumps(current_conversation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                checkpoint_plan = prepare_turn(
                    "checkpoint routing neuron",
                    conversation=current_conversation,
                    memory=fresh_memory,
                )
                self.assertIsNotNone(checkpoint_plan)
                checkpoint_result = execute_turn(
                    checkpoint_plan,
                    conversation=current_conversation,
                    memory=fresh_memory,
                    memory_file=str(fresh_memory_file),
                    log_file=str(current_log_file),
                    llama_path=stack["llama"],
                    model_path=stack["primary"],
                    aura_version=AURA_VERSION,
                )
                current_log_file.write_text(
                    json.dumps(current_conversation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                activity_plan = prepare_turn(
                    "muestra actividad reciente de routing neuron",
                    conversation=current_conversation,
                    memory=fresh_memory,
                )
                self.assertIsNotNone(activity_plan)
                activity_result = execute_turn(
                    activity_plan,
                    conversation=current_conversation,
                    memory=fresh_memory,
                    memory_file=str(fresh_memory_file),
                    log_file=str(current_log_file),
                    llama_path=stack["llama"],
                    model_path=stack["primary"],
                    aura_version=AURA_VERSION,
                )

            self.assertIn("sin historial runtime en memoria", state_result.response)
            self.assertIn("la última sesión registrada", state_result.response)
            self.assertIn("selected_and_applied", state_result.response)
            self.assertIn("sin historial runtime en memoria", checkpoint_result.response)
            self.assertIn("la última sesión registrada", checkpoint_result.response)
            self.assertIn("selected_and_applied", checkpoint_result.response)
            self.assertIn("replay visible desde la última sesión registrada", activity_result.response)
            self.assertIn("selected_and_applied", activity_result.response)
            self.assertIn("skip_critic", activity_result.response)

    def test_replay_from_previous_log_surfaces_weak_signal_consistently(self) -> None:
        with _codex_registry_mocks():
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                model_path, llama_path = self._prepare_runtime(
                    root,
                    model_available=False,
                )
                memory = {"name": "Ada"}
                memory_file = root / "memory.json"
                memory_file.write_text(
                    json.dumps(memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                prior_log_file = root / "session_20260401_010000.json"
                prior_conversation: list[dict] = []

                first_plan = prepare_turn(
                    "hola aura",
                    conversation=prior_conversation,
                    memory=memory,
                )
                self.assertIsNotNone(first_plan)
                first_result = execute_turn(
                    first_plan,
                    conversation=prior_conversation,
                    memory=memory,
                    memory_file=str(memory_file),
                    log_file=str(prior_log_file),
                    llama_path=llama_path,
                    model_path=model_path,
                    aura_version=AURA_VERSION,
                )
                self.assertEqual(first_result.metadata.routing_neuron_decision_path, ROUTING_RUNTIME_PATH_NO_CANDIDATE_MATCH)
                prior_log_file.write_text(
                    json.dumps(prior_conversation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                reset_default_routing_registry()
                fresh_memory = {"name": "Ada"}
                fresh_memory_file = root / "memory_fresh.json"
                fresh_memory_file.write_text(
                    json.dumps(fresh_memory, ensure_ascii=False),
                    encoding="utf-8",
                )
                current_log_file = root / "session_20260401_020000.json"
                current_conversation: list[dict] = []
                recovered_results = []

                for query in (
                    "que estado tienes",
                    "checkpoint routing neuron",
                    "muestra actividad reciente de routing neuron",
                ):
                    turn_plan = prepare_turn(
                        query,
                        conversation=current_conversation,
                        memory=fresh_memory,
                    )
                    self.assertIsNotNone(turn_plan)
                    result = execute_turn(
                        turn_plan,
                        conversation=current_conversation,
                        memory=fresh_memory,
                        memory_file=str(fresh_memory_file),
                        log_file=str(current_log_file),
                        llama_path=llama_path,
                        model_path=model_path,
                        aura_version=AURA_VERSION,
                    )
                    current_log_file.write_text(
                        json.dumps(current_conversation, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    recovered_results.append(result)

            state_result, checkpoint_result, activity_result = recovered_results

            self.assertIn("sin historial runtime en memoria", state_result.response)
            self.assertIn("señal débil visible recuperada de la última sesión registrada", state_result.response)
            self.assertIn("no_candidate_match", state_result.response)
            self.assertIn("sin historial runtime en memoria", checkpoint_result.response)
            self.assertIn("señal débil visible recuperada de la última sesión registrada", checkpoint_result.response)
            self.assertIn("no_candidate_match", checkpoint_result.response)
            self.assertIn("replay visible desde la última sesión registrada", activity_result.response)
            self.assertIn("sin candidata coincidente", activity_result.response)
            self.assertIn("fallback no_match", activity_result.response)

    def test_system_state_admin_queries_expose_routing_neuron_repertoire(self) -> None:
        active_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5"),
            failure_history=(),
            expected_gain=0.24,
            estimated_cost=0.12,
            estimated_latency=70.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        paused_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="compact_before_primary",
            routing_condition="technical_reasoning low",
            intermediate_transform="compacta el contexto antes de responder",
            success_history=("ok-1", "ok-2"),
            failure_history=("fail-1", "fail-2"),
            expected_gain=0.09,
            estimated_cost=0.25,
            estimated_latency=110.0,
            neuron_type=ROUTING_TYPE_TRANSFORMATION,
        )
        self.assertIsNotNone(active_candidate)
        self.assertIsNotNone(paused_candidate)
        active_candidate = replace(
            active_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.88,
            confidence_tier=ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            stability_label=ROUTING_STABILITY_STABLE,
            successful_activations=5,
            failed_activations=0,
            stable_activation_streak=3,
            promotion_ready_signal=True,
            readiness_band=ROUTING_READINESS_NEAR_READY,
            readiness_reason="valor sostenido con poco ruido frente a baseline",
            last_decision="applied",
        )
        paused_candidate = replace(
            paused_candidate,
            neuron_state=ROUTING_STATE_PAUSED,
            global_routing_score=0.41,
            confidence_tier=ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
            stability_label=ROUTING_STABILITY_FRAGILE,
            failed_activations=2,
            recent_fallback_count=2,
            alerts=("fragility_detected",),
            readiness_band=ROUTING_READINESS_NOT_READY,
            readiness_reason="pausada por inestabilidad o revisión",
            last_decision="paused",
        )
        registry = build_empty_routing_neuron_registry().register_candidate(active_candidate)
        registry = registry.register_candidate(paused_candidate)
        registry = replace(
            registry,
            active={active_candidate.neuron_id: active_candidate},
            conflict_log=(f"session-admin:{active_candidate.neuron_id}>{paused_candidate.neuron_id}",),
            alerts=(f"{paused_candidate.neuron_id}:inestable",),
        )
        registry = registry.register_recommendation(
            RoutingPromotionRecommendation(
                neuron_id=active_candidate.neuron_id,
                recommended_stage=PROMOTION_STAGE_ADAPTER,
                reason="valor sostenido y buena estabilidad",
                confidence="high",
            )
        )

        recent_result = self._run_turn(
            "muestra actividad reciente de routing neuron",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        active_result = self._run_turn(
            "que neuronas tienes activas",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        paused_result = self._run_turn(
            "que neuronas estan pausadas",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        alerts_result = self._run_turn(
            "que neuronas tienen alertas",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        score_result = self._run_turn(
            "que neuronas tienen mejor score",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        readiness_result = self._run_turn(
            "que neuronas se estan acercando a promocion",
            memory={"name": "Ada"},
            routing_registry=registry,
        )

        for result in (
            recent_result,
            active_result,
            paused_result,
            alerts_result,
            score_result,
            readiness_result,
        ):
            self.assertEqual(result.metadata.route, "system_state")
            self.assertFalse(result.metadata.used_model)

        self.assertIn(active_candidate.neuron_id, recent_result.response)
        self.assertIn(active_candidate.neuron_id, active_result.response)
        self.assertIn(paused_candidate.neuron_id, paused_result.response)
        self.assertIn("alertas", alerts_result.response)
        self.assertIn(active_candidate.neuron_id, score_result.response)
        self.assertIn("eff", score_result.response)
        self.assertIn("readiness near_ready", readiness_result.response)
        self.assertIn("motivo", readiness_result.response)

    def test_routing_maintenance_builds_review_priority_and_action_suggestion(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6"),
            failure_history=(),
            expected_gain=0.26,
            estimated_cost=0.1,
            estimated_latency=65.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(candidate)
        candidate = replace(
            candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            watch_status=True,
            watch_reason="seguimiento manual",
            global_routing_score=0.91,
            confidence_tier=ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            stability_label=ROUTING_STABILITY_STABLE,
            successful_activations=6,
            promotion_ready_signal=True,
            readiness_band=ROUTING_READINESS_NEAR_READY,
            readiness_reason="valor sostenido con poco ruido frente a baseline",
        )
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        registry = replace(registry, active={candidate.neuron_id: candidate})

        snapshot = build_routing_repertoire_snapshot(registry)
        self.assertTrue(snapshot.entries)
        entry = snapshot.entries[0]
        self.assertTrue(entry.watch_status)
        self.assertEqual(entry.readiness_band, ROUTING_READINESS_NEAR_READY)
        self.assertIn(entry.review_priority, {ROUTING_REVIEW_PRIORITY_HIGH, ROUTING_REVIEW_PRIORITY_MEDIUM})
        self.assertIsNotNone(entry.action_suggestion)

    def test_system_state_admin_queries_expose_watch_review_and_log(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6"),
            failure_history=(),
            expected_gain=0.27,
            estimated_cost=0.1,
            estimated_latency=60.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(candidate)
        candidate = replace(
            candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.9,
            confidence_tier=ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            stability_label=ROUTING_STABILITY_STABLE,
            successful_activations=6,
            promotion_ready_signal=True,
            readiness_band=ROUTING_READINESS_NEAR_READY,
            readiness_reason="valor sostenido con poco ruido frente a baseline",
            watch_status=True,
            watch_reason="seguimiento manual",
            review_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            review_reason="readiness alta con valor sostenido",
            action_suggestion="review_readiness",
        )
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        registry = replace(registry, active={candidate.neuron_id: candidate})
        registry = registry.mark_watch(candidate.neuron_id, "seguimiento manual")
        registry = registry.pause_candidate_administratively(candidate.neuron_id, "revision_manual")
        registry = registry.resume_candidate(candidate.neuron_id, "reanudar_revision")

        watch_result = self._run_turn(
            "que neuronas estan en watch",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        review_result = self._run_turn(
            "que neuronas requieren revision",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        log_result = self._run_turn(
            "muestra la bitacora de routing neuron",
            memory={"name": "Ada"},
            routing_registry=registry,
        )

        self.assertEqual(watch_result.metadata.route, "system_state")
        self.assertEqual(review_result.metadata.route, "system_state")
        self.assertEqual(log_result.metadata.route, "system_state")
        self.assertIn(candidate.neuron_id, watch_result.response)
        self.assertIn(candidate.neuron_id, review_result.response)
        self.assertIn("Bitácora", log_result.response)
        self.assertIn("mark_watch", log_result.response)

    def test_maintenance_can_pause_resume_watch_and_acknowledge_routing_neuron(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=(),
            expected_gain=0.21,
            estimated_cost=0.11,
            estimated_latency=70.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(candidate)
        candidate = replace(
            candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.78,
            alerts=("overuse_detected",),
        )
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        registry = replace(
            registry,
            active={candidate.neuron_id: candidate},
            alerts=(f"{candidate.neuron_id}:overuse_detected",),
        )

        pause_result = self._run_turn(
            f"pausa la neurona {candidate.neuron_id} por revision_manual",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        paused_registry = get_default_routing_registry()
        self.assertEqual(pause_result.metadata.route, "maintenance")
        self.assertEqual(paused_registry.candidates[candidate.neuron_id].neuron_state, ROUTING_STATE_PAUSED)

        resume_result = self._run_turn(
            f"reanuda la neurona {candidate.neuron_id} por reanudar_revision",
            memory={"name": "Ada"},
            routing_registry=paused_registry,
        )
        resumed_registry = get_default_routing_registry()
        self.assertEqual(resume_result.metadata.route, "maintenance")
        self.assertEqual(resumed_registry.candidates[candidate.neuron_id].last_admin_action, "resume")

        watch_result = self._run_turn(
            f"marca en watch la neurona {candidate.neuron_id} por seguimiento_manual",
            memory={"name": "Ada"},
            routing_registry=resumed_registry,
        )
        watched_registry = get_default_routing_registry()
        self.assertEqual(watch_result.metadata.route, "maintenance")
        self.assertTrue(watched_registry.candidates[candidate.neuron_id].watch_status)

        ack_result = self._run_turn(
            f"reconoce alerta de la neurona {candidate.neuron_id} por alerta_revisada",
            memory={"name": "Ada"},
            routing_registry=watched_registry,
        )
        ack_registry = get_default_routing_registry()
        self.assertEqual(ack_result.metadata.route, "maintenance")
        self.assertEqual(
            ack_registry.candidates[candidate.neuron_id].alert_status,
            ALERT_STATUS_ACKNOWLEDGED,
        )
        self.assertTrue(any(action.action_type == "acknowledge_alert" for action in ack_registry.admin_log))

        resolve_alert_result = self._run_turn(
            f"resuelve alerta de la neurona {candidate.neuron_id} por alerta_resuelta",
            memory={"name": "Ada"},
            routing_registry=ack_registry,
        )
        resolved_alert_registry = get_default_routing_registry()
        self.assertEqual(resolve_alert_result.metadata.route, "maintenance")
        self.assertEqual(resolved_alert_registry.candidates[candidate.neuron_id].alerts, ())
        self.assertEqual(
            resolved_alert_registry.candidates[candidate.neuron_id].alert_status,
            ALERT_STATUS_RESOLVED,
        )

        clear_result = self._run_turn(
            f"quita de watch la neurona {candidate.neuron_id} por seguimiento_cerrado",
            memory={"name": "Ada"},
            routing_registry=resolved_alert_registry,
        )
        cleared_registry = get_default_routing_registry()
        self.assertEqual(clear_result.metadata.route, "maintenance")
        self.assertFalse(cleared_registry.candidates[candidate.neuron_id].watch_status)
        self.assertTrue(any(action.action_type == "clear_watch" for action in cleared_registry.admin_log))

    def test_routing_maintenance_tracks_review_and_alert_lifecycle(self) -> None:
        candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=("fail-1",),
            expected_gain=0.11,
            estimated_cost=0.22,
            estimated_latency=95.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(candidate)
        candidate = replace(
            candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            watch_status=True,
            watch_reason="seguimiento manual",
            review_status=REVIEW_STATUS_WATCH,
            review_reason="seguimiento manual",
            last_admin_action="acknowledge_alert",
            last_admin_reason="alerta_revisada",
            alerts=("overuse_detected",),
            alert_status=ALERT_STATUS_ACKNOWLEDGED,
            review_cycles=2,
            alert_cycles=2,
        )
        registry = build_empty_routing_neuron_registry().register_candidate(candidate)
        registry = replace(
            registry,
            active={candidate.neuron_id: candidate},
            alerts=(f"{candidate.neuron_id}:overuse_detected",),
        )

        report = run_routing_maintenance(registry)
        refreshed = report.registry.candidates[candidate.neuron_id]
        self.assertEqual(refreshed.review_status, REVIEW_STATUS_STALE)
        self.assertEqual(refreshed.alert_status, ALERT_STATUS_ACKNOWLEDGED)
        self.assertEqual(refreshed.action_outcome, ACTION_OUTCOME_NO_CLEAR_CHANGE)
        self.assertIn(candidate.neuron_id, report.stale_ids)

        resolved_registry = report.registry.resolve_alert(candidate.neuron_id, "alerta_resuelta")
        resolved_registry = resolved_registry.clear_watch(candidate.neuron_id, "seguimiento_cerrado")
        resolved_report = run_routing_maintenance(resolved_registry)
        resolved_candidate = resolved_report.registry.candidates[candidate.neuron_id]
        self.assertEqual(resolved_candidate.review_status, REVIEW_STATUS_RESOLVED)
        self.assertEqual(resolved_candidate.alert_status, ALERT_STATUS_RESOLVED)
        self.assertEqual(resolved_candidate.action_outcome, ACTION_OUTCOME_HELPED)
        self.assertIn(candidate.neuron_id, resolved_report.resolved_review_ids)

        reopened_candidate = replace(
            resolved_candidate,
            alerts=("fragility_detected",),
        )
        reopened_registry = resolved_report.registry.register_candidate(reopened_candidate)
        reopened_registry = replace(
            reopened_registry,
            alerts=(f"{candidate.neuron_id}:fragility_detected",),
        )
        reopened_report = run_routing_maintenance(reopened_registry)
        reopened = reopened_report.registry.candidates[candidate.neuron_id]
        self.assertEqual(reopened.alert_status, ALERT_STATUS_REOPENED)

    def test_system_state_admin_queries_expose_lifecycle_views(self) -> None:
        open_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.12,
            estimated_cost=0.15,
            estimated_latency=85.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        resolved_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5"),
            failure_history=(),
            expected_gain=0.23,
            estimated_cost=0.1,
            estimated_latency=60.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        stale_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_explain:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=("fail-1",),
            expected_gain=0.1,
            estimated_cost=0.2,
            estimated_latency=90.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        reopened_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:technical_troubleshoot:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=(),
            expected_gain=0.14,
            estimated_cost=0.14,
            estimated_latency=72.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(open_candidate)
        self.assertIsNotNone(resolved_candidate)
        self.assertIsNotNone(stale_candidate)
        self.assertIsNotNone(reopened_candidate)

        open_candidate = replace(
            open_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            review_status=REVIEW_STATUS_OPEN,
            review_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            review_reason="requiere revisión abierta",
            action_suggestion="review_readiness",
        )
        resolved_candidate = replace(
            resolved_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            review_status=REVIEW_STATUS_RESOLVED,
            alert_status=ALERT_STATUS_RESOLVED,
            action_outcome=ACTION_OUTCOME_HELPED,
            action_suggestion="no_action_needed",
        )
        stale_candidate = replace(
            stale_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            review_status=REVIEW_STATUS_STALE,
            watch_status=True,
            watch_reason="seguimiento sin mejora",
            action_outcome=ACTION_OUTCOME_NO_CLEAR_CHANGE,
            action_suggestion="reassess_or_close_review",
            review_priority=ROUTING_REVIEW_PRIORITY_MEDIUM,
            review_reason="seguimiento sin mejora",
        )
        reopened_candidate = replace(
            reopened_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            alert_status=ALERT_STATUS_REOPENED,
            alerts=("fragility_detected",),
            review_status=REVIEW_STATUS_OPEN,
            review_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            review_reason="alerta reabierta",
        )
        registry = build_empty_routing_neuron_registry()
        for candidate in (open_candidate, resolved_candidate, stale_candidate, reopened_candidate):
            registry = registry.register_candidate(candidate)
        registry = replace(
            registry,
            active={
                open_candidate.neuron_id: open_candidate,
                resolved_candidate.neuron_id: resolved_candidate,
                stale_candidate.neuron_id: stale_candidate,
                reopened_candidate.neuron_id: reopened_candidate,
            },
            alerts=(f"{reopened_candidate.neuron_id}:fragility_detected",),
            admin_log=(),
        )
        registry = registry.mark_watch(stale_candidate.neuron_id, "seguimiento sin mejora")
        registry = registry.pause_candidate_administratively(open_candidate.neuron_id, "revision_manual")
        registry = registry.resolve_alert(resolved_candidate.neuron_id, "alerta_resuelta")
        registry = registry.update_last_admin_action_state(
            resolved_candidate.neuron_id,
            outcome=ACTION_OUTCOME_HELPED,
            review_status=REVIEW_STATUS_RESOLVED,
            alert_status=ALERT_STATUS_RESOLVED,
        )

        open_result = self._run_turn(
            "que revisiones siguen abiertas",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        resolved_result = self._run_turn(
            "que revisiones ya se resolvieron",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        reopened_result = self._run_turn(
            "que alertas se reabrieron",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        helped_result = self._run_turn(
            "que acciones funcionaron",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        stale_result = self._run_turn(
            "que items estan estancados",
            memory={"name": "Ada"},
            routing_registry=registry,
        )

        for result in (
            open_result,
            resolved_result,
            reopened_result,
            helped_result,
            stale_result,
        ):
            self.assertEqual(result.metadata.route, "system_state")
            self.assertFalse(result.metadata.used_model)

        self.assertIn(open_candidate.neuron_id, open_result.response)
        self.assertIn(resolved_candidate.neuron_id, resolved_result.response)
        self.assertIn(reopened_candidate.neuron_id, reopened_result.response)
        self.assertIn(resolved_candidate.neuron_id, helped_result.response)
        self.assertIn(stale_candidate.neuron_id, stale_result.response)

    def test_routing_maintenance_curates_shortlist_and_discardables(self) -> None:
        useful_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:curated_useful:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6"),
            failure_history=(),
            expected_gain=0.32,
            estimated_cost=0.05,
            estimated_latency=40.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        promising_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:curated_promising:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.13,
            estimated_cost=0.16,
            estimated_latency=88.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        discardable_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:curated_discardable:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=("fail-1",),
            expected_gain=0.09,
            estimated_cost=0.24,
            estimated_latency=105.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(useful_candidate)
        self.assertIsNotNone(promising_candidate)
        self.assertIsNotNone(discardable_candidate)

        useful_candidate = replace(useful_candidate, neuron_state=ROUTING_STATE_ACTIVE)
        promising_candidate = replace(promising_candidate, neuron_state=ROUTING_STATE_CANDIDATE)
        discardable_candidate = replace(
            discardable_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            watch_status=True,
            watch_reason="seguimiento sin mejora",
            review_status=REVIEW_STATUS_WATCH,
            review_reason="seguimiento sin mejora",
            review_cycles=2,
            alert_status=ALERT_STATUS_ACKNOWLEDGED,
            alert_cycles=2,
            alerts=("overuse_detected",),
            last_admin_action="mark_watch",
            last_admin_reason="seguimiento_manual",
        )
        registry = build_empty_routing_neuron_registry()
        for candidate in (useful_candidate, promising_candidate, discardable_candidate):
            registry = registry.register_candidate(candidate)
        registry = replace(
            registry,
            active={
                useful_candidate.neuron_id: useful_candidate,
                discardable_candidate.neuron_id: discardable_candidate,
            },
            alerts=(f"{discardable_candidate.neuron_id}:overuse_detected",),
        )

        for index in range(6):
            evidence = build_evidence_record(
                task_signature=useful_candidate.task_signature,
                session_id=f"useful-session-{index}",
                task_profile="technical_reasoning",
                risk_profile="low",
                budget_profile="normal",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route="primary_only",
                activated_components=useful_candidate.activated_components,
                latency_ms=72.0,
                latency_delta=-18.0,
                cost_delta=-0.04,
                quality_delta=0.21,
                verification_delta=0.08,
                consistency_delta=0.05,
                success_label="improved",
                outcome_summary=f"salto util {index}",
                neuron_id=useful_candidate.neuron_id,
                existing_registry=registry,
            )
            registry = registry.register_evidence(evidence)

        report = run_routing_maintenance(registry)
        refreshed_useful = report.registry.candidates[useful_candidate.neuron_id]
        refreshed_promising = report.registry.candidates[promising_candidate.neuron_id]
        refreshed_discardable = report.registry.candidates[discardable_candidate.neuron_id]
        snapshot = build_routing_repertoire_snapshot(report.registry)

        self.assertEqual(refreshed_useful.curation_status, ROUTING_CURATION_USEFUL)
        self.assertEqual(refreshed_useful.selection_status, ROUTING_SELECTION_SHORTLISTED)
        self.assertIn(
            refreshed_useful.influence_readiness,
            {ROUTING_INFLUENCE_SHORTLIST_READY, ROUTING_INFLUENCE_BRIDGE_WATCH},
        )
        self.assertIn(
            refreshed_useful.bridge_preflight_status,
            {ROUTING_BRIDGE_PREFLIGHT_CANDIDATE, ROUTING_BRIDGE_PREFLIGHT_READY},
        )
        self.assertIn(
            refreshed_useful.bridge_rehearsal_status,
            {ROUTING_REHEARSAL_CANDIDATE, ROUTING_REHEARSAL_READY},
        )
        self.assertIn(
            refreshed_useful.cutover_readiness,
            {ROUTING_CUTOVER_NEAR_GO, ROUTING_CUTOVER_GO_CANDIDATE},
        )
        self.assertIn(ROUTING_STACK_FIT_GRANITE, refreshed_useful.conceptual_role_fit)
        self.assertIn(ROUTING_STACK_FIT_OLMO, refreshed_useful.conceptual_role_fit)
        self.assertIn(useful_candidate.neuron_id, report.shortlist_ids)
        self.assertIn(useful_candidate.neuron_id, snapshot.shortlist_ids)
        self.assertIn(useful_candidate.neuron_id, snapshot.useful_ids)
        self.assertIn(useful_candidate.neuron_id, report.bridge_slate_ids)
        self.assertIn(useful_candidate.neuron_id, snapshot.rehearsal_slate_ids)

        self.assertEqual(refreshed_promising.curation_status, ROUTING_CURATION_PROMISING)
        self.assertEqual(refreshed_promising.selection_status, ROUTING_SELECTION_OBSERVED_ONLY)
        self.assertEqual(refreshed_promising.influence_readiness, ROUTING_INFLUENCE_EMERGING)
        self.assertEqual(refreshed_promising.bridge_preflight_status, ROUTING_BRIDGE_PREFLIGHT_DEFERRED)
        self.assertEqual(refreshed_promising.bridge_rehearsal_status, ROUTING_REHEARSAL_DEFERRED)
        self.assertEqual(refreshed_promising.cutover_readiness, ROUTING_CUTOVER_WATCH)
        self.assertIn(ROUTING_STACK_FIT_GRANITE, refreshed_promising.conceptual_role_fit)
        self.assertIn(promising_candidate.neuron_id, snapshot.observed_only_ids)
        self.assertIn(promising_candidate.neuron_id, report.bridge_deferred_ids)
        self.assertIn(promising_candidate.neuron_id, snapshot.rehearsal_deferred_ids)

        self.assertEqual(refreshed_discardable.curation_status, ROUTING_CURATION_DISCARDABLE)
        self.assertEqual(refreshed_discardable.selection_status, ROUTING_SELECTION_DISCARDABLE)
        self.assertTrue(refreshed_discardable.discardable_flag)
        self.assertEqual(
            refreshed_discardable.bridge_preflight_status,
            ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED,
        )
        self.assertEqual(refreshed_discardable.bridge_rehearsal_status, ROUTING_REHEARSAL_NOT_IN_REHEARSAL)
        self.assertEqual(refreshed_discardable.cutover_readiness, ROUTING_CUTOVER_NOT_READY)
        self.assertIn(discardable_candidate.neuron_id, report.stale_ids)
        self.assertIn(discardable_candidate.neuron_id, report.discardable_ids)
        self.assertIn(discardable_candidate.neuron_id, snapshot.discardable_ids)

    def test_system_state_admin_queries_expose_selection_and_bridge_views(self) -> None:
        useful_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:selection_useful:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6"),
            failure_history=(),
            expected_gain=0.29,
            estimated_cost=0.08,
            estimated_latency=58.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        observed_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:selection_observed:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.14,
            estimated_cost=0.16,
            estimated_latency=84.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        noise_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:selection_noise:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=("fail-1",),
            expected_gain=0.08,
            estimated_cost=0.24,
            estimated_latency=110.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        blocked_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:selection_blocked:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=("fail-1",),
            expected_gain=0.18,
            estimated_cost=0.14,
            estimated_latency=76.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(useful_candidate)
        self.assertIsNotNone(observed_candidate)
        self.assertIsNotNone(noise_candidate)
        self.assertIsNotNone(blocked_candidate)

        useful_candidate = replace(
            useful_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.94,
            confidence_tier=ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            stability_label=ROUTING_STABILITY_STABLE,
            successful_activations=6,
            promotion_ready_signal=True,
            readiness_band=ROUTING_READINESS_NEAR_READY,
            readiness_reason="valor sostenido con poco ruido frente a baseline",
            curation_status=ROUTING_CURATION_USEFUL,
            curation_reason="ya muestra valor sostenido, buena higiene administrativa y poco ruido frente a baseline",
            selection_status=ROUTING_SELECTION_SHORTLISTED,
            selection_reason="entró en shortlist por valor sostenido, bajo ruido y señal de influencia útil",
            influence_readiness=ROUTING_INFLUENCE_BRIDGE_WATCH,
            influence_reason="ya merece entrar al puente conceptual hacia V0.39, aunque todavía sin promoción real",
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_READY,
            bridge_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            bridge_rationale="ya puede entrar a la bridge slate: valor sostenido, poco ruido y fit claro al stack verde",
            bridge_blockers=(),
            conceptual_role_fit=(ROUTING_STACK_FIT_SMOLLM2, ROUTING_STACK_FIT_GRANITE, ROUTING_STACK_FIT_OLMO),
            conceptual_fit_reason="encaja como router o micro expert liviano / aporta criterio útil sobre el flujo primary conversacional / muestra afinidad con verificación o control crítico",
            bridge_rehearsal_status=ROUTING_REHEARSAL_READY,
            rehearsal_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            rehearsal_rationale="ya puede entrar a rehearsal: el preflight es robusto y la señal se sostiene con poco ruido",
            rehearsal_blockers=(),
            cutover_readiness=ROUTING_CUTOVER_GO_CANDIDATE,
            cutover_rationale="ya merece un go/no-go administrativo favorable: rehearsal sólido, poco ruido y riesgos controlados",
            rollback_concerns=(),
            action_suggestion="review_bridge_readiness",
            review_status=REVIEW_STATUS_RESOLVED,
            alert_status=ALERT_STATUS_RESOLVED,
            action_outcome=ACTION_OUTCOME_HELPED,
        )
        observed_candidate = replace(
            observed_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.69,
            confidence_tier=ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
            stability_label=ROUTING_STABILITY_IMPROVING,
            readiness_band=ROUTING_READINESS_EMERGING,
            readiness_reason="ya muestra señal útil repetida y estable",
            curation_status=ROUTING_CURATION_PROMISING,
            curation_reason="ya tiene señales útiles, pero todavía necesita más observación antes de entrar en foco fuerte",
            selection_status=ROUTING_SELECTION_OBSERVED_ONLY,
            selection_reason="todavía conviene observarla antes de meterla en shortlist operativa",
            influence_readiness=ROUTING_INFLUENCE_EMERGING,
            influence_reason="todavía conviene mantenerla como señal útil en observación",
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_DEFERRED,
            bridge_priority=ROUTING_REVIEW_PRIORITY_MEDIUM,
            bridge_rationale="todavía tiene valor general, pero no merece puente hasta consolidar shortlist y evidencia",
            bridge_blockers=("todavía fuera de shortlist general", "evidencia insuficiente"),
            conceptual_role_fit=(ROUTING_STACK_FIT_GRANITE,),
            conceptual_fit_reason="aporta criterio útil sobre el flujo primary conversacional",
            bridge_rehearsal_status=ROUTING_REHEARSAL_DEFERRED,
            rehearsal_priority=ROUTING_REVIEW_PRIORITY_MEDIUM,
            rehearsal_rationale="todavía conviene consolidar evidencia y shortlist antes del rehearsal",
            rehearsal_blockers=("confianza todavía no sostenida", "evidencia todavía escasa"),
            cutover_readiness=ROUTING_CUTOVER_WATCH,
            cutover_rationale="todavía conviene observarla para cutover, pero primero debe fortalecer el rehearsal",
            rollback_concerns=("evidencia todavía escasa",),
            action_suggestion="collect_more_bridge_evidence",
        )
        noise_candidate = replace(
            noise_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.43,
            confidence_tier=ROUTING_CONFIDENCE_EARLY_SIGNAL,
            stability_label=ROUTING_STABILITY_DEGRADING,
            readiness_band=ROUTING_READINESS_NOT_READY,
            readiness_reason="todavía arrastra ruido operativo",
            curation_status=ROUTING_CURATION_DISCARDABLE,
            curation_reason="ya acumula ruido o desgaste suficiente como para salir del foco principal",
            selection_status=ROUTING_SELECTION_DISCARDABLE,
            selection_reason="conviene sacarla del foco principal hasta que muestre señal nueva",
            influence_readiness="not_ready",
            influence_reason="todavía no conviene empujar influencia adicional",
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_NOT_CONSIDERED,
            bridge_priority="none",
            bridge_rationale="todavía no tiene base suficiente para entrar en el preflight del puente",
            bridge_blockers=("valor operativo insuficiente",),
            conceptual_role_fit=(ROUTING_STACK_FIT_NEUTRAL,),
            conceptual_fit_reason="todavía no se ve un mapeo claro al stack verde",
            bridge_rehearsal_status=ROUTING_REHEARSAL_NOT_IN_REHEARSAL,
            rehearsal_priority="none",
            rehearsal_rationale="todavía no tiene base suficiente para entrar al rehearsal del puente",
            rehearsal_blockers=("fuera de shortlist general",),
            cutover_readiness=ROUTING_CUTOVER_NOT_READY,
            cutover_rationale="todavía no tiene base suficiente para una evaluación de go/no-go",
            rollback_concerns=("fit conceptual ambiguo", "valor poco portable fuera del contexto actual"),
            discardable_flag=True,
            watch_status=True,
            watch_reason="seguimiento sin mejora",
            review_status=REVIEW_STATUS_STALE,
            review_reason="seguimiento sin mejora",
            action_outcome=ACTION_OUTCOME_NO_CLEAR_CHANGE,
            action_suggestion="deprioritize_temporarily",
        )
        blocked_candidate = replace(
            blocked_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.74,
            confidence_tier=ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
            stability_label=ROUTING_STABILITY_DEGRADING,
            readiness_band=ROUTING_READINESS_EMERGING,
            readiness_reason="ya muestra señal útil repetida y estable",
            curation_status=ROUTING_CURATION_USEFUL,
            curation_reason="ya muestra valor sostenido, pero todavía carga ruido administrativo",
            selection_status=ROUTING_SELECTION_SHORTLISTED,
            selection_reason="entró en shortlist por valor sostenido, pero todavía necesita limpieza adicional",
            influence_readiness=ROUTING_INFLUENCE_SHORTLIST_READY,
            influence_reason="ya merece shortlist operativa por valor sostenido y baja fricción",
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_BLOCKED,
            bridge_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            bridge_rationale="sirve para shortlist general, pero el puente queda bloqueado hasta cerrar ruido o riesgos",
            bridge_blockers=("alertas recientes", "revisión todavía abierta"),
            conceptual_role_fit=(ROUTING_STACK_FIT_GRANITE, ROUTING_STACK_FIT_OLMO),
            conceptual_fit_reason="aporta criterio útil sobre el flujo primary conversacional / muestra afinidad con verificación o control crítico",
            bridge_rehearsal_status=ROUTING_REHEARSAL_BLOCKED,
            rehearsal_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            rehearsal_rationale="el rehearsal queda bloqueado mientras el preflight siga con riesgos abiertos",
            rehearsal_blockers=("alertas recientes", "revisión todavía abierta"),
            cutover_readiness=ROUTING_CUTOVER_BLOCKED,
            cutover_rationale="el go/no-go sigue bloqueado porque rehearsal todavía no está limpio",
            rollback_concerns=("ruido administrativo todavía abierto", "fragilidad operativa"),
            alerts=("fragility_detected",),
            review_status=REVIEW_STATUS_OPEN,
            review_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            review_reason="alerta crítica todavía abierta",
            action_suggestion="resolve_rehearsal_blockers",
        )
        registry = build_empty_routing_neuron_registry()
        for candidate in (useful_candidate, observed_candidate, noise_candidate, blocked_candidate):
            registry = registry.register_candidate(candidate)
        registry = replace(
            registry,
            active={
                useful_candidate.neuron_id: useful_candidate,
                observed_candidate.neuron_id: observed_candidate,
                noise_candidate.neuron_id: noise_candidate,
                blocked_candidate.neuron_id: blocked_candidate,
            },
        )

        useful_result = self._run_turn(
            "que neuronas son las mas utiles",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        shortlist_result = self._run_turn(
            "que neuronas entraron en la shortlist",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        noise_result = self._run_turn(
            "que neuronas siguen siendo ruido",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        bridge_result = self._run_turn(
            "que neuronas se estan acercando al puente de v0.39",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        bridge_ready_result = self._run_turn(
            "que neuronas estan listas para el puente",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        bridge_blocked_result = self._run_turn(
            "que neuronas quedaron bloqueadas para v0.39",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        bridge_deferred_result = self._run_turn(
            "que neuronas estan diferidas",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        bridge_fit_result = self._run_turn(
            "que neuronas tienen mejor compatibilidad con el stack verde",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        rehearsal_result = self._run_turn(
            "muestra la rehearsal slate",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        rehearsal_ready_result = self._run_turn(
            "que neuronas estan listas para rehearsal",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        near_go_result = self._run_turn(
            "que neuronas estan mas cerca del go",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        rollback_result = self._run_turn(
            "que neuronas tienen riesgos de rollback",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        explanation_result = self._run_turn(
            f"por que la neurona {useful_candidate.neuron_id} fue seleccionada",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        bridge_reason_result = self._run_turn(
            f"por que la neurona {observed_candidate.neuron_id} no entra al puente",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        cutover_reason_result = self._run_turn(
            f"por que la neurona {observed_candidate.neuron_id} todavia no entra al go/no-go",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        state_result = self._run_turn(
            "que estado tienes",
            memory={"name": "Ada"},
            routing_registry=registry,
        )

        for result in (
            useful_result,
            shortlist_result,
            noise_result,
            bridge_result,
            bridge_ready_result,
            bridge_blocked_result,
            bridge_deferred_result,
            bridge_fit_result,
            rehearsal_result,
            rehearsal_ready_result,
            near_go_result,
            rollback_result,
            explanation_result,
            bridge_reason_result,
            cutover_reason_result,
        ):
            self.assertEqual(result.metadata.route, "system_state")
            self.assertFalse(result.metadata.used_model)

        self.assertIn(useful_candidate.neuron_id, useful_result.response)
        self.assertIn(useful_candidate.neuron_id, shortlist_result.response)
        self.assertIn(noise_candidate.neuron_id, noise_result.response)
        self.assertIn(useful_candidate.neuron_id, bridge_result.response)
        self.assertIn(useful_candidate.neuron_id, bridge_ready_result.response)
        self.assertIn(blocked_candidate.neuron_id, bridge_blocked_result.response)
        self.assertIn(observed_candidate.neuron_id, bridge_deferred_result.response)
        self.assertIn(useful_candidate.neuron_id, bridge_fit_result.response)
        self.assertIn(useful_candidate.neuron_id, rehearsal_result.response)
        self.assertIn(useful_candidate.neuron_id, rehearsal_ready_result.response)
        self.assertIn(useful_candidate.neuron_id, near_go_result.response)
        self.assertIn(blocked_candidate.neuron_id, rollback_result.response)
        self.assertIn("quedó seleccionada para shortlist", explanation_result.response)
        self.assertIn("no entra todavía al puente", bridge_reason_result.response)
        self.assertIn("blockers", bridge_reason_result.response)
        self.assertIn("todavía no llega a near_go", cutover_reason_result.response)
        self.assertIn("riesgos", cutover_reason_result.response)
        self.assertIn("shortlist", state_result.response)
        self.assertIn("listas", state_result.response)
        self.assertIn("bloqueadas", state_result.response)
        self.assertIn("diferidas", state_result.response)
        self.assertIn("rehearsal", state_result.response)
        self.assertIn("near-go", state_result.response)
        self.assertIn("go", state_result.response)
        self.assertIn("riesgos", state_result.response)
        self.assertIn("descartables", state_result.response)
        self.assertIn("puente", state_result.response)

    def test_routing_maintenance_builds_bridge_preflight_statuses(self) -> None:
        ready_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:bridge_ready:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6"),
            failure_history=(),
            expected_gain=0.28,
            estimated_cost=0.08,
            estimated_latency=55.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        deferred_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:bridge_deferred:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.14,
            estimated_cost=0.14,
            estimated_latency=82.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        blocked_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:bridge_blocked:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=(),
            expected_gain=0.19,
            estimated_cost=0.1,
            estimated_latency=70.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(ready_candidate)
        self.assertIsNotNone(deferred_candidate)
        self.assertIsNotNone(blocked_candidate)

        ready_candidate = replace(ready_candidate, neuron_state=ROUTING_STATE_ACTIVE)
        deferred_candidate = replace(deferred_candidate, neuron_state=ROUTING_STATE_CANDIDATE)
        blocked_candidate = replace(
            blocked_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            alerts=("fragility_detected",),
            review_status=REVIEW_STATUS_OPEN,
            review_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            review_reason="alerta abierta",
        )
        registry = build_empty_routing_neuron_registry()
        for candidate in (ready_candidate, deferred_candidate, blocked_candidate):
            registry = registry.register_candidate(candidate)
        registry = replace(
            registry,
            active={
                ready_candidate.neuron_id: ready_candidate,
                blocked_candidate.neuron_id: blocked_candidate,
            },
            alerts=(f"{blocked_candidate.neuron_id}:fragility_detected",),
        )

        for index in range(5):
            evidence = build_evidence_record(
                task_signature=ready_candidate.task_signature,
                session_id=f"bridge-ready-{index}",
                task_profile="technical_reasoning",
                risk_profile="low",
                budget_profile="normal",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route="primary_only",
                activated_components=ready_candidate.activated_components,
                latency_ms=69.0,
                latency_delta=-16.0,
                cost_delta=-0.03,
                quality_delta=0.18,
                verification_delta=0.07,
                consistency_delta=0.04,
                success_label="improved",
                outcome_summary=f"bridge ready {index}",
                neuron_id=ready_candidate.neuron_id,
                existing_registry=registry,
            )
            registry = registry.register_evidence(evidence)

        report = run_routing_maintenance(registry)
        ready = report.registry.candidates[ready_candidate.neuron_id]
        deferred = report.registry.candidates[deferred_candidate.neuron_id]
        blocked = report.registry.candidates[blocked_candidate.neuron_id]

        self.assertEqual(ready.bridge_preflight_status, ROUTING_BRIDGE_PREFLIGHT_READY)
        self.assertIn(ready_candidate.neuron_id, report.bridge_ready_ids)
        self.assertIn(ready_candidate.neuron_id, report.bridge_slate_ids)
        self.assertEqual(ready.bridge_rehearsal_status, ROUTING_REHEARSAL_READY)
        self.assertIn(ready_candidate.neuron_id, report.rehearsal_ready_ids)
        self.assertIn(ready_candidate.neuron_id, report.rehearsal_slate_ids)
        self.assertEqual(ready.cutover_readiness, ROUTING_CUTOVER_NEAR_GO)
        self.assertIn(ready_candidate.neuron_id, report.cutover_near_go_ids)
        self.assertIn(ROUTING_STACK_FIT_GRANITE, ready.conceptual_role_fit)

        self.assertEqual(deferred.bridge_preflight_status, ROUTING_BRIDGE_PREFLIGHT_DEFERRED)
        self.assertIn(deferred_candidate.neuron_id, report.bridge_deferred_ids)
        self.assertIn("evidencia insuficiente", deferred.bridge_blockers)
        self.assertEqual(deferred.bridge_rehearsal_status, ROUTING_REHEARSAL_DEFERRED)
        self.assertIn(deferred_candidate.neuron_id, report.rehearsal_deferred_ids)
        self.assertEqual(deferred.cutover_readiness, ROUTING_CUTOVER_WATCH)
        self.assertIn(deferred_candidate.neuron_id, report.rollback_risk_ids)

        self.assertEqual(blocked.bridge_preflight_status, ROUTING_BRIDGE_PREFLIGHT_BLOCKED)
        self.assertIn(blocked_candidate.neuron_id, report.bridge_blocked_ids)
        self.assertTrue(any("alertas recientes" == blocker for blocker in blocked.bridge_blockers))
        self.assertEqual(blocked.bridge_rehearsal_status, ROUTING_REHEARSAL_BLOCKED)
        self.assertIn(blocked_candidate.neuron_id, report.rehearsal_blocked_ids)
        self.assertEqual(blocked.cutover_readiness, ROUTING_CUTOVER_BLOCKED)
        self.assertTrue(any("ruido administrativo todavía abierto" == risk for risk in blocked.rollback_concerns))

    def test_routing_maintenance_builds_explicit_rehearsal_and_cutover_statuses(self) -> None:
        go_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:cutover_go:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=tuple(f"ok-{index}" for index in range(1, 9)),
            failure_history=(),
            expected_gain=0.34,
            estimated_cost=0.05,
            estimated_latency=45.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        near_go_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:cutover_near_go:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6"),
            failure_history=(),
            expected_gain=0.28,
            estimated_cost=0.08,
            estimated_latency=55.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        deferred_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:cutover_watch:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.14,
            estimated_cost=0.14,
            estimated_latency=82.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        blocked_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:cutover_blocked:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=(),
            expected_gain=0.19,
            estimated_cost=0.1,
            estimated_latency=70.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(go_candidate)
        self.assertIsNotNone(near_go_candidate)
        self.assertIsNotNone(deferred_candidate)
        self.assertIsNotNone(blocked_candidate)

        go_candidate = replace(go_candidate, neuron_state=ROUTING_STATE_ACTIVE)
        near_go_candidate = replace(near_go_candidate, neuron_state=ROUTING_STATE_ACTIVE)
        deferred_candidate = replace(deferred_candidate, neuron_state=ROUTING_STATE_CANDIDATE)
        blocked_candidate = replace(
            blocked_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            alerts=("fragility_detected",),
            review_status=REVIEW_STATUS_OPEN,
            review_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            review_reason="alerta abierta",
        )
        registry = build_empty_routing_neuron_registry()
        for candidate in (go_candidate, near_go_candidate, deferred_candidate, blocked_candidate):
            registry = registry.register_candidate(candidate)
        registry = replace(
            registry,
            active={
                go_candidate.neuron_id: go_candidate,
                near_go_candidate.neuron_id: near_go_candidate,
                blocked_candidate.neuron_id: blocked_candidate,
            },
            alerts=(f"{blocked_candidate.neuron_id}:fragility_detected",),
        )

        for index in range(7):
            evidence = build_evidence_record(
                task_signature=go_candidate.task_signature,
                session_id=f"go-cutover-{index}",
                task_profile="technical_reasoning",
                risk_profile="low",
                budget_profile="normal",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route="primary_only",
                activated_components=go_candidate.activated_components,
                latency_ms=62.0,
                latency_delta=-20.0,
                cost_delta=-0.05,
                quality_delta=0.26,
                verification_delta=0.09,
                consistency_delta=0.06,
                success_label="improved",
                outcome_summary=f"go candidate {index}",
                neuron_id=go_candidate.neuron_id,
                existing_registry=registry,
            )
            registry = registry.register_evidence(evidence)

        for index in range(5):
            evidence = build_evidence_record(
                task_signature=near_go_candidate.task_signature,
                session_id=f"near-go-{index}",
                task_profile="technical_reasoning",
                risk_profile="low",
                budget_profile="normal",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route="primary_only",
                activated_components=near_go_candidate.activated_components,
                latency_ms=69.0,
                latency_delta=-16.0,
                cost_delta=-0.03,
                quality_delta=0.18,
                verification_delta=0.07,
                consistency_delta=0.04,
                success_label="improved",
                outcome_summary=f"near go {index}",
                neuron_id=near_go_candidate.neuron_id,
                existing_registry=registry,
            )
            registry = registry.register_evidence(evidence)

        report = run_routing_maintenance(registry)
        go_entry = report.registry.candidates[go_candidate.neuron_id]
        near_go_entry = report.registry.candidates[near_go_candidate.neuron_id]
        deferred_entry = report.registry.candidates[deferred_candidate.neuron_id]
        blocked_entry = report.registry.candidates[blocked_candidate.neuron_id]

        self.assertEqual(go_entry.bridge_rehearsal_status, ROUTING_REHEARSAL_READY)
        self.assertEqual(go_entry.cutover_readiness, ROUTING_CUTOVER_GO_CANDIDATE)
        self.assertIn(go_candidate.neuron_id, report.rehearsal_ready_ids)
        self.assertIn(go_candidate.neuron_id, report.cutover_go_candidate_ids)
        self.assertEqual(go_entry.rollback_concerns, ())

        self.assertEqual(near_go_entry.bridge_rehearsal_status, ROUTING_REHEARSAL_READY)
        self.assertEqual(near_go_entry.cutover_readiness, ROUTING_CUTOVER_NEAR_GO)
        self.assertIn(near_go_candidate.neuron_id, report.cutover_near_go_ids)

        self.assertEqual(deferred_entry.bridge_rehearsal_status, ROUTING_REHEARSAL_DEFERRED)
        self.assertEqual(deferred_entry.cutover_readiness, ROUTING_CUTOVER_WATCH)
        self.assertIn(deferred_candidate.neuron_id, report.rehearsal_deferred_ids)
        self.assertIn("evidencia todavía escasa", deferred_entry.rollback_concerns)

        self.assertEqual(blocked_entry.bridge_rehearsal_status, ROUTING_REHEARSAL_BLOCKED)
        self.assertEqual(blocked_entry.cutover_readiness, ROUTING_CUTOVER_BLOCKED)
        self.assertIn(blocked_candidate.neuron_id, report.rehearsal_blocked_ids)
        self.assertTrue(any("ruido administrativo todavía abierto" == risk for risk in blocked_entry.rollback_concerns))

    def test_routing_maintenance_builds_specific_rollback_concerns(self) -> None:
        fragile_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:fragile_risk:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1",),
            failure_history=("fail-1", "fail-2", "fail-3", "fail-4", "fail-5"),
            expected_gain=0.1,
            estimated_cost=0.18,
            estimated_latency=96.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        baseline_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:baseline_risk:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=(),
            expected_gain=0.18,
            estimated_cost=0.08,
            estimated_latency=61.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        neutral_candidate = register_routing_neuron_candidate(
            task_signature="maintenance_routing:neutral_fit:model",
            activated_components=("memory", "maintenance"),
            activation_rule="summarize_recent_logs",
            routing_condition="observe_recent_context",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2"),
            failure_history=(),
            expected_gain=0.11,
            estimated_cost=0.11,
            estimated_latency=64.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        fallback_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:fallback_risk:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=(),
            expected_gain=0.17,
            estimated_cost=0.12,
            estimated_latency=73.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(fragile_candidate)
        self.assertIsNotNone(baseline_candidate)
        self.assertIsNotNone(neutral_candidate)
        self.assertIsNotNone(fallback_candidate)

        registry = build_empty_routing_neuron_registry()
        for candidate in (
            replace(fragile_candidate, neuron_state=ROUTING_STATE_ACTIVE),
            replace(baseline_candidate, neuron_state=ROUTING_STATE_ACTIVE),
            replace(neutral_candidate, neuron_state=ROUTING_STATE_CANDIDATE),
            replace(fallback_candidate, neuron_state=ROUTING_STATE_ACTIVE),
        ):
            registry = registry.register_candidate(candidate)
        registry = replace(
            registry,
            active={
                fragile_candidate.neuron_id: replace(fragile_candidate, neuron_state=ROUTING_STATE_ACTIVE),
                baseline_candidate.neuron_id: replace(baseline_candidate, neuron_state=ROUTING_STATE_ACTIVE),
                fallback_candidate.neuron_id: replace(fallback_candidate, neuron_state=ROUTING_STATE_ACTIVE),
            },
        )

        for index in range(3):
            evidence = build_evidence_record(
                task_signature=baseline_candidate.task_signature,
                session_id=f"baseline-risk-{index}",
                task_profile="technical_reasoning",
                risk_profile="low",
                budget_profile="normal",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route="primary_then_critic",
                activated_components=baseline_candidate.activated_components,
                latency_ms=88.0,
                latency_delta=4.0,
                cost_delta=0.01,
                quality_delta=0.0,
                verification_delta=0.0,
                consistency_delta=0.0,
                success_label="baseline_kept",
                outcome_summary=f"baseline kept {index}",
                neuron_id=baseline_candidate.neuron_id,
                existing_registry=registry,
            )
            registry = registry.register_evidence(evidence)

        for index in range(2):
            evidence = build_evidence_record(
                task_signature=fallback_candidate.task_signature,
                session_id=f"fallback-risk-{index}",
                task_profile="technical_reasoning",
                risk_profile="medium",
                budget_profile="normal",
                baseline_route="primary_then_critic",
                recent_route="primary_then_critic",
                evaluated_route="primary_only",
                activated_components=fallback_candidate.activated_components,
                latency_ms=95.0,
                latency_delta=8.0,
                cost_delta=0.04,
                quality_delta=-0.08,
                verification_delta=-0.03,
                consistency_delta=-0.02,
                success_label="fallback",
                outcome_summary=f"fallback risk {index}",
                neuron_id=fallback_candidate.neuron_id,
                existing_registry=registry,
            )
            registry = registry.register_evidence(evidence)

        report = run_routing_maintenance(registry)
        fragile_entry = report.registry.candidates[fragile_candidate.neuron_id]
        baseline_entry = report.registry.candidates[baseline_candidate.neuron_id]
        neutral_entry = report.registry.candidates[neutral_candidate.neuron_id]
        fallback_entry = report.registry.candidates[fallback_candidate.neuron_id]

        self.assertIn("fragilidad operativa", fragile_entry.rollback_concerns)
        self.assertIn("dependencia excesiva del baseline actual", baseline_entry.rollback_concerns)
        self.assertIn("fit conceptual ambiguo", neutral_entry.rollback_concerns)
        self.assertIn("valor poco portable fuera del contexto actual", neutral_entry.rollback_concerns)
        self.assertIn("demasiados fallbacks recientes", fallback_entry.rollback_concerns)

    def test_system_state_admin_queries_expose_rehearsal_cutover_and_risks(self) -> None:
        go_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:state_cutover_go:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4", "ok-5", "ok-6", "ok-7"),
            failure_history=(),
            expected_gain=0.34,
            estimated_cost=0.05,
            estimated_latency=45.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        watch_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:state_cutover_watch:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3"),
            failure_history=(),
            expected_gain=0.14,
            estimated_cost=0.14,
            estimated_latency=82.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        blocked_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:state_cutover_blocked:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=("fail-1",),
            expected_gain=0.18,
            estimated_cost=0.11,
            estimated_latency=74.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(go_candidate)
        self.assertIsNotNone(watch_candidate)
        self.assertIsNotNone(blocked_candidate)

        go_candidate = replace(
            go_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.9,
            confidence_tier=ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            stability_label=ROUTING_STABILITY_STABLE,
            successful_activations=7,
            promotion_ready_signal=True,
            readiness_band=ROUTING_READINESS_NEAR_READY,
            readiness_reason="valor sostenido con poco ruido frente a baseline",
            curation_status=ROUTING_CURATION_USEFUL,
            curation_reason="ya muestra valor sostenido, buena higiene administrativa y poco ruido frente a baseline",
            selection_status=ROUTING_SELECTION_SHORTLISTED,
            selection_reason="entró en shortlist por valor sostenido, bajo ruido y señal de influencia útil",
            influence_readiness=ROUTING_INFLUENCE_BRIDGE_WATCH,
            influence_reason="ya merece entrar al puente conceptual hacia V0.39, aunque todavía sin promoción real",
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_READY,
            bridge_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            bridge_rationale="ya puede entrar a la bridge slate: valor sostenido, poco ruido y fit claro al stack verde",
            bridge_blockers=(),
            conceptual_role_fit=(ROUTING_STACK_FIT_SMOLLM2, ROUTING_STACK_FIT_GRANITE, ROUTING_STACK_FIT_OLMO),
            conceptual_fit_reason="encaja como router o micro expert liviano / aporta criterio útil sobre el flujo primary conversacional / muestra afinidad con verificación o control crítico",
            bridge_rehearsal_status=ROUTING_REHEARSAL_READY,
            rehearsal_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            rehearsal_rationale="ya puede entrar a rehearsal: el preflight es robusto y la señal se sostiene con poco ruido",
            rehearsal_blockers=(),
            cutover_readiness=ROUTING_CUTOVER_GO_CANDIDATE,
            cutover_rationale="ya merece un go/no-go administrativo favorable: rehearsal sólido, poco ruido y riesgos controlados",
            rollback_concerns=(),
            action_outcome=ACTION_OUTCOME_HELPED,
        )
        watch_candidate = replace(
            watch_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.69,
            confidence_tier=ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
            stability_label=ROUTING_STABILITY_IMPROVING,
            readiness_band=ROUTING_READINESS_EMERGING,
            readiness_reason="ya muestra señal útil repetida y estable",
            curation_status=ROUTING_CURATION_PROMISING,
            curation_reason="ya tiene señales útiles, pero todavía necesita más observación antes de entrar en foco fuerte",
            selection_status=ROUTING_SELECTION_OBSERVED_ONLY,
            selection_reason="todavía conviene observarla antes de meterla en shortlist operativa",
            influence_readiness=ROUTING_INFLUENCE_EMERGING,
            influence_reason="todavía conviene mantenerla como señal útil en observación",
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_DEFERRED,
            bridge_priority=ROUTING_REVIEW_PRIORITY_MEDIUM,
            bridge_rationale="todavía tiene valor general, pero no merece puente hasta consolidar shortlist y evidencia",
            bridge_blockers=("todavía fuera de shortlist general", "evidencia insuficiente"),
            conceptual_role_fit=(ROUTING_STACK_FIT_GRANITE,),
            conceptual_fit_reason="aporta criterio útil sobre el flujo primary conversacional",
            bridge_rehearsal_status=ROUTING_REHEARSAL_DEFERRED,
            rehearsal_priority=ROUTING_REVIEW_PRIORITY_MEDIUM,
            rehearsal_rationale="todavía conviene consolidar evidencia y shortlist antes del rehearsal",
            rehearsal_blockers=("confianza todavía no sostenida", "evidencia todavía escasa"),
            cutover_readiness=ROUTING_CUTOVER_WATCH,
            cutover_rationale="todavía conviene observarla para cutover, pero primero debe fortalecer el rehearsal",
            rollback_concerns=("evidencia todavía escasa",),
            action_suggestion="collect_rehearsal_evidence",
        )
        blocked_candidate = replace(
            blocked_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.72,
            confidence_tier=ROUTING_CONFIDENCE_CONFIRMED_PATTERN,
            stability_label=ROUTING_STABILITY_DEGRADING,
            readiness_band=ROUTING_READINESS_EMERGING,
            readiness_reason="ya muestra señal útil repetida y estable",
            curation_status=ROUTING_CURATION_USEFUL,
            curation_reason="ya muestra valor sostenido, pero todavía carga ruido administrativo",
            selection_status=ROUTING_SELECTION_SHORTLISTED,
            selection_reason="entró en shortlist por valor sostenido, pero todavía necesita limpieza adicional",
            influence_readiness=ROUTING_INFLUENCE_SHORTLIST_READY,
            influence_reason="ya merece shortlist operativa por valor sostenido y baja fricción",
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_BLOCKED,
            bridge_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            bridge_rationale="sirve para shortlist general, pero el puente queda bloqueado hasta cerrar ruido o riesgos",
            bridge_blockers=("alertas recientes", "revisión todavía abierta"),
            conceptual_role_fit=(ROUTING_STACK_FIT_GRANITE, ROUTING_STACK_FIT_OLMO),
            conceptual_fit_reason="aporta criterio útil sobre el flujo primary conversacional / muestra afinidad con verificación o control crítico",
            bridge_rehearsal_status=ROUTING_REHEARSAL_BLOCKED,
            rehearsal_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            rehearsal_rationale="el rehearsal queda bloqueado mientras el preflight siga con riesgos abiertos",
            rehearsal_blockers=("alertas recientes", "revisión todavía abierta"),
            cutover_readiness=ROUTING_CUTOVER_BLOCKED,
            cutover_rationale="el go/no-go sigue bloqueado porque rehearsal todavía no está limpio",
            rollback_concerns=("ruido administrativo todavía abierto", "fragilidad operativa"),
            alerts=("fragility_detected",),
            review_status=REVIEW_STATUS_OPEN,
            review_priority=ROUTING_REVIEW_PRIORITY_HIGH,
            review_reason="alerta crítica todavía abierta",
            action_suggestion="resolve_rehearsal_blockers",
        )
        registry = build_empty_routing_neuron_registry()
        for candidate in (go_candidate, watch_candidate, blocked_candidate):
            registry = registry.register_candidate(candidate)
        registry = replace(
            registry,
            active={
                go_candidate.neuron_id: go_candidate,
                watch_candidate.neuron_id: watch_candidate,
                blocked_candidate.neuron_id: blocked_candidate,
            },
        )

        rehearsal_result = self._run_turn(
            "muestra la rehearsal slate",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        rehearsal_ready_result = self._run_turn(
            "que neuronas estan listas para rehearsal",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        near_go_result = self._run_turn(
            "que neuronas estan mas cerca del go",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        rollback_result = self._run_turn(
            "muestra risks de migracion de routing neuron",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        watch_reason_result = self._run_turn(
            f"por que la neurona {watch_candidate.neuron_id} sigue en watch",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        near_go_reason_result = self._run_turn(
            f"por que la neurona {watch_candidate.neuron_id} no llega a near_go",
            memory={"name": "Ada"},
            routing_registry=registry,
        )

        for result in (
            rehearsal_result,
            rehearsal_ready_result,
            near_go_result,
            rollback_result,
            watch_reason_result,
            near_go_reason_result,
        ):
            self.assertEqual(result.metadata.route, "system_state")
            self.assertFalse(result.metadata.used_model)

        self.assertIn(go_candidate.neuron_id, rehearsal_result.response)
        self.assertIn(go_candidate.neuron_id, rehearsal_ready_result.response)
        self.assertIn(go_candidate.neuron_id, near_go_result.response)
        self.assertIn(blocked_candidate.neuron_id, rollback_result.response)
        self.assertIn("sigue en watch", watch_reason_result.response)
        self.assertIn("riesgos", watch_reason_result.response)
        self.assertIn("near_go", near_go_reason_result.response)
        self.assertIn("todavía conviene observarla", near_go_reason_result.response)

    def test_routing_maintenance_maps_cutover_states_into_launch_statuses(self) -> None:
        report, approved_entry, support_entry, hold_entry, rejected_entry = self._build_launch_test_report()

        self.assertEqual(approved_entry.cutover_readiness, ROUTING_CUTOVER_GO_CANDIDATE)
        self.assertEqual(approved_entry.launch_status, ROUTING_LAUNCH_APPROVED)
        self.assertEqual(approved_entry.cutover_role, ROUTING_ROLE_ROUTER_SUPPORT)
        self.assertIn(approved_entry.neuron_id, report.approved_ids)

        self.assertIn(
            support_entry.cutover_readiness,
            {ROUTING_CUTOVER_NEAR_GO, ROUTING_CUTOVER_GO_CANDIDATE},
        )
        self.assertEqual(support_entry.launch_status, ROUTING_LAUNCH_SUPPORT_ONLY)
        self.assertEqual(support_entry.cutover_role, ROUTING_ROLE_CONTEXT_FILTER)
        self.assertIn(support_entry.neuron_id, report.support_only_ids)

        self.assertEqual(hold_entry.cutover_readiness, ROUTING_CUTOVER_NEAR_GO)
        self.assertEqual(hold_entry.launch_status, ROUTING_LAUNCH_HOLD)
        self.assertEqual(hold_entry.cutover_role, ROUTING_ROLE_ROUTER_SUPPORT)
        self.assertIn(hold_entry.neuron_id, report.hold_ids)

        self.assertIn(
            rejected_entry.cutover_readiness,
            {ROUTING_CUTOVER_NOT_READY, ROUTING_CUTOVER_BLOCKED},
        )
        self.assertEqual(rejected_entry.launch_status, ROUTING_LAUNCH_REJECTED)
        self.assertIn(rejected_entry.neuron_id, report.rejected_ids)
        self.assertTrue(
            {"fit conceptual ambiguo", "cutover readiness blocked"} & set(rejected_entry.no_go_conditions)
        )

    def test_routing_maintenance_assigns_roles_dependencies_and_rollback_plan(self) -> None:
        _, approved_entry, support_entry, hold_entry, _ = self._build_launch_test_report()

        self.assertEqual(approved_entry.cutover_role, ROUTING_ROLE_ROUTER_SUPPORT)
        self.assertIn(
            "requires migration_guard baseline checks",
            approved_entry.dependency_hints,
        )
        self.assertEqual(approved_entry.fallback_target, "baseline_primary_then_critic")
        self.assertTrue(approved_entry.safe_reversion)
        self.assertTrue(approved_entry.rollback_triggers)

        self.assertEqual(support_entry.cutover_role, ROUTING_ROLE_CONTEXT_FILTER)
        self.assertIn("should enter before primary_support", support_entry.dependency_hints)
        self.assertEqual(support_entry.fallback_target, "baseline_primary_only")
        self.assertTrue(support_entry.rollback_triggers)

        self.assertTrue(hold_entry.no_go_conditions)
        self.assertIn("quality drift after launch", approved_entry.rollback_triggers)

    def test_routing_maintenance_builds_launch_dossier_and_cutover_slate(self) -> None:
        report, approved_entry, support_entry, hold_entry, rejected_entry = self._build_launch_test_report()
        dossier = build_routing_launch_dossier(report.registry)

        self.assertEqual(dossier.package_recommendation, "conditional_go")
        self.assertIn(approved_entry.neuron_id, dossier.approved_ids)
        self.assertIn(support_entry.neuron_id, dossier.support_only_ids)
        self.assertIn(hold_entry.neuron_id, dossier.hold_ids)
        self.assertIn(rejected_entry.neuron_id, dossier.rejected_ids)
        self.assertEqual(dossier.activation_order_ids[0], approved_entry.neuron_id)
        self.assertIn(support_entry.neuron_id, dossier.activation_order_ids)
        self.assertTrue(dossier.dependency_map)
        self.assertTrue(dossier.rollback_plan_summary)

        snapshot = build_routing_repertoire_snapshot(report.registry)
        self.assertIn(approved_entry.neuron_id, snapshot.approved_ids)
        self.assertIn(support_entry.neuron_id, snapshot.support_only_ids)
        self.assertIn(hold_entry.neuron_id, snapshot.hold_ids)
        self.assertIn(rejected_entry.neuron_id, snapshot.rejected_ids)
        self.assertIn(approved_entry.neuron_id, snapshot.activation_order_ids)
        self.assertIn(support_entry.neuron_id, snapshot.launch_slate_ids)
        self.assertNotIn(rejected_entry.neuron_id, snapshot.launch_slate_ids)

    def test_system_state_admin_queries_expose_launch_dossier_and_cutover_plan(self) -> None:
        approved_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:state_launch_approved:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=(),
            expected_gain=0.3,
            estimated_cost=0.06,
            estimated_latency=47.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        support_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:state_launch_support:model",
            activated_components=("primary", "memory"),
            activation_rule="compact_context_before_answer",
            routing_condition="compact_context_before_answer",
            intermediate_transform="compacta el contexto antes de responder",
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=(),
            expected_gain=0.22,
            estimated_cost=0.08,
            estimated_latency=55.0,
            neuron_type=ROUTING_TYPE_TRANSFORMATION,
        )
        hold_candidate = register_routing_neuron_candidate(
            task_signature="technical_reasoning:state_launch_hold:model",
            activated_components=("primary", "critic"),
            activation_rule="prefer_primary_only_when_low_risk",
            routing_condition="prefer_primary_only skip_critic low",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2", "ok-3", "ok-4"),
            failure_history=(),
            expected_gain=0.24,
            estimated_cost=0.08,
            estimated_latency=58.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        rejected_candidate = register_routing_neuron_candidate(
            task_signature="maintenance_routing:state_launch_rejected:model",
            activated_components=("memory", "maintenance"),
            activation_rule="summarize_recent_logs",
            routing_condition="observe_recent_context",
            intermediate_transform=None,
            success_history=("ok-1", "ok-2"),
            failure_history=(),
            expected_gain=0.08,
            estimated_cost=0.11,
            estimated_latency=74.0,
            neuron_type=ROUTING_TYPE_CONTROL,
        )
        self.assertIsNotNone(approved_candidate)
        self.assertIsNotNone(support_candidate)
        self.assertIsNotNone(hold_candidate)
        self.assertIsNotNone(rejected_candidate)

        approved_candidate = replace(
            approved_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.9,
            confidence_tier=ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            stability_label=ROUTING_STABILITY_STABLE,
            selection_status=ROUTING_SELECTION_SHORTLISTED,
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_READY,
            bridge_rehearsal_status=ROUTING_REHEARSAL_READY,
            cutover_readiness=ROUTING_CUTOVER_GO_CANDIDATE,
            launch_status=ROUTING_LAUNCH_APPROVED,
            launch_rationale="ya puede entrar al paquete final de cutover con rol claro y riesgos controlados",
            cutover_role=ROUTING_ROLE_ROUTER_SUPPORT,
            cutover_role_reason="encaja como apoyo de routing liviano o micro expert del stack verde",
            activation_order=1,
            activation_order_reason="entra primero dentro del núcleo aprobado del cutover",
            dependency_hints=("requires migration_guard baseline checks",),
            rollback_triggers=("quality drift after launch",),
            fallback_target="baseline_primary_then_critic",
            safe_reversion="volver a baseline_primary_then_critic y sacar la neurona del cutover packet",
            no_go_conditions=(),
        )
        support_candidate = replace(
            support_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.79,
            confidence_tier=ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            stability_label=ROUTING_STABILITY_IMPROVING,
            selection_status=ROUTING_SELECTION_SHORTLISTED,
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_READY,
            bridge_rehearsal_status=ROUTING_REHEARSAL_READY,
            cutover_readiness=ROUTING_CUTOVER_NEAR_GO,
            launch_status=ROUTING_LAUNCH_SUPPORT_ONLY,
            launch_rationale="ya aporta valor como apoyo del cutover, aunque todavía no conviene ponerla en el núcleo",
            cutover_role=ROUTING_ROLE_CONTEXT_FILTER,
            cutover_role_reason="aporta una transformación o filtro previo útil para un cutover controlado",
            activation_order=2,
            activation_order_reason="entra después del núcleo aprobado porque cumple un rol de apoyo",
            dependency_hints=("should enter before primary_support",),
            rollback_triggers=("quality drift after launch",),
            fallback_target="baseline_primary_only",
            safe_reversion="volver a baseline_primary_only y sacar la neurona del cutover packet",
            no_go_conditions=(),
        )
        hold_candidate = replace(
            hold_candidate,
            neuron_state=ROUTING_STATE_ACTIVE,
            global_routing_score=0.8,
            confidence_tier=ROUTING_CONFIDENCE_SUSTAINED_VALUE,
            stability_label=ROUTING_STABILITY_STABLE,
            selection_status=ROUTING_SELECTION_SHORTLISTED,
            bridge_preflight_status=ROUTING_BRIDGE_PREFLIGHT_READY,
            bridge_rehearsal_status=ROUTING_REHEARSAL_READY,
            cutover_readiness=ROUTING_CUTOVER_NEAR_GO,
            launch_status=ROUTING_LAUNCH_HOLD,
            launch_rationale="ya está cerca del go, pero todavía faltan señales o limpieza para aprobarla en la ola final",
            cutover_role=ROUTING_ROLE_ROUTER_SUPPORT,
            no_go_conditions=("close_cutover_gaps",),
            rollback_concerns=("dependencia excesiva del baseline actual",),
        )
        rejected_candidate = replace(
            rejected_candidate,
            neuron_state=ROUTING_STATE_CANDIDATE,
            global_routing_score=0.36,
            confidence_tier=ROUTING_CONFIDENCE_EARLY_SIGNAL,
            stability_label=ROUTING_STABILITY_DEGRADING,
            selection_status=ROUTING_SELECTION_OBSERVED_ONLY,
            cutover_readiness=ROUTING_CUTOVER_NOT_READY,
            launch_status=ROUTING_LAUNCH_REJECTED,
            launch_rationale="por ahora sirve como observación o rehearsal, pero no para el paquete final de V0.39",
            no_go_conditions=("launch packet not justified",),
            rollback_concerns=("fit conceptual ambiguo",),
        )

        registry = build_empty_routing_neuron_registry()
        for candidate in (approved_candidate, support_candidate, hold_candidate, rejected_candidate):
            registry = registry.register_candidate(candidate)
        registry = replace(
            registry,
            active={
                approved_candidate.neuron_id: approved_candidate,
                support_candidate.neuron_id: support_candidate,
                hold_candidate.neuron_id: hold_candidate,
            },
        )

        launch_result = self._run_turn(
            "muestra el launch dossier",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        approved_result = self._run_turn(
            "que neuronas estan aprobadas para v0.39",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        support_result = self._run_turn(
            "que neuronas quedaron support only",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        hold_result = self._run_turn(
            "que neuronas estan on hold",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        rejected_result = self._run_turn(
            "que neuronas fueron rechazadas",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        order_result = self._run_turn(
            "que orden de entrada propone el cutover",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        rollback_plan_result = self._run_turn(
            f"que rollback plan tiene la neurona {approved_candidate.neuron_id}",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        dependencies_result = self._run_turn(
            f"que dependencias tiene la neurona {support_candidate.neuron_id}",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        launch_reason_result = self._run_turn(
            f"por que la neurona {hold_candidate.neuron_id} quedo en hold",
            memory={"name": "Ada"},
            routing_registry=registry,
        )
        state_result = self._run_turn(
            "que estado tienes",
            memory={"name": "Ada"},
            routing_registry=registry,
        )

        for result in (
            launch_result,
            approved_result,
            support_result,
            hold_result,
            rejected_result,
            order_result,
            rollback_plan_result,
            dependencies_result,
            launch_reason_result,
        ):
            self.assertEqual(result.metadata.route, "system_state")
            self.assertFalse(result.metadata.used_model)

        self.assertIn(approved_candidate.neuron_id, launch_result.response)
        self.assertIn("approved", launch_result.response)
        self.assertIn(approved_candidate.neuron_id, approved_result.response)
        self.assertIn(support_candidate.neuron_id, support_result.response)
        self.assertIn(hold_candidate.neuron_id, hold_result.response)
        self.assertIn(rejected_candidate.neuron_id, rejected_result.response)
        self.assertIn(approved_candidate.neuron_id, order_result.response)
        self.assertIn("fallback", rollback_plan_result.response)
        self.assertIn("dependencias", dependencies_result.response.lower())
        self.assertIn("quedó hold", launch_reason_result.response)
        self.assertIn("approved", state_result.response)
        self.assertIn("support", state_result.response)
        self.assertIn("hold", state_result.response)
        self.assertIn("rejected", state_result.response)
        self.assertIn("dossier", state_result.response)

    def test_system_state_launch_dossier_empty_is_valid_and_connected(self) -> None:
        result = self._run_turn(
            "muestra el launch dossier",
            memory={"name": "Ada"},
            routing_registry=build_empty_routing_neuron_registry(),
        )

        self.assertEqual(result.metadata.route, "system_state")
        self.assertFalse(result.metadata.used_model)
        self.assertEqual(result.metadata.action, ACTION_SYSTEM_STATE)
        self.assertEqual(result.metadata.tool, TOOL_SYSTEM_STATE_READER)
        self.assertEqual(result.metadata.tool_kind, "base")
        self.assertEqual(result.metadata.no_model_reason, "resolved_by_system_state")
        self.assertIn("Launch dossier de Routing Neuron V1 hacia V0.39 disponible", result.response)
        self.assertIn("actualmente sin neuronas finalistas", result.response)
        self.assertNotIn("Todavía no veo un launch dossier claro", result.response)

    def test_system_state_final_launch_queries_have_non_null_metadata(self) -> None:
        report, approved_entry, _, _, _ = self._build_launch_test_report()
        registry = report.registry

        for query in (
            "muestra el launch dossier",
            "que neuronas estan aprobadas para v0.39",
            "que orden de entrada propone el cutover",
            f"que rollback plan tiene la neurona {approved_entry.neuron_id}",
        ):
            result = self._run_turn(
                query,
                memory={"name": "Ada"},
                routing_registry=registry,
            )
            self.assertEqual(result.metadata.route, "system_state")
            self.assertIsNotNone(result.metadata.action)
            self.assertEqual(result.metadata.tool, TOOL_SYSTEM_STATE_READER)
            self.assertEqual(result.metadata.tool_kind, "base")
            self.assertEqual(result.metadata.routing_decision, "direct_system_state")
            self.assertEqual(result.metadata.composition_mode, "internal_direct")
            self.assertEqual(result.metadata.task_type, "structured_internal")
            self.assertEqual(result.metadata.no_model_reason, "resolved_by_system_state")
            self.assertIsNotNone(result.metadata.route_trace)
            self.assertIn("route:system_state", result.metadata.route_trace)
            self.assertIn("tool:system_state_reader", result.metadata.route_trace)

    def test_system_state_visible_version_matches_runtime_version(self) -> None:
        with _codex_registry_mocks():
            result = self._run_turn("que estado tienes", memory={"name": "Ada"})

        self.assertIn("version AURA V0.39.6", result.response)
        self.assertNotIn("V0.38.8.1", result.response)
        self.assertIn("checkpoint Codex", result.response)
        self.assertIn("riesgo reciente", result.response)

    def test_system_state_launch_queries_handle_empty_but_valid_cutover_views(self) -> None:
        registry = build_empty_routing_neuron_registry()
        queries = (
            ("que neuronas estan aprobadas para v0.39", "sin neuronas aprobadas para V0.39"),
            ("que neuronas quedaron support only", "sin neuronas support-only"),
            ("que neuronas estan on hold", "sin neuronas on hold"),
            ("que neuronas fueron rechazadas", "sin neuronas rechazadas"),
            ("que orden de entrada propone el cutover", "Cutover plan de Routing Neuron V1 disponible"),
        )

        for query, expected_text in queries:
            result = self._run_turn(
                query,
                memory={"name": "Ada"},
                routing_registry=registry,
            )
            self.assertEqual(result.metadata.route, "system_state")
            self.assertIn(expected_text, result.response)
            self.assertNotIn("Todavía no veo", result.response)

    def test_routing_runtime_conflict_can_apply_when_primary_and_critic_are_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stack = self._prepare_multistack_runtime(root)
            fast_candidate = register_routing_neuron_candidate(
                task_signature="technical_reasoning:technical_explain:model",
                activated_components=("primary", "critic"),
                activation_rule="prefer_primary_only_when_low_risk",
                routing_condition="prefer_primary_only skip_critic low",
                intermediate_transform=None,
                success_history=("ok-1", "ok-2", "ok-3"),
                failure_history=(),
                expected_gain=0.22,
                estimated_cost=0.2,
                estimated_latency=80.0,
                neuron_type=ROUTING_TYPE_CONTROL,
            )
            transform_candidate = register_routing_neuron_candidate(
                task_signature="technical_reasoning:technical_explain:model",
                activated_components=("primary", "critic"),
                activation_rule="compact_before_primary",
                routing_condition="technical_reasoning low",
                intermediate_transform="compacta el contexto antes de responder",
                success_history=("ok-1", "ok-2"),
                failure_history=(),
                expected_gain=0.12,
                estimated_cost=0.15,
                estimated_latency=50.0,
                neuron_type=ROUTING_TYPE_TRANSFORMATION,
            )
            self.assertIsNotNone(fast_candidate)
            self.assertIsNotNone(transform_candidate)

            registry = build_empty_routing_neuron_registry()
            registry = registry.register_candidate(fast_candidate)
            registry = registry.register_candidate(transform_candidate)
            registry = registry.activate_candidate(fast_candidate.neuron_id)
            registry = registry.activate_candidate(transform_candidate.neuron_id)

            routing = decide_routing(
                classify_task(BehaviorPlan(intent="technical_explain"), route_action=ROUTE_MODEL),
                build_default_model_registry(
                    stack["llama"],
                    stack["primary"],
                    critic_llama_path=stack["llama"],
                    critic_model_path=stack["critic"],
                    router_llama_path=stack["llama"],
                    router_model_path=stack["router"],
                    fallback_llama_path=stack["llama"],
                    fallback_model_path=stack["fallback"],
                ),
                plan_critic(TASK_TYPE_TECHNICAL_REASONING),
            )
            runtime_decision = apply_routing_runtime(
                routing,
                task_signature="technical_reasoning:technical_explain:model",
                task_type="technical_reasoning",
                route_action=ROUTE_MODEL,
                risk_profile="low",
                budget_profile="balanced",
                registry=registry,
            )

            self.assertTrue(runtime_decision.applied)
            self.assertEqual(runtime_decision.decision, ROUTING_RUNTIME_APPLIED)
            self.assertEqual(runtime_decision.influence, "skip_critic")
            self.assertTrue(runtime_decision.conflict)

    def test_routing_neuron_v1_checkpoint_document_exists_and_is_complete(self) -> None:
        checkpoint_path = Path("docs/routing_neuron_v1_checkpoint.md")

        self.assertTrue(checkpoint_path.exists())
        content = checkpoint_path.read_text(encoding="utf-8")
        self.assertIn("# Routing Neuron V1 Checkpoint", content)
        self.assertIn("## Estado resumido", content)
        self.assertIn("## Lectura correcta", content)
        self.assertIn("## Semantica runtime", content)
        self.assertIn("## Sendero applied", content)
        self.assertIn("## Compatibilidad", content)
        self.assertIn("## Pendiente V1.x", content)
        self.assertIn("no_candidate_match", content)
        self.assertIn("selected_and_applied", content)
        self.assertIn("skip_critic", content)

    def test_windows_launchers_reference_real_entrypoints_and_defaults(self) -> None:
        launcher = Path("iniciar_aura.bat").read_text(encoding="utf-8")
        vscode_launcher = Path("abrir_aura_en_vscode.bat").read_text(encoding="utf-8")

        self.assertIn("A:\\AURA\\project", launcher)
        self.assertIn("python aura.py", launcher)
        self.assertIn("AURA_MODEL_DIR=A:\\AURA\\models", launcher)
        self.assertIn("AURA_LLAMA_PATH=llama-cli", launcher)
        self.assertNotIn("A:\\AURAproject", launcher)
        self.assertNotIn("python aura.python", launcher)

        self.assertIn("@echo off", vscode_launcher)
        self.assertIn("where code", vscode_launcher)
        self.assertIn("code .", vscode_launcher)
        self.assertNotIn("@echo pff", vscode_launcher)

    def test_system_state_metadata_is_direct_and_non_model(self) -> None:
        with _codex_registry_mocks():
            result = self._run_turn("que estado tienes", memory={"name": "Ada"})
        metadata = result.metadata
        self.assertEqual(metadata.route, "system_state")
        self.assertEqual(metadata.routing_decision, "direct_system_state")
        self.assertEqual(metadata.composition_mode, "internal_direct")
        self.assertEqual(metadata.provider_attempts, ())
        self.assertFalse(metadata.critic_requested)
        self.assertFalse(metadata.critic_used)
        self.assertEqual(metadata.no_model_reason, "resolved_by_system_state")

    def test_repeated_smoke_sequence_stays_stable(self) -> None:
        queries = [
            "que tools internas tienes",
            "que conviene hacer ahora",
            "armame un plan corto",
            "que estado tienes",
            "podemos hacer multimodelo mas adelante?",
            "que tan seguro estas?",
        ]

        first_run = self._run_turn_sequence(queries, memory={"name": "Ada"})
        second_run = self._run_turn_sequence(queries, memory={"name": "Ada"})

        for first_result, second_result in zip(first_run, second_run, strict=True):
            self.assertEqual(first_result.metadata.route, second_result.metadata.route)
            self.assertEqual(
                first_result.metadata.routing_decision,
                second_result.metadata.routing_decision,
            )
            self.assertEqual(
                first_result.metadata.composition_mode,
                second_result.metadata.composition_mode,
            )
            self.assertEqual(
                first_result.metadata.no_model_reason,
                second_result.metadata.no_model_reason,
            )
            if first_result.metadata.route == "system_state":
                self.assertIn("local_primary", first_result.response)
                self.assertIn("local_critic", first_result.response)
                self.assertIn("local_router", first_result.response)
                self.assertIn("local_transitional_fallback", first_result.response)
                self.assertIn("SmolLM2-360M-Instruct", first_result.response)
                self.assertIn("Granite 3.0 1B-A400M-Instruct", first_result.response)
                self.assertIn("OLMo-2-0425-1B-Instruct", first_result.response)
                self.assertIn("Qwen2-1.5B-Instruct", first_result.response)
                self.assertIn("local_primary", second_result.response)
                self.assertIn("local_critic", second_result.response)
                self.assertIn("local_router", second_result.response)
                self.assertIn("local_transitional_fallback", second_result.response)
                self.assertIn("SmolLM2-360M-Instruct", second_result.response)
                self.assertIn("Granite 3.0 1B-A400M-Instruct", second_result.response)
                self.assertIn("OLMo-2-0425-1B-Instruct", second_result.response)
                self.assertIn("Qwen2-1.5B-Instruct", second_result.response)
            else:
                self.assertEqual(first_result.response, second_result.response)


if __name__ == "__main__":
    unittest.main()
