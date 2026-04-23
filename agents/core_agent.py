from dataclasses import asdict, dataclass
from typing import Any

from .behavior_agent import (
    INTENT_CAPABILITIES_COMMAND,
    INTENT_CONSISTENCY,
    INTENT_FEASIBILITY,
    INTENT_MAINTENANCE_COMMAND,
    INTENT_MEMORY_COMMAND,
    INTENT_MEMORY_QUERY,
    INTENT_OPERATIONS_COMMAND,
    INTENT_SYSTEM_COMMAND,
    INTENT_TOOLS_COMMAND,
    BehaviorPlan,
    classify_user_intent,
    plan_behavior_for_input,
)
from .capabilities_registry import (
    CAPABILITY_EXIT,
    CAPABILITY_HEURISTIC_RESPONSE,
    CapabilityContext,
)
from .capability_dispatcher import DispatchResult, dispatch
from .chat_agent import UserTurn, process_user_input
from .decision_engine import DecisionAnalysis, analyze_decision
from .memory_agent import remember_basic_memory
from .router_agent import (
    ROUTE_CAPABILITIES,
    ROUTE_HEURISTIC_RESPONSE,
    ROUTE_INTERNAL_FORGET,
    ROUTE_INTERNAL_TOOLS,
    ROUTE_INTERNAL_QUERY,
    ROUTE_MAINTENANCE,
    ROUTE_MEMORY_LOOKUP,
    ROUTE_MEMORY_LOOKUP_AMBIGUOUS,
    ROUTE_MEMORY_UPDATE,
    ROUTE_MODEL,
    ROUTE_OPERATIONS,
    ROUTE_REPETITION,
    ROUTE_SYSTEM_STATE,
    RouteDecision,
    route_turn,
)


RESPONSE_MODE_DIRECT = "direct"
RESPONSE_MODE_MEMORY = "memory"
RESPONSE_MODE_MODEL = "model"
RESPONSE_MODE_NONE = "none"

MEMORY_ROUTES = {
    ROUTE_INTERNAL_QUERY,
    ROUTE_INTERNAL_FORGET,
    ROUTE_MEMORY_LOOKUP,
    ROUTE_MEMORY_LOOKUP_AMBIGUOUS,
    ROUTE_MEMORY_UPDATE,
    ROUTE_REPETITION,
}


@dataclass(frozen=True)
class TurnMetadata:
    intent: str
    route: str
    response_mode: str
    used_memory: bool
    used_model: bool
    capability: str | None = None
    action: str | None = None
    tool: str | None = None
    tool_kind: str | None = None
    sequence: str | None = None
    sequence_kind: str | None = None
    goal: str | None = None
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
    route_trace: tuple[str, ...] | None = None
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
class TurnPlan:
    user_turn: UserTurn
    intent: str
    route_decision: RouteDecision
    behavior_plan: BehaviorPlan


@dataclass(frozen=True)
class TurnResult:
    response: str | None
    metadata: TurnMetadata
    should_exit: bool = False


def _resolve_response_mode(
    route_action: str,
    behavior_plan: BehaviorPlan,
) -> str:
    if route_action == ROUTE_INTERNAL_TOOLS:
        return RESPONSE_MODE_DIRECT

    if route_action == ROUTE_OPERATIONS:
        return RESPONSE_MODE_DIRECT

    if route_action == ROUTE_CAPABILITIES:
        return RESPONSE_MODE_DIRECT

    if route_action == ROUTE_MAINTENANCE:
        return RESPONSE_MODE_DIRECT

    if route_action == ROUTE_SYSTEM_STATE:
        return RESPONSE_MODE_DIRECT

    if route_action == ROUTE_HEURISTIC_RESPONSE:
        return RESPONSE_MODE_DIRECT

    if route_action in MEMORY_ROUTES:
        return RESPONSE_MODE_MEMORY

    if route_action == ROUTE_MODEL and behavior_plan.direct_response:
        return RESPONSE_MODE_DIRECT

    if route_action == ROUTE_MODEL:
        return RESPONSE_MODE_MODEL

    return RESPONSE_MODE_NONE


