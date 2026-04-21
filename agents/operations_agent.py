from dataclasses import dataclass

from .internal_tools_registry import (
    TOOL_COMPOSITE_DIAGNOSTICS,
    TOOL_COMPOSITE_REVIEWS,
    TOOL_HELP_CATALOGS,
    TOOL_LOCAL_MODEL_RUNTIME,
    TOOL_MAINTENANCE_CONSOLE,
    TOOL_SESSION_CONTROL,
    TOOL_SYSTEM_STATE_READER,
    TOOL_USER_MEMORY,
    get_internal_tools_in_order,
)
from .text_matching import matches_normalized_command, normalize_command_variants


OPERATIONS_INVENTORY_QUERY_COMMANDS = normalize_command_variants(
    {
        "que operaciones internas tienes",
        "que operaciones internas puede ejecutar",
        "que operaciones internas puedes ejecutar",
        "que operaciones internas puede hacer",
        "que operaciones internas puedes hacer",
        "que operaciones puede ejecutar",
        "que operaciones puedes ejecutar",
        "que operaciones puede hacer",
        "que operaciones puedes hacer",
        "que acciones internas puede ejecutar",
        "que acciones internas puedes ejecutar",
        "que acciones internas puede hacer",
        "que acciones internas puedes hacer",
        "que acciones puede ejecutar",
        "que acciones puedes ejecutar",
        "que acciones puedes hacer",
        "muestra tus operaciones",
        "muestra tus operaciones internas",
        "muestrame tus operaciones",
        "muestrame tus operaciones internas",
        "mostra tus operaciones",
        "mostra tus operaciones internas",
        "mostrame tus operaciones",
        "mostrame tus operaciones internas",
        "muestra tus acciones internas",
        "muestrame tus acciones internas",
        "mostra tus acciones internas",
        "mostrame tus acciones internas",
    }
)
OPERATIONS_PRACTICAL_QUERY_COMMANDS = normalize_command_variants(
    {
        "como puedo operarte",
        "como te puedo operar",
        "que puedes hacer ahora mismo",
    }
)


@dataclass(frozen=True)
class InternalOperationsQuery:
    scope: str = "all"
    style: str = "inventory"


def _format_items(items: list[str]) -> str:
    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} y {items[1]}"

    return f"{', '.join(items[:-1])} y {items[-1]}"


def _dedupe_items(items: list[str]) -> list[str]:
    unique_items: list[str] = []
    seen: set[str] = set()

    for item in items:
        normalized_item = item.strip()
        key = normalized_item.casefold()

        if not normalized_item or key in seen:
            continue

        seen.add(key)
        unique_items.append(normalized_item)

    return unique_items


def _resolve_catalog_label(definition: object) -> str:
    label = str(getattr(definition, "catalog_label", "")).strip()
    if label:
        return label

    description = str(getattr(definition, "description", "")).strip().rstrip(".")
    if description:
        return description[0].lower() + description[1:]

    return "operación interna disponible"


def _build_fallback_summary(definitions: tuple[object, ...], limit: int = 2) -> str:
    labels: list[str] = []

    for definition in definitions:
        label = _resolve_catalog_label(definition)
        if label not in labels:
            labels.append(label)
        if len(labels) >= limit:
            break

    return _format_items(labels)


