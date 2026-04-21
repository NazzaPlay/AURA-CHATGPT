from __future__ import annotations

from dataclasses import dataclass

from .feasibility_agent import (
    FEASIBILITY_STATUS_CONTRADICTORY,
    FEASIBILITY_STATUS_NOT_FEASIBLE,
    FEASIBILITY_STATUS_POSSIBLE,
    FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS,
    FEASIBILITY_STATUS_UNCERTAIN,
    FeasibilityEvaluation,
    evaluate_feasibility,
)
from .text_matching import (
    build_normalized_command_family,
    matches_normalized_command_family,
    normalize_internal_text,
)


CONSISTENCY_STATUS_CONSISTENT = "consistent"
CONSISTENCY_STATUS_CONDITIONAL = "conditional"
CONSISTENCY_STATUS_UNCERTAIN = "uncertain"
CONSISTENCY_STATUS_TENSION_DETECTED = "tension_detected"
CONSISTENCY_STATUS_CONFLICTED = "conflicted"

CONFIDENCE_LEVEL_HIGH = "high"
CONFIDENCE_LEVEL_MEDIUM = "medium"
CONFIDENCE_LEVEL_LOW = "low"

EVIDENCE_SUFFICIENCY_HIGH = "high"
EVIDENCE_SUFFICIENCY_MEDIUM = "medium"
EVIDENCE_SUFFICIENCY_LOW = "low"

CLAIM_STRENGTH_FIRM = "firm"
CLAIM_STRENGTH_CONDITIONAL = "conditional"
CLAIM_STRENGTH_TENTATIVE = "tentative"

ASSUMPTION_LOAD_LOW = "low"
ASSUMPTION_LOAD_MEDIUM = "medium"
ASSUMPTION_LOAD_HIGH = "high"

CONSISTENCY_FRAME_CONFIDENCE = "confidence_check"
CONSISTENCY_FRAME_ASSERTION = "assertion_check"
CONSISTENCY_FRAME_DEPENDENCY = "dependency_check"
CONSISTENCY_FRAME_EVIDENCE = "evidence_check"
CONSISTENCY_FRAME_CONTEXT_TENSION = "context_tension_check"

CONSISTENCY_ASSERTION_QUERY_COMMANDS = build_normalized_command_family(
    {
        "eso lo afirmarias",
        "eso lo afirmarias asi nomas",
    }
)
CONSISTENCY_CONFIDENCE_QUERY_COMMANDS = build_normalized_command_family(
    {
        "que tan seguro estas",
        "esto es una hipotesis o algo firme",
        "que tan confiable es esa idea",
        "que tan firme es ese juicio",
        "cuanta certeza tienes",
        "este juicio es firme o condicional",
    }
)
CONSISTENCY_DEPENDENCY_QUERY_COMMANDS = build_normalized_command_family(
    {
        "esto depende de algo",
        "que necesitarias para estar mas seguro",
        "que te falta para afirmarlo mejor",
    }
)
CONSISTENCY_EVIDENCE_QUERY_COMMANDS = build_normalized_command_family(
    {
        "hay suficiente base",
        "esto esta claro o todavia es dudoso",
    }
)
CONSISTENCY_TENSION_QUERY_COMMANDS = build_normalized_command_family(
    {
        "esto entra en conflicto con algo que dije antes",
        "ves tension con lo anterior",
    }
)


@dataclass(frozen=True)
class ConsistencyQuery:
    frame: str = CONSISTENCY_FRAME_CONFIDENCE


@dataclass(frozen=True)
class ConsistencyEvaluation:
    confidence_level: str
    consistency_status: str
    consistency_reason: str
    evidence_sufficiency: str
    claim_strength: str
    ambiguity_detected: bool
    assumption_load: str
    required_evidence: tuple[str, ...]
    certainty_frame: str
    revision_trigger: str | None
    contextual_tension: str | None
    recent_context_conflict: bool
    judgment_mode: str
    feasibility: FeasibilityEvaluation
    subject: str


def _dedupe_items(items: list[str]) -> tuple[str, ...]:
    unique: list[str] = []
    seen: set[str] = set()

    for item in items:
        cleaned = " ".join(str(item).split()).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)

    return tuple(unique)


def _contains_any(text: str, options: tuple[str, ...] | list[str] | set[str]) -> bool:
    return any(option in text for option in options)


