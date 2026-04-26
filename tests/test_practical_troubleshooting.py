"""
Tests para Practical Troubleshooting Response Patterns (V0.33.5)

Verifica que behavior_agent.py detecte y responda correctamente a
consultas prácticas de troubleshooting sin pasar por el modelo.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.behavior_agent import (
    plan_behavior_for_input,
    _build_practical_troubleshoot_response,
    _build_generic_troubleshoot_response,
    classify_user_intent,
    INTENT_TECHNICAL_TROUBLESHOOT,
    INTENT_GENERAL,
    INTENT_OPEN,
)


# ============================================================
# Tests de detección de intención
# ============================================================

def test_intent_game_crash():
    """'se me cierra cs2' debe clasificar como technical_troubleshoot."""
    intent = classify_user_intent("se me cierra cs2 sin razón")
    assert intent == INTENT_TECHNICAL_TROUBLESHOOT, (
        f"Esperado INTENT_TECHNICAL_TROUBLESHOOT, obtuvo {intent}"
    )


def test_intent_pc_shutdown():
    """'mi pc se apaga sola' debe clasificar como technical_troubleshoot."""
    intent = classify_user_intent("mi pc se apaga sola")
    assert intent == INTENT_TECHNICAL_TROUBLESHOOT, (
        f"Esperado INTENT_TECHNICAL_TROUBLESHOOT, obtuvo {intent}"
    )


def test_intent_internet_outage():
    """'no me anda internet' debe clasificar como technical_troubleshoot."""
    intent = classify_user_intent("no me anda internet")
    assert intent == INTENT_TECHNICAL_TROUBLESHOOT, (
        f"Esperado INTENT_TECHNICAL_TROUBLESHOOT, obtuvo {intent}"
    )


def test_intent_python_error_still_works():
    """'python me tira error' debe seguir clasificando como technical_troubleshoot."""
    intent = classify_user_intent("python me tira error")
    assert intent == INTENT_TECHNICAL_TROUBLESHOOT, (
        f"Esperado INTENT_TECHNICAL_TROUBLESHOOT, obtuvo {intent}"
    )


def test_intent_normal_chat_not_troubleshoot():
    """'que me recomiendas para aprender python' NO debe ser troubleshoot."""
    intent = classify_user_intent("que me recomiendas para aprender python")
    assert intent != INTENT_TECHNICAL_TROUBLESHOOT, (
        f"No debería ser troubleshoot, obtuvo {intent}"
    )


# ============================================================
# Tests de respuesta directa (plan_behavior_for_input)
# ============================================================

def test_plan_game_crash():
    """plan_behavior_for_input debe retornar direct_response para 'se me cierra cs2'."""
    plan = plan_behavior_for_input("se me cierra cs2 sin razón")
    assert plan.direct_response is not None, (
        "Debe tener direct_response para juego que se cierra"
    )
    assert "juego" in plan.direct_response.lower() or "cs2" in plan.direct_response.lower(), (
        "La respuesta debe mencionar el juego"
    )
    assert "temperatura" in plan.direct_response.lower() or "drivers" in plan.direct_response.lower(), (
        "La respuesta debe incluir pasos de descarte"
    )


def test_plan_pc_shutdown():
    """plan_behavior_for_input debe retornar direct_response para 'mi pc se apaga sola'."""
    plan = plan_behavior_for_input("mi pc se apaga sola")
    assert plan.direct_response is not None, (
        "Debe tener direct_response para PC que se apaga"
    )
    assert "temperatura" in plan.direct_response.lower() or "fuente" in plan.direct_response.lower(), (
        "La respuesta debe mencionar temperatura o fuente"
    )


def test_plan_internet_outage():
    """plan_behavior_for_input debe retornar direct_response para 'no me anda internet'."""
    plan = plan_behavior_for_input("no me anda internet")
    assert plan.direct_response is not None, (
        "Debe tener direct_response para internet caído"
    )
    assert "router" in plan.direct_response.lower() or "ipconfig" in plan.direct_response.lower(), (
        "La respuesta debe mencionar router o ipconfig"
    )


def test_plan_python_error_still_works():
    """plan_behavior_for_input debe retornar direct_response para 'python me tira error'."""
    plan = plan_behavior_for_input("python me tira error")
    assert plan.direct_response is not None, (
        "Debe tener direct_response para error de Python"
    )
    assert "traceback" in plan.direct_response.lower() or "error" in plan.direct_response.lower(), (
        "La respuesta debe mencionar traceback o error"
    )


def test_plan_normal_chat_no_direct_response():
    """plan_behavior_for_input para charla normal NO debe tener direct_response."""
    plan = plan_behavior_for_input("que me cuentas de vos")
    assert plan.direct_response is None, (
        "Charla normal no debe tener direct_response"
    )


def test_plan_technical_question_no_direct_response():
    """plan_behavior_for_input para pregunta técnica normal NO debe tener direct_response."""
    plan = plan_behavior_for_input("como se implementa un patron observer en python")
    assert plan.direct_response is None, (
        "Pregunta técnica normal no debe tener direct_response (va al modelo)"
    )


# ============================================================
# Tests de _build_practical_troubleshoot_response directo
# ============================================================

def test_build_game_crash():
    """_build_practical_troubleshoot_response debe detectar juego que se cierra."""
    result = _build_practical_troubleshoot_response("se me cierra cs2")
    assert result is not None
    assert "Causa probable" in result


def test_build_pc_shutdown():
    """_build_practical_troubleshoot_response debe detectar PC que se apaga."""
    result = _build_practical_troubleshoot_response("mi pc se apaga sola")
    assert result is not None
    assert "Causa probable" in result


def test_build_internet_outage():
    """_build_practical_troubleshoot_response debe detectar internet caído."""
    result = _build_practical_troubleshoot_response("no me anda internet")
    assert result is not None
    assert "Causa probable" in result


def test_build_unrelated_input():
    """_build_practical_troubleshoot_response debe retornar None para input no relacionado."""
    result = _build_practical_troubleshoot_response("que me recomiendas para aprender python")
    assert result is None, (
        "Input no relacionado debe retornar None"
    )


def test_build_python_error():
    """_build_practical_troubleshoot_response debe retornar None para error de Python."""
    result = _build_practical_troubleshoot_response("python me tira error")
    assert result is None, (
        "Error de Python debe ser manejado por _build_generic_troubleshoot_response, no por practical"
    )


# ============================================================
# Tests de _build_generic_troubleshoot_response (no romper)
# ============================================================

def test_generic_python_error():
    """_build_generic_troubleshoot_response debe seguir funcionando para python error."""
    result = _build_generic_troubleshoot_response("python me tira error")
    assert result is not None
    assert "traceback" in result.lower() or "error" in result.lower()


def test_generic_not_python():
    """_build_generic_troubleshoot_response debe retornar None si no es python/error."""
    result = _build_generic_troubleshoot_response("se me cierra cs2")
    assert result is None, (
        "No debe responder a juego que se cierra (no es python/error)"
    )


# ============================================================
# Tests de variantes de input
# ============================================================

def test_variant_game_crash_phrases():
    """Variantes de frases de juego que se cierra deben ser detectadas."""
    phrases = [
        "el juego crashea",
        "tengo tirones en el juego",
        "se me congela el cs2",
        "bajo fps en juegos",
        "pantalla azul jugando",
    ]
    for phrase in phrases:
        result = _build_practical_troubleshoot_response(phrase)
        assert result is not None, f"Frase no detectada: '{phrase}'"


def test_variant_pc_shutdown_phrases():
    """Variantes de frases de PC que se apaga deben ser detectadas."""
    phrases = [
        "la computadora se reinicia sola",
        "se me apaga la pc",
        "mi pc se reinicia sola",
    ]
    for phrase in phrases:
        result = _build_practical_troubleshoot_response(phrase)
        assert result is not None, f"Frase no detectada: '{phrase}'"


def test_variant_internet_phrases():
    """Variantes de frases de internet caído deben ser detectadas."""
    phrases = [
        "el wifi no funciona",
        "sin conexion a internet",
        "no funciona internet",
        "problemas con el router",
    ]
    for phrase in phrases:
        result = _build_practical_troubleshoot_response(phrase)
        assert result is not None, f"Frase no detectada: '{phrase}'"


# ============================================================
# Tests de no falsos positivos
# ============================================================

def test_no_false_positive_greeting():
    """Saludos no deben activar troubleshooting."""
    plan = plan_behavior_for_input("hola")
    assert plan.direct_response is None or "hola" in plan.direct_response.lower(), (
        "Saludo no debe activar troubleshooting"
    )


def test_no_false_positive_gratitude():
    """Agradecimientos no deben activar troubleshooting."""
    plan = plan_behavior_for_input("gracias")
    assert plan.direct_response is None or "nada" in plan.direct_response.lower(), (
        "Agradecimiento no debe activar troubleshooting"
    )


def test_no_false_positive_memory():
    """Consultas de memoria no deben activar troubleshooting."""
    plan = plan_behavior_for_input("que me gusta hacer")
    assert plan.direct_response is None, (
        "Consulta de memoria no debe tener direct_response de troubleshooting"
    )


def test_no_false_positive_capabilities():
    """Consultas de capacidades no deben activar troubleshooting."""
    plan = plan_behavior_for_input("que capacidades tienes")
    # Puede tener direct_response de capabilities, pero no de troubleshooting
    if plan.direct_response:
        assert "Causa probable" not in plan.direct_response, (
            "Consulta de capacidades no debe tener respuesta de troubleshooting"
        )


# ============================================================
# Ejecución directa
# ============================================================

if __name__ == "__main__":
    test_functions = [
        name for name in dir() if name.startswith("test_")
    ]
    passed = 0
    failed = 0
    for name in test_functions:
        func = globals()[name]
        try:
            func()
            print(f"  PASS {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Resultados: {passed} pasaron, {failed} fallaron")
    if failed > 0:
        sys.exit(1)
