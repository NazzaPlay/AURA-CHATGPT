"""
Decision Engine para AURA V0.33 - Optimización del Loop de Ejecución

Capa principal de análisis y scoring que decide qué ruta usar
antes de delegar a router_agent para ejecución.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from .decision_context import DecisionContext
from .decision_rules import (
    evaluate_options,
    score_option,
    select_best_option,
    should_retry_decision,
    MIN_SCORE_THRESHOLD
)


@dataclass
class DecisionAnalysis:
    """Análisis completo de decisión para un turno."""
    task_type: str
    intent: str
    is_deterministic: bool
    options: list[dict[str, Any]]  # Opciones evaluadas con scores
    selected_route: str
    selected_capability: str
    decision_reason: str
    confidence_score: float
    context_summary: dict[str, Any]  # Resumen del contexto


# Estado global para control de reintentos
_decision_history: list[dict[str, Any]] = []
_MAX_HISTORY_SIZE = 50


def analyze_decision(
    user_input: str,
    conversation: list[dict[str, Any]],
    memory: dict[str, Any]
) -> DecisionAnalysis:
    """
    Analizar el input del usuario y decidir la mejor ruta.
    
    Args:
        user_input: Input del usuario
        conversation: Historial de conversación
        memory: Memoria del usuario
    
    Returns:
        Análisis completo de decisión
    """
    # 1. Construir contexto
    context = DecisionContext.from_input(user_input, conversation, memory)
    
    # 2. Verificar si debemos reintentar (anti-loop)
    if not should_retry_decision(_decision_history, context):
        return _safe_fallback_analysis(context, "Límite de reintentos alcanzado")
    
    # 3. Evaluar todas las opciones posibles
    options = evaluate_options(context)
    
    # 4. Aplicar scoring heurístico a cada opción
    scored_options = []
    for option in options:
        score = score_option(option, context)
        scored_option = {**option, "score": score}
        scored_options.append(scored_option)
    
    # 5. Seleccionar mejor opción aplicando umbral mínimo
    best_option = select_best_option(scored_options, context)
    
    # 6. Registrar decisión en historial
    _record_decision(context, best_option, scored_options)
    
    # 7. Logging estructurado mínimo
    _log_decision(context, best_option)
    
    # 8. Construir análisis completo
    return DecisionAnalysis(
        task_type=context.task_type.value,
        intent=context.intent,
        is_deterministic=context.is_deterministic,
        options=scored_options,
        selected_route=best_option["route"],
        selected_capability=best_option["capability"],
        decision_reason=best_option.get("reason", ""),
        confidence_score=best_option.get("score", 0),
        context_summary=_build_context_summary(context)
    )


def _record_decision(
    context: DecisionContext,
    best_option: dict[str, Any],
    all_options: list[dict[str, Any]]
) -> None:
    """Registrar decisión en historial para control de reintentos."""
    decision_record = {
        "timestamp": datetime.now().isoformat(),
        "user_input": context.user_input,
        "task_type": context.task_type.value,
        "selected_route": best_option["route"],
        "score": best_option.get("score", 0),
        "reason": best_option.get("reason", ""),
        "options_count": len(all_options),
        "has_matches": len(context.possible_matches) > 0
    }
    
    _decision_history.append(decision_record)
    
    # Mantener historial dentro del límite
    if len(_decision_history) > _MAX_HISTORY_SIZE:
        _decision_history.pop(0)


def _log_decision(context: DecisionContext, best_option: dict[str, Any]) -> None:
    """Logging estructurado mínimo para debugging.
    NOTA: chosen_route refleja la decisión del Engine en esta etapa.
    core_agent.py:_resolve_direct_response_route() puede sobrescribir
    'model' por 'heuristic_response' si behavior_agent entrega direct_response.
    TurnMetadata final tiene la ruta correcta."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "task_type": context.task_type.value,
        "chosen_route": best_option["route"],
        "score": best_option.get("score", 0),
        "reason": best_option.get("reason", "")[:100],  # truncar
        "has_matches": len(context.possible_matches) > 0,
        "is_deterministic": context.is_deterministic
    }
    
    # Log simple a stdout (puede extenderse a archivo)
    print(f"[DECISION_ENGINE] {json.dumps(log_entry, ensure_ascii=False)}")


