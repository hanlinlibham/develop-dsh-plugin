---
name: develop-dsh-plugin
description: Research, design, implement, review, debug, or rewrite productized DeepSeek Harness (dsh) plugins as out-of-tree source packages. Use for Host or Client plugins involving Cordis services, typed events, model tools, session injection, slots, themes, bundles, patches, packaging, loading, replay, disposal, community publication, or real-composition validation. Route temporary runtime-defined Cordis plugins that use inspect/define/run to cordis-plugin-development instead.
---

# Develop DSH Plugins

Build the smallest source package that owns one current capability, mounts through a documented DSH seam, survives replay when model-visible, and disappears cleanly on unload.

The bundled starter was checked against **DSH 0.2.2-rc.1 / Cordis 4.1.0 / Node.js >=24.9.0** on 2026-11-07. Read [the version and migration notes](references/runtime-0.2.2.md) when targeting this release or reviewing older code. Resolve the actual release tag and npm version; development-branch code and individual packages' `latest` tags may describe different contracts.

## Start from the target repository

1. Read the nearest `AGENTS.md`, `CLAUDE.md`, contribution rules, package standards, and deployment notes before changing files.
2. Identify read-only upstream checkouts, writable out-of-tree directories, runtime versions, package manager, install channels, and required gates.
3. Treat repository instructions as the local contract. Do not transplant commands or dependency versions from another checkout.
4. Read the target project's plugin standards and development workflow. Before implementing a non-trivial tool, lifecycle, session, or UI plugin, inspect its maintained kernel notes and the matching official source.

Do not edit an official checkout, fork a package, replace an official UI seat, publish, install into a live profile, or restart a running service unless the user and repository rules authorize that action.

## Classify the task

- For a new or rewritten source package, follow the entire workflow.
- For a bug fix, inspect the current contract and run the applicable discovery and validation steps; do not redesign unrelated seams.
- For review or diagnosis, remain read-only unless the user asks for changes.
- For a temporary dynamic plugin driven by `cordis_inspect_*`, `cordis_define`, and `cordis_run`, use `cordis-plugin-development`; do not scaffold a package here.

## 1. Research before designing

Search in this order:

1. Inspect official packages, docs, service definitions, events, slots, tools, theme tokens, and examples in the target runtime version.
2. Search maintained community plugins and package registries for the same capability.
3. Inspect the target project's installed composition, ledger, lineage, removed/refused entries, patches, and generated config.
4. Compare one to three relevant implementations only when they answer a concrete open question.

Record evidence, not a generic survey. Name what already owns the surface, what can be reused, what remains missing, and whether a package is installable in the target runtime.

Choose one outcome:

- reuse an existing package;
- extend an existing public seam;
- create one out-of-tree plugin;
- stop and request authority for a core edit, fork, or official-seat replacement.

Do not create a plugin when an installed or maintained package already satisfies the current need.

## 2. Pass the design gate

Write a one-sentence capability statement containing:

- the capability owner and current consumer;
- the service, event, tool, slot, or theme seam;
- Host, Client, or both;
- whether the model sees it;
- the durable source or explicit non-durable scope;
- the unload boundary.

Example:

> Register `wiki_query` on Host `ctx.tools`, return canonical JSON, render bounded model content, rely on session tool events for replay, and remove the registration with the plugin fiber.

Answer these questions before creating files:

1. Who needs this now?
2. Does official or community code already own it?
3. Which existing seam accepts it, and does it add to or replace a product surface?
4. Can it collide by key, capability, file tree, service ownership, or install channel?
5. Can it unload without breaking the host or another plugin?
6. If model-visible, can every request be reconstructed from durable session data?

Stop when any answer is missing. Ask for direction when the missing answer changes the architecture or grants materially broader authority.

Read [references/seam-router.md](references/seam-router.md) before selecting the extension mechanism.

## 3. Design the smallest package

Keep one package responsible for one capability. Split Service Definition, Provider, and Consumer only when those roles have current owners and need to evolve or be replaced independently.

Define before implementing:

- package and plugin names;
- Host and Client entrypoints;
- required and optional services;
- event modes and continuation behavior;
- tool input/output schemas;
- durable events and replay semantics;
- slot keys, selectors, priorities, and owner props;
- configuration and failure policy;
- disposal behavior;
- install and uninstall channels;
- test evidence and known limitations.

Write an ADR before changing a behavior contract, adding a cross-package interface or durable format, forking, replacing an official seat, or rejecting a plausible simpler alternative.

Read [references/package-contract.md](references/package-contract.md) before scaffolding or reviewing package files.

After the design gate passes, use the bundled Host-only starter when it matches the capability:

```bash
python3 <skill-dir>/scripts/scaffold_plugin.py ./dsh-plugin-example \
  --package-name dsh-plugin-example \
  --dsh-version "$TARGET_DSH_VERSION" \
  --cordis-version "$TARGET_CORDIS_VERSION" \
  --dry-run
```

