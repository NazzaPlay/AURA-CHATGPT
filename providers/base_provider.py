from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


PROVIDER_RESULT_SUCCESS = "success"
PROVIDER_RESULT_UNAVAILABLE = "unavailable"
PROVIDER_RESULT_UNSUPPORTED_ROLE = "unsupported_role"
PROVIDER_RESULT_ERROR = "error"
PROVIDER_RESULT_EMPTY = "empty_response"


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    display_name: str
    backend_type: str
    roles_supported: tuple[str, ...]
    is_local: bool
    family: str | None = None
    model_id: str | None = None
    role: str | None = None
    runtime_backend: str | None = None
    artifact_format: str | None = None
    license_tier: str | None = None
    openness_tier: str | None = None
    commercial_ok: bool | None = None
    modifiable_ok: bool | None = None
    device_tier: str | None = None
    policy_status: str | None = None
    runtime_path: str | None = None
    model_path: str | None = None
    availability: bool | None = None
    availability_reason: str | None = None
    license_family: str | None = None
    commercial_use: bool | None = None
    modification_ok: bool | None = None
    redistribution_ok: bool | None = None
    quantization: str | None = None
    footprint: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ProviderRequest:
    prompt: str
    role: str
    task_type: str


@dataclass(frozen=True)
class ProviderResult:
    provider_id: str
    role: str
    status: str
    response: str | None = None
    error: str | None = None
    availability: bool | None = None
    runtime_info: tuple[str, ...] = ()


class BaseProvider(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> ProviderDescriptor:
        raise NotImplementedError

    @abstractmethod
    def check_availability(self) -> tuple[bool, str | None]:
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: ProviderRequest) -> ProviderResult:
        raise NotImplementedError