def analyze_consistency_query(user_input: str) -> ConsistencyQuery | None:
    if matches_normalized_command_family(user_input, CONSISTENCY_TENSION_QUERY_COMMANDS):
        return ConsistencyQuery(frame=CONSISTENCY_FRAME_CONTEXT_TENSION)

    if matches_normalized_command_family(user_input, CONSISTENCY_ASSERTION_QUERY_COMMANDS):
        return ConsistencyQuery(frame=CONSISTENCY_FRAME_ASSERTION)

    if matches_normalized_command_family(user_input, CONSISTENCY_DEPENDENCY_QUERY_COMMANDS):
        return ConsistencyQuery(frame=CONSISTENCY_FRAME_DEPENDENCY)

    if matches_normalized_command_family(user_input, CONSISTENCY_EVIDENCE_QUERY_COMMANDS):
        return ConsistencyQuery(frame=CONSISTENCY_FRAME_EVIDENCE)

    if matches_normalized_command_family(user_input, CONSISTENCY_CONFIDENCE_QUERY_COMMANDS):
        return ConsistencyQuery(frame=CONSISTENCY_FRAME_CONFIDENCE)

    return None


def _extract_latest_assessment_metadata(
    conversation: list[dict[str, object]] | None,
) -> dict[str, object] | None:
    conversation = conversation or []

    for message in reversed(conversation):
        if message.get("role") != "aura":
            continue

        metadata = message.get("metadata")
        if not isinstance(metadata, dict):
            continue

        if metadata.get("feasibility_status") or metadata.get("consistency_status"):
            return metadata

    return None


def _extract_latest_assessment_subject(
    user_input: str,
    conversation: list[dict[str, object]] | None,
) -> str:
    normalized_input = normalize_internal_text(user_input)
    conversation = conversation or []

    for message in reversed(conversation):
        if message.get("role") != "user":
            continue

        content = str(message.get("content", "")).strip()
        if not content:
            continue

        normalized_content = normalize_internal_text(content)
        if normalized_content == normalized_input:
            continue

        if analyze_consistency_query(content):
            continue

        return content

    return user_input.strip()


def _build_feasibility_from_metadata(
    metadata: dict[str, object],
    subject: str,
) -> FeasibilityEvaluation | None:
    status = metadata.get("feasibility_status")
    reason = metadata.get("feasibility_reason")

    if not status or not reason:
        return None

    raw_conditions = metadata.get("conditions_required")
    if isinstance(raw_conditions, tuple):
        conditions = tuple(str(item) for item in raw_conditions if str(item).strip())
    elif isinstance(raw_conditions, list):
        conditions = tuple(str(item) for item in raw_conditions if str(item).strip())
    else:
        conditions = ()

    return FeasibilityEvaluation(
        status=str(status),
        reason=str(reason),
        scope=str(metadata.get("feasibility_scope") or "general"),
        contradiction_detected=bool(metadata.get("contradiction_detected")),
        uncertainty_level=str(metadata.get("uncertainty_level") or "medium"),
        realism_level=str(metadata.get("realism_level") or "medium"),
        conditions_required=conditions,
        frame=str(metadata.get("feasibility_frame") or "feasibility_check"),
        viability_basis=str(metadata.get("viability_basis") or "assessment_trace"),
        primary_constraint=(
            str(metadata["primary_constraint"])
            if metadata.get("primary_constraint") is not None
            else None
        ),
        plausibility_mode=str(metadata.get("plausibility_mode") or "assessment_trace"),
        subject=subject,
    )


