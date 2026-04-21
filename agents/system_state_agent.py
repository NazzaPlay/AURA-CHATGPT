import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.routing_neuron.admin.observable import (
    format_observable_recent_decisions,
    format_observable_runtime_shadow,
    load_observable_routing_summary,
)
from backend.app.routing_neuron.control import (
    load_codex_control_registry,
    summarize_codex_control_status,
    summarize_codex_latest_checkpoint,
)
from backend.app.routing_neuron.admin.rendering import (
    format_runtime_status,
    runtime_history_mode_label,
    runtime_validation_state_text,
)
from backend.app.routing_neuron.schemas.routing_neuron import (
    ROUTING_LIFECYCLE_ACTIVE,
    ROUTING_LIFECYCLE_CANDIDATE,
    ROUTING_LIFECYCLE_OBSERVED_PATTERN,
    ROUTING_LIFECYCLE_PAUSED,
    ROUTING_LIFECYCLE_PROMOTION_READY,
    ROUTING_LIFECYCLE_PROMOTED,
    ROUTING_LIFECYCLE_RETIRED,
    ROUTING_LIFECYCLE_STABILIZED,
    derive_activation_barriers,
    derive_lifecycle_state,
    derive_side_state,
    normalize_confidence_label,
    normalize_neuron_type_label,
)
from config import (
    CRITIC_CALIBRATION_PROFILE,
    DEFAULT_MODEL_ROOT,
    FALLBACK_CALIBRATION_PROFILE,
    get_active_runtime_overrides,
    is_runner_runnable,
    PRIMARY_CALIBRATION_PROFILE,
    ROUTER_CALIBRATION_PROFILE,
)
from .model_registry import (
    ROLE_CRITIC,
    ROLE_MICRO_EXPERT_ROUTER,
    ROLE_PRIMARY,
    build_default_model_registry,
    build_model_bank_governance_snapshot,
    build_stack_health_snapshot,
)
from .model_benchmark import build_benchmark_preparation_snapshot
from .routing_maintenance import (
    build_routing_launch_dossier,
    build_routing_repertoire_snapshot,
)
from .text_matching import (
    matches_normalized_command,
    normalize_command_variants,
    normalize_internal_text,
)

SYSTEM_TARGET_STATE = "state"
SYSTEM_TARGET_MODEL_NAME = "model_name"
SYSTEM_TARGET_MODEL_PATH = "model_path"
SYSTEM_TARGET_LLAMA_PATH = "llama_path"
SYSTEM_TARGET_MODEL_AVAILABLE = "model_available"
SYSTEM_TARGET_VERSION = "version"
SYSTEM_TARGET_LOADED_MEMORY = "loaded_memory"
SYSTEM_TARGET_ROUTING_RECENT = "routing_recent"
SYSTEM_TARGET_ROUTING_ACTIVE = "routing_active"
SYSTEM_TARGET_ROUTING_PAUSED = "routing_paused"
SYSTEM_TARGET_ROUTING_ALERTS = "routing_alerts"
SYSTEM_TARGET_ROUTING_TOP_SCORE = "routing_top_score"
SYSTEM_TARGET_ROUTING_READINESS = "routing_readiness"
SYSTEM_TARGET_ROUTING_WATCH = "routing_watch"
SYSTEM_TARGET_ROUTING_REVIEW = "routing_review"
SYSTEM_TARGET_ROUTING_LOG = "routing_log"
SYSTEM_TARGET_ROUTING_REVIEW_OPEN = "routing_review_open"
SYSTEM_TARGET_ROUTING_REVIEW_RESOLVED = "routing_review_resolved"
SYSTEM_TARGET_ROUTING_REOPENED_ALERTS = "routing_reopened_alerts"
SYSTEM_TARGET_ROUTING_ACTIONS_HELPED = "routing_actions_helped"
SYSTEM_TARGET_ROUTING_STALE = "routing_stale"
SYSTEM_TARGET_ROUTING_USEFUL = "routing_useful"
SYSTEM_TARGET_ROUTING_SHORTLIST = "routing_shortlist"
SYSTEM_TARGET_ROUTING_NOISE = "routing_noise"
SYSTEM_TARGET_ROUTING_BRIDGE = "routing_bridge"
SYSTEM_TARGET_ROUTING_BRIDGE_READY = "routing_bridge_ready"
SYSTEM_TARGET_ROUTING_BRIDGE_BLOCKED = "routing_bridge_blocked"
SYSTEM_TARGET_ROUTING_BRIDGE_DEFERRED = "routing_bridge_deferred"
SYSTEM_TARGET_ROUTING_BRIDGE_FIT = "routing_bridge_fit"
SYSTEM_TARGET_ROUTING_REHEARSAL = "routing_rehearsal"
SYSTEM_TARGET_ROUTING_REHEARSAL_READY = "routing_rehearsal_ready"
SYSTEM_TARGET_ROUTING_CUTOVER_NEAR_GO = "routing_cutover_near_go"
SYSTEM_TARGET_ROUTING_ROLLBACK_RISKS = "routing_rollback_risks"
SYSTEM_TARGET_ROUTING_LAUNCH_DOSSIER = "routing_launch_dossier"
SYSTEM_TARGET_ROUTING_APPROVED = "routing_approved"
SYSTEM_TARGET_ROUTING_SUPPORT_ONLY = "routing_support_only"
SYSTEM_TARGET_ROUTING_HOLD = "routing_hold"
SYSTEM_TARGET_ROUTING_REJECTED = "routing_rejected"
SYSTEM_TARGET_ROUTING_ACTIVATION_ORDER = "routing_activation_order"
SYSTEM_TARGET_ROUTING_ROLLBACK_PLAN = "routing_rollback_plan"
SYSTEM_TARGET_ROUTING_DEPENDENCIES = "routing_dependencies"
SYSTEM_TARGET_ROUTING_LAUNCH_REASON = "routing_launch_reason"
SYSTEM_TARGET_ROUTING_SELECTION_REASON = "routing_selection_reason"
SYSTEM_TARGET_ROUTING_BRIDGE_REASON = "routing_bridge_reason"
SYSTEM_TARGET_ROUTING_CUTOVER_REASON = "routing_cutover_reason"
SYSTEM_TARGET_ROUTING_CHECKPOINT = "routing_checkpoint"
SYSTEM_TARGET_CODEX_LATEST = "codex_latest"
SYSTEM_TARGET_CODEX_STATUS = "codex_status"
SYSTEM_TARGET_CODEX_CHANGES = "codex_changes"
SYSTEM_TARGET_CODEX_DEBTS = "codex_debts"
SYSTEM_TARGET_CODEX_CLOSED_VERSION = "codex_closed_version"
SYSTEM_TARGET_CODEX_PENDING = "codex_pending"
SYSTEM_TARGET_CODEX_STABLE = "codex_stable"
SYSTEM_TARGET_CODEX_WEAK = "codex_weak"
SYSTEM_TARGET_CODEX_RISK_NOW = "codex_risk_now"
SYSTEM_TARGET_CODEX_RECOMMENDED = "codex_recommended"
SYSTEM_TARGET_CODEX_REVIEW_NOW = "codex_review_now"
SYSTEM_TARGET_CODEX_PLAN_NOW = "codex_plan_now"
SYSTEM_TARGET_CODEX_DO_NOT_TOUCH = "codex_do_not_touch"
SYSTEM_TARGET_CODEX_MODEL_CHOICE = "codex_model_choice"


def build_routing_neuron_admin_state(registry):
    from backend.app.routing_neuron.admin.repertoire import build_admin_state

    return build_admin_state(registry)


def get_default_routing_registry():
    from backend.app.routing_neuron.core.runtime import get_default_routing_registry as runtime_get_default_routing_registry

    return runtime_get_default_routing_registry()

MODEL_AVAILABLE_TOKEN_CORRECTIONS = {
    "modelos": "modelo",
    "tenes": "tienes",
}

