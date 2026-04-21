from __future__ import annotations

from dataclasses import dataclass

from .critic_layer import CriticPlan, CRITIC_MODE_CRITIC_ONLY
from .model_registry import ModelRegistry, ROLE_CRITIC
from .task_classifier import TaskClassification


@dataclass(frozen=True)
class RoutingDecision:
    task_type: str
    routing_decision: str
    selected_provider: str | None
    selected_role: str | None
    provider_available: bool | None
    critic_requested: bool
    critic_used: bool
    critic_provider: str | None
    critic_role: str | None
    critic_available: bool | None
    no_model_reason: str | None
    gateway_mode: str
    policy_mode: str = "balanced_runtime"
    decision_reason: str | None = None


def _resolve_provider_availability(
    registry: ModelRegistry,
    role: str | None,
) -> tuple[str | None, bool | None]:
    if role is None:
        return None, None

    provider = registry.get_provider_for_role(role)
    if provider is None:
        return None, False

    available, _ = provider.check_availability()
    return provider.descriptor.provider_id, available


def decide_routing(
    task: TaskClassification,
    registry: ModelRegistry,
    critic_plan: CriticPlan,
) -> RoutingDecision:
    critic_requested = (
        critic_plan.requested
        and task.critic_requested
        and task.critic_role is not None
    )

    if task.no_model_needed:
        return RoutingDecision(
            task_type=task.task_type,
            routing_decision="skip_model",
            selected_provider=None,
            selected_role=None,
            provider_available=None,
            critic_requested=False,
            critic_used=False,
            critic_provider=None,
            critic_role=None,
            critic_available=None,
            no_model_reason=task.no_model_reason,
            gateway_mode="no_model",
            policy_mode="no_model",
            decision_reason=task.no_model_reason or "task_resolved_without_model",
        )

    selected_provider, provider_available = _resolve_provider_availability(
        registry,
        task.requested_role,
    )

    if selected_provider is None:
        return RoutingDecision(
            task_type=task.task_type,
            routing_decision="missing_provider_for_role",
            selected_provider=None,
            selected_role=task.requested_role,
            provider_available=False,
            critic_requested=critic_requested,
            critic_used=False,
            critic_provider=None,
            critic_role=critic_plan.role,
            critic_available=False if critic_plan.role else None,
            no_model_reason=None,
            gateway_mode="provider_missing",
            policy_mode="provider_missing",
            decision_reason="requested_role_without_provider",
        )

    if task.requested_role == ROLE_CRITIC and not task.critic_requested:
        return RoutingDecision(
            task_type=task.task_type,
            routing_decision="critic_only",
            selected_provider=selected_provider,
            selected_role=task.requested_role,
            provider_available=provider_available,
            critic_requested=False,
            critic_used=False,
            critic_provider=None,
            critic_role=None,
            critic_available=None,
            no_model_reason=None,
            gateway_mode="critic_only",
            policy_mode="critic_direct",
            decision_reason="critic_role_direct_request",
        )

    critic_provider = None
    critic_available = None
    critic_role = None
    routing_decision = "primary_only"
    gateway_mode = "primary_only"
    policy_mode = "primary_guarded"
    decision_reason = "low_risk_primary_only"

    if critic_requested:
        critic_provider, critic_available = _resolve_provider_availability(
            registry,
            task.critic_role,
        )
        critic_role = task.critic_role
        if critic_provider is not None and critic_available:
            routing_decision = "primary_then_critic"
            gateway_mode = "primary_then_critic"
            policy_mode = "primary_with_critic_guard"
            decision_reason = critic_plan.reason or task.critic_reason or "critic_second_pass_available"
        else:
            routing_decision = "primary_only"
            gateway_mode = "primary_only"
            policy_mode = "primary_only_degraded_guard"
            decision_reason = task.critic_reason or "critic_requested_but_unavailable"

    return RoutingDecision(
        task_type=task.task_type,
        routing_decision=routing_decision,
        selected_provider=selected_provider,
        selected_role=task.requested_role,
        provider_available=provider_available,
        critic_requested=critic_requested,
        critic_used=False,
        critic_provider=critic_provider,
        critic_role=critic_role,
        critic_available=critic_available,
        no_model_reason=None,
        gateway_mode=gateway_mode,
        policy_mode=policy_mode,
        decision_reason=decision_reason,
    )
