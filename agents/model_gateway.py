from __future__ import annotations

from dataclasses import dataclass

from providers import PROVIDER_RESULT_SUCCESS, ProviderRequest

from .model_registry import ModelRegistry
from .routing_policy import RoutingDecision


@dataclass(frozen=True)
class GatewayResult:
    selected_provider: str | None
    selected_role: str | None
    provider_available: bool | None
    provider_attempts: tuple[str, ...]
    provider_result_status: str | None
    provider_response: str | None
    provider_error: str | None
    provider_trace: tuple[str, ...]
    gateway_mode: str


def invoke_model_gateway(
    prompt: str,
    routing_decision: RoutingDecision,
    registry: ModelRegistry,
    *,
    provider_id: str | None = None,
    role: str | None = None,
    trace_label: str = "primary",
) -> GatewayResult:
    selected_provider = provider_id or routing_decision.selected_provider
    selected_role = role or routing_decision.selected_role

    if not selected_provider or not selected_role:
        return GatewayResult(
            selected_provider=selected_provider,
            selected_role=selected_role,
            provider_available=routing_decision.provider_available,
            provider_attempts=(),
            provider_result_status=None,
            provider_response=None,
            provider_error=None,
            provider_trace=(
                f"gateway:{trace_label}:no_provider_selected",
                f"gateway:{trace_label}:role:{selected_role or 'none'}",
                f"gateway:{trace_label}:task:{routing_decision.task_type}",
            ),
            gateway_mode=routing_decision.gateway_mode,
        )

    provider = registry.get_provider(selected_provider)
    if provider is None:
        return GatewayResult(
            selected_provider=selected_provider,
            selected_role=selected_role,
            provider_available=False,
            provider_attempts=(selected_provider,),
            provider_result_status="provider_missing",
            provider_response=None,
            provider_error="provider_missing",
            provider_trace=(
                f"{trace_label}:selected:{selected_provider}",
                f"{trace_label}:role:{selected_role}",
                f"{trace_label}:task:{routing_decision.task_type}",
                f"{trace_label}:provider_missing",
            ),
            gateway_mode=routing_decision.gateway_mode,
        )

    descriptor = provider.descriptor
    result = provider.generate(
        ProviderRequest(
            prompt=prompt,
            role=selected_role,
            task_type=routing_decision.task_type,
        )
    )
    provider_trace = (
        f"{trace_label}:selected:{selected_provider}",
        f"{trace_label}:role:{selected_role}",
        f"{trace_label}:task:{routing_decision.task_type}",
        f"{trace_label}:gateway:{routing_decision.gateway_mode}",
        f"{trace_label}:policy:{routing_decision.policy_mode}",
        f"{trace_label}:backend:{descriptor.runtime_backend or descriptor.backend_type}",
        f"{trace_label}:family:{descriptor.family or 'unknown'}",
        f"{trace_label}:status:{result.status}",
    )
    if routing_decision.decision_reason:
        provider_trace = provider_trace + (
            f"{trace_label}:routing_reason:{routing_decision.decision_reason}",
        )
    if result.error:
        provider_trace = provider_trace + (f"{trace_label}:error:{result.error}",)
    return GatewayResult(
        selected_provider=selected_provider,
        selected_role=selected_role,
        provider_available=result.availability,
        provider_attempts=(selected_provider,),
        provider_result_status=result.status,
        provider_response=result.response if result.status == PROVIDER_RESULT_SUCCESS else None,
        provider_error=result.error,
        provider_trace=provider_trace + result.runtime_info,
        gateway_mode=routing_decision.gateway_mode,
    )
