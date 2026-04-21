from dataclasses import dataclass

# Las secuencias siguen describiendo flujos reutilizables del núcleo.
# La recomendación situacional, el criterio de momento, el micro plan,
# la evaluación de viabilidad y la calibración de consistencia de
# V0.30/V0.34 se resuelven encima de
# esta capa; no reemplazan sequence, goal, contextual_mode,
# recommendation_style ni la metadata base del turno.

SEQUENCE_INTERNAL_DIAGNOSTIC = "internal_diagnostic_sequence"
SEQUENCE_GENERAL_DIAGNOSTIC = "general_diagnostic_sequence"
SEQUENCE_FULL_DIAGNOSTIC = "full_diagnostic_sequence"
SEQUENCE_SITUATIONAL_STATUS = "situational_status_sequence"
SEQUENCE_QUICK_CHECK = "quick_check_sequence"
SEQUENCE_GENERAL_CHECK = "general_check_sequence"
SEQUENCE_SYSTEM_CHECK = "system_check_sequence"
SEQUENCE_PRIORITY_NOW = "priority_now_sequence"
SEQUENCE_DOMINANT_LIMITATION = "dominant_limitation_sequence"
SEQUENCE_DOMINANT_STRENGTH = "dominant_strength_sequence"
SEQUENCE_WORK_READINESS = "work_readiness_sequence"
SEQUENCE_READINESS_GAP = "readiness_gap_sequence"
SEQUENCE_LIMITATIONS_OVERVIEW = "limitations_overview_sequence"
SEQUENCE_CONTEXTUAL_HELP = "contextual_help_sequence"
SEQUENCE_STRATEGIC_GUIDANCE = "strategic_guidance_sequence"
SEQUENCE_FEASIBILITY_EVALUATION = "feasibility_evaluation_sequence"
SEQUENCE_CONSISTENCY_EVALUATION = "consistency_evaluation_sequence"
SEQUENCE_MEMORY_STATE_REVIEW = "memory_state_review_sequence"
SEQUENCE_PRACTICAL_REVIEW = "practical_review_sequence"
SEQUENCE_OPERATIONAL_REVIEW = "operational_review_sequence"
SEQUENCE_INTERNAL_REVIEW = "internal_review_sequence"
SEQUENCE_COMPLETE_REVIEW = "complete_review_sequence"

INTERNAL_SEQUENCE_ORDER = (
    SEQUENCE_INTERNAL_DIAGNOSTIC,
    SEQUENCE_GENERAL_DIAGNOSTIC,
    SEQUENCE_FULL_DIAGNOSTIC,
    SEQUENCE_SITUATIONAL_STATUS,
    SEQUENCE_QUICK_CHECK,
    SEQUENCE_GENERAL_CHECK,
    SEQUENCE_SYSTEM_CHECK,
    SEQUENCE_PRIORITY_NOW,
    SEQUENCE_DOMINANT_LIMITATION,
    SEQUENCE_DOMINANT_STRENGTH,
    SEQUENCE_WORK_READINESS,
    SEQUENCE_READINESS_GAP,
    SEQUENCE_LIMITATIONS_OVERVIEW,
    SEQUENCE_CONTEXTUAL_HELP,
    SEQUENCE_STRATEGIC_GUIDANCE,
    SEQUENCE_FEASIBILITY_EVALUATION,
    SEQUENCE_CONSISTENCY_EVALUATION,
    SEQUENCE_MEMORY_STATE_REVIEW,
    SEQUENCE_PRACTICAL_REVIEW,
    SEQUENCE_OPERATIONAL_REVIEW,
    SEQUENCE_INTERNAL_REVIEW,
    SEQUENCE_COMPLETE_REVIEW,
)


@dataclass(frozen=True)
class InternalSequenceDefinition:
    name: str
    label: str
    category: str
    kind: str
    goal: str
    summary_mode: str
    adaptive_mode: str
    contextual_mode: str
    description: str
    steps: tuple[str, ...]


