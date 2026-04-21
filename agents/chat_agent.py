from dataclasses import dataclass

from .text_matching import normalize_internal_text, sanitize_visible_text


EXIT_COMMANDS = {"salir", "exit", "/exit"}


@dataclass(frozen=True)
class UserTurn:
    raw: str
    text: str
    normalized: str
    is_empty: bool
    should_exit: bool


def process_user_input(user_input_raw: str) -> UserTurn:
    sanitized_raw = sanitize_visible_text(user_input_raw)
    text = sanitized_raw.strip()
    normalized = normalize_internal_text(text)

    return UserTurn(
        raw=text,
        text=text,
        normalized=normalized,
        is_empty=not text,
        should_exit=normalized in EXIT_COMMANDS,
    )
