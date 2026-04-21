from dataclasses import dataclass
import unicodedata

from config import ROUTER_HELPER_MAX_INPUT_CHARS, ROUTER_HELPER_MAX_INPUT_WORDS

from .behavior_agent import (
    BehaviorPlan,
    INTENT_CONSISTENCY,
    INTENT_FEASIBILITY,
    INTENT_TECHNICAL_EXPLAIN,
    INTENT_TECHNICAL_TROUBLESHOOT,
    plan_behavior,
)
from .critic_layer import build_critic_prompt, plan_critic
from .fallback_manager import build_fallback_response
from .model_gateway import GatewayResult, invoke_model_gateway
from .model_registry import (
    ROLE_MICRO_EXPERT_ROUTER,
    ROLE_PRIMARY,
    build_default_model_registry,
    build_stack_health_snapshot,
)
from .response_composer import compose_response
from .runtime_quality import (
    QUALITY_STATUS_OK,
    assess_runtime_quality,
)
from .routing_policy import decide_routing
from .task_classifier import TASK_TYPE_CHAT_RESPONSE, classify_task


SYSTEM_PROMPT = """
Eres AURA, un asistente inteligente.

Respondes siempre en español.
Eres claro, útil, natural y directo.

Reglas:
- Usas la información conocida del usuario.
- No inventas cosas.
- Si no sabes algo, lo dices.
- Evitas respuestas genéricas, vacías o robóticas.
- No saludes ni metas relleno salvo que aporte valor real.
- En preguntas cortas, igual das una idea concreta.
- Sí puedes ayudar con dudas técnicas y troubleshooting básico.
- Si faltan datos técnicos, pides el dato mínimo útil y aun así das el paso más probable.
- En respuestas técnicas, mantén una estructura estable y clara.
- Si la consulta es técnica, prioriza una causa, criterio, ejemplo o paso accionable antes que teoría difusa.
- Si conoces preferencias del usuario, adapta el estilo de forma natural.
- Si el contexto laboral del usuario es relevante, úsalo para volver la respuesta más útil y aplicada.
""".strip()

ROUTER_HELPER_PROMPT = """
Resume en una sola línea el foco útil para responder.
No converses.
No repitas la pregunta.
Prioriza el ángulo más práctico, corto y útil.
No respondas como asistente principal.
""".strip()


def build_task_signature(*, task_type: str, intent: str, route_action: str | None) -> str:
    from backend.app.routing_neuron.core.observer import build_task_signature as observer_build_task_signature

    return observer_build_task_signature(
        task_type=task_type,
        intent=intent,
        route_action=route_action,
    )


def ingest_routing_observation(*args, **kwargs):
    from backend.app.routing_neuron.core.observer import ingest_routing_observation as observer_ingest_routing_observation

    return observer_ingest_routing_observation(*args, **kwargs)


def resolve_runtime_observation_seed(*args, **kwargs):
    from backend.app.routing_neuron.core.observer import (
        resolve_runtime_observation_seed as observer_resolve_runtime_observation_seed,
    )

    return observer_resolve_runtime_observation_seed(*args, **kwargs)


def apply_routing_runtime(*args, **kwargs):
    from backend.app.routing_neuron.core.runtime import apply_routing_runtime as runtime_apply_routing_runtime

    return runtime_apply_routing_runtime(*args, **kwargs)


def apply_runtime_to_routing_decision(*args, **kwargs):
    from backend.app.routing_neuron.core.runtime import (
        apply_runtime_to_routing_decision as runtime_apply_runtime_to_routing_decision,
    )

    return runtime_apply_runtime_to_routing_decision(*args, **kwargs)


def get_default_routing_registry():
    from backend.app.routing_neuron.core.runtime import get_default_routing_registry as runtime_get_default_routing_registry

    return runtime_get_default_routing_registry()


def record_runtime_outcome(*args, **kwargs):
    from backend.app.routing_neuron.core.runtime import record_runtime_outcome as runtime_record_runtime_outcome

    return runtime_record_runtime_outcome(*args, **kwargs)


def set_default_routing_registry(registry):
    from backend.app.routing_neuron.core.runtime import set_default_routing_registry as runtime_set_default_routing_registry

    return runtime_set_default_routing_registry(registry)


def refresh_routing_session_summary(registry, session_id: str):
    from backend.app.routing_neuron.core.maintenance import (
        refresh_routing_session_summary as maintenance_refresh_routing_session_summary,
    )

    return maintenance_refresh_routing_session_summary(registry, session_id)


@dataclass(frozen=True)
class ResponseExecution:
    response: str
    used_model: bool
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


def _build_prompt_memory_context(memory: dict[str, str]) -> str:
    context_lines = []

    if memory.get("name"):
        context_lines.append(f"El usuario se llama {memory['name']}.")

    if not context_lines:
        return ""

    return "\n".join(context_lines) + "\n\n"


