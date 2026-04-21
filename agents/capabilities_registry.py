from dataclasses import dataclass
from typing import Any, Callable

from .behavior_agent import build_memory_update_response, build_repetition_response
from .internal_commands_agent import execute_internal_command
from .maintenance_agent import (
    MAINTENANCE_TARGET_CLEAN_MEMORY,
    MAINTENANCE_TARGET_CORRECT_PREFERENCES,
    MAINTENANCE_TARGET_RELOAD_MEMORY,
    MAINTENANCE_TARGET_REVIEW_MEMORY,
    MAINTENANCE_TARGET_VALIDATE_CONFIG,
    execute_maintenance_command,
)
from .memory_agent import build_ambiguous_memory_response, build_memory_response
from .response_agent import execute_model_response
from .system_state_agent import (
    SYSTEM_TARGET_LOADED_MEMORY,
    SYSTEM_TARGET_STATE,
    execute_system_state_command,
)


CAPABILITY_EXIT = "exit"
CAPABILITY_CAPABILITIES_CATALOG = "capabilities_catalog"
CAPABILITY_INTERNAL_OPERATIONS_CATALOG = "internal_operations_catalog"
CAPABILITY_INTERNAL_TOOLS_CATALOG = "internal_tools_catalog"
CAPABILITY_INTERNAL_TOOLS_ACTIVE = "internal_tools_active"
CAPABILITY_INTERNAL_COMMAND = "internal_command"
CAPABILITY_MAINTENANCE = "maintenance"
CAPABILITY_MEMORY_LOOKUP = "memory_lookup"
CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS = "memory_lookup_ambiguous"
CAPABILITY_MEMORY_UPDATE = "memory_update"
CAPABILITY_HEURISTIC_RESPONSE = "heuristic_response"
CAPABILITY_MODEL_RESPONSE = "model_response"
CAPABILITY_REPETITION = "repetition"
CAPABILITY_SYSTEM_STATE = "system_state"


@dataclass(frozen=True)
class CapabilityContext:
    user_input_raw: str
    conversation: list[dict[str, Any]]
    memory: dict[str, Any]
    memory_file: str
    log_file: str
    llama_path: str
    model_path: str
    aura_version: str
    behavior_plan: Any
    route_action: str
    memory_intent: str | None = None
    operations_query: Any = None
    tools_query: Any = None
    internal_command: Any = None
    maintenance_command: Any = None
    system_state_command: Any = None


@dataclass(frozen=True)
class CapabilityExecution:
    response: str | None
    should_exit: bool = False
    used_model: bool | None = None
    used_memory_override: bool | None = None
    task_type: str | None = None
    routing_decision: str | None = None
    selected_provider: str | None = None
    selected_role: str | None = None
    provider_available: bool | None = None
    provider_attempts: tuple[str, ...] | None = None
    fallback_used: bool | None = None
    fallback_reason: str | None = None
    composition_mode: str | None = None
    critic_requested: bool | None = None
    critic_used: bool | None = None
    critic_provider: str | None = None
    critic_available: bool | None = None
    critic_result_status: str | None = None
    critic_summary: str | None = None
    verification_outcome: str | None = None
    verification_mode: str | None = None
    no_model_reason: str | None = None
    provider_trace: tuple[str, ...] | None = None
    gateway_mode: str | None = None
    provider_result_status: str | None = None
    runtime_quality_status: str | None = None
    degradation_hint: str | None = None
    critic_value: str | None = None
    router_value: str | None = None
    fallback_pressure: str | None = None
    routing_neuron_applied: bool | None = None
    routing_neuron_id: str | None = None
    routing_neuron_state: str | None = None
    routing_neuron_type: str | None = None
    routing_neuron_influence: str | None = None
    routing_neuron_trace: tuple[str, ...] | None = None
    routing_neuron_conflict: str | None = None
    routing_neuron_fallback_reason: str | None = None
    routing_neuron_decision: str | None = None
    routing_neuron_alerts: tuple[str, ...] | None = None
    routing_neuron_considered: bool | None = None
    routing_neuron_considered_ids: tuple[str, ...] | None = None
    routing_neuron_selected: bool | None = None
    routing_neuron_barriers_checked: tuple[str, ...] | None = None
    routing_neuron_barriers_blocked: tuple[str, ...] | None = None
    routing_neuron_conflict_resolution: str | None = None
    routing_neuron_outcome_label: str | None = None
    routing_neuron_decision_path: str | None = None


@dataclass(frozen=True)
class CapabilityDefinition:
    name: str
    description: str
    category: str
    examples: tuple[str, ...]
    handler: Callable[[CapabilityContext], CapabilityExecution]


def _handle_exit(context: CapabilityContext) -> CapabilityExecution:
    del context
    return CapabilityExecution(
        response=None,
        should_exit=True,
    )


