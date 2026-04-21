from dataclasses import dataclass
from typing import Callable

from .behavior_agent import build_memory_update_response, build_repetition_response
from .capabilities_agent import build_capabilities_response
from .capabilities_registry import (
    CAPABILITY_CAPABILITIES_CATALOG,
    CAPABILITY_EXIT,
    CAPABILITY_HEURISTIC_RESPONSE,
    CAPABILITY_INTERNAL_COMMAND,
    CAPABILITY_INTERNAL_OPERATIONS_CATALOG,
    CAPABILITY_INTERNAL_TOOLS_ACTIVE,
    CAPABILITY_INTERNAL_TOOLS_CATALOG,
    CAPABILITY_MAINTENANCE,
    CAPABILITY_MEMORY_LOOKUP,
    CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS,
    CAPABILITY_MEMORY_UPDATE,
    CAPABILITY_MODEL_RESPONSE,
    CAPABILITY_REPETITION,
    CAPABILITY_SYSTEM_STATE,
    CapabilityContext,
    CapabilityExecution,
)
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
from .internal_tools_registry import (
    TOOL_COMPOSITE_DIAGNOSTICS,
    TOOL_COMPOSITE_REVIEWS,
    TOOL_HELP_CATALOGS,
    TOOL_LOCAL_MODEL_RUNTIME,
    TOOL_MAINTENANCE_CONSOLE,
    TOOL_RESPONSE_HEURISTICS,
    TOOL_SESSION_CONTROL,
    TOOL_SYSTEM_STATE_READER,
    TOOL_USER_MEMORY,
)
from .internal_sequences_registry import (
    SEQUENCE_COMPLETE_REVIEW,
    SEQUENCE_FULL_DIAGNOSTIC,
    SEQUENCE_DOMINANT_LIMITATION,
    SEQUENCE_DOMINANT_STRENGTH,
    SEQUENCE_GENERAL_CHECK,
    SEQUENCE_GENERAL_DIAGNOSTIC,
    SEQUENCE_CONTEXTUAL_HELP,
    SEQUENCE_CONSISTENCY_EVALUATION,
    SEQUENCE_FEASIBILITY_EVALUATION,
    SEQUENCE_INTERNAL_DIAGNOSTIC,
    SEQUENCE_INTERNAL_REVIEW,
    SEQUENCE_LIMITATIONS_OVERVIEW,
    SEQUENCE_MEMORY_STATE_REVIEW,
    SEQUENCE_OPERATIONAL_REVIEW,
    SEQUENCE_PRACTICAL_REVIEW,
    SEQUENCE_PRIORITY_NOW,
    SEQUENCE_QUICK_CHECK,
    SEQUENCE_READINESS_GAP,
    SEQUENCE_STRATEGIC_GUIDANCE,
    SEQUENCE_SITUATIONAL_STATUS,
    SEQUENCE_SYSTEM_CHECK,
    SEQUENCE_WORK_READINESS,
)


