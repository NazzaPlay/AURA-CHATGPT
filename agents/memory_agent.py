import re
from dataclasses import dataclass
from typing import Any

from memory_store import save_memory
from .text_matching import normalize_internal_text


MEMORY_INTENT_NAME = "name"
MEMORY_INTENT_WORK = "work"
MEMORY_INTENT_LIKES = "likes"
MEMORY_INTENT_PREFERENCES = "preferences"
QUESTION_PREFIXES = (
    "que ",
    "como ",
    "cuando ",
    "donde ",
    "quien ",
    "cual ",
    "cuales ",
    "por que ",
)
EXACT_NAME_QUESTIONS = {"como me llamo"}
EXACT_WORK_QUESTIONS = {
    "en que trabajo",
    "de que trabajo",
    "cual es mi trabajo",
    "que trabajo tengo",
    "que trabajo hago",
}
EXACT_LIKES_QUESTIONS = {
    "que me gusta",
    "que me interesa",
    "cuales son mis gustos",
}
INVALID_INTEREST_ITEMS = {
    "hacer",
    "algo",
    "cosas",
    "de todo",
    "eso",
    "esto",
    "nada",
    "todo",
}
KNOWN_PREFERENCE_CORRECTIONS = {
    "respuertas claras": "respuestas claras",
}

NAME_PATTERN = re.compile(r"\bme llamo\s+(.+)", re.IGNORECASE)
ASK_NAME_PATTERN = re.compile(r"\bc[oó]mo me llamo\b", re.IGNORECASE)
ASK_WORK_PATTERN = re.compile(
    r"\ben\s+qu[eé]\s+trabajo\b|\bde\s+qu[eé]\s+trabajo\b"
    r"|\bcu[aá]l\s+es\s+mi\s+trabajo\b"
    r"|\bqu[eé]\s+trabajo\s+(?:tengo|hago)\b",
    re.IGNORECASE,
)
ASK_LIKES_PATTERN = re.compile(
    r"\bqu[eé]\s+me\s+gusta\b|\bqu[eé]\s+me\s+interesa\b|\bcu[aá]les?\s+son\s+mis\s+gustos\b",
    re.IGNORECASE,
)
WORK_AS_PATTERN = re.compile(r"\btrabajo\s+como\s+(.+)", re.IGNORECASE)
WORK_IN_PATTERN = re.compile(r"\btrabajo\s+en\s+(.+)", re.IGNORECASE)
WORK_DEDICO_PATTERN = re.compile(r"\bme dedico a\s+(.+)", re.IGNORECASE)
WORK_SOY_PATTERN = re.compile(r"\bsoy\s+(?:un|una)?\s*(.+)", re.IGNORECASE)
INTEREST_PATTERNS = (
    re.compile(r"(?<!no )\bme\s+gusta(?:n)?\s+(.+)", re.IGNORECASE),
    re.compile(r"(?<!no )\bme\s+encanta(?:n)?\s+(.+)", re.IGNORECASE),
    re.compile(r"\bme\s+interesa(?:n)?\s+(.+)", re.IGNORECASE),
    re.compile(r"\bmis\s+hobbies\s+son\s+(.+)", re.IGNORECASE),
)
PREFERENCE_PATTERN = re.compile(r"\bprefiero\s+(.+)", re.IGNORECASE)
FAVORITE_PATTERN = re.compile(
    r"\bmi\s+(.+?)\s+favorit[oa]\s+es\s+(.+)",
    re.IGNORECASE,
)
ASK_FAVORITE_PATTERN = re.compile(
    r"\bcu[aá]l\s+es\s+mi\s+(.+?)\s+favorit[oa]\b"
    r"|\b(?:decime|dime)\s+mi\s+(.+?)\s+favorit[oa]\b",
    re.IGNORECASE,
)
NAME_STOP_WORDS = {"y", "pero", "porque", "soy", "tengo", "vivo", "trabajo", "mi"}
CLAUSE_STOP_WORDS = {"y", "pero", "porque", "aunque", "ademas", "además"}
INVALID_SOY_PREFIXES = ("de ", "del ", "de la ", "muy ", "fan ", "feliz", "triste")


