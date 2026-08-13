from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityIdentity:
    module_name: str
    capability_name: str
    major_version: int

    def __post_init__(self) -> None:
        if not self.module_name:
            raise ValueError("CapabilityIdentity.module_name must be non-empty.")
        if not self.capability_name:
            raise ValueError("CapabilityIdentity.capability_name must be non-empty.")
        if self.major_version < 1:
            raise ValueError("CapabilityIdentity.major_version must be positive.")

    @property
    def canonical(self) -> str:
        return f"{self.module_name}.{self.capability_name}@{self.major_version}"

    def is_compatible_with(self, other: CapabilityIdentity) -> bool:
        return self == other


@dataclass(frozen=True)
class HostBindingId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("HostBindingId.value must be non-empty.")

    def __str__(self) -> str:
        return self.value
