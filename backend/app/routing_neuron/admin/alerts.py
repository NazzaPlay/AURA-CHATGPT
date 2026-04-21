"""Alert views for Routing Neuron V1."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.runtime import get_default_routing_registry
from .repertoire import build_admin_state


@dataclass(frozen=True)
class RoutingAlertView:
    neuron_id: str
    alerts: tuple[str, ...]
    review_status: str
    alert_status: str


def list_alert_views(registry=None) -> tuple[RoutingAlertView, ...]:
    resolved_registry = registry or get_default_routing_registry()
    state = build_admin_state(resolved_registry)
    return tuple(
        RoutingAlertView(
            neuron_id=entry.neuron_id,
            alerts=entry.alerts,
            review_status=entry.review_status,
            alert_status=entry.alert_status,
        )
        for entry in state.snapshot.entries
        if entry.alerts or entry.alert_status != "none"
    )


__all__ = ["RoutingAlertView", "list_alert_views"]