ACTION_EXIT = "exit"
ACTION_CAPABILITIES_CATALOG = "capabilities_catalog"
ACTION_INTERNAL_OPERATIONS_CATALOG = "internal_operations_catalog"
ACTION_INTERNAL_TOOLS_CATALOG = "internal_tools_catalog"
ACTION_INTERNAL_TOOLS_DIAGNOSTIC = "internal_tools_diagnostic"
ACTION_INTERNAL_TOOLS_GENERAL_DIAGNOSTIC = "internal_tools_general_diagnostic"
ACTION_INTERNAL_TOOLS_FULL_DIAGNOSTIC = "internal_tools_full_diagnostic"
ACTION_INTERNAL_TOOLS_SITUATIONAL_STATUS = "internal_tools_situational_status"
ACTION_INTERNAL_TOOLS_QUICK_CHECK = "internal_tools_quick_check"
ACTION_INTERNAL_TOOLS_GENERAL_CHECK = "internal_tools_general_check"
ACTION_INTERNAL_TOOLS_SYSTEM_CHECK = "internal_tools_system_check"
ACTION_INTERNAL_TOOLS_PRIORITY_NOW = "internal_tools_priority_now"
ACTION_INTERNAL_TOOLS_DOMINANT_LIMITATION = "internal_tools_dominant_limitation"
ACTION_INTERNAL_TOOLS_DOMINANT_STRENGTH = "internal_tools_dominant_strength"
ACTION_INTERNAL_TOOLS_WORK_READINESS = "internal_tools_work_readiness"
ACTION_INTERNAL_TOOLS_READINESS_GAP = "internal_tools_readiness_gap"
ACTION_INTERNAL_TOOLS_LIMITATIONS_OVERVIEW = "internal_tools_limitations_overview"
ACTION_INTERNAL_TOOLS_CONTEXTUAL_HELP = "internal_tools_contextual_help"
ACTION_INTERNAL_TOOLS_STRATEGIC_GUIDANCE = "internal_tools_strategic_guidance"
ACTION_INTERNAL_TOOLS_FEASIBILITY = "internal_tools_feasibility"
ACTION_INTERNAL_TOOLS_CONSISTENCY = "internal_tools_consistency"
ACTION_INTERNAL_TOOLS_MEMORY_AND_STATE_REVIEW = "internal_tools_memory_and_state_review"
ACTION_INTERNAL_TOOLS_PRACTICAL_REVIEW = "internal_tools_practical_review"
ACTION_INTERNAL_TOOLS_OPERATIONAL_REVIEW = "internal_tools_operational_review"
ACTION_INTERNAL_TOOLS_INTERNAL_REVIEW = "internal_tools_internal_review"
ACTION_INTERNAL_TOOLS_COMPLETE_REVIEW = "internal_tools_complete_review"
ACTION_MEMORY_LOOKUP_NAME = "memory_lookup_name"
ACTION_MEMORY_LOOKUP_WORK = "memory_lookup_work"
ACTION_MEMORY_LOOKUP_LIKES = "memory_lookup_likes"
ACTION_MEMORY_LOOKUP_AMBIGUOUS_NAME = "memory_lookup_ambiguous_name"
ACTION_MEMORY_LOOKUP_AMBIGUOUS_WORK = "memory_lookup_ambiguous_work"
ACTION_MEMORY_LOOKUP_AMBIGUOUS_LIKES = "memory_lookup_ambiguous_likes"
ACTION_MEMORY_UPDATE = "memory_update"
ACTION_REPETITION = "repetition"
ACTION_INTERNAL_QUERY_ALL = "internal_query_all"
ACTION_INTERNAL_QUERY_WORK = "internal_query_work"
ACTION_INTERNAL_QUERY_INTERESTS = "internal_query_interests"
ACTION_INTERNAL_QUERY_PREFERENCES = "internal_query_preferences"
ACTION_INTERNAL_FORGET_NAME = "internal_forget_name"
ACTION_INTERNAL_FORGET_WORK = "internal_forget_work"
ACTION_INTERNAL_FORGET_INTERESTS = "internal_forget_interests"
ACTION_INTERNAL_FORGET_PREFERENCES = "internal_forget_preferences"
ACTION_SYSTEM_STATE = "system_state"
ACTION_SYSTEM_MODEL_NAME = "system_model_name"
ACTION_SYSTEM_MODEL_PATH = "system_model_path"
ACTION_SYSTEM_LLAMA_PATH = "system_llama_path"
ACTION_SYSTEM_MODEL_AVAILABLE = "system_model_available"
ACTION_SYSTEM_VERSION = "system_version"
ACTION_SYSTEM_LOADED_MEMORY = "system_loaded_memory"
ACTION_MAINTENANCE_VALIDATE_CONFIG = "maintenance_validate_config"
ACTION_MAINTENANCE_REVIEW_MEMORY = "maintenance_review_memory"
ACTION_MAINTENANCE_RELOAD_MEMORY = "maintenance_reload_memory"
ACTION_MAINTENANCE_CLEAN_MEMORY = "maintenance_clean_memory"
ACTION_MAINTENANCE_SHOW_LAST_LOG = "maintenance_show_last_log"
ACTION_MAINTENANCE_SUMMARIZE_LAST_LOG = "maintenance_summarize_last_log"
ACTION_MAINTENANCE_SUMMARIZE_LAST_TURN = "maintenance_summarize_last_turn"
ACTION_MAINTENANCE_CORRECT_PREFERENCES = "maintenance_correct_preferences"
ACTION_HEURISTIC_RESPONSE = "heuristic_response"
ACTION_MODEL_RESPONSE = "model_response"

FRIENDLY_VERB_PREFIXES = {
    "aplica": "aplicar",
    "cierra": "cerrar",
    "confirma": "confirmar",
    "consulta": "consultar",
    "corrige": "corregir",
    "devuelve": "mostrar",
    "expone": "mostrar",
    "genera": "generar",
    "indica": "mostrar",
    "recarga": "recargar",
    "resuelve": "resolver",
    "revisa": "revisar",
    "valida": "validar",
}