def build_response_frame(intent: str) -> str:
    if intent == INTENT_TECHNICAL_TROUBLESHOOT:
        return (
            "Formato objetivo para esta respuesta:\n"
            "- Idea breve: resume el punto central en una frase.\n"
            "- Explicación clara: explica la causa o criterio principal.\n"
            "- Qué hacer: da 2 o 3 pasos concretos.\n"
            "- Cómo verificar: inclúyelo si aplica.\n\n"
        )

    if intent == INTENT_TECHNICAL_EXPLAIN:
        return (
            "Formato objetivo para esta respuesta:\n"
            "- Idea breve: resume el concepto.\n"
            "- Explicación clara: desarrolla solo lo necesario.\n"
            "- Pasos o ejemplo: inclúyelos si ayudan.\n\n"
        )

    if intent == INTENT_FEASIBILITY:
        return (
            "Formato objetivo para esta respuesta:\n"
            "- Juicio breve: posible, posible con condiciones, incierto, poco realista, contradictorio o inviable.\n"
            "- Motivo central: explica el límite o criterio principal.\n"
            "- Condición o reformulación: inclúyela si aporta claridad.\n\n"
        )

    if intent == INTENT_CONSISTENCY:
        return (
            "Formato objetivo para esta respuesta:\n"
            "- Calibración breve: qué tan firme o tentativo es el juicio.\n"
            "- Base o dependencia: explica qué lo sostiene o de qué depende.\n"
            "- Evidencia o tensión: inclúyela solo si aporta claridad.\n\n"
        )

    return ""


def build_prompt(
    conversation: list[dict[str, str]],
    memory: dict[str, str],
    profile_context: str = "",
    style_instructions: str = "",
    planning_instructions: str = "",
    response_frame: str = "",
) -> str:
    recent = conversation[-8:]
    prompt = SYSTEM_PROMPT.strip() + "\n\n"
    prompt += _build_prompt_memory_context(memory)

    if profile_context:
        prompt += "Perfil útil del usuario para esta respuesta:\n"
        prompt += f"{profile_context}\n\n"

    if style_instructions:
        prompt += "Instrucciones de estilo para esta respuesta:\n"
        prompt += f"{style_instructions}\n\n"

    if planning_instructions:
        prompt += f"{planning_instructions}\n\n"

    if response_frame:
        prompt += response_frame

    for msg in recent:
        role = "Usuario" if msg["role"] == "user" else "AURA"
        prompt += f"{role}: {msg['content']}\n"

    prompt += "AURA:"
    return prompt


def _build_no_model_execution(
    resolved_plan: BehaviorPlan,
    task_type: str,
    critic_requested: bool,
    critic_used: bool,
    no_model_reason: str | None,
    *,
    fallback_pressure: str | None = None,
) -> ResponseExecution:
    composed = compose_response(direct_response=resolved_plan.direct_response)
    return ResponseExecution(
        response=composed.response,
        used_model=composed.used_model,
        task_type=task_type,
        routing_decision="skip_model",
        selected_provider=None,
        selected_role=None,
        provider_available=None,
        provider_attempts=(),
        fallback_used=False,
        fallback_reason=None,
        composition_mode=composed.composition_mode,
        critic_requested=critic_requested,
        critic_used=critic_used,
        critic_provider=None,
        critic_available=None,
        critic_result_status=None,
        critic_summary=None,
        verification_outcome=None,
        verification_mode=None,
        no_model_reason=no_model_reason,
        provider_trace=("gateway:no_model",),
        gateway_mode="no_model",
        provider_result_status=None,
        runtime_quality_status="not_applicable",
        degradation_hint=None,
        critic_value="not_requested",
        router_value="not_needed",
        fallback_pressure=fallback_pressure,
        routing_neuron_applied=False,
        routing_neuron_id=None,
        routing_neuron_state=None,
        routing_neuron_type=None,
        routing_neuron_influence=None,
        routing_neuron_trace=None,
        routing_neuron_conflict=None,
        routing_neuron_fallback_reason=None,
        routing_neuron_decision=None,
        routing_neuron_alerts=None,
        routing_neuron_considered=False,
        routing_neuron_considered_ids=(),
        routing_neuron_selected=False,
        routing_neuron_barriers_checked=(),
        routing_neuron_barriers_blocked=(),
        routing_neuron_conflict_resolution=None,
        routing_neuron_outcome_label="no_model",
    )