INTERNAL_SEQUENCES_REGISTRY = {
    SEQUENCE_INTERNAL_DIAGNOSTIC: InternalSequenceDefinition(
        name=SEQUENCE_INTERNAL_DIAGNOSTIC,
        label="diagnóstico interno",
        category="system",
        kind="diagnostic",
        goal="snapshot",
        summary_mode="compact",
        adaptive_mode="status_adaptive",
        contextual_mode="diagnostic",
        description="Secuencia corta para revisar el estado base del núcleo.",
        steps=("core_status", "memory_brief", "overall_health"),
    ),
    SEQUENCE_GENERAL_DIAGNOSTIC: InternalSequenceDefinition(
        name=SEQUENCE_GENERAL_DIAGNOSTIC,
        label="diagnóstico general",
        category="system",
        kind="diagnostic",
        goal="prioritized_diagnostic",
        summary_mode="prioritized",
        adaptive_mode="priority_adaptive",
        contextual_mode="diagnostic",
        description="Secuencia para revisar estado base, memoria, limitaciones y foco actual.",
        steps=("core_status", "memory_brief", "limitations", "next_step"),
    ),
    SEQUENCE_FULL_DIAGNOSTIC: InternalSequenceDefinition(
        name=SEQUENCE_FULL_DIAGNOSTIC,
        label="diagnóstico completo",
        category="system",
        kind="diagnostic",
        goal="deep_diagnostic",
        summary_mode="detailed",
        adaptive_mode="priority_adaptive",
        contextual_mode="diagnostic",
        description="Secuencia ampliada para revisar estado base, rutas clave, memoria y foco sugerido.",
        steps=("core_status", "key_paths", "memory_brief", "limitations", "next_step"),
    ),
    SEQUENCE_SITUATIONAL_STATUS: InternalSequenceDefinition(
        name=SEQUENCE_SITUATIONAL_STATUS,
        label="estado actual",
        category="system",
        kind="status",
        goal="situational_summary",
        summary_mode="brief",
        adaptive_mode="status_adaptive",
        contextual_mode="readiness",
        description="Secuencia compacta para resumir cómo está AURA ahora mismo.",
        steps=("overall_health", "memory_brief", "limitations"),
    ),
    SEQUENCE_QUICK_CHECK: InternalSequenceDefinition(
        name=SEQUENCE_QUICK_CHECK,
        label="chequeo rápido",
        category="system",
        kind="check",
        goal="quick_check",
        summary_mode="brief",
        adaptive_mode="priority_adaptive",
        contextual_mode="diagnostic",
        description="Secuencia breve tipo checklist del núcleo.",
        steps=("overall_health", "availability", "memory_brief", "memory_review"),
    ),
    SEQUENCE_GENERAL_CHECK: InternalSequenceDefinition(
        name=SEQUENCE_GENERAL_CHECK,
        label="chequeo general",
        category="system",
        kind="check",
        goal="general_check",
        summary_mode="prioritized",
        adaptive_mode="priority_adaptive",
        contextual_mode="diagnostic",
        description="Secuencia para revisar estado, disponibilidad, memoria y principal bloqueo actual.",
        steps=("overall_health", "availability", "memory_brief", "limitations", "next_step"),
    ),
    SEQUENCE_SYSTEM_CHECK: InternalSequenceDefinition(
        name=SEQUENCE_SYSTEM_CHECK,
        label="chequeo del sistema",
        category="system",
        kind="check",
        goal="system_check",
        summary_mode="prioritized",
        adaptive_mode="priority_adaptive",
        contextual_mode="diagnostic",
        description="Secuencia para revisar disponibilidad, memoria y limitaciones actuales.",
        steps=("core_status", "availability", "memory_brief", "limitations"),
    ),
    SEQUENCE_PRIORITY_NOW: InternalSequenceDefinition(
        name=SEQUENCE_PRIORITY_NOW,
        label="prioridad actual",
        category="system",
        kind="status",
        goal="priority_now",
        summary_mode="adaptive",
        adaptive_mode="priority_adaptive",
        contextual_mode="diagnostic",
        description="Secuencia para resaltar lo más importante del núcleo según el contexto actual.",
        steps=("overall_health", "priority_focus", "limitations", "next_step"),
    ),
    SEQUENCE_DOMINANT_LIMITATION: InternalSequenceDefinition(
        name=SEQUENCE_DOMINANT_LIMITATION,
        label="limitación principal",
        category="system",
        kind="status",
        goal="dominant_limitation",
        summary_mode="adaptive",
        adaptive_mode="limitations_adaptive",
        contextual_mode="limitation_focus",
        description="Secuencia para resaltar la limitación principal y el siguiente foco útil.",
        steps=("limitations", "overall_health", "next_step"),
    ),
    SEQUENCE_DOMINANT_STRENGTH: InternalSequenceDefinition(
        name=SEQUENCE_DOMINANT_STRENGTH,
        label="fortaleza principal",
        category="system",
        kind="status",
        goal="dominant_strength",
        summary_mode="adaptive",
        adaptive_mode="strength_adaptive",
        contextual_mode="strength_focus",
        description="Secuencia para resaltar la fortaleza más útil del núcleo ahora mismo.",
        steps=("overall_health", "strengths", "next_step"),
    ),
    SEQUENCE_WORK_READINESS: InternalSequenceDefinition(
        name=SEQUENCE_WORK_READINESS,
        label="revisión de preparación",
        category="system",
        kind="review",
        goal="readiness_evaluation",
        summary_mode="readiness",
        adaptive_mode="readiness_adaptive",
        contextual_mode="readiness",
        description="Secuencia para evaluar si AURA está lista para trabajar dentro del núcleo.",
        steps=("readiness", "core_status", "memory_brief", "limitations"),
    ),
    SEQUENCE_READINESS_GAP: InternalSequenceDefinition(
        name=SEQUENCE_READINESS_GAP,
        label="brecha de preparación",
        category="system",
        kind="review",
        goal="readiness_gap",
        summary_mode="readiness",
        adaptive_mode="readiness_adaptive",
        contextual_mode="readiness",
        description="Secuencia para indicar qué falta o qué limita a AURA para trabajar.",
        steps=("readiness", "limitations", "next_step"),
    ),
    SEQUENCE_LIMITATIONS_OVERVIEW: InternalSequenceDefinition(
        name=SEQUENCE_LIMITATIONS_OVERVIEW,
        label="limitaciones actuales",
        category="system",
        kind="status",
        goal="limitations_overview",
        summary_mode="limits",
        adaptive_mode="limitations_adaptive",
        contextual_mode="limitation_focus",
        description="Secuencia para explicar las limitaciones actuales y su impacto principal.",
        steps=("limitations", "availability", "next_step"),
    ),
    SEQUENCE_CONTEXTUAL_HELP: InternalSequenceDefinition(
        name=SEQUENCE_CONTEXTUAL_HELP,
        label="ayuda contextual",
        category="help",
        kind="guidance",
        goal="contextual_help",
        summary_mode="guidance",
        adaptive_mode="guidance_adaptive",
        contextual_mode="actionable_help",
        description="Secuencia para orientar cómo puede ayudar AURA ahora según su estado actual.",
        steps=("overall_health", "availability", "memory_brief", "next_step"),
    ),
    SEQUENCE_STRATEGIC_GUIDANCE: InternalSequenceDefinition(
        name=SEQUENCE_STRATEGIC_GUIDANCE,
        label="foco recomendado",
        category="help",
        kind="strategy",
        goal="strategic_guidance",
        summary_mode="strategic",
        adaptive_mode="strategy_adaptive",
        contextual_mode="strategic_output",
        description="Secuencia para orientar el siguiente movimiento útil; la formulación visible se ajusta además con perfil situacional.",
        steps=("readiness", "priority_focus", "strengths", "limitations", "next_step"),
    ),
    SEQUENCE_FEASIBILITY_EVALUATION: InternalSequenceDefinition(
        name=SEQUENCE_FEASIBILITY_EVALUATION,
        label="evaluación de viabilidad",
        category="help",
        kind="assessment",
        goal="feasibility_evaluation",
        summary_mode="compact",
        adaptive_mode="feasibility_adaptive",
        contextual_mode="feasibility_evaluation",
        description="Secuencia para evaluar viabilidad, contradicciones, límites y condiciones útiles.",
        steps=("feasibility_scan", "constraints", "conditions", "reformulation"),
    ),
    SEQUENCE_CONSISTENCY_EVALUATION: InternalSequenceDefinition(
        name=SEQUENCE_CONSISTENCY_EVALUATION,
        label="calibración de consistencia",
        category="help",
        kind="assessment",
        goal="consistency_evaluation",
        summary_mode="compact",
        adaptive_mode="consistency_adaptive",
        contextual_mode="consistency_evaluation",
        description="Secuencia para calibrar certeza, evidencia, dependencia y tensión contextual del juicio actual.",
        steps=("judgment_trace", "evidence_check", "context_tension", "certainty_hint"),
    ),
    SEQUENCE_MEMORY_STATE_REVIEW: InternalSequenceDefinition(
        name=SEQUENCE_MEMORY_STATE_REVIEW,
        label="revisión de memoria y estado",
        category="maintenance",
        kind="review",
        goal="memory_state_review",
        summary_mode="prioritized",
        adaptive_mode="review_adaptive",
        contextual_mode="review",
        description="Secuencia para revisar memoria cargada, saneamiento y foco operativo.",
        steps=("core_status", "memory_brief", "memory_review", "next_step"),
    ),
    SEQUENCE_PRACTICAL_REVIEW: InternalSequenceDefinition(
        name=SEQUENCE_PRACTICAL_REVIEW,
        label="revisión práctica",
        category="maintenance",
        kind="review",
        goal="practical_review",
        summary_mode="actionable",
        adaptive_mode="review_adaptive",
        contextual_mode="actionable_help",
        description="Secuencia para revisar el estado actual con foco en qué puedo hacer ahora y cuál es el siguiente foco útil.",
        steps=("readiness", "priority_focus", "strengths", "next_step"),
    ),
    SEQUENCE_OPERATIONAL_REVIEW: InternalSequenceDefinition(
        name=SEQUENCE_OPERATIONAL_REVIEW,
        label="revisión operativa",
        category="maintenance",
        kind="review",
        goal="operational_review",
        summary_mode="prioritized",
        adaptive_mode="review_adaptive",
        contextual_mode="review",
        description="Secuencia para revisar estado, memoria, mantenimiento sugerido y preparación operativa.",
        steps=("readiness", "core_status", "memory_brief", "memory_review", "next_step"),
    ),
    SEQUENCE_INTERNAL_REVIEW: InternalSequenceDefinition(
        name=SEQUENCE_INTERNAL_REVIEW,
        label="revisión interna",
        category="maintenance",
        kind="review",
        goal="internal_review",
        summary_mode="compact",
        adaptive_mode="review_adaptive",
        contextual_mode="review",
        description="Secuencia para revisar memoria, estado y actividad reciente.",
        steps=("core_status", "memory_brief", "memory_review", "recent_activity", "next_step"),
    ),
    SEQUENCE_COMPLETE_REVIEW: InternalSequenceDefinition(
        name=SEQUENCE_COMPLETE_REVIEW,
        label="revisión completa",
        category="maintenance",
        kind="review",
        goal="complete_review",
        summary_mode="prioritized",
        adaptive_mode="review_adaptive",
        contextual_mode="review",
        description="Secuencia más completa para revisar estado, memoria, actividad y preparación del núcleo.",
        steps=("readiness", "core_status", "memory_brief", "memory_review", "recent_activity", "limitations", "next_step"),
    ),
}


def get_internal_sequence_definition(sequence_name: str) -> InternalSequenceDefinition:
    sequence_definition = INTERNAL_SEQUENCES_REGISTRY.get(sequence_name)
    if sequence_definition is None:
        raise KeyError(f"Secuencia interna desconocida: {sequence_name}")

    return sequence_definition


def get_internal_sequences_in_order() -> tuple[InternalSequenceDefinition, ...]:
    return tuple(
        INTERNAL_SEQUENCES_REGISTRY[sequence_name]
        for sequence_name in INTERNAL_SEQUENCE_ORDER
        if sequence_name in INTERNAL_SEQUENCES_REGISTRY
    )
