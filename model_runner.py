import os
import re
import subprocess
import unicodedata

from agents.text_matching import repair_common_mojibake, sanitize_visible_text
from config import resolve_runner_command


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
BACKSPACE_RE = re.compile(r".\x08")
PROMPT_FRAGMENT_RE = re.compile(r"\b(?:Usuario|AURA):|\[ Prompt:")
TRUNCATED_MARKER_RE = re.compile(r"\.\.\.\s*\(truncated\)", re.IGNORECASE)
PROMPT_LEAK_PREFIX_PATTERNS = (
    re.compile(r"^\s*Eres AURA, un asistente inteligente\.\s*", re.IGNORECASE),
    re.compile(r"^\s*Respondes siempre en [^.]{3,40}\.\s*", re.IGNORECASE),
    re.compile(r"^\s*Respondes siempre en espa[nñ]ol\.\s*", re.IGNORECASE),
    re.compile(r"^\s*Eres claro, [^.]*directo\.\s*", re.IGNORECASE),
    re.compile(r"^\s*Reglas:\s*", re.IGNORECASE),
    re.compile(r"^\s*Instrucciones de estilo(?: para esta respuesta)?:\s*", re.IGNORECASE),
    re.compile(r"^\s*Plan interno de respuesta \(no lo muestres\):\s*", re.IGNORECASE),
    re.compile(r"^\s*-\s*resumir en una sola l\S*nea [^\n.]*\.?\s*", re.IGNORECASE),
    re.compile(r"^\s*resume en una sola l\S*nea [^\n.]*\.?\s*", re.IGNORECASE),
    re.compile(r"^\s*-\s*responde con una sola l\S*nea breve\.?\s*", re.IGNORECASE),
    re.compile(r"^\s*-\s*no expliques de m\S*s\.?\s*", re.IGNORECASE),
    re.compile(r"^\s*l\S*nea de foco:\s*", re.IGNORECASE),
    re.compile(r"^\s*-\s*Usas la informaci[^.]{0,60}usuario\.\s*", re.IGNORECASE),
    re.compile(r"^\s*-\s*Usas la informaci[oó]n conocida del usuario\.\s*", re.IGNORECASE),
    re.compile(r"^\s*-\s*No inventas cosas\.\s*", re.IGNORECASE),
    re.compile(r"^\s*-\s*Si no sabes algo, lo dices\.\s*", re.IGNORECASE),
    re.compile(r"^\s*-\s*Evitas respuestas gen[eé]ricas o rob[oó]ticas\.\s*", re.IGNORECASE),
    re.compile(
        r"^\s*-\s*Responde siempre en espa[nñ]ol\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Ve directo al punto y evita saludos o relleno innecesario\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Ve directo al punto y evita saludos, relleno y frases vac[ií]as\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r'^\s*-\s*No escribas etiquetas como "Usuario:" o "AURA:"\.\s*',
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*No cierres con preguntas gen[eé]ricas[^.]*\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*No repitas literalmente la pregunta del usuario\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Da una respuesta clara, concreta y explicativa\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Si hay una causa probable, menci[oó]nala temprano\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Si aplica, da pasos o acciones espec[ií]ficas\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Evita responder de forma vaga o gen[eé]rica\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Da una respuesta [^.]*concreta[^.]*\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Incluye al menos una idea pr[aá]ctica, ejemplo o siguiente paso\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Evita frases vac[ií]as o demasiado generales\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Responde de forma natural, breve y [uú]til\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Haz la respuesta clara, estructurada y pr[aá]ctica\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Sigue este orden si aplica: idea breve, explicaci[oó]n clara, "
        r"qu[eé] hacer y c[oó]mo verificar\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Prioriza una causa probable y una soluci[oó]n accionable\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Si faltan datos, dilo en una sola frase y da igualmente el primer "
        r"paso m[aá]s [uú]til\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Evita explicaciones vagas o demasiado largas\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Empieza con una idea breve\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Explica el tema con claridad y orden\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Incluye contexto [uú]til y pasos o ejemplo breve si ayudan\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Mant[eé]n la respuesta compacta y enfocada\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Da una respuesta [uú]til, concreta y natural\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Incluye una idea pr[aá]ctica, ejemplo o siguiente paso si suma valor\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Deja al menos una idea [^\n.]*\.?\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Evita sonar rob[oó]tico o demasiado abstracto\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Responde de forma breve, directa y operativa\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*-\s*Responde sin saludo ni pre[aá]mbulo\.?\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*identifica el problema; resume la causa probable; da pasos concretos; "
        r"cierra con una verificaci[oó]n breve\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*explica primero la idea principal; agrega contexto [uú]til; termina con "
        r"una aplicaci[oó]n pr[aá]ctica o ejemplo breve\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*responde directo; aporta una idea [uú]til o ejemplo; cierra sin relleno\.\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*responde de forma breve, natural y [uú]til\.\s*",
        re.IGNORECASE,
    ),
    re.compile(r"^\s*L[ií]nea de foco:.*", re.IGNORECASE),
    re.compile(
        r"^\s*Resume en una sola l[ií]nea el foco[^\n.]*\.?\s*",
        re.IGNORECASE,
    ),
    re.compile(r"^\s*Prioriza el [^\n.]*\.?\s*", re.IGNORECASE),
    re.compile(r"^\s*No repita la pregunta\.\s*", re.IGNORECASE),
    re.compile(r"^\s*El usuario se llama [^.]+\.\s*", re.IGNORECASE),
    re.compile(r"^\s*El usuario trabaja [^.]+\.\s*", re.IGNORECASE),
    re.compile(r"^\s*Al usuario le gusta [^.]+\.\s*", re.IGNORECASE),
    re.compile(r"^\s*Preferencias conocidas del usuario: [^.]+\.\s*", re.IGNORECASE),
    re.compile(r"^\s*Perfil [uú]til del usuario para esta respuesta:\s*", re.IGNORECASE),
    re.compile(r"^\s*Formato objetivo para esta respuesta:\s*", re.IGNORECASE),
    re.compile(r"^\s*-\s*Idea breve:.*", re.IGNORECASE),
    re.compile(r"^\s*-\s*Explicaci[oó]n clara:.*", re.IGNORECASE),
    re.compile(r"^\s*-\s*Qu[eé] hacer:.*", re.IGNORECASE),
    re.compile(r"^\s*-\s*C[oó]mo verificar:.*", re.IGNORECASE),
    re.compile(r"^\s*-\s*Pasos o ejemplo:.*", re.IGNORECASE),
)
NOISE_LINES = {
    "available commands:",
    "/exit or Ctrl+C     stop or exit",
    "/regen              regenerate the last response",
    "/clear              clear the chat history",
    "/read               add a text file",
    "Exiting...",
    "Failed to load the model",
}
ERROR_PREFIXES = (
    "error:",
    "gguf_",
    "llama_",
    "common_init_from_params:",
    "srv    load_model:",
)

