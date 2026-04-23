"""
Decision Rules para AURA V0.33 - Decision Engine Optimizado

Heurísticas simples de scoring para evaluar opciones de ruta.
Sin ML, solo reglas claras y predecibles.
"""

from typing import Any, Optional
from .decision_context import DecisionContext, TaskType


# Constantes de configuración
MIN_SCORE_THRESHOLD = 0.3  # Umbral mínimo para aceptar decisión
MAX_DECISION_ATTEMPTS = 2  # Límite de reintentos anti-loop


def evaluate_options(context: DecisionContext) -> list[dict[str, Any]]:
    """
    Evaluar todas las rutas posibles para el contexto.
    
    Returns:
        Lista de opciones con metadata básica.
    """
    options = []
    
    # 1. Tools internas (si aplica)
    if "internal_tools" in context.possible_matches:
        match = context.possible_matches["internal_tools"]
        options.append({
            "route": "internal_tools",
            "capability": _resolve_internal_tools_capability(match["query"]),
            "confidence": match["confidence"],
            "cost": 1,  # Bajo costo
            "relevance": _calculate_relevance(context, "internal_tools"),
            "reason": "Match con tools internas"
        })
    
    # 2. Operaciones (si aplica)
    if "operations" in context.possible_matches:
        match = context.possible_matches["operations"]
        options.append({
            "route": "operations",
            "capability": "internal_operations_catalog",
            "confidence": match["confidence"],
            "cost": 1,
            "relevance": _calculate_relevance(context, "operations"),
            "reason": "Consulta de catálogo de operaciones"
        })
    
    # 3. Capacidades (si aplica)
    if "capabilities" in context.possible_matches:
        match = context.possible_matches["capabilities"]
        options.append({
            "route": "capabilities",
            "capability": "capabilities_catalog",
            "confidence": match["confidence"],
            "cost": 1,
            "relevance": _calculate_relevance(context, "capabilities"),
            "reason": "Consulta de catálogo de capacidades"
        })
    
    # 4. Mantenimiento (si aplica)
    if "maintenance" in context.possible_matches:
        match = context.possible_matches["maintenance"]
        options.append({
            "route": "maintenance",
            "capability": "maintenance",
            "confidence": match["confidence"],
            "cost": 1,
            "relevance": _calculate_relevance(context, "maintenance"),
            "reason": "Comando de mantenimiento"
        })
    
    # 5. Estado del sistema (si aplica)
    if "system_state" in context.possible_matches:
        match = context.possible_matches["system_state"]
        options.append({
            "route": "system_state",
            "capability": "system_state",
            "confidence": match["confidence"],
            "cost": 1,
            "relevance": _calculate_relevance(context, "system_state"),
            "reason": "Consulta de estado del sistema"
        })
    
    # 6. Comandos internos (si aplica)
    if "internal_command" in context.possible_matches:
        match = context.possible_matches["internal_command"]
        route = _resolve_internal_command_route(match["command"])
        options.append({
            "route": route,
            "capability": "internal_command",
            "confidence": match["confidence"],
            "cost": 1,
            "relevance": _calculate_relevance(context, "internal_command"),
            "reason": "Comando interno de memoria"
        })
    
    # 7. Consultas de memoria (si aplica)
    if "memory_query" in context.possible_matches:
        match = context.possible_matches["memory_query"]
        route, capability = _resolve_memory_route_capability(match["question"])
        options.append({
            "route": route,
            "capability": capability,
            "confidence": match["confidence"],
            "cost": 1,
            "relevance": _calculate_relevance(context, "memory_query"),
            "reason": "Consulta de memoria"
        })
    
    # 8. Actualizaciones de memoria (si aplica)
    if "memory_update" in context.possible_matches:
        match = context.possible_matches["memory_update"]
        options.append({
            "route": "memory_update",
            "capability": "memory_update",
            "confidence": match["confidence"],
            "cost": 1,
            "relevance": _calculate_relevance(context, "memory_update"),
            "reason": "Actualización de memoria"
        })
    
    # 9. Repeticiones (si aplica)
    if "repetition" in context.possible_matches:
        match = context.possible_matches["repetition"]
        options.append({
            "route": "repetition",
            "capability": "repetition",
            "confidence": match["confidence"],
            "cost": 1,
            "relevance": _calculate_relevance(context, "repetition"),
            "reason": "Input repetido"
        })
    
    # 10. Modelo LLM (siempre disponible como fallback)
    options.append({
        "route": "model",
        "capability": "model_response",
        "confidence": 0.3,  # Baja confianza por defecto
        "cost": 10,  # Alto costo (tokens, tiempo)
        "relevance": _calculate_relevance(context, "model"),
        "reason": "Fallback a modelo LLM"
    })
    
    return options


