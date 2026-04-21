from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from config import (
    CRITIC_HIGH_RISK_HINTS,
    CRITIC_REVIEW_HINTS,
    ROUTER_HELPER_MAX_INPUT_CHARS,
    ROUTER_HELPER_MAX_INPUT_WORDS,
    ROUTER_HELPER_TRIGGER_HINTS,
    TECHNICAL_COMPLEXITY_WORD_THRESHOLD,
)

from .behavior_agent import (
    INTENT_CONSISTENCY,
    INTENT_FEASIBILITY,
    INTENT_TECHNICAL_EXPLAIN,
    INTENT_TECHNICAL_TROUBLESHOOT,
    BehaviorPlan,
)
from .model_registry import ROLE_CRITIC, ROLE_PRIMARY


ROUTE_CAPABILITIES = "capabilities"
ROUTE_HEURISTIC_RESPONSE = "heuristic_response"
ROUTE_INTERNAL_FORGET = "internal_forget"
ROUTE_INTERNAL_QUERY = "internal_query"
ROUTE_INTERNAL_TOOLS = "internal_tools"
ROUTE_MAINTENANCE = "maintenance"
ROUTE_MEMORY_LOOKUP = "memory_lookup"
ROUTE_MEMORY_LOOKUP_AMBIGUOUS = "memory_lookup_ambiguous"
ROUTE_MEMORY_UPDATE = "memory_update"
ROUTE_OPERATIONS = "operations"
ROUTE_REPETITION = "repetition"
ROUTE_SYSTEM_STATE = "system_state"


TASK_TYPE_CHAT_RESPONSE = "chat_response"
TASK_TYPE_TECHNICAL_REASONING = "technical_reasoning"
TASK_TYPE_VERIFICATION = "verification"
TASK_TYPE_CRITIQUE = "critique"
TASK_TYPE_FALLBACK_CHAT = "fallback_chat"
TASK_TYPE_STRUCTURED_INTERNAL = "structured_internal"
TASK_TYPE_NO_MODEL_NEEDED = "no_model_needed"


@dataclass(frozen=True)
class TaskClassification:
    task_type: str
    requested_role: str
    no_model_needed: bool
    no_model_reason: str | None = None
    critic_requested: bool = False
    critic_role: str | None = None
    critic_reason: str | None = None
    risk_profile: str = "low"
    router_hint: str = "none"


