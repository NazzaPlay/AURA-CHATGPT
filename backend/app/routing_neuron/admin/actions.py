"""Administrative action helpers for Routing Neuron V1."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.runtime import get_default_routing_registry

SUPPORTED_ROUTING_ADMIN_ACTIONS = (
    "pause",
    "resume",
    "mark_watch",
    "clear_watch",
    "acknowledge_alert",
)


@dataclass(frozen=True)
class RoutingAdminActionView:
    action_id: str
    neuron_id: str
    action_type: str
    reason: str
    outcome: str | None
    review_status: str | None
    alert_status: str | None


def list_recent_admin_actions(registry=None, *, limit: int = 10) -> tuple[RoutingAdminActionView, ...]:
    resolved_registry = registry or get_default_routing_registry()
    recent = resolved_registry.admin_log[-limit:]
    return tuple(
        RoutingAdminActionView(
            action_id=action.action_id,
            neuron_id=action.neuron_id,
            action_type=action.action_type,
            reason=action.reason,
            outcome=action.outcome,
            review_status=action.review_status,
            alert_status=action.alert_status,
        )
        for action in recent
    )


__all__ = [
    "RoutingAdminActionView",
    "SUPPORTED_ROUTING_ADMIN_ACTIONS",
    "list_recent_admin_actions",
]
