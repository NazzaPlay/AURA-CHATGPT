import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR_PATH = Path(__file__).resolve().parent
AURA_ROOT_PATH = BASE_DIR_PATH.parent
LOG_DIR_PATH = BASE_DIR_PATH / "logs"
MEMORY_FILE_PATH = BASE_DIR_PATH / "memory.json"
META_DIR_PATH = AURA_ROOT_PATH / "meta"

AURA_VERSION = "0.39.6"
DEFAULT_MODEL_ROOT = Path(
    os.getenv("AURA_MODEL_DIR", str(AURA_ROOT_PATH / "models"))
).expanduser().resolve(strict=False)

SUPPORTED_MODEL_ARTIFACT_SUFFIXES = (
    ".gguf",
    ".safetensors",
    ".bin",
    ".pt",
)

RUNTIME_OVERRIDE_ENV_VARS = (
    "AURA_MODEL_DIR",
    "AURA_MODEL_PATH",
    "AURA_PRIMARY_MODEL_PATH",
    "AURA_CRITIC_MODEL_PATH",
    "AURA_ROUTER_MODEL_PATH",
    "AURA_FALLBACK_MODEL_PATH",
    "AURA_LLAMA_PATH",
    "AURA_PRIMARY_LLAMA_PATH",
    "AURA_CRITIC_LLAMA_PATH",
    "AURA_ROUTER_LLAMA_PATH",
    "AURA_FALLBACK_LLAMA_PATH",
)

PRIMARY_MODEL_NAME = "granite-3.0-1b-a400m-instruct-Q4_K_M.gguf"
CRITIC_MODEL_NAME = "OLMo-2-0425-1B-Instruct-Q4_K_M.gguf"
ROUTER_MODEL_NAME = "smollm2-360m-instruct-q8_0.gguf"
TRANSITIONAL_FALLBACK_MODEL_NAME = "qwen2-1_5b-instruct-q4_k_m.gguf"

PRIMARY_MODEL_ID = "Granite 3.0 1B-A400M-Instruct"
CRITIC_MODEL_ID = "OLMo-2-0425-1B-Instruct"
ROUTER_MODEL_ID = "SmolLM2-360M-Instruct"
TRANSITIONAL_FALLBACK_MODEL_ID = "Qwen2-1.5B-Instruct"
FALLBACK_MODEL_ID = TRANSITIONAL_FALLBACK_MODEL_ID

DEFAULT_MODEL_NAME = PRIMARY_MODEL_NAME
PREFERRED_MODEL_PATH = DEFAULT_MODEL_ROOT / DEFAULT_MODEL_NAME
TRANSITIONAL_MODEL_FAMILY = "qwen2"
TRANSITIONAL_MODEL_ID = TRANSITIONAL_FALLBACK_MODEL_ID
GREEN_MODEL_ALLOWLIST = (
    PRIMARY_MODEL_ID,
    CRITIC_MODEL_ID,
    ROUTER_MODEL_ID,
)

PRIMARY_CALIBRATION_PROFILE = "granite_practical_v0_39_6"
CRITIC_CALIBRATION_PROFILE = "olmo_selective_v0_39_6"
ROUTER_CALIBRATION_PROFILE = "smollm2_sparse_helper_v0_39_6"
FALLBACK_CALIBRATION_PROFILE = "qwen_explicit_fallback_v0_39_6"

ROUTER_HELPER_MAX_INPUT_WORDS = 18
ROUTER_HELPER_MAX_INPUT_CHARS = 140
TECHNICAL_COMPLEXITY_WORD_THRESHOLD = 10

CRITIC_REVIEW_HINTS = (
    "afirmarias",
    "asi nomas",
    "audit",
    "auditar",
    "certeza",
    "claim",
    "claims",
    "comparar",
    "compare",
    "consistente",
    "consistencia",
    "corregir",
    "critica",
    "critico",
    "critic",
    "depende",
    "edge case",
    "garantiza",
    "garantizar",
    "produccion",
    "production",
    "revisa",
    "review",
    "riesgo",
    "riesgos",
    "seguridad",
    "seguro",
    "tradeoff",
    "valida",
    "validar",
    "verifica",
    "verificar",
)

CRITIC_HIGH_RISK_HINTS = (
    "auth",
    "autenticacion",
    "base de datos",
    "configuracion",
    "configurar",
    "credentials",
    "deploy",
    "despliegue",
    "docker",
    "error",
    "exception",
    "fallback",
    "infra",
    "latencia",
    "latency",
    "migracion",
    "production",
    "produccion",
    "rollback",
    "seguridad",
    "traceback",
)

ROUTER_HELPER_TRIGGER_HINTS = (
    "ayudame",
    "ayuda",
    "como lo encararias",
    "cual conviene",
    "explicame",
    "explicá",
    "hola",
    "por donde empiezo",
    "que haria",
    "que harias",
    "que me recomiendas",
    "responde",
    "resumime",
    "resume",
)