STATE_QUERY_COMMANDS = normalize_command_variants(
    {
        "que estado tienes",
        "cual es tu estado",
        "muestra tu estado",
        "muestrame tu estado",
        "mostra tu estado",
        "mostrame tu estado",
    }
)
MODEL_NAME_QUERY_COMMANDS = normalize_command_variants(
    {
        "que modelo estas usando",
        "que modelo usas",
        "que modelo tienes configurado",
    }
)
MODEL_PATH_QUERY_COMMANDS = normalize_command_variants(
    {
        "que ruta de modelo tienes",
        "muestra tu ruta de modelo",
        "muestrame tu ruta de modelo",
        "mostrame tu ruta de modelo",
    }
)
LLAMA_PATH_QUERY_COMMANDS = normalize_command_variants(
    {
        "que ruta de llama tienes",
        "que ruta de llama cli tienes",
        "muestra tu ruta de llama",
        "muestrame tu ruta de llama",
        "mostrame tu ruta de llama",
    }
)
MODEL_AVAILABLE_QUERY_COMMANDS = normalize_command_variants(
    {
        "tienes modelo disponible",
        "tenes modelo disponible",
        "tienes modelos disponible",
        "tenes modelos disponible",
        "el modelo esta disponible",
        "esta disponible el modelo",
    },
    token_corrections=MODEL_AVAILABLE_TOKEN_CORRECTIONS,
)
VERSION_QUERY_COMMANDS = normalize_command_variants(
    {
        "que version eres",
        "que version tienes",
        "cual es tu version",
        "mostra la version",
        "mostra tu version",
        "muestra la version",
        "muestra tu version",
        "muestrame la version",
        "muestrame tu version",
        "mostrame la version",
        "mostrame tu version",
    }
)
LOADED_MEMORY_QUERY_COMMANDS = normalize_command_variants(
    {
        "que memoria tienes cargada",
        "muestra tu memoria cargada",
        "muestra la memoria cargada",
        "muestrame tu memoria cargada",
        "muestrame la memoria cargada",
        "mostra tu memoria cargada",
        "mostra la memoria cargada",
        "mostrame tu memoria cargada",
        "mostrame la memoria cargada",
    }
)
ROUTING_RECENT_QUERY_COMMANDS = normalize_command_variants(
    {
        "muestra actividad reciente de routing neuron",
        "muestrame actividad reciente de routing neuron",
        "mostrame actividad reciente de routing neuron",
        "que actividad reciente tiene routing neuron",
        "que actividad reciente tienen tus neuronas",
    }
)
ROUTING_ACTIVE_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas tienes activas",
        "muestra tus neuronas activas",
        "muestrame tus neuronas activas",
        "mostrame tus neuronas activas",
    }
)
ROUTING_PAUSED_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas estan pausadas",
        "muestra neuronas pausadas",
        "muestrame neuronas pausadas",
        "mostrame neuronas pausadas",
    }
)
ROUTING_ALERTS_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas tienen alertas",
        "que alertas siguen abiertas",
        "muestra alertas abiertas de routing neuron",
        "muestrame alertas abiertas de routing neuron",
        "mostrame alertas abiertas de routing neuron",
        "muestra alertas de routing neuron",
        "muestrame alertas de routing neuron",
        "mostrame alertas de routing neuron",
    }
)
ROUTING_TOP_SCORE_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas tienen mejor score",
        "muestra tus neuronas con mejor score",
        "muestrame tus neuronas con mejor score",
        "mostrame tus neuronas con mejor score",
    }
)
ROUTING_READINESS_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas se estan acercando a promocion",
        "que neuronas tienen readiness",
        "muestra neuronas cerca de promocion",
        "muestrame neuronas cerca de promocion",
        "mostrame neuronas cerca de promocion",
    }
)
ROUTING_WATCH_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas estan en watch",
        "muestra neuronas en watch",
        "muestrame neuronas en watch",
        "mostrame neuronas en watch",
    }
)
ROUTING_REVIEW_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas requieren revision",
        "que neuronas merecen revision",
        "muestra neuronas para revision",
        "muestrame neuronas para revision",
        "mostrame neuronas para revision",
    }
)
ROUTING_LOG_QUERY_COMMANDS = normalize_command_variants(
    {
        "muestra la bitacora de routing neuron",
        "muestrame la bitacora de routing neuron",
        "mostrame la bitacora de routing neuron",
        "muestra acciones recientes de routing neuron",
        "muestrame acciones recientes de routing neuron",
        "mostrame acciones recientes de routing neuron",
    }
)
ROUTING_REVIEW_OPEN_QUERY_COMMANDS = normalize_command_variants(
    {
        "que revisiones siguen abiertas",
        "muestra revisiones abiertas de routing neuron",
        "muestrame revisiones abiertas de routing neuron",
        "mostrame revisiones abiertas de routing neuron",
    }
)
ROUTING_REVIEW_RESOLVED_QUERY_COMMANDS = normalize_command_variants(
    {
        "que revisiones ya se resolvieron",
        "muestra revisiones resueltas de routing neuron",
        "muestrame revisiones resueltas de routing neuron",
        "mostrame revisiones resueltas de routing neuron",
    }
)
ROUTING_REOPENED_ALERTS_QUERY_COMMANDS = normalize_command_variants(
    {
        "que alertas se reabrieron",
        "muestra alertas reabiertas de routing neuron",
        "muestrame alertas reabiertas de routing neuron",
        "mostrame alertas reabiertas de routing neuron",
    }
)
ROUTING_ACTIONS_HELPED_QUERY_COMMANDS = normalize_command_variants(
    {
        "que acciones funcionaron",
        "muestra acciones administrativas que funcionaron",
        "muestrame acciones administrativas que funcionaron",
        "mostrame acciones administrativas que funcionaron",
    }
)
ROUTING_STALE_QUERY_COMMANDS = normalize_command_variants(
    {
        "que items estan estancados",
        "que neuronas siguen en watch sin mejorar",
        "muestra items estancados de routing neuron",
        "muestrame items estancados de routing neuron",
        "mostrame items estancados de routing neuron",
    }
)
ROUTING_USEFUL_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas son las mas utiles",
        "muestra tus neuronas mas utiles",
        "muestrame tus neuronas mas utiles",
        "mostrame tus neuronas mas utiles",
    }
)
ROUTING_SHORTLIST_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas entraron en la shortlist",
        "muestra la shortlist de routing neuron",
        "muestrame la shortlist de routing neuron",
        "mostrame la shortlist de routing neuron",
    }
)
ROUTING_NOISE_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas siguen siendo ruido",
        "que neuronas no deberian seguir en foco",
        "muestra neuronas descartables de routing neuron",
        "muestrame neuronas descartables de routing neuron",
        "mostrame neuronas descartables de routing neuron",
    }
)
ROUTING_BRIDGE_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas se estan acercando al puente de v0.39",
        "muestra la bridge slate",
        "muestrame la bridge slate",
        "mostrame la bridge slate",
        "muestra neuronas cerca del puente v0.39",
        "muestrame neuronas cerca del puente v0.39",
        "mostrame neuronas cerca del puente v0.39",
    }
)
ROUTING_BRIDGE_READY_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas estan listas para el puente",
        "que neuronas estan listas para v0.39",
        "muestra neuronas listas para el puente",
        "muestrame neuronas listas para el puente",
        "mostrame neuronas listas para el puente",
    }
)
ROUTING_BRIDGE_BLOCKED_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas quedaron bloqueadas para v0.39",
        "muestra neuronas bloqueadas para v0.39",
        "muestrame neuronas bloqueadas para v0.39",
        "mostrame neuronas bloqueadas para v0.39",
    }
)
ROUTING_BRIDGE_DEFERRED_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas estan diferidas",
        "muestra neuronas diferidas para el puente",
        "muestrame neuronas diferidas para el puente",
        "mostrame neuronas diferidas para el puente",
    }
)
ROUTING_BRIDGE_FIT_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas tienen mejor compatibilidad con el stack verde",
        "muestra neuronas con mejor compatibilidad con el stack verde",
        "muestrame neuronas con mejor compatibilidad con el stack verde",
        "mostrame neuronas con mejor compatibilidad con el stack verde",
    }
)
ROUTING_REHEARSAL_QUERY_COMMANDS = normalize_command_variants(
    {
        "muestra la rehearsal slate",
        "muestrame la rehearsal slate",
        "mostrame la rehearsal slate",
        "que neuronas estan en rehearsal",
    }
)
ROUTING_REHEARSAL_READY_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas estan listas para rehearsal",
        "muestra neuronas listas para rehearsal",
        "muestrame neuronas listas para rehearsal",
        "mostrame neuronas listas para rehearsal",
    }
)
ROUTING_CUTOVER_NEAR_GO_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas estan mas cerca del go",
        "que neuronas estan mas cerca del go no go",
        "muestra neuronas cerca del go",
        "muestrame neuronas cerca del go",
        "mostrame neuronas cerca del go",
    }
)
ROUTING_ROLLBACK_RISKS_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas tienen riesgos de rollback",
        "muestra risks de migracion de routing neuron",
        "muestrame risks de migracion de routing neuron",
        "mostrame risks de migracion de routing neuron",
        "muestra riesgos de migracion de routing neuron",
        "muestrame riesgos de migracion de routing neuron",
        "mostrame riesgos de migracion de routing neuron",
        "muestra riesgos de rollback de routing neuron",
        "muestrame riesgos de rollback de routing neuron",
        "mostrame riesgos de rollback de routing neuron",
    }
)
ROUTING_LAUNCH_DOSSIER_QUERY_COMMANDS = normalize_command_variants(
    {
        "muestra el launch dossier",
        "muestrame el launch dossier",
        "mostrame el launch dossier",
        "muestra el decision pack de routing neuron",
        "muestrame el decision pack de routing neuron",
        "mostrame el decision pack de routing neuron",
        "muestra el cutover packet",
        "muestrame el cutover packet",
        "mostrame el cutover packet",
    }
)
ROUTING_APPROVED_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas estan aprobadas para v0.39",
        "muestra neuronas aprobadas para v0.39",
        "muestrame neuronas aprobadas para v0.39",
        "mostrame neuronas aprobadas para v0.39",
    }
)
ROUTING_SUPPORT_ONLY_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas quedaron support only",
        "que neuronas quedaron support-only",
        "muestra neuronas support only",
        "muestrame neuronas support only",
        "mostrame neuronas support only",
    }
)
ROUTING_HOLD_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas estan on hold",
        "muestra neuronas on hold",
        "muestrame neuronas on hold",
        "mostrame neuronas on hold",
    }
)
ROUTING_REJECTED_QUERY_COMMANDS = normalize_command_variants(
    {
        "que neuronas fueron rechazadas",
        "muestra neuronas rechazadas",
        "muestrame neuronas rechazadas",
        "mostrame neuronas rechazadas",
    }
)
ROUTING_ACTIVATION_ORDER_QUERY_COMMANDS = normalize_command_variants(
    {
        "que orden de entrada propone el cutover",
        "muestra el orden de entrada del cutover",
        "muestrame el orden de entrada del cutover",
        "mostrame el orden de entrada del cutover",
        "muestra activation order de routing neuron",
        "muestrame activation order de routing neuron",
        "mostrame activation order de routing neuron",
    }
)
ROUTING_CHECKPOINT_QUERY_COMMANDS = normalize_command_variants(
    {
        "checkpoint routing neuron",
        "muestra el checkpoint de routing neuron",
        "muestrame el checkpoint de routing neuron",
        "mostrame el checkpoint de routing neuron",
        "resumen ejecutivo de routing neuron",
    }
)
CODEX_LATEST_QUERY_COMMANDS = normalize_command_variants(
    {
        "ultimo trabajo de codex",
        "resumen del ultimo trabajo de codex",
        "ultimo checkpoint de codex",
        "muestra el ultimo trabajo de codex",
        "muestrame el ultimo trabajo de codex",
        "mostrame el ultimo trabajo de codex",
    }
)
CODEX_STATUS_QUERY_COMMANDS = normalize_command_variants(
    {
        "estado del registro de codex",
        "estado del codex control registry",
        "estado del registro de trabajo de codex",
        "muestra el estado del registro de codex",
        "muestrame el estado del registro de codex",
        "mostrame el estado del registro de codex",
    }
)
CODEX_CHANGES_QUERY_COMMANDS = normalize_command_variants(
    {
        "que cambio codex",
        "que cambios hizo codex",
        "que modifico codex",
        "muestra que cambio codex",
        "muestrame que cambio codex",
        "mostrame que cambio codex",
    }
)
CODEX_DEBTS_QUERY_COMMANDS = normalize_command_variants(
    {
        "ultima deuda de codex",
        "que deuda dejo codex",
        "que deuda tiene codex",
        "muestra la ultima deuda de codex",
        "muestrame la ultima deuda de codex",
        "mostrame la ultima deuda de codex",
    }
)
CODEX_CLOSED_VERSION_QUERY_COMMANDS = normalize_command_variants(
    {
        "que version cerro codex",
        "que version dejo cerrada codex",
        "ultima version cerrada por codex",
        "muestra la ultima version cerrada por codex",
        "muestrame la ultima version cerrada por codex",
        "mostrame la ultima version cerrada por codex",
    }
)
CODEX_PENDING_QUERY_COMMANDS = normalize_command_variants(
    {
        "que quedo pendiente",
        "que quedo pendiente en codex",
        "que dejo pendiente codex",
        "muestra lo pendiente de codex",
        "muestrame lo pendiente de codex",
        "mostrame lo pendiente de codex",
    }
)
CODEX_STABLE_QUERY_COMMANDS = normalize_command_variants(
    {
        "que esta consolidado",
        "que esta estable",
        "que sigue verde",
    }
)
CODEX_WEAK_QUERY_COMMANDS = normalize_command_variants(
    {
        "que quedo debil",
        "que sigue flojo",
        "que sigue debil",
    }
)
CODEX_RISK_QUERY_COMMANDS = normalize_command_variants(
    {
        "que riesgos ves",
        "cual es el riesgo actual",
        "que riesgo ves ahora",
    }
)
CODEX_RECOMMENDED_QUERY_COMMANDS = normalize_command_variants(
    {
        "que sigue ahora",
        "que recomienda rn ahora",
        "que recomienda routing neuron ahora",
        "que tocarias primero",
        "que parte del sistema tocarias",
    }
)
CODEX_REVIEW_NOW_QUERY_COMMANDS = normalize_command_variants(
    {
        "que revisarias",
        "que revisarias ahora",
    }
)
CODEX_PLAN_NOW_QUERY_COMMANDS = normalize_command_variants(
    {
        "como lo dividirias",
    }
)
CODEX_DO_NOT_TOUCH_QUERY_COMMANDS = normalize_command_variants(
    {
        "que no tocarias todavia",
        "que no tocarias aun",
    }
)
CODEX_MODEL_CHOICE_QUERY_COMMANDS = normalize_command_variants(
    {
        "que modelo usarias para esto",
        "que modelo conviene para esto",
    }
)
ROUTING_SELECTION_REASON_RE = re.compile(
    r"^\s*por\s+que(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)\s+fue\s+seleccionada\s*$",
    re.IGNORECASE,
)
ROUTING_BRIDGE_REASON_RE = re.compile(
    r"^\s*por\s+que(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)\s+no\s+entra\s+al\s+puente\s*$",
    re.IGNORECASE,
)
ROUTING_CUTOVER_REASON_RE = re.compile(
    r"^\s*por\s+que(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)\s+todavia\s+no\s+entra\s+al\s+go(?:\s*[-/ ]\s*no\s*[-/ ]\s*go)?\s*$",
    re.IGNORECASE,
)
ROUTING_CUTOVER_WATCH_REASON_RE = re.compile(
    r"^\s*por\s+que(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)\s+sigue\s+en\s+watch\s*$",
    re.IGNORECASE,
)
ROUTING_CUTOVER_NEAR_GO_REASON_RE = re.compile(
    r"^\s*por\s+que(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)\s+no\s+llega\s+a\s+near[_ -]?go\s*$",
    re.IGNORECASE,
)
ROUTING_ROLLBACK_PLAN_RE = re.compile(
    r"^\s*que\s+rollback\s+plan\s+tiene(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)\s*$",
    re.IGNORECASE,
)
ROUTING_DEPENDENCIES_RE = re.compile(
    r"^\s*que\s+dependencias\s+tiene(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)\s*$",
    re.IGNORECASE,
)
ROUTING_LAUNCH_REASON_RE = re.compile(
    r"^\s*por\s+que(?:\s+la)?\s+neurona\s+(?P<neuron_id>[A-Za-z0-9:_-]+)\s+(?:fue\s+aprobada(?:\s+para\s+v0\.39)?|quedo\s+support(?:[- ]?only)?|quedo\s+en\s+hold|fue\s+rechazada)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SystemStateCommand:
    target: str
    neuron_id: str | None = None


def _contains_all_phrases(normalized_input: str, *phrases: str) -> bool:
    return all(phrase in normalized_input for phrase in phrases)


def _matches_state_query(normalized_input: str) -> bool:
    if normalized_input in STATE_QUERY_COMMANDS:
        return True

    if "estado" not in normalized_input:
        return False

    if "cual es tu estado" in normalized_input:
        return True

    return "tu estado" in normalized_input and any(
        marker in normalized_input
        for marker in ("muestra", "muestrame", "mostra", "mostrame", "ver")
    )


def _matches_recent_routing_query(normalized_input: str) -> bool:
    return normalized_input in ROUTING_RECENT_QUERY_COMMANDS or (
        _contains_all_phrases(normalized_input, "routing neuron", "actividad")
        and "reciente" in normalized_input
    )


def _matches_launch_dossier_query(normalized_input: str) -> bool:
    return normalized_input in ROUTING_LAUNCH_DOSSIER_QUERY_COMMANDS or any(
        phrase in normalized_input
        for phrase in ("launch dossier", "decision pack", "cutover packet")
    )


def _matches_routing_checkpoint_query(normalized_input: str) -> bool:
    return normalized_input in ROUTING_CHECKPOINT_QUERY_COMMANDS or (
        "checkpoint" in normalized_input and "routing neuron" in normalized_input
    )


def _matches_codex_latest_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_LATEST_QUERY_COMMANDS or (
        "codex" in normalized_input
        and (
            "ultimo trabajo" in normalized_input
            or "ultimo checkpoint" in normalized_input
            or "ultimo run" in normalized_input
        )
    )


def _matches_codex_status_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_STATUS_QUERY_COMMANDS or (
        "codex" in normalized_input
        and "registro" in normalized_input
        and "estado" in normalized_input
    )


def _matches_codex_changes_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_CHANGES_QUERY_COMMANDS or (
        "codex" in normalized_input
        and any(
            phrase in normalized_input
            for phrase in ("que cambio", "que cambios", "que modifico", "que tocaste")
        )
    )


def _matches_codex_debts_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_DEBTS_QUERY_COMMANDS or (
        "codex" in normalized_input
        and any(phrase in normalized_input for phrase in ("deuda", "deudas", "riesgo", "riesgos"))
    )


def _matches_codex_closed_version_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_CLOSED_VERSION_QUERY_COMMANDS or (
        "codex" in normalized_input
        and "version" in normalized_input
        and any(phrase in normalized_input for phrase in ("cerro", "cerrada", "cerrado"))
    )


def _matches_codex_pending_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_PENDING_QUERY_COMMANDS or (
        "codex" in normalized_input
        and any(phrase in normalized_input for phrase in ("pendiente", "abierto", "abierta"))
    )


def _matches_codex_stable_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_STABLE_QUERY_COMMANDS


def _matches_codex_weak_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_WEAK_QUERY_COMMANDS


def _matches_codex_risk_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_RISK_QUERY_COMMANDS


def _matches_codex_recommended_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_RECOMMENDED_QUERY_COMMANDS


def _matches_codex_review_now_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_REVIEW_NOW_QUERY_COMMANDS


def _matches_codex_plan_now_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_PLAN_NOW_QUERY_COMMANDS


def _matches_codex_do_not_touch_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_DO_NOT_TOUCH_QUERY_COMMANDS


def _matches_codex_model_choice_query(normalized_input: str) -> bool:
    return normalized_input in CODEX_MODEL_CHOICE_QUERY_COMMANDS


def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def _format_compact_items(items: list[str], *, limit: int = 4) -> str:
    if not items:
        return "sin elementos"

    if len(items) <= limit:
        return _format_items(items)

    visible_items = items[:limit]
    hidden_count = len(items) - limit
    return f"{_format_items(visible_items)} y {hidden_count} más"


def _build_memory_summary(memory: dict[str, Any]) -> str:
    parts = []

    if memory.get("name"):
        parts.append(f"nombre: {memory['name']}")

    if memory.get("work"):
        parts.append(f"trabajo: {memory['work']}")

    if memory.get("interests"):
        parts.append(f"gustos: {_format_items(memory['interests'])}")

    if memory.get("preferences"):
        parts.append(f"preferencias: {_format_items(memory['preferences'])}")

    if not parts:
        return "sin datos cargados"

    return "; ".join(parts)


def _path_exists(path_value: str) -> bool:
    if not path_value:
        return False

    return Path(path_value).expanduser().exists()


def _llama_status_text(llama_path: str) -> str:
    if not _path_exists(llama_path):
        return "no disponible"

    if is_runner_runnable(llama_path):
        return "disponible"

    return "existe, pero no es ejecutable"


def _model_status_text(model_path: str) -> str:
    if _path_exists(model_path):
        return "disponible"

    return "no disponible"


def _availability_reason_text(reason: str | None) -> str:
    return {
        None: "sin diagnóstico extra",
        "runner_missing": "runner ausente",
        "runner_not_executable": "runner no ejecutable",
        "model_missing": "modelo ausente",
    }.get(reason, reason or "sin diagnóstico extra")


def _provider_state_text(
    descriptor,
    *,
    active: bool = False,
    fallback: bool = False,
) -> str:
    if descriptor is None:
        return "sin provider"

    states = ["configurado"]
    if descriptor.availability:
        states.append("usable ahora")
    else:
        states.append(
            f"no usable ahora ({_availability_reason_text(descriptor.availability_reason)})"
        )

    if active:
        states.append("activo")

    if fallback:
        states.append("fallback transicional")

    return ", ".join(states)


def _format_stack_health(snapshot) -> str:
    parts = [snapshot.health, f"pressure {snapshot.fallback_pressure}"]

    if snapshot.partial_stack:
        parts.append("partial_stack")

    if snapshot.missing_roles:
        role_labels = [
            role.replace("_verifier", "").replace("_", " ")
            for role in snapshot.missing_roles
        ]
        parts.append(f"faltan {_format_items(role_labels)}")

    return ", ".join(parts)


def _summarize_policy_entries(entries: tuple[Any, ...], *, limit: int = 4) -> str:
    model_ids = [
        getattr(entry, "model_id", None)
        for entry in entries
        if getattr(entry, "model_id", None)
    ]
    return _format_compact_items(model_ids, limit=limit)


def _build_runtime_override_summary() -> str:
    active_overrides = list(get_active_runtime_overrides())
    if active_overrides:
        return f"overrides activas {_format_compact_items(active_overrides, limit=3)}"

    default_model_root = str(DEFAULT_MODEL_ROOT)
    return (
        "sin overrides activas; defaults Windows listos con "
        f"AURA_MODEL_DIR={default_model_root} y PATH/llama-cli"
    )


def _format_codex_control_inline(codex_control: Any) -> str:
    if getattr(codex_control, "entry_count", 0) == 0 or not getattr(codex_control, "latest_run_id", None):
        return "registro Codex vacio, sin iteraciones consolidadas todavia"

    version = getattr(codex_control, "latest_version", None) or "sin version"
    status = getattr(codex_control, "latest_status", None) or "sin estado"
    tests = getattr(codex_control, "latest_tests_status", None) or "not_run"
    smokes = getattr(codex_control, "latest_smokes_status", None) or "not_run"
    runtime_health = getattr(codex_control, "latest_runtime_health", None) or "unknown"
    risk = getattr(codex_control, "latest_risk", None) or "unknown"
    checkpoint = getattr(codex_control, "latest_checkpoint_short", None) or "sin checkpoint breve"
    return (
        f"registro Codex activo con {codex_control.entry_count} iteraciones; "
        f"ultimo run {codex_control.latest_run_id} para V{version} ({status}), "
        f"tests {tests}, smokes {smokes}, runtime {runtime_health}, riesgo {risk}; checkpoint {checkpoint}"
    )


def _format_codex_open_debts(codex_control: Any, *, limit: int = 3) -> str:
    open_debts = list(getattr(codex_control, "latest_open_debts", ()) or ())
    if not open_debts:
        return "sin deuda abierta declarada"
    return _format_compact_items(open_debts, limit=limit)


def _build_codex_registry_response(
    *,
    include_changes: bool = False,
    status_only: bool = False,
    debts_only: bool = False,
    closed_version_only: bool = False,
    pending_only: bool = False,
) -> str:
    registry = load_codex_control_registry()
    latest = registry["latest"]
    entries = registry["entries"]

    if not entries or latest["run_id"] is None:
        return "Registro de Codex vacio: RN V1.3 ya tiene la capa de control, pero todavia sin iteraciones consolidadas."

    latest_entry = entries[-1]

    if debts_only:
        debts = _format_compact_items(list(registry.get("latest_open_debts", [])), limit=4)
        return (
            f"Deuda abierta de Codex: version cerrada V{registry.get('latest_version_closed_for_scope') or latest_entry['version_target'] or 'sin version'}; "
            f"riesgo {registry.get('latest_risk') or 'unknown'}; "
            f"deudas {debts}; siguiente paso {registry.get('latest_next_step') or latest_entry['next_recommended_step'] or 'sin paso sugerido'}."
        )

    if closed_version_only:
        return (
            f"Ultima version cerrada por Codex: V{registry.get('latest_version_closed_for_scope') or latest_entry['version_target'] or 'sin version'} "
            f"({latest_entry['status']}); checkpoint corto {registry.get('latest_checkpoint_short') or latest_entry['checkpoint_short'] or 'sin checkpoint breve'}; "
            f"runtime {registry.get('latest_runtime_health') or 'unknown'}."
        )

    if pending_only:
        weak = registry.get("latest_known_weakness") or latest_entry.get("known_weakness") or "sin debilidad declarada"
        debts = _format_compact_items(list(registry.get("latest_open_debts", [])), limit=4)
        return (
            f"Pendiente de Codex: punto debil {weak}; deuda abierta {debts}; "
            f"siguiente paso {registry.get('latest_next_step') or latest_entry['next_recommended_step'] or 'sin paso sugerido'}."
        )

    if status_only:
        return (
            f"Estado del registro de Codex: {summarize_codex_control_status()}; "
            "archivo canonico backend/app/routing_neuron/control/codex_control_registry.json; "
            f"schema {registry.get('schema_version') or 'sin schema'}; "
            f"latest checkpoint {registry.get('latest_checkpoint_short') or 'sin checkpoint breve'}; "
            f"artifacts review {_format_compact_items(list(registry.get('latest_review_artifacts_needed', [])), limit=3)}."
        )

    if include_changes:
        files_modified = _format_compact_items(list(latest_entry["files_modified"]), limit=5)
        files_created = _format_compact_items(list(latest_entry["files_created"]), limit=3)
        modules_touched = _format_compact_items(list(latest_entry["modules_touched"]), limit=4)
        contracts_affected = _format_compact_items(list(latest_entry["contracts_affected"]), limit=4)
        aura_changes = _format_compact_items(list(latest_entry["aura_changes"]), limit=4)
        rn_changes = _format_compact_items(list(latest_entry["rn_changes"]), limit=4)
        model_bank_changes = _format_compact_items(list(latest_entry["model_bank_changes"]), limit=4)
        return (
            f"Cambios del ultimo trabajo de Codex: run {latest_entry['run_id']} para V{latest_entry['version_target']} "
            f"({latest_entry['status']}); resumen {latest_entry['summary'] or 'sin resumen breve'}; "
            f"archivos modificados {files_modified}; archivos creados {files_created}; "
            f"modulos tocados {modules_touched}; contratos afectados {contracts_affected}; "
            f"cambios AURA {aura_changes}; cambios RN {rn_changes}; "
            f"cambios banco de modelos {model_bank_changes}; "
            f"deuda abierta {_format_compact_items(list(latest_entry['open_debts']), limit=3)}."
        )

    return (
        f"Ultimo trabajo de Codex: run {latest_entry['run_id']} para V{latest_entry['version_target']} "
        f"({latest_entry['status']}); alcance {latest_entry['requested_scope'] or latest_entry['work_scope'] or 'sin scope'}; "
        f"resumen {latest_entry['summary'] or 'sin resumen breve'}; "
        f"checkpoint {latest_entry['checkpoint_short'] or summarize_codex_latest_checkpoint()}; "
        f"tests {latest_entry['tests_result']['status']}, smokes {latest_entry['smokes_result']['status']}, runtime {registry.get('latest_runtime_health') or 'unknown'}, riesgo {registry.get('latest_risk') or 'unknown'}; "
        f"siguiente paso {latest_entry['next_recommended_step'] or 'sin paso sugerido'}."
    )


def _load_codex_registry_context() -> tuple[dict[str, Any], dict[str, Any] | None]:
    registry = load_codex_control_registry()
    entries = registry.get("entries", [])
    latest_entry = entries[-1] if entries else None
    return registry, latest_entry


def _dedupe_compact_items(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _infer_focus_modules_from_registry(
    registry: dict[str, Any],
    latest_entry: dict[str, Any] | None,
) -> str:
    focus_text = " ".join(
        [
            registry.get("latest_known_weakness") or "",
            " ".join(registry.get("latest_open_debts", [])),
            " ".join(registry.get("known_issues", {}).get("latest_long_tail_failures", [])),
        ]
    ).casefold()

    if any(marker in focus_text for marker in ("long tail", "prompt", "tecnico", "familia")):
        return "clasificacion tecnica, runtime_quality y rescate/fallback"

    if any(marker in focus_text for marker in ("registry", "codex", "administrativ", "routing neuron")):
        return "system_state, checkpoint y codex_control_registry"

    modules = list((latest_entry or {}).get("modules_touched", []))
    if modules:
        return _format_compact_items(modules, limit=3)

    return "la capa con deuda abierta visible"


def _collect_review_artifacts(
    registry: dict[str, Any],
    latest_entry: dict[str, Any] | None,
) -> list[str]:
    artifacts = list(registry.get("latest_review_artifacts_needed", []))
    focus_modules = _infer_focus_modules_from_registry(registry, latest_entry)

    if "runtime_quality" in focus_modules or "rescate/fallback" in focus_modules:
        artifacts.extend(
            [
                "agents/behavior_agent.py",
                "agents/runtime_quality.py",
                "agents/fallback_manager.py",
                "agents/response_agent.py",
            ]
        )

    if "system_state" in focus_modules or "codex_control_registry" in focus_modules:
        artifacts.extend(
            [
                "agents/system_state_agent.py",
                "backend/app/routing_neuron/control/codex_control_registry.json",
            ]
        )

    return _dedupe_compact_items(artifacts)


def _build_codex_stable_response() -> str:
    registry, latest_entry = _load_codex_registry_context()
    if latest_entry is None:
        return "Todavia no hay iteraciones consolidadas en el registro de Codex para marcar una zona estable."

    stable = (
        registry.get("latest_known_good")
        or latest_entry.get("known_good")
        or "sin zona estable declarada"
    )
    production_models = _format_compact_items(
        list(registry.get("model_bank", {}).get("production_models", [])),
        limit=4,
    )
    return (
        f"Lo mas consolidado ahora: {stable}; tests {latest_entry['tests_result']['status']}, "
        f"smokes {latest_entry['smokes_result']['status']}, runtime {registry.get('latest_runtime_health') or 'unknown'}; "
        f"core vigente {production_models}."
    )


def _build_codex_weak_response() -> str:
    registry, latest_entry = _load_codex_registry_context()
    if latest_entry is None:
        return "Todavia no hay iteraciones consolidadas en el registro de Codex para ubicar una debilidad viva."

    weak = (
        registry.get("latest_known_weakness")
        or latest_entry.get("known_weakness")
        or "sin debilidad declarada"
    )
    debts = _format_compact_items(list(registry.get("latest_open_debts", [])), limit=4)
    long_tail = _format_compact_items(
        list(registry.get("known_issues", {}).get("latest_long_tail_failures", [])),
        limit=3,
    )
    return (
        f"Lo que sigue flojo: {weak}; deuda abierta {debts}; "
        f"long tail observado {long_tail}."
    )


def _build_codex_risk_now_response() -> str:
    registry, latest_entry = _load_codex_registry_context()
    if latest_entry is None:
        return "Riesgo actual: unknown. El registro de Codex todavia no tiene una iteracion consolidada para sostener ese juicio."

    risk = registry.get("latest_risk") or "unknown"
    runtime_health = registry.get("latest_runtime_health") or "unknown"
    weak = (
        registry.get("latest_known_weakness")
        or latest_entry.get("known_weakness")
        or _format_compact_items(list(registry.get("latest_open_debts", [])), limit=3)
    )
    attention = _format_compact_items(list(latest_entry.get("rn_attention_points", [])), limit=3)
    return (
        f"Riesgo actual: {risk}; runtime {runtime_health}; motivo central {weak}; "
        f"atencion RN {attention}. No lo doy por cerrado todavia."
    )


def _build_codex_recommended_response() -> str:
    registry, latest_entry = _load_codex_registry_context()
    if latest_entry is None:
        return "Sin iteracion consolidada todavia, yo empezaria por correr una pasada chica de estado, tests y registry antes de tocar el resto."

    focus_modules = _infer_focus_modules_from_registry(registry, latest_entry)
    next_step = registry.get("latest_next_step") or latest_entry.get("next_recommended_step") or "sin paso sugerido"
    recommendations = _format_compact_items(list(latest_entry.get("rn_recommendations", [])), limit=3)
    weak = (
        registry.get("latest_known_weakness")
        or latest_entry.get("known_weakness")
        or "sin debilidad declarada"
    )
    return (
        f"Yo tocaria primero {focus_modules}; siguiente paso recomendado {next_step}; "
        f"recomendacion RN {recommendations}; deuda viva {weak}."
    )


def _build_codex_review_now_response() -> str:
    registry, latest_entry = _load_codex_registry_context()
    if latest_entry is None:
        return "Sin iteracion consolidada todavia, yo revisaria primero el registry canonico y una pasada basica de estado."

    artifacts = _format_compact_items(_collect_review_artifacts(registry, latest_entry), limit=4)
    weak = (
        registry.get("latest_known_weakness")
        or latest_entry.get("known_weakness")
        or "sin debilidad declarada"
    )
    degradation_patterns = _format_compact_items(
        list(registry.get("runtime_patterns", {}).get("degradation_patterns", [])),
        limit=3,
    )
    return (
        f"Yo revisaria {artifacts}; foco debil {weak}; "
        f"patrones de degradacion/rescate {degradation_patterns}."
    )


def _build_codex_plan_now_response() -> str:
    registry, latest_entry = _load_codex_registry_context()
    if latest_entry is None:
        return (
            "Lo dividiria en 3 pasos: 1. fijar una linea base de estado y tests, "
            "2. revisar deuda visible en el registry, 3. recien ahi abrir una tanda de estabilizacion."
        )

    focus_modules = _infer_focus_modules_from_registry(registry, latest_entry)
    weak = (
        registry.get("latest_known_weakness")
        or latest_entry.get("known_weakness")
        or "sin debilidad declarada"
    )
    return (
        "Lo dividiria en 3 pasos: "
        f"1. endurecer {focus_modules} sobre {weak}; "
        "2. correr smokes tecnicos abiertos y revisar metadata de degradacion/rescate; "
        "3. cerrar registry y checkpoint con lo que quedo estable y la deuda que siga viva."
    )


def _build_codex_do_not_touch_response() -> str:
    registry, latest_entry = _load_codex_registry_context()
    del latest_entry
    candidates = _format_compact_items(
        list(registry.get("model_bank", {}).get("candidate_models", [])),
        limit=4,
    )
    notes = _format_compact_items(
        list(registry.get("model_bank", {}).get("do_not_promote_notes", [])),
        limit=3,
    )
    return (
        "Todavia no tocaria el corazon multimodelo: Granite primary, OLMo critic/verifier, "
        "SmolLM2 router/helper y Qwen fallback transicional. "
        f"Tampoco promoveria candidatos {candidates}; criterio vigente {notes}."
    )


def _resolve_model_choice_response(
    conversation: list[dict[str, Any]] | None,
) -> str:
    user_messages = [
        str(message.get("content", ""))
        for message in (conversation or [])
        if message.get("role") == "user"
    ]
    reference_text = user_messages[-2] if len(user_messages) >= 2 else ""
    normalized_reference = normalize_internal_text(reference_text)

    if not normalized_reference:
        return (
            "Si no me das mas contexto, usaria Granite para la respuesta principal. "
            "OLMo lo reservaria para critica, chequeo de riesgo o consistencia; "
            "SmolLM2 para foco corto de routing; y Qwen solo como fallback transicional si el primary degrada. "
            "No promoveria candidatos al core todavia."
        )

    if any(marker in normalized_reference for marker in ("critica", "verifica", "verificar", "riesgo", "audita", "consistencia")):
        return (
            "Para eso usaria OLMo como critic/verifier, con Granite generando la base si hace falta. "
            "Ese reparto sirve mejor para revisar riesgo, tension o consistencia sin mover el core."
        )

    if any(marker in normalized_reference for marker in ("foco", "resume", "resumime", "encaminar", "ruta", "router")):
        return (
            "Para eso usaria SmolLM2 como router/helper, porque alcanza para foco corto y apoyo liviano. "
            "Dejaria Granite para la respuesta principal y no cambiaria el stack."
        )

    if any(marker in normalized_reference for marker in ("fallback", "degrada", "degradacion", "rescate", "si falla", "si se cae")):
        return (
            "Para ese caso usaria Qwen solo como fallback transicional. "
            "No lo subiria al core: lo dejaria acotado a recuperacion cuando Granite no cubre bien."
        )

    return (
        "Para eso usaria Granite como primary. "
        "Si luego quisiera revisar riesgo o tension tecnica, agregaria OLMo como critic. "
        "Mantendria SmolLM2 y Qwen en sus roles actuales."
    )


def _format_model_bank_governance(governance_snapshot: Any, benchmark_snapshot: Any) -> str:
    ready_now = _format_compact_items(list(benchmark_snapshot.ready_now), limit=4)
    blocked = _format_compact_items(list(benchmark_snapshot.blocked), limit=3)
    lab_watch = _format_compact_items(list(governance_snapshot.exploratory_ids), limit=4)
    return (
        f"gobierno de banco: produccion {governance_snapshot.production_count}, "
        f"candidatos {governance_snapshot.candidate_count}, laboratorio {governance_snapshot.lab_count}; "
        f"benchmark listo {ready_now}; bloqueados {blocked}; laboratorio en observacion {lab_watch}"
    )


def _routing_type_label(neuron_type: str | None) -> str:
    return normalize_neuron_type_label(neuron_type).replace("Unknown", "desconocido")


def _routing_confidence_label(confidence_tier: str | None) -> str:
    return normalize_confidence_label(confidence_tier).replace("sin señal", "sin señal")


def _format_score_axes(entry: Any) -> str:
    return (
        f"eff {getattr(entry, 'efficiency_score', 0.0)}, "
        f"stab {getattr(entry, 'stability_score', 0.0)}, "
        f"qual {getattr(entry, 'quality_score', 0.0)}, "
        f"reuse {getattr(entry, 'reusability_score', 0.0)}, "
        f"global {getattr(entry, 'global_routing_score', 0.0)}"
    )


def _structural_status_label(status: str, *, sealed: bool) -> str:
    if status == "sealed_structurally" or sealed:
        return "sellada estructuralmente"
    return status.replace("_", " ")


def _resolve_blueprint_state(entry: Any) -> tuple[str, str | None]:
    side_state = derive_side_state(entry)
    if side_state == "demoted":
        return "Demoted", "demoted"

    lifecycle_state = derive_lifecycle_state(entry)
    label = {
        ROUTING_LIFECYCLE_OBSERVED_PATTERN: "Observed Pattern",
        ROUTING_LIFECYCLE_CANDIDATE: "Candidate",
        ROUTING_LIFECYCLE_ACTIVE: "Active",
        ROUTING_LIFECYCLE_STABILIZED: "Stabilized",
        ROUTING_LIFECYCLE_PROMOTION_READY: "Promotion Ready",
        ROUTING_LIFECYCLE_PROMOTED: "Promoted",
        ROUTING_LIFECYCLE_PAUSED: "Paused",
        ROUTING_LIFECYCLE_RETIRED: "Retired",
    }.get(lifecycle_state, "Observed Pattern")
    return label, side_state


def _resolve_activation_barriers(entry: Any) -> tuple[str, ...]:
    return derive_activation_barriers(entry)


def analyze_system_state_command(user_input: str) -> SystemStateCommand | None:
    normalized_input = normalize_internal_text(user_input)

    if _matches_state_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_STATE)

    if matches_normalized_command(user_input, MODEL_NAME_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_MODEL_NAME)

    if matches_normalized_command(user_input, MODEL_PATH_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_MODEL_PATH)

    if matches_normalized_command(user_input, LLAMA_PATH_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_LLAMA_PATH)

    if matches_normalized_command(
        user_input,
        MODEL_AVAILABLE_QUERY_COMMANDS,
        token_corrections=MODEL_AVAILABLE_TOKEN_CORRECTIONS,
    ):
        return SystemStateCommand(target=SYSTEM_TARGET_MODEL_AVAILABLE)

    if matches_normalized_command(user_input, VERSION_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_VERSION)

    if matches_normalized_command(user_input, LOADED_MEMORY_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_LOADED_MEMORY)

    if _matches_recent_routing_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_RECENT)

    if matches_normalized_command(user_input, ROUTING_ACTIVE_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_ACTIVE)

    if matches_normalized_command(user_input, ROUTING_PAUSED_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_PAUSED)

    if matches_normalized_command(user_input, ROUTING_ALERTS_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_ALERTS)

    if matches_normalized_command(user_input, ROUTING_TOP_SCORE_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_TOP_SCORE)

    if matches_normalized_command(user_input, ROUTING_READINESS_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_READINESS)

    if matches_normalized_command(user_input, ROUTING_WATCH_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_WATCH)

    if matches_normalized_command(user_input, ROUTING_REVIEW_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_REVIEW)

    if matches_normalized_command(user_input, ROUTING_LOG_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_LOG)

    if matches_normalized_command(user_input, ROUTING_REVIEW_OPEN_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_REVIEW_OPEN)

    if matches_normalized_command(user_input, ROUTING_REVIEW_RESOLVED_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_REVIEW_RESOLVED)

    if matches_normalized_command(user_input, ROUTING_REOPENED_ALERTS_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_REOPENED_ALERTS)

    if matches_normalized_command(user_input, ROUTING_ACTIONS_HELPED_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_ACTIONS_HELPED)

    if matches_normalized_command(user_input, ROUTING_STALE_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_STALE)

    if matches_normalized_command(user_input, ROUTING_USEFUL_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_USEFUL)

    if matches_normalized_command(user_input, ROUTING_SHORTLIST_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_SHORTLIST)

    if matches_normalized_command(user_input, ROUTING_NOISE_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_NOISE)

    if matches_normalized_command(user_input, ROUTING_BRIDGE_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_BRIDGE)

    if matches_normalized_command(user_input, ROUTING_BRIDGE_READY_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_BRIDGE_READY)

    if matches_normalized_command(user_input, ROUTING_BRIDGE_BLOCKED_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_BRIDGE_BLOCKED)

    if matches_normalized_command(user_input, ROUTING_BRIDGE_DEFERRED_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_BRIDGE_DEFERRED)

    if matches_normalized_command(user_input, ROUTING_BRIDGE_FIT_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_BRIDGE_FIT)

    if matches_normalized_command(user_input, ROUTING_REHEARSAL_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_REHEARSAL)

    if matches_normalized_command(user_input, ROUTING_REHEARSAL_READY_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_REHEARSAL_READY)

    if matches_normalized_command(user_input, ROUTING_CUTOVER_NEAR_GO_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_CUTOVER_NEAR_GO)

    if matches_normalized_command(user_input, ROUTING_ROLLBACK_RISKS_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_ROLLBACK_RISKS)

    if _matches_launch_dossier_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_LAUNCH_DOSSIER)

    if matches_normalized_command(user_input, ROUTING_APPROVED_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_APPROVED)

    if matches_normalized_command(user_input, ROUTING_SUPPORT_ONLY_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_SUPPORT_ONLY)

    if matches_normalized_command(user_input, ROUTING_HOLD_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_HOLD)

    if matches_normalized_command(user_input, ROUTING_REJECTED_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_REJECTED)

    if matches_normalized_command(user_input, ROUTING_ACTIVATION_ORDER_QUERY_COMMANDS):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_ACTIVATION_ORDER)

    if _matches_routing_checkpoint_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_ROUTING_CHECKPOINT)

    if _matches_codex_latest_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_LATEST)

    if _matches_codex_status_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_STATUS)

    if _matches_codex_changes_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_CHANGES)

    if _matches_codex_debts_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_DEBTS)

    if _matches_codex_closed_version_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_CLOSED_VERSION)

    if _matches_codex_pending_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_PENDING)

    if _matches_codex_stable_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_STABLE)

    if _matches_codex_weak_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_WEAK)

    if _matches_codex_risk_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_RISK_NOW)

    if _matches_codex_recommended_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_RECOMMENDED)

    if _matches_codex_review_now_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_REVIEW_NOW)

    if _matches_codex_plan_now_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_PLAN_NOW)

    if _matches_codex_do_not_touch_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_DO_NOT_TOUCH)

    if _matches_codex_model_choice_query(normalized_input):
        return SystemStateCommand(target=SYSTEM_TARGET_CODEX_MODEL_CHOICE)

    selection_match = ROUTING_SELECTION_REASON_RE.match(user_input)
    if selection_match:
        return SystemStateCommand(
            target=SYSTEM_TARGET_ROUTING_SELECTION_REASON,
            neuron_id=selection_match.group("neuron_id"),
        )

    bridge_reason_match = ROUTING_BRIDGE_REASON_RE.match(user_input)
    if bridge_reason_match:
        return SystemStateCommand(
            target=SYSTEM_TARGET_ROUTING_BRIDGE_REASON,
            neuron_id=bridge_reason_match.group("neuron_id"),
        )

    cutover_reason_match = ROUTING_CUTOVER_REASON_RE.match(user_input)
    if cutover_reason_match:
        return SystemStateCommand(
            target=SYSTEM_TARGET_ROUTING_CUTOVER_REASON,
            neuron_id=cutover_reason_match.group("neuron_id"),
        )

    cutover_watch_match = ROUTING_CUTOVER_WATCH_REASON_RE.match(user_input)
    if cutover_watch_match:
        return SystemStateCommand(
            target=SYSTEM_TARGET_ROUTING_CUTOVER_REASON,
            neuron_id=cutover_watch_match.group("neuron_id"),
        )

    cutover_near_go_match = ROUTING_CUTOVER_NEAR_GO_REASON_RE.match(user_input)
    if cutover_near_go_match:
        return SystemStateCommand(
            target=SYSTEM_TARGET_ROUTING_CUTOVER_REASON,
            neuron_id=cutover_near_go_match.group("neuron_id"),
        )

    rollback_plan_match = ROUTING_ROLLBACK_PLAN_RE.match(user_input)
    if rollback_plan_match:
        return SystemStateCommand(
            target=SYSTEM_TARGET_ROUTING_ROLLBACK_PLAN,
            neuron_id=rollback_plan_match.group("neuron_id"),
        )

    dependencies_match = ROUTING_DEPENDENCIES_RE.match(user_input)
    if dependencies_match:
        return SystemStateCommand(
            target=SYSTEM_TARGET_ROUTING_DEPENDENCIES,
            neuron_id=dependencies_match.group("neuron_id"),
        )

    launch_reason_match = ROUTING_LAUNCH_REASON_RE.match(user_input)
    if launch_reason_match:
        return SystemStateCommand(
            target=SYSTEM_TARGET_ROUTING_LAUNCH_REASON,
            neuron_id=launch_reason_match.group("neuron_id"),
        )

    return None