DEFAULT_MODEL_TIMEOUT_SECONDS = 90

PROMPT_LEAK_GENERIC_CONTROL_HINTS = (
    "responde",
    "respondes siempre",
    "resume",
    "resumir",
    "evita",
    "deja",
    "prioriza",
    "saludo",
    "preambulo",
    "relleno",
    "linea de foco",
    "foco util",
    "informacion conocida del usuario",
)

PROMPT_LEADING_COMMAND_PREFIXES = (
    "- responde",
    "- respondes siempre",
    "- resume",
    "- resumir",
    "- evita",
    "- deja",
    "- prioriza",
    "- no expliques",
    "- no escriba",
    "linea de foco",
    "respondes siempre",
)

VISIBLE_SCAFFOLD_LABEL_PATTERNS = (
    re.compile(
        r"(?i)(?:^|(?<=[.!?])\s+|[-*]\s+)(?:idea breve|explicaci[oó]n clara|qu[eé] hacer|c[oó]mo verificar|pasos o ejemplo):\s*"
    ),
)

CRITIC_SECTION_PATTERNS = (
    re.compile(
        r"(?i)(?:^|(?<=[.!?])\s+)(?:verificaci[oó]n breve|verificada|ajuste|dudosa):\s*[^.!?]*(?:[.!?]|$)"
    ),
)


def _normalize_output(raw_output: str) -> str:
    cleaned = sanitize_visible_text(raw_output)

    while True:
        updated = BACKSPACE_RE.sub("", cleaned)
        if updated == cleaned:
            break
        cleaned = updated

    return ANSI_ESCAPE_RE.sub("", cleaned)


def _decode_process_output(raw_output: bytes | str | None) -> str:
    if raw_output is None:
        return ""

    if isinstance(raw_output, str):
        return sanitize_visible_text(raw_output)

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return sanitize_visible_text(raw_output.decode(encoding))
        except UnicodeDecodeError:
            continue

    return sanitize_visible_text(raw_output.decode("utf-8", errors="replace"))


