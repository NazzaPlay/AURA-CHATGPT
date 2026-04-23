"""
Decision Context para AURA V0.33 - Decision Engine Optimizado

Define el contexto estructurado para la toma de decisiones,
incluyendo tipo de tarea, intención, entidades y matches posibles.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
import re


class TaskType(Enum):
    """Tipos de tarea que puede realizar AURA."""
    COMMAND = "command"        # Comando interno (tools, ops, capabilities)
    QUERY = "query"            # Consulta (memoria, catálogos)
    CONVERSATION = "conversation"  # Diálogo abierto
    MEMORY = "memory"          # Actualización/consulta de memoria
    CALCULATION = "calculation" # Cálculo/feasibility/consistency
    ACTION = "action"          # Acción con tool específica


@dataclass
class DecisionContext:
    """Contexto completo para la toma de decisiones."""
    user_input: str
    normalized_input: str
    conversation: list[dict[str, Any]]
    memory: dict[str, Any]
    task_type: TaskType
    intent: str
    is_deterministic: bool
    entities: dict[str, Any]  # Entidades extraídas
    possible_matches: dict[str, Any]  # Matches con tools/memoria
    
    @classmethod
    def from_input(
        cls,
        user_input: str,
        conversation: list[dict[str, Any]],
        memory: dict[str, Any]
    ) -> "DecisionContext":
        """Construir contexto a partir del input del usuario."""
        # Normalizar input
        normalized_input = _normalize_input(user_input)
        
        # Clasificar tipo de tarea
        task_type = _classify_task_type(user_input, memory)
        
        # Determinar intención (usar behavior_agent existente)
        from .behavior_agent import classify_user_intent
        intent = classify_user_intent(user_input)
        
        # Determinar si es determinístico
        is_deterministic = task_type in {
            TaskType.COMMAND, 
            TaskType.MEMORY, 
            TaskType.CALCULATION,
            TaskType.ACTION
        }
        
        # Extraer entidades
        entities = _extract_entities(user_input, memory)
        
        # Encontrar matches posibles
        possible_matches = _find_possible_matches(user_input, memory, conversation)
        
        return cls(
            user_input=user_input,
            normalized_input=normalized_input,
            conversation=conversation,
            memory=memory,
            task_type=task_type,
            intent=intent,
            is_deterministic=is_deterministic,
            entities=entities,
            possible_matches=possible_matches
        )


def _normalize_input(text: str) -> str:
    """Normalizar texto para comparaciones."""
    # Usar text_matching existente
    from .text_matching import normalize_internal_text
    return normalize_internal_text(text)


def _classify_task_type(user_input: str, memory: dict[str, Any]) -> TaskType:
    """Clasificar el tipo de tarea basado en el input."""
    normalized = _normalize_input(user_input)
    
    # Comandos internos (tools, ops, capabilities)
    if _is_internal_command(normalized):
        return TaskType.COMMAND
    
    # Consultas de memoria
    from .memory_agent import analyze_memory_question, is_memory_update
    if analyze_memory_question(user_input) or is_memory_update(user_input):
        return TaskType.MEMORY
    
    # Cálculos (feasibility, consistency)
    from .feasibility_agent import looks_like_feasibility_statement
    from .consistency_agent import analyze_consistency_query
    if looks_like_feasibility_statement(user_input) or analyze_consistency_query(user_input):
        return TaskType.CALCULATION
    
    # Acciones con tools específicas
    if _looks_like_action(user_input):
        return TaskType.ACTION
    
    # Consultas generales (preguntas)
    if _is_query_like(normalized):
        return TaskType.QUERY
    
    # Diálogo abierto por defecto
    return TaskType.CONVERSATION


def _is_internal_command(normalized_input: str) -> bool:
    """Determinar si el input es un comando interno."""
    # Patrones de comandos internos
    command_patterns = [
        r"^(que|muestra|mostra|haz|revisa|abre|valida|chequea)\s+(tools|herramientas|operaciones|capacidades|estado|memoria)",
        r"^(diagnostico|diagnóstico|chequeo|revision|revisión|resumen)",
        r"^(como estas|estas lista|estas listo|que tan lista|que tan listo)",
        r"^(que puedes hacer|como puedes ayudar|que conviene hacer)",
    ]
    
    for pattern in command_patterns:
        if re.search(pattern, normalized_input, re.IGNORECASE):
            return True
    
    return False


def _looks_like_action(user_input: str) -> bool:
    """Determinar si el input parece una acción con tool específica."""
    # Patrones de acción
    action_keywords = {
        "ejecuta", "corre", "run", "llama", "invoca", "usa", "utiliza",
        "aplica", "implementa", "construye", "crea", "genera"
    }
    
    normalized = _normalize_input(user_input)
    words = set(normalized.split())
    
    return bool(words & action_keywords)


def _is_query_like(normalized_input: str) -> bool:
    """Determinar si el input es una consulta (pregunta)."""
    question_patterns = [
        r"^(que|como|por que|porque|cual|cuales|cuando|donde|quien)\b",
        r"\?$"
    ]
    
    for pattern in question_patterns:
        if re.search(pattern, normalized_input, re.IGNORECASE):
            return True
    
    return False


def _extract_entities(user_input: str, memory: dict[str, Any]) -> dict[str, Any]:
    """Extraer entidades relevantes del input."""
    entities = {}
    
    # Extraer nombre si está presente
    from .memory_agent import extract_name
    name = extract_name(user_input)
    if name:
        entities["name"] = name
    
    # Extraer trabajo si está presente
    from .memory_agent import extract_work
    work = extract_work(user_input)
    if work:
        entities["work"] = work
    
    # Extraer intereses si están presentes
    from .memory_agent import extract_interests
    interests = extract_interests(user_input)
    if interests:
        entities["interests"] = interests
    
    # Extraer preferencias si están presentes
    from .memory_agent import extract_preferences
    preferences = extract_preferences(user_input)
    if preferences:
        entities["preferences"] = preferences
    
    # Keywords técnicas
    technical_keywords = {
        "api", "auth", "cache", "cola", "colas", "backend", "frontend",
        "database", "modelo", "llama", "python", "git", "docker"
    }
    
    normalized = _normalize_input(user_input)
    found_keywords = [kw for kw in technical_keywords if kw in normalized]
    if found_keywords:
        entities["technical_keywords"] = found_keywords
    
    return entities


def _find_possible_matches(
    user_input: str,
    memory: dict[str, Any],
    conversation: list[dict[str, Any]]
) -> dict[str, Any]:
    """Encontrar matches posibles con tools, memoria, etc."""
    matches = {}
    
    # Check tools internas
    from .internal_tools_agent import analyze_internal_tools_query
    tools_match = analyze_internal_tools_query(user_input)
    if tools_match:
        matches["internal_tools"] = {
            "query": tools_match,
            "confidence": 0.8 if tools_match.mode == "catalog" else 0.6
        }
    
    # Check operaciones
    from .operations_agent import analyze_internal_operations_query
    ops_match = analyze_internal_operations_query(user_input)
    if ops_match:
        matches["operations"] = {
            "query": ops_match,
            "confidence": 0.7
        }
    
    # Check capacidades
    from .capabilities_agent import analyze_capabilities_query
    caps_match = analyze_capabilities_query(user_input)
    if caps_match:
        matches["capabilities"] = {
            "query": caps_match,
            "confidence": 0.7
        }
    
    # Check memoria
    from .memory_agent import (
        analyze_memory_question,
        is_memory_update,
        is_memory_update_already_stored
    )
    
    memory_question = analyze_memory_question(user_input)
    if memory_question:
        matches["memory_query"] = {
            "question": memory_question,
            "confidence": 0.9 if not memory_question.is_ambiguous else 0.6
        }
    
    if is_memory_update(user_input):
        matches["memory_update"] = {
            "is_update": True,
            "confidence": 0.8
        }
    
    # Check si es repetición
    if is_memory_update_already_stored(user_input, memory):
        matches["repetition"] = {
            "is_repetition": True,
            "confidence": 0.9
        }
    
    # Check mantenimiento
    from .maintenance_agent import analyze_maintenance_command
    maintenance_match = analyze_maintenance_command(user_input)
    if maintenance_match:
        matches["maintenance"] = {
            "command": maintenance_match,
            "confidence": 0.8
        }
    
    # Check estado del sistema
    from .system_state_agent import analyze_system_state_command
    system_match = analyze_system_state_command(user_input)
    if system_match:
        matches["system_state"] = {
            "command": system_match,
            "confidence": 0.8
        }
    
    # Check comandos internos
    from .internal_commands_agent import analyze_internal_command
    internal_cmd = analyze_internal_command(user_input)
    if internal_cmd:
        matches["internal_command"] = {
            "command": internal_cmd,
            "confidence": 0.9
        }
    
    return matches