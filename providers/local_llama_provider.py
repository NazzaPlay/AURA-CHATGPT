from __future__ import annotations

import os
from pathlib import Path

from config import (
    CRITIC_MODEL_NAME,
    DEFAULT_MODEL_ROOT,
    PRIMARY_MODEL_NAME,
    ROUTER_MODEL_NAME,
    TRANSITIONAL_FALLBACK_MODEL_NAME,
    is_runner_runnable,
)
from model_runner import run_model

from .base_provider import (
    BaseProvider,
    PROVIDER_RESULT_EMPTY,
    PROVIDER_RESULT_ERROR,
    PROVIDER_RESULT_SUCCESS,
    PROVIDER_RESULT_UNAVAILABLE,
    PROVIDER_RESULT_UNSUPPORTED_ROLE,
    ProviderDescriptor,
    ProviderRequest,
    ProviderResult,
)


LOCAL_PRIMARY_PROVIDER_ID = "local_primary"
LOCAL_CRITIC_PROVIDER_ID = "local_critic"
LOCAL_ROUTER_PROVIDER_ID = "local_router"
LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID = "local_transitional_fallback"
LOCAL_LLAMA_PRIMARY_PROVIDER_ID = LOCAL_PRIMARY_PROVIDER_ID
LOCAL_LLAMA_CRITIC_PROVIDER_ID = LOCAL_CRITIC_PROVIDER_ID
LOCAL_PROVIDER_PRIMARY_ROLE = "primary_conversational"
LOCAL_PROVIDER_CRITIC_ROLE = "critic_verifier"
LOCAL_PROVIDER_ROUTER_ROLE = "micro_expert_router"

LOCAL_LLAMA_PROVIDER_ID = LOCAL_PRIMARY_PROVIDER_ID

CRITIC_PROMPT_PREFIX = """
Eres el verificador crítico de AURA.

Objetivo:
- revisar la respuesta principal de forma breve
- detectar si hay una afirmación demasiado fuerte, una contradicción o una omisión importante
- no reescribir toda la respuesta

Formato:
- responde con una sola línea
- usa una de estas salidas:
  - VERIFICADA: <motivo breve>
  - AJUSTE: <ajuste o cautela concreta>
  - DUDOSA: <qué falta para afirmarlo mejor>
""".strip()

ROUTER_PROMPT_PREFIX = """
Eres el helper de routing local de AURA.

Objetivo:
- resumir en una sola línea el foco útil para responder
- ayudar con routing o filtrado leve
- no convertirte en el asistente principal

Formato:
- responde con una sola línea breve
- no saludes
- no expliques de más
""".strip()

PRIMARY_TECHNICAL_PROMPT_PREFIX = """
Ajuste de salida para el modelo principal de AURA:
- responde sin saludo ni preámbulo
- si es técnico, da una idea concreta temprano
- evita respuestas vacías, demasiado abstractas o infladas
- si falta un dato, dilo en una frase y da igual el paso más útil
""".strip()

PRIMARY_CHAT_PROMPT_PREFIX = """
Ajuste de salida para el modelo principal de AURA:
- responde de forma natural y breve
- no metas relleno ni frases ceremoniales
- deja al menos una idea útil, ejemplo o siguiente paso si suma valor
""".strip()

FALLBACK_PRIMARY_PROMPT_PREFIX = """
Modo fallback transicional de AURA:
- conserva claridad y brevedad
- no te presentes como modelo distinto
- evita sobreactuar seguridad o creatividad
""".strip()


PROVIDER_MODEL_NAMES = {
    LOCAL_PRIMARY_PROVIDER_ID: PRIMARY_MODEL_NAME,
    LOCAL_CRITIC_PROVIDER_ID: CRITIC_MODEL_NAME,
    LOCAL_ROUTER_PROVIDER_ID: ROUTER_MODEL_NAME,
    LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID: TRANSITIONAL_FALLBACK_MODEL_NAME,
}

PROVIDER_DISCOVERY_HINTS = {
    LOCAL_PRIMARY_PROVIDER_ID: ("granite",),
    LOCAL_CRITIC_PROVIDER_ID: ("olmo",),
    LOCAL_ROUTER_PROVIDER_ID: ("smollm", "smol"),
    LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID: ("qwen",),
}