def _candidate_path(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()

    if not path.is_absolute():
        path = BASE_DIR_PATH / path

    return path.resolve(strict=False)


def _build_candidates(
    env_var: str,
    *defaults: str | Path,
) -> list[Path]:
    candidates: list[Path] = []
    raw_env_value = os.getenv(env_var)

    if raw_env_value:
        candidates.append(_candidate_path(raw_env_value))

    for default in defaults:
        if default in ("", None):
            continue
        candidates.append(_candidate_path(default))

    unique_candidates: list[Path] = []
    seen: set[str] = set()

    for candidate in candidates:
        candidate_str = str(candidate)

        if candidate_str in seen:
            continue

        seen.add(candidate_str)
        unique_candidates.append(candidate)

    return unique_candidates


def _pick_preferred_path(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


WINDOWS_LAUNCHABLE_SUFFIXES = {".bat", ".cmd", ".com", ".exe"}
WINDOWS_GIT_SHELL_RELATIVE_PATHS = (
    Path("Git") / "bin" / "sh.exe",
    Path("Git") / "usr" / "bin" / "sh.exe",
    Path("Git") / "bin" / "bash.exe",
    Path("Git") / "usr" / "bin" / "bash.exe",
)


def _read_shebang(path: Path) -> str | None:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            first_line = handle.readline().strip()
    except OSError:
        return None

    if not first_line.startswith("#!"):
        return None

    return first_line[2:].strip()


def _resolve_windows_interpreter(program_hint: str) -> str | None:
    if not program_hint:
        return None

    raw_candidate = Path(program_hint)
    if raw_candidate.is_absolute():
        resolved_candidate = raw_candidate.expanduser().resolve(strict=False)
        if resolved_candidate.is_file():
            return str(resolved_candidate)

    program_name = raw_candidate.name or program_hint
    normalized_name = program_name.casefold()
    direct_candidates = [program_name]

    if not Path(program_name).suffix:
        direct_candidates.append(f"{program_name}.exe")

    for candidate_name in direct_candidates:
        resolved = shutil.which(candidate_name)
        if resolved:
            return resolved

    if normalized_name in {"python", "python.exe", "python3", "python3.exe"}:
        executable = Path(sys.executable).resolve(strict=False)
        if executable.is_file():
            return str(executable)

    if normalized_name in {"sh", "sh.exe", "bash", "bash.exe"}:
        program_files_roots = (
            os.getenv("ProgramW6432"),
            os.getenv("ProgramFiles"),
            os.getenv("ProgramFiles(x86)"),
        )
        for root in program_files_roots:
            if not root:
                continue
            for relative_path in WINDOWS_GIT_SHELL_RELATIVE_PATHS:
                candidate = Path(root) / relative_path
                if candidate.is_file():
                    return str(candidate.resolve(strict=False))

    return None


def resolve_runner_command(path_value: str | Path) -> list[str] | None:
    candidate = _candidate_path(path_value)
    if not candidate.is_file():
        return None

    if os.name != "nt":
        if os.access(candidate, os.X_OK):
            return [str(candidate)]
        return None

    if candidate.suffix.casefold() in WINDOWS_LAUNCHABLE_SUFFIXES:
        return [str(candidate)]

    if candidate.suffix.casefold() == ".py":
        executable = Path(sys.executable).resolve(strict=False)
        if executable.is_file():
            return [str(executable), str(candidate)]

    shebang = _read_shebang(candidate)
    if not shebang:
        return None

    parts = shebang.split()
    if not parts:
        return None

    interpreter_hint = parts[0]
    interpreter_name = Path(interpreter_hint).name.casefold()
    if interpreter_name == "env" and len(parts) > 1:
        interpreter_hint = parts[1]

    resolved_interpreter = _resolve_windows_interpreter(interpreter_hint)
    if resolved_interpreter is None:
        return None

    return [resolved_interpreter, str(candidate)]


def is_runner_runnable(path_value: str | Path) -> bool:
    return resolve_runner_command(path_value) is not None


def list_model_artifacts(model_root: str | Path | None = None) -> tuple[Path, ...]:
    resolved_root = (
        Path(model_root).expanduser().resolve(strict=False)
        if model_root is not None
        else DEFAULT_MODEL_ROOT
    )
    if not resolved_root.is_dir():
        return ()

    artifacts = [
        path
        for path in resolved_root.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_MODEL_ARTIFACT_SUFFIXES
    ]
    return tuple(sorted(artifacts, key=lambda path: path.name.casefold()))


def get_active_runtime_overrides() -> tuple[str, ...]:
    active_overrides: list[str] = []
    for env_var in RUNTIME_OVERRIDE_ENV_VARS:
        value = os.getenv(env_var)
        if value:
            active_overrides.append(f"{env_var}={value}")
    return tuple(active_overrides)


MODEL_CANDIDATES = _build_candidates(
    "AURA_PRIMARY_MODEL_PATH",
    os.getenv("AURA_MODEL_PATH", ""),
    DEFAULT_MODEL_ROOT / PRIMARY_MODEL_NAME,
    AURA_ROOT_PATH / "models" / PRIMARY_MODEL_NAME,
    PRIMARY_MODEL_NAME,
    Path("models") / PRIMARY_MODEL_NAME,
    Path.home() / "aura" / PRIMARY_MODEL_NAME,
)

LLAMA_CANDIDATES = _build_candidates(
    "AURA_PRIMARY_LLAMA_PATH",
    os.getenv("AURA_LLAMA_PATH", ""),
    shutil.which("llama-cli.exe"),
    shutil.which("llama-cli"),
    AURA_ROOT_PATH / "llama.cpp" / "build" / "bin" / "Release" / "llama-cli.exe",
    AURA_ROOT_PATH / "llama.cpp" / "build" / "bin" / "llama-cli.exe",
    AURA_ROOT_PATH / "llama.cpp" / "build" / "bin" / "Release" / "llama-cli",
    AURA_ROOT_PATH / "llama.cpp" / "build" / "bin" / "llama-cli",
    Path("llama.cpp/build/bin/llama-cli"),
    Path("llama.cpp") / "build" / "bin" / "Release" / "llama-cli.exe",
    Path("llama.cpp") / "build" / "bin" / "llama-cli.exe",
    Path("llama.cpp") / "build" / "bin" / "Release" / "llama-cli",
    Path.home() / "llama.cpp/build/bin/llama-cli",
)

CRITIC_MODEL_CANDIDATES = _build_candidates(
    "AURA_CRITIC_MODEL_PATH",
    DEFAULT_MODEL_ROOT / CRITIC_MODEL_NAME,
    AURA_ROOT_PATH / "models" / CRITIC_MODEL_NAME,
    CRITIC_MODEL_NAME,
    Path("models") / CRITIC_MODEL_NAME,
    Path.home() / "aura" / CRITIC_MODEL_NAME,
)

CRITIC_LLAMA_CANDIDATES = _build_candidates(
    "AURA_CRITIC_LLAMA_PATH",
    *LLAMA_CANDIDATES,
)

ROUTER_MODEL_CANDIDATES = _build_candidates(
    "AURA_ROUTER_MODEL_PATH",
    DEFAULT_MODEL_ROOT / ROUTER_MODEL_NAME,
    AURA_ROOT_PATH / "models" / ROUTER_MODEL_NAME,
    ROUTER_MODEL_NAME,
    Path("models") / ROUTER_MODEL_NAME,
    Path.home() / "aura" / ROUTER_MODEL_NAME,
)

ROUTER_LLAMA_CANDIDATES = _build_candidates(
    "AURA_ROUTER_LLAMA_PATH",
    *LLAMA_CANDIDATES,
)

FALLBACK_MODEL_CANDIDATES = _build_candidates(
    "AURA_FALLBACK_MODEL_PATH",
    DEFAULT_MODEL_ROOT / TRANSITIONAL_FALLBACK_MODEL_NAME,
    AURA_ROOT_PATH / "models" / TRANSITIONAL_FALLBACK_MODEL_NAME,
    TRANSITIONAL_FALLBACK_MODEL_NAME,
    Path("models") / TRANSITIONAL_FALLBACK_MODEL_NAME,
    Path.home() / "aura" / TRANSITIONAL_FALLBACK_MODEL_NAME,
)

FALLBACK_LLAMA_CANDIDATES = _build_candidates(
    "AURA_FALLBACK_LLAMA_PATH",
    *LLAMA_CANDIDATES,
)

BASE_DIR = str(BASE_DIR_PATH)
LOG_DIR = str(LOG_DIR_PATH)
MEMORY_FILE = str(MEMORY_FILE_PATH)
MODEL_PATH = str(_pick_preferred_path(MODEL_CANDIDATES))
LLAMA_PATH = str(_pick_preferred_path(LLAMA_CANDIDATES))
CRITIC_MODEL_PATH = str(_pick_preferred_path(CRITIC_MODEL_CANDIDATES))
CRITIC_LLAMA_PATH = str(_pick_preferred_path(CRITIC_LLAMA_CANDIDATES))
ROUTER_MODEL_PATH = str(_pick_preferred_path(ROUTER_MODEL_CANDIDATES))
ROUTER_LLAMA_PATH = str(_pick_preferred_path(ROUTER_LLAMA_CANDIDATES))
FALLBACK_MODEL_PATH = str(_pick_preferred_path(FALLBACK_MODEL_CANDIDATES))
FALLBACK_LLAMA_PATH = str(_pick_preferred_path(FALLBACK_LLAMA_CANDIDATES))


def build_log_file() -> str:
    LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)
    return str(
        LOG_DIR_PATH / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
