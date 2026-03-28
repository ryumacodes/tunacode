"""Typed schema for the bundled models_registry.json document."""

from __future__ import annotations

from typing import NotRequired, TypeAlias, TypedDict

RegistryNumber: TypeAlias = float | int


class RegistryModalities(TypedDict, total=False):
    """Input/output modality metadata for a model."""

    input: list[str]
    output: list[str]


class RegistryInterleavedConfig(TypedDict):
    """Interleaved content metadata for a model."""

    field: str


class RegistryProviderOverride(TypedDict, total=False):
    """Provider-specific override metadata at the model level."""

    api: str
    npm: str
    shape: str


class RegistryCostBreakdown(TypedDict, total=False):
    """Numeric pricing metadata for a model cost tier."""

    input: RegistryNumber
    output: RegistryNumber
    cache_read: RegistryNumber
    cache_write: RegistryNumber


class RegistryModelCost(RegistryCostBreakdown, total=False):
    """Model pricing metadata from the registry."""

    input_audio: RegistryNumber
    output_audio: RegistryNumber
    reasoning: RegistryNumber
    context_over_200k: RegistryCostBreakdown


class RegistryModelLimit(TypedDict, total=False):
    """Token limit metadata for a model."""

    context: int
    input: int
    output: int


class RegistryModelEntry(TypedDict):
    """Model entry in the bundled registry."""

    id: str
    name: str
    attachment: NotRequired[bool]
    cost: NotRequired[RegistryModelCost]
    family: NotRequired[str]
    interleaved: NotRequired[bool | RegistryInterleavedConfig]
    knowledge: NotRequired[str]
    last_updated: NotRequired[str]
    limit: NotRequired[RegistryModelLimit]
    modalities: NotRequired[RegistryModalities]
    open_weights: NotRequired[bool]
    provider: NotRequired[RegistryProviderOverride]
    reasoning: NotRequired[bool]
    release_date: NotRequired[str]
    status: NotRequired[str]
    structured_output: NotRequired[bool]
    temperature: NotRequired[bool]
    tool_call: NotRequired[bool]


class RegistryProviderEntry(TypedDict):
    """Provider entry in the bundled registry."""

    id: str
    name: str
    models: dict[str, RegistryModelEntry]
    alchemy_api: NotRequired[str]
    api: NotRequired[str]
    doc: NotRequired[str]
    env: NotRequired[list[str]]
    npm: NotRequired[str]


ModelsRegistryDocument: TypeAlias = dict[str, RegistryProviderEntry]
ModelConfig: TypeAlias = RegistryModelEntry
ModelRegistry: TypeAlias = ModelsRegistryDocument
