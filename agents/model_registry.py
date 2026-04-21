from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import (
    CRITIC_LLAMA_PATH,
    CRITIC_MODEL_PATH,
    CRITIC_MODEL_ID,
    DEFAULT_MODEL_ROOT,
    FALLBACK_LLAMA_PATH,
    FALLBACK_MODEL_ID,
    FALLBACK_MODEL_PATH,
    LLAMA_PATH,
    MODEL_PATH,
    PRIMARY_MODEL_ID,
    ROUTER_LLAMA_PATH,
    ROUTER_MODEL_ID,
    ROUTER_MODEL_PATH,
    TRANSITIONAL_MODEL_FAMILY,
    list_model_artifacts,
)
from providers import (
    BaseProvider,
    LOCAL_CRITIC_PROVIDER_ID,
    LOCAL_PRIMARY_PROVIDER_ID,
    LOCAL_PROVIDER_CRITIC_ROLE,
    LOCAL_PROVIDER_PRIMARY_ROLE,
    LOCAL_PROVIDER_ROUTER_ROLE,
    LOCAL_ROUTER_PROVIDER_ID,
    LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
    LocalLlamaProvider,
    ProviderDescriptor,
)


ROLE_PRIMARY = LOCAL_PROVIDER_PRIMARY_ROLE
ROLE_CRITIC = LOCAL_PROVIDER_CRITIC_ROLE
ROLE_MICRO_EXPERT_ROUTER = LOCAL_PROVIDER_ROUTER_ROLE
ROLE_TRANSITIONAL_FALLBACK = "transitional_fallback"

MODEL_POLICY_ACTIVE_GREEN = "green_stack_active"
MODEL_POLICY_TRANSITIONAL_FALLBACK = "transitional_fallback"
MODEL_POLICY_TRANSITIONAL = MODEL_POLICY_TRANSITIONAL_FALLBACK
MODEL_POLICY_ALLOWLIST = "green_allowlist_candidate"
MODEL_POLICY_LAB = "open_lab_candidate"

MODEL_CATALOG_PRODUCTION = "production"
MODEL_CATALOG_CANDIDATE = "candidate"
MODEL_CATALOG_LAB = "lab"

RUNTIME_BACKEND_LLAMA_CPP = "llama_cpp_cli"
RUNTIME_BACKEND_PENDING = "pending_backend_selection"
ARTIFACT_FORMAT_GGUF = "gguf"
ARTIFACT_FORMAT_PENDING = "pending_artifact_selection"

STACK_HEALTH_HEALTHY = "healthy"
STACK_HEALTH_DEGRADED = "degraded"
STACK_HEALTH_PARTIAL_STACK = "partial_stack"
STACK_HEALTH_AT_RISK = "at_risk"
STACK_HEALTH_MISSING_MODELS = "missing_models"


@dataclass(frozen=True)
class ModelPolicyEntry:
    entry_id: str
    family: str
    model_id: str
    provider_id: str | None
    role: str | None
    runtime_backend: str | None
    artifact_format: str | None
    license_tier: str | None
    openness_tier: str | None
    commercial_ok: bool | None
    modifiable_ok: bool | None
    device_tier: str | None
    notes: str | None
    policy_status: str
    is_active: bool = False
    catalog_track: str | None = None
    discovered_path: str | None = None
    available_in_bank: bool | None = None
    governance_lane: str | None = None
    benchmark_readiness: str | None = None
    benchmark_priority: str | None = None
    promotion_barrier: str | None = None


@dataclass(frozen=True)
class ModelRegistry:
    providers: dict[str, BaseProvider]
    default_roles: dict[str, str]
    model_policies: tuple[ModelPolicyEntry, ...]
    fallback_provider_id: str | None = None

    def get_provider(self, provider_id: str) -> BaseProvider | None:
        return self.providers.get(provider_id)

    def get_provider_for_role(self, role: str) -> BaseProvider | None:
        provider_id = self.default_roles.get(role)
        if provider_id is None:
            return None

        return self.get_provider(provider_id)

    def list_descriptors(self) -> tuple[ProviderDescriptor, ...]:
        return tuple(provider.descriptor for provider in self.providers.values())

    def list_model_policies(self) -> tuple[ModelPolicyEntry, ...]:
        return self.model_policies

    def list_allowlisted_candidates(self) -> tuple[ModelPolicyEntry, ...]:
        return tuple(
            entry
            for entry in self.model_policies
            if entry.policy_status == MODEL_POLICY_ALLOWLIST
        )

    def list_production_stack(self) -> tuple[ModelPolicyEntry, ...]:
        return tuple(
            entry
            for entry in self.model_policies
            if entry.catalog_track == MODEL_CATALOG_PRODUCTION
        )

    def list_candidate_benchmarks(self) -> tuple[ModelPolicyEntry, ...]:
        entries = [
            entry
            for entry in self.model_policies
            if entry.catalog_track == MODEL_CATALOG_CANDIDATE
        ]
        return tuple(
            sorted(
                entries,
                key=lambda entry: (
                    entry.discovered_path is None,
                    entry.model_id,
                ),
            )
        )

    def list_lab_models(self) -> tuple[ModelPolicyEntry, ...]:
        entries = [
            entry
            for entry in self.model_policies
            if entry.catalog_track == MODEL_CATALOG_LAB
        ]
        return tuple(sorted(entries, key=lambda entry: entry.model_id))

    def get_fallback_provider(self) -> BaseProvider | None:
        if self.fallback_provider_id is None:
            return None

        return self.get_provider(self.fallback_provider_id)

    def get_active_policy_for_role(self, role: str) -> ModelPolicyEntry | None:
        for entry in self.model_policies:
            if entry.is_active and entry.role == role:
                return entry

        return None

    def get_transitional_fallback_policy(self) -> ModelPolicyEntry | None:
        for entry in self.model_policies:
            if entry.role == ROLE_TRANSITIONAL_FALLBACK:
                return entry

        return None