def _normalize_text(text: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(character for character in normalized if not unicodedata.combining(character)).casefold()


def _extract_last_user_message(
    *,
    user_input: str | None = None,
    conversation: list[dict[str, str]] | None = None,
) -> str:
    if user_input:
        return user_input

    if not conversation:
        return ""

    for message in reversed(conversation):
        if message.get("role") == "user" and message.get("content"):
            return str(message["content"])

    return ""


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    return any(hint in text for hint in hints)


def _has_repeated_user_prompt(
    normalized_input: str,
    conversation: list[dict[str, str]] | None,
) -> bool:
    if not normalized_input or not conversation:
        return False

    seen_same_prompt = 0
    for message in conversation[:-1]:
        if message.get("role") != "user":
            continue
        if _normalize_text(str(message.get("content", ""))) == normalized_input:
            seen_same_prompt += 1
            if seen_same_prompt >= 1:
                return True

    return False


def _should_request_critic_for_technical_explain(normalized_input: str) -> tuple[bool, str | None]:
    if not normalized_input:
        return True, "technical_explain_default_guard"

    word_count = len(normalized_input.split())

    if _contains_any(normalized_input, CRITIC_REVIEW_HINTS):
        return True, "explicit_review_or_verification_request"

    if _contains_any(normalized_input, CRITIC_HIGH_RISK_HINTS):
        return True, "technical_high_risk_surface"

    if word_count >= TECHNICAL_COMPLEXITY_WORD_THRESHOLD:
        return True, "complex_technical_explain"

    return False, None


def _resolve_risk_profile(
    *,
    behavior_intent: str,
    normalized_input: str,
    critic_requested: bool,
) -> str:
    if behavior_intent == INTENT_TECHNICAL_TROUBLESHOOT:
        if _contains_any(normalized_input, CRITIC_HIGH_RISK_HINTS):
            return "high"
        return "medium"

    if behavior_intent == INTENT_TECHNICAL_EXPLAIN:
        if critic_requested:
            return "medium"
        return "low"

    return "low"


def _resolve_router_hint(normalized_input: str) -> str:
    if not normalized_input:
        return "short_focus"

    if any(symbol in normalized_input for symbol in ("```", "traceback", "error:", "exception")):
        return "none"

    word_count = len(normalized_input.split())
    if word_count > ROUTER_HELPER_MAX_INPUT_WORDS or len(normalized_input) > ROUTER_HELPER_MAX_INPUT_CHARS:
        return "none"

    if _contains_any(normalized_input, ROUTER_HELPER_TRIGGER_HINTS):
        return "short_focus"

    if normalized_input.endswith("?") or word_count <= 6:
        return "short_focus"

    return "none"


def classify_task(
    behavior_plan: BehaviorPlan,
    route_action: str | None = None,
    *,
    user_input: str | None = None,
    conversation: list[dict[str, str]] | None = None,
) -> TaskClassification:
    last_user_message = _extract_last_user_message(
        user_input=user_input,
        conversation=conversation,
    )
    normalized_input = _normalize_text(last_user_message)

    if behavior_plan.direct_response:
        return TaskClassification(
            task_type=TASK_TYPE_NO_MODEL_NEEDED,
            requested_role="none",
            no_model_needed=True,
            no_model_reason="behavior_direct_response",
            critic_requested=False,
            critic_role=None,
            critic_reason=None,
            risk_profile="low",
            router_hint="none",
        )

    if route_action in {
        ROUTE_CAPABILITIES,
        ROUTE_HEURISTIC_RESPONSE,
        ROUTE_INTERNAL_FORGET,
        ROUTE_INTERNAL_QUERY,
        ROUTE_INTERNAL_TOOLS,
        ROUTE_MAINTENANCE,
        ROUTE_MEMORY_LOOKUP,
        ROUTE_MEMORY_LOOKUP_AMBIGUOUS,
        ROUTE_MEMORY_UPDATE,
        ROUTE_OPERATIONS,
        ROUTE_REPETITION,
        ROUTE_SYSTEM_STATE,
    }:
        return TaskClassification(
            task_type=TASK_TYPE_NO_MODEL_NEEDED,
            requested_role="none",
            no_model_needed=True,
            no_model_reason="route_resolved_without_model",
            critic_requested=False,
            critic_role=None,
            critic_reason=None,
            risk_profile="low",
            router_hint="none",
        )

    if behavior_plan.intent == INTENT_TECHNICAL_TROUBLESHOOT:
        return TaskClassification(
            task_type=TASK_TYPE_TECHNICAL_REASONING,
            requested_role=ROLE_PRIMARY,
            no_model_needed=False,
            critic_requested=True,
            critic_role=ROLE_CRITIC,
            critic_reason="technical_troubleshoot_second_pass",
            risk_profile=_resolve_risk_profile(
                behavior_intent=behavior_plan.intent,
                normalized_input=normalized_input,
                critic_requested=True,
            ),
            router_hint="none",
        )

    if behavior_plan.intent == INTENT_TECHNICAL_EXPLAIN:
        critic_requested, critic_reason = _should_request_critic_for_technical_explain(
            normalized_input,
        )
        if not critic_requested and _has_repeated_user_prompt(normalized_input, conversation):
            critic_requested = True
            critic_reason = "repeated_technical_explain_followup"
        return TaskClassification(
            task_type=TASK_TYPE_TECHNICAL_REASONING,
            requested_role=ROLE_PRIMARY,
            no_model_needed=False,
            critic_requested=critic_requested,
            critic_role=ROLE_CRITIC,
            critic_reason=critic_reason,
            risk_profile=_resolve_risk_profile(
                behavior_intent=behavior_plan.intent,
                normalized_input=normalized_input,
                critic_requested=critic_requested,
            ),
            router_hint="none",
        )

    if behavior_plan.intent == INTENT_FEASIBILITY:
        return TaskClassification(
            task_type=TASK_TYPE_VERIFICATION,
            requested_role=ROLE_CRITIC,
            no_model_needed=False,
            critic_requested=False,
            critic_role=None,
            critic_reason=None,
            risk_profile="high",
            router_hint="none",
        )

    if behavior_plan.intent == INTENT_CONSISTENCY:
        return TaskClassification(
            task_type=TASK_TYPE_CRITIQUE,
            requested_role=ROLE_CRITIC,
            no_model_needed=False,
            critic_requested=False,
            critic_role=None,
            critic_reason=None,
            risk_profile="high",
            router_hint="none",
        )

    return TaskClassification(
        task_type=TASK_TYPE_CHAT_RESPONSE,
        requested_role=ROLE_PRIMARY,
        no_model_needed=False,
        critic_requested=False,
        critic_role=None,
        critic_reason=None,
        risk_profile="low",
        router_hint=_resolve_router_hint(normalized_input),
    )