def _build_tool_inventory_summary(tool_name: str, definitions: tuple[object, ...]) -> str:
    from .internal_actions_registry import (
        ACTION_CAPABILITIES_CATALOG,
        ACTION_INTERNAL_OPERATIONS_CATALOG,
        ACTION_INTERNAL_TOOLS_CONTEXTUAL_HELP,
        ACTION_INTERNAL_TOOLS_DIAGNOSTIC,
        ACTION_INTERNAL_TOOLS_GENERAL_CHECK,
        ACTION_INTERNAL_TOOLS_GENERAL_DIAGNOSTIC,
        ACTION_INTERNAL_TOOLS_FULL_DIAGNOSTIC,
        ACTION_INTERNAL_TOOLS_INTERNAL_REVIEW,
        ACTION_INTERNAL_TOOLS_LIMITATIONS_OVERVIEW,
        ACTION_INTERNAL_TOOLS_MEMORY_AND_STATE_REVIEW,
        ACTION_INTERNAL_TOOLS_OPERATIONAL_REVIEW,
        ACTION_INTERNAL_TOOLS_STRATEGIC_GUIDANCE,
        ACTION_INTERNAL_TOOLS_FEASIBILITY,
        ACTION_INTERNAL_TOOLS_QUICK_CHECK,
        ACTION_INTERNAL_TOOLS_READINESS_GAP,
        ACTION_INTERNAL_TOOLS_SYSTEM_CHECK,
        ACTION_INTERNAL_TOOLS_SITUATIONAL_STATUS,
        ACTION_INTERNAL_TOOLS_CATALOG,
        ACTION_INTERNAL_TOOLS_COMPLETE_REVIEW,
        ACTION_INTERNAL_TOOLS_CONSISTENCY,
        ACTION_INTERNAL_TOOLS_WORK_READINESS,
        ACTION_MAINTENANCE_SHOW_LAST_LOG,
        ACTION_MAINTENANCE_SUMMARIZE_LAST_LOG,
        ACTION_MAINTENANCE_SUMMARIZE_LAST_TURN,
        ACTION_MAINTENANCE_VALIDATE_CONFIG,
        ACTION_MEMORY_UPDATE,
        ACTION_REPETITION,
        ACTION_SYSTEM_LOADED_MEMORY,
        ACTION_SYSTEM_STATE,
    )

    names = {str(getattr(definition, "name", "")).strip() for definition in definitions}
    summary_parts: list[str] = []

    if tool_name == TOOL_HELP_CATALOGS:
        if {
            ACTION_CAPABILITIES_CATALOG,
            ACTION_INTERNAL_OPERATIONS_CATALOG,
            ACTION_INTERNAL_TOOLS_CATALOG,
        }.issubset(names):
            summary_parts.append("mostrar catálogos y ayudas internas")
        else:
            if ACTION_CAPABILITIES_CATALOG in names:
                summary_parts.append("mostrar mis capacidades")
            if ACTION_INTERNAL_OPERATIONS_CATALOG in names:
                summary_parts.append("mostrar mis operaciones disponibles")
            if ACTION_INTERNAL_TOOLS_CATALOG in names:
                summary_parts.append("mostrar mis tools internas")
    elif tool_name == TOOL_USER_MEMORY:
        has_memory_update = ACTION_MEMORY_UPDATE in names
        has_memory_queries = any(name.startswith("memory_lookup") for name in names) or any(
            name.startswith("internal_query") for name in names
        )
        has_memory_forget = any(name.startswith("internal_forget") for name in names)

        if has_memory_update and has_memory_queries and has_memory_forget:
            summary_parts.append("guardar, recordar y olvidar datos tuyos")
        else:
            if has_memory_update:
                summary_parts.append("guardar datos básicos tuyos")
            if has_memory_queries:
                summary_parts.append("recordar y mostrar lo que sé de ti")
            if has_memory_forget:
                summary_parts.append("olvidar memoria guardada si me lo pides")

        if ACTION_REPETITION in names:
            summary_parts.append("detectar datos repetidos")
    elif tool_name == TOOL_SYSTEM_STATE_READER:
        has_system_details = any(name.startswith("system_") for name in names)
        if has_system_details and ACTION_SYSTEM_LOADED_MEMORY in names:
            summary_parts.append(
                "mostrar versión, modelo, rutas, disponibilidad y memoria cargada"
            )
        else:
            if ACTION_SYSTEM_STATE in names:
                summary_parts.append("mostrar mi estado general")
            if has_system_details:
                summary_parts.append("decirte versión, modelo, rutas y disponibilidad")
            if ACTION_SYSTEM_LOADED_MEMORY in names:
                summary_parts.append("mostrar la memoria cargada")
    elif tool_name == TOOL_MAINTENANCE_CONSOLE:
        has_memory_maintenance = any(
            name.startswith("maintenance_review")
            or name.startswith("maintenance_reload")
            or name.startswith("maintenance_clean")
            or name.startswith("maintenance_correct")
            for name in names
        )
        has_turn_or_log_summary = bool(
            {
                ACTION_MAINTENANCE_SHOW_LAST_LOG,
                ACTION_MAINTENANCE_SUMMARIZE_LAST_LOG,
                ACTION_MAINTENANCE_SUMMARIZE_LAST_TURN,
            }
            & names
        )

        if ACTION_MAINTENANCE_VALIDATE_CONFIG in names:
            summary_parts.append("validar la configuración")
        if has_memory_maintenance:
            summary_parts.append("revisar, limpiar o recargar memoria")
        if has_turn_or_log_summary:
            summary_parts.append("mostrar o resumir log y último turno")
    elif tool_name == TOOL_COMPOSITE_DIAGNOSTICS:
        has_diagnostic_suite = bool(
            {
                ACTION_INTERNAL_TOOLS_DIAGNOSTIC,
                ACTION_INTERNAL_TOOLS_GENERAL_CHECK,
                ACTION_INTERNAL_TOOLS_GENERAL_DIAGNOSTIC,
                ACTION_INTERNAL_TOOLS_FULL_DIAGNOSTIC,
                ACTION_INTERNAL_TOOLS_CONTEXTUAL_HELP,
                ACTION_INTERNAL_TOOLS_LIMITATIONS_OVERVIEW,
                ACTION_INTERNAL_TOOLS_READINESS_GAP,
                ACTION_INTERNAL_TOOLS_SITUATIONAL_STATUS,
                ACTION_INTERNAL_TOOLS_QUICK_CHECK,
                ACTION_INTERNAL_TOOLS_SYSTEM_CHECK,
                ACTION_INTERNAL_TOOLS_WORK_READINESS,
            }
            & names
        )
        if has_diagnostic_suite:
            summary_parts.append(
                "hacer diagnósticos, chequeos y secuencias orientadas a objetivo para revisar cómo está el núcleo"
            )
    elif tool_name == TOOL_COMPOSITE_REVIEWS:
        has_review_suite = bool(
            {
                ACTION_INTERNAL_TOOLS_MEMORY_AND_STATE_REVIEW,
                ACTION_INTERNAL_TOOLS_OPERATIONAL_REVIEW,
                ACTION_INTERNAL_TOOLS_INTERNAL_REVIEW,
                ACTION_INTERNAL_TOOLS_COMPLETE_REVIEW,
                ACTION_INTERNAL_TOOLS_STRATEGIC_GUIDANCE,
                ACTION_INTERNAL_TOOLS_FEASIBILITY,
                ACTION_INTERNAL_TOOLS_CONSISTENCY,
            }
            & names
        )
        if has_review_suite:
            summary_parts.append(
                "hacer revisiones, orientar el siguiente foco y evaluar viabilidad, certeza o contradicciones útiles"
            )
    elif tool_name == TOOL_LOCAL_MODEL_RUNTIME:
        summary_parts.append("responder preguntas generales o técnicas cuando hace falta")
    elif tool_name == TOOL_SESSION_CONTROL:
        summary_parts.append("cerrar la sesión")

    summary_parts = _dedupe_items(summary_parts)
    if summary_parts:
        return _format_items(summary_parts)

    return _build_fallback_summary(definitions)