@dataclass(frozen=True)
class ProviderAvailabilitySnapshot:
    provider_id: str
    role: str | None
    model_id: str | None
    configured: bool
    available: bool
    availability_reason: str | None
    runtime_path: str | None
    model_path: str | None


@dataclass(frozen=True)
class StackHealthSnapshot:
    health: str
    primary_ready: bool
    fallback_ready: bool
    partial_stack: bool
    fallback_pressure: str
    available_provider_count: int
    total_provider_count: int
    optional_ready_count: int
    missing_roles: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ModelBankDefinition:
    entry_id: str
    family: str
    model_id: str
    role: str | None
    policy_status: str
    catalog_track: str
    device_tier: str | None
    notes: str
    filename_hints: tuple[str, ...]
    governance_lane: str | None = None
    benchmark_readiness: str | None = None
    benchmark_priority: str | None = None
    promotion_barrier: str | None = None


@dataclass(frozen=True)
class ModelBankGovernanceSnapshot:
    production_summary: tuple[str, ...]
    candidate_summary: tuple[str, ...]
    lab_summary: tuple[str, ...]
    benchmark_ready_ids: tuple[str, ...]
    exploratory_ids: tuple[str, ...]
    blocked_ids: tuple[str, ...]
    production_count: int
    candidate_count: int
    lab_count: int


def _infer_family(model_name: str) -> str:
    normalized = model_name.lower()

    if "phi" in normalized:
        return "phi"
    if "deepseek" in normalized:
        return "deepseek"
    if "gemma" in normalized:
        return "gemma"
    if "jamba" in normalized:
        return "jamba"
    if "mobilellm" in normalized:
        return "mobilellm"
    if "pleias" in normalized:
        return "pleias"
    if "qwen" in normalized:
        return "qwen2"
    if "smollm" in normalized:
        return "smollm2"
    if "granite" in normalized:
        return "granite"
    if "olmo" in normalized:
        return "olmo2"

    return "unknown"


def _infer_artifact_format_from_path(path_value: str | Path) -> str | None:
    suffix = Path(path_value).suffix.lower()

    if suffix == ".gguf":
        return ARTIFACT_FORMAT_GGUF

    if suffix in {".bin", ".pt", ".safetensors"}:
        return "transformers_weights"

    return None


def _active_model_id(model_path: str) -> str:
    model_name = Path(model_path).name or model_path
    family = _infer_family(model_name)

    if family == "granite":
        return PRIMARY_MODEL_ID
    if family == "olmo2":
        return CRITIC_MODEL_ID
    if family == "smollm2":
        return ROUTER_MODEL_ID
    if family == TRANSITIONAL_MODEL_FAMILY:
        return FALLBACK_MODEL_ID

    return Path(model_name).stem