def _build_context_summary(context: DecisionContext) -> dict[str, Any]:
    """Construir resumen del contexto para análisis."""
    return {
        "task_type": context.task_type.value,
        "intent": context.intent,
        "is_deterministic": context.is_deterministic,
        "entities_count": len(context.entities),
        "matches_count": len(context.possible_matches),
        "match_types": list(context.possible_matches.keys()),
        "has_technical_keywords": "technical_keywords" in context.entities
    }


def _safe_fallback_analysis(
    context: DecisionContext,
    reason: str
) -> DecisionAnalysis:
    """Análisis de fallback seguro cuando no se puede tomar decisión."""
    fallback_option = {
        "route": "model",
        "capability": "model_response",
        "confidence": 0.3,
        "cost": 10,
        "relevance": 0.5,
        "score": 0.3,
        "reason": reason
    }
    
    # Log del fallback
    print(f"[DECISION_ENGINE_FALLBACK] {reason}")
    
    return DecisionAnalysis(
        task_type=context.task_type.value,
        intent=context.intent,
        is_deterministic=context.is_deterministic,
        options=[fallback_option],
        selected_route="model",
        selected_capability="model_response",
        decision_reason=reason,
        confidence_score=0.3,
        context_summary=_build_context_summary(context)
    )


def get_decision_history() -> list[dict[str, Any]]:
    """Obtener historial de decisiones (para debugging)."""
    return _decision_history.copy()


def clear_decision_history() -> None:
    """Limpiar historial de decisiones (para testing)."""
    global _decision_history
    _decision_history = []


def get_decision_stats() -> dict[str, Any]:
    """Obtener estadísticas de decisiones."""
    if not _decision_history:
        return {"total": 0, "by_route": {}, "avg_score": 0}
    
    total = len(_decision_history)
    
    # Conteo por ruta
    by_route = {}
    for decision in _decision_history:
        route = decision["selected_route"]
        by_route[route] = by_route.get(route, 0) + 1
    
    # Score promedio
    scores = [d.get("score", 0) for d in _decision_history if "score" in d]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "total": total,
        "by_route": by_route,
        "avg_score": round(avg_score, 2),
        "threshold_violations": len([
            d for d in _decision_history 
            if d.get("score", 0) < MIN_SCORE_THRESHOLD
        ])
    }


# Funciones de utilidad para integración con sistema existente
def should_use_model_directly(user_input: str, memory: dict[str, Any]) -> bool:
    """
    Determinar si se debe usar el modelo directamente (shortcut para casos simples).
    
    Esta función permite optimizaciones cuando sabemos que el modelo es
    la mejor opción sin análisis completo.
    """
    from .behavior_agent import classify_user_intent
    
    intent = classify_user_intent(user_input)
    
    # Intenciones que siempre requieren modelo
    model_intents = {"open", "general", "technical_explain"}
    
    if intent in model_intents:
        return True
    
    # Diálogos abiertos sin entidades específicas
    if "?" in user_input and len(user_input) > 20:
        from .memory_agent import extract_entities
        entities = extract_entities(user_input, memory)
        if not entities:
            return True
    
    return False


def get_recommended_fallback_chain(
    selected_route: str,
    context: DecisionContext
) -> list[tuple[str, str]]:
    """
    Obtener cadena de fallback recomendada para una ruta.
    
    Returns:
        Lista de (route, capability) en orden de fallback
    """
    # Mapeo de fallback por ruta primaria
    fallback_chains = {
        "internal_tools": [
            ("operations", "internal_operations_catalog"),
            ("capabilities", "capabilities_catalog"),
            ("model", "model_response")
        ],
        "operations": [
            ("capabilities", "capabilities_catalog"),
            ("internal_tools", "internal_tools_catalog"),
            ("model", "model_response")
        ],
        "capabilities": [
            ("operations", "internal_operations_catalog"),
            ("internal_tools", "internal_tools_catalog"),
            ("model", "model_response")
        ],
        "memory_lookup": [
            ("memory_lookup_ambiguous", "memory_lookup_ambiguous"),
            ("model", "model_response")
        ],
        "memory_update": [
            ("repetition", "repetition"),
            ("model", "model_response")
        ],
        "maintenance": [
            ("system_state", "system_state"),
            ("model", "model_response")
        ],
        "system_state": [
            ("maintenance", "maintenance"),
            ("model", "model_response")
        ]
    }
    
    # Cadena por defecto (para modelo o rutas no mapeadas)
    default_chain = [("model", "model_response")]
    
    return fallback_chains.get(selected_route, default_chain)