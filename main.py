import json
from pathlib import Path
import sys

from backend.app.routing_neuron.control import ensure_codex_control_registry
from agents.core_agent import execute_turn, prepare_turn
from agents.memory_agent import migrate_memory
from agents.model_registry import (
    ROLE_PRIMARY,
    build_default_model_registry,
    build_stack_health_snapshot,
)
from config import (
    AURA_VERSION,
    LLAMA_PATH,
    MEMORY_FILE,
    MODEL_PATH,
    build_log_file,
    get_active_runtime_overrides,
    list_model_artifacts,
)
from memory_store import load_memory, save_memory


def save_log(conversation, log_file):
    if not conversation:
        return

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=2, ensure_ascii=False)


def _configure_console_streams() -> None:
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except ValueError:
            continue


def _is_interactive_session() -> bool:
    stdin_isatty = bool(getattr(sys.stdin, "isatty", lambda: False)())
    stdout_isatty = bool(getattr(sys.stdout, "isatty", lambda: False)())
    return stdin_isatty and stdout_isatty


def _read_next_user_input(*, interactive_mode: bool) -> str | None:
    if interactive_mode:
        return input("Tu: ")

    raw_line = sys.stdin.readline()
    if raw_line == "":
        return None

    return raw_line.rstrip("\r\n")


def _build_startup_lines(llama_path: str, model_path: str) -> tuple[str, ...]:
    registry = build_default_model_registry(
        llama_path=llama_path,
        model_path=model_path,
    )
    primary_provider = registry.get_provider_for_role(ROLE_PRIMARY)
    primary_descriptor = primary_provider.descriptor if primary_provider is not None else None
    stack_health = build_stack_health_snapshot(registry)
    model_root = Path(model_path).expanduser().resolve(strict=False).parent
    model_bank_count = len(list_model_artifacts(model_root))
    override_names = [
        override.split("=", 1)[0]
        for override in get_active_runtime_overrides()
    ]

    lines = [
        f"AURA V{AURA_VERSION} iniciada.",
        (
            "Stack: "
            f"health {stack_health.health}, pressure {stack_health.fallback_pressure}, "
            f"providers {stack_health.available_provider_count}/{stack_health.total_provider_count} usables."
        ),
        (
            "Primary: "
            f"{primary_descriptor.model_id if primary_descriptor and primary_descriptor.model_id else Path(model_path).name} "
            f"en {primary_descriptor.model_path if primary_descriptor and primary_descriptor.model_path else model_path}."
        ),
        f"Runner: {llama_path}.",
        f"Banco detectado en {model_root}: {model_bank_count} artefactos.",
    ]

    if override_names:
        lines.append(f"Overrides activas: {', '.join(override_names)}.")
    else:
        lines.append(
            "Overrides activas: ninguna. Puedes forzar runner con "
            "AURA_PRIMARY_LLAMA_PATH/AURA_LLAMA_PATH y modelo con "
            "AURA_PRIMARY_MODEL_PATH/AURA_MODEL_PATH."
        )

    if primary_descriptor is not None and not primary_descriptor.availability:
        reason = primary_descriptor.availability_reason or "unknown"
        lines.append(f"Aviso: el provider primario no esta usable ahora ({reason}).")

    return tuple(lines)


def main():
    _configure_console_streams()
    ensure_codex_control_registry()
    log_file = build_log_file()
    memory = load_memory(MEMORY_FILE)
    conversation = []
    interactive_mode = _is_interactive_session()

    if migrate_memory(memory):
        save_memory(memory, MEMORY_FILE)

    if interactive_mode:
        for line in _build_startup_lines(LLAMA_PATH, MODEL_PATH):
            print(line)
        print()

    while True:
        try:
            user_input = _read_next_user_input(interactive_mode=interactive_mode)
            if user_input is None:
                save_log(conversation, log_file)
                save_memory(memory, MEMORY_FILE)
                break

            turn_plan = prepare_turn(
                user_input,
                conversation=conversation,
                memory=memory,
            )
            if turn_plan is None:
                continue

            turn_result = execute_turn(
                turn_plan,
                conversation=conversation,
                memory=memory,
                memory_file=MEMORY_FILE,
                log_file=log_file,
                llama_path=LLAMA_PATH,
                model_path=MODEL_PATH,
                aura_version=AURA_VERSION,
            )

            if turn_result.should_exit:
                save_log(conversation, log_file)
                save_memory(memory, MEMORY_FILE)
                if interactive_mode:
                    print("AURA: sesion guardada. Chau.")
                break

            if interactive_mode:
                print(f"AURA: {turn_result.response}\n")
            else:
                print(turn_result.response)
            save_log(conversation, log_file)

        except EOFError:
            save_log(conversation, log_file)
            save_memory(memory, MEMORY_FILE)
            if interactive_mode:
                print("\n[INFO] Entrada finalizada. Guardando sesion...")
                print("AURA: sesion guardada. Chau.")
            break
        except KeyboardInterrupt:
            save_log(conversation, log_file)
            save_memory(memory, MEMORY_FILE)
            if interactive_mode:
                print("\n[INFO] Guardando sesion...")
                print("AURA: Chau.")
            break


if __name__ == "__main__":
    main()