def _build_active_policy_entries(
    *,
    model_path: str,
    critic_model_path: str,
    router_model_path: str,
    fallback_model_path: str,
) -> tuple[ModelPolicyEntry, ModelPolicyEntry, ModelPolicyEntry, ModelPolicyEntry]:
    primary_model_id = _active_model_id(model_path)
    critic_model_id = _active_model_id(critic_model_path)
    router_model_id = _active_model_id(router_model_path)
    fallback_model_id = _active_model_id(fallback_model_path)
    primary_family = _infer_family(primary_model_id)
    if primary_family == "unknown":
        primary_family = "granite"

    critic_family = _infer_family(critic_model_id)
    if critic_family == "unknown":
        critic_family = "olmo2"

    router_family = _infer_family(router_model_id)
    if router_family == "unknown":
        router_family = "smollm2"

    fallback_family = _infer_family(fallback_model_id)
    if fallback_family == "unknown":
        fallback_family = TRANSITIONAL_MODEL_FAMILY

    primary_entry = ModelPolicyEntry(
        entry_id="active_primary",
        family=primary_family,
        model_id=primary_model_id,
        provider_id=LOCAL_PRIMARY_PROVIDER_ID,
        role=ROLE_PRIMARY,
        runtime_backend=RUNTIME_BACKEND_LLAMA_CPP,
        artifact_format=ARTIFACT_FORMAT_GGUF,
        license_tier="green_stack_reviewed",
        openness_tier="green_open_runtime",
        commercial_ok=None,
        modifiable_ok=None,
        device_tier="mini_pc_local",
        notes="Provider principal real de V0.39.3 para conversación general local calibrada.",
        policy_status=MODEL_POLICY_ACTIVE_GREEN,
        is_active=True,
        catalog_track=MODEL_CATALOG_PRODUCTION,
        discovered_path=model_path,
        available_in_bank=Path(model_path).expanduser().resolve(strict=False).is_file(),
        governance_lane="core_production",
        benchmark_readiness="in_rotation",
        benchmark_priority="locked_core",
        promotion_barrier="active_primary_no_auto_swap",
    )
    critic_entry = ModelPolicyEntry(
        entry_id="active_critic",
        family=critic_family,
        model_id=critic_model_id,
        provider_id=LOCAL_CRITIC_PROVIDER_ID,
        role=ROLE_CRITIC,
        runtime_backend=RUNTIME_BACKEND_LLAMA_CPP,
        artifact_format=ARTIFACT_FORMAT_GGUF,
        license_tier="green_stack_reviewed",
        openness_tier="green_open_runtime",
        commercial_ok=None,
        modifiable_ok=None,
        device_tier="mini_pc_local",
        notes="Provider crítico/verificador real de V0.39.3 para chequeos y verificación breve bajo gating.",
        policy_status=MODEL_POLICY_ACTIVE_GREEN,
        is_active=True,
        catalog_track=MODEL_CATALOG_PRODUCTION,
        discovered_path=critic_model_path,
        available_in_bank=Path(critic_model_path).expanduser().resolve(strict=False).is_file(),
        governance_lane="core_production",
        benchmark_readiness="in_rotation",
        benchmark_priority="locked_core",
        promotion_barrier="active_critic_no_auto_swap",
    )
    router_entry = ModelPolicyEntry(
        entry_id="active_router",
        family=router_family,
        model_id=router_model_id,
        provider_id=LOCAL_ROUTER_PROVIDER_ID,
        role=ROLE_MICRO_EXPERT_ROUTER,
        runtime_backend=RUNTIME_BACKEND_LLAMA_CPP,
        artifact_format=ARTIFACT_FORMAT_GGUF,
        license_tier="green_stack_reviewed",
        openness_tier="green_open_runtime",
        commercial_ok=None,
        modifiable_ok=None,
        device_tier="mini_pc_micro",
        notes="Helper micro local para routing liviano, clasificación o apoyo breve sin convertirse en chat principal.",
        policy_status=MODEL_POLICY_ACTIVE_GREEN,
        is_active=True,
        catalog_track=MODEL_CATALOG_PRODUCTION,
        discovered_path=router_model_path,
        available_in_bank=Path(router_model_path).expanduser().resolve(strict=False).is_file(),
        governance_lane="core_production",
        benchmark_readiness="in_rotation",
        benchmark_priority="locked_core",
        promotion_barrier="active_router_no_auto_swap",
    )
    fallback_entry = ModelPolicyEntry(
        entry_id="transitional_fallback",
        family=fallback_family,
        model_id=fallback_model_id,
        provider_id=LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
        role=ROLE_TRANSITIONAL_FALLBACK,
        runtime_backend=RUNTIME_BACKEND_LLAMA_CPP,
        artifact_format=ARTIFACT_FORMAT_GGUF,
        license_tier="transitional_review_pending",
        openness_tier="transitional_runtime",
        commercial_ok=None,
        modifiable_ok=None,
        device_tier="mini_pc_local",
        notes="Fallback transicional controlado si Granite falla o no está disponible, nunca como primary nominal.",
        policy_status=MODEL_POLICY_TRANSITIONAL_FALLBACK,
        is_active=True,
        catalog_track=MODEL_CATALOG_PRODUCTION,
        discovered_path=fallback_model_path,
        available_in_bank=Path(fallback_model_path).expanduser().resolve(strict=False).is_file(),
        governance_lane="controlled_fallback",
        benchmark_readiness="in_rotation",
        benchmark_priority="operational_backup",
        promotion_barrier="fallback_never_promotes_without_review",
    )

    return primary_entry, critic_entry, router_entry, fallback_entry


