# DSH 0.2.2 plugin-development checkpoint

Checked on **2026-11-07** against release tag **`dsh-v0.2.2-rc.1`**, commit `66491b05e3f05ad35bcdd4f6cd7ed26041d9e3db`. This is a release candidate, published on November 4, not a stable-release claim. The CLI npm `latest` and `next` tags both resolved to this version at review time. [Release notes](https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.2.2-rc.1)

Use this checkpoint to review older plugins. The general workflow still applies to other releases, but signatures, dependency graphs and examples must be checked against the version actually installed.

## 1. Runtime and package requirements

The checked release requires **Node.js >=24.9.0** and ships **Cordis 4.1.0**, Loader 1.1.0 and Include 1.1.0. The starter now targets Node 24 and declares its runtime requirements. A desktop application's bundled Node runtime and the Python SDK's packaged carrier have separate installation concerns. [Node migration](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/docs/upgrade-guide/v0.2.1-rc.2/node-24/guide.md)

Do not resolve every package through its npm `latest` tag: at this checkpoint, `@deepseek-ai/dsh-tools` still had `latest=0.0.1-rc.1` while `next=0.2.2-rc.1`. Use explicit versions obtained from the target release. Cordis's tags also need independent verification. [CLI metadata](https://registry.npmjs.org/@deepseek-ai%2fdsh), [tool package metadata](https://registry.npmjs.org/@deepseek-ai%2fdsh-tools)

The launcher checks `engines.dsh` first; without it, DSH peer requirements provide the compatibility fallback. Use an exact prerelease until a wider range is verified. This field controls compatibility admission; it does not install or align package copies. [Compatibility migration](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/docs/upgrade-guide/v0.2.1-alpha.3/plugin-engines-dsh/guide.md)

Host dependencies that must share the runtime instance belong in `peerDependencies`, with matching exact `devDependencies` for standalone development. Ordinary utilities can remain production dependencies. Browser and type-only relationships belong in dev dependencies; follow the target build's explicit external-module contract. `dsh.bundle.patch` supports either a string or an ordered list. Git-source installation needs a self-contained build and explicit build-script permission; a prebuilt npm package or tarball follows a different path. [Packaging guide](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/docs/user/develop/basic/publish.md)

A clean installation of the old starter failed type checking because published LLM declarations referenced `dsh-attachment` and `dsh-package-manifest`, which were not installed. The current starter supplies both as exact dev dependencies and keeps full type checking. This is a verified workaround for this release's published type graph; reassess it at the next checkpoint instead of disabling declaration checks.

## 2. Tool registration and execution

Tool definitions still use `defineTool` and `ctx.tools.register`. Conditional availability now belongs to `register(definition, { when })`. The loop resolves availability once per proposed step and shares that `toolSet` across schema exposure, native dispatch, PTC and retries. A false condition omits the tool; a thrown condition fails preparation. A custom programmatic caller resolves the set, passes it to assembly and execution, and disposes it after settlement.

`system-prompt/assemble` only transforms presentation sections, contexts and variables. It no longer carries a mutable callable-tool list. Custom dispatchers use `tools.executable`, not an unrestricted definition lookup. [Conditional-tool migration](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/docs/upgrade-guide/v0.2.1-rc.2/conditional-tools/guide.md)

`tools.mode`, `tools.maxParallelSubCalls` and `DSH_TOOLS_MODE` no longer select execution. A composition mounts a native or PTC executor; PTC also needs a compatible runtime provider. The shipped base composition already selects native execution, so a normal tool plugin must not mount a second executor. Programmatic execution uses complete raw-call batches. [Executor migration](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/docs/upgrade-guide/v0.2.1-rc.2/tool-executor-plugins/guide.md)

Canonical execution values are distinct from durable model content. Session events retain rendered content and optional metadata; they do not automatically retain the canonical value itself. Host presentation callbacks do not control built-in Web cards, which derive their view through Client slots. [Tool contract](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/packages/core/tools/README.md)