SPECIAL_CATALOG_LABELS = {
    "aplica limpieza segura de memoria": "limpiar memoria de forma segura",
    "genera una respuesta usando el modelo local": "responder con el modelo local",
}

DEFAULT_TOOLS_BY_CATEGORY = {
    "help": TOOL_HELP_CATALOGS,
    "memory": TOOL_USER_MEMORY,
    "system": TOOL_SYSTEM_STATE_READER,
    "maintenance": TOOL_MAINTENANCE_CONSOLE,
    "assistant": TOOL_LOCAL_MODEL_RUNTIME,
    "session": TOOL_SESSION_CONTROL,
}


@dataclass(frozen=True)
class InternalActionDefinition:
    name: str
    capability: str
    category: str
    description: str
    examples: tuple[str, ...]
    catalog_label: str
    tool_name: str | None
    sequence_name: str | None
    handler: Callable[[CapabilityContext], CapabilityExecution]


def _build_catalog_label(description: str) -> str:
    cleaned = description.strip().rstrip(".")
    if not cleaned:
        return ""

    special_label = SPECIAL_CATALOG_LABELS.get(cleaned.casefold())
    if special_label:
        return special_label

    words = cleaned.split()
    if not words:
        return ""

    friendly_prefix = FRIENDLY_VERB_PREFIXES.get(words[0].casefold())
    if friendly_prefix:
        return " ".join([friendly_prefix, *words[1:]])

    return cleaned[0].lower() + cleaned[1:]


def _register_action(
    name: str,
    capability: str,
    category: str,
    description: str,
    examples: tuple[str, ...],
    handler: Callable[[CapabilityContext], CapabilityExecution],
    tool_name: str | None = None,
    sequence_name: str | None = None,
) -> InternalActionDefinition:
    return InternalActionDefinition(
        name=name,
        capability=capability,
        category=category,
        description=description,
        examples=examples,
        catalog_label=_build_catalog_label(description),
        tool_name=tool_name or DEFAULT_TOOLS_BY_CATEGORY.get(category),
        sequence_name=sequence_name,
        handler=handler,
    )


def _handle_exit(context: CapabilityContext) -> CapabilityExecution:
    del context
    return CapabilityExecution(response=None, should_exit=True)


def _handle_capabilities_catalog(context: CapabilityContext) -> CapabilityExecution:
    del context
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
    return CapabilityExecution(
        response=execute_system_state_command(
            context.system_state_command,
            memory=context.memory,
            aura_version=context.aura_version,
            model_path=context.model_path,
            llama_path=context.llama_path,
            conversation=context.conversation,
            log_file=context.log_file,
        ),
        used_memory_override=context.system_state_command.target in {
            SYSTEM_TARGET_STATE,
            SYSTEM_TARGET_LOADED_MEMORY,
        },
    )


