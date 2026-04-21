from __future__ import annotations

from dataclasses import dataclass

from .behavior_agent import (
    BehaviorPlan,
    INTENT_TECHNICAL_EXPLAIN,
    INTENT_TECHNICAL_TROUBLESHOOT,
    build_stable_technical_explain_response,
)
from .profile_agent import build_user_profile
from .text_matching import normalize_internal_text


@dataclass(frozen=True)
class FallbackDecision:
    response: str
    fallback_reason: str


def _contains_any(text: str, options: tuple[str, ...] | list[str] | set[str]) -> bool:
    return any(option in text for option in options)


def _prefix_rescue_response(prefix: str, response: str) -> str:
    compact = " ".join((response or "").split())
    if not compact:
        return prefix
    return f"{prefix} {compact}"


def _build_open_technical_rescue_response(
    user_input: str,
    *,
    profile,
) -> str | None:
    normalized_input = normalize_internal_text(user_input or "")
    if not normalized_input:
        return None

    asks_for_explanation = _contains_any(
        normalized_input,
        {
            "que es",
            "que significa",
            "explica",
            "explicame",
            "como funciona",
            "como balancearias",
            "como equilibrarias",
            "tradeoff",
            "tradeoffs",
        },
    )
    if not asks_for_explanation and "?" not in user_input:
        return None

    if (
        "api" in normalized_input
        and _contains_any(normalized_input, {"cache", "cola", "colas"})
        and _contains_any(normalized_input, {"auth", "autenticacion", "autorizacion"})
    ):
        response = (
            "En esa API, auth, cache y colas no deberian competir por el mismo lugar. "
            "Auth tiene que validar rapido y dejar una identidad confiable en el request; "
            "cache conviene usarla para lecturas, permisos derivables o datos repetidos con TTL e invalidez clara; "
            "y las colas sirven para trabajo asincrono, reintentos y efectos externos que no necesitas cerrar dentro de la misma respuesta. "
            "Si hay mucho trafico, agrega idempotencia, backpressure y observabilidad para no ganar throughput a costa de perder control."
        )
        if profile.prefers_practical or profile.works_in_workshop:
            response += " Protege primero consistencia y auth, y optimiza despues la parte asincrona."
        return response

    if _contains_any(
        normalized_input,
        {"observabilidad", "metricas", "metrics", "logs", "logging", "tracing", "trace"},
    ) and _contains_any(
        normalized_input,
        {"api", "backend", "servicio", "servicios", "integracion", "integraciones"},
    ):
        return (
            "En backend, observabilidad util es poder seguir una request de punta a punta. "
            "Eso suele pedir logs estructurados con request id, metricas de error y latencia, trazas entre servicios e integraciones, "
            "y alertas sobre timeouts, retries y colas acumuladas. Si no ves eso, el sistema puede parecer sano y fallar justo en produccion."
        )

    if _contains_any(
        normalized_input,
        {"api", "backend", "servicio", "servicios", "arquitectura", "integracion", "integraciones"},
    ) and _contains_any(
        normalized_input,
        {"auth", "rollback", "cache", "cola", "colas", "latencia", "estado", "observabilidad"},
    ):
        return (
            "Lo sano en ese tipo de diseno backend es separar contrato de API, reglas de dominio y adaptadores a persistencia o integraciones. "
            "Deja auth, validacion y cambios de estado criticos en el camino sincrono; usa cache y colas solo donde toleras TTL, replay o compensacion; "
            "y apoya todo con timeouts, idempotencia y observabilidad para que rollback y latencia no dependan de suposiciones ocultas."
        )

    return None


def _classify_provider_failure(error_text: str | None) -> str:
    normalized_error = (error_text or "").casefold()

    if "prompt_leak_output" in normalized_error:
        return "prompt_leak_output"

    if "off_topic_output" in normalized_error:
        return "off_topic_output"

    if "placeholder_output" in normalized_error:
        return "placeholder_output"

    if "critic_leak_output" in normalized_error:
        return "critic_leak_output"

    if (
        "model_missing" in normalized_error
        or "no se encontro el modelo" in normalized_error
        or "no se encontró el modelo" in normalized_error
    ):
        return "model_missing"

    if (
        "runner_missing" in normalized_error
        or "runner_not_executable" in normalized_error
        or "no se encontro llama-cli" in normalized_error
        or "no se encontró llama-cli" in normalized_error
        or "llama-cli no es ejecutable" in normalized_error
    ):
        return "runner_unavailable"

    if "empty_response" in normalized_error or "sin respuesta" in normalized_error:
        return "empty_response"

    if "unsupported_role" in normalized_error:
        return "unsupported_role"

    if "provider_missing" in normalized_error:
        return "provider_missing"

    return "runtime_error"