def _build_allowlist_policy_entries() -> tuple[ModelPolicyEntry, ...]:
    return (
        ModelPolicyEntry(
            entry_id="allowlist_smollm2_router",
            family="smollm2",
            model_id=ROUTER_MODEL_ID,
            provider_id=None,
            role=ROLE_MICRO_EXPERT_ROUTER,
            runtime_backend=RUNTIME_BACKEND_PENDING,
            artifact_format=ARTIFACT_FORMAT_PENDING,
            license_tier="green_allowlist_reviewed",
            openness_tier="green_open_candidate",
            commercial_ok=True,
            modifiable_ok=True,
            device_tier="mini_pc_micro",
            notes="Anchor de benchmark para micro expert, router liviano y helper barato.",
            policy_status=MODEL_POLICY_ALLOWLIST,
            is_active=False,
            catalog_track=MODEL_CATALOG_CANDIDATE,
            available_in_bank=None,
            governance_lane="benchmark_anchor",
            benchmark_readiness="ready_for_benchmark",
            benchmark_priority="high",
            promotion_barrier="requires_eval_hook_and_scorecard",
        ),
        ModelPolicyEntry(
            entry_id="allowlist_granite_primary",
            family="granite",
            model_id=PRIMARY_MODEL_ID,
            provider_id=None,
            role=ROLE_PRIMARY,
            runtime_backend=RUNTIME_BACKEND_PENDING,
            artifact_format=ARTIFACT_FORMAT_PENDING,
            license_tier="green_allowlist_reviewed",
            openness_tier="green_open_candidate",
            commercial_ok=True,
            modifiable_ok=True,
            device_tier="mini_pc_primary",
            notes="Anchor de benchmark para provider principal conversacional local.",
            policy_status=MODEL_POLICY_ALLOWLIST,
            is_active=False,
            catalog_track=MODEL_CATALOG_CANDIDATE,
            available_in_bank=None,
            governance_lane="benchmark_anchor",
            benchmark_readiness="ready_for_benchmark",
            benchmark_priority="high",
            promotion_barrier="requires_eval_hook_and_scorecard",
        ),
        ModelPolicyEntry(
            entry_id="allowlist_olmo_critic",
            family="olmo2",
            model_id=CRITIC_MODEL_ID,
            provider_id=None,
            role=ROLE_CRITIC,
            runtime_backend=RUNTIME_BACKEND_PENDING,
            artifact_format=ARTIFACT_FORMAT_PENDING,
            license_tier="green_allowlist_reviewed",
            openness_tier="green_open_candidate",
            commercial_ok=True,
            modifiable_ok=True,
            device_tier="mini_pc_critic_lab",
            notes="Anchor de benchmark para critic, verifier y open lab.",
            policy_status=MODEL_POLICY_ALLOWLIST,
            is_active=False,
            catalog_track=MODEL_CATALOG_CANDIDATE,
            available_in_bank=None,
            governance_lane="benchmark_anchor",
            benchmark_readiness="ready_for_benchmark",
            benchmark_priority="high",
            promotion_barrier="requires_eval_hook_and_scorecard",
        ),
    )


