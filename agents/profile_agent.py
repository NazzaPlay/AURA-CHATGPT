import re
import unicodedata
from dataclasses import dataclass
from typing import Any


TECHNICAL_INTENTS = {"technical_troubleshoot", "technical_explain"}
INTEREST_CONTEXT_INTENTS = {"technical_explain"}

CLEAR_PREFERENCE_HINTS = ("clar", "simple", "ordenad", "entend")
BRIEF_PREFERENCE_HINTS = ("cort", "breve", "concis", "resumen", "al grano")
PRACTICAL_PREFERENCE_HINTS = ("practic", "paso", "concret", "direct", "aplic")
WORKSHOP_HINTS = ("taller",)
INTEREST_CONTEXT_HINTS = (
    "ejemplo",
    "ejemplos",
    "analogia",
    "analogia",
    "compar",
    "imagina",
    "como funciona",
    "que es",
    "que significa",
    "para que sirve",
)


@dataclass(frozen=True)
class UserProfile:
    name: str = ""
    work: str = ""
    interests: tuple[str, ...] = ()
    preferences: tuple[str, ...] = ()
    prefers_clear: bool = False
    prefers_brief: bool = False
    prefers_practical: bool = False
    works_in_workshop: bool = False


def _normalize_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    if value is None:
        return ""

    return str(value).strip()


def _normalize_match_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    cleaned = re.sub(r"[^\w\s]", " ", without_accents)
    return " ".join(cleaned.split())


def _normalize_items(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, str) and value.strip():
        raw_items = [value]
    else:
        raw_items = []

    items: list[str] = []
    seen: set[str] = set()

    for raw_item in raw_items:
        item = _normalize_text(raw_item)
        if not item:
            continue

        key = item.casefold()
        if key in seen:
            continue

        seen.add(key)
        items.append(item)

    return tuple(items)


def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def _contains_hint(texts: tuple[str, ...], hints: tuple[str, ...]) -> bool:
    for text in texts:
        normalized_text = _normalize_match_text(text)
        if any(hint in normalized_text for hint in hints):
            return True

    return False


def _select_interest_context(interests: tuple[str, ...], limit: int = 2) -> list[str]:
    return list(interests[:limit])


def _should_use_work_context(profile: UserProfile, intent: str) -> bool:
    return bool(profile.work) and intent in TECHNICAL_INTENTS


def _should_use_interest_context(
    profile: UserProfile,
    intent: str,
    user_input: str,
) -> bool:
    if not profile.interests or intent not in INTEREST_CONTEXT_INTENTS:
        return False

    normalized_input = _normalize_match_text(user_input)
    return any(hint in normalized_input for hint in INTEREST_CONTEXT_HINTS)


def build_user_profile(memory: dict[str, Any]) -> UserProfile:
    preferences = _normalize_items(memory.get("preferences", []))
    work = _normalize_text(memory.get("work", ""))
    normalized_work = _normalize_match_text(work)

    prefers_clear = _contains_hint(preferences, CLEAR_PREFERENCE_HINTS)
    prefers_brief = _contains_hint(preferences, BRIEF_PREFERENCE_HINTS)
    prefers_practical = _contains_hint(preferences, PRACTICAL_PREFERENCE_HINTS)
    works_in_workshop = any(hint in normalized_work for hint in WORKSHOP_HINTS)

    return UserProfile(
        name=_normalize_text(memory.get("name", "")),
        work=work,
        interests=_normalize_items(memory.get("interests", [])),
        preferences=preferences,
        prefers_clear=prefers_clear,
        prefers_brief=prefers_brief,
        prefers_practical=prefers_practical,
        works_in_workshop=works_in_workshop,
    )


def build_profile_style_hints(
    profile: UserProfile,
    intent: str,
    user_input: str = "",
) -> list[str]:
    hints: list[str] = []

    if profile.prefers_clear:
        hints.append("Prioriza frases claras y fáciles de seguir.")

    if profile.prefers_brief:
        hints.append("Mantén la respuesta compacta cuando no haga falta más detalle.")

    if profile.prefers_practical or (
        profile.works_in_workshop and intent in TECHNICAL_INTENTS
    ):
        hints.append("Prioriza pasos concretos, criterios accionables y ejemplos aplicados.")

    if profile.works_in_workshop and _should_use_work_context(profile, intent):
        hints.append(
            "Si ayuda, aterriza la explicación a un contexto práctico parecido a un taller "
            "o trabajo manual, sin forzarlo."
        )

    if _should_use_interest_context(profile, intent, user_input):
        interest_context = _format_items(_select_interest_context(profile.interests))
        hints.append(
            f"Si suma valor real, puedes usar un ejemplo breve conectado con {interest_context}, "
            "sin exagerar ni desviar el tema."
        )

    return hints


def build_profile_planning_hints(
    profile: UserProfile,
    intent: str,
    user_input: str = "",
) -> list[str]:
    hints: list[str] = []

    if profile.prefers_brief:
        hints.append("Si puedes resolverlo con menos palabras, mejor.")

    if profile.prefers_clear:
        hints.append("Haz visible rápido la idea principal antes del detalle.")

    if profile.prefers_practical or _should_use_work_context(profile, intent):
        hints.append("Baja pronto a la aplicación práctica y a pasos concretos.")

    if _should_use_interest_context(profile, intent, user_input):
        hints.append("Si un ejemplo ayuda de verdad, usa uno breve y natural.")

    return hints


def build_profile_prompt_context(
    profile: UserProfile,
    intent: str,
    user_input: str = "",
) -> str:
    lines: list[str] = []

    if _should_use_work_context(profile, intent):
        lines.append(f"Contexto del usuario: trabaja {profile.work}.")

    if profile.works_in_workshop and _should_use_work_context(profile, intent):
        lines.append(
            "Para temas técnicos, suele servir más una respuesta práctica, orientada a acción "
            "y fácil de aplicar en un contexto de taller."
        )

    preference_labels: list[str] = []
    if profile.prefers_clear:
        preference_labels.append("claras")
    if profile.prefers_brief:
        preference_labels.append("cortas")
    if profile.prefers_practical:
        preference_labels.append("prácticas")

    if preference_labels:
        lines.append(
            "Preferencias de estilo del usuario: "
            f"{_format_items(preference_labels)}."
        )

    if _should_use_interest_context(profile, intent, user_input):
        interest_context = _format_items(_select_interest_context(profile.interests))
        lines.append(
            "Intereses disponibles para contextualizar solo si encajan de forma natural: "
            f"{interest_context}."
        )

    return "\n".join(lines)
