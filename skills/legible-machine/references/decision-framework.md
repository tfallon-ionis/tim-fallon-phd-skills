# Decision Framework

Use this reference for ordinary engineering choices: code shape, module boundaries, dependency decisions, refactors, API style, Rust-style explicitness, DDD, htmx/hypermedia, and complexity reduction.

## Table of Contents

- Core thesis
- Layer map
- Legibility dials
- Minimalism and ponytail
- Edge rules
- Core rules
- Module and abstraction rules
- DDD rules
- Rust-style explicitness rules
- Review checklist

## Core Thesis

Optimize for whole-system legibility under cognitive-load constraints.

The enemy is not length. The enemy is complexity: hidden behavior, interacting parts, unknown unknowns, change amplification, stale rationale, unclear ownership, and commitments made at the wrong layer.

The school coheres only if "verbose" means "explicit enough to make important behavior visible." Verbosity is a price, not a virtue.

## Layer Map

Use the layer to decide which style is correct:

| Layer | Bias | Good explicitness | Bad explicitness |
|---|---|---|---|
| Edge | Minimal edge | Local behavior, visible requests, simple handlers, native browser/platform | DDD aggregates for CRUD forms, framework magic, over-modeled DTOs |
| Application shell | Thin orchestration | Transaction boundaries, authorization checks, idempotency, input/output mapping | Business rules hidden in controllers or jobs |
| Domain core | Rich explicit model | Value objects, entities, aggregates, state machines, typed IDs, invariants | Primitive obsession, string-typed states, hidden exceptions |
| Architecture/interface | Durable contracts | bounded contexts, APIs, ICD-like interface docs, ADRs | Speculative plugin systems, universal abstractions |
| Operational/business context | Coarse durable language | ConOps, user goals, workflows, constraints, non-goals | Fine implementation details disguised as strategy |
| Physical storage | Swappable detail | metadata indirection when location changes, manifest/logs | semantic paths or natural keys that bake high-churn content into durable links |

Layer is not ownership or file location. A controller can contain domain-core logic by mistake; a database migration can encode an architecture/interface decision; a path or key can accidentally become stable identity. Classify by the commitment being made.

## Legibility Dials

Before recommending a style, set these dials. They are the First Pass classifiers viewed as dose levers, so the membership differs by design: **Layer** is absent because it selects the *style*, not the dose, and **Identity** is absent because it is categorical, not a low→high axis. **Criticality** carries both the kind and the severity of harm.

The dials do not all act alike. **Criticality**, **reversal cost**, and **iteration cost** are the *cost* dials — cost of harm, cost to undo, cost to learn — and they set how much rigor a decision earns. **Change rate** is the *frequency* that scales those costs, not a fourth cost; **audience** shapes the artifact, not its rigor. So a phrase like "specify the low-churn, high-criticality, high-reversal-cost, high-iteration-cost parts richly" is the frequency dial plus the three cost dials, and the bare triad "criticality, reversal cost, and iteration cost" is the same cost dials with the frequency left implicit.

| Dial | Low setting | High setting | Effect |
|---|---|---|---|
| Change rate | high churn | low churn | high churn favors swappable detail and lighter artifacts; low churn can justify durable names, models, and contracts |
| Criticality | ordinary | trust-boundary, regulated, security-critical, safety-critical, financial-ledger-critical, or otherwise catastrophic | higher criticality demands explicit invariants, conservative defaults, stronger proof, and traceability |
| Reversal cost | local deletion | durable interface, public API, persistent data, external contract, migration, retraining | higher reversal cost moves the decision up the gradient |
| Iteration cost | fast trusted feedback, safe recovery | slow feedback, scarce environment, risky exercise, hard recovery | high iteration cost favors more design before build; low iteration cost favors prototype and learn |
| Audience | same maintainer, local code | operator, domain expert, future team, external integrator, regulator, agent | broader or more distant audiences need audience-fit artifacts, not automatically more machinery |

If the user frames a choice as Agile vs specification, translate it to these dials. Software often has low iteration cost, but high-criticality software and durable interfaces often do not.

## Minimalism and Ponytail

Use `$ponytail` as the source of truth for the detailed "do less" workflow when it is installed. Do not reimplement or paraphrase the full ponytail skill here.