_MODEL_BANK_DEFINITIONS = (
    ModelBankDefinition(
        entry_id="candidate_gemma_3_1b_it",
        family="gemma",
        model_id="Gemma 3 1B Instruct",
        role=ROLE_PRIMARY,
        policy_status=MODEL_POLICY_ALLOWLIST,
        catalog_track=MODEL_CATALOG_CANDIDATE,
        device_tier="mini_pc_primary",
        notes="Candidata inmediata para benchmark conversacional liviano si demuestra valor real frente a Granite.",
        filename_hints=("gemma-3-1b-it",),
        governance_lane="immediate_candidate",
        benchmark_readiness="ready_for_benchmark",
        benchmark_priority="high",
        promotion_barrier="needs_core_comparison_and_runtime_validation",
    ),
    ModelBankDefinition(
        entry_id="candidate_phi_4_mini_instruct",
        family="phi",
        model_id="Phi-4 Mini Instruct",
        role=ROLE_PRIMARY,
        policy_status=MODEL_POLICY_ALLOWLIST,
        catalog_track=MODEL_CATALOG_CANDIDATE,
        device_tier="mini_pc_primary",
        notes="Candidata inmediata para benchmark técnico y eficiencia general en CPU.",
        filename_hints=("phi-4-mini",),
        governance_lane="immediate_candidate",
        benchmark_readiness="ready_for_benchmark",
        benchmark_priority="high",
        promotion_barrier="needs_core_comparison_and_runtime_validation",
    ),
    ModelBankDefinition(
        entry_id="candidate_deepseek_r1_distill_1_5b",
        family="deepseek",
        model_id="DeepSeek R1 Distill Qwen 1.5B",
        role=ROLE_PRIMARY,
        policy_status=MODEL_POLICY_ALLOWLIST,
        catalog_track=MODEL_CATALOG_CANDIDATE,
        device_tier="mini_pc_primary",
        notes="Candidata inmediata para benchmark razonado de bajo costo antes de cualquier promoción al core.",
        filename_hints=("deepseek-r1-distill-qwen-1.5b",),
        governance_lane="immediate_candidate",
        benchmark_readiness="ready_for_benchmark",
        benchmark_priority="medium",
        promotion_barrier="needs_core_comparison_and_runtime_validation",
    ),
    ModelBankDefinition(
        entry_id="lab_gemma_4_e2b",
        family="gemma",
        model_id="Gemma 4 E2B",
        role=ROLE_PRIMARY,
        policy_status=MODEL_POLICY_LAB,
        catalog_track=MODEL_CATALOG_LAB,
        device_tier="server_review",
        notes="Modelo de laboratorio: requiere benchmark y backend compatibles antes de considerarlo candidato operativo.",
        filename_hints=("gemma-4-e2b",),
        governance_lane="exploratory_lab",
        benchmark_readiness="blocked_pending_backend",
        benchmark_priority="watch_only",
        promotion_barrier="backend_and_runtime_compatibility_pending",
    ),
    ModelBankDefinition(
        entry_id="lab_granite_4_350m",
        family="granite",
        model_id="Granite 4.0 350M",
        role=ROLE_MICRO_EXPERT_ROUTER,
        policy_status=MODEL_POLICY_LAB,
        catalog_track=MODEL_CATALOG_LAB,
        device_tier="edge_micro",
        notes="Laboratorio edge-friendly para futuras rutas micro, sin activación automática en el stack actual.",
        filename_hints=("granite-4.0-350m",),
        governance_lane="exploratory_lab",
        benchmark_readiness="exploratory_only",
        benchmark_priority="medium",
        promotion_barrier="future_micro_route_only",
    ),
    ModelBankDefinition(
        entry_id="lab_ai21_jamba_reasoning_3b",
        family="jamba",
        model_id="AI21 Jamba Reasoning 3B",
        role=ROLE_PRIMARY,
        policy_status=MODEL_POLICY_LAB,
        catalog_track=MODEL_CATALOG_LAB,
        device_tier="server_review",
        notes="Laboratorio de reasoning pesado: visible para benchmark, fuera del core CPU-friendly.",
        filename_hints=("ai21-jamba-reasoning-3b",),
        governance_lane="exploratory_lab",
        benchmark_readiness="exploratory_only",
        benchmark_priority="watch_only",
        promotion_barrier="outside_cpu_friendly_core",
    ),
    ModelBankDefinition(
        entry_id="lab_pleias_rag_1b",
        family="pleias",
        model_id="Pleias RAG 1B",
        role=None,
        policy_status=MODEL_POLICY_LAB,
        catalog_track=MODEL_CATALOG_LAB,
        device_tier="mini_pc_lab",
        notes="Laboratorio temático para evaluación posterior; no forma parte del routing general.",
        filename_hints=("pleias-rag-1b",),
        governance_lane="exploratory_lab",
        benchmark_readiness="exploratory_only",
        benchmark_priority="low",
        promotion_barrier="not_in_general_routing_scope",
    ),
    ModelBankDefinition(
        entry_id="lab_mobilellm_r1_950m_base",
        family="mobilellm",
        model_id="MobileLLM R1 950M Base",
        role=None,
        policy_status=MODEL_POLICY_LAB,
        catalog_track=MODEL_CATALOG_LAB,
        device_tier="edge_lab",
        notes="Artefacto base de laboratorio orientado a hardware pequeño; falta capa instruct y benchmark útil.",
        filename_hints=("mobilellm-r1-950m-base",),
        governance_lane="exploratory_lab",
        benchmark_readiness="blocked_pending_instruct",
        benchmark_priority="low",
        promotion_barrier="missing_instruct_variant",
    ),
)


def _policy_key(entry: ModelPolicyEntry) -> tuple[str, str, str | None]:
    return (entry.model_id, entry.policy_status, entry.role)


def _match_model_bank_definition(model_path: Path) -> ModelBankDefinition | None:
    normalized_name = model_path.name.casefold()
    for definition in _MODEL_BANK_DEFINITIONS:
        if any(hint in normalized_name for hint in definition.filename_hints):
            return definition
    return None


def _build_generic_lab_entry(model_path: Path) -> ModelPolicyEntry:
    model_name = model_path.name
    return ModelPolicyEntry(
        entry_id=f"lab_{model_path.stem.casefold().replace('-', '_').replace(' ', '_')}",
        family=_infer_family(model_name),
        model_id=model_path.stem,
        provider_id=None,
        role=None,
        runtime_backend=RUNTIME_BACKEND_PENDING,
        artifact_format=_infer_artifact_format_from_path(model_path) or ARTIFACT_FORMAT_PENDING,
        license_tier="lab_review_pending",
        openness_tier="lab_unknown",
        commercial_ok=None,
        modifiable_ok=None,
        device_tier="lab_unknown",
        notes="Artefacto descubierto en el banco local sin política explícita; queda en laboratorio hasta benchmark útil.",
        policy_status=MODEL_POLICY_LAB,
        is_active=False,
        catalog_track=MODEL_CATALOG_LAB,
        discovered_path=str(model_path),
        available_in_bank=True,
        governance_lane="exploratory_lab",
        benchmark_readiness="needs_triage",
        benchmark_priority="low",
        promotion_barrier="no_policy_or_benchmark_profile_yet",
    )


