"""Tests para V0.33.4.3 — Fix diagnóstico routing sin tocar RN.

Corrige:
- Importa TOOLS_DIAGNOSTIC_QUERY_COMMANDS real desde agents.internal_tools_agent
- Verifica que analyze_decision("hacer un diagnóstico") → internal_tools
- Verifica que _is_internal_command reconoce "hacer un diagnostico"
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.text_matching import matches_normalized_command
from agents.internal_tools_agent import (
    TOOLS_DIAGNOSTIC_QUERY_COMMANDS,
    analyze_internal_tools_query,
)
from agents.decision_context import _is_internal_command, _classify_task_type, TaskType
from agents.decision_engine import analyze_decision


def test_diagnostic_variants():
    """Test 1: Todas las variantes matchean TOOLS_DIAGNOSTIC_QUERY_COMMANDS real."""
    tests = [
        ("ejecutar diagnostico", True),
        ("ejecutar un diagnostico", True),
        ("correr diagnostico", True),
        ("correr un diagnostico", True),
        ("hacer diagnostico", True),
        ("hacer un diagnostico", True),
        ("ejecutar diagnóstico", True),  # con acento
        ("ejecutar un diagnóstico", True),
        ("correr diagnóstico", True),
        ("hacer diagnóstico", True),
        ("haz un diagnostico interno", True),  # original
        ("mostrame las tools", False),  # no deberia matchear
    ]

    all_passed = True
    for input_text, expected in tests:
        result = matches_normalized_command(input_text, TOOLS_DIAGNOSTIC_QUERY_COMMANDS)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        print(f"  [{status}] \"{input_text}\" -> {result} (expected {expected})")

    assert all_passed, "ALGUNOS TESTS DE VARIANTES FALLARON"
    print("\n  [OK] Todas las variantes de diagnóstico matchean correctamente")


def test_analyze_internal_tools_query():
    """Test 2: analyze_internal_tools_query devuelve InternalToolsQuery para las variantes."""
    variants = [
        "ejecutar diagnóstico",
        "ejecutar un diagnóstico",
        "correr diagnóstico",
        "correr un diagnóstico",
        "hacer diagnóstico",
        "hacer un diagnóstico",
    ]

    all_passed = True
    for variant in variants:
        result = analyze_internal_tools_query(variant)
        if result is None:
            print(f"  [FAIL] \"{variant}\" -> None (expected InternalToolsQuery)")
            all_passed = False
        elif result.mode != "diagnostic":
            print(f"  [FAIL] \"{variant}\" -> mode={result.mode} (expected 'diagnostic')")
            all_passed = False
        else:
            print(f"  [PASS] \"{variant}\" -> mode={result.mode}")

    assert all_passed, "ALGUNOS TESTS DE analyze_internal_tools_query FALLARON"
    print("\n  [OK] analyze_internal_tools_query enruta correctamente todas las variantes")


def test_is_internal_command_reconoce_hacer():
    """Test 3: _is_internal_command reconoce 'hacer un diagnostico' (V0.33.4.3 fix).

    Nota: _is_internal_command recibe texto ya normalizado (sin acentos).
    Por eso pasamos texto sin acentos.
    """
    from agents.text_matching import normalize_internal_text

    tests = [
        ("hacer un diagnostico", True),
        ("hacer diagnostico", True),
        ("ejecutar diagnostico", True),
        ("correr diagnostico", True),
        ("haz un diagnostico interno", True),
        ("como estas", True),  # matchea patron 2: ^(como estas|...)
        ("quien creo a aura", False),
    ]

    all_passed = True
    for input_text, expected in tests:
        result = _is_internal_command(input_text)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        print(f"  [{status}] _is_internal_command({repr(input_text)}) -> {result} (expected {expected})")

    assert all_passed, "ALGUNOS TESTS DE _is_internal_command FALLARON"
    print("\n  [OK] _is_internal_command reconoce correctamente 'hacer un diagnostico'")


def test_classify_task_type_hacer_diagnostico():
    """Test 4: 'hacer un diagnóstico' se clasifica como COMMAND (V0.33.4.3 fix)."""
    result = _classify_task_type("hacer un diagnóstico", {})
    assert result == TaskType.COMMAND, (
        f"Se esperaba TaskType.COMMAND, se obtuvo {result}"
    )
    print(f"  [PASS] _classify_task_type('hacer un diagnóstico') -> {result}")


def test_analyze_decision_hacer_diagnostico():
    """Test 5: analyze_decision('hacer un diagnóstico') selecciona internal_tools."""
    result = analyze_decision("hacer un diagnóstico", [], {})
    assert result.selected_route == "internal_tools", (
        f"Se esperaba route='internal_tools', se obtuvo '{result.selected_route}'"
    )
    assert result.selected_capability == "internal_tools_active", (
        f"Se esperaba capability='internal_tools_active', se obtuvo '{result.selected_capability}'"
    )
    print(f"  [PASS] analyze_decision('hacer un diagnóstico') -> route={result.selected_route}, "
          f"capability={result.selected_capability}, score={result.confidence_score}")


def test_rn_not_touched():
    """Test 6: Confirmar que RN no fue modificado."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "backend/app/routing_neuron/"],
        capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), "..")
    )
    assert result.stdout.strip() == "", f"RN fue modificado: {result.stdout}"
    print("  [OK] RN no fue modificado")


if __name__ == "__main__":
    print("=" * 60)
    print("Tests V0.33.4.3 — Fix diagnóstico routing")
    print("=" * 60)

    print("\n--- Test 1: Variantes de diagnóstico (set real) ---")
    test_diagnostic_variants()

    print("\n--- Test 2: analyze_internal_tools_query ---")
    test_analyze_internal_tools_query()

    print("\n--- Test 3: _is_internal_command reconoce 'hacer' ---")
    test_is_internal_command_reconoce_hacer()

    print("\n--- Test 4: _classify_task_type -> COMMAND ---")
    test_classify_task_type_hacer_diagnostico()

    print("\n--- Test 5: analyze_decision -> internal_tools ---")
    test_analyze_decision_hacer_diagnostico()

    print("\n--- Test 6: RN no tocado ---")
    test_rn_not_touched()

    print("\n" + "=" * 60)
    print("[OK] TODOS LOS TESTS PASARON")
    print("=" * 60)
