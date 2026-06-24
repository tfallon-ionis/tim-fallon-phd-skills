# Modeling and Specification

Use this reference for architecture-as-code, diagrams, ADRs, requirements, systems engineering, Agile vs specification, and model/tool recommendations.

## Table of Contents

- Specificity gradient
- Model-centric vs diagram-centric
- Peer skills
- Tool guidance
- Specification dose
- Systems engineering lens
- Anti-bureaucracy guardrails
- Architecture documentation set
- Review checklist

## Specificity Gradient

Use this gradient as a map of durability and change rate:

```text
Business ecosystem
  -> User goals
  -> User tasks
  -> System tasks
  -> System behaviours
  -> Code
```

The upper bands are usually lower-churn, more durable, and higher-reversal-cost. The lower bands are more specific, higher-churn, and more disposable.

Make coarse, durable commitments explicit. Keep fine, fast-changing details cheap to change.

Do not confuse "defer specificity" with "add abstraction." Deferring a perishable decision often means doing less, not building a framework to postpone it.

## Model-Centric vs Diagram-Centric

Diagnose architecture tooling by whether it defines a shared model.

| Type | Examples | Use |
|---|---|---|
| Diagram-centric | PlantUML, Mermaid, D2, C4-PlantUML | One-off diagrams, sequence diagrams, class sketches, low-level explanatory pictures |
| Model-centric | LikeC4, Structurizr, Context Mapper, ArchiMate tooling, Ilograph | One semantic model projected into many synchronized views |

PlantUML is useful, but it does not maintain a shared semantic model across diagrams. If the user wants multi-level cartography, traceability, or rename-once consistency, recommend model-centric tooling.

## Peer Skills

Use installed peer skills for concrete artifact work:

- `$likec4-dsl` owns exact LikeC4 syntax, CLI validation/export commands, predicates, deployment snippets, dynamic views, and project configuration.
- `$plantuml` owns PlantUML diagram creation, syntax selection, validation, and PNG/SVG conversion.
- `$domain-modeling` owns `CONTEXT.md`, ubiquitous language, and ADR capture while modeling.
- `$codebase-design` owns module/interface/seam vocabulary when architecture work turns into code shape.
- `$request-refactor-plan` owns interview-driven refactor plans split into tiny working commits.

Legible Machine should recommend the modeling level and tool family; the peer skill should produce exact syntax or run the artifact workflow.

## Tool Guidance

Prefer this staged toolchain:

1. **LikeC4** for the main learn-by-doing architecture model when custom element kinds and arbitrary nesting matter. It fits the full gradient better than fixed C4 tools.
2. **Structurizr** when the team wants the C4 reference implementation, stricter C4 vocabulary, or established C4 practice.
3. **Context Mapper** for DDD bounded contexts, context maps, aggregates, user stories, and domain events as code.
4. **ADRs plus arc42** for rationale and architecture narrative.
5. **PlantUML, Mermaid, or D2** for local diagrams that do not need shared-model consistency.
6. **ArchiMate** as vocabulary for upper business/strategy/motivation layers, but adopt it carefully because the tooling and notation can be heavyweight.
7. **SysML v2 / MBSE** only when the domain truly demands formal systems engineering rigor.

When recommending a tool, include the complexity cost and a stop condition. A modeling tool that nobody keeps current is worse than no model.

## Specification Dose

gist grounds the term concretely: `gist:Specification` is "the set of characteristics and constraints on their values... sufficiently precise to allow evaluating conformance to the specification." A specification you cannot evaluate conformance against is not yet a specification — which is the proof this skill keeps asking for.

Choose specification depth by criticality, reversal cost, and iteration cost:

| Situation | Bias |
|---|---|
| Low reversal cost, low criticality | Iterate cheaply, write lightweight notes, avoid process overhead |
| High reversal cost | Specify interfaces, constraints, and acceptance criteria before building |
| High criticality | Use rigorous requirements, verification, and traceability |
| Unknown domain with low-cost feedback | Prototype to discover the spec, then record the durable learning |
| Regulated/security/safety/ledger core | Move toward systems-engineering rigor, formal methods, exhaustive tests, and explicit verification |

The synthesis is: specify the low-churn, high-criticality, high-reversal-cost, high-iteration-cost bands richly; iterate the high-churn, low-criticality, low-reversal-cost, low-iteration-cost bands cheaply. The boundary can move: better automated tests, simulation, telemetry, feature flags, reversible deploys, and recovery paths lower iteration cost and earn the right to specify less.

## Systems Engineering Lens

Use systems engineering as the mature version of this philosophy:

- ConOps maps to operational context and user goals.
- Requirements flow-down maps outer durable context to inner technical detail.
- Interface Control Documents map to explicit API and subsystem boundaries.
- Verification and validation map each requirement to a proof, test, analysis, inspection, or demonstration.
- Configuration management maps to versioned, baselined artifacts.
- MBSE/SysML maps to architecture-as-code for physical and cyber-physical systems.

Use the Vee model as a reasoning pattern, not as a command to waterfall everything:

- Left side: define need, behavior, architecture, interface, and design.
- Bottom: implement.
- Right side: integrate, verify, and validate against the matching band.

Write the acceptance test or verification plan while defining the requirement whenever failure is expensive.

Verification answers "did we build it right?" against the requirement. Validation answers "did we build the right thing?" against user, mission, or domain need. Good architecture artifacts should make both questions easier to ask.

## Anti-Bureaucracy Guardrails

Specification can become the complexity demon. Apply these guardrails:

- Prefer breadth before depth. Cover all major concerns lightly before detailing one concern deeply.
- Require a named owner for every requirement. Delete ownerless requirements.
- Require a verification method for every high-criticality or high-failure-cost requirement: test, analysis, inspection, demonstration, model check, conformance harness, or human review.
- Tailor rigor to criticality. Back-of-envelope is fine for low-risk decisions; formal traceability is for high-risk ones.
- Treat an unread spec as a defect; rewrite, shrink, or move it to the audience that will use it.
- Keep specs close to code, version-controlled, linked, and easy to diff.
- Capture why in ADRs. Do not force diagrams to carry rationale they cannot express well.
- Add telemetry, simulation, CI, reversible deploys, and recovery paths to lower iteration cost before adding process.

## Architecture Documentation Set

For a substantial design, produce only the audience-fit artifacts that will be used:

- A one-page context/ConOps summary: actors, goals, workflows, constraints, non-goals.
- A model-centric architecture view: LikeC4/Structurizr/Context Mapper as appropriate.
- One or more ADRs for high-reversal-cost decisions.
- Interface contracts for durable boundaries.
- Verification plan: tests, checks, demos, or analyses proving the important claims.

Avoid README sprawl, stale diagrams, and unowned documents.

## Review Checklist

1. Is this a durable commitment or a perishable implementation detail?
2. Is the requested rigor justified by criticality and reversal cost?
3. Does the model have one source of truth, or are diagrams drifting manually?
4. Does every high-level statement trace to a concrete behavior, interface, or verification?
5. Does every detailed mechanism trace back to a user, mission, or domain goal?
6. Is the spec shaped for the intended audience strongly enough that they will actually read and use it?
7. What will make the model stale, and who will update it?
8. Is this artifact replacing conversation, preserving a decision, or proving a contract? If none apply, delete or shrink it.