class LocalLlamaProvider(BaseProvider):
    def __init__(
        self,
        llama_path: str,
        model_path: str,
        *,
        provider_id: str = LOCAL_PRIMARY_PROVIDER_ID,
        display_name: str = "Local primary provider",
        roles_supported: tuple[str, ...] = (LOCAL_PROVIDER_PRIMARY_ROLE,),
        notes: str = "Provider principal local encapsulado para AURA.",
        family_override: str | None = None,
        model_id_override: str | None = None,
        policy_status: str | None = None,
        license_tier: str | None = None,
        openness_tier: str | None = None,
        device_tier: str = "mini_pc_local",
    ) -> None:
        self._llama_path = llama_path
        self._model_path = model_path
        self._provider_id = provider_id
        self._display_name = display_name
        self._roles_supported = roles_supported
        self._notes = notes
        self._family_override = family_override
        self._model_id_override = model_id_override
        self._policy_status = policy_status
        self._license_tier = license_tier
        self._openness_tier = openness_tier
        self._device_tier = device_tier

    def _infer_model_family(self, model_path: str | None = None) -> str:
        if self._family_override:
            return self._family_override

        candidate_model_path = model_path or self._model_path
        model_name = (Path(candidate_model_path).name or candidate_model_path).lower()

        if "qwen" in model_name:
            return "qwen2"
        if "smollm" in model_name:
            return "smollm2"
        if "granite" in model_name:
            return "granite"
        if "olmo" in model_name:
            return "olmo2"

        return "unknown"

    def _infer_artifact_format(self, model_path: str | None = None) -> str | None:
        suffix = Path(model_path or self._model_path).suffix.lower()

        if suffix == ".gguf":
            return "gguf"

        if suffix in {".bin", ".pt", ".safetensors"}:
            return "transformers_weights"

        return None

    def _resolve_model_path(self) -> str:
        configured_path = Path(self._model_path).expanduser().resolve(strict=False)
        if configured_path.is_file():
            return str(configured_path)

        candidate_dirs = self._iter_model_search_dirs(configured_path)
        canonical_name = PROVIDER_MODEL_NAMES.get(self._provider_id)
        if canonical_name:
            for candidate_dir in candidate_dirs:
                candidate_path = candidate_dir / canonical_name
                if candidate_path.is_file():
                    return str(candidate_path.resolve(strict=False))

        discovery_hints = PROVIDER_DISCOVERY_HINTS.get(self._provider_id, ())
        for candidate_dir in candidate_dirs:
            if not candidate_dir.is_dir():
                continue
            for candidate_path in sorted(candidate_dir.glob("*.gguf")):
                lower_name = candidate_path.name.casefold()
                if any(hint in lower_name for hint in discovery_hints):
                    return str(candidate_path.resolve(strict=False))

        return str(configured_path)

    def _iter_model_search_dirs(self, configured_path: Path) -> tuple[Path, ...]:
        llama_path = Path(self._llama_path).expanduser().resolve(strict=False)
        configured_parent = configured_path.parent.resolve(strict=False)
        default_model_root = DEFAULT_MODEL_ROOT.resolve(strict=False)
        candidates = [
            configured_path.parent,
            configured_path.parent / "models",
        ]
        if configured_parent == default_model_root or default_model_root in configured_parent.parents:
            candidates.append(DEFAULT_MODEL_ROOT)
        candidates.extend(
            [
                llama_path.parent,
                llama_path.parent.parent,
                llama_path.parent.parent.parent,
            ]
        )
        unique_candidates: list[Path] = []
        seen: set[str] = set()

        for candidate in candidates:
            candidate_key = str(candidate.resolve(strict=False))
            if candidate_key in seen:
                continue
            seen.add(candidate_key)
            unique_candidates.append(candidate)

        return tuple(unique_candidates)

    @property
    def descriptor(self) -> ProviderDescriptor:
        available, availability_reason = self.check_availability()
        resolved_model_path = self._resolve_model_path()
        role = self._roles_supported[0] if len(self._roles_supported) == 1 else None
        model_name = Path(resolved_model_path).name or resolved_model_path
        family = self._infer_model_family(resolved_model_path)
        artifact_format = self._infer_artifact_format(resolved_model_path)
        policy_status = self._policy_status or (
            "transitional_fallback"
            if self._provider_id == LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID
            else "runtime_candidate"
        )
        license_tier = self._license_tier or (
            "transitional_review_pending"
            if family == "qwen2"
            else "green_stack_reviewed"
        )
        openness_tier = self._openness_tier or (
            "transitional_runtime"
            if family == "qwen2"
            else "green_open_runtime"
        )
        return ProviderDescriptor(
            provider_id=self._provider_id,
            display_name=self._display_name,
            backend_type="llama_cpp_cli",
            roles_supported=self._roles_supported,
            is_local=True,
            family=family,
            model_id=self._model_id_override or model_name.removesuffix(".gguf"),
            role=role,
            runtime_backend="llama_cpp_cli",
            artifact_format=artifact_format,
            license_tier=license_tier,
            openness_tier=openness_tier,
            commercial_ok=None,
            modifiable_ok=None,
            device_tier=self._device_tier,
            policy_status=policy_status,
            runtime_path=self._llama_path,
            model_path=resolved_model_path,
            availability=available,
            availability_reason=availability_reason,
            license_family=None,
            commercial_use=None,
            modification_ok=None,
            redistribution_ok=None,
            quantization=None,
            footprint=None,
            notes=self._notes,
        )

    def check_availability(self) -> tuple[bool, str | None]:
        if not os.path.isfile(self._llama_path):
            return False, "runner_missing"

        if not is_runner_runnable(self._llama_path):
            return False, "runner_not_executable"

        if not os.path.isfile(self._resolve_model_path()):
            return False, "model_missing"

        return True, None

    def _build_effective_prompt(self, request: ProviderRequest) -> str:
        if request.role == LOCAL_PROVIDER_CRITIC_ROLE:
            return (
                f"{CRITIC_PROMPT_PREFIX}\n\n"
                f"{request.prompt}\n\n"
                "Verificador:"
            )

        if request.role == LOCAL_PROVIDER_ROUTER_ROLE:
            return (
                f"{ROUTER_PROMPT_PREFIX}\n\n"
                f"{request.prompt}\n\n"
                "Helper:"
            )

        if request.role == LOCAL_PROVIDER_PRIMARY_ROLE:
            if request.task_type == "technical_reasoning":
                prefix = PRIMARY_TECHNICAL_PROMPT_PREFIX
            else:
                prefix = PRIMARY_CHAT_PROMPT_PREFIX

            if self._provider_id == LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID:
                prefix = f"{FALLBACK_PRIMARY_PROMPT_PREFIX}\n\n{prefix}"

            return (
                f"{prefix}\n\n"
                f"{request.prompt}"
            )

        return request.prompt

    def generate(self, request: ProviderRequest) -> ProviderResult:
        if request.role not in self.descriptor.roles_supported:
            return ProviderResult(
                provider_id=self._provider_id,
                role=request.role,
                status=PROVIDER_RESULT_UNSUPPORTED_ROLE,
                error="unsupported_role",
                availability=self.descriptor.availability,
                runtime_info=("role_not_supported",),
            )

        available, reason = self.check_availability()
        if not available:
            return ProviderResult(
                provider_id=self._provider_id,
                role=request.role,
                status=PROVIDER_RESULT_UNAVAILABLE,
                error=reason,
                availability=False,
                runtime_info=(
                    "availability_check_failed",
                    f"availability_reason:{reason or 'unknown'}",
                ),
            )

        resolved_model_path = self._resolve_model_path()
        raw_response = run_model(
            self._build_effective_prompt(request),
            self._llama_path,
            resolved_model_path,
        )
        if raw_response == "[sin respuesta]":
            return ProviderResult(
                provider_id=self._provider_id,
                role=request.role,
                status=PROVIDER_RESULT_EMPTY,
                error="empty_response",
                availability=True,
                runtime_info=("provider_returned_empty_response",),
            )

        if raw_response.startswith("[error: ") and raw_response.endswith("]"):
            return ProviderResult(
                provider_id=self._provider_id,
                role=request.role,
                status=PROVIDER_RESULT_ERROR,
                error=raw_response[len("[error: ") : -1].strip(),
                availability=True,
                runtime_info=("provider_runtime_error",),
            )

        if request.role == LOCAL_PROVIDER_CRITIC_ROLE:
            generation_mode = "critic_provider_generation"
        elif request.role == LOCAL_PROVIDER_ROUTER_ROLE:
            generation_mode = "router_helper_generation"
        elif self._provider_id == LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID:
            generation_mode = "fallback_provider_generation"
        else:
            generation_mode = "primary_provider_generation"
        return ProviderResult(
            provider_id=self._provider_id,
            role=request.role,
            status=PROVIDER_RESULT_SUCCESS,
            response=raw_response,
            availability=True,
            runtime_info=(
                generation_mode,
                f"provider_family:{self._infer_model_family(resolved_model_path)}",
                f"task_type:{request.task_type}",
            ),
        )
