from dataclasses import dataclass

from .capabilities_registry import (
    CapabilityDefinition,
    CapabilityContext,
    CapabilityExecution,
    get_capability_definition,
)
from .internal_actions_agent import resolve_internal_action
from .internal_actions_registry import InternalActionDefinition, get_internal_action_definition
from .internal_sequences_registry import (
    InternalSequenceDefinition,
    get_internal_sequence_definition,
)
from .internal_tools_agent import (
    execute_internal_tool,
    resolve_contextual_response_signals,
)
from .internal_tools_registry import InternalToolDefinition, get_internal_tool_definition


@dataclass(frozen=True)
class DispatchResolution:
    capability: str
    capability_definition: CapabilityDefinition
    action: str | None
    action_definition: InternalActionDefinition | None
    sequence: str | None
    sequence_kind: str | None
    goal: str | None
    summary_mode: str | None
    adaptive_mode: str | None
    readiness_status: str | None
    priority_focus: str | None
    dominant_limitation: str | None
    dominant_strength: str | None
    recommendation_level: str | None
    contextual_mode: str | None
    diagnostic_scope: str | None
    readiness_reason: str | None
    suggested_next_step: str | None
    main_help_scope: str | None
    strategic_mode: str | None
    recommended_focus: str | None
    recommended_action: str | None
    next_step_type: str | None
    readiness_path: str | None
    limitation_severity: str | None
    recommendation_style: str | None
    recommendation_priority: str | None
    recommendation_basis: str | None
    decision_focus: str | None
    actionability_level: str | None
    advice_scope: str | None
    situational_profile: str | None
    advice_frame: str | None
    recommended_order: tuple[str, ...] | None
    blocker_type: str | None
    opportunity_focus: str | None
    recovery_strategy: str | None
    exploitation_path: str | None
    moment_profile: str | None
    next_move_chain: tuple[str, ...] | None
    move_priority: str | None
    move_count: int | None
    guidance_mode: str | None
    followup_trigger: str | None
    sequence_confidence: str | None
    momentum_type: str | None
    micro_plan: tuple[str, ...] | None
    plan_horizon: str | None
    now_step: str | None
    next_step: str | None
    later_step: str | None
    planning_mode: str | None
    sequence_depth: int | None
    plan_confidence: str | None
    followup_priority: str | None
    feasibility_status: str | None
    feasibility_reason: str | None
    feasibility_scope: str | None
    contradiction_detected: bool | None
    uncertainty_level: str | None
    realism_level: str | None
    conditions_required: tuple[str, ...] | None
    feasibility_frame: str | None
    viability_basis: str | None
    primary_constraint: str | None
    plausibility_mode: str | None
    confidence_level: str | None
    consistency_status: str | None
    consistency_reason: str | None
    evidence_sufficiency: str | None
    claim_strength: str | None
    ambiguity_detected: bool | None
    assumption_load: str | None
    required_evidence: tuple[str, ...] | None
    certainty_frame: str | None
    revision_trigger: str | None
    contextual_tension: str | None
    recent_context_conflict: bool | None
    judgment_mode: str | None
    sequence_definition: InternalSequenceDefinition | None
    tool: str | None
    tool_kind: str | None
    tool_definition: InternalToolDefinition | None


@dataclass(frozen=True)
class DispatchResult:
    resolution: DispatchResolution
    execution: CapabilityExecution


def _resolve_action_definition(
    capability: str,
    context: CapabilityContext,
) -> tuple[str | None, InternalActionDefinition | None]:
    action = resolve_internal_action(capability, context)
    if action is None:
        return None, None

    return action, get_internal_action_definition(action)


def _resolve_tool_definition(
    action_definition: InternalActionDefinition | None,
) -> tuple[str | None, InternalToolDefinition | None]:
    if action_definition is None:
        return None, None

    tool = action_definition.tool_name
    if tool is None:
        return None, None

    return tool, get_internal_tool_definition(tool)


def _resolve_sequence_definition(
    action_definition: InternalActionDefinition | None,
) -> tuple[str | None, InternalSequenceDefinition | None]:
    if action_definition is None:
        return None, None

    sequence = action_definition.sequence_name
    if sequence is None:
        return None, None

    return sequence, get_internal_sequence_definition(sequence)


