import re
import unicodedata


SAFE_TOKEN_CORRECTIONS = {
    "herramientras": "herramientas",
    "heramientas": "herramientas",
    "capasidades": "capacidades",
    "capcidades": "capacidades",
    "pudes": "puedes",
    "pueds": "puedes",
    "tenes": "tienes",
    "vercion": "version",
    "reusme": "resume",
    "muesrame": "muestrame",
    "mostame": "mostrame",
}
LEADING_TEXT_NOISE = "\ufeff\u200b\u2060\x00"
LEADING_TEXT_NOISE_PREFIXES = ("ï»¿", "Ã¯Â»Â¿", "ÃƒÂ¯Ã‚Â»Ã‚Â¿")
COMMON_MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ï»¿", "\ufffd")


def repair_common_mojibake(
    text: str,
    *,
    max_rounds: int = 2,
) -> str:
    repaired = text or ""

    for _ in range(max_rounds):
        if not any(marker in repaired for marker in COMMON_MOJIBAKE_MARKERS):
            break

        recovered = None
        for source_encoding in ("cp1252", "latin-1"):
            try:
                candidate = repaired.encode(source_encoding).decode("utf-8-sig")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue

            if candidate != repaired:
                recovered = candidate
                break

        if recovered is None:
            break

        repaired = recovered

    return repaired


def strip_leading_text_noise(text: str) -> str:
    cleaned = (text or "").lstrip(LEADING_TEXT_NOISE)

    while True:
        matched_prefix = next(
            (
                prefix
                for prefix in LEADING_TEXT_NOISE_PREFIXES
                if cleaned.startswith(prefix)
            ),
            None,
        )
        if matched_prefix is None:
            break
        cleaned = cleaned[len(matched_prefix) :].lstrip(LEADING_TEXT_NOISE)

    return cleaned


def sanitize_visible_text(text: str) -> str:
    cleaned = repair_common_mojibake(text or "")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("\xa0", " ")
    cleaned = cleaned.replace("\ufeff", "")
    cleaned = cleaned.replace("\u200b", "")
    cleaned = cleaned.replace("\u2060", "")
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    return strip_leading_text_noise(cleaned)


def normalize_internal_text(
    text: str,
    token_corrections: dict[str, str] | None = None,
) -> str:
    corrections = dict(SAFE_TOKEN_CORRECTIONS)
    if token_corrections:
        corrections.update(token_corrections)

    visible_text = sanitize_visible_text(text).casefold()
    normalized = unicodedata.normalize("NFKD", visible_text)
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    cleaned = re.sub(r"[^\w\s]", " ", without_accents)
    tokens = cleaned.split()
    corrected_tokens = [corrections.get(token, token) for token in tokens]
    return " ".join(corrected_tokens)


def normalize_lookup_key(
    text: str,
    token_corrections: dict[str, str] | None = None,
) -> str:
    return normalize_internal_text(text, token_corrections=token_corrections)


def normalize_command_variants(
    commands: set[str] | list[str] | tuple[str, ...],
    token_corrections: dict[str, str] | None = None,
) -> set[str]:
    return {
        normalize_internal_text(command, token_corrections=token_corrections)
        for command in commands
    }


def build_normalized_command_family(
    *command_groups: set[str] | list[str] | tuple[str, ...],
    token_corrections: dict[str, str] | None = None,
) -> set[str]:
    family: set[str] = set()

    for group in command_groups:
        family.update(
            normalize_command_variants(group, token_corrections=token_corrections)
        )

    return family


def matches_normalized_command(
    user_input: str,
    normalized_commands: set[str],
    token_corrections: dict[str, str] | None = None,
) -> bool:
    normalized_input = normalize_internal_text(
        user_input,
        token_corrections=token_corrections,
    )
    return normalized_input in normalized_commands


def matches_normalized_command_family(
    user_input: str,
    *normalized_families: set[str],
    token_corrections: dict[str, str] | None = None,
) -> bool:
    normalized_input = normalize_internal_text(
        user_input,
        token_corrections=token_corrections,
    )
    return any(normalized_input in family for family in normalized_families)