@dataclass(frozen=True)
class MemoryQuestion:
    intent: str
    is_ambiguous: bool = False


def _normalize_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    if value is None:
        return ""

    return str(value).strip()


def _normalize_list(value: Any, *, item_type: str = "generic") -> list[str]:
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, str) and value.strip():
        raw_items = [value]
    else:
        raw_items = []

    items = []

    for raw_item in raw_items:
        item = _normalize_text(raw_item)
        if not item:
            continue

        cleaned_item = _clean_memory_item(item, item_type=item_type)
        if cleaned_item:
            items.append(cleaned_item)

    return _dedupe_items(items)


def _dedupe_items(items: list[str]) -> list[str]:
    unique_items: list[str] = []
    seen: set[str] = set()

    for item in items:
        key = normalize_internal_text(item)
        if key in seen:
            continue

        seen.add(key)
        unique_items.append(item)

    return unique_items


def _normalize_match_text(text: str) -> str:
    return normalize_internal_text(text)


def _trim_punctuation(candidate: str) -> str:
    return re.split(r"[.!?;:]", candidate, maxsplit=1)[0].strip(" ¿?¡!")


def _truncate_clause(candidate: str) -> str:
    words = []

    for part in _trim_punctuation(candidate).split():
        if part.lower() in CLAUSE_STOP_WORDS and words:
            break

        words.append(part)

    return " ".join(words).strip()


def _is_question_like_interest(user_input: str) -> bool:
    normalized_input = _normalize_match_text(user_input)
    if "?" not in user_input and not user_input.strip().startswith("¿"):
        return False

    return normalized_input.startswith(QUESTION_PREFIXES)


def _clean_memory_item(candidate: str, *, item_type: str) -> str | None:
    cleaned = _trim_punctuation(candidate)
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return None

    normalized_item = _normalize_match_text(cleaned)
    if not normalized_item:
        return None

    if item_type == "interest":
        item_tokens = tuple(normalized_item.split())
        generic_tokens = INVALID_INTEREST_ITEMS | {"hacer"}

        if normalized_item in INVALID_INTEREST_ITEMS:
            return None

        if normalized_item in EXACT_LIKES_QUESTIONS:
            return None

        if normalized_item.startswith(QUESTION_PREFIXES):
            return None

        if item_tokens and all(token in generic_tokens for token in item_tokens):
            return None

    if item_type == "preference":
        corrected_item = KNOWN_PREFERENCE_CORRECTIONS.get(normalized_item)
        if corrected_item:
            return corrected_item

    return cleaned


def _split_memory_items(candidate: str, *, item_type: str = "generic") -> list[str]:
    cleaned = _trim_punctuation(candidate)
    parts = re.split(r",|\s+y\s+|\s+e\s+", cleaned, flags=re.IGNORECASE)
    items = [part.strip(" ¿?¡!").strip() for part in parts if part.strip()]

    if not items and cleaned:
        items = [cleaned]

    cleaned_items = []

    for item in items:
        cleaned_item = _clean_memory_item(item, item_type=item_type)
        if cleaned_item:
            cleaned_items.append(cleaned_item)

    return _dedupe_items(cleaned_items)


def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def _ensure_memory_schema(memory: dict[str, Any]) -> bool:
    changed = False
    legacy_name = memory.pop("nombre", None)

    if legacy_name and not memory.get("name"):
        memory["name"] = _normalize_text(legacy_name)
        changed = True

    normalized_name = _normalize_text(memory.get("name", ""))
    normalized_work = _normalize_text(memory.get("work", ""))
    normalized_interests = _normalize_list(
        memory.get("interests", []),
        item_type="interest",
    )
    normalized_preferences = _normalize_list(
        memory.get("preferences", []),
        item_type="preference",
    )

    if memory.get("name") != normalized_name:
        memory["name"] = normalized_name
        changed = True

    if memory.get("work") != normalized_work:
        memory["work"] = normalized_work
        changed = True

    if memory.get("interests") != normalized_interests:
        memory["interests"] = normalized_interests
        changed = True

    if memory.get("preferences") != normalized_preferences:
        memory["preferences"] = normalized_preferences
        changed = True

    return changed


