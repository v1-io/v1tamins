"""Typed discovery and proposal records for peer catalog JSON."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class AuthFact:
    source: str
    confidence: str
    credential_presence: str
    policy_state: str
    key_env_names: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "confidence": self.confidence,
            "credential_presence": self.credential_presence,
            "policy_state": self.policy_state,
            "key_env_names": list(self.key_env_names),
        }


@dataclass(frozen=True)
class ModelEntry:
    id: str
    family: str
    efforts: tuple[str, ...] = ()
    reasoning_levels: tuple[str, ...] = ()
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        levels = self.reasoning_levels or self.efforts
        return {
            "id": self.id,
            "family": self.family,
            "efforts": list(self.efforts),
            "reasoning_levels": list(levels),
            "rank": self.rank,
        }


@dataclass(frozen=True)
class ModelCatalog:
    status: str
    confidence: str
    source: str | None = None
    fingerprint: str | None = None

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
    workflow: str

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
            "workflow": self.workflow,
        }


@dataclass(frozen=True)
class Candidate:
    cli: str
    version: str | None
    version_fingerprint: str | None
    model: str
    model_family: str
    reasoning: str | None
    role: str
    permission: str
    auth: AuthFact
    catalog_confidence: str
    catalog_fingerprint: str | None
    confidence: dict[str, str]
    workflow: str
    provider_rank: int
    eligible: bool
    launch_state: str
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
            "confidence": dict(self.confidence),
            "workflow": self.workflow,
            "provider_rank": self.provider_rank,
            "eligible": self.eligible,
            "launch_state": self.launch_state,
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