def _build_fallback_execution(
    *,
    conversation: list[dict[str, str]],
    memory: dict[str, str],
    behavior_plan: BehaviorPlan,
    task_type: str,
    routing,
    critic_plan,
    provider_trace: tuple[str, ...],
    provider_result_status: str | None,
    error_text: str | None,
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
    provider_attempts: tuple[str, ...] | None = None,
    runtime_quality_status: str | None = None,
    degradation_hint: str | None = None,
    critic_value: str | None = None,
    router_value: str | None = None,
    fallback_pressure: str | None = None,
) -> ResponseExecution:
    fallback = build_fallback_response(
        conversation=conversation,
        memory=memory,
        behavior_plan=behavior_plan,
        error_text=error_text,
    )
    composed = compose_response(fallback_response=fallback.response)
    return ResponseExecution(
        response=composed.response,
        used_model=composed.used_model,
        task_type=task_type,
        routing_decision=routing.routing_decision,
        selected_provider=routing.selected_provider,
        selected_role=routing.selected_role,
        provider_available=routing.provider_available,
        provider_attempts=provider_attempts
        or (
            tuple(
                provider_id
                for provider_id in (
                    routing.selected_provider,
                    routing.critic_provider if routing.critic_used else None,
                )
                if provider_id is not None
            )
            or ()
        ),
        fallback_used=True,
        fallback_reason=fallback.fallback_reason,
        composition_mode=composed.composition_mode,
        critic_requested=routing.critic_requested,
        critic_used=False,
        critic_provider=routing.critic_provider,
        critic_available=routing.critic_available,
        critic_result_status=None,
        critic_summary=None,
        verification_outcome=None,
        verification_mode=critic_plan.mode if routing.critic_requested else None,
        no_model_reason=None,
        provider_trace=provider_trace + ("fallback:manager_response",),
        gateway_mode=routing.gateway_mode,
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


def _merge_provider_traces(*traces: tuple[str, ...]) -> tuple[str, ...]:
    merged: list[str] = []
    for trace in traces:
        for item in trace:
            merged.append(item)
    return tuple(merged)


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(character for character in normalized if not unicodedata.combining(character)).casefold()


def _last_user_message(conversation: list[dict[str, str]]) -> str:
    return next(
        (message["content"] for message in reversed(conversation) if message["role"] == "user"),
        "",
    )


def _resolve_risk_profile(
    task_type: str,
    intent: str,
    task_risk_profile: str | None = None,
) -> str:
    if task_risk_profile:
        return task_risk_profile

    if task_type in {"verification", "critique"}:
        return "high"

    if task_type == "technical_reasoning":
        if intent == INTENT_TECHNICAL_TROUBLESHOOT:
            return "medium"
        return "low"

    return "low"


def _resolve_budget_profile(task_type: str, critic_requested: bool) -> str:
    if task_type == TASK_TYPE_CHAT_RESPONSE:
        return "tight"

    if task_type == "technical_reasoning" and not critic_requested:
        return "tight"

    return "balanced"


def _build_primary_calibration_prompt(
    *,
    task_type: str,
    intent: str,
    router_hint: str,
) -> str:
    if task_type == "technical_reasoning":
        return (
            "Calibracion V0.39.6 para el primary:\n"
            "- evita respuestas placeholder, planas o demasiado abstractas\n"
            "- abre con la idea o criterio principal\n"
            "- anade una causa probable, ejemplo o paso concreto temprano\n"
            "- si algo depende de contexto, dilo sin vaciar la respuesta\n"
        )

    if intent == "open" or router_hint != "none":
        return (
            "Calibracion V0.39.6 para el primary:\n"
            "- responde natural y directo\n"
            "- evita saludos, muletillas y cierres vacios\n"
            "- deja una idea util o siguiente paso si suma valor\n"
        )

    return (
        "Calibracion V0.39.6 para el primary:\n"
        "- responde breve, clara y util\n"
        "- evita relleno y generalidades\n"
    )


def _should_use_router_helper(
    *,
    task_type: str,
    selected_role: str | None,
    router_hint: str,
    conversation: list[dict[str, str]],
) -> bool:
    if task_type != TASK_TYPE_CHAT_RESPONSE or selected_role != ROLE_PRIMARY:
        return False

    if router_hint == "none":
        return False

    last_user_message = _normalize_text(_last_user_message(conversation))
    if not last_user_message:
        return True

    if len(last_user_message.split()) > ROUTER_HELPER_MAX_INPUT_WORDS:
        return False

    if len(last_user_message) > ROUTER_HELPER_MAX_INPUT_CHARS:
        return False

    technical_markers = ("api", "error", "python", "traceback", "docker", "bug", "codigo")
    if any(marker in last_user_message for marker in technical_markers):
        return False

    return True


def _build_router_helper_prompt(
    *,
    conversation: list[dict[str, str]],
    memory: dict[str, str],
) -> str:
    last_user_message = next(
        (message["content"] for message in reversed(conversation) if message["role"] == "user"),
        "",
    )
    memory_hint = f"Usuario: {memory.get('name')}." if memory.get("name") else ""
    return (
        f"{ROUTER_HELPER_PROMPT}\n\n"
        f"{memory_hint}\n"
        f"Consulta actual: {last_user_message}\n\n"
        "Línea de foco:"
    ).strip()


def _build_transitional_fallback_reason(
    *,
    primary_provider_id: str | None,
    primary_status: str | None,
    fallback_provider_id: str | None,
) -> str:
    primary_label = primary_provider_id or "primary_missing"
    status_label = primary_status or "unavailable"
    fallback_label = fallback_provider_id or "fallback_missing"
    return (
        "transitional_fallback:"
        f"{primary_label}->{fallback_label}:"
        f"{status_label}"
    )


def _resolve_router_value(
    *,
    router_hint: str,
    helper_result: GatewayResult | None,
    helper_used: bool,
) -> str:
    if router_hint == "none":
        return "not_needed"

    if helper_used:
        return "applied"

    if helper_result is None:
        return "skipped"

    if helper_result.provider_result_status == "unavailable":
        return "unavailable"

    return "checked_no_value"


def _resolve_critic_value(
    *,
    critic_requested: bool,
    critic_available: bool | None,
    critic_used: bool,
    verification_outcome: str | None,
) -> str:
    if not critic_requested:
        return "not_requested"

    if critic_used:
        return verification_outcome or "used"

    if critic_available is False:
        return "unavailable"

    return "requested_no_value"


def _record_routing_runtime_observation(
    *,
    runtime_decision,
    session_id: str,
    task_signature: str,
    task_type: str,
    risk_profile: str,
    budget_profile: str,
    baseline_route: str,
    evaluated_route: str,
    activated_components: tuple[str, ...],
    success_label: str,
    outcome_summary: str,
    notes: str | None = None,
    latency_delta: float = 0.0,
    cost_delta: float = 0.0,
    quality_delta: float = 0.0,
    verification_delta: float = 0.0,
    consistency_delta: float = 0.0,
    critic_used: bool = False,
    verification_outcome: str | None = None,
) -> None:
    runtime_registry = runtime_decision.registry_snapshot or get_default_routing_registry()
    if runtime_decision.conflict:
        runtime_registry = runtime_registry.append_conflict(
            f"{session_id}:{runtime_decision.conflict}"
        )
    runtime_registry = record_runtime_outcome(
        runtime_registry,
        runtime_decision,
        session_id=session_id,
        task_signature=task_signature,
        outcome_label=success_label,
        outcome_summary=outcome_summary,
    )
    observation_seed = resolve_runtime_observation_seed(
        task_signature=task_signature,
        task_type=task_type,
        risk_profile=risk_profile,
        baseline_route=baseline_route,
        evaluated_route=evaluated_route,
        runtime_influence=runtime_decision.influence,
        prompt_transform=runtime_decision.prompt_transform,
        critic_used=critic_used,
        verification_outcome=verification_outcome,
    )
    updated_registry, _, _, _ = ingest_routing_observation(
        runtime_registry,
        task_signature=task_signature,
        session_id=session_id,
        task_profile=task_type,
        risk_profile=risk_profile,
        budget_profile=budget_profile,
        baseline_route=baseline_route,
        recent_route=baseline_route,
        evaluated_route=evaluated_route,
        activated_components=activated_components,
        latency_ms=0.0,
        latency_delta=latency_delta,
        cost_delta=cost_delta,
        quality_delta=quality_delta,
        verification_delta=verification_delta,
        consistency_delta=consistency_delta,
        success_label=success_label,
        outcome_summary=outcome_summary[:120],
        activation_rule=observation_seed.activation_rule,
        routing_condition=observation_seed.routing_condition,
        intermediate_transform=observation_seed.intermediate_transform,
        notes=notes or runtime_decision.fallback_reason,
        routing_neuron_considered=runtime_decision.considered,
        considered_neuron_ids=runtime_decision.considered_ids,
        routing_neuron_selected=runtime_decision.selected,
        routing_neuron_decision=runtime_decision.decision,
        routing_neuron_influence=runtime_decision.influence,
        routing_neuron_barriers_checked=runtime_decision.barriers_checked,
        routing_neuron_barriers_blocked=runtime_decision.barriers_blocked,
        routing_neuron_conflict=runtime_decision.conflict,
        routing_neuron_conflict_resolution=runtime_decision.conflict_resolution,
        routing_neuron_fallback_reason=runtime_decision.fallback_reason,
        routing_neuron_outcome_label=success_label,
        routing_neuron_decision_path=runtime_decision.decision_path,
    )
    refreshed_registry = refresh_routing_session_summary(updated_registry, session_id)
    set_default_routing_registry(refreshed_registry)


def execute_model_response(
    conversation: list[dict[str, str]],
    memory: dict[str, str],
    llama_path: str,
    model_path: str,
    behavior_plan: BehaviorPlan | None = None,
    route_action: str | None = None,
    critic_llama_path: str | None = None,
    critic_model_path: str | None = None,
    router_llama_path: str | None = None,
    router_model_path: str | None = None,
    fallback_llama_path: str | None = None,
    fallback_model_path: str | None = None,
    session_id: str | None = None,
) -> ResponseExecution:
    resolved_plan = behavior_plan or plan_behavior(conversation, memory)
    last_user_message = _last_user_message(conversation)
    task = classify_task(
        resolved_plan,
        route_action=route_action,
        conversation=conversation,
    )
    critic_plan = plan_critic(task)
    registry = build_default_model_registry(
        llama_path=llama_path,
        model_path=model_path,
        critic_llama_path=critic_llama_path,
        critic_model_path=critic_model_path,
        router_llama_path=router_llama_path,
        router_model_path=router_model_path,
        fallback_llama_path=fallback_llama_path,
        fallback_model_path=fallback_model_path,
    )
    stack_health = build_stack_health_snapshot(registry)
    routing = decide_routing(
        task,
        registry,
        critic_plan,
    )
    task_signature = build_task_signature(
        task_type=task.task_type,
        intent=resolved_plan.intent,
        route_action=route_action,
    )
    risk_profile = _resolve_risk_profile(
        task.task_type,
        resolved_plan.intent,
        task.risk_profile,
    )
    budget_profile = _resolve_budget_profile(task.task_type, routing.critic_requested)
    baseline_route = routing.routing_decision
    runtime_decision = apply_routing_runtime(
        routing,
        task_signature=task_signature,
        task_type=task.task_type,
        route_action=route_action,
        risk_profile=risk_profile,
        budget_profile=budget_profile,
    )
    routing = apply_runtime_to_routing_decision(routing, runtime_decision)

    if task.no_model_needed:
        return _build_no_model_execution(
            resolved_plan=resolved_plan,
            task_type=task.task_type,
            critic_requested=False,
            critic_used=False,
            no_model_reason=task.no_model_reason,
            fallback_pressure=stack_health.fallback_pressure,
        )

    if routing.selected_provider is None:
        _record_routing_runtime_observation(
            runtime_decision=runtime_decision,
            session_id=session_id or "runtime_session",
            task_signature=task_signature,
            task_type=task.task_type,
            risk_profile=risk_profile,
            budget_profile=budget_profile,
            baseline_route=baseline_route,
            evaluated_route=routing.routing_decision,
            activated_components=(),
            success_label="fallback_no_provider",
            outcome_summary="fallback sin provider primario disponible",
            notes="selected_provider_missing",
        )
        return _build_fallback_execution(
            conversation=conversation,
            memory=memory,
            behavior_plan=resolved_plan,
            task_type=task.task_type,
            routing=routing,
            critic_plan=critic_plan,
            provider_trace=(
                ("gateway:primary:no_provider_selected",)
                if routing.selected_provider is None
                else (
                    f"primary:selected:{routing.selected_provider}",
                    "primary:unavailable",
                )
            ),
            provider_result_status="unavailable",
            error_text=routing.routing_decision,
            routing_neuron_applied=runtime_decision.applied,
            routing_neuron_id=runtime_decision.neuron_id,
            routing_neuron_state=runtime_decision.neuron_state,
            routing_neuron_type=runtime_decision.neuron_type,
            routing_neuron_influence=runtime_decision.influence,
            routing_neuron_trace=runtime_decision.trace,
            routing_neuron_conflict=runtime_decision.conflict,
            routing_neuron_fallback_reason=runtime_decision.fallback_reason,
            routing_neuron_decision=runtime_decision.decision,
            routing_neuron_alerts=runtime_decision.alerts,
            routing_neuron_considered=runtime_decision.considered,
            routing_neuron_considered_ids=runtime_decision.considered_ids,
            routing_neuron_selected=runtime_decision.selected,
            routing_neuron_barriers_checked=runtime_decision.barriers_checked,
            routing_neuron_barriers_blocked=runtime_decision.barriers_blocked,
            routing_neuron_conflict_resolution=runtime_decision.conflict_resolution,
            routing_neuron_outcome_label="fallback_no_provider",
            routing_neuron_decision_path=runtime_decision.decision_path,
            runtime_quality_status="not_available",
            degradation_hint="primary_provider_missing",
            critic_value=_resolve_critic_value(
                critic_requested=routing.critic_requested,
                critic_available=routing.critic_available,
                critic_used=False,
                verification_outcome=None,
            ),
            router_value="not_needed",
            fallback_pressure=stack_health.fallback_pressure,
        )

    prompt = build_prompt(
        conversation,
        memory,
        profile_context=resolved_plan.profile_context,
        style_instructions=resolved_plan.style_instructions,
        planning_instructions=(
            (
                resolved_plan.planning_instructions + "\n\n"
                if resolved_plan.planning_instructions
                else ""
            )
            + _build_primary_calibration_prompt(
                task_type=task.task_type,
                intent=resolved_plan.intent,
                router_hint=task.router_hint,
            )
        ),
        response_frame=build_response_frame(resolved_plan.intent),
    )
    if runtime_decision.prompt_transform:
        prompt = (
            "Transformación operativa sugerida por Routing Neuron:\n"
            f"{runtime_decision.prompt_transform}\n\n"
            f"{prompt}"
        )

    helper_result: GatewayResult | None = None
    helper_used = False
    helper_trace: tuple[str, ...] = ()
    helper_attempts: list[str] = []
    effective_gateway_mode = routing.gateway_mode

    if _should_use_router_helper(
        task_type=task.task_type,
        selected_role=routing.selected_role,
        router_hint=task.router_hint,
        conversation=conversation,
    ):
        helper_prompt = _build_router_helper_prompt(
            conversation=conversation,
            memory=memory,
        )
        helper_provider = registry.get_provider_for_role(ROLE_MICRO_EXPERT_ROUTER)
        if helper_provider is not None:
            helper_result = invoke_model_gateway(
                prompt=helper_prompt,
                routing_decision=routing,
                registry=registry,
                provider_id=helper_provider.descriptor.provider_id,
                role=ROLE_MICRO_EXPERT_ROUTER,
                trace_label="router",
            )
            helper_trace = helper_result.provider_trace
            helper_attempts.extend(helper_result.provider_attempts)
            if helper_result.provider_response is not None:
                helper_used = True
                effective_gateway_mode = f"router_helper+{effective_gateway_mode}"
                prompt = (
                    "Apoyo breve del router/helper local:\n"
                    f"{helper_result.provider_response}\n\n"
                    f"{prompt}"
                )

    router_value = _resolve_router_value(
        router_hint=task.router_hint,
        helper_result=helper_result,
        helper_used=helper_used,
    )

    primary_result = invoke_model_gateway(
        prompt=prompt,
        routing_decision=routing,
        registry=registry,
        provider_id=routing.selected_provider,
        role=routing.selected_role,
        trace_label="primary",
    )
    provider_attempts = list(helper_attempts)
    provider_attempts.extend(primary_result.provider_attempts)
    provider_trace = (
        _merge_provider_traces(helper_trace, primary_result.provider_trace)
        if helper_trace
        else primary_result.provider_trace
    )
    fallback_provider = registry.get_fallback_provider()
    transitional_fallback_used = False
    transitional_fallback_reason = None
    primary_failure_status = primary_result.provider_result_status
    runtime_quality = assess_runtime_quality(
        primary_result.provider_response,
        task_type=task.task_type,
        fallback_available=bool(
            fallback_provider is not None and fallback_provider.descriptor.availability
        ),
        source_text=last_user_message,
    )
    initial_runtime_issue = runtime_quality.issue

    if (
        primary_result.provider_response is not None
        and runtime_quality.retry_with_fallback
        and routing.selected_role == ROLE_PRIMARY
        and fallback_provider is not None
        and fallback_provider.descriptor.availability
    ):
        fallback_result = invoke_model_gateway(
            prompt=prompt,
            routing_decision=routing,
            registry=registry,
            provider_id=fallback_provider.descriptor.provider_id,
            role=ROLE_PRIMARY,
            trace_label="fallback",
        )
        provider_attempts.extend(fallback_result.provider_attempts)
        provider_trace = _merge_provider_traces(provider_trace, fallback_result.provider_trace)
        fallback_quality = assess_runtime_quality(
            fallback_result.provider_response,
            task_type=task.task_type,
            fallback_available=False,
            source_text=last_user_message,
        )
        provider_trace = _merge_provider_traces(
            provider_trace,
            (f"quality_guard:trigger:{runtime_quality.issue}",),
        )
        if (
            fallback_result.provider_response is not None
            and fallback_quality.status == QUALITY_STATUS_OK
        ):
            primary_result = fallback_result
            transitional_fallback_used = True
            transitional_fallback_reason = _build_transitional_fallback_reason(
                primary_provider_id=routing.selected_provider,
                primary_status=f"quality_guard_{runtime_quality.issue}",
                fallback_provider_id=fallback_result.selected_provider,
            )
            runtime_quality = fallback_quality
            effective_gateway_mode = f"quality_guard+transitional_fallback+{effective_gateway_mode}"
            provider_trace = _merge_provider_traces(
                provider_trace,
                (
                    "fallback:used:transitional",
                    f"fallback:reason:{transitional_fallback_reason}",
                    "quality_guard:recovered_by_fallback",
                ),
            )
        else:
            provider_trace = _merge_provider_traces(
                provider_trace,
                (f"quality_guard:fallback_status:{fallback_quality.status}",),
            )

    if primary_result.provider_response is None:
        fallback_result: GatewayResult | None = None
        if routing.selected_role == ROLE_PRIMARY and fallback_provider is not None:
            fallback_result = invoke_model_gateway(
                prompt=prompt,
                routing_decision=routing,
                registry=registry,
                provider_id=fallback_provider.descriptor.provider_id,
                role=ROLE_PRIMARY,
                trace_label="fallback",
            )
            provider_attempts.extend(fallback_result.provider_attempts)
            provider_trace = _merge_provider_traces(provider_trace, fallback_result.provider_trace)
            if fallback_result.provider_response is not None:
                primary_result = fallback_result
                runtime_quality = assess_runtime_quality(
                    primary_result.provider_response,
                    task_type=task.task_type,
                    fallback_available=False,
                    source_text=last_user_message,
                )
                transitional_fallback_used = True
                transitional_fallback_reason = _build_transitional_fallback_reason(
                    primary_provider_id=routing.selected_provider,
                    primary_status=primary_failure_status,
                    fallback_provider_id=fallback_result.selected_provider,
                )
                effective_gateway_mode = f"transitional_fallback+{effective_gateway_mode}"
                provider_trace = _merge_provider_traces(
                    provider_trace,
                    (
                        "fallback:used:transitional",
                        f"fallback:reason:{transitional_fallback_reason}",
                    ),
                )

        if primary_result.provider_response is None:
            if fallback_result is not None and fallback_result.provider_error:
                error_text = fallback_result.provider_error
            else:
                error_text = primary_result.provider_error
            fallback_components = tuple(
                component
                for component, enabled in (
                    ("router_helper", helper_used),
                    ("primary", bool(routing.selected_provider)),
                    ("transitional_fallback", transitional_fallback_used),
                )
                if enabled
            )
            _record_routing_runtime_observation(
                runtime_decision=runtime_decision,
                session_id=session_id or "runtime_session",
                task_signature=task_signature,
                task_type=task.task_type,
                risk_profile=risk_profile,
                budget_profile=budget_profile,
                baseline_route=baseline_route,
                evaluated_route=routing.routing_decision,
                activated_components=fallback_components,
                success_label="fallback_runtime_error",
                outcome_summary=error_text or "fallback por error de runtime",
                notes=runtime_decision.fallback_reason or error_text,
            )
            return _build_fallback_execution(
                conversation=conversation,
                memory=memory,
                behavior_plan=resolved_plan,
                task_type=task.task_type,
                routing=routing,
                critic_plan=critic_plan,
                provider_trace=provider_trace,
                provider_result_status=primary_result.provider_result_status,
                error_text=error_text,
                routing_neuron_applied=runtime_decision.applied,
                routing_neuron_id=runtime_decision.neuron_id,
                routing_neuron_state=runtime_decision.neuron_state,
                routing_neuron_type=runtime_decision.neuron_type,
                routing_neuron_influence=runtime_decision.influence,
                routing_neuron_trace=runtime_decision.trace,
                routing_neuron_conflict=runtime_decision.conflict,
                routing_neuron_fallback_reason=runtime_decision.fallback_reason,
                routing_neuron_decision=runtime_decision.decision,
                routing_neuron_alerts=runtime_decision.alerts,
                routing_neuron_considered=runtime_decision.considered,
                routing_neuron_considered_ids=runtime_decision.considered_ids,
                routing_neuron_selected=runtime_decision.selected,
                routing_neuron_barriers_checked=runtime_decision.barriers_checked,
                routing_neuron_barriers_blocked=runtime_decision.barriers_blocked,
                routing_neuron_conflict_resolution=runtime_decision.conflict_resolution,
                routing_neuron_outcome_label="fallback_runtime_error",
                routing_neuron_decision_path=runtime_decision.decision_path,
                provider_attempts=tuple(provider_attempts),
                runtime_quality_status=runtime_quality.status,
                degradation_hint=runtime_quality.degradation_hint or "primary_runtime_failure",
                critic_value=_resolve_critic_value(
                    critic_requested=routing.critic_requested,
                    critic_available=routing.critic_available,
                    critic_used=False,
                    verification_outcome=None,
                ),
                router_value=router_value,
                fallback_pressure=stack_health.fallback_pressure,
            )

    quality_rescue_allowed = (
        task.task_type == "technical_reasoning"
        and resolved_plan.intent == INTENT_TECHNICAL_EXPLAIN
    )
    if (
        quality_rescue_allowed
        and primary_result.provider_response is not None
        and runtime_quality.status != QUALITY_STATUS_OK
    ):
        provider_trace = _merge_provider_traces(
            provider_trace,
            (
                f"quality_guard:trigger:{runtime_quality.issue}",
                "quality_guard:recovered_by_fallback_manager",
            ),
        )
        rescue_components = tuple(
            component
            for component, enabled in (
                ("router_helper", helper_used),
                ("primary", bool(routing.selected_provider)),
                ("transitional_fallback", transitional_fallback_used),
                ("fallback_manager", True),
            )
            if enabled
        )
        _record_routing_runtime_observation(
            runtime_decision=runtime_decision,
            session_id=session_id or "runtime_session",
            task_signature=task_signature,
            task_type=task.task_type,
            risk_profile=risk_profile,
            budget_profile=budget_profile,
            baseline_route=baseline_route,
            evaluated_route=routing.routing_decision,
            activated_components=rescue_components,
            success_label="fallback_quality_rescue",
            outcome_summary=runtime_quality.issue or runtime_quality.status,
            notes=runtime_decision.fallback_reason or runtime_quality.issue,
        )
        return _build_fallback_execution(
            conversation=conversation,
            memory=memory,
            behavior_plan=resolved_plan,
            task_type=task.task_type,
            routing=routing,
            critic_plan=critic_plan,
            provider_trace=provider_trace,
            provider_result_status=primary_result.provider_result_status,
            error_text=runtime_quality.issue or runtime_quality.status,
            routing_neuron_applied=runtime_decision.applied,
            routing_neuron_id=runtime_decision.neuron_id,
            routing_neuron_state=runtime_decision.neuron_state,
            routing_neuron_type=runtime_decision.neuron_type,
            routing_neuron_influence=runtime_decision.influence,
            routing_neuron_trace=runtime_decision.trace,
            routing_neuron_conflict=runtime_decision.conflict,
            routing_neuron_fallback_reason=runtime_decision.fallback_reason,
            routing_neuron_decision=runtime_decision.decision,
            routing_neuron_alerts=runtime_decision.alerts,
            routing_neuron_considered=runtime_decision.considered,
            routing_neuron_considered_ids=runtime_decision.considered_ids,
            routing_neuron_selected=runtime_decision.selected,
            routing_neuron_barriers_checked=runtime_decision.barriers_checked,
            routing_neuron_barriers_blocked=runtime_decision.barriers_blocked,
            routing_neuron_conflict_resolution=runtime_decision.conflict_resolution,
            routing_neuron_outcome_label="fallback_quality_rescue",
            routing_neuron_decision_path=runtime_decision.decision_path,
            provider_attempts=tuple(provider_attempts),
            runtime_quality_status="recovered_by_fallback_manager",
            degradation_hint=(
                f"quality_guard_rescued_by_fallback_manager:{initial_runtime_issue or runtime_quality.issue}"
                if initial_runtime_issue or runtime_quality.issue
                else runtime_quality.degradation_hint or "quality_guard_rescued_by_fallback_manager"
            ),
            critic_value=_resolve_critic_value(
                critic_requested=routing.critic_requested,
                critic_available=routing.critic_available,
                critic_used=False,
                verification_outcome=None,
            ),
            router_value=router_value,
            fallback_pressure=stack_health.fallback_pressure,
        )

    critic_result: GatewayResult | None = None
    critic_used = False

    if routing.critic_requested and routing.critic_provider and routing.critic_available:
        critic_prompt = build_critic_prompt(
            conversation=conversation,
            behavior_plan=resolved_plan,
            primary_response=primary_result.provider_response,
        )
        critic_result = invoke_model_gateway(
            prompt=critic_prompt,
            routing_decision=routing,
            registry=registry,
            provider_id=routing.critic_provider,
            role=routing.critic_role,
            trace_label="critic",
        )
        critic_used = critic_result.provider_response is not None

    composed = compose_response(
        provider_response=primary_result.provider_response,
        critic_response=(
            critic_result.provider_response
            if critic_result is not None and critic_result.provider_response is not None
            else None
        ),
        selected_role=routing.selected_role,
    )

    critic_result_status = None
    critic_summary = None
    verification_outcome = None

    if critic_result is not None:
        provider_attempts.extend(critic_result.provider_attempts)
        provider_trace = _merge_provider_traces(provider_trace, critic_result.provider_trace)
        critic_result_status = critic_result.provider_result_status

    if routing.critic_requested and critic_result is None:
        critic_result_status = "unavailable"
        if routing.critic_provider:
            provider_trace = _merge_provider_traces(
                provider_trace,
                (
                    f"critic:selected:{routing.critic_provider}",
                    "critic:unavailable",
                ),
            )
        else:
            provider_trace = _merge_provider_traces(
                provider_trace,
                ("critic:no_provider_selected",),
            )

    if composed.critic_summary:
        critic_summary = composed.critic_summary
        verification_outcome = composed.verification_outcome

    critic_value = _resolve_critic_value(
        critic_requested=routing.critic_requested,
        critic_available=routing.critic_available,
        critic_used=critic_used,
        verification_outcome=verification_outcome,
    )

    degradation_hint = runtime_quality.degradation_hint
    if transitional_fallback_used:
        degradation_hint = "transitional_fallback_active"
    elif routing.critic_requested and routing.critic_available is False:
        degradation_hint = "critic_unavailable_primary_only"
    elif stack_health.health != "healthy":
        degradation_hint = f"stack_{stack_health.health}"

    provider_trace = _merge_provider_traces(
        provider_trace,
        (f"composer:{composed.composition_mode}",),
    )
    if helper_used:
        provider_trace = _merge_provider_traces(
            provider_trace,
            ("router:helper_applied",),
        )
    elif task.router_hint != "none":
        provider_trace = _merge_provider_traces(
            provider_trace,
            ("router:helper_skipped",),
        )

    activated_components = ["primary"]
    if critic_used:
        activated_components.append("critic")
    if helper_used:
        activated_components.append("router_helper")

    latency_delta = -50.0 if runtime_decision.influence == "skip_critic" and runtime_decision.applied else 0.0
    cost_delta = -0.15 if runtime_decision.influence == "skip_critic" and runtime_decision.applied else 0.0
    quality_delta = 0.02 if runtime_decision.applied and not critic_used else 0.0
    verification_delta = {
        "verified": 0.05,
        "adjustment_suggested": -0.03,
        "uncertain": -0.05,
    }.get(verification_outcome, 0.0)
    consistency_delta = (
        0.05
        if (
            not runtime_decision.applied
            and baseline_route == "primary_then_critic"
            and routing.routing_decision == "primary_then_critic"
            and critic_used
            and verification_outcome == "verified"
            and task.task_type == "technical_reasoning"
            and risk_profile in {"low", "medium"}
        )
        else 0.0
    )
    success_label = "fallback" if composed.composition_mode == "fallback_safe" else "stable_success"
    if transitional_fallback_used:
        success_label = "fallback"
    if runtime_decision.applied and runtime_decision.influence == "skip_critic" and composed.used_model:
        success_label = "improved"
    elif runtime_decision.decision in {"suggested_only", "blocked_by_barrier", "paused", "cooldown"}:
        success_label = "baseline_kept"

    _record_routing_runtime_observation(
        runtime_decision=runtime_decision,
        session_id=session_id or "runtime_session",
        task_signature=task_signature,
        risk_profile=risk_profile,
        budget_profile=budget_profile,
        baseline_route=baseline_route,
        evaluated_route=routing.routing_decision,
        activated_components=tuple(activated_components),
        success_label=success_label,
        outcome_summary=composed.response,
        notes=runtime_decision.fallback_reason,
        task_type=task.task_type,
        latency_delta=latency_delta,
        cost_delta=cost_delta,
        quality_delta=quality_delta,
        verification_delta=verification_delta,
        consistency_delta=consistency_delta,
        critic_used=critic_used,
        verification_outcome=verification_outcome,
    )

    return ResponseExecution(
        response=composed.response,
        used_model=composed.used_model,
        task_type=task.task_type,
        routing_decision=routing.routing_decision,
        selected_provider=primary_result.selected_provider,
        selected_role=primary_result.selected_role,
        provider_available=primary_result.provider_available,
        provider_attempts=tuple(provider_attempts),
        fallback_used=transitional_fallback_used,
        fallback_reason=transitional_fallback_reason,
        composition_mode=composed.composition_mode,
        critic_requested=routing.critic_requested,
        critic_used=critic_used,
        critic_provider=routing.critic_provider,
        critic_available=routing.critic_available,
        critic_result_status=critic_result_status,
        critic_summary=critic_summary,
        verification_outcome=verification_outcome,
        verification_mode=critic_plan.mode if routing.critic_requested else None,
        no_model_reason=None,
        provider_trace=provider_trace,
        gateway_mode=effective_gateway_mode,
        provider_result_status=primary_result.provider_result_status,
        runtime_quality_status=(
            "recovered_by_fallback"
            if transitional_fallback_used and runtime_quality.status == QUALITY_STATUS_OK
            else runtime_quality.status
        ),
        degradation_hint=(
            f"{degradation_hint}:{initial_runtime_issue}"
            if transitional_fallback_used and initial_runtime_issue and degradation_hint
            else degradation_hint
        ),
        critic_value=critic_value,
        router_value=router_value,
        fallback_pressure=stack_health.fallback_pressure,
        routing_neuron_applied=runtime_decision.applied,
        routing_neuron_id=runtime_decision.neuron_id,
        routing_neuron_state=runtime_decision.neuron_state,
        routing_neuron_type=runtime_decision.neuron_type,
        routing_neuron_influence=runtime_decision.influence,
        routing_neuron_trace=runtime_decision.trace,
        routing_neuron_conflict=runtime_decision.conflict,
        routing_neuron_fallback_reason=runtime_decision.fallback_reason,
        routing_neuron_decision=runtime_decision.decision,
        routing_neuron_alerts=runtime_decision.alerts,
        routing_neuron_considered=runtime_decision.considered,
        routing_neuron_considered_ids=runtime_decision.considered_ids,
        routing_neuron_selected=runtime_decision.selected,
        routing_neuron_barriers_checked=runtime_decision.barriers_checked,
        routing_neuron_barriers_blocked=runtime_decision.barriers_blocked,
        routing_neuron_conflict_resolution=runtime_decision.conflict_resolution,
        routing_neuron_outcome_label=success_label,
        routing_neuron_decision_path=runtime_decision.decision_path,
    )


def generate_model_response(
    conversation: list[dict[str, str]],
    memory: dict[str, str],
    llama_path: str,
    model_path: str,
) -> str:
    return execute_model_response(
        conversation=conversation,
        memory=memory,
        llama_path=llama_path,
        model_path=model_path,
    ).response


def generate_response(
    conversation: list[dict[str, str]],
    memory: dict[str, str],
    llama_path: str,
    model_path: str,
) -> str:
    return generate_model_response(
        conversation=conversation,
        memory=memory,
        llama_path=llama_path,
        model_path=model_path,
    )