def extract_name(user_input: str) -> str | None:
    match = NAME_PATTERN.search(user_input)
    if not match:
        return None

    candidate = _trim_punctuation(match.group(1))
    parts = []

    for part in candidate.split():
        clean_part = part.strip("¿?¡!")

        if clean_part.lower() in NAME_STOP_WORDS and parts:
            break

        parts.append(clean_part)

    name = " ".join(parts).strip()
    return name or None


def extract_work(user_input: str) -> str | None:
    for pattern, prefix in (
        (WORK_AS_PATTERN, "como"),
        (WORK_IN_PATTERN, "en"),
        (WORK_DEDICO_PATTERN, "a"),
    ):
        match = pattern.search(user_input)
        if not match:
            continue

        candidate = _truncate_clause(match.group(1))
        if candidate:
            return f"{prefix} {candidate}"

    match = WORK_SOY_PATTERN.search(user_input)
    if not match:
        return None

    candidate = _truncate_clause(match.group(1))
    candidate = re.sub(r"^(?:un|una)\s+", "", candidate, flags=re.IGNORECASE).strip()

    if not candidate:
        return None

    if candidate.lower().startswith(INVALID_SOY_PREFIXES):
        return None

    return f"como {candidate}"


def analyze_memory_question(user_input: str) -> MemoryQuestion | None:
    normalized_input = _normalize_match_text(user_input)

    if is_name_question(user_input):
        return MemoryQuestion(
            intent=MEMORY_INTENT_NAME,
            is_ambiguous=normalized_input not in EXACT_NAME_QUESTIONS,
        )

    if is_work_question(user_input):
        return MemoryQuestion(
            intent=MEMORY_INTENT_WORK,
            is_ambiguous=normalized_input not in EXACT_WORK_QUESTIONS,
        )

    if is_likes_question(user_input):
        return MemoryQuestion(
            intent=MEMORY_INTENT_LIKES,
            is_ambiguous=normalized_input not in EXACT_LIKES_QUESTIONS,
        )

    if is_preference_question(user_input):
        return MemoryQuestion(
            intent=MEMORY_INTENT_PREFERENCES,
            is_ambiguous=False,
        )

    return None


def extract_interests(user_input: str) -> list[str]:
    memory_question = analyze_memory_question(user_input)
    if memory_question and memory_question.intent == MEMORY_INTENT_LIKES:
        return []

    if _is_question_like_interest(user_input):
        return []

    items: list[str] = []

    for pattern in INTEREST_PATTERNS:
        match = pattern.search(user_input)
        if not match:
            continue

        items.extend(_split_memory_items(match.group(1), item_type="interest"))

    return _dedupe_items(items)


def extract_preferences(user_input: str) -> list[str]:
    preferences: list[str] = []

    preference_match = PREFERENCE_PATTERN.search(user_input)
    if preference_match:
        preferences.extend(_split_memory_items(preference_match.group(1), item_type="preference"))

    favorite_match = FAVORITE_PATTERN.search(user_input)
    if favorite_match:
        favorite_type = _truncate_clause(favorite_match.group(1))
        favorite_value = _truncate_clause(favorite_match.group(2))

        if favorite_type and favorite_value:
            preferences.append(f"{favorite_type} favorito: {favorite_value}")

    return _dedupe_items(preferences)


def extract_memory_update(user_input: str) -> dict[str, Any]:
    memory_update: dict[str, Any] = {}

    extracted_name = extract_name(user_input)
    if extracted_name:
        memory_update["name"] = extracted_name

    extracted_work = extract_work(user_input)
    if extracted_work:
        memory_update["work"] = extracted_work

    extracted_interests = extract_interests(user_input)
    if extracted_interests:
        memory_update["interests"] = extracted_interests

    extracted_preferences = extract_preferences(user_input)
    if extracted_preferences:
        memory_update["preferences"] = extracted_preferences

    return memory_update


