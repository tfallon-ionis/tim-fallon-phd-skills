---
name: legible-machine
description: Legible Machine adjudicates software tradeoffs by layer, change rate, reversal cost, criticality, and identity. Use for explicitness vs verbosity, minimal edge vs rich domain core, DDD, htmx/hypermedia, Rust-style explicitness, architecture-as-code, specification vs iteration, identifier/object-store design, or complexity reduction.
---

# Legible Machine

Use this skill to make software decisions by optimizing for whole-system legibility: explicit durable commitments, minimal accidental machinery, and a clear separation between stable identity, domain meaning, implementation detail, and storage location.

The core slogan is:

> Make the important things explicit, and the accidental things disappear.

## Operating Model

Treat complexity as cognitive load: interacting parts, hidden behavior, change amplification, and unknown unknowns. Do not treat code length as complexity by itself.

Keep these three axes separate in every recommendation:

- **Verbosity**: how many words, lines, files, or artifacts exist.
- **Complexity**: how many interacting parts and hidden dependencies a maintainer must reason about.
- **Explicitness**: how locally visible the behavior, invariants, commitments, and failure modes are.

Prefer more verbosity when it buys meaningful explicitness or lowers whole-system complexity. Reject verbosity when it is ceremony, pass-through layering, speculative generality, or documentation nobody will read.

## First Pass

For any design or implementation question, classify the decision before prescribing a style:

1. **Layer**: where the decision lives in the system, not which file it appears in: edge, application shell, domain core, architecture/interface, operational/business context, or physical storage. If a proposal crosses layers, classify each part separately.
2. **Change rate**: how often the underlying need, rule, interface, or detail is expected to change, independent of how costly the change would be.
3. **Reversal cost**: what must change if the decision is wrong: none/local deletion, or migrations, contract changes, data rewrites, user retraining, or external coordination.
4. **Criticality**: the kind and severity of harm or obligation if this fails: ordinary, trust-boundary, regulated, security-critical, safety-critical, or financial-ledger-critical.
5. **Identity**: what remains the same across change: stable identity, mutable content, logical reference, storage location, or a true immutable value.
6. **Iteration cost**: the cost of getting trustworthy feedback safely: prototype, test, simulate, deploy, observe, and recover.
7. **Audience**: who must correctly understand, operate, approve, integrate with, or maintain the decision: developer, operator, domain expert, stakeholder, external integrator, agent, regulator, or future maintainer.

Layer chooses the style. The other classifiers choose the dose of rigor. Then choose the smallest method that preserves legibility at the correct layer.

## Core Workflow

1. Restate the decision in terms of the user's goal, not the proposed mechanism.
2. Classify the decision against the seven First Pass classifiers.
3. Name the complexity being fought: hidden behavior, too many moving parts, premature commitment, stale specification, primitive obsession, location coupling, surface-legibility bias, or abstractness masquerading as explicitness.
4. Apply the matching reference:
   - For everyday design and code choices, read [references/decision-framework.md](references/decision-framework.md).
   - For architecture-as-code, specification, Agile vs systems engineering, or documentation strategy, read [references/modeling-and-specification.md](references/modeling-and-specification.md).
   - For identifiers, natural keys, UUIDs, resolver indirection, S3/object-store paths, metadata indirection, or subtype-vs-category modeling, read [references/identity-and-location.md](references/identity-and-location.md).
   - For source lineage, caveats, and further reading, read [references/source-map.md](references/source-map.md).
   - For "do less", YAGNI, shortest-path, dependency avoidance, or over-engineering decisions, use `$ponytail` when it is installed. If it is not installed, read [references/source-map.md](references/source-map.md) for the peer-skill link and keep only the minimal local anti-complexity heuristic here.
   - For codebase-design, domain-modeling, LikeC4, PlantUML, TDD, refactor-planning, or workflow-routing details, use the installed peer skills listed in [references/source-map.md](references/source-map.md). Do not duplicate their detailed procedures here.
5. Choose the dose: specify the low-churn, high-criticality, high-reversal-cost, high-iteration-cost parts; iterate the high-churn, low-criticality, low-reversal-cost, low-iteration-cost parts.
6. Name the proof of legibility for the audience: a test, type check, ADR, model validation, trace, telemetry signal, demo, inspection path, or deletion.
7. Give a concrete recommendation with the tradeoff and reversal condition stated plainly.
8. Prefer implementing the recommendation or producing the requested artifact when the user asked for action.