def _build_model_name_response(model_path: str, llama_path: str) -> str:
    registry = build_default_model_registry(
        llama_path=llama_path,
        model_path=model_path,
    )
    primary_descriptor = registry.get_provider_for_role(ROLE_PRIMARY).descriptor
    model_name = primary_descriptor.model_id or Path(model_path).name or model_path
    model_status = (
        "usable ahora"
        if primary_descriptor.availability
        else f"no usable ahora ({_availability_reason_text(primary_descriptor.availability_reason)})"
    )
    return (
        f"Tengo configurado este modelo: {model_name}. "
        f"Ahora mismo está {model_status}."
    )


def _build_model_path_response(model_path: str, llama_path: str) -> str:
    registry = build_default_model_registry(
        llama_path=llama_path,
        model_path=model_path,
    )
    primary_descriptor = registry.get_provider_for_role(ROLE_PRIMARY).descriptor
    effective_path = primary_descriptor.model_path or model_path
    if effective_path != model_path:
        return (
            f"La ruta configurada del modelo es: {model_path}. "
            f"La ruta usable detectada ahora es: {effective_path}. "
            "Si quieres fijarla manualmente, usa AURA_PRIMARY_MODEL_PATH o AURA_MODEL_PATH."
        )

    return (
        f"La ruta del modelo es: {effective_path}. "
        "Si necesitas forzar otra en Windows, usa AURA_PRIMARY_MODEL_PATH o AURA_MODEL_PATH."
    )