Inspect the dry run, then repeat without `--dry-run`. Resolve `<skill-dir>` to this Skill's directory and take both exact versions from the target runtime. The script refuses to overwrite a non-empty directory. Do not use the template for Client UI, a service seam, or a capability that failed the research gate.

## 4. Implement within the seam

Follow these invariants:

- Use named `name`, `inject`, `Config`, and `apply` exports for function plugins. Do not default-export `apply`.
- Put service keys in plugin `inject`. Client manifest `inject` entries are informational package-name edges; they do not order activation. Register into another package's slot through `ctx.slots.inject(slotName, callback)` so contributions follow the slot declaration's lifetime.
- Access an optional service with `ctx.get(name)` or a nested `ctx.inject`; never probe `ctx.foo` before declaring it.
- Keep cross-plugin runtime dependencies behind services, events, slots, or another published contract. Allow `import type` only when it does not create a runtime edge.
- Confirm ownership for each registration API. `ctx.on`, tool registrations and slot registrations are fiber-owned; an API returning an unowned disposer must be adopted through `ctx.effect()`. Wrap external DOM nodes, subscriptions, timers, sockets, workers, and child processes in a disposing effect as well.
- Let required misconfiguration fail loudly. Do not turn a missing required service, wrong path, duplicate key, or invalid config into a plausible partial success.
- Keep tool arguments read-only, honor `AbortSignal`, return canonical JSON, and separate model rendering from UI presentation.
- For conditional tools, use `register(definition, { when })` and the step's resolved tool set. Do not add or remove callable tools through `system-prompt/assemble`. Custom compositions must mount an executor; `tools.mode` and `DSH_TOOLS_MODE` are removed in the checked release.
- Select the next step's model through `agent.model.select(...)`; do not add `agent/request` routing listeners. Await projection registration before exposing synchronous readers; async plugin setup returns `void`, not the projection handle.
- Call `next()` in a waterfall listener unless intentionally and contractually stopping the chain.
- Persist model-visible context through session events or supported injection APIs so replay, fork, and resume reconstruct the same request.
- Keep conversation node identity stable from running to settled state.
- Build the declared artifacts. Do not point exports or package `files` at missing output.

Do not edit generated files when the repository declares another source of truth. Change the generator or ledger and regenerate.

## 5. Validate the real plugin

Discover the target repository's gates; do not assume command names. Run evidence in increasing scope:

1. Typecheck every changed source entrypoint.
2. Run inject/export, dependency, manifest, lint, and package-shape checks that cover the changed package.
3. Test each model-visible behavior and every important error, cancellation, and disposal path.
4. Build Host and Client artifacts and inspect the exported files.
5. Inspect the expanded config, then boot a real Loader composition and verify activation. `--dump-config` alone is boot-free and does not prove service readiness.
6. Exercise the model-facing path in a real session.
7. For UI, click through desktop and narrow layouts, including running, settled, error, empty, close, and reopen states.
8. Unload or disable the plugin and verify that its registrations and external resources disappear while the host and unrelated plugins continue working.

After building, run the bundled deterministic package audit:

```bash
python3 <skill-dir>/scripts/audit_plugin.py <plugin-dir> \
  --dsh-version "$TARGET_DSH_VERSION" \
  --require-built
```

Fix every error. Review warnings against the actual plugin shape. This audit checks manifests, exports, pinned runtime dependencies, scripts, packaged files, bundle references, and common function-plugin export mistakes. It cannot prove service activation, double mounting, model behavior, replay, UI behavior, or cleanup; keep the real-composition steps above.

Confirm that aggregate green commands actually include the changed package and tests. A test file outside the runner or a source file outside typecheck is missing evidence.

Read [references/validation-and-casebook.md](references/validation-and-casebook.md) for the verification matrix and failure patterns.

## 6. Record composition and limitations

Update the target project's authoritative records for:

- self-built, forked, or community lineage;
- one installation channel;
- added, removed, refused, or disabled state;
- runtime compatibility;
- Model Experience, token budget, and KV-cache effect;
- Known Limitations and Deferred Work;
- upstream URL, revision, license, and local changes for a fork.

Do not claim completion from source inspection alone. Report the exact commands, real-composition evidence, browser or session checks, and unload result. State unverified items plainly.

## Stop conditions

Stop implementation and report the reason when:

- an existing capability already satisfies the request;
- no current owner or consumer exists;
- the only path edits the official checkout or forks/replaces a product surface without authorization;
- the design duplicates a service owner, slot key, file tree, or installation channel;
- model-visible state cannot be reconstructed after replay, fork, or resume;
- an external side effect has no supported cleanup path;
- required configuration would silently degrade;
- verification cannot cover the actual mounted package.

Use [references/validation-and-casebook.md](references/validation-and-casebook.md) to distinguish a real product gap from an operational trace or a surface already owned by the host.