def score_option(option: dict[str, Any], context: DecisionContext) -> float:
    """
    Scoring heurístico simple: confianza * relevancia / costo
    
    Args:
        option: Opción a evaluar
        context: Contexto de decisión
    
    Returns:
        Puntaje normalizado (0.0 - 1.0+)
    """
    confidence = option.get("confidence", 0)
    relevance = option.get("relevance", 0)
    cost = max(option.get("cost", 1), 0.1)  # Evitar división por cero
    
    # Puntaje base
    base_score = (confidence * relevance) / cost
    
    # Bonificaciones/penalizaciones basadas en contexto
    if context.is_deterministic and option["route"] != "model":
        # Preferir rutas determinísticas para tareas determinísticas
        base_score *= 1.5
    
    if option["route"] == "model" and context.is_deterministic:
        # Penalizar modelo para tareas determinísticas
        base_score *= 0.3
    
    # Bonificación por alta confianza
    if confidence > 0.8:
        base_score *= 1.2
    
    # Bonificación por bajo costo
    if cost <= 1:
        base_score *= 1.1
    
    # Penalización por ruta genérica cuando hay matches específicos
    if option["route"] == "model" and len(context.possible_matches) > 0:
        base_score *= 0.5
    
    # Task type boost (multiplicador, no suma)
    task_boost = 1.0
    if context.task_type == TaskType.MEMORY and "memory" in option["route"]:
        # Solo boost si hay datos reales en memoria
        memory_match = context.possible_matches.get("memory_query", {})
        if memory_match.get("data_exists", False):
            task_boost = 1.5          # Memoria con datos → +50%
        else:
            task_boost = 0.8          # Memoria sin datos → penalizar
    elif context.task_type == TaskType.COMMAND and option["route"] in (
        "internal_tools", "maintenance", "system_state"
    ):
        task_boost = 1.5          # Comando + tool → +50%
    elif context.task_type == TaskType.CONVERSATION and option["route"] == "model":
        task_boost = 1.2          # Diálogo + modelo → +20%
    
    base_score *= task_boost
    
    return round(base_score, 2)


def select_best_option(
    scored_options: list[dict[str, Any]], 
    context: DecisionContext
) -> dict[str, Any]:
    """
    Seleccionar la mejor opción aplicando umbral mínimo.
    
    Args:
        scored_options: Opciones ya puntuadas
        context: Contexto de decisión
    
    Returns:
        Mejor opción (puede ser fallback seguro si ninguna supera umbral)
    """
    if not scored_options:
        return _safe_fallback_option(context)
    
    # Encontrar la mejor opción por score
    best_option = max(scored_options, key=lambda x: x.get("score", 0))
    best_score = best_option.get("score", 0)
    
    # Aplicar umbral mínimo
    if best_score < MIN_SCORE_THRESHOLD:
        return {
            "route": "model",
            "capability": "model_response",
            "confidence": 0.3,
            "cost": 10,
            "relevance": 0.5,
            "score": 0.3,
            "reason": f"Ninguna opción superó el umbral mínimo ({MIN_SCORE_THRESHOLD})"
        }
    
    return best_option


def _resolve_internal_tools_capability(tools_query) -> str:
    """Resolver capability para tools internas."""
    from .internal_tools_agent import TOOLS_MODE_CATALOG
    from .capabilities_registry import (
        CAPABILITY_INTERNAL_TOOLS_CATALOG,
        CAPABILITY_INTERNAL_TOOLS_ACTIVE
    )
    
    if hasattr(tools_query, 'mode'):
        if tools_query.mode == TOOLS_MODE_CATALOG:
            return CAPABILITY_INTERNAL_TOOLS_CATALOG
    return CAPABILITY_INTERNAL_TOOLS_ACTIVE


