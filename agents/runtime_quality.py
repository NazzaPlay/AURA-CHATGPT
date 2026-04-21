from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from .text_matching import repair_common_mojibake


QUALITY_STATUS_OK = "ok"
QUALITY_STATUS_PLACEHOLDER = "placeholder_output"
QUALITY_STATUS_EMPTY = "empty_output"
QUALITY_STATUS_OFF_TOPIC = "off_topic_output"

SEVERE_PLACEHOLDER_PREFIXES = (
    "placeholder",
    "respuesta granite",
    "respuesta generica",
    "respuesta qwen fallback",
)

TECHNICAL_TOPIC_HINTS = (
    "api",
    "auth",
    "autorizacion",
    "backend",
    "servicio",
    "arquitectura",
    "integracion",
    "idempotencia",
    "oauth",
    "rollback",
    "rest",
    "stateless",
    "produccion",
    "production",
    "docker",
    "python",
    "traceback",
    "error",
    "jwt",
    "token",
)

PROMPT_LEAK_HINTS = (
    "respondes siempre en espanol",
    "respondes siempre en espa",
    "usas la informacion conocida del usuario",
    "responde sin saludo ni preambulo",
    "si es tecnico da una idea concreta temprano",
    "evita respuestas vacias demasiado abstractas o infladas",
    "si falta un dato dilo en una frase y da igual el paso mas util",
    "deja al menos una idea",
    "linea de foco",
    "resume en una sola linea el foco",
    "formato objetivo para esta respuesta",
    "plan interno de respuesta",
    "calibracion v0 39 3 para el primary",
    "calibracion v0 39 3 1 para el primary",
    "calibracion v0 39 4 para el primary",
    "calibracion v0 39 5 para el primary",
    "calibracion v0.39.5 para el primary",
    "calibracion v0 39 6 para el primary",
    "calibracion v0.39.6 para el primary",
    "transformacion operativa sugerida por routing neuron",
    "apoyo breve del router helper local",
    "idea breve:",
    "explicacion clara:",
    "pasos o ejemplo:",
    "que hacer:",
    "como verificar:",
)

SELF_PRESENTATION_HINTS = (
    "soy aura",
    "estoy aura",
    "asistente inteligente",
    "estoy aqui para ayudarte",
    "hola me alegra ayudarte",
    "estare encantado de ayudarte",
)

PROMPT_CONTROL_HINTS = (
    "responde",
    "respondes siempre",
    "resume",
    "resumir",
    "evita",
    "deja",
    "prioriza",
    "saludo",
    "preambulo",
    "relleno",
    "si es tecnico",
    "si falta un dato",
    "linea de foco",
    "foco util",
    "informacion conocida del usuario",
    "idea concreta temprano",
    "respuestas vacias",
    "formato objetivo",
    "plan interno",
    "calibracion",
)

CRITIC_LEAK_HINTS = (
    "verificacion breve",
    "verificada:",
    "ajuste:",
    "dudosa:",
    "chequea si la respuesta principal",
)

PLACEHOLDER_HINTS = (
    "lorem ipsum",
    "por completar",
    "completar luego",
    "pendiente de completar",
    "placeholder",
    "sin conflicto claro",
    "sin resumen breve",
)

CEREMONIAL_TECHNICAL_OPENERS = (
    "claro, te explico",
    "por supuesto",
    "vamos paso a paso",
    "aqui tienes una explicacion",
)

ACTION_ORIENTED_PROMPT_HINTS = (
    "como balancearias",
    "como equilibrarias",
    "como priorizarias",
    "como migrarias",
    "como disenar",
    "como lo dividirias",
    "que tocarias",
    "que revisarias",
)

ACTION_ORIENTED_RESPONSE_HINTS = (
    "primero",
    "despues",
    "conviene",
    "usa",
    "usar",
    "separa",
    "separar",
    "define",
    "prioriza",
    "evita",
    "mide",
    "manten",
    "protege",
    "aisla",
    "mueve",
    "valida",
)

TECHNICAL_TOPIC_GROUPS = {
    "api": ("api", "rest", "http", "endpoint"),
    "auth": ("auth", "autenticacion", "autorizacion", "jwt", "oauth", "oauth2", "token"),
    "rollback": ("rollback", "reversion", "compensacion"),
    "cache": ("cache", "ttl", "invalida", "invalidez"),
    "queues": ("cola", "colas", "queue", "queues", "consumer", "consumidor"),
    "latency": ("latencia", "p95", "p99", "timeout", "timeouts"),
    "integrations": ("integracion", "integraciones", "webhook", "externa", "externas"),
    "migration": ("migrar", "migrarias", "monolito", "monolitico", "monolitica", "strangler"),
    "observability": ("observabilidad", "metricas", "metrics", "logs", "logging", "trace", "tracing"),
    "services": ("backend", "servicio", "servicios", "microservicio", "microservicios"),
    "state": ("estado", "estados", "stateful", "stateless", "idempotencia", "idempotente"),
    "tenancy": ("tenant", "tenants", "multi tenant", "multitenant", "quota", "rate limit", "limite por cliente"),
    "versioning": ("versionado", "version", "compatibilidad", "backward", "rollout", "despliegue", "release", "canary"),
}