def is_memory_update(user_input: str) -> bool:
    return bool(extract_memory_update(user_input))


def is_name_question(user_input: str) -> bool:
    return bool(ASK_NAME_PATTERN.search(user_input))


def is_work_question(user_input: str) -> bool:
    return bool(ASK_WORK_PATTERN.search(user_input))


def is_likes_question(user_input: str) -> bool:
    return bool(ASK_LIKES_PATTERN.search(user_input))


def is_preference_question(user_input: str) -> bool:
    return bool(ASK_FAVORITE_PATTERN.search(user_input))


def get_memory_question_type(user_input: str) -> str | None:
    memory_question = analyze_memory_question(user_input)
    if memory_question and not memory_question.is_ambiguous:
        return memory_question.intent

    return None


def get_ambiguous_memory_question_type(user_input: str) -> str | None:
    memory_question = analyze_memory_question(user_input)
    if memory_question and memory_question.is_ambiguous:
        return memory_question.intent

    return None


def _contains_all_items(stored_items: list[str], expected_items: list[str]) -> bool:
    stored_keys = {normalize_internal_text(item) for item in stored_items}
    return all(normalize_internal_text(item) in stored_keys for item in expected_items)


def is_memory_update_already_stored(user_input: str, memory: dict[str, Any]) -> bool:
    memory_update = extract_memory_update(user_input)
    if not memory_update:
        return False

    if "name" in memory_update and _normalize_text(memory.get("name", "")) != memory_update["name"]:
        return False

    if "work" in memory_update and _normalize_text(memory.get("work", "")) != memory_update["work"]:
        return False

    if "interests" in memory_update and not _contains_all_items(
        _normalize_list(memory.get("interests", [])),
        memory_update["interests"],
    ):
        return False

    if "preferences" in memory_update and not _contains_all_items(
        _normalize_list(memory.get("preferences", [])),
        memory_update["preferences"],
    ):
        return False

    return True


def migrate_memory(memory: dict[str, Any]) -> bool:
    return _ensure_memory_schema(memory)


def remember_basic_memory(
    user_input_raw: str,
    memory: dict[str, Any],
    memory_file: str,
) -> bool:
    changed = _ensure_memory_schema(memory)

    extracted_name = extract_name(user_input_raw)
    if extracted_name and memory.get("name") != extracted_name:
        memory["name"] = extracted_name
        changed = True

    extracted_work = extract_work(user_input_raw)
    if extracted_work and memory.get("work") != extracted_work:
        memory["work"] = extracted_work
        changed = True

    extracted_interests = extract_interests(user_input_raw)
    merged_interests = _dedupe_items(memory.get("interests", []) + extracted_interests)
    if merged_interests != memory.get("interests"):
        memory["interests"] = merged_interests
        changed = True

    extracted_preferences = extract_preferences(user_input_raw)
    merged_preferences = _dedupe_items(memory.get("preferences", []) + extracted_preferences)
    if merged_preferences != memory.get("preferences"):
        memory["preferences"] = merged_preferences
        changed = True

    if changed:
        save_memory(memory, memory_file)

    return changed


def build_memory_context(memory: dict[str, Any]) -> str:
    context_lines = []

    if memory.get("name"):
        context_lines.append(f"El usuario se llama {memory['name']}.")

    if memory.get("work"):
        context_lines.append(f"El usuario trabaja {memory['work']}.")

    if memory.get("interests"):
        context_lines.append(f"Al usuario le gusta {_format_items(memory['interests'])}.")

    if memory.get("preferences"):
        context_lines.append(
            f"Preferencias conocidas del usuario: {_format_items(memory['preferences'])}."
        )

    if not context_lines:
        return ""

    return "\n".join(context_lines) + "\n\n"


def build_name_response(memory: dict[str, Any]) -> str:
    if memory.get("name"):
        return f"Te llamas {memory['name']}."

    return "Todavía no me dijiste tu nombre."


