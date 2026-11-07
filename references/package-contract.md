# Productized DSH package contract

Read this file when scaffolding or reviewing an out-of-tree package. Copy versions and build details from the target runtime, not from this reference.

## Contents

- [Minimal source package](#minimal-source-package)
- [Bundled helpers](#bundled-helpers)
- [package.json checks](#packagejson-checks)
- [Function plugin exports](#function-plugin-exports)
- [Required and optional services](#required-and-optional-services)
- [Reversible effects](#reversible-effects)
- [Tool contract](#tool-contract)
- [Client contract](#client-contract)
- [Installation contract](#installation-contract)
- [README contract](#readme-contract)

## Minimal source package

```text
plugin-name/
├── package.json
├── tsconfig.json
├── cordis.patch.yml
├── README.md
├── src/
│   ├── index.ts
│   └── client/index.ts     # only when a Client half exists
└── tests/
```

Compile source into declared `lib/` artifacts. Keep private packages private until publication is an explicit task.

## Bundled helpers

Use `scripts/scaffold_plugin.py` after the research and design gates when a Host-only tool is the right shape. It renders `assets/minimal-host-plugin/`, requires exact DSH and Cordis versions, and refuses to overwrite a non-empty destination.

Use `scripts/audit_plugin.py` after building to check deterministic package-shape rules. It is deliberately narrower than the repository gates and real-composition verification: it cannot prove activation, model behavior, replay, UI interaction, or unload cleanup.

## package.json checks

- Set `type: "module"` when using ESM.
- Point `exports["."]` at the compiled Host artifact.
- Add `exports["./client"]` and `dsh.client.platform: "web"` only for a Client half.
- Declare `dsh.bundle.patch` so installation activates the package.
- Put Cordis in `peerDependencies`; let the host own the runtime framework instance.
- Pin DSH RC dependencies to the exact target runtime version.
- List only files that build or exist.
- Add build, typecheck, and test scripts and ensure the repository aggregate invokes them.

Do not use source-workspace aliases from an official monorepo in an independent package unless the target repository explicitly provides them.

## Function plugin exports

```ts
import type { Context } from '@deepseek-ai/cordis'

export const name = 'my-plugin'
export const inject = ['requiredService']

export function apply(ctx: Context): void {
  ctx.requiredService.register(/* contribution */)
}
```

Use named exports. Default-export only a Service subclass when the framework contract calls for it.

## Required and optional services

Hard dependency:

```ts
export const inject = ['tools']

export function apply(ctx: Context): void {
  ctx.tools.register(/* tool */)
}
```

Optional dependency:

```ts
export function apply(ctx: Context): void {
  const optional = ctx.get('optionalService')
  if (optional === undefined) return
  optional.register(/* contribution */)
}
```

Deferred local activation:

```ts
export function apply(ctx: Context): void {
  ctx.inject(['optionalService'], inner => {
    inner.optionalService.register(/* contribution */)
  })
}
```

Never access `ctx.foo` merely to test whether `foo` exists. Undeclared property access is an error. A hard dependency missing from the tree leaves the fiber pending; a required package configuration should make that condition observable during boot validation.

## Reversible effects

Cordis-owned registrations are scoped to the plugin fiber:

```ts
ctx.on('event', listener)
ctx.tools.register(tool)
ctx.slots.register(options, renderer)
```

Use `ctx.effect()` for resources outside that ownership system:

```ts
ctx.effect(() => {
  const socket = openSocket()
  const unsubscribe = source.subscribe(onValue)
  return () => {
    unsubscribe()
    socket.close()
  }
})
```

Do not create process-wide or page-wide effects at module scope.

## Tool contract

- Use the target runtime's schema helper and inspect a current official tool.
- Validate semantic constraints that the schema cannot express.
- Treat `args` as read-only.
- Honor `exec.signal` before and during cancellable work.
- Return JSON matching the output schema.
- Render model content through the output renderer.
- Put UI-only diff, card, or intent data in supported presentation metadata.
- Keep results bounded and include provenance when the model may cite, edit, or follow a returned object.

## Client contract

- Build a separate Client artifact.
- Put service keys in the Client plugin's exported `inject`.
- Put package-name edges in `dsh.client.inject` when the manifest requires them.
- Query or inspect the live slot/service contract before using names, keys, priorities, selectors, or props.
- Prefer additive inner slots.
- Scope styles to the package and reuse theme variables.
- Keep stable node keys across running and settled forms.
- Exercise loading, error, empty, close, reopen, desktop, and narrow states.

## Installation contract

Choose one channel per mounted package:

- package bundle through `dsh plugin add`;
- project-owned patch/generator;
- explicit local `link:` for a maintained fork when project policy requires it.

Do not mount the same package through a profile bundle and a patch. Treat generated composition files as projections when a ledger or generator owns them.

## README contract

Include:

- one-sentence responsibility;
- provided and consumed services, events, tools, and slots;
- Host/Client boundary;
- installation and removal instructions;
- runtime compatibility;
- Model Experience and token/KV-cache effect;
- Known Limitations and Deferred Work;
- validation commands and real-product checks.
