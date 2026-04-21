from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .capabilities_registry import CapabilityContext, CapabilityExecution


TOOL_HELP_CATALOGS = "help_catalogs"
TOOL_USER_MEMORY = "user_memory"
TOOL_SYSTEM_STATE_READER = "system_state_reader"
TOOL_MAINTENANCE_CONSOLE = "maintenance_console"
TOOL_COMPOSITE_DIAGNOSTICS = "composite_diagnostics"
TOOL_COMPOSITE_REVIEWS = "composite_reviews"
TOOL_RESPONSE_HEURISTICS = "response_heuristics"
TOOL_LOCAL_MODEL_RUNTIME = "local_model_runtime"
TOOL_SESSION_CONTROL = "session_control"

INTERNAL_TOOL_ORDER = (
    TOOL_HELP_CATALOGS,
    TOOL_USER_MEMORY,
    TOOL_SYSTEM_STATE_READER,
    TOOL_MAINTENANCE_CONSOLE,
    TOOL_COMPOSITE_DIAGNOSTICS,
    TOOL_COMPOSITE_REVIEWS,
    TOOL_LOCAL_MODEL_RUNTIME,
    TOOL_SESSION_CONTROL,
)


@dataclass(frozen=True)
class InternalToolDefinition:
    name: str
    label: str
    category: str
    kind: str
    description: str
    catalog_label: str
    catalog_summary: str
    status: str
    handler: Callable[[InternalToolInvocation], CapabilityExecution]


@dataclass(frozen=True)
class InternalToolInvocation:
    tool_definition: InternalToolDefinition
    capability: str
    action_name: str | None
    action_category: str | None
    action_description: str | None
    action_examples: tuple[str, ...]
    context: CapabilityContext
    sequence_name: str | None = None
    sequence_kind: str | None = None
    sequence_goal: str | None = None
    summary_mode: str | None = None
    adaptive_mode: str | None = None
    readiness_status: str | None = None
    priority_focus: str | None = None
    dominant_limitation: str | None = None
    dominant_strength: str | None = None
    recommendation_level: str | None = None
    contextual_mode: str | None = None
    diagnostic_scope: str | None = None
    readiness_reason: str | None = None
    suggested_next_step: str | None = None
    main_help_scope: str | None = None
    strategic_mode: str | None = None
    recommended_focus: str | None = None
    recommended_action: str | None = None
    next_step_type: str | None = None
    readiness_path: str | None = None
    limitation_severity: str | None = None
    recommendation_style: str | None = None
    recommendation_priority: str | None = None
    recommendation_basis: str | None = None
    decision_focus: str | None = None
    actionability_level: str | None = None
    advice_scope: str | None = None
    situational_profile: str | None = None
    advice_frame: str | None = None
    recommended_order: tuple[str, ...] | None = None
    blocker_type: str | None = None
    opportunity_focus: str | None = None
    recovery_strategy: str | None = None
    exploitation_path: str | None = None
    moment_profile: str | None = None
    next_move_chain: tuple[str, ...] | None = None
    move_priority: str | None = None
    move_count: int | None = None
    guidance_mode: str | None = None
    followup_trigger: str | None = None
    sequence_confidence: str | None = None
    momentum_type: str | None = None
    micro_plan: tuple[str, ...] | None = None
    plan_horizon: str | None = None
    now_step: str | None = None
    next_step: str | None = None
    later_step: str | None = None
    planning_mode: str | None = None
    sequence_depth: int | None = None
    plan_confidence: str | None = None
    followup_priority: str | None = None
    feasibility_status: str | None = None
    feasibility_reason: str | None = None
    feasibility_scope: str | None = None
    contradiction_detected: bool | None = None
    uncertainty_level: str | None = None
    realism_level: str | None = None
    conditions_required: tuple[str, ...] | None = None
    feasibility_frame: str | None = None
    viability_basis: str | None = None
    primary_constraint: str | None = None
    plausibility_mode: str | None = None
    confidence_level: str | None = None
    consistency_status: str | None = None
    consistency_reason: str | None = None
    evidence_sufficiency: str | None = None
    claim_strength: str | None = None
    ambiguity_detected: bool | None = None
    assumption_load: str | None = None
    required_evidence: tuple[str, ...] | None = None
    certainty_frame: str | None = None
    revision_trigger: str | None = None
    contextual_tension: str | None = None
    recent_context_conflict: bool | None = None
    judgment_mode: str | None = None


