from __future__ import annotations

from dataclasses import dataclass

from .behavior_agent import BehaviorPlan
from .model_registry import ROLE_CRITIC
from .task_classifier import (
    TASK_TYPE_CRITIQUE,
    TASK_TYPE_TECHNICAL_REASONING,
    TASK_TYPE_VERIFICATION,
    TaskClassification,
)


CRITIC_MODE_NONE = "none"
CRITIC_MODE_POST_RESPONSE_CHECK = "post_response_check"
CRITIC_MODE_CRITIC_ONLY = "critic_only"


@dataclass(frozen=True)
class CriticPlan:
    requested: bool
    used: bool
    role: str | None = None
    mode: str = CRITIC_MODE_NONE
    reason: str | None = None


def plan_critic(task: TaskClassification | str) -> CriticPlan:
    if isinstance(task, TaskClassification):
        task_type = task.task_type
        critic_requested = task.critic_requested
        critic_reason = task.critic_reason
    else:
        task_type = task
        critic_requested = task_type == TASK_TYPE_TECHNICAL_REASONING
        critic_reason = (
            "technical_reasoning_light_verification"
            if task_type == TASK_TYPE_TECHNICAL_REASONING
            else None
        )

    if task_type == TASK_TYPE_TECHNICAL_REASONING:
        if not critic_requested:
            return CriticPlan(
                requested=False,
                used=False,
                role=None,
                mode=CRITIC_MODE_NONE,
                reason="technical_reasoning_primary_only",
            )

        return CriticPlan(
            requested=True,
            used=False,
            role=ROLE_CRITIC,
            mode=CRITIC_MODE_POST_RESPONSE_CHECK,
            reason=critic_reason or "technical_reasoning_light_verification",
        )

    if task_type in {TASK_TYPE_VERIFICATION, TASK_TYPE_CRITIQUE}:
        return CriticPlan(
            requested=False,
            used=False,
            role=ROLE_CRITIC,
            mode=CRITIC_MODE_CRITIC_ONLY,
            reason="critic_role_ready_for_direct_evaluation",
        )

    return CriticPlan(
        requested=False,
        used=False,
        role=None,
        mode=CRITIC_MODE_NONE,
        reason=None,
    )


def build_critic_prompt(
    *,
    conversation: list[dict[str, str]],
    behavior_plan: BehaviorPlan,
    primary_response: str,
) -> str:
    recent_user = next(
        (msg["content"] for msg in reversed(conversation) if msg.get("role") == "user"),
        "",
    )
    task_hint = (
        "Chequea claridad técnica, posibles sobreafirmaciones, contradicciones y omisiones."
        if behavior_plan.intent == "technical_troubleshoot"
        else "Chequea si la respuesta principal tiene una afirmación demasiado fuerte, una omisión importante o una cautela útil."
    )

    return (
        "Usuario:\n"
        f"{recent_user}\n\n"
        "Respuesta principal de AURA:\n"
        f"{primary_response}\n\n"
        "Tarea del verificador:\n"
        f"{task_hint}\n"
        "Responde en una sola línea con VERIFICADA, AJUSTE o DUDOSA."
    )
