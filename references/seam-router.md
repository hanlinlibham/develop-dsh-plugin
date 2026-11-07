# DSH extension seam router

Read this file when deciding where a capability belongs. Confirm every name and signature against the target runtime; this is a routing guide, not a substitute for source inspection.

## Runtime split

| Runtime | Owns | Typical entry |
|---|---|---|
| Host | sessions, tools, model providers, filesystem, processes, policies, lifecycle | `exports["."]` |
| Client | slots, theme, conversation views, page state, browser interaction | `exports["./client"]` |

Host and Client have different Contexts and service graphs. A Client service does not exist on Host merely because both halves share a package.

## Requirement router

| Requirement | Preferred seam | Avoid |
|---|---|---|
| Add a model-callable capability | `ctx.tools.register` | patching agent loop |
| Enable a tool conditionally per step | registration `{ when }` plus the resolved tool set | editing tools in `system-prompt/assemble` |
| Choose the model for the next prepared step | `agent.model.select(...)` | changing the route in `agent/request` |
| Maintain log-derived Session state | awaited `sessionProjections.register` handle | returning a handle as an async Cordis effect |
| Add bounded context before a model step | `agent/pre-step` plus supported durable injection | privately concatenating a prompt |
| Transform or reject a request | typed waterfall event | emit listener or UI interception |
| Enforce a final monotonic denial | supported guard | hidden denial inside business execution |
| Observe a lifecycle event | emit event | waterfall without continuation |
| Check a turn before settlement | `agent/turn-stopping` | unbounded steering loops |
| Add a replaceable backend | Service Definition + Provider + Consumer | consumer importing provider implementation |
| Add an independent UI contribution | the narrowest additive slot or public UI service | querying product DOM |
| Contribute to another package's slot | `ctx.slots.inject` around registration | treating service activation as slot readiness |
| Add resource context-menu actions | `contextMenus` public registry | replacing the owner view or implementing a second menu system |
| Replace a keyed UI occupant | exact slot contract plus explicit replacement authority | guessing key or priority |
| Change global appearance | official theme tokens | a second theme system |
| Style one component | package-local styles using theme variables | mutating `document.body` or unrelated selectors |
| Add a sidebar tab or file viewer | the owning public registry service | editing the shell to name the consumer |
| Compose installation | bundle/profile/patch according to project policy | mounting the same package twice |

## Event modes

| Mode | Meaning | Listener obligation |
|---|---|---|
| waterfall | transform, wrap, recover, or stop a value-producing chain | call and return `next()` unless intentionally stopping |
| serial | ordered checkpoint | preserve ordering and await work |
| parallel | independent fan-out | avoid shared mutable ordering assumptions |
| emit | one-way notification | do not treat it as a control decision |

## Model-visible decision

Treat a capability as model-visible when it changes any of the following:

- system or user context sent to the model;
- advertised tool schema;
- tool result content;
- turn continuation or stopping guidance;
- visible skill catalog or invocation evidence.

For model-visible behavior:

1. Identify the durable session event or supported injection path.
2. Prove that replay, fork, and resume derive the same request.
3. Bound injected bytes or tokens.
4. Describe KV-cache behavior: stable prefix, append-only suffix, or invalidating change.
5. Keep canonical business data separate from rendered model content and UI presentation.

## Capability seam test

Split Definition, Provider, and Consumer only if:

- the whole capability is replaceable;
- at least two roles need independent ownership or release cadence now;
- consumers can depend on a stable definition without importing a provider;
- provider removal causes consumers to wait or deactivate through the service lifecycle.

Keep a single tool or view in one package when those conditions do not hold.

## UI replacement test

Before replacing a slot occupant, record:

- exact slot name and registration protocol;
- current occupant, key, selector, and priority semantics;
- descendant slots lost with the occupant;
- current user need that additive placement cannot meet;
- rollback and unload behavior;
- desktop and narrow-layout verification cases.

If the official view already supplies the behavior, retain it.