## 3. Model selection

Use `agent.model.current()` and `agent.model.select({ provider, model, reasoningEffort? })`. Selection affects the next step whose preparation has not started; a prepared step and its retries keep their captured choice. Do not add `agent/request` listeners: the event is deprecated and existing listeners cannot change routing or reasoning effort. Read the captured selection from the step or assembly context. [Model-selection migration](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/docs/upgrade-guide/v0.2.1-alpha.4/session-model-selection/guide.md)

## 4. Projection readiness and cleanup

Await `ctx.sessionProjections.register(definition)` before publishing synchronous readers. Keep the returned handle and use `handle.stateOf(session)`; explicitly releasing it is asynchronous. Registration remains owned by the calling fiber.

An async `apply` or effect must not return the handle: Cordis interprets an effect's result as cleanup, and the handle is not a disposer. Await registration and return `void`. The deprecated callable-thenable compatibility behavior is not a pattern for new plugins. [Projection contract](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/packages/session/session-projection/README.md)

## 5. Client registration and presentation

Use `ctx.slots.inject(slotName, () => ctx.slots.register(...))` when contributing to a slot declared by another package. This binds the contribution to declaration, removal and redeclaration; injecting a related business service does not establish slot readiness.

`dsh.client.inject` contains informational package names. Cordis `inject` contains service names and governs activation. `dsh.client.external` declares exact module-table requests for permitted infrastructure edges; it must not be used to import a feature plugin's implementation. Keep `platform: 'web'` for the shared Web renderer, including Desktop. [Client authoring contract](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/packages/client/AGENTS.md)

Resource context menus now have a public `contextMenus` registry. Prefer that service for right-click actions; follow its effect/disposer contract rather than assuming every service method named `register` automatically adopts its result. [Context-menu API](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/packages/client/ui-context-menu/README.md)

## 6. Composition and configuration integrations

`--dump-config` expands layers without booting. It cannot validate service activation, plugin readiness or actual execution. Use it before, not instead of, a Loader boot. Public discovery excludes `private` packages; keep that flag during development and deliberately change it for publication. [Packaging guide](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/docs/user/develop/basic/publish.md)

Consumers of official bundle lists now import them from `@deepseek-ai/dsh-official-bundles`, not `dsh-app-boot`. Custom `EntryTree` subclasses use `commit(change)` in place of `write()`, patch application returns clones, and Include persistence needs awaited flushes. These changes matter to installers and configuration integrations; ordinary tool plugins should not add those dependencies. [Bundle-list migration](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/docs/upgrade-guide/v0.2.1-rc.2/official-bundle-lists/guide.md), [Loader migration](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.1/docs/upgrade-guide/v0.2.2-alpha.2/cordis-loader-entry-trees/guide.md)

## 7. Development branch is a separate target

At review time `master` was `fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159` and differed from the release. It contains a new `hoc` slot kind for wrapping owner content and a naming policy for new first-party experimental packages without the `experimental` prefix. Neither should be assumed available in 0.2.2-rc.1, nor should the first-party naming policy trigger renaming of existing third-party packages. Verify the exact runtime before adopting either. [HOC decision](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/notes/implemented/architecture/2026-11-03-hoc-slot-kind.md), [Naming decision](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/.agents/notes/implemented/architecture/2026-11-04-unprefixed-experimental-package-names.md)

## 8. Evidence and limits

For the starter at this checkpoint, validation includes a clean npm install, strict TypeScript check, build, native registry/executor invocation, canonical and rendered result checks, pre-cancellation, plugin unload, and the package audit. Python tests also cover ordered patch lists, packaged files, path containment and version mismatches. CI repeats the generated-package check on Node 24.9.0.

These checks do not call a live LLM, boot a full CLI profile through Loader, prove Session replay or exercise a browser. They establish a working Host starter and updated guidance; each real product plugin still needs the workflow's relevant runtime and UI evidence. No schedule or production runtime upgrade is implied by this checkpoint.