def _handle_maintenance(context: CapabilityContext) -> CapabilityExecution:
    return CapabilityExecution(
        response=execute_maintenance_command(
            context.maintenance_command,
            conversation=context.conversation,
            memory=context.memory,
            memory_file=context.memory_file,
            log_file=context.log_file,
            aura_version=context.aura_version,
            model_path=context.model_path,
            llama_path=context.llama_path,
        ),
        used_memory_override=context.maintenance_command.target in {
            MAINTENANCE_TARGET_VALIDATE_CONFIG,
            MAINTENANCE_TARGET_REVIEW_MEMORY,
            MAINTENANCE_TARGET_RELOAD_MEMORY,
            MAINTENANCE_TARGET_CLEAN_MEMORY,
            MAINTENANCE_TARGET_CORRECT_PREFERENCES,
        },
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


INTERNAL_ACTIONS_REGISTRY = {
    ACTION_EXIT: _register_action(
        name=ACTION_EXIT,
        capability=CAPABILITY_EXIT,
        category="session",
        description="Cierra la sesión actual.",
        examples=("/exit",),
        handler=_handle_exit,
    ),
    ACTION_CAPABILITIES_CATALOG: _register_action(
        name=ACTION_CAPABILITIES_CATALOG,
        capability=CAPABILITY_CAPABILITIES_CATALOG,
        category="help",
        description="Expone el catálogo real de capacidades.",
        examples=("que capacidades tienes",),
        handler=_handle_capabilities_catalog,
    ),
    ACTION_INTERNAL_OPERATIONS_CATALOG: _register_action(
        name=ACTION_INTERNAL_OPERATIONS_CATALOG,
        capability=CAPABILITY_INTERNAL_OPERATIONS_CATALOG,
        category="help",
        description="Expone el catálogo formal de operaciones internas.",
        examples=("que operaciones internas tienes",),
        handler=_handle_internal_operations_catalog,
    ),
    ACTION_INTERNAL_TOOLS_CATALOG: _register_action(
        name=ACTION_INTERNAL_TOOLS_CATALOG,
        capability=CAPABILITY_INTERNAL_TOOLS_CATALOG,
        category="help",
        description="Expone el catálogo real de tools internas y su ayuda visible.",
        examples=(
            "que tools internas tienes",
            "que herramientas internas reales tienes",
        ),
        handler=_handle_internal_tools_catalog,
    ),
    ACTION_INTERNAL_TOOLS_DIAGNOSTIC: _register_action(
        name=ACTION_INTERNAL_TOOLS_DIAGNOSTIC,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Construye un diagnóstico corto del núcleo.",
        examples=("haz un diagnostico interno",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_INTERNAL_DIAGNOSTIC,
    ),
    ACTION_INTERNAL_TOOLS_GENERAL_DIAGNOSTIC: _register_action(
        name=ACTION_INTERNAL_TOOLS_GENERAL_DIAGNOSTIC,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Construye un diagnóstico general orientado a prioridad.",
        examples=("haz un diagnostico general",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_GENERAL_DIAGNOSTIC,
    ),
    ACTION_INTERNAL_TOOLS_FULL_DIAGNOSTIC: _register_action(
        name=ACTION_INTERNAL_TOOLS_FULL_DIAGNOSTIC,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Construye un diagnóstico operativo completo del núcleo.",
        examples=("haz un diagnostico completo",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_FULL_DIAGNOSTIC,
    ),
    ACTION_INTERNAL_TOOLS_SITUATIONAL_STATUS: _register_action(
        name=ACTION_INTERNAL_TOOLS_SITUATIONAL_STATUS,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Resume de forma compacta el estado situacional actual de AURA.",
        examples=("resume tu estado actual",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_SITUATIONAL_STATUS,
    ),
    ACTION_INTERNAL_TOOLS_QUICK_CHECK: _register_action(
        name=ACTION_INTERNAL_TOOLS_QUICK_CHECK,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Hace un chequeo rápido con foco en el principal bloqueo o punto fuerte.",
        examples=("haz un chequeo rapido",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_QUICK_CHECK,
    ),
    ACTION_INTERNAL_TOOLS_GENERAL_CHECK: _register_action(
        name=ACTION_INTERNAL_TOOLS_GENERAL_CHECK,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Hace un chequeo general orientado a estado, limitaciones y siguiente paso.",
        examples=("haz un chequeo general",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_GENERAL_CHECK,
    ),
    ACTION_INTERNAL_TOOLS_SYSTEM_CHECK: _register_action(
        name=ACTION_INTERNAL_TOOLS_SYSTEM_CHECK,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Hace un chequeo compacto del sistema interno.",
        examples=("haz un chequeo del sistema",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_SYSTEM_CHECK,
    ),
    ACTION_INTERNAL_TOOLS_PRIORITY_NOW: _register_action(
        name=ACTION_INTERNAL_TOOLS_PRIORITY_NOW,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Resalta lo más importante del núcleo según el contexto actual.",
        examples=("que es lo mas importante ahora",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_PRIORITY_NOW,
    ),
    ACTION_INTERNAL_TOOLS_DOMINANT_LIMITATION: _register_action(
        name=ACTION_INTERNAL_TOOLS_DOMINANT_LIMITATION,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Resalta la limitación principal del núcleo y el siguiente foco útil.",
        examples=("cual es tu principal limitacion",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_DOMINANT_LIMITATION,
    ),
    ACTION_INTERNAL_TOOLS_DOMINANT_STRENGTH: _register_action(
        name=ACTION_INTERNAL_TOOLS_DOMINANT_STRENGTH,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Resalta la fortaleza principal del núcleo ahora mismo.",
        examples=("cual es tu principal fortaleza",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_DOMINANT_STRENGTH,
    ),
    ACTION_INTERNAL_TOOLS_WORK_READINESS: _register_action(
        name=ACTION_INTERNAL_TOOLS_WORK_READINESS,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Indica si AURA está lista, parcialmente lista o limitada para trabajar.",
        examples=("como estas para trabajar",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_WORK_READINESS,
    ),
    ACTION_INTERNAL_TOOLS_READINESS_GAP: _register_action(
        name=ACTION_INTERNAL_TOOLS_READINESS_GAP,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Indica qué falta o qué limita a AURA para trabajar ahora.",
        examples=("que te falta para trabajar",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_READINESS_GAP,
    ),
    ACTION_INTERNAL_TOOLS_LIMITATIONS_OVERVIEW: _register_action(
        name=ACTION_INTERNAL_TOOLS_LIMITATIONS_OVERVIEW,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="system",
        description="Explica las limitaciones actuales y su impacto principal.",
        examples=("que limitaciones tienes ahora",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_LIMITATIONS_OVERVIEW,
    ),
    ACTION_INTERNAL_TOOLS_CONTEXTUAL_HELP: _register_action(
        name=ACTION_INTERNAL_TOOLS_CONTEXTUAL_HELP,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="help",
        description="Traduce el estado actual de AURA en ayuda realmente disponible.",
        examples=(
            "que puedes hacer ahora segun tu estado",
            "como me puedes ayudar ahora mismo",
        ),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_DIAGNOSTICS,
        sequence_name=SEQUENCE_CONTEXTUAL_HELP,
    ),
    ACTION_INTERNAL_TOOLS_STRATEGIC_GUIDANCE: _register_action(
        name=ACTION_INTERNAL_TOOLS_STRATEGIC_GUIDANCE,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="help",
        description="Orienta el siguiente movimiento útil con recomendación situacional desde código.",
        examples=(
            "que conviene hacer ahora",
            "armame un plan corto",
            "que me recomiendas hacer ahora",
            "si quiero avanzar ahora por donde empiezo",
        ),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_REVIEWS,
        sequence_name=SEQUENCE_STRATEGIC_GUIDANCE,
    ),
    ACTION_INTERNAL_TOOLS_FEASIBILITY: _register_action(
        name=ACTION_INTERNAL_TOOLS_FEASIBILITY,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="help",
        description="Evalúa viabilidad, límites y contradicciones útiles desde código.",
        examples=(
            "esto es posible",
            "ves alguna contradiccion",
            "te parece realista",
            "esto tiene algun limite importante",
        ),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_REVIEWS,
        sequence_name=SEQUENCE_FEASIBILITY_EVALUATION,
    ),
    ACTION_INTERNAL_TOOLS_CONSISTENCY: _register_action(
        name=ACTION_INTERNAL_TOOLS_CONSISTENCY,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="help",
        description="Calibra certeza, evidencia, dependencia y tensión contextual del juicio actual.",
        examples=(
            "que tan seguro estas",
            "esto depende de algo",
            "hay suficiente base",
            "ves tension con lo anterior",
        ),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_REVIEWS,
        sequence_name=SEQUENCE_CONSISTENCY_EVALUATION,
    ),
    ACTION_INTERNAL_TOOLS_MEMORY_AND_STATE_REVIEW: _register_action(
        name=ACTION_INTERNAL_TOOLS_MEMORY_AND_STATE_REVIEW,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="maintenance",
        description="Revisa memoria cargada y estado actual del núcleo.",
        examples=("revisa tu memoria y estado",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_REVIEWS,
        sequence_name=SEQUENCE_MEMORY_STATE_REVIEW,
    ),
    ACTION_INTERNAL_TOOLS_PRACTICAL_REVIEW: _register_action(
        name=ACTION_INTERNAL_TOOLS_PRACTICAL_REVIEW,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="maintenance",
        description="Hace una revisión práctica orientada a lo que AURA puede hacer ahora y al siguiente foco útil.",
        examples=("haz una revision practica",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_REVIEWS,
        sequence_name=SEQUENCE_PRACTICAL_REVIEW,
    ),
    ACTION_INTERNAL_TOOLS_OPERATIONAL_REVIEW: _register_action(
        name=ACTION_INTERNAL_TOOLS_OPERATIONAL_REVIEW,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="maintenance",
        description="Hace una revisión operativa con prioridad sobre estado, memoria y mantenimiento.",
        examples=("haz una revision operativa",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_REVIEWS,
        sequence_name=SEQUENCE_OPERATIONAL_REVIEW,
    ),
    ACTION_INTERNAL_TOOLS_INTERNAL_REVIEW: _register_action(
        name=ACTION_INTERNAL_TOOLS_INTERNAL_REVIEW,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="maintenance",
        description="Hace una revisión interna compacta con memoria, estado y actividad reciente.",
        examples=("haz una revision general",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_REVIEWS,
        sequence_name=SEQUENCE_INTERNAL_REVIEW,
    ),
    ACTION_INTERNAL_TOOLS_COMPLETE_REVIEW: _register_action(
        name=ACTION_INTERNAL_TOOLS_COMPLETE_REVIEW,
        capability=CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        category="maintenance",
        description="Hace una revisión completa del núcleo con resumen priorizado.",
        examples=("haz una revision completa",),
        handler=_handle_internal_tools_active,
        tool_name=TOOL_COMPOSITE_REVIEWS,
        sequence_name=SEQUENCE_COMPLETE_REVIEW,
    ),
    ACTION_MEMORY_LOOKUP_NAME: _register_action(
        name=ACTION_MEMORY_LOOKUP_NAME,
        capability=CAPABILITY_MEMORY_LOOKUP,
        category="memory",
        description="Consulta el nombre recordado del usuario.",
        examples=("como me llamo?",),
        handler=_handle_memory_lookup,
    ),
    ACTION_MEMORY_LOOKUP_WORK: _register_action(
        name=ACTION_MEMORY_LOOKUP_WORK,
        capability=CAPABILITY_MEMORY_LOOKUP,
        category="memory",
        description="Consulta el trabajo recordado del usuario.",
        examples=("en que trabajo?",),
        handler=_handle_memory_lookup,
    ),
    ACTION_MEMORY_LOOKUP_LIKES: _register_action(
        name=ACTION_MEMORY_LOOKUP_LIKES,
        capability=CAPABILITY_MEMORY_LOOKUP,
        category="memory",
        description="Consulta gustos recordados del usuario.",
        examples=("que me gusta?",),
        handler=_handle_memory_lookup,
    ),
    ACTION_MEMORY_LOOKUP_AMBIGUOUS_NAME: _register_action(
        name=ACTION_MEMORY_LOOKUP_AMBIGUOUS_NAME,
        capability=CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS,
        category="memory",
        description="Resuelve una consulta ambigua sobre el nombre del usuario.",
        examples=("te acuerdas de mi nombre?",),
        handler=_handle_memory_lookup_ambiguous,
    ),
    ACTION_MEMORY_LOOKUP_AMBIGUOUS_WORK: _register_action(
        name=ACTION_MEMORY_LOOKUP_AMBIGUOUS_WORK,
        capability=CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS,
        category="memory",
        description="Resuelve una consulta ambigua sobre el trabajo del usuario.",
        examples=("te acuerdas donde trabajo?",),
        handler=_handle_memory_lookup_ambiguous,
    ),
    ACTION_MEMORY_LOOKUP_AMBIGUOUS_LIKES: _register_action(
        name=ACTION_MEMORY_LOOKUP_AMBIGUOUS_LIKES,
        capability=CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS,
        category="memory",
        description="Resuelve una consulta ambigua sobre gustos del usuario.",
        examples=("que me gusta hacer?",),
        handler=_handle_memory_lookup_ambiguous,
    ),
    ACTION_MEMORY_UPDATE: _register_action(
        name=ACTION_MEMORY_UPDATE,
        capability=CAPABILITY_MEMORY_UPDATE,
        category="memory",
        description="Confirma actualización de memoria.",
        examples=("me gusta la mecanica",),
        handler=_handle_memory_update,
    ),
    ACTION_REPETITION: _register_action(
        name=ACTION_REPETITION,
        capability=CAPABILITY_REPETITION,
        category="memory",
        description="Confirma que un dato ya estaba guardado.",
        examples=("me gusta la mecanica",),
        handler=_handle_repetition,
    ),
    ACTION_INTERNAL_QUERY_ALL: _register_action(
        name=ACTION_INTERNAL_QUERY_ALL,
        capability=CAPABILITY_INTERNAL_COMMAND,
        category="memory",
        description="Muestra la memoria general del usuario.",
        examples=("que sabes de mi",),
        handler=_handle_internal_command,
    ),
    ACTION_INTERNAL_QUERY_WORK: _register_action(
        name=ACTION_INTERNAL_QUERY_WORK,
        capability=CAPABILITY_INTERNAL_COMMAND,
        category="memory",
        description="Muestra el trabajo guardado del usuario.",
        examples=("muestrame mi trabajo guardado",),
        handler=_handle_internal_command,
    ),
    ACTION_INTERNAL_QUERY_INTERESTS: _register_action(
        name=ACTION_INTERNAL_QUERY_INTERESTS,
        capability=CAPABILITY_INTERNAL_COMMAND,
        category="memory",
        description="Muestra los gustos guardados del usuario.",
        examples=("muestrame mis gustos",),
        handler=_handle_internal_command,
    ),
    ACTION_INTERNAL_QUERY_PREFERENCES: _register_action(
        name=ACTION_INTERNAL_QUERY_PREFERENCES,
        capability=CAPABILITY_INTERNAL_COMMAND,
        category="memory",
        description="Muestra las preferencias guardadas del usuario.",
        examples=("muestrame mis preferencias",),
        handler=_handle_internal_command,
    ),
    ACTION_INTERNAL_FORGET_NAME: _register_action(
        name=ACTION_INTERNAL_FORGET_NAME,
        capability=CAPABILITY_INTERNAL_COMMAND,
        category="memory",
        description="Olvida el nombre guardado del usuario.",
        examples=("olvida mi nombre",),
        handler=_handle_internal_command,
    ),
    ACTION_INTERNAL_FORGET_WORK: _register_action(
        name=ACTION_INTERNAL_FORGET_WORK,
        capability=CAPABILITY_INTERNAL_COMMAND,
        category="memory",
        description="Olvida el trabajo guardado del usuario.",
        examples=("olvida mi trabajo",),
        handler=_handle_internal_command,
    ),
    ACTION_INTERNAL_FORGET_INTERESTS: _register_action(
        name=ACTION_INTERNAL_FORGET_INTERESTS,
        capability=CAPABILITY_INTERNAL_COMMAND,
        category="memory",
        description="Olvida los gustos guardados del usuario.",
        examples=("olvida mis gustos",),
        handler=_handle_internal_command,
    ),
    ACTION_INTERNAL_FORGET_PREFERENCES: _register_action(
        name=ACTION_INTERNAL_FORGET_PREFERENCES,
        capability=CAPABILITY_INTERNAL_COMMAND,
        category="memory",
        description="Olvida las preferencias guardadas del usuario.",
        examples=("olvida mis preferencias",),
        handler=_handle_internal_command,
    ),
    ACTION_SYSTEM_STATE: _register_action(
        name=ACTION_SYSTEM_STATE,
        capability=CAPABILITY_SYSTEM_STATE,
        category="system",
        description="Devuelve el estado general del sistema.",
        examples=("que estado tienes",),
        handler=_handle_system_state,
    ),
    ACTION_SYSTEM_MODEL_NAME: _register_action(
        name=ACTION_SYSTEM_MODEL_NAME,
        capability=CAPABILITY_SYSTEM_STATE,
        category="system",
        description="Devuelve el modelo configurado.",
        examples=("que modelo usas",),
        handler=_handle_system_state,
    ),
    ACTION_SYSTEM_MODEL_PATH: _register_action(
        name=ACTION_SYSTEM_MODEL_PATH,
        capability=CAPABILITY_SYSTEM_STATE,
        category="system",
        description="Devuelve la ruta del modelo.",
        examples=("que ruta de modelo tienes",),
        handler=_handle_system_state,
    ),
    ACTION_SYSTEM_LLAMA_PATH: _register_action(
        name=ACTION_SYSTEM_LLAMA_PATH,
        capability=CAPABILITY_SYSTEM_STATE,
        category="system",
        description="Devuelve la ruta de llama-cli.",
        examples=("que ruta de llama cli tienes",),
        handler=_handle_system_state,
    ),
    ACTION_SYSTEM_MODEL_AVAILABLE: _register_action(
        name=ACTION_SYSTEM_MODEL_AVAILABLE,
        capability=CAPABILITY_SYSTEM_STATE,
        category="system",
        description="Indica si el modelo está disponible.",
        examples=("tienes modelo disponible",),
        handler=_handle_system_state,
    ),
    ACTION_SYSTEM_VERSION: _register_action(
        name=ACTION_SYSTEM_VERSION,
        capability=CAPABILITY_SYSTEM_STATE,
        category="system",
        description="Devuelve la versión de AURA.",
        examples=("que version eres",),
        handler=_handle_system_state,
    ),
    ACTION_SYSTEM_LOADED_MEMORY: _register_action(
        name=ACTION_SYSTEM_LOADED_MEMORY,
        capability=CAPABILITY_SYSTEM_STATE,
        category="system",
        description="Devuelve la memoria cargada.",
        examples=("que memoria tienes cargada",),
        handler=_handle_system_state,
    ),
    ACTION_MAINTENANCE_VALIDATE_CONFIG: _register_action(
        name=ACTION_MAINTENANCE_VALIDATE_CONFIG,
        capability=CAPABILITY_MAINTENANCE,
        category="maintenance",
        description="Valida la configuración actual.",
        examples=("valida tu configuracion",),
        handler=_handle_maintenance,
    ),
    ACTION_MAINTENANCE_REVIEW_MEMORY: _register_action(
        name=ACTION_MAINTENANCE_REVIEW_MEMORY,
        capability=CAPABILITY_MAINTENANCE,
        category="maintenance",
        description="Revisa el estado saneado de memoria.",
        examples=("revisa la memoria",),
        handler=_handle_maintenance,
    ),
    ACTION_MAINTENANCE_RELOAD_MEMORY: _register_action(
        name=ACTION_MAINTENANCE_RELOAD_MEMORY,
        capability=CAPABILITY_MAINTENANCE,
        category="maintenance",
        description="Recarga la memoria desde disco.",
        examples=("recarga la memoria",),
        handler=_handle_maintenance,
    ),
    ACTION_MAINTENANCE_CLEAN_MEMORY: _register_action(
        name=ACTION_MAINTENANCE_CLEAN_MEMORY,
        capability=CAPABILITY_MAINTENANCE,
        category="maintenance",
        description="Aplica limpieza segura de memoria.",
        examples=("limpia la memoria",),
        handler=_handle_maintenance,
    ),
    ACTION_MAINTENANCE_SHOW_LAST_LOG: _register_action(
        name=ACTION_MAINTENANCE_SHOW_LAST_LOG,
        capability=CAPABILITY_MAINTENANCE,
        category="maintenance",
        description="Muestra el último log disponible.",
        examples=("muestrame el ultimo log",),
        handler=_handle_maintenance,
    ),
    ACTION_MAINTENANCE_SUMMARIZE_LAST_LOG: _register_action(
        name=ACTION_MAINTENANCE_SUMMARIZE_LAST_LOG,
        capability=CAPABILITY_MAINTENANCE,
        category="maintenance",
        description="Resume el último log disponible.",
        examples=("resume el ultimo log",),
        handler=_handle_maintenance,
    ),
    ACTION_MAINTENANCE_SUMMARIZE_LAST_TURN: _register_action(
        name=ACTION_MAINTENANCE_SUMMARIZE_LAST_TURN,
        capability=CAPABILITY_MAINTENANCE,
        category="maintenance",
        description="Resume el último turno disponible.",
        examples=("resume el ultimo turno",),
        handler=_handle_maintenance,
    ),
    ACTION_MAINTENANCE_CORRECT_PREFERENCES: _register_action(
        name=ACTION_MAINTENANCE_CORRECT_PREFERENCES,
        capability=CAPABILITY_MAINTENANCE,
        category="maintenance",
        description="Corrige preferencias guardadas con cambios seguros.",
        examples=("corrige preferencias guardadas",),
        handler=_handle_maintenance,
    ),
    ACTION_HEURISTIC_RESPONSE: _register_action(
        name=ACTION_HEURISTIC_RESPONSE,
        capability=CAPABILITY_HEURISTIC_RESPONSE,
        category="assistant",
        description="Devuelve una respuesta heurística directa sin usar provider de modelo.",
        examples=(),
        handler=_handle_model_response,
        tool_name=TOOL_RESPONSE_HEURISTICS,
    ),
    ACTION_MODEL_RESPONSE: _register_action(
        name=ACTION_MODEL_RESPONSE,
        capability=CAPABILITY_MODEL_RESPONSE,
        category="assistant",
        description="Genera una respuesta usando el modelo local.",
        examples=("como funciona una api",),
        handler=_handle_model_response,
    ),
}


def get_internal_action_definition(action: str) -> InternalActionDefinition:
    action_definition = INTERNAL_ACTIONS_REGISTRY.get(action)
    if action_definition is None:
        raise KeyError(f"Acción interna desconocida: {action}")

    return action_definition


def get_internal_actions_for_tool(tool_name: str) -> tuple[InternalActionDefinition, ...]:
    return tuple(
        definition
        for definition in INTERNAL_ACTIONS_REGISTRY.values()
        if definition.tool_name == tool_name
    )


def get_internal_actions_for_category(category: str) -> tuple[InternalActionDefinition, ...]:
    return tuple(
        definition
        for definition in INTERNAL_ACTIONS_REGISTRY.values()
        if definition.category == category
    )


def get_internal_actions_for_capability(capability: str) -> tuple[InternalActionDefinition, ...]:
    return tuple(
        definition
        for definition in INTERNAL_ACTIONS_REGISTRY.values()
        if definition.capability == capability
    )