def _build_llama_path_response(llama_path: str) -> str:
    return (
        f"La ruta de llama-cli es: {llama_path}. "
        "Si necesitas forzar otro runner en Windows, usa AURA_PRIMARY_LLAMA_PATH o AURA_LLAMA_PATH."
    )


def _build_model_available_response(model_path: str, llama_path: str) -> str:
    registry = build_default_model_registry(
        llama_path=llama_path,
        model_path=model_path,
    )
    primary_descriptor = registry.get_provider_for_role(ROLE_PRIMARY).descriptor
    if primary_descriptor.availability:
        if primary_descriptor.model_path and primary_descriptor.model_path != model_path:
            return (
                "Sí, el modelo está usable ahora. "
                f"Se detectó una ruta efectiva distinta a la configurada: {primary_descriptor.model_path}. "
                "Puedes fijarla con AURA_PRIMARY_MODEL_PATH o AURA_MODEL_PATH."
            )
        return "Sí, el modelo está usable ahora."

    return (
        "No, el modelo no está usable ahora "
        f"({_availability_reason_text(primary_descriptor.availability_reason)}). "
        "Revisa AURA_PRIMARY_MODEL_PATH/AURA_MODEL_PATH y que el runner exista por AURA_PRIMARY_LLAMA_PATH/AURA_LLAMA_PATH."
    )


def _build_version_response(aura_version: str) -> str:
    return f"Soy AURA V{aura_version}."


def _build_loaded_memory_response(memory: dict[str, Any]) -> str:
    summary = _build_memory_summary(memory)
    if summary == "sin datos cargados":
        return "La memoria cargada está vacía."

    return f"Tengo cargada esta memoria: {summary}."


