# v1tamins

v1tamins is a shared collection of reusable AI development skills. One plugin
package makes the same skills available in multiple agent runtimes.

## Language

**Skill**:
A reusable workflow that an agent loads for a particular kind of task. It
includes the instructions and any resources needed to carry out that workflow.
_Avoid_: prompt, command, agent

**Canonical Source**:
The authoritative, editable version of a skill. An installed copy is a derived
version, even when its contents match.
_Avoid_: cache, installation, master copy

**Plugin package**:
The collection of skills and supporting resources distributed together to an
agent runtime.
_Avoid_: application, marketplace

**Marketplace**:
A catalog through which a runtime discovers an available plugin package.
_Avoid_: plugin package, installed copy

**Installed copy**:
The version of a plugin package available to a particular runtime. It can differ
from the current Canonical Source.
_Avoid_: Canonical Source, checkout

**Runtime**:
The host that discovers skills, loads their instructions, and executes agent
turns, such as Claude Code or Codex.
_Avoid_: model, plugin

**Trigger**:
User language that should lead a runtime to select a particular skill.
_Avoid_: keyword, invocation

**Invocation posture**:
The rule governing whether a skill may be selected implicitly or requires an
explicit request. It does not grant permission for consequential actions.
_Avoid_: permission, authorization

**Explicit invocation**:
A request that names the skill to use.
_Avoid_: implicit routing

**Implicit routing**:
Selection of a skill from the task expressed by the user, without the user
naming that skill.
_Avoid_: explicit invocation, skill execution

**Packaging check**:
A static check that a plugin's structure, metadata, and referenced resources
are internally consistent. It does not establish runtime behavior.
_Avoid_: live verification, behavior proof

**Live verification**:
An observed runtime session used to check plugin loading, skill selection, or
skill behavior. Its result applies to the source, runtime, and scenario tested.
_Avoid_: packaging check, universal proof

**Public-safe**:
Suitable for sharing outside the project that inspired the skill, without
private facts, credentials, or dependencies on private context.
_Avoid_: anonymized, internal-only
