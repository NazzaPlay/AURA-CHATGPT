"""Tests para V0.33.4.2 — Fix diagnóstico routing sin tocar RN."""
import sys
sys.path.insert(0, "a:\\AURA\\project")

from agents.text_matching import matches_normalized_command, normalize_command_variants

TOOLS_DIAGNOSTIC_QUERY_COMMANDS = normalize_command_variants(
    {
        "haz un diagnostico interno",
        "ejecutar diagnostico",
        "ejecutar un diagnostico",
        "correr diagnostico",
        "correr un diagnostico",
        "hacer diagnostico",
        "hacer un diagnostico",
    }
)

from agents.internal_tools_agent import analyze_internal_tools_query


def test_diagnostic_variants():
    """Test 1: Todas las variantes matchean TOOLS_DIAGNOSTIC_QUERY_COMMANDS."""
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
    print("\n  ✅ Todas las variantes de diagnóstico matchean correctamente")


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
    print("\n  ✅ analyze_internal_tools_query enruta correctamente todas las variantes")


def test_rn_not_touched():
    """Test 3: Confirmar que RN no fue modificado."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "backend/app/routing_neuron/"],
        capture_output=True, text=True, cwd="a:\\AURA\\project"
    )
    assert result.stdout.strip() == "", f"RN fue modificado: {result.stdout}"
    print("  ✅ RN no fue modificado")


if __name__ == "__main__":
    print("=" * 60)
    print("Tests V0.33.4.2 — Fix diagnóstico routing")
    print("=" * 60)

    print("\n--- Test 1: Variantes de diagnóstico ---")
    test_diagnostic_variants()

    print("\n--- Test 2: analyze_internal_tools_query ---")
    test_analyze_internal_tools_query()

    print("\n--- Test 3: RN no tocado ---")
    test_rn_not_touched()

    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)
