from dataclasses import dataclass
from typing import Any

from memory_store import save_memory
from .text_matching import matches_normalized_command, normalize_command_variants


INTERNAL_ACTION_QUERY = "query"
INTERNAL_ACTION_FORGET = "forget"

INTERNAL_TARGET_ALL = "all"
INTERNAL_TARGET_NAME = "name"
INTERNAL_TARGET_WORK = "work"
INTERNAL_TARGET_INTERESTS = "interests"
INTERNAL_TARGET_PREFERENCES = "preferences"

ALL_MEMORY_QUERY_COMMANDS = normalize_command_variants(
    {
        "que sabes de mi",
        "mostrame mi memoria",
        "muestra mi memoria",
        "mostra mi memoria",
        "muestrame mi memoria",
        "muestra lo que sabes de mi",
        "muestrame lo que sabes de mi",
        "mostrame lo que sabes de mi",
        "resume lo que sabes de mi",
    }
)
PREFERENCES_QUERY_COMMANDS = normalize_command_variants(
    {
        "que preferencias tienes guardadas",
        "que preferencias tenes guardadas",
        "que preferencias tengo guardadas",
        "muestrame mis preferencias",
        "mostrame mis preferencias",
        "muestrame mis preferencias guardadas",
        "mostrame mis preferencias guardadas",
    }
)
INTERESTS_QUERY_COMMANDS = normalize_command_variants(
    {
        "que gustos tengo guardados",
        "que gustos tienes guardados",
        "muestrame mis gustos",
        "mostrame mis gustos",
        "muestrame mis gustos guardados",
        "mostrame mis gustos guardados",
    }
)
WORK_QUERY_COMMANDS = normalize_command_variants(
    {
        "que sabes de mi trabajo",
        "muestrame mi trabajo guardado",
        "mostrame mi trabajo guardado",
    }
)

FORGET_NAME_COMMANDS = normalize_command_variants({"olvida mi nombre"})
FORGET_WORK_COMMANDS = normalize_command_variants({"olvida mi trabajo"})
FORGET_INTERESTS_COMMANDS = normalize_command_variants({"olvida mis gustos"})
FORGET_PREFERENCES_COMMANDS = normalize_command_variants({"olvida mis preferencias"})


@dataclass(frozen=True)
class InternalCommand:
    action: str
    target: str

def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def _build_memory_summary(memory: dict[str, Any]) -> str:
    parts = []

    if memory.get("name"):
        parts.append(f"nombre: {memory['name']}")

    if memory.get("work"):
        parts.append(f"trabajo: {memory['work']}")

    if memory.get("interests"):
        parts.append(f"gustos: {_format_items(memory['interests'])}")

    if memory.get("preferences"):
        parts.append(f"preferencias: {_format_items(memory['preferences'])}")

    if not parts:
        return "Todavía no tengo datos tuyos guardados."

    return f"Tengo guardado esto: {'; '.join(parts)}."


def analyze_internal_command(user_input: str) -> InternalCommand | None:
    if matches_normalized_command(user_input, ALL_MEMORY_QUERY_COMMANDS):
        return InternalCommand(
            action=INTERNAL_ACTION_QUERY,
            target=INTERNAL_TARGET_ALL,
        )

    if matches_normalized_command(user_input, PREFERENCES_QUERY_COMMANDS):
        return InternalCommand(
            action=INTERNAL_ACTION_QUERY,
            target=INTERNAL_TARGET_PREFERENCES,
        )

    if matches_normalized_command(user_input, INTERESTS_QUERY_COMMANDS):
        return InternalCommand(
            action=INTERNAL_ACTION_QUERY,
            target=INTERNAL_TARGET_INTERESTS,
        )

    if matches_normalized_command(user_input, WORK_QUERY_COMMANDS):
        return InternalCommand(
            action=INTERNAL_ACTION_QUERY,
            target=INTERNAL_TARGET_WORK,
        )

    if matches_normalized_command(user_input, FORGET_NAME_COMMANDS):
        return InternalCommand(
            action=INTERNAL_ACTION_FORGET,
            target=INTERNAL_TARGET_NAME,
        )

    if matches_normalized_command(user_input, FORGET_WORK_COMMANDS):
        return InternalCommand(
            action=INTERNAL_ACTION_FORGET,
            target=INTERNAL_TARGET_WORK,
        )

    if matches_normalized_command(user_input, FORGET_INTERESTS_COMMANDS):
        return InternalCommand(
            action=INTERNAL_ACTION_FORGET,
            target=INTERNAL_TARGET_INTERESTS,
        )

    if matches_normalized_command(user_input, FORGET_PREFERENCES_COMMANDS):
        return InternalCommand(
            action=INTERNAL_ACTION_FORGET,
            target=INTERNAL_TARGET_PREFERENCES,
        )

    return None