def _describe_routing_entry(entry: Any) -> str:
    blueprint_state, side_state = _resolve_blueprint_state(entry)
    parts = [
        entry.neuron_id,
        f"estado {entry.neuron_state}",
        f"blueprint {blueprint_state}",
        f"tipo {_routing_type_label(getattr(entry, 'neuron_type', None))}",
        f"score {entry.global_routing_score}",
        f"confianza {_routing_confidence_label(entry.confidence_tier)}",
        f"estabilidad {entry.stability_label}",
        f"readiness {entry.readiness_band}",
    ]
    if side_state:
        parts.append(f"lateral {side_state}")
    if getattr(entry, "promotion_stage", None):
        parts.append(f"promotion {entry.promotion_stage}")
    if getattr(entry, "curation_status", None):
        parts.append(f"curacion {entry.curation_status}")
    if getattr(entry, "selection_status", None):
        parts.append(f"seleccion {entry.selection_status}")
    if getattr(entry, "influence_readiness", None):
        parts.append(f"influence {entry.influence_readiness}")
    if getattr(entry, "bridge_preflight_status", "not_considered") != "not_considered":
        parts.append(f"puente {entry.bridge_preflight_status}")
    if getattr(entry, "bridge_rehearsal_status", "not_in_rehearsal") != "not_in_rehearsal":
        parts.append(f"rehearsal {entry.bridge_rehearsal_status}")
    if getattr(entry, "cutover_readiness", "not_ready") != "not_ready":
        parts.append(f"cutover {entry.cutover_readiness}")
    if getattr(entry, "launch_status", "none") != "none":
        parts.append(f"launch {entry.launch_status}")
    if getattr(entry, "cutover_role", "none") != "none":
        parts.append(f"rol {entry.cutover_role}")
    if getattr(entry, "activation_order", None) is not None:
        parts.append(f"orden {entry.activation_order}")
    if entry.cooldown_turns_remaining > 0:
        parts.append(f"cooldown {entry.cooldown_turns_remaining}")
    if entry.alerts:
        parts.append(f"alertas {len(entry.alerts)}")
    if getattr(entry, "watch_status", False):
        parts.append("watch")
    if getattr(entry, "review_priority", "none") != "none":
        parts.append(f"revision {entry.review_priority}")
    return ", ".join(parts)


def _describe_admin_routing_entry(entry: Any) -> str:
    parts = [_describe_routing_entry(entry)]
    parts.append(f"ejes {_format_score_axes(entry)}")
    activation_barriers = _resolve_activation_barriers(entry)
    if activation_barriers:
        parts.append(f"barriers {_format_items(list(activation_barriers))}")
    if getattr(entry, "review_status", "none") != "none":
        parts.append(f"review {entry.review_status}")
    if getattr(entry, "alert_status", "none") != "none":
        parts.append(f"alerta {entry.alert_status}")
    if getattr(entry, "action_outcome", None):
        parts.append(f"outcome {entry.action_outcome}")
    if getattr(entry, "action_suggestion", None):
        parts.append(f"accion sugerida {entry.action_suggestion}")
    if getattr(entry, "selection_reason", None):
        parts.append(f"motivo seleccion {entry.selection_reason}")
    elif getattr(entry, "curation_reason", None):
        parts.append(f"motivo curacion {entry.curation_reason}")
    if getattr(entry, "influence_reason", None):
        parts.append(f"motivo influencia {entry.influence_reason}")
    if getattr(entry, "bridge_rationale", None):
        parts.append(f"motivo puente {entry.bridge_rationale}")
    if getattr(entry, "bridge_blockers", ()):
        parts.append(f"blockers {_format_items(list(entry.bridge_blockers))}")
    if getattr(entry, "rehearsal_rationale", None):
        parts.append(f"motivo rehearsal {entry.rehearsal_rationale}")
    if getattr(entry, "rehearsal_blockers", ()):
        parts.append(f"blockers rehearsal {_format_items(list(entry.rehearsal_blockers))}")
    if getattr(entry, "cutover_rationale", None):
        parts.append(f"motivo cutover {entry.cutover_rationale}")
    if getattr(entry, "rollback_concerns", ()):
        parts.append(f"riesgos {_format_items(list(entry.rollback_concerns))}")
    if getattr(entry, "launch_rationale", None):
        parts.append(f"motivo launch {entry.launch_rationale}")
    if getattr(entry, "cutover_role_reason", None):
        parts.append(f"motivo rol {entry.cutover_role_reason}")
    if getattr(entry, "dependency_hints", ()):
        parts.append(f"dependencias {_format_items(list(entry.dependency_hints))}")
    if getattr(entry, "rollback_triggers", ()):
        parts.append(f"triggers rollback {_format_items(list(entry.rollback_triggers))}")
    if getattr(entry, "fallback_target", None):
        parts.append(f"fallback {entry.fallback_target}")
    if getattr(entry, "safe_reversion", None):
        parts.append(f"reversion {entry.safe_reversion}")
    if getattr(entry, "no_go_conditions", ()):
        parts.append(f"no-go {_format_items(list(entry.no_go_conditions))}")
    if getattr(entry, "conceptual_role_fit", ()):
        fit_values = [fit for fit in entry.conceptual_role_fit if fit]
        if fit_values:
            parts.append(f"fit {_format_items(fit_values)}")
    if getattr(entry, "review_reason", None):
        parts.append(f"motivo revision {entry.review_reason}")
    elif getattr(entry, "readiness_reason", None):
        parts.append(f"motivo {entry.readiness_reason}")
    if getattr(entry, "watch_reason", None):
        parts.append(f"watch {entry.watch_reason}")
    if getattr(entry, "action_outcome_reason", None):
        parts.append(f"efecto {entry.action_outcome_reason}")
    return ", ".join(parts)


def _build_routing_recent_response(
    *,
    conversation: list[dict[str, Any]] | None = None,
    log_file: str | None = None,
) -> str:
    registry = get_default_routing_registry()
    snapshot = build_routing_repertoire_snapshot(registry)
    admin_state = build_routing_neuron_admin_state(registry)
    runtime_status = admin_state.runtime_status
    observable_summary = load_observable_routing_summary(conversation, log_file)
    history_mode = runtime_history_mode_label(runtime_status, observable_summary)
    if runtime_status.total_decisions > 0:
        activity = _format_items(list(snapshot.recent_activity[-2:])) if snapshot.recent_activity else "sin detalle corto"
        return (
            f"Actividad reciente de Routing Neuron V1: {history_mode}, "
            f"{activity}. {format_runtime_status(runtime_status)}."
        )
    if observable_summary is not None:
        replay_label = (
            "traza visible de la sesión actual"
            if observable_summary.source_mode == "conversation"
            else f"replay visible desde {observable_summary.source_label}"
        )
        return (
            f"Actividad reciente de Routing Neuron V1: {replay_label}, "
            "sin historial runtime en memoria; "
            f"{format_observable_runtime_shadow(observable_summary, include_source_label=False)}."
        )
    if snapshot.recent_activity:
        return (
            "Actividad estructural reciente de Routing Neuron V1: "
            + _format_items(list(snapshot.recent_activity[-2:]))
            + "."
        )
    return "Routing Neuron V1 todavía no tiene actividad reciente relevante."


def _build_routing_active_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    active_entries = [entry for entry in snapshot.entries if entry.neuron_state == "active"]
    if not active_entries:
        return "No tengo neuronas activas ahora."
    return f"Neuronas activas: {_format_items([_describe_routing_entry(entry) for entry in active_entries[:3]])}."


def _build_routing_paused_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    paused_entries = [entry for entry in snapshot.entries if entry.neuron_state == "paused"]
    if not paused_entries:
        return "No tengo neuronas pausadas ahora."
    return f"Neuronas pausadas: {_format_items([_describe_routing_entry(entry) for entry in paused_entries[:3]])}."


def _build_routing_alerts_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    alerted_entries = [entry for entry in snapshot.entries if entry.alerts]
    if not alerted_entries:
        return "Routing Neuron V1 no tiene alertas activas ahora."
    return f"Neuronas con alertas: {_format_items([_describe_admin_routing_entry(entry) for entry in alerted_entries[:3]])}."


def _build_routing_top_score_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    if not snapshot.entries:
        return "Todavía no tengo neuronas con score suficiente para mostrar."
    top_entries = [entry for entry in snapshot.entries if entry.neuron_id in snapshot.top_score_ids]
    return (
        "Top score de Routing Neuron V1: "
        + _format_items(
            [
                f"{_describe_routing_entry(entry)}, ejes {_format_score_axes(entry)}"
                for entry in top_entries[:3]
            ]
        )
        + "."
    )


def _build_routing_readiness_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    readiness_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.readiness_ids
    ]
    if not readiness_entries:
        return "Todavía no veo neuronas cerca de promoción: por ahora la señal de readiness sigue siendo temprana o de observación."
    return (
        "Neuronas cerca de promoción: "
        + _format_items(
            [
                f"{_describe_admin_routing_entry(entry)}"
                for entry in readiness_entries[:3]
            ]
        )
        + "."
    )


def _build_routing_watch_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    watch_entries = [entry for entry in snapshot.entries if entry.watch_status]
    if not watch_entries:
        return "No tengo neuronas en watch ahora."
    return (
        "Neuronas en watch: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in watch_entries[:3]])
        + "."
    )


def _build_routing_review_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    review_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.review_queue_ids
    ]
    if not review_entries:
        return "No veo neuronas que requieran revisión inmediata ahora."
    return (
        "Neuronas para revisión: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in review_entries[:3]])
        + "."
    )


def _build_routing_log_response() -> str:
    registry = get_default_routing_registry()
    if not registry.admin_log:
        return "La bitácora de Routing Neuron V1 todavía no tiene acciones administrativas."
    recent_actions = [
        f"{action.action_type} {action.neuron_id} ({action.reason}, outcome {action.outcome or 'pending'}, review {action.review_status or 'none'}, alerta {action.alert_status or 'none'})"
        for action in registry.admin_log[-5:]
    ]
    return "Bitácora reciente de Routing Neuron V1: " + _format_items(recent_actions) + "."


def _build_routing_open_reviews_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    review_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.open_review_ids
    ]
    if not review_entries:
        return "No veo revisiones abiertas ahora."
    return (
        "Revisiones abiertas: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in review_entries[:3]])
        + "."
    )


def _build_routing_resolved_reviews_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    resolved_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.resolved_review_ids
    ]
    if not resolved_entries:
        return "Todavía no tengo revisiones resueltas recientes para mostrar."
    return (
        "Revisiones resueltas: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in resolved_entries[:3]])
        + "."
    )


def _build_routing_reopened_alerts_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    reopened_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.reopened_alert_ids
    ]
    if not reopened_entries:
        return "No veo alertas reabiertas ahora."
    return (
        "Alertas reabiertas: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in reopened_entries[:3]])
        + "."
    )


def _build_routing_actions_helped_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    helped_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.helped_ids
    ]
    if not helped_entries:
        return "Todavía no veo acciones administrativas claramente útiles para mostrar."
    return (
        "Acciones que ayudaron: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in helped_entries[:3]])
        + "."
    )


def _build_routing_stale_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    stale_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.stale_ids
    ]
    if not stale_entries:
        return "No veo items estancados ahora."
    return (
        "Items estancados: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in stale_entries[:3]])
        + "."
    )


def _build_routing_useful_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    useful_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.useful_ids
    ]
    if not useful_entries:
        return "Todavía no veo neuronas claramente útiles y consistentes para destacar."
    return (
        "Neuronas más útiles: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in useful_entries[:3]])
        + "."
    )


def _build_routing_shortlist_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    shortlist_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.shortlist_ids
    ]
    if not shortlist_entries:
        return "Todavía no tengo neuronas en shortlist operativa."
    return (
        "Shortlist operativa de Routing Neuron V1: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in shortlist_entries[:3]])
        + "."
    )


def _build_routing_noise_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    noisy_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.discardable_ids
    ]
    if not noisy_entries:
        return "No veo neuronas descartables o claramente ruidosas ahora."
    return (
        "Neuronas que ya no deberían seguir en foco: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in noisy_entries[:3]])
        + "."
    )


def _build_routing_bridge_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    bridge_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.bridge_slate_ids
    ]
    if not bridge_entries:
        return "Todavía no veo una bridge slate clara para V0.39."
    return (
        "Bridge slate de Routing Neuron V1 hacia V0.39: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in bridge_entries[:3]])
        + "."
    )


def _build_routing_bridge_ready_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    ready_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.bridge_ready_ids
    ]
    if not ready_entries:
        return "Todavía no veo neuronas listas para el puente de V0.39."
    return (
        "Neuronas listas para el puente de V0.39: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in ready_entries[:3]])
        + "."
    )


def _build_routing_bridge_blocked_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    blocked_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.bridge_blocked_ids
    ]
    if not blocked_entries:
        return "No veo neuronas bloqueadas para V0.39 ahora."
    return (
        "Neuronas bloqueadas para V0.39: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in blocked_entries[:3]])
        + "."
    )


def _build_routing_bridge_deferred_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    deferred_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.bridge_deferred_ids
    ]
    if not deferred_entries:
        return "No veo neuronas diferidas para el puente ahora."
    return (
        "Neuronas diferidas para el puente: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in deferred_entries[:3]])
        + "."
    )


def _build_routing_bridge_fit_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    fit_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.stack_fit_ids
    ]
    if not fit_entries:
        return "Todavía no veo neuronas con compatibilidad clara con el stack verde."
    return (
        "Neuronas con mejor compatibilidad con el stack verde: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in fit_entries[:3]])
        + "."
    )


def _build_routing_rehearsal_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    rehearsal_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.rehearsal_slate_ids
    ]
    if not rehearsal_entries:
        return "Todavía no veo una rehearsal slate clara para V0.39."
    return (
        "Rehearsal slate de Routing Neuron V1 hacia V0.39: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in rehearsal_entries[:3]])
        + "."
    )


def _build_routing_rehearsal_ready_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    ready_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.rehearsal_ready_ids
    ]
    if not ready_entries:
        return "Todavía no veo neuronas listas para rehearsal."
    return (
        "Neuronas listas para rehearsal: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in ready_entries[:3]])
        + "."
    )


def _build_routing_cutover_near_go_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    near_go_entries = [
        entry
        for entry in snapshot.entries
        if entry.neuron_id in (snapshot.cutover_go_candidate_ids + snapshot.cutover_near_go_ids)
    ]
    if not near_go_entries:
        return "Todavía no veo neuronas cerca de un go/no-go favorable."
    return (
        "Neuronas más cerca del go/no-go administrativo: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in near_go_entries[:3]])
        + "."
    )


def _build_routing_rollback_risks_response() -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    risk_entries = [
        entry for entry in snapshot.entries if entry.neuron_id in snapshot.rollback_risk_ids
    ]
    if not risk_entries:
        return "No veo riesgos de rollback especialmente relevantes ahora."
    return (
        "Neuronas con riesgos de rollback o migración: "
        + _format_items([_describe_admin_routing_entry(entry) for entry in risk_entries[:3]])
        + "."
    )


def _build_empty_launch_dossier_response(dossier) -> str:
    return (
        f"Launch dossier de Routing Neuron V1 hacia V0.39 disponible ({dossier.package_recommendation}): "
        "approved 0, support-only 0, hold 0, rejected 0; "
        f"motivo {dossier.package_rationale}; "
        "actualmente sin neuronas finalistas; no bloquea por sí solo el cutover del stack core."
    )


def _build_routing_launch_dossier_response() -> str:
    dossier = build_routing_launch_dossier(get_default_routing_registry())
    if not dossier.entries:
        return _build_empty_launch_dossier_response(dossier)
    top_entries = [
        f"{entry.neuron_id} ({entry.launch_status}, rol {entry.cutover_role}, orden {entry.activation_order or 'n/a'})"
        for entry in dossier.entries[:4]
    ]
    return (
        f"Launch dossier de Routing Neuron V1 hacia V0.39 ({dossier.package_recommendation}): "
        f"approved {len(dossier.approved_ids)}, support-only {len(dossier.support_only_ids)}, "
        f"hold {len(dossier.hold_ids)}, rejected {len(dossier.rejected_ids)}; "
        f"blockers residuales {len(dossier.residual_blockers)}, "
        f"dependencias {len(dossier.dependency_map)}, "
        f"planes rollback {len(dossier.rollback_plan_summary)}; "
        f"motivo {dossier.package_rationale}; "
        f"entradas {_format_items(top_entries)}."
    )


