"""Canonical Routing Neuron V1.x subsystem.

This package is the durable home for Routing Neuron going forward.
Legacy modules under ``agents/routing_*`` remain available for
compatibility with the current AURA runtime and test suite.
"""

from .admin.actions import SUPPORTED_ROUTING_ADMIN_ACTIONS, list_recent_admin_actions
from .admin.alerts import list_alert_views
from .admin.repertoire import build_admin_state
from .core.governor import build_governance_snapshot
from .core.maintenance import (
    build_routing_launch_dossier,
    build_routing_repertoire_snapshot,
    refresh_routing_session_summary,
    run_routing_maintenance,
)
from .control import (
    CODEX_CONTROL_REGISTRY_PATH,
    CODEX_CONTROL_SCHEMA_VERSION,
    build_codex_control_status,
    ensure_codex_control_registry,
    load_codex_control_registry,
    summarize_codex_control_status,
    summarize_codex_latest_checkpoint,
    update_codex_control_registry,
)
from .core.observer import build_task_signature, ingest_routing_observation
from .core.promoter import describe_promotion_path, resolve_next_promotion_stage
from .core.registry import build_empty_routing_neuron_registry, promote_routing_neuron
from .core.runtime import apply_routing_runtime, apply_runtime_to_routing_decision

__all__ = [
    "SUPPORTED_ROUTING_ADMIN_ACTIONS",
    "apply_routing_runtime",
    "apply_runtime_to_routing_decision",
    "build_admin_state",
    "build_codex_control_status",
    "build_empty_routing_neuron_registry",
    "build_governance_snapshot",
    "build_routing_launch_dossier",
    "build_routing_repertoire_snapshot",
    "build_task_signature",
    "CODEX_CONTROL_REGISTRY_PATH",
    "CODEX_CONTROL_SCHEMA_VERSION",
    "describe_promotion_path",
    "ensure_codex_control_registry",
    "ingest_routing_observation",
    "list_alert_views",
    "list_recent_admin_actions",
    "load_codex_control_registry",
    "promote_routing_neuron",
    "refresh_routing_session_summary",
    "resolve_next_promotion_stage",
    "run_routing_maintenance",
    "summarize_codex_control_status",
    "summarize_codex_latest_checkpoint",
    "update_codex_control_registry",
]