def build_work_response(memory: dict[str, Any]) -> str:
    if memory.get("work"):
        return f"Tengo guardado que trabajas {memory['work']}."

    return "Todavía no me dijiste en qué trabajas."


def build_likes_response(memory: dict[str, Any]) -> str:
    if memory.get("interests"):
        return f"Te gusta {_format_items(memory['interests'])}."

    return "Todavía no tengo gustos tuyos guardados."


def build_preferences_response(memory: dict[str, Any]) -> str:
    if memory.get("preferences"):
        return f"Tus preferencias guardadas son: {_format_items(memory['preferences'])}."

    return "Todavía no tengo preferencias tuyas guardadas."


def build_memory_response(memory: dict[str, Any], memory_intent: str | None) -> str:
    if memory_intent == MEMORY_INTENT_NAME:
        return build_name_response(memory)

    if memory_intent == MEMORY_INTENT_WORK:
        return build_work_response(memory)

    if memory_intent == MEMORY_INTENT_LIKES:
        return build_likes_response(memory)

    if memory_intent == MEMORY_INTENT_PREFERENCES:
        return build_preferences_response(memory)

    return "[sin respuesta]"


def build_ambiguous_memory_response(
    memory: dict[str, Any],
    memory_intent: str | None,
) -> str:
    if memory_intent == MEMORY_INTENT_NAME:
        if memory.get("name"):
            return f"Tengo guardado que te llamas {memory['name']}, pero no quiero asumir más de eso."

        return "No tengo guardado tu nombre con suficiente precisión para responder eso."

    if memory_intent == MEMORY_INTENT_WORK:
        if memory.get("work"):
            return (
                f"Tengo guardado que trabajas {memory['work']}, "
                "pero no tengo más detalle para responder eso con precisión."
            )

        return "No tengo guardado con precisión en qué trabajas."

    if memory_intent == MEMORY_INTENT_LIKES:
        if memory.get("interests"):
            return (
                f"Tengo guardado que te gusta {_format_items(memory['interests'])}, "
                "pero no sé específicamente qué te gusta hacer."
            )

        return "No tengo guardado con precisión qué te gusta hacer."

    if memory_intent == MEMORY_INTENT_PREFERENCES:
        if memory.get("preferences"):
            return (
                f"Tengo guardado que tus preferencias son {_format_items(memory['preferences'])}, "
                "pero no sé específicamente cuál consultas."
            )

        return "No tengo guardado con precisión tus preferencias."

    return "No tengo suficiente memoria para responder eso con precisión."


def build_memory_update_response(user_input: str, memory: dict[str, Any]) -> str:
    memory_update = extract_memory_update(user_input)
    detail_parts = []

    if "name" in memory_update and memory.get("name"):
        detail_parts.append(f"te llamas {memory['name']}")

    if "work" in memory_update and memory.get("work"):
        detail_parts.append(f"trabajas {memory['work']}")

    if "interests" in memory_update:
        detail_parts.append(f"te gusta {_format_items(memory_update['interests'])}")

    if "preferences" in memory_update:
        detail_parts.append(
            f"prefieres {_format_items(memory_update['preferences'])}"
        )

    if not detail_parts:
        return "Anotado."

    return f"Anotado: {'; '.join(detail_parts)}."


def build_repetition_response(user_input: str, memory: dict[str, Any]) -> str:
    memory_update = extract_memory_update(user_input)
    detail_parts = []

    if "name" in memory_update and memory.get("name"):
        detail_parts.append(f"te llamas {memory['name']}")

    if "work" in memory_update and memory.get("work"):
        detail_parts.append(f"trabajas {memory['work']}")

    if "interests" in memory_update:
        detail_parts.append(f"te gusta {_format_items(memory_update['interests'])}")

    if "preferences" in memory_update:
        detail_parts.append(
            f"tus preferencias incluyen {_format_items(memory_update['preferences'])}"
        )

    if not detail_parts:
        return "Eso ya estaba guardado."

    return f"Eso ya estaba guardado: {'; '.join(detail_parts)}."