def _build_routing_launch_status_response(
    *,
    status_ids: tuple[str, ...],
    empty_label: str,
    label: str,
) -> str:
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    dossier = build_routing_launch_dossier(get_default_routing_registry())
    entries = [entry for entry in snapshot.entries if entry.neuron_id in status_ids]
    if not entries:
        return (
            f"Cutover slate final disponible ({dossier.package_recommendation}), "
            f"sin {empty_label}."
        )
    return f"{label}: " + _format_items([_describe_admin_routing_entry(entry) for entry in entries[:3]]) + "."


def _find_launch_entry(neuron_id: str | None):
    if not neuron_id:
        return None
    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    return next((entry for entry in snapshot.entries if entry.neuron_id == neuron_id), None)


def _build_routing_activation_order_response() -> str:
    dossier = build_routing_launch_dossier(get_default_routing_registry())
    if not dossier.activation_order_ids:
        return (
            f"Cutover plan de Routing Neuron V1 disponible ({dossier.package_recommendation}), "
            "pero todavía sin orden de entrada final porque no hay neuronas approved o support-only."
        )
    ordered_entries = [entry for entry in dossier.entries if entry.activation_order is not None]
    ordered_entries = sorted(
        ordered_entries,
        key=lambda entry: (entry.activation_order or 999, entry.neuron_id),
    )
    return (
        "Orden de entrada sugerido para el cutover: "
        + _format_items(
            [
                f"{entry.activation_order}. {entry.neuron_id} ({entry.launch_status}, rol {entry.cutover_role})"
                for entry in ordered_entries[:5]
            ]
        )
        + "."
    )


def _build_routing_rollback_plan_response(neuron_id: str | None) -> str:
    if not neuron_id:
        return "Necesito el id de la neurona para mostrar su rollback plan."

    entry = _find_launch_entry(neuron_id)
    if entry is None:
        return f"No encontré la neurona {neuron_id} en el repertorio actual."

    triggers = _format_items(list(getattr(entry, "rollback_triggers", ()))) or "sin triggers fuertes"
    no_go = _format_items(list(getattr(entry, "no_go_conditions", ()))) or "sin no-go conditions fuertes"
    fallback_target = getattr(entry, "fallback_target", None) or "sin fallback target"
    safe_reversion = getattr(entry, "safe_reversion", None) or "sin reversion definida"
    return (
        f"Rollback plan de {entry.neuron_id}: launch {entry.launch_status}, rol {entry.cutover_role}; "
        f"triggers {triggers}; fallback {fallback_target}; reversion {safe_reversion}; "
        f"no-go {no_go}."
    )


def _build_routing_dependencies_response(neuron_id: str | None) -> str:
    if not neuron_id:
        return "Necesito el id de la neurona para mostrar sus dependencias."

    entry = _find_launch_entry(neuron_id)
    if entry is None:
        return f"No encontré la neurona {neuron_id} en el repertorio actual."

    dependencies = _format_items(list(getattr(entry, "dependency_hints", ()))) or "sin dependencias fuertes"
    return (
        f"Dependencias de {entry.neuron_id}: launch {entry.launch_status}, rol {entry.cutover_role}; "
        f"{dependencies}."
    )


def _build_routing_launch_reason_response(neuron_id: str | None) -> str:
    if not neuron_id:
        return "Necesito el id de la neurona para explicar su decisión final."

    entry = _find_launch_entry(neuron_id)
    if entry is None:
        return f"No encontré la neurona {neuron_id} en el repertorio actual."

    blockers = _format_items(list(getattr(entry, "no_go_conditions", ()))) or "sin blockers fuertes"
    risks = _format_items(list(getattr(entry, "rollback_concerns", ()))) or "sin riesgos fuertes"
    dependencies = _format_items(list(getattr(entry, "dependency_hints", ()))) or "sin dependencias fuertes"
    order_text = str(getattr(entry, "activation_order", None) or "n/a")
    return (
        f"La neurona {entry.neuron_id} quedó {entry.launch_status}. "
        f"Rol: {entry.cutover_role}; orden: {order_text}; riesgos: {risks}; blockers: {blockers}; "
        f"dependencias: {dependencies}; razón: {getattr(entry, 'launch_rationale', None) or 'todavía no hay explicación final'}."
    )


def _build_routing_selection_reason_response(neuron_id: str | None) -> str:
    if not neuron_id:
        return "Necesito el id de la neurona para explicar por qué fue seleccionada."

    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    entry = next((entry for entry in snapshot.entries if entry.neuron_id == neuron_id), None)
    if entry is None:
        return f"No encontré la neurona {neuron_id} en el repertorio actual."

    if entry.selection_status == "shortlisted":
        explanation = entry.selection_reason or entry.influence_reason or entry.curation_reason
        return (
            f"La neurona {entry.neuron_id} quedó seleccionada para shortlist. "
            f"Estado: {entry.selection_status}; influence readiness: {entry.influence_readiness}; "
            f"razón: {explanation or 'tiene suficiente valor sostenido para entrar en foco operativo'}."
        )

    explanation = entry.selection_reason or entry.curation_reason or entry.influence_reason
    return (
        f"La neurona {entry.neuron_id} no quedó seleccionada para shortlist. "
        f"Estado: {entry.selection_status}; influence readiness: {entry.influence_readiness}; "
        f"razón: {explanation or 'todavía no muestra suficiente valor sostenido o higiene administrativa'}."
    )


def _build_routing_bridge_reason_response(neuron_id: str | None) -> str:
    if not neuron_id:
        return "Necesito el id de la neurona para explicar por qué no entra al puente."

    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    entry = next((entry for entry in snapshot.entries if entry.neuron_id == neuron_id), None)
    if entry is None:
        return f"No encontré la neurona {neuron_id} en el repertorio actual."

    blockers = _format_items(list(entry.bridge_blockers)) if entry.bridge_blockers else "sin blockers fuertes"
    fit = _format_items(list(entry.conceptual_role_fit)) if entry.conceptual_role_fit else "sin fit claro"

    if entry.bridge_preflight_status == "preflight_ready":
        return (
            f"La neurona {entry.neuron_id} sí entra al puente. "
            f"Estado: {entry.bridge_preflight_status}; fit: {fit}; "
            f"razón: {entry.bridge_rationale or 'ya tiene valor sostenido y bajo ruido para el preflight'}."
        )

    return (
        f"La neurona {entry.neuron_id} no entra todavía al puente. "
        f"Estado: {entry.bridge_preflight_status}; fit: {fit}; blockers: {blockers}; "
        f"razón: {entry.bridge_rationale or 'todavía le faltan señales más limpias para el preflight'}."
    )


def _build_routing_cutover_reason_response(neuron_id: str | None) -> str:
    if not neuron_id:
        return "Necesito el id de la neurona para explicar por qué no entra al go/no-go."

    snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
    entry = next((entry for entry in snapshot.entries if entry.neuron_id == neuron_id), None)
    if entry is None:
        return f"No encontré la neurona {neuron_id} en el repertorio actual."

    risks = _format_items(list(entry.rollback_concerns)) if entry.rollback_concerns else "sin riesgos fuertes"
    blockers = _format_items(list(entry.rehearsal_blockers or entry.bridge_blockers)) if (entry.rehearsal_blockers or entry.bridge_blockers) else "sin blockers fuertes"
    fit = _format_items(list(entry.conceptual_role_fit)) if entry.conceptual_role_fit else "sin fit claro"

    if entry.cutover_readiness == "go_candidate":
        return (
            f"La neurona {entry.neuron_id} ya está cerca de un go/no-go favorable. "
            f"Estado: {entry.cutover_readiness}; rehearsal: {entry.bridge_rehearsal_status}; fit: {fit}; "
            f"riesgos: {risks}; razón: {entry.cutover_rationale or 'ya sostiene una base administrativa fuerte para cutover'}."
        )

    if entry.cutover_readiness == "near_go":
        return (
            f"La neurona {entry.neuron_id} ya llegó a near_go, pero todavía no conviene marcarla como go_candidate. "
            f"Estado: {entry.cutover_readiness}; rehearsal: {entry.bridge_rehearsal_status}; fit: {fit}; "
            f"riesgos: {risks}; razón: {entry.cutover_rationale or 'todavía conviene cerrar algunos riesgos antes del go/no-go'}."
        )

    if entry.cutover_readiness == "watch":
        return (
            f"La neurona {entry.neuron_id} sigue en watch para cutover y todavía no llega a near_go. "
            f"Estado: {entry.cutover_readiness}; rehearsal: {entry.bridge_rehearsal_status}; fit: {fit}; "
            f"blockers: {blockers}; riesgos: {risks}; "
            f"razón: {entry.cutover_rationale or 'todavía conviene observarla y consolidar rehearsal antes de empujarla'}."
        )

    return (
        f"La neurona {entry.neuron_id} todavía no entra al go/no-go. "
        f"Estado: {entry.cutover_readiness}; rehearsal: {entry.bridge_rehearsal_status}; fit: {fit}; "
        f"blockers: {blockers}; riesgos: {risks}; "
        f"razón: {entry.cutover_rationale or 'todavía le faltan señales más robustas para un cutover administrativo'}."
    )


def _build_routing_checkpoint_response(
    *,
    conversation: list[dict[str, Any]] | None = None,
    log_file: str | None = None,
) -> str:
    registry = get_default_routing_registry()
    admin_state = build_routing_neuron_admin_state(registry)
    snapshot = admin_state.snapshot
    dossier = admin_state.dossier
    runtime_status = admin_state.runtime_status
    observable_summary = load_observable_routing_summary(conversation, log_file)
    top_entry = snapshot.entries[0] if snapshot.entries else None
    top_state = _resolve_blueprint_state(top_entry)[0] if top_entry is not None else "Observed Pattern"
    top_type = _routing_type_label(getattr(top_entry, "neuron_type", None)) if top_entry is not None else "Selection/Transformation/Control"
    top_barriers = _format_items(list(_resolve_activation_barriers(top_entry))) if top_entry is not None else "state, budget, context, competitive, stability, composition y fallback"
    top_promotion = getattr(top_entry, "promotion_stage", None) or "specialized_prompt"
    seal_status = (
        "estructuralmente sellado"
        if admin_state.seal_status.v1_sealed
        else _structural_status_label(
            admin_state.seal_status.structural_status,
            sealed=admin_state.seal_status.v1_sealed,
        )
    )
    seal_gaps = _format_items(list(admin_state.seal_status.gaps)) if admin_state.seal_status.gaps else "sin gaps abiertos"
    sealed_scope = _format_items(list(admin_state.seal_status.sealed_scope))
    partial_scope = _format_items(list(admin_state.seal_status.partial_scope))
    v1x_debts = _format_items(list(admin_state.seal_status.v1x_debts))
    score_axes = _format_items([axis.axis for axis in admin_state.score_axes])

    return (
        f"Checkpoint de Routing Neuron V1: subsistema {seal_status} en backend/app/routing_neuron; "
        "capa transversal activa; "
        "tipos base Selection, Transformation y Control; "
        "flujo online observe -> evidence -> score -> runtime -> maintenance; "
        "extensiones tácticas offline shortlist -> bridge -> rehearsal -> launch dossier cuando aplican; "
        "cadena blueprint visible Observed Pattern -> Candidate -> Active -> Stabilized -> Promotion Ready -> Promoted; "
        "estados laterales cubiertos por paused y, a nivel admin, por rutas de retired/demoted; "
        f"ejes de score {score_axes}; "
        f"{format_runtime_status(runtime_status, observable_summary)}; "
        f"ventana liviana de historial reciente {runtime_status.history_window_limit}; "
        f"confianza progresiva {_routing_confidence_label(getattr(top_entry, 'confidence_tier', None)) if top_entry is not None else 'señal temprana, patrón confirmado y confianza estable'}; "
        f"barreras admin/runtime {top_barriers}; "
        "senderos applied seguros: skip_critic y transformaciones de prompt livianas cuando la barrera lo permite; "
        f"promoción fuerte por defecto {top_promotion}; "
        f"fallback baseline/última ruta estable representado por fallback_target y safe_reversion; "
        "separación conceptual mantenida respecto del cutover de V0.39; "
        f"sellado {sealed_scope}; estado de validación {runtime_validation_state_text(admin_state.seal_status.operational_validation_status)}; parcial {partial_scope}; deuda V1.x {v1x_debts}; "
        f"gaps aceptados {seal_gaps}; "
        "estado operativo actual: "
        f"patterns {len(registry.observed_patterns)}, candidatas {len(registry.candidates)}, activas {len(registry.active)}, "
        f"blueprint líder {top_state}, tipo líder {top_type}, dossier {dossier.package_recommendation}, "
        "decisiones recientes "
        f"{_format_items(list(runtime_status.recent_decisions)) if runtime_status.recent_decisions else (format_observable_recent_decisions(observable_summary) if observable_summary is not None else 'sin historial runtime reciente todavía')}."
    )


