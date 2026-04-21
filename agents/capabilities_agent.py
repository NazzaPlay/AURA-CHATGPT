from dataclasses import dataclass

from .text_matching import matches_normalized_command, normalize_command_variants

CAPABILITIES_QUERY_COMMANDS = normalize_command_variants(
    {
        "que capacidades tienes",
        "muestra tus capacidades",
        "muestrame tus capacidades",
        "mostra tus capacidades",
        "mostrame tus capacidades",
        "que puedes hacer",
        "muestra que puedes hacer",
        "mostra que puedes hacer",
        "muestrame que puedes hacer",
        "mostrame que puedes hacer",
        "muestra lo que puedes hacer",
        "muestrame lo que puedes hacer",
        "mostra lo que puedes hacer",
        "mostrame lo que puedes hacer",
        "como me puedes ayudar",
        "como me puedes ayudar ahora",
        "como me podes ayudar",
        "como me podes ayudar ahora",
    }
)


@dataclass(frozen=True)
class CapabilitiesQuery:
    scope: str = "all"


def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def _clean_description(description: str) -> str:
    return description.strip().rstrip(".")


def analyze_capabilities_query(user_input: str) -> CapabilitiesQuery | None:
    if matches_normalized_command(user_input, CAPABILITIES_QUERY_COMMANDS):
        return CapabilitiesQuery()

    return None


def build_capabilities_response() -> str:
    from .capabilities_registry import (
        CAPABILITIES_REGISTRY,
        CAPABILITY_CAPABILITIES_CATALOG,
        CAPABILITY_EXIT,
        CAPABILITY_INTERNAL_COMMAND,
        CAPABILITY_INTERNAL_OPERATIONS_CATALOG,
        CAPABILITY_INTERNAL_TOOLS_ACTIVE,
        CAPABILITY_MAINTENANCE,
        CAPABILITY_MEMORY_LOOKUP,
        CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS,
        CAPABILITY_MEMORY_UPDATE,
        CAPABILITY_MODEL_RESPONSE,
        CAPABILITY_REPETITION,
        CAPABILITY_SYSTEM_STATE,
    )

    active_capabilities = {
        capability_name: definition
        for capability_name, definition in CAPABILITIES_REGISTRY.items()
        if capability_name != CAPABILITY_EXIT
    }

    if not active_capabilities:
        return "No tengo capacidades registradas para mostrar ahora."

    response_parts: list[str] = []

    if CAPABILITY_CAPABILITIES_CATALOG in active_capabilities:
        response_parts.append("ayuda del sistema")

    if CAPABILITY_INTERNAL_TOOLS_ACTIVE in active_capabilities:
        response_parts.append("tools activas del núcleo")

    memory_parts: list[str] = []
    if CAPABILITY_MEMORY_UPDATE in active_capabilities:
        memory_parts.append("guardar datos tuyos")
    if (
        CAPABILITY_MEMORY_LOOKUP in active_capabilities
        or CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS in active_capabilities
    ):
        memory_parts.append("recordar lo que sé de ti")
    if CAPABILITY_INTERNAL_COMMAND in active_capabilities:
        memory_parts.append("mostrar u olvidar memoria")
    if CAPABILITY_REPETITION in active_capabilities:
        memory_parts.append("detectar datos repetidos")
    if memory_parts:
        response_parts.append(f"memoria del usuario ({_format_items(memory_parts)})")

    if CAPABILITY_SYSTEM_STATE in active_capabilities:
        response_parts.append("estado interno")

    if CAPABILITY_MAINTENANCE in active_capabilities:
        response_parts.append("mantenimiento")

    if CAPABILITY_MODEL_RESPONSE in active_capabilities:
        response_parts.append("modelo local cuando hace falta")

    examples = []
    for capability_name in (
        CAPABILITY_CAPABILITIES_CATALOG,
        CAPABILITY_SYSTEM_STATE,
        CAPABILITY_MAINTENANCE,
    ):
        definition = active_capabilities.get(capability_name)
        if not definition:
            continue
        examples.extend(definition.examples[:1])

    examples_text = _format_items([f'"{example}"' for example in examples[:3]])
    response = (
        "Mis capacidades son áreas generales del sistema: "
        + _format_items(response_parts)
        + ". Si quieres bajar un nivel, puedo mostrarte operaciones concretas o tools internas reales."
    )
    if examples_text:
        response += f" Ejemplos rápidos: {examples_text}."

    return response
