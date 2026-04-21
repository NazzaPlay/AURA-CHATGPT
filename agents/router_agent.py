from dataclasses import dataclass

from .capabilities_registry import (
    CAPABILITY_CAPABILITIES_CATALOG,
    CAPABILITY_EXIT,
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
)
from .capabilities_agent import analyze_capabilities_query
from .chat_agent import UserTurn
from .internal_commands_agent import analyze_internal_command
from .internal_tools_agent import analyze_internal_tools_query
from .maintenance_agent import analyze_maintenance_command
from .memory_agent import (
    analyze_memory_question,
    is_memory_update,
    is_memory_update_already_stored,
)
from .system_state_agent import analyze_system_state_command
from .text_matching import normalize_internal_text
from .operations_agent import analyze_internal_operations_query


ROUTE_EXIT = "exit"
ROUTE_CAPABILITIES = "capabilities"
ROUTE_INTERNAL_TOOLS = "internal_tools"
ROUTE_OPERATIONS = "operations"
ROUTE_INTERNAL_QUERY = "internal_query"
ROUTE_INTERNAL_FORGET = "internal_forget"
ROUTE_MAINTENANCE = "maintenance"
ROUTE_SYSTEM_STATE = "system_state"
ROUTE_MEMORY_LOOKUP = "memory_lookup"
ROUTE_MEMORY_LOOKUP_AMBIGUOUS = "memory_lookup_ambiguous"
ROUTE_MEMORY_UPDATE = "memory_update"
ROUTE_REPETITION = "repetition"
ROUTE_HEURISTIC_RESPONSE = "heuristic_response"
ROUTE_MODEL = "model"
ROUTE_MEMORY = ROUTE_MEMORY_LOOKUP


@dataclass(frozen=True)
class RouteDecision:
    action: str
    capability: str
    memory_intent: str | None = None
    operations_query: object | None = None
    tools_query: object | None = None
    internal_command: object | None = None
    maintenance_command: object | None = None
    system_state_command: object | None = None


def _normalize_user_message(user_input: str) -> str:
    return normalize_internal_text(user_input)


def _is_repeated_user_input(
    user_turn: UserTurn,
    conversation: list[dict[str, str]],
    recent_limit: int = 6,
) -> bool:
    current_input = _normalize_user_message(user_turn.raw)
    if not current_input:
        return False

    recent_user_messages = [
        message["content"]
        for message in conversation
        if message.get("role") == "user"
    ][-recent_limit:]

    return any(_normalize_user_message(message) == current_input for message in recent_user_messages)


def route_turn(
    user_turn: UserTurn,
    conversation: list[dict[str, str]] | None = None,
    memory: dict[str, object] | None = None,
) -> RouteDecision:
    conversation = conversation or []
    memory = memory or {}

    if user_turn.should_exit:
        return RouteDecision(
            action=ROUTE_EXIT,
            capability=CAPABILITY_EXIT,
        )

    tools_query = analyze_internal_tools_query(user_turn.raw)
    if tools_query:
        return RouteDecision(
            action=ROUTE_INTERNAL_TOOLS,
            capability=(
                CAPABILITY_INTERNAL_TOOLS_CATALOG
                if tools_query.mode == "catalog"
                else CAPABILITY_INTERNAL_TOOLS_ACTIVE
            ),
            tools_query=tools_query,
        )

    operations_query = analyze_internal_operations_query(user_turn.raw)
    if operations_query:
        return RouteDecision(
            action=ROUTE_OPERATIONS,
            capability=CAPABILITY_INTERNAL_OPERATIONS_CATALOG,
            operations_query=operations_query,
        )

    if analyze_capabilities_query(user_turn.raw):
        return RouteDecision(
            action=ROUTE_CAPABILITIES,
            capability=CAPABILITY_CAPABILITIES_CATALOG,
        )

    maintenance_command = analyze_maintenance_command(user_turn.raw)
    if maintenance_command:
        return RouteDecision(
            action=ROUTE_MAINTENANCE,
            capability=CAPABILITY_MAINTENANCE,
            maintenance_command=maintenance_command,
        )

    system_state_command = analyze_system_state_command(user_turn.raw)
    if system_state_command:
        return RouteDecision(
            action=ROUTE_SYSTEM_STATE,
            capability=CAPABILITY_SYSTEM_STATE,
            system_state_command=system_state_command,
        )

    internal_command = analyze_internal_command(user_turn.raw)
    if internal_command:
        route_action = (
            ROUTE_INTERNAL_FORGET
            if internal_command.action == "forget"
            else ROUTE_INTERNAL_QUERY
        )
        return RouteDecision(
            action=route_action,
            capability=CAPABILITY_INTERNAL_COMMAND,
            internal_command=internal_command,
        )

    memory_question = analyze_memory_question(user_turn.raw)
    if memory_question:
        if memory_question.is_ambiguous:
            return RouteDecision(
                action=ROUTE_MEMORY_LOOKUP_AMBIGUOUS,
                capability=CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS,
                memory_intent=memory_question.intent,
            )

        return RouteDecision(
            action=ROUTE_MEMORY_LOOKUP,
            capability=CAPABILITY_MEMORY_LOOKUP,
            memory_intent=memory_question.intent,
        )

    if _is_repeated_user_input(user_turn, conversation) and is_memory_update_already_stored(
        user_turn.raw,
        memory,
    ):
        return RouteDecision(
            action=ROUTE_REPETITION,
            capability=CAPABILITY_REPETITION,
        )

    if is_memory_update(user_turn.raw):
        return RouteDecision(
            action=ROUTE_MEMORY_UPDATE,
            capability=CAPABILITY_MEMORY_UPDATE,
        )

    return RouteDecision(
        action=ROUTE_MODEL,
        capability=CAPABILITY_MODEL_RESPONSE,
    )