def _build_state_response(
    memory: dict[str, Any],
    aura_version: str,
    model_path: str,
    llama_path: str,
    conversation: list[dict[str, Any]] | None = None,
    log_file: str | None = None,
) -> str:
    registry = build_default_model_registry(
        llama_path=llama_path,
        model_path=model_path,
    )
    primary_provider = registry.get_provider_for_role(ROLE_PRIMARY)
    critic_provider = registry.get_provider_for_role(ROLE_CRITIC)
    router_provider = registry.get_provider_for_role(ROLE_MICRO_EXPERT_ROUTER)
    fallback_provider = registry.get_fallback_provider()
    primary_policy = registry.get_active_policy_for_role(ROLE_PRIMARY)
    critic_policy = registry.get_active_policy_for_role(ROLE_CRITIC)
    router_policy = registry.get_active_policy_for_role(ROLE_MICRO_EXPERT_ROUTER)
    fallback_policy = registry.get_transitional_fallback_policy()
    allowlist = registry.list_allowlisted_candidates()
    production_entries = registry.list_production_stack()
    candidate_entries = registry.list_candidate_benchmarks()
    lab_entries = registry.list_lab_models()
    routing_registry = get_default_routing_registry()
    routing_admin_state = build_routing_neuron_admin_state(routing_registry)
    routing_snapshot = routing_admin_state.snapshot
    launch_dossier = routing_admin_state.dossier
    score_axes_summary = _format_items([axis.axis for axis in routing_admin_state.score_axes])
    runtime_status = routing_admin_state.runtime_status
    observable_summary = load_observable_routing_summary(conversation, log_file)
    primary_descriptor = primary_provider.descriptor if primary_provider is not None else None
    critic_descriptor = critic_provider.descriptor if critic_provider is not None else None
    router_descriptor = router_provider.descriptor if router_provider is not None else None
    fallback_descriptor = fallback_provider.descriptor if fallback_provider is not None else None
    stack_health_snapshot = build_stack_health_snapshot(registry)
    model_name = (
        primary_descriptor.model_id
        if primary_descriptor and primary_descriptor.model_id
        else Path(model_path).name or model_path
    )
    llama_status = _llama_status_text(llama_path)
    memory_summary = _build_memory_summary(memory)
    primary_status = _provider_state_text(primary_descriptor, active=True)
    critic_status = _provider_state_text(
        critic_descriptor,
        active=critic_policy is not None,
    )
    router_status = _provider_state_text(
        router_descriptor,
        active=router_policy is not None,
    )
    fallback_status = _provider_state_text(
        fallback_descriptor,
        fallback=fallback_policy is not None,
    )
    stack_health = _format_stack_health(stack_health_snapshot)
    allowlist_summary = _format_compact_items([entry.model_id for entry in allowlist], limit=6)
    production_summary = _summarize_policy_entries(production_entries)
    candidate_summary = _summarize_policy_entries(candidate_entries)
    lab_summary = _summarize_policy_entries(lab_entries)
    transitional_marker = (
        primary_policy.policy_status.replace("_", " ")
        if primary_policy is not None
        else "sin clasificar"
    )
    effective_model_path = (
        primary_descriptor.model_path
        if primary_descriptor and primary_descriptor.model_path
        else model_path
    )
    runtime_backend = (
        primary_descriptor.runtime_backend
        if primary_descriptor and primary_descriptor.runtime_backend
        else primary_descriptor.backend_type if primary_descriptor else "sin backend"
    )
    artifact_format = (
        primary_descriptor.artifact_format
        if primary_descriptor and primary_descriptor.artifact_format
        else "sin artefacto"
    )
    routing_summary = (
        f"Routing Neuron V1: {_structural_status_label(routing_admin_state.seal_status.structural_status, sealed=routing_admin_state.seal_status.v1_sealed)}, disponible, núcleo "
        f"patterns {len(routing_registry.observed_patterns)}, "
        f"candidatas {len(routing_registry.candidates)}, "
        f"activas {len(routing_registry.active)}, "
        f"pausadas {len(routing_registry.list_paused())}, "
        f"watch {len(routing_snapshot.watch_ids)}, "
        f"revision {len(routing_snapshot.review_queue_ids)}, "
        f"abiertas {len(routing_snapshot.open_review_ids)}, "
        f"resueltas {len(routing_snapshot.resolved_review_ids)}, "
        f"stale {len(routing_snapshot.stale_ids)}, "
        f"alertas {len(routing_registry.alerts)}, "
        f"recomendaciones {len(routing_registry.promotion_recommendations)}, "
        f"readiness {len(routing_snapshot.readiness_ids)}, "
        f"ejes de score {score_axes_summary}, "
        f"{format_runtime_status(runtime_status, observable_summary, compact=True)}; "
        f"extensiones tácticas shortlist {len(routing_snapshot.shortlist_ids)}, "
        f"puente {len(routing_snapshot.bridge_slate_ids)}, "
        f"listas {len(routing_snapshot.bridge_ready_ids)}, "
        f"bloqueadas {len(routing_snapshot.bridge_blocked_ids)}, "
        f"diferidas {len(routing_snapshot.bridge_deferred_ids)}, "
        f"rehearsal {len(routing_snapshot.rehearsal_slate_ids)}, "
        f"listas rehearsal {len(routing_snapshot.rehearsal_ready_ids)}, "
        f"near-go {len(routing_snapshot.cutover_near_go_ids)}, "
        f"go {len(routing_snapshot.cutover_go_candidate_ids)}, "
        f"approved {len(routing_snapshot.approved_ids)}, "
        f"support {len(routing_snapshot.support_only_ids)}, "
        f"hold {len(routing_snapshot.hold_ids)}, "
        f"rejected {len(routing_snapshot.rejected_ids)}, "
        f"riesgos {len(routing_snapshot.rollback_risk_ids)}, "
        f"descartables {len(routing_snapshot.discardable_ids)}"
    )
    routing_summary += f", dossier {launch_dossier.package_recommendation}"
    if launch_dossier.package_recommendation == "no_go":
        routing_summary += " (solo capa administrativa V1; no bloquea el cutover core)"
    routing_summary += f", estado de validación {runtime_validation_state_text(routing_admin_state.seal_status.operational_validation_status)}"
    if routing_snapshot.recent_conflicts:
        routing_summary += f", conflictos recientes {len(routing_snapshot.recent_conflicts)}"
    if routing_snapshot.recent_admin_actions:
        routing_summary += f", acciones recientes {len(routing_snapshot.recent_admin_actions)}"
    if routing_snapshot.recent_activity:
        routing_summary += f", reciente {routing_snapshot.recent_activity[-1]}"
    if runtime_status.recent_conflicts:
        routing_summary += f", conflictos runtime {_format_items(list(runtime_status.recent_conflicts))}"

    calibration_summary = (
        f"primary {PRIMARY_CALIBRATION_PROFILE}, critic {CRITIC_CALIBRATION_PROFILE}, "
        f"router {ROUTER_CALIBRATION_PROFILE}, fallback {FALLBACK_CALIBRATION_PROFILE}"
    )
    runtime_override_summary = _build_runtime_override_summary()

    return (
        f"Estado actual: version AURA V{aura_version}; "
        f"modelo configurado: {model_name} ({primary_status}, {transitional_marker}); "
        f"ruta del modelo: {effective_model_path}; "
        f"llama-cli: {llama_status}; "
        f"ruta de llama-cli: {llama_path}; "
        f"providers: primary {primary_descriptor.provider_id if primary_descriptor else 'sin provider'} / {primary_descriptor.model_id if primary_descriptor else 'sin modelo'} ({primary_status}), "
        f"critic {critic_descriptor.provider_id if critic_descriptor else 'sin provider'} / {critic_descriptor.model_id if critic_descriptor else 'sin modelo'} ({critic_status}), "
        f"router {router_descriptor.provider_id if router_descriptor else 'sin provider'} / {router_descriptor.model_id if router_descriptor else 'sin modelo'} ({router_status}), "
        f"fallback {fallback_descriptor.provider_id if fallback_descriptor else 'sin provider'} / {fallback_descriptor.model_id if fallback_descriptor else 'sin modelo'} ({fallback_status}); "
        f"stack activo: multimodelo local abierto, backend {runtime_backend}, artefacto {artifact_format}, health {stack_health}; "
        f"roles del corazón: Granite primary, OLMo critic/verifier, SmolLM2 router/helper, Qwen fallback transicional; "
        f"calibracion V0.39.6: {calibration_summary}; "
        f"allowlist verde: {allowlist_summary}; "
        f"banco de modelos: producción {production_summary}; "
        f"candidatos inmediatos {candidate_summary}; "
        f"laboratorio {lab_summary}; "
        f"bootstrap Windows: {runtime_override_summary}; "
        f"{routing_summary}; "
        f"memoria cargada: {memory_summary}."
    )


def _build_routing_checkpoint_response_v11(
    *,
    conversation: list[dict[str, Any]] | None = None,
    log_file: str | None = None,
) -> str:
    registry = get_default_routing_registry()
    admin_state = build_routing_neuron_admin_state(registry)
    snapshot = admin_state.snapshot
    dossier = admin_state.dossier
    runtime_status = admin_state.runtime_status
    observable_summary = load_observable_routing_summary(conversation, log_file)
    top_entry = snapshot.entries[0] if snapshot.entries else None
    top_state = _resolve_blueprint_state(top_entry)[0] if top_entry is not None else "Observed Pattern"
    top_type = _routing_type_label(getattr(top_entry, "neuron_type", None)) if top_entry is not None else "Selection/Transformation/Control"
    top_barriers = _format_items(list(_resolve_activation_barriers(top_entry))) if top_entry is not None else "state, budget, context, competitive, stability, composition y fallback"
    top_promotion = getattr(top_entry, "promotion_stage", None) or "specialized_prompt"
    seal_status = (
        "estructuralmente sellado"
        if admin_state.seal_status.v1_sealed
        else _structural_status_label(
            admin_state.seal_status.structural_status,
            sealed=admin_state.seal_status.v1_sealed,
        )
    )
    seal_gaps = _format_items(list(admin_state.seal_status.gaps)) if admin_state.seal_status.gaps else "sin gaps abiertos"
    sealed_scope = _format_items(list(admin_state.seal_status.sealed_scope))
    partial_scope = _format_items(list(admin_state.seal_status.partial_scope))
    v1x_debts = _format_items(list(admin_state.seal_status.v1x_debts))
    score_axes = _format_items([axis.axis for axis in admin_state.score_axes])
    codex_control = admin_state.codex_control
    codex_checkpoint = _format_codex_control_inline(codex_control)
    codex_debts = _format_codex_open_debts(codex_control)
    codex_good = getattr(codex_control, "latest_known_good", None) or "sin zona estable declarada"
    codex_weakness = getattr(codex_control, "latest_known_weakness", None) or "sin debilidad declarada"
    codex_next = getattr(codex_control, "latest_next_step", None) or "sin paso sugerido"
    codex_recommendation = _format_compact_items(list(getattr(codex_control, "latest_rn_recommendations", ()) or ()), limit=3)
    codex_runtime_patterns = _format_compact_items(
        list(getattr(codex_control, "latest_degradation_patterns", ()) or ())
        + list(getattr(codex_control, "latest_fallback_patterns", ()) or ()),
        limit=4,
    )
    codex_closed_version = getattr(codex_control, "latest_version_closed_for_scope", None) or getattr(
        codex_control,
        "latest_version",
        None,
    ) or "sin version"

    return (
        f"Checkpoint de Routing Neuron V1.3: subsistema {seal_status} en backend/app/routing_neuron; "
        "capa transversal activa; "
        "tipos base Selection, Transformation y Control; "
        "flujo online observe -> evidence -> score -> runtime -> maintenance; "
        "extensiones tacticas offline shortlist -> bridge -> rehearsal -> launch dossier cuando aplican; "
        "capa de control canonica para Codex integrada en backend/app/routing_neuron/control como memoria administrativa viva; "
        "cadena blueprint visible Observed Pattern -> Candidate -> Active -> Stabilized -> Promotion Ready -> Promoted; "
        "estados laterales cubiertos por paused y, a nivel admin, por rutas de retired/demoted; "
        f"ejes de score {score_axes}; "
        f"{format_runtime_status(runtime_status, observable_summary)}; "
        f"ventana liviana de historial reciente {runtime_status.history_window_limit}; "
        f"confianza progresiva {_routing_confidence_label(getattr(top_entry, 'confidence_tier', None)) if top_entry is not None else 'senal temprana, patron confirmado y confianza estable'}; "
        f"barreras admin/runtime {top_barriers}; "
        "senderos applied seguros: skip_critic y transformaciones de prompt livianas cuando la barrera lo permite; "
        f"promocion fuerte por defecto {top_promotion}; "
        "fallback baseline/ultima ruta estable representado por fallback_target y safe_reversion; "
        "separacion conceptual mantenida respecto del cutover de V0.39; "
        f"memoria iterativa Codex {codex_checkpoint}; version cerrada V{codex_closed_version}; "
        f"zona estable {codex_good}; deuda visible {codex_debts}; punto debil {codex_weakness}; "
        f"patrones runtime {codex_runtime_patterns}; recomendacion RN {codex_recommendation}; siguiente paso {codex_next}; "
        f"sellado {sealed_scope}; estado de validacion {runtime_validation_state_text(admin_state.seal_status.operational_validation_status)}; parcial {partial_scope}; deuda V1.x {v1x_debts}; "
        f"gaps aceptados {seal_gaps}; "
        "estado operativo actual: "
        f"patterns {len(registry.observed_patterns)}, candidatas {len(registry.candidates)}, activas {len(registry.active)}, "
        f"blueprint lider {top_state}, tipo lider {top_type}, dossier {dossier.package_recommendation}, "
        "decisiones recientes "
        f"{_format_items(list(runtime_status.recent_decisions)) if runtime_status.recent_decisions else (format_observable_recent_decisions(observable_summary) if observable_summary is not None else 'sin historial runtime reciente todavía')}."
    )