def _build_execution(
    response: str | None,
    should_exit: bool = False,
    used_model: bool | None = None,
    used_memory_override: bool | None = None,
    task_type: str | None = None,
    routing_decision: str | None = None,
    selected_provider: str | None = None,
    selected_role: str | None = None,
    provider_available: bool | None = None,
    provider_attempts: tuple[str, ...] | None = None,
    fallback_used: bool | None = None,
    fallback_reason: str | None = None,
    composition_mode: str | None = None,
    critic_requested: bool | None = None,
    critic_used: bool | None = None,
    critic_provider: str | None = None,
    critic_available: bool | None = None,
    critic_result_status: str | None = None,
    critic_summary: str | None = None,
    verification_outcome: str | None = None,
    verification_mode: str | None = None,
    no_model_reason: str | None = None,
    provider_trace: tuple[str, ...] | None = None,
    gateway_mode: str | None = None,
    provider_result_status: str | None = None,
    runtime_quality_status: str | None = None,
    degradation_hint: str | None = None,
    critic_value: str | None = None,
    router_value: str | None = None,
    fallback_pressure: str | None = None,
    routing_neuron_applied: bool | None = None,
    routing_neuron_id: str | None = None,
    routing_neuron_state: str | None = None,
    routing_neuron_type: str | None = None,
    routing_neuron_influence: str | None = None,
    routing_neuron_trace: tuple[str, ...] | None = None,
    routing_neuron_conflict: str | None = None,
    routing_neuron_fallback_reason: str | None = None,
    routing_neuron_decision: str | None = None,
    routing_neuron_alerts: tuple[str, ...] | None = None,
    routing_neuron_considered: bool | None = None,
    routing_neuron_considered_ids: tuple[str, ...] | None = None,
    routing_neuron_selected: bool | None = None,
    routing_neuron_barriers_checked: tuple[str, ...] | None = None,
    routing_neuron_barriers_blocked: tuple[str, ...] | None = None,
    routing_neuron_conflict_resolution: str | None = None,
    routing_neuron_outcome_label: str | None = None,
    routing_neuron_decision_path: str | None = None,
) -> CapabilityExecution:
    from .capabilities_registry import CapabilityExecution

    return CapabilityExecution(
        response=response,
        should_exit=should_exit,
        used_model=used_model,
        used_memory_override=used_memory_override,
        task_type=task_type,
        routing_decision=routing_decision,
        selected_provider=selected_provider,
        selected_role=selected_role,
        provider_available=provider_available,
        provider_attempts=provider_attempts,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        composition_mode=composition_mode,
        critic_requested=critic_requested,
        critic_used=critic_used,
        critic_provider=critic_provider,
        critic_available=critic_available,
        critic_result_status=critic_result_status,
        critic_summary=critic_summary,
        verification_outcome=verification_outcome,
        verification_mode=verification_mode,
        no_model_reason=no_model_reason,
        provider_trace=provider_trace,
        gateway_mode=gateway_mode,
        provider_result_status=provider_result_status,
        runtime_quality_status=runtime_quality_status,
        degradation_hint=degradation_hint,
        critic_value=critic_value,
        router_value=router_value,
        fallback_pressure=fallback_pressure,
        routing_neuron_applied=routing_neuron_applied,
        routing_neuron_id=routing_neuron_id,
        routing_neuron_state=routing_neuron_state,
        routing_neuron_type=routing_neuron_type,
        routing_neuron_influence=routing_neuron_influence,
        routing_neuron_trace=routing_neuron_trace,
        routing_neuron_conflict=routing_neuron_conflict,
        routing_neuron_fallback_reason=routing_neuron_fallback_reason,
        routing_neuron_decision=routing_neuron_decision,
        routing_neuron_alerts=routing_neuron_alerts,
        routing_neuron_considered=routing_neuron_considered,
        routing_neuron_considered_ids=routing_neuron_considered_ids,
        routing_neuron_selected=routing_neuron_selected,
        routing_neuron_barriers_checked=routing_neuron_barriers_checked,
        routing_neuron_barriers_blocked=routing_neuron_barriers_blocked,
        routing_neuron_conflict_resolution=routing_neuron_conflict_resolution,
        routing_neuron_outcome_label=routing_neuron_outcome_label,
        routing_neuron_decision_path=routing_neuron_decision_path,
    )


