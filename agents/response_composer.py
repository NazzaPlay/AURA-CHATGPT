from __future__ import annotations

from dataclasses import dataclass


COMPOSITION_MODE_HEURISTIC_DIRECT = "heuristic_direct"
COMPOSITION_MODE_INTERNAL_DIRECT = "internal_direct"
COMPOSITION_MODE_PROVIDER_PRIMARY = "provider_primary"
COMPOSITION_MODE_PROVIDER_PRIMARY_WITH_CRITIC = "provider_primary_with_critic"
COMPOSITION_MODE_PROVIDER_CRITIC_ONLY = "provider_critic_only"
COMPOSITION_MODE_FALLBACK_SAFE = "fallback_safe"

VERIFICATION_OUTCOME_VERIFIED = "verified"
VERIFICATION_OUTCOME_ADJUSTMENT = "adjustment_suggested"
VERIFICATION_OUTCOME_UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class ComposedResponse:
    response: str
    used_model: bool
    composition_mode: str
    critic_summary: str | None = None
    verification_outcome: str | None = None


def _parse_critic_feedback(critic_response: str | None) -> tuple[str | None, str | None]:
    if critic_response is None:
        return None, None

    compact = " ".join(critic_response.split()).strip()
    if not compact:
        return None, None

    upper = compact.upper()
    if upper.startswith("VERIFICADA"):
        summary = compact.split(":", 1)[1].strip() if ":" in compact else ""
        return VERIFICATION_OUTCOME_VERIFIED, summary or "sin conflicto claro"

    if upper.startswith("AJUSTE"):
        summary = compact.split(":", 1)[1].strip() if ":" in compact else ""
        return VERIFICATION_OUTCOME_ADJUSTMENT, summary or compact

    if upper.startswith("DUDOSA"):
        summary = compact.split(":", 1)[1].strip() if ":" in compact else ""
        return VERIFICATION_OUTCOME_UNCERTAIN, summary or compact

    return VERIFICATION_OUTCOME_UNCERTAIN, compact


def _merge_verification_note(provider_response: str, critic_summary: str) -> str:
    base = provider_response.strip()
    note = critic_summary.strip().rstrip(".")

    if not base:
        return f"Verificación breve: {note}."

    if base[-1] not in ".!?":
        base = f"{base}."

    return f"{base} Verificación breve: {note}."


def compose_response(
    *,
    direct_response: str | None = None,
    provider_response: str | None = None,
    fallback_response: str | None = None,
    critic_response: str | None = None,
    selected_role: str | None = None,
) -> ComposedResponse:
    if direct_response is not None:
        return ComposedResponse(
            response=direct_response,
            used_model=False,
            composition_mode=COMPOSITION_MODE_HEURISTIC_DIRECT,
        )

    if provider_response is not None and critic_response is not None:
        verification_outcome, critic_summary = _parse_critic_feedback(critic_response)
        return ComposedResponse(
            response=provider_response,
            used_model=True,
            composition_mode=COMPOSITION_MODE_PROVIDER_PRIMARY_WITH_CRITIC,
            critic_summary=critic_summary,
            verification_outcome=verification_outcome,
        )

    if provider_response is not None:
        return ComposedResponse(
            response=provider_response,
            used_model=True,
            composition_mode=(
                COMPOSITION_MODE_PROVIDER_CRITIC_ONLY
                if selected_role == "critic_verifier"
                else COMPOSITION_MODE_PROVIDER_PRIMARY
            ),
            critic_summary=None,
            verification_outcome=None,
        )

    return ComposedResponse(
        response=fallback_response or "",
        used_model=False,
        composition_mode=COMPOSITION_MODE_FALLBACK_SAFE,
    )
