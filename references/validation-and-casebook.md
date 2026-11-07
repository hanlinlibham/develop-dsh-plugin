# Validation matrix and casebook

Read this file before declaring a plugin complete, reviewing a rewrite, or deciding whether an observed symptom deserves a new plugin.

## Completion evidence matrix

| Requirement | Strong evidence | Weak evidence |
|---|---|---|
| Source contract | typecheck and inject/export checks include every changed entrypoint | one package command is green but omits the file |
| Package shape | built artifacts match exports and package file list | source exists |
| Behavior | normal, error, cancellation, and disposal tests execute | test file exists |
| Composition | real Loader boot resolves the intended row, services, and config | YAML looks correct |
| Model visibility | real session shows the schema/content and replay reconstructs it | prompt text appears in source |
| Client UI | browser interaction on desktop and narrow layouts | static screenshot |
| Independence | unload removes contributions; host and unrelated plugins remain live | startup succeeds with plugin enabled |
| Documentation | README, ADR, lineage, and install ledger match the mounted state | comments mention the package |

Inspect the scope of every verifier before accepting its result.

## Minimum test surface

Test at least:

- each model-visible behavior;
- each configuration branch that changes activation;
- missing/invalid required data;
- cancellation of long-running work;
- duplicate or conflicting registration when relevant;
- cleanup of external subscriptions and resources;
- replay/fork/resume for durable context;
- running-to-settled identity for conversation UI;
- install and unload composition.

Do not chase a coverage percentage without checking behavior ownership. Do not leave a model-visible path with no executable assertion.

## Real-composition procedure

1. Build the exact package mounted by the target profile.
2. Resolve the profile plus every applicable patch through the real Loader.
3. Confirm row id, package name, disabled state, config interpolation, and service activation.
4. Verify no second channel mounts the same package.
5. Run a real model or browser interaction.
6. Disable or remove the package through the owning channel.
7. Resolve and exercise the composition again.

Avoid restarting a live process while a human-input tool or turn is waiting unless the task explicitly requires that failure scenario.

## Casebook: what prior failures teach

### A custom conversation card replaced official tool views

The package mounted and rendered, but replacing the official conversation/tool occupant removed behavior owned by Ask, Bash, and Read views. The correction was removal, not another compatibility layer.

Rule: inspect the current occupant and descendant slots; prefer additive placement; require a current product need before replacement.

### A custom Ask view duplicated existing HITL

The custom row changed a historical summary but did not own the live user-question composer. Official packages already supplied the tool row and input-area interaction.

Rule: identify the actual behavior owner before building a view with the same label.

### A second file tree was refused

Several community candidates offered another filesystem surface while the product already had one. Installing them would create conflicting ownership and user state.

Rule: reuse one capability owner; record refused packages and reasons so later agents do not repeat the search.

### A task lifecycle failed despite visible instructions

A finished task was reopened for a new deliverable even though the relevant skill was visible. The failure belonged at typed execution boundaries, so a narrow Host policy plugin interpreted the existing manifest and CLI through pre-step, tool, and stopping seams. It did not create a second state machine.

Rule: move mechanical correctness into observable execution contracts; keep prose for guidance.

### Green-looking engineering had missing coverage

An audit found a dead test outside the root runner, UI packages outside typecheck, model-visible code with one assertion, and a mounted package missing from the ledger.

Rule: verifier coverage and composition records are part of the evidence; a green command alone proves little.

### A layout fix kept moving because the product boundary was unsettled

Code alternated between the official sidebar, a plugin panel, left/right workbench placement, and competing collapse state. Several local fixes were technically sound but served contradictory product contracts.

Rule: settle ownership, layout, and replacement boundaries before implementing slot or CSS behavior.

## Symptoms that do not justify a plugin

Do not create a plugin solely for:

- an incomplete tool call repaired as an unknown outcome after a process restart;
- a one-off operational trace with no current user action;
- a fallback row already specified and tested by the host;
- a package that exists only to hide required misconfiguration;
- a future abstraction with no current consumer;
- a second installation of an already mounted capability.

Explain the behavior or fix the owning configuration instead.