def _normalize_signal_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", repair_common_mojibake(text or ""))
    return "".join(
        character for character in normalized if not unicodedata.combining(character)
    ).replace("�", "?").casefold()


def _collect_lines(raw_output: str) -> list[str]:
    cleaned = _normalize_output(raw_output)
    lines: list[str] = []

    for raw_line in cleaned.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith(">"):
            continue

        if line.startswith("Loading model..."):
            continue

        if line.startswith(("build", "model", "modalities")):
            continue

        if line in NOISE_LINES:
            continue

        lines.append(line)

    return lines


def _dedupe_lines(lines: list[str]) -> list[str]:
    unique_lines: list[str] = []
    seen: set[str] = set()

    for line in lines:
        if line in seen:
            continue

        seen.add(line)
        unique_lines.append(line)

    return unique_lines


def _build_prompt_line_set(prompt: str | None) -> set[str]:
    if not prompt:
        return set()

    prompt_lines: set[str] = set()

    for raw_line in _normalize_output(prompt).splitlines():
        line = raw_line.strip()
        if not line:
            continue

        prompt_lines.add(line)

        stripped_prompt_line = _strip_prompt_fragments(line)
        if stripped_prompt_line:
            prompt_lines.add(stripped_prompt_line)

    return prompt_lines


def _strip_prompt_fragments(text: str) -> str:
    match = PROMPT_FRAGMENT_RE.search(text)
    if not match:
        return text.strip()

    return text[: match.start()].strip()


def _strip_prompt_leak_text(text: str) -> str:
    cleaned = text.strip()

    while cleaned:
        previous = cleaned

        for pattern in PROMPT_LEAK_PREFIX_PATTERNS:
            cleaned = pattern.sub("", cleaned).strip()

        if cleaned == previous:
            break

    return cleaned


def _is_prompt_like_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    return stripped.startswith((">", "Usuario:", "AURA:"))


def _drop_fragment_lines(lines: list[str]) -> list[str]:
    cleaned_lines = [line for line in lines if "(truncated)" not in line.lower()]

    while len(cleaned_lines) > 1:
        first_line = cleaned_lines[0]
        compact_first_line = first_line.replace(" ", "")

        if len(compact_first_line) <= 3 and not re.search(r"[.!?]$", first_line):
            cleaned_lines = cleaned_lines[1:]
            continue

        if first_line.endswith("..."):
            cleaned_lines = cleaned_lines[1:]
            continue

        break

    while len(cleaned_lines) > 1:
        last_line = cleaned_lines[-1]
        compact_last_line = last_line.replace(" ", "")

        if len(compact_last_line) <= 3 and not re.search(r"[.!?]$", last_line):
            cleaned_lines = cleaned_lines[:-1]
            continue

        if last_line.endswith("...") and len(last_line.split()) <= 4:
            cleaned_lines = cleaned_lines[:-1]
            continue

        break

    return cleaned_lines


def _cleanup_response_text(text: str) -> str:
    cleaned = " ".join(sanitize_visible_text(text).split()).strip()
    for pattern in VISIBLE_SCAFFOLD_LABEL_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([.!?])\s*([.!?])+", r"\1", cleaned)
    cleaned = re.sub(r",\s*,+", ",", cleaned)
    sentence_parts = re.split(r"(?<=[.!?])\s+", cleaned)
    deduped_parts: list[str] = []

    for part in sentence_parts:
        compact_part = part.strip()
        if not compact_part:
            continue
        if deduped_parts and _normalize_signal_text(compact_part) == _normalize_signal_text(
            deduped_parts[-1]
        ):
            continue
        deduped_parts.append(compact_part)

    if deduped_parts:
        cleaned = " ".join(deduped_parts)

    cleaned = repair_common_mojibake(cleaned)
    return cleaned.strip()


def _expand_inline_prompt_bullets(text: str) -> str:
    stripped = text.lstrip()
    if not stripped.startswith("- ") or " - " not in text[:260]:
        return text

    return re.sub(r"\s+-\s+", "\n- ", text, count=8)


def _looks_like_prompt_instruction(line: str) -> bool:
    normalized = _normalize_signal_text(line)
    if not normalized:
        return False

    if normalized.startswith(PROMPT_LEADING_COMMAND_PREFIXES):
        return True

    control_hits = sum(
        hint in normalized for hint in PROMPT_LEAK_GENERIC_CONTROL_HINTS
    )
    if control_hits < 2:
        return False

    return (
        normalized.startswith("- ")
        or normalized.startswith("respondes siempre")
        or normalized.startswith("resume en una sola linea")
        or normalized.startswith("linea de foco")
    )