def _handle_help_catalogs(invocation: InternalToolInvocation) -> CapabilityExecution:
    from .internal_actions_registry import (
        ACTION_INTERNAL_OPERATIONS_CATALOG,
        ACTION_INTERNAL_TOOLS_CATALOG,
    )

    if invocation.action_name == ACTION_INTERNAL_OPERATIONS_CATALOG:
        from .operations_agent import build_internal_operations_response

        return _build_execution(
            response=build_internal_operations_response(invocation.context.operations_query),
            used_memory_override=False,
        )

    if invocation.action_name == ACTION_INTERNAL_TOOLS_CATALOG:
        from .internal_tools_agent import build_internal_tools_response

        return _build_execution(
            response=build_internal_tools_response(
                invocation.context.tools_query,
                context=invocation.context,
            ),
            used_memory_override=False,
        )

    from .capabilities_agent import build_capabilities_response

    return _build_execution(
        response=build_capabilities_response(),
        used_memory_override=False,
    )


def _handle_user_memory(invocation: InternalToolInvocation) -> CapabilityExecution:
    context = invocation.context

    if context.internal_command is not None:
        from .internal_commands_agent import execute_internal_command

        return _build_execution(
            response=execute_internal_command(
                context.internal_command,
                memory=context.memory,
                memory_file=context.memory_file,
            ),
            used_memory_override=True,
        )

    if invocation.capability == "memory_lookup":
        from .memory_agent import build_memory_response

        return _build_execution(
            response=build_memory_response(context.memory, context.memory_intent),
            used_memory_override=True,
        )

    if invocation.capability == "memory_lookup_ambiguous":
        from .memory_agent import build_ambiguous_memory_response

        return _build_execution(
            response=build_ambiguous_memory_response(
                context.memory,
                context.memory_intent,
            ),
            used_memory_override=True,
        )

    if invocation.capability == "memory_update":
        from .behavior_agent import build_memory_update_response

        return _build_execution(
            response=build_memory_update_response(context.user_input_raw, context.memory),
            used_memory_override=True,
        )

    if invocation.capability == "repetition":
        from .behavior_agent import build_repetition_response

        return _build_execution(
            response=build_repetition_response(context.user_input_raw, context.memory),
            used_memory_override=True,
        )

    return _build_execution(
        response="No pude resolver esa operación interna de memoria.",
        used_memory_override=True,
    )


def _handle_system_state_reader(invocation: InternalToolInvocation) -> CapabilityExecution:
    from .system_state_agent import (
        SYSTEM_TARGET_LOADED_MEMORY,
        SYSTEM_TARGET_STATE,
        execute_system_state_command,
    )

    command = invocation.context.system_state_command
    if command is None:
        return _build_execution(response="No pude leer ese estado interno.")

    return _build_execution(
        response=execute_system_state_command(
            command,
            memory=invocation.context.memory,
            aura_version=invocation.context.aura_version,
            model_path=invocation.context.model_path,
            llama_path=invocation.context.llama_path,
            conversation=invocation.context.conversation,
            log_file=invocation.context.log_file,
        ),
        used_memory_override=command.target in {
            SYSTEM_TARGET_STATE,
            SYSTEM_TARGET_LOADED_MEMORY,
        },
    )


def _handle_maintenance_console(invocation: InternalToolInvocation) -> CapabilityExecution:
    from .maintenance_agent import (
        MAINTENANCE_TARGET_CLEAN_MEMORY,
        MAINTENANCE_TARGET_CORRECT_PREFERENCES,
        MAINTENANCE_TARGET_RELOAD_MEMORY,
        MAINTENANCE_TARGET_REVIEW_MEMORY,
        MAINTENANCE_TARGET_VALIDATE_CONFIG,
        execute_maintenance_command,
    )

    command = invocation.context.maintenance_command
    if command is None:
        return _build_execution(response="No pude ejecutar ese mantenimiento interno.")

    return _build_execution(
        response=execute_maintenance_command(
            command,
            conversation=invocation.context.conversation,
            memory=invocation.context.memory,
            memory_file=invocation.context.memory_file,
            log_file=invocation.context.log_file,
            aura_version=invocation.context.aura_version,
            model_path=invocation.context.model_path,
            llama_path=invocation.context.llama_path,
        ),
        used_memory_override=command.target in {
            MAINTENANCE_TARGET_VALIDATE_CONFIG,
            MAINTENANCE_TARGET_REVIEW_MEMORY,
            MAINTENANCE_TARGET_RELOAD_MEMORY,
            MAINTENANCE_TARGET_CLEAN_MEMORY,
            MAINTENANCE_TARGET_CORRECT_PREFERENCES,
        },
    )


def _handle_composite_diagnostics(invocation: InternalToolInvocation) -> CapabilityExecution:
    from .internal_tools_agent import (
        build_internal_sequence_response,
    )

    response = build_internal_sequence_response(
        invocation.sequence_name,
        invocation.context,
    )

    return _build_execution(
        response=response,
        used_memory_override=True,
    )