def build_fallback_response(
    *,
    conversation: list[dict[str, str]],
    memory: dict[str, str],
    behavior_plan: BehaviorPlan,
    error_text: str | None,
) -> FallbackDecision:
    latest_user_message = ""
    for message in reversed(conversation):
        if message.get("role") == "user":
            latest_user_message = str(message.get("content", ""))
            break

    profile = build_user_profile(memory)
    issue_type = _classify_provider_failure(error_text)

    if issue_type == "prompt_leak_output":
        base_message = "Ahora mismo el provider devolvio una salida contaminada por instrucciones internas."
    elif issue_type == "off_topic_output":
        base_message = "Ahora mismo el provider se fue de tema y no dio una salida tecnica confiable."
    elif issue_type == "placeholder_output":
        base_message = "Ahora mismo el provider devolvio una salida pobre o placeholder."
    elif issue_type == "critic_leak_output":
        base_message = "Ahora mismo el provider devolvio texto de critica interna en la salida visible."
    elif issue_type == "model_missing":
        base_message = "Ahora mismo no tengo disponible el archivo del modelo local y el stack quedó degradado."
    elif issue_type == "runner_unavailable":
        base_message = "Ahora mismo no tengo disponible llama-cli para usar el provider local y el stack quedó degradado."
    elif issue_type == "empty_response":
        base_message = "Ahora mismo el provider principal no devolvió una salida útil."
    elif issue_type == "unsupported_role":
        base_message = "Ahora mismo no tengo un provider listo para ese rol."
    elif issue_type == "provider_missing":
        base_message = "Ahora mismo no tengo un provider registrado para esa ruta."
    else:
        base_message = "Ahora mismo no pude usar bien el provider principal para ampliar esa respuesta."

    if behavior_plan.intent == INTENT_TECHNICAL_TROUBLESHOOT:
        if profile.prefers_practical or profile.works_in_workshop:
            return FallbackDecision(
                response=(
                    f"{base_message} Si me pasas el error exacto o el dato puntual, "
                    "voy directo al paso más práctico."
                ),
                fallback_reason=issue_type,
            )

        return FallbackDecision(
            response=(
                f"{base_message} Si me pasas el error exacto o el dato puntual, "
                "te ayudo con el siguiente paso."
            ),
            fallback_reason=issue_type,
        )

    if behavior_plan.intent == INTENT_TECHNICAL_EXPLAIN:
        stable_rescue = build_stable_technical_explain_response(
            latest_user_message,
            profile,
        )
        if stable_rescue:
            return FallbackDecision(
                response=_prefix_rescue_response("Rescate razonable:", stable_rescue),
                fallback_reason=f"stable_technical_rescue:{issue_type}",
            )

        open_technical_rescue = _build_open_technical_rescue_response(
            latest_user_message,
            profile=profile,
        )
        if open_technical_rescue:
            return FallbackDecision(
                response=_prefix_rescue_response("Cobertura parcial:", open_technical_rescue),
                fallback_reason=f"contextual_technical_rescue:{issue_type}",
            )

        coverage_note = (
            "Cobertura baja. "
            if issue_type in {"prompt_leak_output", "off_topic_output", "placeholder_output", "critic_leak_output"}
            else ""
        )
        if profile.prefers_clear or profile.prefers_brief:
            return FallbackDecision(
                response=(
                    f"{coverage_note}{base_message} Si quieres, hazme una pregunta más concreta "
                    "y te respondo corto y claro."
                ),
                fallback_reason=issue_type,
            )

        return FallbackDecision(
            response=(
                f"{coverage_note}{base_message} Si me lo acotas un poco más, "
                "te doy una explicación breve y útil."
            ),
            fallback_reason=issue_type,
        )

    if profile.prefers_clear or profile.prefers_brief:
        return FallbackDecision(
            response=(
                f"{base_message} Si me dices el punto exacto, "
                "te ayudo con una respuesta más corta y concreta."
            ),
            fallback_reason=issue_type,
        )

    return FallbackDecision(
        response=(
            f"{base_message} Si me dices qué parte necesitas, "
            "te ayudo con lo puntual."
        ),
        fallback_reason=issue_type,
    )