def _definition_to_policy_entry(
    definition: ModelBankDefinition,
    model_path: Path,
) -> ModelPolicyEntry:
    return ModelPolicyEntry(
        entry_id=definition.entry_id,
        family=definition.family,
        model_id=definition.model_id,
        provider_id=None,
        role=definition.role,
        runtime_backend=RUNTIME_BACKEND_PENDING,
        artifact_format=_infer_artifact_format_from_path(model_path) or ARTIFACT_FORMAT_PENDING,
        license_tier=(
            "green_allowlist_reviewed"
            if definition.policy_status == MODEL_POLICY_ALLOWLIST
            else "lab_review_pending"
        ),
        openness_tier=(
            "green_open_candidate"
            if definition.policy_status == MODEL_POLICY_ALLOWLIST
            else "lab_unknown"
        ),
        commercial_ok=True if definition.policy_status == MODEL_POLICY_ALLOWLIST else None,
        modifiable_ok=True if definition.policy_status == MODEL_POLICY_ALLOWLIST else None,
        device_tier=definition.device_tier,
        notes=definition.notes,
        policy_status=definition.policy_status,
        is_active=False,
        catalog_track=definition.catalog_track,
        discovered_path=str(model_path),
        available_in_bank=True,
        governance_lane=definition.governance_lane,
        benchmark_readiness=definition.benchmark_readiness,
        benchmark_priority=definition.benchmark_priority,
        promotion_barrier=definition.promotion_barrier,
    )


def _discover_bank_policy_entries(
    *existing_entries: ModelPolicyEntry,
    model_root: str | Path,
) -> tuple[ModelPolicyEntry, ...]:
    existing_keys = {_policy_key(entry) for entry in existing_entries}
    production_ids = {
        entry.model_id
        for entry in existing_entries
        if entry.catalog_track == MODEL_CATALOG_PRODUCTION
    }
    discovered_entries: list[ModelPolicyEntry] = []

    for model_artifact in list_model_artifacts(model_root):
        model_id = _active_model_id(str(model_artifact))
        if model_id in production_ids:
            continue

        definition = _match_model_bank_definition(model_artifact)
        if definition is not None:
            entry = _definition_to_policy_entry(definition, model_artifact)
        else:
            entry = _build_generic_lab_entry(model_artifact)

        entry_key = _policy_key(entry)
        if entry_key in existing_keys:
            continue

        existing_keys.add(entry_key)
        discovered_entries.append(entry)

    return tuple(discovered_entries)


def _build_colocated_model_path(model_path: str, sibling_model_name: str) -> str:
    return str(Path(model_path).expanduser().resolve(strict=False).with_name(sibling_model_name))


def _resolve_model_bank_root(model_path: str) -> Path:
    configured_parent = Path(model_path).expanduser().resolve(strict=False).parent
    if configured_parent.is_dir():
        return configured_parent
    return DEFAULT_MODEL_ROOT