@dataclass(frozen=True)
class RuntimeQualityAssessment:
    status: str
    issue: str | None
    degradation_hint: str | None
    retry_with_fallback: bool


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", repair_common_mojibake(text or ""))
    return "".join(
        character for character in normalized if not unicodedata.combining(character)
    ).replace("\ufffd", "?").replace("ï¿½", "?").casefold()


def _looks_like_prompt_leak(leading_window: str) -> bool:
    if any(hint in leading_window for hint in PROMPT_LEAK_HINTS):
        return True

    if leading_window.startswith("respondes siempre"):
        return True

    control_hits = sum(hint in leading_window for hint in PROMPT_CONTROL_HINTS)
    if control_hits < 2:
        return False

    return (
        leading_window.startswith("- ")
        or leading_window.startswith("respondes siempre")
        or leading_window.startswith("resume en una sola linea")
        or " - " in leading_window[:160]
    )


def _extract_topic_groups(text: str) -> set[str]:
    matches: set[str] = set()
    for topic_name, topic_hints in TECHNICAL_TOPIC_GROUPS.items():
        if any(hint in text for hint in topic_hints):
            matches.add(topic_name)
    return matches


def _looks_like_action_oriented_prompt(text: str) -> bool:
    return any(hint in text for hint in ACTION_ORIENTED_PROMPT_HINTS)


def _count_action_markers(text: str) -> int:
    return sum(hint in text for hint in ACTION_ORIENTED_RESPONSE_HINTS)


def assess_runtime_quality(
    response: str | None,
    *,
    task_type: str,
    fallback_available: bool,
    source_text: str = "",
) -> RuntimeQualityAssessment:
    compact = " ".join((response or "").split())
    normalized = _normalize_text(compact)

    if not compact:
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_EMPTY,
            issue="empty_output",
            degradation_hint="runtime_empty_output",
            retry_with_fallback=fallback_available and task_type == "technical_reasoning",
        )

    if any(
        normalized.startswith(prefix)
        for prefix in SEVERE_PLACEHOLDER_PREFIXES
    ):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_PLACEHOLDER,
            issue="placeholder_output",
            degradation_hint="runtime_placeholder_output",
            retry_with_fallback=fallback_available and task_type == "technical_reasoning",
        )

    if any(hint in normalized for hint in PLACEHOLDER_HINTS):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_PLACEHOLDER,
            issue="placeholder_output",
            degradation_hint="runtime_placeholder_output",
            retry_with_fallback=fallback_available and task_type == "technical_reasoning",
        )

    leading_window = normalized[:240]
    if any(hint in leading_window for hint in CRITIC_LEAK_HINTS):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_PLACEHOLDER,
            issue="critic_leak_output",
            degradation_hint="runtime_critic_leak_output",
            retry_with_fallback=fallback_available,
        )

    if _looks_like_prompt_leak(leading_window):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_PLACEHOLDER,
            issue="prompt_leak_output",
            degradation_hint="runtime_prompt_leak_output",
            retry_with_fallback=fallback_available,
        )

    normalized_source = _normalize_text(source_text)
    expected_markers = tuple(
        marker for marker in TECHNICAL_TOPIC_HINTS if marker in normalized_source
    )
    source_groups = _extract_topic_groups(normalized_source)
    response_groups = _extract_topic_groups(normalized)
    if (
        task_type == "technical_reasoning"
        and len(compact.split()) <= 7
        and expected_markers
    ):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_PLACEHOLDER,
            issue="placeholder_output",
            degradation_hint="runtime_too_short_for_technical_output",
            retry_with_fallback=fallback_available,
        )
    if (
        task_type == "technical_reasoning"
        and any(hint in leading_window for hint in SELF_PRESENTATION_HINTS)
    ):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_OFF_TOPIC,
            issue="off_topic_output",
            degradation_hint="runtime_off_topic_output",
            retry_with_fallback=fallback_available,
        )
    if (
        task_type == "technical_reasoning"
        and expected_markers
        and not any(marker in normalized for marker in expected_markers)
    ):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_OFF_TOPIC,
            issue="off_topic_output",
            degradation_hint="runtime_off_topic_output",
            retry_with_fallback=fallback_available,
        )
    if (
        task_type == "technical_reasoning"
        and len(source_groups) >= 3
        and len(source_groups.intersection(response_groups)) <= 1
    ):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_OFF_TOPIC,
            issue="off_topic_output",
            degradation_hint="runtime_low_topic_coverage",
            retry_with_fallback=fallback_available,
        )
    if (
        task_type == "technical_reasoning"
        and _looks_like_action_oriented_prompt(normalized_source)
        and _count_action_markers(normalized) == 0
        and len(compact.split()) < 50
    ):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_PLACEHOLDER,
            issue="placeholder_output",
            degradation_hint="runtime_low_decision_density",
            retry_with_fallback=fallback_available,
        )
    if (
        task_type == "technical_reasoning"
        and any(opener in leading_window for opener in CEREMONIAL_TECHNICAL_OPENERS)
        and len(compact.split()) < 18
    ):
        return RuntimeQualityAssessment(
            status=QUALITY_STATUS_PLACEHOLDER,
            issue="placeholder_output",
            degradation_hint="runtime_ceremonial_output",
            retry_with_fallback=fallback_available,
        )

    return RuntimeQualityAssessment(
        status=QUALITY_STATUS_OK,
        issue=None,
        degradation_hint=None,
        retry_with_fallback=False,
    )