def _build_tool_practical_hint(tool_name: str, definitions: tuple[object, ...]) -> str:
    names = {str(getattr(definition, "name", "")).strip() for definition in definitions}

    if tool_name == TOOL_HELP_CATALOGS and names:
        return "te muestre capacidades, operaciones o tools internas del sistema"

    if tool_name == TOOL_USER_MEMORY and names:
        return "guarde, recuerde u olvide datos tuyos cuando me lo pidas"

    if tool_name == TOOL_SYSTEM_STATE_READER and names:
        return "te diga mi versión, modelo, rutas o memoria cargada"

    if tool_name == TOOL_MAINTENANCE_CONSOLE and names:
        return "valide configuración, revise memoria o resuma el último log o turno"

    if tool_name == TOOL_COMPOSITE_DIAGNOSTICS and names:
        return "haga un diagnóstico, un chequeo general o te diga si estoy lista para trabajar"

    if tool_name == TOOL_COMPOSITE_REVIEWS and names:
        return "haga una revisión de memoria y estado, una revisión operativa o una revisión general priorizada del núcleo"

    if tool_name == TOOL_LOCAL_MODEL_RUNTIME and names:
        return "responda una duda general o técnica con el modelo local"

    if tool_name == TOOL_SESSION_CONTROL and names:
        return "cierre la sesión"

    fallback_summary = _build_fallback_summary(definitions, limit=1)
    if not fallback_summary:
        return ""

    return fallback_summary