When `$ponytail` is unavailable, preserve only the integration principle needed by Legible Machine: remove accidental work before adding explicit machinery. Ask whether the feature, abstraction, dependency, config surface, or documentation artifact needs to exist; then prefer existing code, standard library, native platform, already-installed dependencies, and the smallest clear custom change.

Never delete or underbuild trust-boundary validation, security, data-loss prevention, accessibility, or essential observability.

## Edge Rules

At the edge, prefer local behavior and native platform semantics:

- Prefer server-rendered hypermedia for forms, CRUD, text-heavy workflows, and server-owned state.
- Prefer htmx-style behavior when the browser can remain a browser and the server owns most state.
- Use a richer client framework when substantial state never touches the server: editors, canvases, offline-first flows, real-time collaboration, drag-heavy interactions, or complex local simulations.
- Keep application/hypermedia APIs tightly coupled to the owned UI. Create a separate stable data API only for real external, mobile, or third-party consumers.
- Keep DTOs boring. Do not enforce domain invariants in serialization structures when the domain core can enforce them.

## Core Rules

At the core, prefer explicit invariants. Use `$domain-modeling` when this changes the project's ubiquitous language, and use `$codebase-design` when it changes module seams or interfaces.

- Model concepts from the ubiquitous language, not database or UI accidents.
- Use value objects for money, time ranges, units, identifiers, statuses, and other values with constraints.
- Use entities when identity persists while attributes change.
- Use state machines or exhaustive enums when states and transitions matter.
- Make invalid states unrepresentable when doing so reduces reasoning load.
- Accept extra lines for visible error handling, explicit transitions, and local invariants.
- Avoid hidden control flow in high-criticality paths: swallowed exceptions, magic callbacks, implicit transactions, and framework lifecycle surprises.

## Module and Abstraction Rules

Use `$codebase-design` as the source of truth for deep-module vocabulary and interface design. Do not duplicate its definitions of module, interface, seam, adapter, depth, leverage, and locality here.

Legible Machine's local rule is only the integration rule: prefer a small, durable interface that hides real complexity; reject abstraction layers whose deletion would make the system simpler without spreading complexity back to callers.

Explicitness is not abstractness. A new abstraction layer is explicit only when it makes behavior, invariants, ownership, or failure modes easier to inspect. A layer added to "stay general" before a real cut point exists is premature commitment in disguise.

## DDD Rules

Use `$domain-modeling` as the source of truth for actively sharpening vocabulary, updating `CONTEXT.md`, and creating ADRs. Keep only the Legible Machine rule here: DDD is justified when it organizes essential domain complexity; it is ceremony when applied to edge glue or CRUD surfaces that do not carry domain invariants.

For identity decisions, read [identity-and-location.md](identity-and-location.md): natural keys belong to immutable value objects/reference data; stable surrogate identity belongs to entities whose attributes can change.

## Rust-Style Explicitness Rules

The Rust strand is an aesthetic of explicit, locally visible behavior:

- Prefer explicit error channels over hidden exceptions in high-criticality core logic.
- Prefer `Option`-like absence over null-like ambiguity.
- Prefer exhaustive matches for finite states.
- Prefer newtypes/typed IDs where category confusion is plausible.
- Prefer ownership and lifetime clarity over shared mutable state.
- Use unsafe, reflection, dynamic dispatch, macros, or codegen only when the complexity is isolated and justified.

Do not recommend Rust, rewrites, or formal methods as aesthetic upgrades. Recommend them when the safety, concurrency, or correctness problem warrants the cost and can be validated.

## Review Checklist

Ask these questions in order:

1. What behavior or invariant is currently hidden?
2. If this decision is wrong, what must change: local code, persistent data, public contracts, docs, users, or partner systems?
3. What underlying need, rule, interface, or detail changes most often?
4. Is the proposal binding a high-churn detail to a durable interface?
5. Is the proposal adding indirection to solve a real identity, location, or reversal-cost problem, or only discomfort?
6. Would a maintainer understand the local behavior faster after the change?
7. Does the design reduce whole-system cognitive load, or merely move complexity somewhere less visible?
8. What runnable check proves the explicitness is real?
9. If no runnable check fits, what audience-fit inspection path, owner, or review keeps the artifact honest?