def resolve_dispatch(
    capability: str,
    context: CapabilityContext,
) -> DispatchResolution:
    capability_definition = get_capability_definition(capability)
    action, action_definition = _resolve_action_definition(capability, context)
    sequence, sequence_definition = _resolve_sequence_definition(action_definition)
    tool, tool_definition = _resolve_tool_definition(action_definition)
    adaptive_signals = resolve_contextual_response_signals(sequence, context)

    return DispatchResolution(
        capability=capability,
        capability_definition=capability_definition,
        action=action,
        action_definition=action_definition,
        sequence=sequence,
        sequence_kind=sequence_definition.kind if sequence_definition is not None else None,
        goal=sequence_definition.goal if sequence_definition is not None else None,
        summary_mode=sequence_definition.summary_mode if sequence_definition is not None else None,
        adaptive_mode=(
            sequence_definition.adaptive_mode if sequence_definition is not None else None
        ),
        readiness_status=adaptive_signals.readiness_status,
        priority_focus=adaptive_signals.priority_focus,
        dominant_limitation=adaptive_signals.dominant_limitation,
        dominant_strength=adaptive_signals.dominant_strength,
        recommendation_level=adaptive_signals.recommendation_level,
        contextual_mode=adaptive_signals.contextual_mode,
        diagnostic_scope=adaptive_signals.diagnostic_scope,
        readiness_reason=adaptive_signals.readiness_reason,
        suggested_next_step=adaptive_signals.suggested_next_step,
        main_help_scope=adaptive_signals.main_help_scope,
        strategic_mode=adaptive_signals.strategic_mode,
        recommended_focus=adaptive_signals.recommended_focus,
        recommended_action=adaptive_signals.recommended_action,
        next_step_type=adaptive_signals.next_step_type,
        readiness_path=adaptive_signals.readiness_path,
        limitation_severity=adaptive_signals.limitation_severity,
        recommendation_style=adaptive_signals.recommendation_style,
        recommendation_priority=adaptive_signals.recommendation_priority,
        recommendation_basis=adaptive_signals.recommendation_basis,
        decision_focus=adaptive_signals.decision_focus,
        actionability_level=adaptive_signals.actionability_level,
        advice_scope=adaptive_signals.advice_scope,
        situational_profile=adaptive_signals.situational_profile,
        advice_frame=adaptive_signals.advice_frame,
        recommended_order=adaptive_signals.recommended_order,
        blocker_type=adaptive_signals.blocker_type,
        opportunity_focus=adaptive_signals.opportunity_focus,
        recovery_strategy=adaptive_signals.recovery_strategy,
        exploitation_path=adaptive_signals.exploitation_path,
        moment_profile=adaptive_signals.moment_profile,
        next_move_chain=adaptive_signals.next_move_chain,
        move_priority=adaptive_signals.move_priority,
        move_count=adaptive_signals.move_count,
        guidance_mode=adaptive_signals.guidance_mode,
        followup_trigger=adaptive_signals.followup_trigger,
        sequence_confidence=adaptive_signals.sequence_confidence,
        momentum_type=adaptive_signals.momentum_type,
        micro_plan=adaptive_signals.micro_plan,
        plan_horizon=adaptive_signals.plan_horizon,
        now_step=adaptive_signals.now_step,
        next_step=adaptive_signals.next_step,
        later_step=adaptive_signals.later_step,
        planning_mode=adaptive_signals.planning_mode,
        sequence_depth=adaptive_signals.sequence_depth,
        plan_confidence=adaptive_signals.plan_confidence,
        followup_priority=adaptive_signals.followup_priority,
        feasibility_status=adaptive_signals.feasibility_status,
        feasibility_reason=adaptive_signals.feasibility_reason,
        feasibility_scope=adaptive_signals.feasibility_scope,
        contradiction_detected=adaptive_signals.contradiction_detected,
        uncertainty_level=adaptive_signals.uncertainty_level,
        realism_level=adaptive_signals.realism_level,
        conditions_required=adaptive_signals.conditions_required,
        feasibility_frame=adaptive_signals.feasibility_frame,
        viability_basis=adaptive_signals.viability_basis,
        primary_constraint=adaptive_signals.primary_constraint,
        plausibility_mode=adaptive_signals.plausibility_mode,
        confidence_level=adaptive_signals.confidence_level,
        consistency_status=adaptive_signals.consistency_status,
        consistency_reason=adaptive_signals.consistency_reason,
        evidence_sufficiency=adaptive_signals.evidence_sufficiency,
        claim_strength=adaptive_signals.claim_strength,
        ambiguity_detected=adaptive_signals.ambiguity_detected,
        assumption_load=adaptive_signals.assumption_load,
        required_evidence=adaptive_signals.required_evidence,
        certainty_frame=adaptive_signals.certainty_frame,
        revision_trigger=adaptive_signals.revision_trigger,
        contextual_tension=adaptive_signals.contextual_tension,
        recent_context_conflict=adaptive_signals.recent_context_conflict,
        judgment_mode=adaptive_signals.judgment_mode,
        sequence_definition=sequence_definition,
        tool=tool,
        tool_kind=tool_definition.kind if tool_definition is not None else None,
        tool_definition=tool_definition,
    )


def dispatch(capability: str, context: CapabilityContext) -> DispatchResult:
    resolution = resolve_dispatch(capability, context)

    if resolution.action_definition is None:
        execution = resolution.capability_definition.handler(context)
    elif resolution.tool_definition is not None:
        execution = execute_internal_tool(
            capability=capability,
            context=context,
            action_definition=resolution.action_definition,
            tool_definition=resolution.tool_definition,
        )
    else:
        execution = resolution.action_definition.handler(context)

    return DispatchResult(
        resolution=resolution,
        execution=execution,
    )