def _detect_recent_context_tension(
    conversation: list[dict[str, object]] | None,
    user_input: str,
) -> tuple[bool, str | None, str | None]:
    conversation = conversation or []
    normalized_input = normalize_internal_text(user_input)
    recent_user_messages: list[str] = []

    for message in conversation:
        if message.get("role") != "user":
            continue

        content = str(message.get("content", "")).strip()
        if not content:
            continue

        if normalize_internal_text(content) == normalized_input:
            continue

        recent_user_messages.append(content)

    recent_user_messages = recent_user_messages[-4:]
    if not recent_user_messages:
        return False, None, None

    normalized_recent = [normalize_internal_text(message) for message in recent_user_messages]

    offline_markers = (
        "offline",
        "todo offline",
        "local",
        "sin internet",
        "cero recursos",
        "sin hardware potente",
    )
    live_markers = (
        "siempre lo ultimo que paso en internet",
        "siempre sepa lo ultimo de internet",
        "siempre lo ultimo",
        "lo ultimo de internet",
        "lo ultimo que paso en internet",
        "servidor enorme",
        "7 modelos grandes",
        "varios modelos grandes",
        "calidad de servidor grande",
    )
    low_resource_markers = (
        "cero recursos",
        "sin hardware potente",
        "gratis",
    )
    high_resource_markers = (
        "servidor enorme",
        "calidad de servidor grande",
        "7 modelos grandes",
        "varios modelos grandes",
        "instantaneo",
    )

    offline_indexes = [
        index for index, message in enumerate(normalized_recent) if _contains_any(message, offline_markers)
    ]
    live_indexes = [
        index for index, message in enumerate(normalized_recent) if _contains_any(message, live_markers)
    ]
    if offline_indexes and live_indexes and any(
        offline_index != live_index
        for offline_index in offline_indexes
        for live_index in live_indexes
    ):
        return (
            True,
            "en lo reciente mezclaste restricciones offline o de recursos bajos con exigencias de conexión o cómputo alto",
            "recent_requirement_conflict",
        )

    low_resource_indexes = [
        index
        for index, message in enumerate(normalized_recent)
        if _contains_any(message, low_resource_markers)
    ]
    high_resource_indexes = [
        index
        for index, message in enumerate(normalized_recent)
        if _contains_any(message, high_resource_markers)
    ]
    if low_resource_indexes and high_resource_indexes and any(
        low_index != high_index
        for low_index in low_resource_indexes
        for high_index in high_resource_indexes
    ):
        return (
            True,
            "en lo reciente mezclaste un presupuesto mínimo de recursos con una ambición de cómputo mucho más alta",
            "recent_resource_conflict",
        )

    return False, None, None


def _subject_matches_tension(subject: str, revision_trigger: str | None) -> bool:
    normalized_subject = normalize_internal_text(subject)
    if not normalized_subject:
        return False

    requirement_markers = (
        "offline",
        "local",
        "sin internet",
        "internet",
        "al dia",
        "ultimo de internet",
        "ultimo que paso en internet",
    )
    resource_markers = (
        "cero recursos",
        "sin hardware potente",
        "servidor enorme",
        "calidad de servidor grande",
        "7 modelos",
        "modelos grandes",
        "multimodelo",
        "verificador",
        "providers",
    )

    if revision_trigger == "recent_requirement_conflict":
        return _contains_any(normalized_subject, requirement_markers)

    if revision_trigger == "recent_resource_conflict":
        return _contains_any(normalized_subject, resource_markers)

    return False


def _should_apply_recent_context_tension(
    frame: str,
    subject: str,
    revision_trigger: str | None,
) -> bool:
    if not revision_trigger:
        return False

    if frame == CONSISTENCY_FRAME_CONTEXT_TENSION:
        return True

    return _subject_matches_tension(subject, revision_trigger)


def _derive_required_evidence(
    feasibility: FeasibilityEvaluation,
) -> tuple[str, ...]:
    if feasibility.primary_constraint == "missing_hardware_data":
        return (
            "RAM o VRAM disponibles",
            "tamaño real y cantidad de modelos",
        )

    if feasibility.primary_constraint in {"missing_context", "insufficient_detail"}:
        return (
            "el alcance concreto de la idea",
            "el límite principal que quieres sostener",
        )

    if feasibility.primary_constraint == "architecture_maturity":
        return (
            "cómo aislar providers o verificadores",
            "qué costo y latencia aceptarías",
        )

    if feasibility.primary_constraint == "competing_requirements":
        return ("qué restricción estás dispuesta a ceder",)

    if feasibility.status == FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS:
        return feasibility.conditions_required[:2]

    if feasibility.status == FEASIBILITY_STATUS_UNCERTAIN:
        return feasibility.conditions_required[:2]

    return ()