def _collect_examples(style: str) -> list[str]:
    from .internal_actions_registry import get_internal_actions_for_tool

    preferred_examples_by_tool = {
        "inventory": {
            TOOL_HELP_CATALOGS: (
                "que capacidades tienes",
                "que operaciones internas tienes",
            ),
            TOOL_SYSTEM_STATE_READER: ("que estado tienes",),
            TOOL_COMPOSITE_DIAGNOSTICS: ("haz un chequeo general",),
            TOOL_COMPOSITE_REVIEWS: ("haz una revision operativa",),
            TOOL_MAINTENANCE_CONSOLE: ("valida tu configuracion",),
        },
        "practical": {
            TOOL_USER_MEMORY: (
                "que sabes de mi",
                "que me gusta?",
            ),
            TOOL_SYSTEM_STATE_READER: ("que estado tienes",),
            TOOL_COMPOSITE_DIAGNOSTICS: ("que puedes hacer ahora segun tu estado",),
            TOOL_COMPOSITE_REVIEWS: ("haz una revision operativa",),
            TOOL_MAINTENANCE_CONSOLE: (
                "resume el ultimo turno",
                "muestrame el ultimo log",
            ),
            TOOL_HELP_CATALOGS: ("que capacidades tienes",),
        },
    }

    if style == "practical":
        tool_order = (
            TOOL_USER_MEMORY,
            TOOL_SYSTEM_STATE_READER,
            TOOL_MAINTENANCE_CONSOLE,
            TOOL_HELP_CATALOGS,
        )
    else:
        tool_order = (
            TOOL_HELP_CATALOGS,
            TOOL_SYSTEM_STATE_READER,
            TOOL_MAINTENANCE_CONSOLE,
            TOOL_USER_MEMORY,
        )

    examples: list[str] = []
    for tool_name in tool_order:
        definitions = get_internal_actions_for_tool(tool_name)
        if not definitions:
            continue

        preferred_examples = preferred_examples_by_tool.get(style, {}).get(tool_name, ())
        used_preferred_examples = False
        if preferred_examples:
            available_examples = {
                example
                for definition in definitions
                for example in getattr(definition, "examples", ())
            }
            for example in preferred_examples:
                if example in available_examples and example not in examples:
                    examples.append(example)
                    used_preferred_examples = True
                if len(examples) >= 3:
                    return examples

        if style == "practical" and used_preferred_examples:
            continue

        for definition in definitions:
            for example in getattr(definition, "examples", ())[:1]:
                if example not in examples:
                    examples.append(example)
                if len(examples) >= 3:
                    return examples

    return examples


def analyze_internal_operations_query(user_input: str) -> InternalOperationsQuery | None:
    if matches_normalized_command(user_input, OPERATIONS_PRACTICAL_QUERY_COMMANDS):
        return InternalOperationsQuery(style="practical")

    if matches_normalized_command(user_input, OPERATIONS_INVENTORY_QUERY_COMMANDS):
        return InternalOperationsQuery(style="inventory")

    return None


def _build_inventory_response() -> str:
    from .internal_actions_registry import get_internal_actions_for_tool

    sections: list[str] = []

    for tool_definition in get_internal_tools_in_order():
        definitions = get_internal_actions_for_tool(tool_definition.name)
        if not definitions:
            continue

        summary = _build_tool_inventory_summary(tool_definition.name, definitions)
        if not summary:
            continue

        sections.append(f"{tool_definition.label.lower()}: {summary}")

    if not sections:
        return "No tengo operaciones internas registradas ahora."

    response = "Estas son mis operaciones concretas por área: "
    response += "; ".join(sections)
    response += "."

    examples = _collect_examples(style="inventory")
    if examples:
        examples_text = _format_items([f'"{example}"' for example in examples[:2]])
        response += f" Ejemplos directos: {examples_text}."

    return response


def _build_practical_response() -> str:
    from .internal_actions_registry import get_internal_actions_for_tool

    suggestions: list[str] = []

    for tool_definition in get_internal_tools_in_order():
        definitions = get_internal_actions_for_tool(tool_definition.name)
        if not definitions:
            continue

        hint = _build_tool_practical_hint(tool_definition.name, definitions)
        if hint:
            suggestions.append(hint)

    suggestions = _dedupe_items(suggestions)
    if not suggestions:
        return "Ahora mismo no tengo operaciones internas listas para usar."

    response = "Si quieres operarme ahora, puedes pedirme que "
    response += _format_items(suggestions)
    response += "."

    examples = _collect_examples(style="practical")
    if examples:
        examples_text = _format_items([f'"{example}"' for example in examples[:3]])
        response += f" Prueba, por ejemplo, {examples_text}."

    return response


def build_internal_operations_response(
    query: InternalOperationsQuery | None = None,
) -> str:
    query = query or InternalOperationsQuery()

    if query.style == "practical":
        return _build_practical_response()

    return _build_inventory_response()