def _resolve_default_task_type(
    route_action: str,
    response_mode: str,
    used_model: bool,
    fallback_used: bool | None,
) -> str:
    if used_model:
        return "chat_response"

    if fallback_used:
        return "fallback_chat"

    if route_action == ROUTE_HEURISTIC_RESPONSE:
        return "no_model_needed"

    if route_action in {ROUTE_CAPABILITIES, ROUTE_INTERNAL_TOOLS, ROUTE_OPERATIONS}:
        return "structured_internal"

    if route_action in MEMORY_ROUTES:
        return "structured_internal"

    if route_action in {ROUTE_MAINTENANCE, ROUTE_SYSTEM_STATE}:
        return "structured_internal"

    if response_mode == RESPONSE_MODE_DIRECT:
        return "no_model_needed"

    return "chat_response"


def _resolve_default_routing_decision(
    route_action: str,
    response_mode: str,
    used_model: bool,
    fallback_used: bool | None,
) -> str | None:
    if used_model:
        return "use_provider"

    if fallback_used:
        return "fallback_response"

    return {
        ROUTE_HEURISTIC_RESPONSE: "skip_model",
        ROUTE_INTERNAL_TOOLS: "direct_internal_tools",
        ROUTE_CAPABILITIES: "direct_capabilities",
        ROUTE_OPERATIONS: "direct_operations",
        ROUTE_MAINTENANCE: "direct_maintenance",
        ROUTE_SYSTEM_STATE: "direct_system_state",
        ROUTE_MEMORY_LOOKUP: "direct_memory_lookup",
        ROUTE_MEMORY_LOOKUP_AMBIGUOUS: "direct_memory_lookup",
        ROUTE_MEMORY_UPDATE: "direct_memory_update",
        ROUTE_REPETITION: "direct_memory_repetition",
        ROUTE_INTERNAL_QUERY: "direct_memory_command",
        ROUTE_INTERNAL_FORGET: "direct_memory_command",
    }.get(route_action)


def _resolve_default_composition_mode(
    route_action: str,
    response_mode: str,
    used_model: bool,
    fallback_used: bool | None,
) -> str | None:
    if fallback_used:
        return "fallback_safe"

    if used_model:
        return "provider_primary"

    if route_action == ROUTE_HEURISTIC_RESPONSE:
        return "heuristic_direct"

    if response_mode in {RESPONSE_MODE_DIRECT, RESPONSE_MODE_MEMORY}:
        return "internal_direct"

    return None


def _resolve_default_no_model_reason(route_action: str) -> str | None:
    return {
        ROUTE_HEURISTIC_RESPONSE: "behavior_direct_response",
        ROUTE_INTERNAL_TOOLS: "resolved_by_internal_tools",
        ROUTE_CAPABILITIES: "resolved_by_capabilities_catalog",
        ROUTE_OPERATIONS: "resolved_by_operations_catalog",
        ROUTE_MAINTENANCE: "resolved_by_maintenance",
        ROUTE_SYSTEM_STATE: "resolved_by_system_state",
        ROUTE_MEMORY_LOOKUP: "resolved_by_memory_lookup",
        ROUTE_MEMORY_LOOKUP_AMBIGUOUS: "resolved_by_memory_lookup",
        ROUTE_MEMORY_UPDATE: "resolved_by_memory_update",
        ROUTE_REPETITION: "resolved_by_memory_repetition",
        ROUTE_INTERNAL_QUERY: "resolved_by_memory_command",
        ROUTE_INTERNAL_FORGET: "resolved_by_memory_command",
    }.get(route_action)


def _build_route_trace(
    route_action: str,
    capability: str | None,
    action: str | None,
    tool: str | None,
    routing_decision: str | None,
    gateway_mode: str | None,
) -> tuple[str, ...]:
    steps = [f"route:{route_action}"]

    if capability:
        steps.append(f"capability:{capability}")

    if action:
        steps.append(f"action:{action}")

    if tool:
        steps.append(f"tool:{tool}")

    if routing_decision:
        steps.append(f"routing:{routing_decision}")

    if gateway_mode:
        steps.append(f"gateway:{gateway_mode}")

    return tuple(steps)