def _build_state_response_v0394(
    memory: dict[str, Any],
    aura_version: str,
    model_path: str,
    llama_path: str,
    conversation: list[dict[str, Any]] | None = None,
    log_file: str | None = None,
) -> str:
    registry = build_default_model_registry(
        llama_path=llama_path,
        model_path=model_path,
    )
    primary_provider = registry.get_provider_for_role(ROLE_PRIMARY)
    critic_provider = registry.get_provider_for_role(ROLE_CRITIC)
    router_provider = registry.get_provider_for_role(ROLE_MICRO_EXPERT_ROUTER)
    fallback_provider = registry.get_fallback_provider()
    primary_policy = registry.get_active_policy_for_role(ROLE_PRIMARY)
    critic_policy = registry.get_active_policy_for_role(ROLE_CRITIC)
    router_policy = registry.get_active_policy_for_role(ROLE_MICRO_EXPERT_ROUTER)
    fallback_policy = registry.get_transitional_fallback_policy()
    allowlist = registry.list_allowlisted_candidates()
    production_entries = registry.list_production_stack()
    candidate_entries = registry.list_candidate_benchmarks()
    lab_entries = registry.list_lab_models()
    governance_snapshot = build_model_bank_governance_snapshot(registry)
    benchmark_snapshot = build_benchmark_preparation_snapshot(registry)
    routing_registry = get_default_routing_registry()
    routing_admin_state = build_routing_neuron_admin_state(routing_registry)
    routing_snapshot = routing_admin_state.snapshot
    launch_dossier = routing_admin_state.dossier
    codex_control = routing_admin_state.codex_control
    score_axes_summary = _format_items([axis.axis for axis in routing_admin_state.score_axes])
    runtime_status = routing_admin_state.runtime_status
    observable_summary = load_observable_routing_summary(conversation, log_file)
    primary_descriptor = primary_provider.descriptor if primary_provider is not None else None
    critic_descriptor = critic_provider.descriptor if critic_provider is not None else None
    router_descriptor = router_provider.descriptor if router_provider is not None else None
    fallback_descriptor = fallback_provider.descriptor if fallback_provider is not None else None
    stack_health_snapshot = build_stack_health_snapshot(registry)
    model_name = (
        primary_descriptor.model_id
        if primary_descriptor and primary_descriptor.model_id
        else Path(model_path).name or model_path
    )
    llama_status = _llama_status_text(llama_path)
    memory_summary = _build_memory_summary(memory)
    primary_status = _provider_state_text(primary_descriptor, active=True)
    critic_status = _provider_state_text(
        critic_descriptor,
        active=critic_policy is not None,
    )
    router_status = _provider_state_text(
        router_descriptor,
        active=router_policy is not None,
    )
    fallback_status = _provider_state_text(
        fallback_descriptor,
        fallback=fallback_policy is not None,
    )
    stack_health = _format_stack_health(stack_health_snapshot)
    allowlist_summary = _format_compact_items([entry.model_id for entry in allowlist], limit=6)
    production_summary = _summarize_policy_entries(production_entries)
    candidate_summary = _summarize_policy_entries(candidate_entries)
    lab_summary = _summarize_policy_entries(lab_entries)
    governance_summary = _format_model_bank_governance(governance_snapshot, benchmark_snapshot)
    transitional_marker = (
        primary_policy.policy_status.replace("_", " ")
        if primary_policy is not None
        else "sin clasificar"
    )
    effective_model_path = (
        primary_descriptor.model_path
        if primary_descriptor and primary_descriptor.model_path
        else model_path
    )
    runtime_backend = (
        primary_descriptor.runtime_backend
        if primary_descriptor and primary_descriptor.runtime_backend
        else primary_descriptor.backend_type if primary_descriptor else "sin backend"
    )
    artifact_format = (
        primary_descriptor.artifact_format
        if primary_descriptor and primary_descriptor.artifact_format
        else "sin artefacto"
    )
    routing_summary = (
        f"Routing Neuron V1.3: {_structural_status_label(routing_admin_state.seal_status.structural_status, sealed=routing_admin_state.seal_status.v1_sealed)}, disponible, nucleo "
        f"patterns {len(routing_registry.observed_patterns)}, "
        f"candidatas {len(routing_registry.candidates)}, "
        f"activas {len(routing_registry.active)}, "
        f"pausadas {len(routing_registry.list_paused())}, "
        f"watch {len(routing_snapshot.watch_ids)}, "
        f"revision {len(routing_snapshot.review_queue_ids)}, "
        f"abiertas {len(routing_snapshot.open_review_ids)}, "
        f"resueltas {len(routing_snapshot.resolved_review_ids)}, "
        f"stale {len(routing_snapshot.stale_ids)}, "
        f"alertas {len(routing_registry.alerts)}, "
        f"recomendaciones {len(routing_registry.promotion_recommendations)}, "
        f"readiness {len(routing_snapshot.readiness_ids)}, "
        f"ejes de score {score_axes_summary}, "
        f"{format_runtime_status(runtime_status, observable_summary, compact=True)}; "
        f"extensiones tacticas shortlist {len(routing_snapshot.shortlist_ids)}, "
        f"puente {len(routing_snapshot.bridge_slate_ids)}, "
        f"listas {len(routing_snapshot.bridge_ready_ids)}, "
        f"bloqueadas {len(routing_snapshot.bridge_blocked_ids)}, "
        f"diferidas {len(routing_snapshot.bridge_deferred_ids)}, "
        f"rehearsal {len(routing_snapshot.rehearsal_slate_ids)}, "
        f"listas rehearsal {len(routing_snapshot.rehearsal_ready_ids)}, "
        f"near-go {len(routing_snapshot.cutover_near_go_ids)}, "
        f"go {len(routing_snapshot.cutover_go_candidate_ids)}, "
        f"approved {len(routing_snapshot.approved_ids)}, "
        f"support {len(routing_snapshot.support_only_ids)}, "
        f"hold {len(routing_snapshot.hold_ids)}, "
        f"rejected {len(routing_snapshot.rejected_ids)}, "
        f"riesgos {len(routing_snapshot.rollback_risk_ids)}, "
        f"descartables {len(routing_snapshot.discardable_ids)}"
    )
    routing_summary += f", dossier {launch_dossier.package_recommendation}"
    if launch_dossier.package_recommendation == "no_go":
        routing_summary += " (solo capa administrativa V1.3; no bloquea el cutover core)"
    routing_summary += f", estado de validacion {runtime_validation_state_text(routing_admin_state.seal_status.operational_validation_status)}"
    if routing_snapshot.recent_conflicts:
        routing_summary += f", conflictos recientes {len(routing_snapshot.recent_conflicts)}"
    if routing_snapshot.recent_admin_actions:
        routing_summary += f", acciones recientes {len(routing_snapshot.recent_admin_actions)}"
    if routing_snapshot.recent_activity:
        routing_summary += f", reciente {routing_snapshot.recent_activity[-1]}"
    if runtime_status.recent_conflicts:
        routing_summary += f", conflictos runtime {_format_items(list(runtime_status.recent_conflicts))}"

    calibration_summary = (
        f"primary {PRIMARY_CALIBRATION_PROFILE}, critic {CRITIC_CALIBRATION_PROFILE}, "
        f"router {ROUTER_CALIBRATION_PROFILE}, fallback {FALLBACK_CALIBRATION_PROFILE}"
    )
    runtime_override_summary = _build_runtime_override_summary()
    codex_summary = _format_codex_control_inline(codex_control)
    codex_risk = getattr(codex_control, "latest_risk", None) or "unknown"
    codex_debts = _format_codex_open_debts(codex_control)
    codex_good = getattr(codex_control, "latest_known_good", None) or "sin zona estable declarada"
    codex_weakness = getattr(codex_control, "latest_known_weakness", None) or "sin debilidad declarada"

    return (
        f"Estado actual: version AURA V{aura_version}; "
        f"modelo configurado: {model_name} ({primary_status}, {transitional_marker}); "
        f"ruta del modelo: {effective_model_path}; "
        f"llama-cli: {llama_status}; "
        f"ruta de llama-cli: {llama_path}; "
        f"providers: primary {primary_descriptor.provider_id if primary_descriptor else 'sin provider'} / {primary_descriptor.model_id if primary_descriptor else 'sin modelo'} ({primary_status}), "
        f"critic {critic_descriptor.provider_id if critic_descriptor else 'sin provider'} / {critic_descriptor.model_id if critic_descriptor else 'sin modelo'} ({critic_status}), "
        f"router {router_descriptor.provider_id if router_descriptor else 'sin provider'} / {router_descriptor.model_id if router_descriptor else 'sin modelo'} ({router_status}), "
        f"fallback {fallback_descriptor.provider_id if fallback_descriptor else 'sin provider'} / {fallback_descriptor.model_id if fallback_descriptor else 'sin modelo'} ({fallback_status}); "
        f"stack activo: multimodelo local abierto, backend {runtime_backend}, artefacto {artifact_format}, health {stack_health}; "
        "roles del corazon: Granite primary, OLMo critic/verifier, SmolLM2 router/helper, Qwen fallback transicional; "
        f"calibracion V0.39.6: {calibration_summary}; "
        f"allowlist verde: {allowlist_summary}; "
        f"banco de modelos: produccion {production_summary}; "
        f"candidatos inmediatos {candidate_summary}; "
        f"laboratorio {lab_summary}; "
        f"{governance_summary}; "
        f"bootstrap Windows: {runtime_override_summary}; "
        f"{routing_summary}; "
        f"checkpoint Codex: {codex_summary}; zona estable {codex_good}; punto debil {codex_weakness}; deuda abierta {codex_debts}; riesgo reciente {codex_risk}; "
        f"memoria cargada: {memory_summary}."
    )


def execute_system_state_command(
    command: SystemStateCommand,
    memory: dict[str, Any],
    aura_version: str,
    model_path: str,
    llama_path: str,
    conversation: list[dict[str, Any]] | None = None,
    log_file: str | None = None,
) -> str:
    if command.target == SYSTEM_TARGET_STATE:
        return _build_state_response_v0394(
            memory,
            aura_version,
            model_path,
            llama_path,
            conversation=conversation,
            log_file=log_file,
        )

    if command.target == SYSTEM_TARGET_MODEL_NAME:
        return _build_model_name_response(model_path, llama_path)

    if command.target == SYSTEM_TARGET_MODEL_PATH:
        return _build_model_path_response(model_path, llama_path)

    if command.target == SYSTEM_TARGET_LLAMA_PATH:
        return _build_llama_path_response(llama_path)

    if command.target == SYSTEM_TARGET_MODEL_AVAILABLE:
        return _build_model_available_response(model_path, llama_path)

    if command.target == SYSTEM_TARGET_VERSION:
        return _build_version_response(aura_version)

    if command.target == SYSTEM_TARGET_LOADED_MEMORY:
        return _build_loaded_memory_response(memory)

    if command.target == SYSTEM_TARGET_ROUTING_RECENT:
        return _build_routing_recent_response(
            conversation=conversation,
            log_file=log_file,
        )

    if command.target == SYSTEM_TARGET_ROUTING_ACTIVE:
        return _build_routing_active_response()

    if command.target == SYSTEM_TARGET_ROUTING_PAUSED:
        return _build_routing_paused_response()

    if command.target == SYSTEM_TARGET_ROUTING_ALERTS:
        return _build_routing_alerts_response()

    if command.target == SYSTEM_TARGET_ROUTING_TOP_SCORE:
        return _build_routing_top_score_response()

    if command.target == SYSTEM_TARGET_ROUTING_READINESS:
        return _build_routing_readiness_response()

    if command.target == SYSTEM_TARGET_ROUTING_WATCH:
        return _build_routing_watch_response()

    if command.target == SYSTEM_TARGET_ROUTING_REVIEW:
        return _build_routing_review_response()

    if command.target == SYSTEM_TARGET_ROUTING_LOG:
        return _build_routing_log_response()

    if command.target == SYSTEM_TARGET_ROUTING_REVIEW_OPEN:
        return _build_routing_open_reviews_response()

    if command.target == SYSTEM_TARGET_ROUTING_REVIEW_RESOLVED:
        return _build_routing_resolved_reviews_response()

    if command.target == SYSTEM_TARGET_ROUTING_REOPENED_ALERTS:
        return _build_routing_reopened_alerts_response()

    if command.target == SYSTEM_TARGET_ROUTING_ACTIONS_HELPED:
        return _build_routing_actions_helped_response()

    if command.target == SYSTEM_TARGET_ROUTING_STALE:
        return _build_routing_stale_response()

    if command.target == SYSTEM_TARGET_ROUTING_USEFUL:
        return _build_routing_useful_response()

    if command.target == SYSTEM_TARGET_ROUTING_SHORTLIST:
        return _build_routing_shortlist_response()

    if command.target == SYSTEM_TARGET_ROUTING_NOISE:
        return _build_routing_noise_response()

    if command.target == SYSTEM_TARGET_ROUTING_BRIDGE:
        return _build_routing_bridge_response()

    if command.target == SYSTEM_TARGET_ROUTING_BRIDGE_READY:
        return _build_routing_bridge_ready_response()

    if command.target == SYSTEM_TARGET_ROUTING_BRIDGE_BLOCKED:
        return _build_routing_bridge_blocked_response()

    if command.target == SYSTEM_TARGET_ROUTING_BRIDGE_DEFERRED:
        return _build_routing_bridge_deferred_response()

    if command.target == SYSTEM_TARGET_ROUTING_BRIDGE_FIT:
        return _build_routing_bridge_fit_response()

    if command.target == SYSTEM_TARGET_ROUTING_REHEARSAL:
        return _build_routing_rehearsal_response()

    if command.target == SYSTEM_TARGET_ROUTING_REHEARSAL_READY:
        return _build_routing_rehearsal_ready_response()

    if command.target == SYSTEM_TARGET_ROUTING_CUTOVER_NEAR_GO:
        return _build_routing_cutover_near_go_response()

    if command.target == SYSTEM_TARGET_ROUTING_ROLLBACK_RISKS:
        return _build_routing_rollback_risks_response()

    if command.target == SYSTEM_TARGET_ROUTING_LAUNCH_DOSSIER:
        return _build_routing_launch_dossier_response()

    if command.target == SYSTEM_TARGET_ROUTING_APPROVED:
        snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
        return _build_routing_launch_status_response(
            status_ids=snapshot.approved_ids,
            empty_label="neuronas aprobadas para V0.39 todavía",
            label="Neuronas aprobadas para V0.39",
        )

    if command.target == SYSTEM_TARGET_ROUTING_SUPPORT_ONLY:
        snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
        return _build_routing_launch_status_response(
            status_ids=snapshot.support_only_ids,
            empty_label="neuronas support-only para esta ola",
            label="Neuronas support-only",
        )

    if command.target == SYSTEM_TARGET_ROUTING_HOLD:
        snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
        return _build_routing_launch_status_response(
            status_ids=snapshot.hold_ids,
            empty_label="neuronas on hold ahora",
            label="Neuronas on hold",
        )

    if command.target == SYSTEM_TARGET_ROUTING_REJECTED:
        snapshot = build_routing_repertoire_snapshot(get_default_routing_registry())
        return _build_routing_launch_status_response(
            status_ids=snapshot.rejected_ids,
            empty_label="neuronas rechazadas en esta ola ahora",
            label="Neuronas rechazadas",
        )

    if command.target == SYSTEM_TARGET_ROUTING_ACTIVATION_ORDER:
        return _build_routing_activation_order_response()

    if command.target == SYSTEM_TARGET_ROUTING_CHECKPOINT:
        return _build_routing_checkpoint_response_v11(
            conversation=conversation,
            log_file=log_file,
        )

    if command.target == SYSTEM_TARGET_CODEX_LATEST:
        return _build_codex_registry_response()

    if command.target == SYSTEM_TARGET_CODEX_STATUS:
        return _build_codex_registry_response(status_only=True)

    if command.target == SYSTEM_TARGET_CODEX_CHANGES:
        return _build_codex_registry_response(include_changes=True)

    if command.target == SYSTEM_TARGET_CODEX_DEBTS:
        return _build_codex_registry_response(debts_only=True)

    if command.target == SYSTEM_TARGET_CODEX_CLOSED_VERSION:
        return _build_codex_registry_response(closed_version_only=True)

    if command.target == SYSTEM_TARGET_CODEX_PENDING:
        return _build_codex_registry_response(pending_only=True)

    if command.target == SYSTEM_TARGET_CODEX_STABLE:
        return _build_codex_stable_response()

    if command.target == SYSTEM_TARGET_CODEX_WEAK:
        return _build_codex_weak_response()

    if command.target == SYSTEM_TARGET_CODEX_RISK_NOW:
        return _build_codex_risk_now_response()

    if command.target == SYSTEM_TARGET_CODEX_RECOMMENDED:
        return _build_codex_recommended_response()

    if command.target == SYSTEM_TARGET_CODEX_REVIEW_NOW:
        return _build_codex_review_now_response()

    if command.target == SYSTEM_TARGET_CODEX_PLAN_NOW:
        return _build_codex_plan_now_response()

    if command.target == SYSTEM_TARGET_CODEX_DO_NOT_TOUCH:
        return _build_codex_do_not_touch_response()

    if command.target == SYSTEM_TARGET_CODEX_MODEL_CHOICE:
        return _resolve_model_choice_response(conversation)

    if command.target == SYSTEM_TARGET_ROUTING_ROLLBACK_PLAN:
        return _build_routing_rollback_plan_response(command.neuron_id)

    if command.target == SYSTEM_TARGET_ROUTING_DEPENDENCIES:
        return _build_routing_dependencies_response(command.neuron_id)

    if command.target == SYSTEM_TARGET_ROUTING_LAUNCH_REASON:
        return _build_routing_launch_reason_response(command.neuron_id)

    if command.target == SYSTEM_TARGET_ROUTING_SELECTION_REASON:
        return _build_routing_selection_reason_response(command.neuron_id)

    if command.target == SYSTEM_TARGET_ROUTING_BRIDGE_REASON:
        return _build_routing_bridge_reason_response(command.neuron_id)

    if command.target == SYSTEM_TARGET_ROUTING_CUTOVER_REASON:
        return _build_routing_cutover_reason_response(command.neuron_id)

    return "No pude leer ese estado interno."