def _handle_capabilities_catalog(context: CapabilityContext) -> CapabilityExecution:
    from .capabilities_agent import build_capabilities_response

    return CapabilityExecution(
        response=build_capabilities_response(),
        used_memory_override=False,
    )


def _handle_internal_operations_catalog(context: CapabilityContext) -> CapabilityExecution:
    from .operations_agent import build_internal_operations_response

    return CapabilityExecution(
        response=build_internal_operations_response(context.operations_query),
        used_memory_override=False,
    )


def _handle_internal_tools_catalog(context: CapabilityContext) -> CapabilityExecution:
    from .internal_tools_agent import build_internal_tools_response

    return CapabilityExecution(
        response=build_internal_tools_response(context.tools_query, context=context),
        used_memory_override=False,
    )


def _handle_internal_tools_active(context: CapabilityContext) -> CapabilityExecution:
    from .internal_tools_agent import build_internal_tools_response

    return CapabilityExecution(
        response=build_internal_tools_response(context.tools_query, context=context),
        used_memory_override=True,
    )


def _handle_memory_lookup(context: CapabilityContext) -> CapabilityExecution:
    return CapabilityExecution(
        response=build_memory_response(context.memory, context.memory_intent),
        used_memory_override=True,
    )


def _handle_memory_lookup_ambiguous(context: CapabilityContext) -> CapabilityExecution:
    return CapabilityExecution(
        response=build_ambiguous_memory_response(
            context.memory,
            context.memory_intent,
        ),
        used_memory_override=True,
    )


def _handle_memory_update(context: CapabilityContext) -> CapabilityExecution:
    return CapabilityExecution(
        response=build_memory_update_response(context.user_input_raw, context.memory),
        used_memory_override=True,
    )


def _handle_repetition(context: CapabilityContext) -> CapabilityExecution:
    return CapabilityExecution(
        response=build_repetition_response(context.user_input_raw, context.memory),
        used_memory_override=True,
    )


def _handle_internal_command(context: CapabilityContext) -> CapabilityExecution:
    return CapabilityExecution(
        response=execute_internal_command(
            context.internal_command,
            memory=context.memory,
            memory_file=context.memory_file,
        ),
        used_memory_override=True,
    )


def _handle_system_state(context: CapabilityContext) -> CapabilityExecution:
    system_state_command = context.system_state_command
    return CapabilityExecution(
        response=execute_system_state_command(
            system_state_command,
            memory=context.memory,
            aura_version=context.aura_version,
            model_path=context.model_path,
            llama_path=context.llama_path,
            conversation=context.conversation,
            log_file=context.log_file,
        ),
        used_memory_override=system_state_command.target in {
            SYSTEM_TARGET_STATE,
            SYSTEM_TARGET_LOADED_MEMORY,
        },
    )


def _handle_maintenance(context: CapabilityContext) -> CapabilityExecution:
    maintenance_command = context.maintenance_command
    return CapabilityExecution(
        response=execute_maintenance_command(
            maintenance_command,
            conversation=context.conversation,
            memory=context.memory,
            memory_file=context.memory_file,
            log_file=context.log_file,
            aura_version=context.aura_version,
            model_path=context.model_path,
            llama_path=context.llama_path,
        ),
        used_memory_override=maintenance_command.target in {
            MAINTENANCE_TARGET_VALIDATE_CONFIG,
            MAINTENANCE_TARGET_REVIEW_MEMORY,
            MAINTENANCE_TARGET_RELOAD_MEMORY,
            MAINTENANCE_TARGET_CLEAN_MEMORY,
            MAINTENANCE_TARGET_CORRECT_PREFERENCES,
        },
    )