The workflow is complete only when the recommendation is tied to the classified layer and includes a concrete proof or inspection path. If no proof is appropriate, say why the decision is intentionally judgment-only.

## Peer Skills

Legible Machine is the adjudication lens. When an installed peer skill owns the detailed workflow, use it instead of rephrasing it:

- `$ponytail`: minimalism, YAGNI, dependency avoidance, and over-engineering pressure; `$ponytail-review` and `$ponytail-audit` to review a diff or whole repo for over-engineering.
- `$codebase-design`: deep modules, interfaces, seams, adapters, leverage, locality, and testable module shape.
- `/improve-codebase-architecture`: repo-wide scan for deepening opportunities.
- `$domain-modeling`: ubiquitous language, `CONTEXT.md`, bounded domain vocabulary, and ADR capture.
- `$likec4-dsl`: exact LikeC4 syntax, validation commands, views, predicates, and project configuration.
- `$plantuml`: PlantUML diagram generation and image conversion.
- `$tdd`: red-green-refactor, public-interface tests, tracer bullets, and integration-style behavior tests.
- `$request-refactor-plan`: interview-driven refactor plans split into tiny working commits.

Legible Machine decides which lens applies and states the tradeoff; the peer skill owns the step-by-step mechanics. The fullest peer list, with sources and install commands, is in [references/source-map.md](references/source-map.md).

## Default Decision Rules

- Defer detailed "write less" behavior to `$ponytail` when available. Locally, keep only the integration rule: first ask whether the thing needs to exist, then prefer existing code, standard library, native platform, installed dependency, and the smallest clear custom code.
- Use minimal, native, local behavior at the edge: HTML, HTTP, forms, htmx/hypermedia, templates, simple handlers, thin DTOs, and visible glue.
- Use richer explicit modeling in the domain core: value objects, entities, invariants, state machines, exhaustive error handling, typed IDs, and ubiquitous language.
- Do not model the edge like the core. Do not model the core like the edge.
- Specify the low-churn/high-criticality/high-reversal-cost/high-iteration-cost richly. Iterate the high-churn/low-criticality/low-reversal-cost/low-iteration-cost cheaply. Invest in tests, simulation, telemetry, feature flags, and recovery paths when lowering iteration cost is cheaper than adding process.
- Keep durable commitments explicit: business language, bounded contexts, interfaces, failure modes, operational constraints, and verification criteria.
- Keep perishable details swappable: framework choices, physical layouts, generated code, wire details, and implementation mechanisms.
- Separate stable identity from mutable content or storage location. Add indirection only when reversal cost justifies it.
- Treat diagrams, specs, ADRs, and architecture models as tools for legibility, not proof of rigor by volume.
- Prefer deep modules over shallow pass-through modules. Use `$codebase-design` for the detailed vocabulary and procedure when changing module shape.
- Say no to speculative abstractions, plugin systems, generic factories, and "future-proofing" until a real cut point appears.

## Output Shape

When answering, lead with the recommendation, then the reasoning. Use crisp labels:

- **Verdict**: choose the direction.
- **Why**: name the First Pass classifiers that drove the decision, and the complexity being fought.
- **Tradeoff**: state what gets worse.
- **Reversal test**: state what evidence would flip the answer.
- **Proof**: name the test, type check, validation, inspection path, telemetry, or human review that shows the legibility is real.
- **Concrete next step**: name the implementation, spec, diagram, ADR, test, or deletion to perform.

For codebase work, inspect the local code first and adapt the philosophy to the actual repo instead of forcing the vocabulary onto it.

## Anti-Patterns

- Treating explicitness as abstraction. More interfaces, abstraction layers, classes, or config are not more explicit unless they make behavior or invariants easier to see.
- Treating surface readability as system legibility. Human-readable keys and paths can still create hidden coupling.
- Treating "specification" as document volume. A stale or unread spec is complexity.
- Building a general-purpose API only to power one tightly-owned front end.
- Adding a resolver, registry, metadata service, or UUID indirection when the thing is small, static, immutable, and human-operated.
- Using natural/composite keys for entities whose identifying attributes can change.
- Using primitive/string-typed values in the domain core where invariants matter.
- Proliferating subclasses or types for a classification that churns or is not known when the instance is created — it belongs in category instances or reference data instead.
- Rewriting in Rust, adopting formal methods, or adding architecture tooling as aesthetic theater without conformance tests or operational need.
- Letting agents generate large explicit-looking systems whose behavior is not locally verifiable.
- Treating iteration and specification as ideologies instead of cost decisions. The dial is criticality, reversal cost, and iteration cost.