def _handle_composite_reviews(invocation: InternalToolInvocation) -> CapabilityExecution:
    from .internal_tools_agent import (
        build_internal_sequence_response,
    )

    response = build_internal_sequence_response(
        invocation.sequence_name,
        invocation.context,
    )

    return _build_execution(
        response=response,
        used_memory_override=True,
    )


def _handle_response_heuristics(invocation: InternalToolInvocation) -> CapabilityExecution:
    return _build_execution(
        response=invocation.context.behavior_plan.direct_response,
        used_model=False,
        used_memory_override=False,
        task_type="no_model_needed",
        routing_decision="skip_model",
        provider_available=None,
        provider_attempts=(),
        fallback_used=False,
        composition_mode="heuristic_direct",
        critic_requested=False,
        critic_used=False,
        no_model_reason="behavior_direct_response",
        provider_trace=("gateway:no_model",),
        gateway_mode="no_model",
        runtime_quality_status="not_applicable",
        degradation_hint=None,
        critic_value="not_requested",
        router_value="not_needed",
    )


def _handle_local_model_runtime(invocation: InternalToolInvocation) -> CapabilityExecution:
    from .response_agent import execute_model_response

    execution = execute_model_response(
        conversation=invocation.context.conversation,
        memory=invocation.context.memory,
        llama_path=invocation.context.llama_path,
        model_path=invocation.context.model_path,
        behavior_plan=invocation.context.behavior_plan,
        route_action=invocation.context.route_action,
        session_id=invocation.context.log_file,
    )
    return _build_execution(
        response=execution.response,
        used_model=execution.used_model,
        task_type=execution.task_type,
        routing_decision=execution.routing_decision,
        selected_provider=execution.selected_provider,
        selected_role=execution.selected_role,
        provider_available=execution.provider_available,
        provider_attempts=execution.provider_attempts,
        fallback_used=execution.fallback_used,
        fallback_reason=execution.fallback_reason,
        composition_mode=execution.composition_mode,
        critic_requested=execution.critic_requested,
        critic_used=execution.critic_used,
        critic_provider=execution.critic_provider,
        critic_available=execution.critic_available,
        critic_result_status=execution.critic_result_status,
        critic_summary=execution.critic_summary,
        verification_outcome=execution.verification_outcome,
        verification_mode=execution.verification_mode,
        no_model_reason=execution.no_model_reason,
        provider_trace=execution.provider_trace,
        gateway_mode=execution.gateway_mode,
        provider_result_status=execution.provider_result_status,
        runtime_quality_status=execution.runtime_quality_status,
        degradation_hint=execution.degradation_hint,
        critic_value=execution.critic_value,
        router_value=execution.router_value,
        fallback_pressure=execution.fallback_pressure,
        routing_neuron_applied=execution.routing_neuron_applied,
        routing_neuron_id=execution.routing_neuron_id,
        routing_neuron_state=execution.routing_neuron_state,
        routing_neuron_type=execution.routing_neuron_type,
        routing_neuron_influence=execution.routing_neuron_influence,
        routing_neuron_trace=execution.routing_neuron_trace,
        routing_neuron_conflict=execution.routing_neuron_conflict,
        routing_neuron_fallback_reason=execution.routing_neuron_fallback_reason,
        routing_neuron_decision=execution.routing_neuron_decision,
        routing_neuron_alerts=execution.routing_neuron_alerts,
        routing_neuron_considered=execution.routing_neuron_considered,
        routing_neuron_considered_ids=execution.routing_neuron_considered_ids,
        routing_neuron_selected=execution.routing_neuron_selected,
        routing_neuron_barriers_checked=execution.routing_neuron_barriers_checked,
        routing_neuron_barriers_blocked=execution.routing_neuron_barriers_blocked,
        routing_neuron_conflict_resolution=execution.routing_neuron_conflict_resolution,
        routing_neuron_outcome_label=execution.routing_neuron_outcome_label,
        routing_neuron_decision_path=execution.routing_neuron_decision_path,
    )


def _handle_session_control(invocation: InternalToolInvocation) -> CapabilityExecution:
    del invocation
    return _build_execution(response=None, should_exit=True)