def _resolve_internal_command_route(internal_command) -> str:
    """Resolver ruta para comandos internos."""
    if hasattr(internal_command, 'action'):
        if internal_command.action == "forget":
            return "internal_forget"
    return "internal_query"


def _resolve_memory_route_capability(memory_question) -> tuple[str, str]:
    """Resolver ruta y capability para consultas de memoria."""
    from .memory_agent import MEMORY_INTENT_NAME, MEMORY_INTENT_WORK, MEMORY_INTENT_LIKES
    from .capabilities_registry import (
        CAPABILITY_MEMORY_LOOKUP,
        CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS
    )
    
    if memory_question.is_ambiguous:
        return "memory_lookup_ambiguous", CAPABILITY_MEMORY_LOOKUP_AMBIGUOUS
    
    return "memory_lookup", CAPABILITY_MEMORY_LOOKUP


def _calculate_relevance(context: DecisionContext, option_type: str) -> float:
    """
    Calcular relevancia de una opción para el contexto.
    
    Args:
        context: Contexto de decisión
        option_type: Tipo de opción (internal_tools, memory, etc.)
    
    Returns:
        Relevancia normalizada (0.0 - 1.0)
    """
    # Mapeo de tipos de tarea a relevancia de opciones
    task_relevance_map = {
        TaskType.COMMAND: {
            "internal_tools": 0.9,
            "operations": 0.7,
            "capabilities": 0.6,
            "maintenance": 0.8,
            "system_state": 0.7,
            "model": 0.3
        },
        TaskType.QUERY: {
            "operations": 0.8,
            "capabilities": 0.9,
            "memory_query": 0.7,
            "model": 0.6
        },
        TaskType.CONVERSATION: {
            "model": 0.9,
            "memory_query": 0.4,
            "internal_tools": 0.2
        },
        TaskType.MEMORY: {
            "memory_query": 0.9,
            "memory_update": 0.9,
            "repetition": 0.8,
            "internal_command": 0.8,
            "model": 0.2
        },
        TaskType.CALCULATION: {
            "internal_tools": 0.7,  # feasibility/consistency tools
            "model": 0.5
        },
        TaskType.ACTION: {
            "internal_tools": 0.8,
            "model": 0.4
        }
    }
    
    # Obtener relevancia base del mapa
    base_relevance = task_relevance_map.get(
        context.task_type, {}
    ).get(option_type, 0.5)
    
    # Ajustar por intención específica
    if context.intent in ["feasibility_evaluation", "consistency_evaluation"]:
        if option_type == "internal_tools":
            base_relevance = 0.9
    
    # Ajustar por presencia de entidades
    if option_type in ["memory_query", "memory_update"] and context.entities:
        base_relevance = min(base_relevance + 0.2, 1.0)
    
    return round(base_relevance, 2)


def _safe_fallback_option(context: DecisionContext) -> dict[str, Any]:
    """Opción de fallback seguro garantizado."""
    return {
        "route": "model",
        "capability": "model_response",
        "confidence": 0.3,
        "cost": 10,
        "relevance": 0.5,
        "score": 0.3,
        "reason": "Fallback seguro (sin opciones disponibles)"
    }


def should_retry_decision(
    previous_decisions: list[dict[str, Any]],
    current_context: DecisionContext
) -> bool:
    """
    Determinar si se debe reintentar la decisión (anti-loop).
    
    Args:
        previous_decisions: Decisiones anteriores en esta conversación
        current_context: Contexto actual
    
    Returns:
        True si se debe reintentar, False si se debe usar fallback
    """
    # Contar intentos recientes
    recent_attempts = len([
        d for d in previous_decisions[-10:]  # Últimas 10 decisiones
        if d.get("user_input") == current_context.user_input
    ])
    
    # Si supera el límite, no reintentar
    if recent_attempts >= MAX_DECISION_ATTEMPTS:
        return False
    
    # Si la última decisión fue modelo y tenemos matches específicos, reintentar
    if previous_decisions:
        last_decision = previous_decisions[-1]
        if (last_decision.get("route") == "model" and 
            len(current_context.possible_matches) > 0):
            return True
    
    return True