def _slice_after_prompt_echo(cleaned_output: str, prompt: str) -> str:
    normalized_prompt = _normalize_output(prompt).strip()

    if normalized_prompt and normalized_prompt in cleaned_output:
        return cleaned_output.split(normalized_prompt, 1)[1]

    lines = cleaned_output.splitlines()
    last_prompt_like_index = -1

    for index, line in enumerate(lines):
        if _is_prompt_like_line(line):
            last_prompt_like_index = index

    if last_prompt_like_index == -1:
        return cleaned_output

    return "\n".join(lines[last_prompt_like_index + 1 :])


def _extract_response(raw_output: str, prompt: str | None = None) -> str:
    cleaned = _normalize_output(raw_output).split("[ Prompt:", 1)[0]
    prompt_lines = _build_prompt_line_set(prompt)

    if prompt:
        cleaned = _slice_after_prompt_echo(cleaned, prompt)

    if "AURA:" in cleaned:
        cleaned = cleaned.rsplit("AURA:", 1)[1]

    cleaned = _strip_prompt_fragments(cleaned)
    cleaned = _strip_prompt_leak_text(cleaned)
    cleaned = _expand_inline_prompt_bullets(cleaned)
    lines = []

    for raw_line in cleaned.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        line = _strip_prompt_fragments(line)
        line = _strip_prompt_leak_text(line)
        if not line:
            continue

        if line in prompt_lines:
            continue

        if not lines and _looks_like_prompt_instruction(line):
            continue

        if line.startswith(">"):
            continue

        if line.startswith("Loading model..."):
            continue

        if line.startswith(("build", "model", "modalities", "llama_")):
            continue

        if line in NOISE_LINES:
            continue

        if line.startswith("llama_"):
            continue

        lines.append(line)

    lines = _drop_fragment_lines(_dedupe_lines(lines))
    response = " ".join(lines).strip()
    response = TRUNCATED_MARKER_RE.sub("", response).strip()
    response = repair_common_mojibake(response)
    response = _strip_prompt_leak_text(response)
    response = _cleanup_response_text(response)

    return response


def _extract_error(stdout: str, stderr: str, returncode: int) -> str:
    stderr_lines = _collect_lines(stderr)
    stdout_lines = _collect_lines(stdout)

    priority_lines = [
        line
        for line in stderr_lines + stdout_lines
        if line.lower().startswith(ERROR_PREFIXES)
    ]

    detail_lines = _dedupe_lines(priority_lines or stderr_lines or stdout_lines)

    if detail_lines:
        return " | ".join(detail_lines)

    return f"llama.cpp terminó con código {returncode}"


def _read_timeout_seconds() -> int:
    raw_timeout = os.getenv("AURA_MODEL_TIMEOUT_SECONDS", "").strip()
    if not raw_timeout:
        return DEFAULT_MODEL_TIMEOUT_SECONDS

    try:
        parsed_timeout = int(raw_timeout)
    except ValueError:
        return DEFAULT_MODEL_TIMEOUT_SECONDS

    return max(parsed_timeout, 5)


def run_model(prompt: str, llama_path: str, model_path: str) -> str:
    if not os.path.isfile(llama_path):
        return f"[error: no se encontró llama-cli en '{llama_path}']"

    runner_command = resolve_runner_command(llama_path)
    if runner_command is None:
        return f"[error: llama-cli no es ejecutable: '{llama_path}']"

    if not os.path.isfile(model_path):
        return f"[error: no se encontró el modelo GGUF en '{model_path}']"

    command = [
        *runner_command,
        "-m",
        model_path,
        "-p",
        prompt,
        "-n",
        "320",
        "--no-display-prompt",
        "--no-show-timings",
        "--single-turn",
        "--simple-io",
    ]
    timeout_seconds = _read_timeout_seconds()

    try:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return f"[error: timeout tras {timeout_seconds}s]"
    except Exception as exc:
        return f"[error: {exc}]"

    stdout_text = _decode_process_output(result.stdout)
    stderr_text = _decode_process_output(result.stderr)

    if result.returncode != 0:
        return f"[error: {_extract_error(stdout_text, stderr_text, result.returncode)}]"

    response = _extract_response(stdout_text, prompt=prompt)

    if response:
        return response

    fallback_response = _extract_response(stderr_text, prompt=prompt)
    if fallback_response:
        return fallback_response

    return "[sin respuesta]"