def _build_query_response(command: InternalCommand, memory: dict[str, Any]) -> str:
    if command.target == INTERNAL_TARGET_ALL:
        return _build_memory_summary(memory)

    if command.target == INTERNAL_TARGET_NAME:
        if memory.get("name"):
            return f"Tengo guardado que te llamas {memory['name']}."

        return "No tengo tu nombre guardado."

    if command.target == INTERNAL_TARGET_WORK:
        if memory.get("work"):
            return f"Tengo guardado que trabajas {memory['work']}."

        return "No tengo tu trabajo guardado."

    if command.target == INTERNAL_TARGET_INTERESTS:
        if memory.get("interests"):
            return f"Tengo guardado que te gusta {_format_items(memory['interests'])}."

        return "No tengo gustos tuyos guardados."

    if command.target == INTERNAL_TARGET_PREFERENCES:
        if memory.get("preferences"):
            return (
                "Tengo guardadas estas preferencias: "
                f"{_format_items(memory['preferences'])}."
            )

        return "No tengo preferencias tuyas guardadas."

    return "No encontré nada útil para mostrarte."


def _forget_name(memory: dict[str, Any]) -> bool:
    if not memory.get("name"):
        return False

    memory["name"] = ""
    return True


def _forget_work(memory: dict[str, Any]) -> bool:
    if not memory.get("work"):
        return False

    memory["work"] = ""
    return True


def _forget_interests(memory: dict[str, Any]) -> bool:
    if not memory.get("interests"):
        return False

    memory["interests"] = []
    return True


def _forget_preferences(memory: dict[str, Any]) -> bool:
    if not memory.get("preferences"):
        return False

    memory["preferences"] = []
    return True


def _execute_forget(command: InternalCommand, memory: dict[str, Any], memory_file: str) -> str:
    if command.target == INTERNAL_TARGET_NAME:
        if not _forget_name(memory):
            return "No tenía guardado tu nombre."

        save_memory(memory, memory_file)
        return "Listo, olvidé tu nombre."

    if command.target == INTERNAL_TARGET_WORK:
        if not _forget_work(memory):
            return "No tenía guardado tu trabajo."

        save_memory(memory, memory_file)
        return "Listo, olvidé tu trabajo."

    if command.target == INTERNAL_TARGET_INTERESTS:
        if not _forget_interests(memory):
            return "No tenía guardados tus gustos."

        save_memory(memory, memory_file)
        return "Listo, olvidé tus gustos."

    if command.target == INTERNAL_TARGET_PREFERENCES:
        if not _forget_preferences(memory):
            return "No tenía guardadas tus preferencias."

        save_memory(memory, memory_file)
        return "Listo, olvidé tus preferencias."

    return "No hice cambios en tu memoria."


def execute_internal_command(
    command: InternalCommand,
    memory: dict[str, Any],
    memory_file: str,
) -> str:
    if command.action == INTERNAL_ACTION_QUERY:
        return _build_query_response(command, memory)

    if command.action == INTERNAL_ACTION_FORGET:
        return _execute_forget(command, memory, memory_file)

    return "No entendí ese comando interno."