def _resolve_consistency_from_feasibility(
    feasibility: FeasibilityEvaluation,
    recent_context_conflict: bool,
    contextual_tension: str | None,
) -> tuple[str, str, str, str, bool, str, tuple[str, ...], str | None]:
    required_evidence = _derive_required_evidence(feasibility)

    if recent_context_conflict:
        return (
            CONFIDENCE_LEVEL_HIGH,
            CONSISTENCY_STATUS_TENSION_DETECTED,
            contextual_tension or "veo una tensión útil con el contexto reciente",
            EVIDENCE_SUFFICIENCY_HIGH,
            CLAIM_STRENGTH_FIRM,
            False,
            ASSUMPTION_LOAD_LOW,
            required_evidence,
            "revisar premisas recientes",
        )

    if feasibility.status == FEASIBILITY_STATUS_CONTRADICTORY:
        return (
            CONFIDENCE_LEVEL_HIGH,
            CONSISTENCY_STATUS_CONFLICTED,
            "veo un choque directo entre requisitos, no una duda menor",
            EVIDENCE_SUFFICIENCY_HIGH,
            CLAIM_STRENGTH_FIRM,
            False,
            ASSUMPTION_LOAD_LOW,
            required_evidence,
            "resolver el conflicto de requisitos",
        )

    if feasibility.status == FEASIBILITY_STATUS_NOT_FEASIBLE:
        return (
            CONFIDENCE_LEVEL_HIGH,
            CONSISTENCY_STATUS_CONSISTENT,
            "el límite principal es concreto y no depende de una interpretación fina",
            EVIDENCE_SUFFICIENCY_HIGH,
            CLAIM_STRENGTH_FIRM,
            False,
            ASSUMPTION_LOAD_LOW,
            required_evidence,
            "reducir exigencia o subir recursos",
        )

    if feasibility.status == FEASIBILITY_STATUS_POSSIBLE_WITH_CONDITIONS:
        return (
            CONFIDENCE_LEVEL_MEDIUM,
            CONSISTENCY_STATUS_CONDITIONAL,
            "el juicio puede sostenerse, pero depende de condiciones claras",
            EVIDENCE_SUFFICIENCY_MEDIUM,
            CLAIM_STRENGTH_CONDITIONAL,
            False,
            ASSUMPTION_LOAD_MEDIUM,
            required_evidence,
            "verificar condiciones de arquitectura o costo",
        )

    if feasibility.status == FEASIBILITY_STATUS_POSSIBLE:
        return (
            CONFIDENCE_LEVEL_MEDIUM,
            CONSISTENCY_STATUS_CONSISTENT,
            "no veo un choque fuerte, aunque no lo tomaría como garantía absoluta",
            EVIDENCE_SUFFICIENCY_MEDIUM,
            CLAIM_STRENGTH_CONDITIONAL,
            False,
            ASSUMPTION_LOAD_MEDIUM,
            required_evidence,
            None,
        )

    return (
        CONFIDENCE_LEVEL_LOW,
        CONSISTENCY_STATUS_UNCERTAIN,
        "falta base suficiente para afirmarlo con firmeza",
        EVIDENCE_SUFFICIENCY_LOW,
        CLAIM_STRENGTH_TENTATIVE,
        True,
        ASSUMPTION_LOAD_HIGH,
        required_evidence,
        "pedir contexto o datos más concretos",
    )


def _resolve_judgment_mode(frame: str) -> str:
    if frame == CONSISTENCY_FRAME_ASSERTION:
        return "assertion_review"
    if frame == CONSISTENCY_FRAME_DEPENDENCY:
        return "dependency_review"
    if frame == CONSISTENCY_FRAME_EVIDENCE:
        return "evidence_review"
    if frame == CONSISTENCY_FRAME_CONTEXT_TENSION:
        return "context_tension_review"
    return "confidence_review"


def evaluate_consistency(
    user_input: str,
    conversation: list[dict[str, object]] | None = None,
    feasibility_evaluation: FeasibilityEvaluation | None = None,
    preferred_frame: str | None = None,
) -> ConsistencyEvaluation:
    frame = preferred_frame or CONSISTENCY_FRAME_CONFIDENCE
    conversation = conversation or []
    subject = _extract_latest_assessment_subject(user_input, conversation)

    latest_assessment = _extract_latest_assessment_metadata(conversation)
    if feasibility_evaluation is None and latest_assessment is not None:
        feasibility_evaluation = _build_feasibility_from_metadata(
            latest_assessment,
            subject=subject,
        )

    if feasibility_evaluation is None:
        feasibility_evaluation = evaluate_feasibility(
            subject or user_input,
            conversation=conversation,
        )

    recent_context_conflict, contextual_tension, revision_trigger = _detect_recent_context_tension(
        conversation,
        user_input,
    )
    apply_recent_context_tension = _should_apply_recent_context_tension(
        frame,
        subject,
        revision_trigger,
    )
    if not apply_recent_context_tension:
        recent_context_conflict = False
        contextual_tension = None
        revision_trigger = None

    (
        confidence_level,
        consistency_status,
        consistency_reason,
        evidence_sufficiency,
        claim_strength,
        ambiguity_detected,
        assumption_load,
        required_evidence,
        inferred_revision_trigger,
    ) = _resolve_consistency_from_feasibility(
        feasibility_evaluation,
        recent_context_conflict=recent_context_conflict,
        contextual_tension=contextual_tension,
    )

    return ConsistencyEvaluation(
        confidence_level=confidence_level,
        consistency_status=consistency_status,
        consistency_reason=consistency_reason,
        evidence_sufficiency=evidence_sufficiency,
        claim_strength=claim_strength,
        ambiguity_detected=ambiguity_detected,
        assumption_load=assumption_load,
        required_evidence=_dedupe_items(list(required_evidence)),
        certainty_frame=frame,
        revision_trigger=revision_trigger or inferred_revision_trigger,
        contextual_tension=contextual_tension,
        recent_context_conflict=recent_context_conflict,
        judgment_mode=_resolve_judgment_mode(frame),
        feasibility=feasibility_evaluation,
        subject=subject,
    )