INTERNAL_TOOLS_REGISTRY = {
    TOOL_HELP_CATALOGS: InternalToolDefinition(
        name=TOOL_HELP_CATALOGS,
        label="Ayuda",
        category="help",
        kind="base",
        description="Tool interna para catálogos, orientación de uso y acceso visible a las capas del núcleo.",
        catalog_label="ayuda interna",
        catalog_summary="catálogos y orientación de uso del sistema",
        status="active",
        handler=_handle_help_catalogs,
    ),
    TOOL_USER_MEMORY: InternalToolDefinition(
        name=TOOL_USER_MEMORY,
        label="Memoria",
        category="memory",
        kind="base",
        description="Tool interna para lectura, actualizacion y olvido de memoria del usuario.",
        catalog_label="memoria del usuario",
        catalog_summary="lectura, actualización y olvido de memoria guardada",
        status="active",
        handler=_handle_user_memory,
    ),
    TOOL_SYSTEM_STATE_READER: InternalToolDefinition(
        name=TOOL_SYSTEM_STATE_READER,
        label="Estado interno",
        category="system",
        kind="base",
        description="Tool interna para version, modelo, rutas, disponibilidad y memoria cargada.",
        catalog_label="estado interno",
        catalog_summary="estado, versión, modelo, rutas, disponibilidad y memoria cargada",
        status="active",
        handler=_handle_system_state_reader,
    ),
    TOOL_MAINTENANCE_CONSOLE: InternalToolDefinition(
        name=TOOL_MAINTENANCE_CONSOLE,
        label="Mantenimiento",
        category="maintenance",
        kind="base",
        description="Tool interna para validacion, limpieza, recarga y resumenes operativos.",
        catalog_label="mantenimiento interno",
        catalog_summary="validación de configuración, memoria, logs y turnos del núcleo",
        status="active",
        handler=_handle_maintenance_console,
    ),
    TOOL_COMPOSITE_DIAGNOSTICS: InternalToolDefinition(
        name=TOOL_COMPOSITE_DIAGNOSTICS,
        label="Diagnósticos compuestos",
        category="system",
        kind="composite",
        description="Tool compuesta para diagnósticos, chequeos y lecturas compactas del estado del núcleo.",
        catalog_label="diagnósticos del núcleo",
        catalog_summary="diagnósticos, chequeos y lectura priorizada del estado del núcleo",
        status="active",
        handler=_handle_composite_diagnostics,
    ),
    TOOL_COMPOSITE_REVIEWS: InternalToolDefinition(
        name=TOOL_COMPOSITE_REVIEWS,
        label="Revisiones compuestas",
        category="maintenance",
        kind="composite",
        description="Tool compuesta para revisiones y recomendación situacional con memoria, estado y actividad reciente.",
        catalog_label="revisiones del núcleo",
        catalog_summary="revisiones operativas y recomendación del siguiente paso útil",
        status="active",
        handler=_handle_composite_reviews,
    ),
    TOOL_RESPONSE_HEURISTICS: InternalToolDefinition(
        name=TOOL_RESPONSE_HEURISTICS,
        label="Respuesta heurística",
        category="assistant",
        kind="base",
        description="Tool interna para respuestas directas resueltas desde heurística sin usar provider de modelo.",
        catalog_label="heurísticas de respuesta",
        catalog_summary="respuestas directas sin uso real de modelo",
        status="active",
        handler=_handle_response_heuristics,
    ),
    TOOL_LOCAL_MODEL_RUNTIME: InternalToolDefinition(
        name=TOOL_LOCAL_MODEL_RUNTIME,
        label="Modelo local",
        category="assistant",
        kind="base",
        description="Tool interna para respuestas asistidas por el modelo local.",
        catalog_label="soporte del modelo local",
        catalog_summary="respuestas generales o técnicas con el runtime local",
        status="active",
        handler=_handle_local_model_runtime,
    ),
    TOOL_SESSION_CONTROL: InternalToolDefinition(
        name=TOOL_SESSION_CONTROL,
        label="Sesión",
        category="session",
        kind="base",
        description="Tool interna para cierre ordenado de sesion.",
        catalog_label="sesión",
        catalog_summary="cierre ordenado de la sesión",
        status="active",
        handler=_handle_session_control,
    ),
}

TOOLS_REGISTRY = INTERNAL_TOOLS_REGISTRY


def get_internal_tool_definition(tool_name: str) -> InternalToolDefinition:
    tool_definition = INTERNAL_TOOLS_REGISTRY.get(tool_name)
    if tool_definition is None:
        raise KeyError(f"Herramienta interna desconocida: {tool_name}")

    return tool_definition


def get_internal_tools_in_order() -> tuple[InternalToolDefinition, ...]:
    return tuple(
        INTERNAL_TOOLS_REGISTRY[tool_name]
        for tool_name in INTERNAL_TOOL_ORDER
        if tool_name in INTERNAL_TOOLS_REGISTRY
    )