def _handle_heuristic_response(context: CapabilityContext) -> CapabilityExecution:
    return CapabilityExecution(
        response=context.behavior_plan.direct_response,
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


def _handle_model_response(context: CapabilityContext) -> CapabilityExecution:
    execution = execute_model_response(
        conversation=context.conversation,
        memory=context.memory,
        llama_path=context.llama_path,
        model_path=context.model_path,
        behavior_plan=context.behavior_plan,
        route_action=context.route_action,
        session_id=context.log_file,
    )
    return CapabilityExecution(
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


CAPABILITIES_REGISTRY = {
    CAPABILITY_EXIT: CapabilityDefinition(
        name=CAPABILITY_EXIT,
        description="Finaliza el turno y permite cerrar la sesión.",
        category="session",
        examples=("/exit",),
        handler=_handle_exit,
    ),
    CAPABILITY_CAPABILITIES_CATALOG: CapabilityDefinition(
        name=CAPABILITY_CAPABILITIES_CATALOG,
        description="Expone el catálogo real de capacidades disponibles y ejemplos de uso.",
        category="help",
        examples=(
            "que capacidades tienes",
            "muestrame tus capacidades",
            "muestrame que puedes hacer",
        ),
        handler=_handle_capabilities_catalog,
    ),
    CAPABILITY_INTERNAL_OPERATIONS_CATALOG: CapabilityDefinition(
        name=CAPABILITY_INTERNAL_OPERATIONS_CATALOG,
        description="Expone el catálogo formal de operaciones internas disponibles.",
        category="help",
        examples=(
            "que operaciones internas tienes",
            "que acciones internas puedes ejecutar",
            "muestra tus operaciones",
            "como puedo operarte",
        ),
        handler=_handle_internal_operations_catalog,
    ),
    CAPABILITY_INTERNAL_TOOLS_CATALOG: CapabilityDefinition(
        name=CAPABILITY_INTERNAL_TOOLS_CATALOG,
        description="Expone el catálogo real de tools internas del núcleo.",
        category="help",
        examples=(
            "que tools internas tienes",
            "que herramientas internas tienes",
            "que herramientas internas reales tienes",
            "muestra tus tools internas",
        ),
        handler=_handle_internal_tools_catalog,
    ),
    CAPABILITY_INTERNAL_TOOLS_ACTIVE: CapabilityDefinition(
        name=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        description="Ejecuta tools internas activas, compuestas y secuencias con foco estratégico y evaluación útil del núcleo.",
        category="system",
        examples=(
            "haz un chequeo general",
            "haz una revision operativa",
            "que conviene hacer ahora",
            "esto es posible",
            "que tan seguro estas",
            "que puedes hacer ahora segun tu estado",
        ),
        handler=_handle_internal_tools_active,
    ),
    CAPABILITY_MEMORY_LOOKUP: CapabilityDefinition(
        name=CAPABILITY_MEMORY_LOOKUP,
        description="Responde consultas directas de memoria exacta.",
        category="memory",
        examples=("que me gusta?", "en que trabajo?", "como me llamo?"),
        handler=_handle_memory_lookup,
    ),
    CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS: CapabilityDefinition(
        name=CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS,
        description="Responde consultas ambiguas de memoria con cautela.",
        category="memory",
        examples=("que me gusta hacer?",),
        handler=_handle_memory_lookup_ambiguous,
    ),
    CAPABILITY_MEMORY_UPDATE: CapabilityDefinition(
        name=CAPABILITY_MEMORY_UPDATE,
        description="Confirma actualizaciones de memoria guardadas desde código.",
        category="memory",
        examples=("me gusta la mecanica y correr", "prefiero respuestas claras"),
        handler=_handle_memory_update,
    ),
    CAPABILITY_REPETITION: CapabilityDefinition(
        name=CAPABILITY_REPETITION,
        description="Responde a datos repetidos ya guardados en memoria.",
        category="memory",
        examples=("me gusta la mecanica",),
        handler=_handle_repetition,
    ),
    CAPABILITY_INTERNAL_COMMAND: CapabilityDefinition(
        name=CAPABILITY_INTERNAL_COMMAND,
        description="Ejecuta consultas y olvidos internos de memoria.",
        category="memory",
        examples=("que sabes de mi", "olvida mis gustos"),
        handler=_handle_internal_command,
    ),
    CAPABILITY_SYSTEM_STATE: CapabilityDefinition(
        name=CAPABILITY_SYSTEM_STATE,
        description="Responde autodiagnóstico y estado interno desde código.",
        category="system",
        examples=("que estado tienes", "que version eres"),
        handler=_handle_system_state,
    ),
    CAPABILITY_MAINTENANCE: CapabilityDefinition(
        name=CAPABILITY_MAINTENANCE,
        description="Ejecuta mantenimiento operativo interno desde código.",
        category="maintenance",
        examples=("valida tu configuracion", "muestrame el ultimo log"),
        handler=_handle_maintenance,
    ),
    CAPABILITY_HEURISTIC_RESPONSE: CapabilityDefinition(
        name=CAPABILITY_HEURISTIC_RESPONSE,
        description="Resuelve respuestas heurísticas internas sin usar el modelo cuando el criterio ya está disponible desde código.",
        category="assistant",
        examples=(),
        handler=_handle_heuristic_response,
    ),
    CAPABILITY_MODEL_RESPONSE: CapabilityDefinition(
        name=CAPABILITY_MODEL_RESPONSE,
        description="Genera respuestas asistidas por el modelo local.",
        category="assistant",
        examples=("como funciona una api", "explicame que es un prompt"),
        handler=_handle_model_response,
    ),
}


def get_capability_definition(capability: str) -> CapabilityDefinition:
    capability_definition = CAPABILITIES_REGISTRY.get(capability)
    if capability_definition is None:
        raise KeyError(f"Capacidad desconocida: {capability}")

    return capability_definition