def build_consistency_response(evaluation: ConsistencyEvaluation) -> str:
    required_evidence_text = ", ".join(evaluation.required_evidence[:3])
    contextual_tension_is_distinct = (
        bool(evaluation.contextual_tension)
        and normalize_internal_text(evaluation.contextual_tension or "")
        != normalize_internal_text(evaluation.consistency_reason)
    )

    if evaluation.certainty_frame == CONSISTENCY_FRAME_CONTEXT_TENSION:
        if evaluation.recent_context_conflict:
            response = f"Sí, veo tensión con lo reciente: {evaluation.consistency_reason}."
            if required_evidence_text:
                response += f" Para resolverla, haría falta {required_evidence_text}."
            return response

        if evaluation.feasibility.contradiction_detected:
            return (
                "No veo una tensión nueva con lo anterior; el choque fuerte está dentro del planteo actual."
            )

        return f"No veo una tensión clara con lo reciente: {evaluation.consistency_reason}."

    if evaluation.certainty_frame == CONSISTENCY_FRAME_ASSERTION:
        if evaluation.claim_strength == CLAIM_STRENGTH_FIRM:
            response = f"Sí, lo afirmaría sin mucho rodeo: {evaluation.consistency_reason}."
            if contextual_tension_is_distinct:
                response += f" Además, {evaluation.contextual_tension}."
            return response

        if evaluation.claim_strength == CLAIM_STRENGTH_CONDITIONAL:
            response = f"No lo afirmaría así nomás: {evaluation.consistency_reason}."
            if required_evidence_text:
                response += f" Antes querría cerrar {required_evidence_text}."
            return response

        response = f"No, todavía no lo afirmaría así: {evaluation.consistency_reason}."
        if required_evidence_text:
            response += f" Para sostenerlo mejor, necesitaría {required_evidence_text}."
        return response

    if evaluation.certainty_frame == CONSISTENCY_FRAME_DEPENDENCY:
        if evaluation.consistency_status == CONSISTENCY_STATUS_CONDITIONAL:
            response = "Sí, depende de condiciones claras."
            if required_evidence_text:
                response += f" Para afirmarlo mejor, necesitaría {required_evidence_text}."
            return response

        if evaluation.consistency_status in {
            CONSISTENCY_STATUS_CONFLICTED,
            CONSISTENCY_STATUS_TENSION_DETECTED,
        }:
            return f"No depende de un detalle fino: {evaluation.consistency_reason}."

        if required_evidence_text:
            return f"Sí, y para afirmarlo mejor me faltaría {required_evidence_text}."

        return f"No mucho: {evaluation.consistency_reason}."

    if evaluation.certainty_frame == CONSISTENCY_FRAME_EVIDENCE:
        sufficiency_text = {
            EVIDENCE_SUFFICIENCY_HIGH: "alta",
            EVIDENCE_SUFFICIENCY_MEDIUM: "intermedia",
            EVIDENCE_SUFFICIENCY_LOW: "baja",
        }.get(evaluation.evidence_sufficiency, "intermedia")
        response = f"Base actual {sufficiency_text}: {evaluation.consistency_reason}."
        if required_evidence_text and evaluation.evidence_sufficiency != EVIDENCE_SUFFICIENCY_HIGH:
            response += f" Para subirla, necesitaría {required_evidence_text}."
        return response

    if evaluation.claim_strength == CLAIM_STRENGTH_FIRM:
        response = f"Estoy bastante segura de ese juicio: {evaluation.consistency_reason}."
        if contextual_tension_is_distinct:
            response += f" Además, {evaluation.contextual_tension}."
        return response

    if evaluation.claim_strength == CLAIM_STRENGTH_CONDITIONAL:
        response = f"Mi confianza acá es media: {evaluation.consistency_reason}."
        if required_evidence_text:
            response += f" Depende sobre todo de {required_evidence_text}."
        return response

    response = f"Mi confianza acá es baja: {evaluation.consistency_reason}."
    if required_evidence_text:
        response += f" Para estar más seguro, necesitaría {required_evidence_text}."
    return response