def build_default_model_registry(
    llama_path: str,
    model_path: str,
    *,
    critic_llama_path: str | None = None,
    critic_model_path: str | None = None,
    router_llama_path: str | None = None,
    router_model_path: str | None = None,
    fallback_llama_path: str | None = None,
    fallback_model_path: str | None = None,
) -> ModelRegistry:
    use_default_stack = llama_path == LLAMA_PATH and model_path == MODEL_PATH

    effective_critic_llama_path = (
        critic_llama_path
        if critic_llama_path is not None
        else (CRITIC_LLAMA_PATH if use_default_stack else llama_path)
    )
    effective_critic_model_path = (
        critic_model_path
        if critic_model_path is not None
        else (
            CRITIC_MODEL_PATH
            if use_default_stack
            else _build_colocated_model_path(model_path, Path(CRITIC_MODEL_PATH).name)
        )
    )
    effective_router_llama_path = (
        router_llama_path
        if router_llama_path is not None
        else (ROUTER_LLAMA_PATH if use_default_stack else llama_path)
    )
    effective_router_model_path = (
        router_model_path
        if router_model_path is not None
        else (
            ROUTER_MODEL_PATH
            if use_default_stack
            else _build_colocated_model_path(model_path, Path(ROUTER_MODEL_PATH).name)
        )
    )
    effective_fallback_llama_path = (
        fallback_llama_path
        if fallback_llama_path is not None
        else (FALLBACK_LLAMA_PATH if use_default_stack else llama_path)
    )
    effective_fallback_model_path = (
        fallback_model_path
        if fallback_model_path is not None
        else (
            FALLBACK_MODEL_PATH
            if use_default_stack
            else _build_colocated_model_path(model_path, Path(FALLBACK_MODEL_PATH).name)
        )
    )

    primary_provider = LocalLlamaProvider(
        llama_path=llama_path,
        model_path=model_path,
        provider_id=LOCAL_PRIMARY_PROVIDER_ID,
        display_name="Granite local primary",
        roles_supported=(ROLE_PRIMARY,),
        notes="Provider principal conversacional local real de V0.39.3 sobre Granite.",
        family_override="granite",
        model_id_override=PRIMARY_MODEL_ID,
        policy_status=MODEL_POLICY_ACTIVE_GREEN,
        license_tier="green_stack_reviewed",
        openness_tier="green_open_runtime",
        device_tier="mini_pc_primary",
    )
    critic_provider = LocalLlamaProvider(
        llama_path=effective_critic_llama_path,
        model_path=effective_critic_model_path,
        provider_id=LOCAL_CRITIC_PROVIDER_ID,
        display_name="OLMo local critic",
        roles_supported=(ROLE_CRITIC,),
        notes="Provider crítico/verificador local real de V0.39.3 sobre OLMo.",
        family_override="olmo2",
        model_id_override=CRITIC_MODEL_ID,
        policy_status=MODEL_POLICY_ACTIVE_GREEN,
        license_tier="green_stack_reviewed",
        openness_tier="green_open_runtime",
        device_tier="mini_pc_critic_lab",
    )
    router_provider = LocalLlamaProvider(
        llama_path=effective_router_llama_path,
        model_path=effective_router_model_path,
        provider_id=LOCAL_ROUTER_PROVIDER_ID,
        display_name="SmolLM2 local router/helper",
        roles_supported=(ROLE_MICRO_EXPERT_ROUTER,),
        notes="Helper/router local liviano de V0.39.3 sobre SmolLM2.",
        family_override="smollm2",
        model_id_override=ROUTER_MODEL_ID,
        policy_status=MODEL_POLICY_ACTIVE_GREEN,
        license_tier="green_stack_reviewed",
        openness_tier="green_open_runtime",
        device_tier="mini_pc_micro",
    )
    transitional_fallback_provider = LocalLlamaProvider(
        llama_path=effective_fallback_llama_path,
        model_path=effective_fallback_model_path,
        provider_id=LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
        display_name="Qwen transitional fallback",
        roles_supported=(ROLE_PRIMARY,),
        notes="Fallback transicional controlado de V0.39.3 sobre Qwen.",
        family_override=TRANSITIONAL_MODEL_FAMILY,
        model_id_override=FALLBACK_MODEL_ID,
        policy_status=MODEL_POLICY_TRANSITIONAL_FALLBACK,
        license_tier="transitional_review_pending",
        openness_tier="transitional_runtime",
        device_tier="mini_pc_local",
    )

    effective_primary_policy_path = primary_provider.descriptor.model_path or model_path
    effective_critic_policy_path = critic_provider.descriptor.model_path or effective_critic_model_path
    effective_router_policy_path = router_provider.descriptor.model_path or effective_router_model_path
    effective_fallback_policy_path = (
        transitional_fallback_provider.descriptor.model_path or effective_fallback_model_path
    )
    active_policy_entries = _build_active_policy_entries(
        model_path=effective_primary_policy_path,
        critic_model_path=effective_critic_policy_path,
        router_model_path=effective_router_policy_path,
        fallback_model_path=effective_fallback_policy_path,
    )
    allowlist_policy_entries = _build_allowlist_policy_entries()
    bank_root = _resolve_model_bank_root(effective_primary_policy_path)
    discovered_bank_entries = _discover_bank_policy_entries(
        *active_policy_entries,
        *allowlist_policy_entries,
        model_root=bank_root,
    )
    policy_entries = (
        *active_policy_entries,
        *allowlist_policy_entries,
        *discovered_bank_entries,
    )

    return ModelRegistry(
        providers={
            LOCAL_PRIMARY_PROVIDER_ID: primary_provider,
            LOCAL_CRITIC_PROVIDER_ID: critic_provider,
            LOCAL_ROUTER_PROVIDER_ID: router_provider,
            LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID: transitional_fallback_provider,
        },
        default_roles={
            ROLE_PRIMARY: LOCAL_PRIMARY_PROVIDER_ID,
            ROLE_CRITIC: LOCAL_CRITIC_PROVIDER_ID,
            ROLE_MICRO_EXPERT_ROUTER: LOCAL_ROUTER_PROVIDER_ID,
        },
        model_policies=policy_entries,
        fallback_provider_id=LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID,
    )


