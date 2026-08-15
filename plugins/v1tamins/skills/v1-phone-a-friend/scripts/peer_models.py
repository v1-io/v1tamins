"""Typed discovery and proposal records for peer catalog JSON."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Literal

PolicyState = Literal[
    "eligible",
    "not_authenticated",
    "auth_not_verified",
    "blocked_api_key_present",
    "explicit_api_mode",
    "api_key_required",
    "not_installed",
]
CatalogStatus = Literal["resolved", "unresolved"]
CatalogConfidence = Literal["verified", "unresolved"]
CatalogFormat = Literal["json", "tsv", "id_dash_label", "lines", "unresolved"]
LaunchState = Literal[
    "eligible",
    "blocked_api_key_present",
    "not_authenticated",
    "api_key_required",
    "auth_unverified",
    "model_unresolved",
    "launch_unrepresentable",
]
# How the selected model ID was established, not where it will be sent.
ModelRepresentation = Literal["catalog", "alias", "explicit"]
SelectionErrorCode = Literal[
    "model_not_current",
    "reasoning_level_unsupported",
]


@dataclass(frozen=True)
class AuthFact:
    """Single tagged auth decision. Launch derives from policy_state alone."""

    policy_state: PolicyState
    key_env_names: tuple[str, ...] = ()

    @classmethod
    def eligible(cls) -> AuthFact:
        return cls(policy_state="eligible")

    @classmethod
    def not_authenticated(cls) -> AuthFact:
        return cls(policy_state="not_authenticated")

    @classmethod
    def unverified(cls) -> AuthFact:
        return cls(policy_state="auth_not_verified")

    @classmethod
    def not_installed(cls) -> AuthFact:
        return cls(policy_state="not_installed")

    @classmethod
    def blocked_api_keys(cls, key_env_names: tuple[str, ...]) -> AuthFact:
        return cls(
            policy_state="blocked_api_key_present",
            key_env_names=key_env_names,
        )

    @classmethod
    def explicit_api(cls, key_env_names: tuple[str, ...]) -> AuthFact:
        return cls(
            policy_state="explicit_api_mode",
            key_env_names=key_env_names,
        )

    @classmethod
    def api_key_required(cls) -> AuthFact:
        return cls(policy_state="api_key_required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_state": self.policy_state,
            "key_env_names": list(self.key_env_names),
        }


@dataclass(frozen=True)
class ModelEntry:
    id: str
    family: str
    reasoning_levels: tuple[str, ...] = ()
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        levels = list(self.reasoning_levels)
        return {
            "id": self.id,
            "family": self.family,
            # Alias retained for receipt consumers that still read efforts.
            "efforts": levels,
            "reasoning_levels": levels,
            "rank": self.rank,
        }


@dataclass(frozen=True)
class ModelCatalog:
    status: CatalogStatus
    confidence: CatalogConfidence
    source: str | None = None
    fingerprint: str | None = None
    catalog_format: CatalogFormat = "unresolved"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderDiscovery:
    cli: str
    installed: bool
    executable: str | None
    version: str | None
    version_fingerprint: str | None
    auth: AuthFact
    models: tuple[ModelEntry, ...]
    model_catalog: ModelCatalog
    reasoning_levels: tuple[str, ...]
    roles: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cli": self.cli,
            "installed": self.installed,
            "executable": self.executable,
            "version": self.version,
            "version_fingerprint": self.version_fingerprint,
            "auth": self.auth.to_dict(),
            "models": [model.to_dict() for model in self.models],
            "model_catalog": self.model_catalog.to_dict(),
            "reasoning_levels": list(self.reasoning_levels),
            "roles": list(self.roles),
        }


@dataclass(frozen=True)
class ModelSelection:
    model: str | None
    model_family: str
    reasoning: str | None
    model_confidence: CatalogConfidence
    explicit: bool = False
    # The argument the installed CLI will actually receive. None means the
    # selected model and level pair has no validated launch representation.
    launch_model: str | None = None
    representation: ModelRepresentation = "catalog"
    reasoning_confidence: CatalogConfidence = "unresolved"


@dataclass(frozen=True)
class SelectionError:
    code: SelectionErrorCode
    alternatives: tuple[str, ...] = ()
    requested_model: str | None = None
    requested_reasoning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "alternatives": list(self.alternatives),
        }
        if self.requested_model is not None:
            payload["requested_model"] = self.requested_model
        if self.requested_reasoning is not None:
            payload["requested_reasoning"] = self.requested_reasoning
        return payload


@dataclass(frozen=True)
class Candidate:
    cli: str
    version: str | None
    version_fingerprint: str | None
    model: str | None
    model_family: str
    reasoning: str | None
    role: str
    permission: str
    auth: AuthFact
    catalog_confidence: CatalogConfidence
    catalog_fingerprint: str | None
    model_confidence: CatalogConfidence
    provider_rank: int
    launch_state: LaunchState
    catalog_model_id: str | None = None
    launch_model_argument: str | None = None
    representation: ModelRepresentation = "catalog"
    reasoning_confidence: CatalogConfidence = "unresolved"
    prompt: dict[str, Any] | None = None

    def with_prompt(self, prompt: dict[str, Any]) -> Candidate:
        return replace(self, prompt=prompt)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "cli": self.cli,
            "version": self.version,
            "version_fingerprint": self.version_fingerprint,
            "model": self.model,
            "model_family": self.model_family,
            "reasoning": self.reasoning,
            "role": self.role,
            "permission": self.permission,
            "auth": self.auth.to_dict(),
            "catalog_confidence": self.catalog_confidence,
            "catalog_fingerprint": self.catalog_fingerprint,
            "model_confidence": self.model_confidence,
            "provider_rank": self.provider_rank,
            "launch_state": self.launch_state,
            "catalog_model_id": self.catalog_model_id,
            "launch_model_argument": self.launch_model_argument,
            "representation": self.representation,
            "reasoning_confidence": self.reasoning_confidence,
        }
        if self.prompt is not None:
            payload["prompt"] = self.prompt
        return payload


@dataclass
class Proposal:
    ok: bool
    schema: str
    profile: str
    auth_mode: str
    confirmation_required: bool
    profile_options: list[dict[str, Any]]
    eligible_count: int
    roster_status: str
    recommended_roster: list[Candidate]
    alternatives: list[Candidate]
    discovered: list[ProviderDiscovery]
    selection_errors: list[dict[str, Any]]
    prompt_resolution: dict[str, Any]
    catalog_fingerprint: str
    snapshot_fingerprint: str | None
    context: dict[str, Any]
    error: dict[str, Any] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        if not self.ok and self.error is not None:
            return {"ok": False, "error": self.error}
        return {
            "ok": self.ok,
            "schema": self.schema,
            "profile": self.profile,
            "auth_mode": self.auth_mode,
            "confirmation_required": self.confirmation_required,
            "profile_options": self.profile_options,
            "eligible_count": self.eligible_count,
            "roster_status": self.roster_status,
            "recommended_roster": [
                candidate.to_dict() for candidate in self.recommended_roster
            ],
            "alternatives": [candidate.to_dict() for candidate in self.alternatives],
            "discovered": [provider.to_dict() for provider in self.discovered],
            "selection_errors": self.selection_errors,
            "prompt_resolution": self.prompt_resolution,
            "catalog_fingerprint": self.catalog_fingerprint,
            "snapshot_fingerprint": self.snapshot_fingerprint,
            "context": self.context,
        }