def _resolve_default_provider_attempts(
    provider_attempts: tuple[str, ...] | None,
    response_mode: str,
) -> tuple[str, ...] | None:
    if provider_attempts is not None:
        return provider_attempts

    if response_mode != RESPONSE_MODE_MODEL:
        return ()

    return None


def _resolve_default_critic_flag(value: bool | None) -> bool:
    return bool(value) if value is not None else False


def _build_metadata(
    intent: str,
    route_action: str,
    behavior_plan: BehaviorPlan,
    memory: dict[str, Any],
    capability: str | None = None,
    action: str | None = None,
    tool: str | None = None,
    tool_kind: str | None = None,
    sequence: str | None = None,
    sequence_kind: str | None = None,
    goal: str | None = None,
    summary_mode: str | None = None,
    adaptive_mode: str | None = None,
    readiness_status: str | None = None,
    priority_focus: str | None = None,
    dominant_limitation: str | None = None,
    dominant_strength: str | None = None,
    recommendation_level: str | None = None,
    contextual_mode: str | None = None,
    diagnostic_scope: str | None = None,
    readiness_reason: str | None = None,
    suggested_next_step: str | None = None,
    main_help_scope: str | None = None,
    strategic_mode: str | None = None,
    recommended_focus: str | None = None,
    recommended_action: str | None = None,
    next_step_type: str | None = None,
    readiness_path: str | None = None,
    limitation_severity: str | None = None,
    recommendation_style: str | None = None,
    recommendation_priority: str | None = None,
    recommendation_basis: str | None = None,
    decision_focus: str | None = None,
    actionability_level: str | None = None,
    advice_scope: str | None = None,
    situational_profile: str | None = None,
    advice_frame: str | None = None,
    recommended_order: tuple[str, ...] | None = None,
    blocker_type: str | None = None,
    opportunity_focus: str | None = None,
    recovery_strategy: str | None = None,
    exploitation_path: str | None = None,
    moment_profile: str | None = None,
    next_move_chain: tuple[str, ...] | None = None,
    move_priority: str | None = None,
    move_count: int | None = None,
    guidance_mode: str | None = None,
    followup_trigger: str | None = None,
    sequence_confidence: str | None = None,
    momentum_type: str | None = None,
    micro_plan: tuple[str, ...] | None = None,
    plan_horizon: str | None = None,
    now_step: str | None = None,
    next_step: str | None = None,
    later_step: str | None = None,
    planning_mode: str | None = None,
    sequence_depth: int | None = None,
    plan_confidence: str | None = None,
    followup_priority: str | None = None,
    feasibility_status: str | None = None,
    feasibility_reason: str | None = None,
    feasibility_scope: str | None = None,
    contradiction_detected: bool | None = None,
    uncertainty_level: str | None = None,
    realism_level: str | None = None,
    conditions_required: tuple[str, ...] | None = None,
    feasibility_frame: str | None = None,
    viability_basis: str | None = None,
    primary_constraint: str | None = None,
    plausibility_mode: str | None = None,
    confidence_level: str | None = None,
    consistency_status: str | None = None,
    consistency_reason: str | None = None,
    evidence_sufficiency: str | None = None,
    claim_strength: str | None = None,
    ambiguity_detected: bool | None = None,
    assumption_load: str | None = None,
    required_evidence: tuple[str, ...] | None = None,
    certainty_frame: str | None = None,
    revision_trigger: str | None = None,
    contextual_tension: str | None = None,
    recent_context_conflict: bool | None = None,
    judgment_mode: str | None = None,
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
    route_trace: tuple[str, ...] | None = None,
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
    used_model: bool | None = None,
    used_memory_override: bool | None = None,
) -> TurnMetadata:
    response_mode = _resolve_response_mode(route_action, behavior_plan)
    resolved_used_model = response_mode == RESPONSE_MODE_MODEL if used_model is None else used_model

    if used_memory_override is not None:
        used_memory = used_memory_override
    elif route_action in {ROUTE_CAPABILITIES, ROUTE_INTERNAL_TOOLS, ROUTE_OPERATIONS}:
        used_memory = False
    elif route_action in {ROUTE_MAINTENANCE, ROUTE_SYSTEM_STATE}:
        used_memory = bool(memory)
    elif route_action in MEMORY_ROUTES:
        used_memory = True
    elif response_mode == RESPONSE_MODE_MODEL:
        used_memory = bool(memory)
    else:
        used_memory = False

    resolved_fallback_used = bool(fallback_used) if fallback_used is not None else False
    resolved_task_type = task_type or _resolve_default_task_type(
        route_action=route_action,
        response_mode=response_mode,
        used_model=resolved_used_model,
        fallback_used=fallback_used,
    )
    resolved_routing_decision = routing_decision or _resolve_default_routing_decision(
        route_action=route_action,
        response_mode=response_mode,
        used_model=resolved_used_model,
        fallback_used=fallback_used,
    )
    resolved_composition_mode = composition_mode or _resolve_default_composition_mode(
        route_action=route_action,
        response_mode=response_mode,
        used_model=resolved_used_model,
        fallback_used=fallback_used,
    )
    resolved_no_model_reason = no_model_reason
    if not resolved_used_model and resolved_no_model_reason is None:
        resolved_no_model_reason = _resolve_default_no_model_reason(route_action)
    resolved_provider_attempts = _resolve_default_provider_attempts(
        provider_attempts=provider_attempts,
        response_mode=response_mode,
    )
    resolved_critic_requested = _resolve_default_critic_flag(critic_requested)
    resolved_critic_used = _resolve_default_critic_flag(critic_used)

    resolved_route_trace = route_trace or _build_route_trace(
        route_action=route_action,
        capability=capability,
        action=action,
        tool=tool,
        routing_decision=resolved_routing_decision,
        gateway_mode=gateway_mode,
    )

    return TurnMetadata(
        intent=intent,
        route=route_action,
        response_mode=response_mode,
        used_memory=used_memory,
        used_model=resolved_used_model,
        capability=capability,
        action=action,
        tool=tool,
        tool_kind=tool_kind,
        sequence=sequence,
        sequence_kind=sequence_kind,
        goal=goal,
        summary_mode=summary_mode,
        adaptive_mode=adaptive_mode,
        readiness_status=readiness_status,
        priority_focus=priority_focus,
        dominant_limitation=dominant_limitation,
        dominant_strength=dominant_strength,
        recommendation_level=recommendation_level,
        contextual_mode=contextual_mode,
        diagnostic_scope=diagnostic_scope,
        readiness_reason=readiness_reason,
        suggested_next_step=suggested_next_step,
        main_help_scope=main_help_scope,
        strategic_mode=strategic_mode,
        recommended_focus=recommended_focus,
        recommended_action=recommended_action,
        next_step_type=next_step_type,
        readiness_path=readiness_path,
        limitation_severity=limitation_severity,
        recommendation_style=recommendation_style,
        recommendation_priority=recommendation_priority,
        recommendation_basis=recommendation_basis,
        decision_focus=decision_focus,
        actionability_level=actionability_level,
        advice_scope=advice_scope,
        situational_profile=situational_profile,
        advice_frame=advice_frame,
        recommended_order=recommended_order,
        blocker_type=blocker_type,
        opportunity_focus=opportunity_focus,
        recovery_strategy=recovery_strategy,
        exploitation_path=exploitation_path,
        moment_profile=moment_profile,
        next_move_chain=next_move_chain,
        move_priority=move_priority,
        move_count=move_count,
        guidance_mode=guidance_mode,
        followup_trigger=followup_trigger,
        sequence_confidence=sequence_confidence,
        momentum_type=momentum_type,
        micro_plan=micro_plan,
        plan_horizon=plan_horizon,
        now_step=now_step,
        next_step=next_step,
        later_step=later_step,
        planning_mode=planning_mode,
        sequence_depth=sequence_depth,
        plan_confidence=plan_confidence,
        followup_priority=followup_priority,
        feasibility_status=feasibility_status,
        feasibility_reason=feasibility_reason,
        feasibility_scope=feasibility_scope,
        contradiction_detected=contradiction_detected,
        uncertainty_level=uncertainty_level,
        realism_level=realism_level,
        conditions_required=conditions_required,
        feasibility_frame=feasibility_frame,
        viability_basis=viability_basis,
        primary_constraint=primary_constraint,
        plausibility_mode=plausibility_mode,
        confidence_level=confidence_level,
        consistency_status=consistency_status,
        consistency_reason=consistency_reason,
        evidence_sufficiency=evidence_sufficiency,
        claim_strength=claim_strength,
        ambiguity_detected=ambiguity_detected,
        assumption_load=assumption_load,
        required_evidence=required_evidence,
        certainty_frame=certainty_frame,
        revision_trigger=revision_trigger,
        contextual_tension=contextual_tension,
        recent_context_conflict=recent_context_conflict,
        judgment_mode=judgment_mode,
        task_type=resolved_task_type,
        routing_decision=resolved_routing_decision,
        selected_provider=selected_provider,
        selected_role=selected_role,
        provider_available=provider_available,
        provider_attempts=resolved_provider_attempts,
        fallback_used=resolved_fallback_used,
        fallback_reason=fallback_reason,
        composition_mode=resolved_composition_mode,
        critic_requested=resolved_critic_requested,
        critic_used=resolved_critic_used,
        critic_provider=critic_provider,
        critic_available=critic_available,
        critic_result_status=critic_result_status,
        critic_summary=critic_summary,
        verification_outcome=verification_outcome,
        verification_mode=verification_mode,
        no_model_reason=resolved_no_model_reason,
        route_trace=resolved_route_trace,
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


def _build_metadata_from_dispatch(
    turn_plan: TurnPlan,
    memory: dict[str, Any],
    dispatch_result: DispatchResult,
) -> TurnMetadata:
    return _build_metadata(
        intent=turn_plan.intent,
        route_action=turn_plan.route_decision.action,
        behavior_plan=turn_plan.behavior_plan,
        memory=memory,
        capability=dispatch_result.resolution.capability,
        action=dispatch_result.resolution.action,
        tool=dispatch_result.resolution.tool,
        tool_kind=dispatch_result.resolution.tool_kind,
        sequence=dispatch_result.resolution.sequence,
        sequence_kind=dispatch_result.resolution.sequence_kind,
        goal=dispatch_result.resolution.goal,
        summary_mode=dispatch_result.resolution.summary_mode,
        adaptive_mode=dispatch_result.resolution.adaptive_mode,
        readiness_status=dispatch_result.resolution.readiness_status,
        priority_focus=dispatch_result.resolution.priority_focus,
        dominant_limitation=dispatch_result.resolution.dominant_limitation,
        dominant_strength=dispatch_result.resolution.dominant_strength,
        recommendation_level=dispatch_result.resolution.recommendation_level,
        contextual_mode=dispatch_result.resolution.contextual_mode,
        diagnostic_scope=dispatch_result.resolution.diagnostic_scope,
        readiness_reason=dispatch_result.resolution.readiness_reason,
        suggested_next_step=dispatch_result.resolution.suggested_next_step,
        main_help_scope=dispatch_result.resolution.main_help_scope,
        strategic_mode=dispatch_result.resolution.strategic_mode,
        recommended_focus=dispatch_result.resolution.recommended_focus,
        recommended_action=dispatch_result.resolution.recommended_action,
        next_step_type=dispatch_result.resolution.next_step_type,
        readiness_path=dispatch_result.resolution.readiness_path,
        limitation_severity=dispatch_result.resolution.limitation_severity,
        recommendation_style=dispatch_result.resolution.recommendation_style,
        recommendation_priority=dispatch_result.resolution.recommendation_priority,
        recommendation_basis=dispatch_result.resolution.recommendation_basis,
        decision_focus=dispatch_result.resolution.decision_focus,
        actionability_level=dispatch_result.resolution.actionability_level,
        advice_scope=dispatch_result.resolution.advice_scope,
        situational_profile=dispatch_result.resolution.situational_profile,
        advice_frame=dispatch_result.resolution.advice_frame,
        recommended_order=dispatch_result.resolution.recommended_order,
        blocker_type=dispatch_result.resolution.blocker_type,
        opportunity_focus=dispatch_result.resolution.opportunity_focus,
        recovery_strategy=dispatch_result.resolution.recovery_strategy,
        exploitation_path=dispatch_result.resolution.exploitation_path,
        moment_profile=dispatch_result.resolution.moment_profile,
        next_move_chain=dispatch_result.resolution.next_move_chain,
        move_priority=dispatch_result.resolution.move_priority,
        move_count=dispatch_result.resolution.move_count,
        guidance_mode=dispatch_result.resolution.guidance_mode,
        followup_trigger=dispatch_result.resolution.followup_trigger,
        sequence_confidence=dispatch_result.resolution.sequence_confidence,
        momentum_type=dispatch_result.resolution.momentum_type,
        micro_plan=dispatch_result.resolution.micro_plan,
        plan_horizon=dispatch_result.resolution.plan_horizon,
        now_step=dispatch_result.resolution.now_step,
        next_step=dispatch_result.resolution.next_step,
        later_step=dispatch_result.resolution.later_step,
        planning_mode=dispatch_result.resolution.planning_mode,
        sequence_depth=dispatch_result.resolution.sequence_depth,
        plan_confidence=dispatch_result.resolution.plan_confidence,
        followup_priority=dispatch_result.resolution.followup_priority,
        feasibility_status=dispatch_result.resolution.feasibility_status,
        feasibility_reason=dispatch_result.resolution.feasibility_reason,
        feasibility_scope=dispatch_result.resolution.feasibility_scope,
        contradiction_detected=dispatch_result.resolution.contradiction_detected,
        uncertainty_level=dispatch_result.resolution.uncertainty_level,
        realism_level=dispatch_result.resolution.realism_level,
        conditions_required=dispatch_result.resolution.conditions_required,
        feasibility_frame=dispatch_result.resolution.feasibility_frame,
        viability_basis=dispatch_result.resolution.viability_basis,
        primary_constraint=dispatch_result.resolution.primary_constraint,
        plausibility_mode=dispatch_result.resolution.plausibility_mode,
        confidence_level=dispatch_result.resolution.confidence_level,
        consistency_status=dispatch_result.resolution.consistency_status,
        consistency_reason=dispatch_result.resolution.consistency_reason,
        evidence_sufficiency=dispatch_result.resolution.evidence_sufficiency,
        claim_strength=dispatch_result.resolution.claim_strength,
        ambiguity_detected=dispatch_result.resolution.ambiguity_detected,
        assumption_load=dispatch_result.resolution.assumption_load,
        required_evidence=dispatch_result.resolution.required_evidence,
        certainty_frame=dispatch_result.resolution.certainty_frame,
        revision_trigger=dispatch_result.resolution.revision_trigger,
        contextual_tension=dispatch_result.resolution.contextual_tension,
        recent_context_conflict=dispatch_result.resolution.recent_context_conflict,
        judgment_mode=dispatch_result.resolution.judgment_mode,
        task_type=dispatch_result.execution.task_type,
        routing_decision=dispatch_result.execution.routing_decision,
        selected_provider=dispatch_result.execution.selected_provider,
        selected_role=dispatch_result.execution.selected_role,
        provider_available=dispatch_result.execution.provider_available,
        provider_attempts=dispatch_result.execution.provider_attempts,
        fallback_used=dispatch_result.execution.fallback_used,
        fallback_reason=dispatch_result.execution.fallback_reason,
        composition_mode=dispatch_result.execution.composition_mode,
        critic_requested=dispatch_result.execution.critic_requested,
        critic_used=dispatch_result.execution.critic_used,
        critic_provider=dispatch_result.execution.critic_provider,
        critic_available=dispatch_result.execution.critic_available,
        critic_result_status=dispatch_result.execution.critic_result_status,
        critic_summary=dispatch_result.execution.critic_summary,
        verification_outcome=dispatch_result.execution.verification_outcome,
        verification_mode=dispatch_result.execution.verification_mode,
        no_model_reason=dispatch_result.execution.no_model_reason,
        provider_trace=dispatch_result.execution.provider_trace,
        gateway_mode=dispatch_result.execution.gateway_mode,
        provider_result_status=dispatch_result.execution.provider_result_status,
        runtime_quality_status=dispatch_result.execution.runtime_quality_status,
        degradation_hint=dispatch_result.execution.degradation_hint,
        critic_value=dispatch_result.execution.critic_value,
        router_value=dispatch_result.execution.router_value,
        fallback_pressure=dispatch_result.execution.fallback_pressure,
        routing_neuron_applied=dispatch_result.execution.routing_neuron_applied,
        routing_neuron_id=dispatch_result.execution.routing_neuron_id,
        routing_neuron_state=dispatch_result.execution.routing_neuron_state,
        routing_neuron_type=dispatch_result.execution.routing_neuron_type,
        routing_neuron_influence=dispatch_result.execution.routing_neuron_influence,
        routing_neuron_trace=dispatch_result.execution.routing_neuron_trace,
        routing_neuron_conflict=dispatch_result.execution.routing_neuron_conflict,
        routing_neuron_fallback_reason=dispatch_result.execution.routing_neuron_fallback_reason,
        routing_neuron_decision=dispatch_result.execution.routing_neuron_decision,
        routing_neuron_alerts=dispatch_result.execution.routing_neuron_alerts,
        routing_neuron_considered=dispatch_result.execution.routing_neuron_considered,
        routing_neuron_considered_ids=dispatch_result.execution.routing_neuron_considered_ids,
        routing_neuron_selected=dispatch_result.execution.routing_neuron_selected,
        routing_neuron_barriers_checked=dispatch_result.execution.routing_neuron_barriers_checked,
        routing_neuron_barriers_blocked=dispatch_result.execution.routing_neuron_barriers_blocked,
        routing_neuron_conflict_resolution=dispatch_result.execution.routing_neuron_conflict_resolution,
        routing_neuron_outcome_label=dispatch_result.execution.routing_neuron_outcome_label,
        routing_neuron_decision_path=dispatch_result.execution.routing_neuron_decision_path,
        used_model=dispatch_result.execution.used_model,
        used_memory_override=dispatch_result.execution.used_memory_override,
    )


def _resolve_intent_for_route(classified_intent: str, route_action: str) -> str:
    if route_action == ROUTE_CAPABILITIES:
        return INTENT_CAPABILITIES_COMMAND

    if route_action == ROUTE_INTERNAL_TOOLS:
        if classified_intent in {INTENT_FEASIBILITY, INTENT_CONSISTENCY}:
            return classified_intent
        return INTENT_TOOLS_COMMAND

    if route_action == ROUTE_OPERATIONS:
        return INTENT_OPERATIONS_COMMAND

    if route_action == ROUTE_MAINTENANCE:
        return INTENT_MAINTENANCE_COMMAND

    if route_action == ROUTE_SYSTEM_STATE:
        return INTENT_SYSTEM_COMMAND

    if route_action in {ROUTE_INTERNAL_QUERY, ROUTE_INTERNAL_FORGET}:
        return INTENT_MEMORY_COMMAND

    if route_action in {ROUTE_MEMORY_LOOKUP, ROUTE_MEMORY_LOOKUP_AMBIGUOUS}:
        return INTENT_MEMORY_QUERY

    return classified_intent


def _resolve_direct_response_route(
    route_decision: RouteDecision,
    behavior_plan: BehaviorPlan,
) -> RouteDecision:
    if route_decision.action != ROUTE_MODEL:
        return route_decision

    if not behavior_plan.direct_response:
        return route_decision

    return RouteDecision(
        action=ROUTE_HEURISTIC_RESPONSE,
        capability=CAPABILITY_HEURISTIC_RESPONSE,
    )


def _build_capability_context(
    turn_plan: TurnPlan,
    conversation: list[dict[str, Any]],
    memory: dict[str, Any],
    memory_file: str,
    log_file: str,
    llama_path: str,
    model_path: str,
    aura_version: str,
) -> CapabilityContext:
    return CapabilityContext(
        user_input_raw=turn_plan.user_turn.raw,
        conversation=conversation,
        memory=memory,
        memory_file=memory_file,
        log_file=log_file,
        llama_path=llama_path,
        model_path=model_path,
        aura_version=aura_version,
        behavior_plan=turn_plan.behavior_plan,
        route_action=turn_plan.route_decision.action,
        memory_intent=turn_plan.route_decision.memory_intent,
        operations_query=turn_plan.route_decision.operations_query,
        tools_query=turn_plan.route_decision.tools_query,
        internal_command=turn_plan.route_decision.internal_command,
        maintenance_command=turn_plan.route_decision.maintenance_command,
        system_state_command=turn_plan.route_decision.system_state_command,
    )


def prepare_turn(
    user_input_raw: str,
    conversation: list[dict[str, Any]],
    memory: dict[str, Any],
) -> TurnPlan | None:
    user_turn = process_user_input(user_input_raw)
    if user_turn.is_empty:
        return None

    # 1. Decision Engine: analiza y determina la ruta óptima
    decision_analysis = analyze_decision(
        user_turn.raw,
        conversation=conversation,
        memory=memory,
    )
    
    # 2. route_turn: obtiene RouteDecision completo con contextos de ejecución
    full_route = route_turn(user_turn, conversation, memory)
    selected_route = decision_analysis.selected_route
    
    # 3. Construir RouteDecision: ruta del Engine + contextos filtrados de route_turn
    route_decision = RouteDecision(
        action=selected_route,
        capability=decision_analysis.selected_capability,
        memory_intent=(
            full_route.memory_intent
            if selected_route in ("memory_lookup", "memory_lookup_ambiguous")
            else None
        ),
        operations_query=(
            full_route.operations_query
            if selected_route == "operations"
            else None
        ),
        tools_query=(
            full_route.tools_query
            if selected_route in ("internal_tools", "capabilities")
            else None
        ),
        internal_command=(
            full_route.internal_command
            if selected_route in ("internal_query", "internal_forget")
            else None
        ),
        maintenance_command=(
            full_route.maintenance_command
            if selected_route == "maintenance"
            else None
        ),
        system_state_command=(
            full_route.system_state_command
            if selected_route == "system_state"
            else None
        ),
    )
    
    intent = _resolve_intent_for_route(
        classify_user_intent(user_turn.raw),
        route_decision.action,
    )
    behavior_plan = plan_behavior_for_input(
        user_turn.raw,
        intent=intent,
        memory=memory,
        conversation=conversation,
    )
    route_decision = _resolve_direct_response_route(route_decision, behavior_plan)

    return TurnPlan(
        user_turn=user_turn,
        intent=intent,
        route_decision=route_decision,
        behavior_plan=behavior_plan,
    )


def execute_turn(
    turn_plan: TurnPlan,
    conversation: list[dict[str, Any]],
    memory: dict[str, Any],
    memory_file: str,
    log_file: str,
    llama_path: str,
    model_path: str,
    aura_version: str,
) -> TurnResult:
    route_action = turn_plan.route_decision.action
    capability_context = _build_capability_context(
        turn_plan=turn_plan,
        conversation=conversation,
        memory=memory,
        memory_file=memory_file,
        log_file=log_file,
        llama_path=llama_path,
        model_path=model_path,
        aura_version=aura_version,
    )

    if turn_plan.route_decision.capability == CAPABILITY_EXIT:
        dispatch_result = dispatch(turn_plan.route_decision.capability, capability_context)
        metadata = _build_metadata_from_dispatch(
            turn_plan=turn_plan,
            memory=memory,
            dispatch_result=dispatch_result,
        )
        return TurnResult(
            response=dispatch_result.execution.response,
            metadata=metadata,
            should_exit=dispatch_result.execution.should_exit,
        )

    remember_basic_memory(turn_plan.user_turn.raw, memory, memory_file)

    conversation.append(
        {
            "role": "user",
            "content": turn_plan.user_turn.raw,
        }
    )

    dispatch_result = dispatch(turn_plan.route_decision.capability, capability_context)
    response = dispatch_result.execution.response
    metadata = _build_metadata_from_dispatch(
        turn_plan=turn_plan,
        memory=memory,
        dispatch_result=dispatch_result,
    )

    conversation.append(
        {
            "role": "aura",
            "content": response,
            "metadata": asdict(metadata),
        }
    )

    return TurnResult(
        response=response,
        metadata=metadata,
        should_exit=dispatch_result.execution.should_exit,
    )