def build_provider_availability_snapshot(
    provider: BaseProvider | None,
) -> ProviderAvailabilitySnapshot | None:
    if provider is None:
        return None

    descriptor = provider.descriptor
    role = descriptor.role
    if descriptor.provider_id == LOCAL_TRANSITIONAL_FALLBACK_PROVIDER_ID:
        role = ROLE_TRANSITIONAL_FALLBACK
    return ProviderAvailabilitySnapshot(
        provider_id=descriptor.provider_id,
        role=role,
        model_id=descriptor.model_id,
        configured=descriptor.runtime_path is not None or descriptor.model_path is not None,
        available=bool(descriptor.availability),
        availability_reason=descriptor.availability_reason,
        runtime_path=descriptor.runtime_path,
        model_path=descriptor.model_path,
    )


def build_stack_health_snapshot(registry: ModelRegistry) -> StackHealthSnapshot:
    primary = build_provider_availability_snapshot(registry.get_provider_for_role(ROLE_PRIMARY))
    critic = build_provider_availability_snapshot(registry.get_provider_for_role(ROLE_CRITIC))
    router = build_provider_availability_snapshot(registry.get_provider_for_role(ROLE_MICRO_EXPERT_ROUTER))
    fallback = build_provider_availability_snapshot(registry.get_fallback_provider())

    provider_snapshots = tuple(
        snapshot
        for snapshot in (primary, critic, router, fallback)
        if snapshot is not None
    )
    optional_snapshots = tuple(
        snapshot
        for snapshot in (critic, router, fallback)
        if snapshot is not None
    )
    available_provider_count = sum(
        1 for snapshot in provider_snapshots if snapshot.available
    )
    total_provider_count = len(provider_snapshots)
    optional_ready_count = sum(
        1 for snapshot in optional_snapshots if snapshot.available
    )
    primary_ready = bool(primary and primary.available)
    fallback_ready = bool(fallback and fallback.available)
    missing_roles = tuple(
        snapshot.role or snapshot.provider_id
        for snapshot in provider_snapshots
        if not snapshot.available
    )
    reasons = tuple(
        f"{snapshot.provider_id}:{snapshot.availability_reason}"
        for snapshot in provider_snapshots
        if not snapshot.available and snapshot.availability_reason
    )

    if not primary_ready:
        if primary is not None and primary.availability_reason == "model_missing":
            health = STACK_HEALTH_MISSING_MODELS
        else:
            health = STACK_HEALTH_AT_RISK
    elif optional_ready_count == len(optional_snapshots):
        health = STACK_HEALTH_HEALTHY
    elif optional_ready_count <= 1:
        health = STACK_HEALTH_PARTIAL_STACK
    else:
        health = STACK_HEALTH_DEGRADED

    if health in {STACK_HEALTH_MISSING_MODELS, STACK_HEALTH_AT_RISK}:
        fallback_pressure = "high"
    elif health in {STACK_HEALTH_DEGRADED, STACK_HEALTH_PARTIAL_STACK}:
        fallback_pressure = "medium"
    else:
        fallback_pressure = "low"

    return StackHealthSnapshot(
        health=health,
        primary_ready=primary_ready,
        fallback_ready=fallback_ready,
        partial_stack=health == STACK_HEALTH_PARTIAL_STACK,
        fallback_pressure=fallback_pressure,
        available_provider_count=available_provider_count,
        total_provider_count=total_provider_count,
        optional_ready_count=optional_ready_count,
        missing_roles=missing_roles,
        reasons=reasons,
    )


def _format_governance_entry(entry: ModelPolicyEntry) -> str:
    readiness = entry.benchmark_readiness or "sin_readiness"
    priority = entry.benchmark_priority or "sin_prioridad"
    lane = entry.governance_lane or "sin_lane"
    return f"{entry.model_id} ({lane}, {readiness}, {priority})"


def build_model_bank_governance_snapshot(registry: ModelRegistry) -> ModelBankGovernanceSnapshot:
    production_entries = registry.list_production_stack()
    candidate_entries = registry.list_candidate_benchmarks()
    lab_entries = registry.list_lab_models()

    benchmark_ready_ids = tuple(
        entry.model_id
        for entry in candidate_entries
        if entry.benchmark_readiness in {"ready_for_benchmark", "benchmark_ready"}
    )
    exploratory_ids = tuple(
        entry.model_id
        for entry in lab_entries
        if (entry.governance_lane or "").startswith("exploratory")
    )
    blocked_ids = tuple(
        entry.model_id
        for entry in (*candidate_entries, *lab_entries)
        if entry.benchmark_readiness in {
            "blocked_pending_backend",
            "blocked_pending_instruct",
            "needs_triage",
        }
    )

    return ModelBankGovernanceSnapshot(
        production_summary=tuple(_format_governance_entry(entry) for entry in production_entries),
        candidate_summary=tuple(_format_governance_entry(entry) for entry in candidate_entries),
        lab_summary=tuple(_format_governance_entry(entry) for entry in lab_entries),
        benchmark_ready_ids=benchmark_ready_ids,
        exploratory_ids=exploratory_ids,
        blocked_ids=blocked_ids,
        production_count=len(production_entries),
        candidate_count=len(candidate_entries),
        lab_count=len(lab_entries),
    )
