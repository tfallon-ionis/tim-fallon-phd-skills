# Source Map

Use this reference to ground the skill in its source traditions, link to canonical sources, and preserve caveats honestly.

## Philosophy Name

Use "Legible Machine" as the working name:

```text
Make the important things explicit, and the accidental things disappear.
```

## Source Priority

Prefer sources in this order:

1. Official project documentation, standards bodies, author pages, or publisher pages.
2. Primary essays, talks, papers, and canonical repositories.
3. Secondary summaries only when they add context or the primary source is unavailable.
4. The original synthesis document only as provenance for this skill's framing.

## Original Synthesis Inputs

These URLs were explicitly present in the research document that produced this skill:

- htmx essays: <https://htmx.org/essays/>
- Dorian Taylor, "The Specificity Gradient": <https://doriantaylor.com/the-specificity-gradient>
- grug-brained development: <https://grugbrain.dev/>
- FrankenSQLite: <https://github.com/dicklesworthstone/frankensqlite>
- Ponytail: <https://github.com/DietrichGebert/ponytail>
- Lewis Campbell, "Reject Agility, Embrace Specification": <https://lewiscampbell.tech/blog/260622.html>
- Vitalik Buterin, "A shallow dive into formal verification": <https://vitalik.eth.limo/general/2026/05/18/fv.html>
- Original captured Claude conversation, provenance only: <https://claude.ai/chat/8b663e32-fec5-44ec-bcb3-08600a301040>

## Hypermedia and Minimal Edges

- htmx essays index: <https://htmx.org/essays/>
- htmx, "Locality of Behaviour": <https://htmx.org/essays/locality-of-behaviour/>
- htmx, "When Should You Use Hypermedia?": <https://htmx.org/essays/when-to-use-hypermedia/>
- htmx, "Splitting Your Data & Application APIs: Going Further": <https://htmx.org/essays/splitting-your-apis/>
- htmx, "Why I Tend Not To Use Content Negotiation": <https://htmx.org/essays/why-tend-not-to-use-content-negotiation/>
- Carson Gross, Adam Stepinski, Deniz Aksimsek, *Hypermedia Systems*: <https://hypermedia.systems/>
- *Hypermedia Systems* bibliographic record: <https://books.google.com/books/about/Hypermedia_Systems.html?id=8UQF0QEACAAJ>

Use these sources for edge-layer guidance: hypermedia-driven applications, locality of behavior, browser-native workflows, and separate hypermedia/application APIs vs general data APIs.

## Complexity Reduction and "Do Less"

- grug-brained development: <https://grugbrain.dev/>
- Ponytail skill: <https://github.com/DietrichGebert/ponytail>
- Ponytail portability notes: <https://github.com/DietrichGebert/ponytail/blob/main/docs/agent-portability.md>
- Ponytail review skill: <https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail-review/SKILL.md>

Use `$ponytail` as the peer skill for detailed "do less" behavior when it is installed. Install with `npx skills add DietrichGebert/ponytail` when using the skills CLI.

## Specificity Gradient and Shearing Layers

- Dorian Taylor, "The Specificity Gradient": <https://doriantaylor.com/the-specificity-gradient>
- Dorian Taylor's main technical writing site: <https://doriantaylor.com/>
- Dorian Taylor, "On the 'Building' of Software and Websites": <https://doriantaylor.com/on-the-building-of-software-and-websites>
- Dorian Taylor, "Confluence" / shearing-layer context: <https://dorian.substack.com/p/confluence>
- Stewart Brand, "Shearing Layers" bibliographic entry: <https://www.taylorfrancis.com/chapters/edit/10.4324/9780080468129-39/shearing-layers-brand-stewart>

Use these sources for the gradient from durable business/goal bands to perishable code and for the warning against bridging bands with the wrong level of specificity.

## Domain Modeling and Core Explicitness

- Eric Evans / Domain Language DDD resources: <https://www.domainlanguage.com/ddd/>
- Eric Evans, *Domain-Driven Design* publisher page: <https://www.oreilly.com/library/view/domain-driven-design-tackling/0321125215/>
- Martin Fowler, "Domain Driven Design": <https://martinfowler.com/bliki/DomainDrivenDesign.html>
- Martin Fowler, "Bounded Context": <https://martinfowler.com/bliki/BoundedContext.html>
- Vaughn Vernon, *Implementing Domain-Driven Design* publisher page: <https://www.informit.com/store/implementing-domain-driven-design-9780133039894>
- Vaughn Vernon, *Implementing Domain-Driven Design* sample pages: <https://ptgmedia.pearsoncmg.com/images/9780321834577/samplepages/0321834577.pdf>
- John Ousterhout, *A Philosophy of Software Design* official page: <https://web.stanford.edu/~ouster/cgi-bin/book.php>
- John Ousterhout, *A Philosophy of Software Design* ACM record: <https://dl.acm.org/doi/10.5555/3288797>
- Gary Bernhardt, "Boundaries": <https://www.destroyallsoftware.com/talks/boundaries>
- Gary Bernhardt, "Functional Core, Imperative Shell": <https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell>
- gist minimalist upper ontology (Semantic Arts): <https://www.semanticarts.com/gist/> (v14.1.0 used at time of writing)
- gist ontology repository: <https://github.com/semanticarts/gist>

Use these sources for bounded contexts, ubiquitous language, entities/value objects, deep modules, complexity as cognitive load, and functional-core/imperative-shell layer separation. Use gist as a worked example of a minimal-core domain foundation: fewest primitives with rich composition, classification carried as category instances and reference data rather than proliferating subclasses, and stable persistent identifiers decoupled from ontology packaging and hosting (see [identity-and-location.md](identity-and-location.md)).

## Rust-Style Explicitness and Safety-Critical Code

- The Rust Book, recoverable errors with `Result`: <https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html>
- The Rust Book, concurrency chapter: <https://doc.rust-lang.org/book/ch16-00-concurrency.html>
- FrankenSQLite repository: <https://github.com/dicklesworthstone/frankensqlite>
- TigerStyle: <https://tigerstyle.dev/>
- TigerBeetle `TIGER_STYLE.md`: <https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md>
- TigerBeetle site: <https://tigerbeetle.com/>

Use these sources for visible error handling, typed categories, compile-time checks, explicit limits, assertions, and the caveat that a Rust rewrite is not evidence of quality without conformance tests.

## Architecture as Code and Modeling Tools

- PlantUML site: <https://plantuml.com/>
- PlantUML repository: <https://github.com/plantuml/plantuml>
- Mermaid documentation: <https://mermaid.js.org/>
- D2 documentation: <https://d2lang.com/>
- C4 model official site: <https://c4model.com/>
- Simon Brown site: <https://simonbrown.je/>
- Structurizr site: <https://structurizr.com/>
- Structurizr DSL documentation: <https://docs.structurizr.com/dsl>
- Structurizr ADR documentation: <https://docs.structurizr.com/dsl/adrs>
- Structurizr decisions UI documentation: <https://docs.structurizr.com/ui/decisions/>
- LikeC4 site: <https://likec4.dev/>
- LikeC4 model documentation: <https://likec4.dev/dsl/model/>
- LikeC4 view predicates: <https://likec4.dev/dsl/views/predicates/>
- LikeC4 repository: <https://github.com/likec4/likec4>
- Context Mapper documentation: <https://contextmapper.org/docs/home/>
- Context Mapper bounded-context documentation: <https://contextmapper.org/docs/bounded-context/>
- Context Mapper user requirements: <https://contextmapper.org/docs/user-requirements/>
- Context Mapper DSL repository: <https://github.com/ContextMapper/context-mapper-dsl>
- ArchiMate overview, The Open Group: <https://www.opengroup.org/archimate-forum/archimate-overview>
- ArchiMate tool: <https://www.archimatetool.com/>
- Ilograph: <https://www.ilograph.com/>

Use LikeC4 as the default recommendation when the user needs a flexible, model-centric, text-based architecture map with custom element kinds. Use Structurizr for stricter C4. Use PlantUML/Mermaid/D2 for local diagrams that do not need shared-model consistency.

## Architecture Rationale and Docs as Code

- arc42 site: <https://arc42.org/>
- arc42 documentation: <https://docs.arc42.org/>
- arc42 section 9, architecture decisions: <https://docs.arc42.org/section-9/>
- Michael Nygard, "Documenting Architecture Decisions": <https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
- ADR GitHub organization and overview: <https://adr.github.io/>
- Martin Fowler, "Architecture Decision Record": <https://martinfowler.com/bliki/ArchitectureDecisionRecord.html>
- Log4brains: <https://github.com/thomvaill/log4brains>
- adr-tools: <https://github.com/npryce/adr-tools>

Use these sources when diagrams need a companion explanation of why a decision was made.

## Systems Engineering, Specification, and Formal Methods

- Lewis Campbell, "Reject Agility, Embrace Specification": <https://lewiscampbell.tech/blog/260622.html>
- NASA Systems Engineering Handbook landing page: <https://www.nasa.gov/reference/systems-engineering-handbook/>
- NASA Systems Engineering Handbook PDF: <https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf>
- INCOSE Systems Engineering Handbook page: <https://www.incose.org/resources-publications/technical-publications/se-handbook/>
- INCOSE Systems Engineering Handbook, 5th edition resource page: <https://www.incose.org/resource/incose-systems-engineering-handbook-fifth-edition-updating-the-reference-for-practitioners/>
- INCOSE Systems Engineering Handbook, Wiley page: <https://www.wiley.com/INCOSE%2BSystems%2BEngineering%2BHandbook%2C%2B5th%2BEdition-p-9781119814290>
- Royce, "Managing the Development of Large Software Systems": <https://dl.acm.org/doi/10.5555/41765.41801>
- Royce paper PDF mirror: <https://www.praxisframework.org/files/royce1970.pdf>
- OMG SysML v2 overview: <https://www.omg.org/spec/SysML/2.0/Beta2/About-SysML>
- SysML v2 release repository: <https://github.com/systems-modeling/sysml-v2-release>
- OMG press release on SysML v2 adoption: <https://www.omg.org/news/releases/pr2025/07-21-25.htm>
- AWS, "How Amazon Web Services Uses Formal Methods": <https://www.amazon.science/publications/how-amazon-web-services-uses-formal-methods>
- CACM, "How Amazon Web Services Uses Formal Methods": <https://cacm.acm.org/research/how-amazon-web-services-uses-formal-methods/>
- CACM, "Systems Correctness Practices at Amazon Web Services": <https://cacm.acm.org/practice/systems-correctness-practices-at-amazon-web-services/>
- Leslie Lamport's TLA+ page: <https://lamport.azurewebsites.net/tla/tla.html>
- Vitalik Buterin, "A shallow dive into formal verification": <https://vitalik.eth.limo/general/2026/05/18/fv.html>

Use these sources for cost-of-iteration framing, ConOps, requirements flow-down, verification and validation, the Vee model, MBSE, formal methods, and the warning that specification volume is not the same as legibility.

## Identity, Location, and Persistent References

- E. F. Codd, "Extending the database relational model to capture more meaning": <https://dl.acm.org/doi/10.1145/320107.320109>
- IBM Research record for Codd 1979: <https://research.ibm.com/publications/extending-the-database-relational-model-to-capture-more-meaning>
- Hadley Wickham, "Tidy Data" (tidyverse article): <https://tidyr.tidyverse.org/articles/tidy-data.html>
- Tim Berners-Lee / W3C, "Cool URIs don't change": <https://www.w3.org/Provider/Style/URI>
- DOI and Handle System factsheet: <https://www.doi.org/the-identifier/resources/factsheets/doi-system-and-the-handle-system>
- DOI and PURL factsheet: <https://www.doi.org/the-identifier/resources/factsheets/doi-system-and-persistent-urls>
- Internet Archive PURL administration: <https://purl.archive.org/>
- OCLC PURL background: <https://www.oclc.org/research/areas/data-science/purl.html>
- ARK Alliance: <https://arks.org/>
- ARK identifier scheme IETF draft: <https://www.ietf.org/archive/id/draft-kunze-ark-34.html>
- Apache Iceberg documentation: <https://iceberg.apache.org/docs/latest/>
- Apache Iceberg specification: <https://iceberg.apache.org/spec/>
- Apache Iceberg evolution documentation: <https://iceberg.apache.org/docs/latest/evolution/>
- Delta Lake transaction log protocol: <https://delta.io/blog/2023-07-07-delta-lake-transaction-log-protocol/>
- Delta Lake protocol specification: <https://github.com/delta-io/delta/blob/master/PROTOCOL.md>
- Databricks Delta Lake overview: <https://docs.databricks.com/aws/en/delta/>

Use these sources for the distinction between stable identity, mutable content, logical references, and storage location. Use the tidy-data article for canonical table/column/row shape: observational unit as entity, value object or reference datum as dimension.

## Skill Packaging and Cross-References

- Agent Skills specification: <https://agentskills.io/specification>
- Vercel guide to creating, installing, and sharing skills: <https://vercel.com/kb/guide/agent-skills-creating-installing-and-sharing-reusable-agent-context>
- Vercel Labs `skills` CLI: <https://github.com/vercel-labs/skills>
- RFC discussion for `skills.json` package dependencies: <https://github.com/agentskills/agentskills/discussions/210>

The current portable Agent Skills format supports relative references to files inside one skill. It does not define runtime skill-to-skill imports. Keep ponytail as an optional peer skill for now; if package-level dependency manifests become standard, declare ponytail there instead of copying its text.

## Installed Peer Skills

These peer skills are installed locally in `.agents/skills/` in this workspace. Point to them instead of duplicating their detailed instructions:

- `/ask-matt`: router over the Matt Pocock skill flows. Source: `mattpocock/skills`, installed with `npx skills add mattpocock/skills --skill ask-matt`.
- `$codebase-design`: deep-module vocabulary and interface design: module, interface, seam, adapter, depth, leverage, locality. Source: `mattpocock/skills`, installed with `npx skills add mattpocock/skills --skill codebase-design`.
- `$domain-modeling`: ubiquitous language, `CONTEXT.md`, bounded vocabulary, and ADR capture. Source: `mattpocock/skills`, installed with `npx skills add mattpocock/skills --skill domain-modeling`.
- `/improve-codebase-architecture`: repo-wide scan for deepening opportunities and visual HTML architecture report. Source: `mattpocock/skills`, installed with `npx skills add mattpocock/skills --skill improve-codebase-architecture`.
- `$likec4-dsl`: exact LikeC4 DSL and CLI syntax. Source: well-known `likec4.dev`, installed with `npx skills add likec4.dev --skill likec4-dsl`.
- `$plantuml`: PlantUML diagram creation and image conversion. Source: `SpillwaveSolutions/plantuml`, installed with `npx skills add SpillwaveSolutions/plantuml --skill plantuml`.
- `$tdd`: red-green-refactor, public-interface tests, tracer bullets, and integration-style behavior tests. Source: `mattpocock/skills`, installed with `npx skills add mattpocock/skills --skill tdd`.
- `$request-refactor-plan`: detailed refactor planning via user interview, tiny commits, and issue creation. Source: `mattpocock/skills`, installed with `npx skills add mattpocock/skills --skill request-refactor-plan`.
- `$review`: diff review against standards and spec. Source: `mattpocock/skills`, installed with `npx skills add mattpocock/skills --skill review`.
- `$writing-great-skills`: skill-writing vocabulary: progressive disclosure, context pointers, duplication, sprawl, and leading words. Source: `mattpocock/skills`, installed with `npx skills add mattpocock/skills --skill writing-great-skills`.

## Optional Jeffrey's Skills Core Peer Candidates

These peers are not required for portable use of Legible Machine. They are subscription catalog candidates from <https://jeffreys-skills.md/skills> that can extend the skill when installed through the `jsm` CLI. Install any listed peer with `jsm install <skill-name>`.

Specification alignment: ground the term in `gist:Specification` — "the set of characteristics and constraints on their values... sufficiently precise to allow evaluating conformance" (see [modeling-and-specification.md](modeling-and-specification.md)). That definition has two halves: the characteristics and constraints (what must hold) and the conformance evaluation (the proof it holds). Jeffrey's catalog operationalizes the second half, using "spec", "specification", and adjacent terms as executable verification against concrete contracts: conformance, parity, golden artifacts, metamorphic relations, formal proof loops, and evidence packs. That is coherent with Legible Machine's verification side, but it does not supply the first half — Legible Machine's broader requirements flow-down from business ecosystem, user goals, user tasks, system tasks, system behaviours, and code, which decides which characteristics and constraints matter at each layer. Use Legible Machine to decide which layer deserves specification and how much rigor it needs; use the Jeffrey's spec-flavored peers to execute the proof, conformance, or regression workflow once the requirement or contract is chosen.

- `operationalizing-expertise`: distill expert methods into executable corpora, quote banks, operator libraries, and validators. Use as a peer when turning Legible Machine source material or philosophy into sharper skill rules.
- `mcp-server-design`: design agent-friendly MCP servers, tool names, error messages, and documentation. Use as a peer for agent-facing APIs, tool contracts, and self-correcting interface design.
- `codebase-archaeology`: systematically explore unfamiliar codebases and build working mental models. Use as a peer before applying Legible Machine to a repo the agent has not understood yet.
- `codebase-report`: produce reusable technical architecture documents from codebase exploration. Use as a peer when Legible Machine decisions need to become architecture writeups, onboarding docs, or handoffs.
- `research-software`: research software tools through source code, GitHub, and the web. Use as a peer when Legible Machine needs current, source-backed grounding for tools, libraries, or undocumented behavior.
- `testing-conformance-harnesses`: build conformance harnesses that verify implementations against specifications. Use as a peer when explicit core commitments need executable spec coverage.
- `testing-golden-artifacts`: build golden artifact regression suites for stable outputs. Use as a peer when preserving behavior across refactors, ports, generated output, CLI output, or serialization changes.
- `testing-metamorphic`: design metamorphic tests for systems where exact expected outputs are hard to know. Use as a peer for oracle-problem domains where correctness is expressed as input/output relations.
- `simplify-and-refactor-code-isomorphically`: shrink, deduplicate, and refactor code without behavior changes. Use as a peer when Legible Machine identifies ceremony or duplication that should be removed while preserving behavior.
- `de-monolithize-your-codebase-isomorphically`: split oversized files or monolith modules with empirical proof of unchanged behavior. Use as a peer when Legible Machine identifies a real module boundary that should be extracted carefully.
- `agent-ergonomics-and-intuitiveness-maximization-for-cli-tools`: audit and improve CLI ergonomics for AI agents. Use as a peer for robot modes, JSON output, help text, error design, and CLI affordances.
- `world-class-doctor-mode-for-cli-tools`: add or upgrade agent-friendly CLI `doctor` commands. Use as a peer when Legible Machine decisions point toward safe self-diagnosis, idempotent repair, or operational state remediation.

Shortcut installs by source family:

- Matt Pocock engineering skills: `npx skills add mattpocock/skills`
- LikeC4 DSL skill: `npx skills add likec4.dev --skill likec4-dsl`
- PlantUML skill: `npx skills add SpillwaveSolutions/plantuml --skill plantuml`
- Ponytail family: `npx skills add DietrichGebert/ponytail`

Portability caveat: these peer references are local composition points, not portable package dependencies. If publishing `legible-machine` by itself, leave the references as optional peer-skill hooks and keep the local fallback heuristics.

## Caveats to Preserve

- FrankenSQLite is useful as an articulation of the Rust rewrite aesthetic, not as proven evidence that rewriting mature C systems in Rust is automatically wise.
- Ponytail should remain an optional peer skill, not vendored text.
- htmx/hypermedia is a boundary-layer doctrine. Do not force it onto rich client state.
- DDD is a core/domain complexity tool. Do not use it as ceremony at every layer.
- Systems engineering can become bureaucracy. Legibility is the invariant, not spec volume.
- Specification vs iteration is a cost decision, not a tribe. Use criticality, reversal cost, and iteration cost to set the dose.
- SpaceX-style iteration works by lowering cost of iteration, not by abolishing requirements.- Natural keys are correct for immutable value objects and reference data; they are risky for mutable entities.
- Architecture models become harmful when stale. Recommend ownership and update triggers.

## Quoting Guidance

Prefer paraphrase. Quote only short phrases when they carry distinctive force, such as:

- "Make the important things explicit, and the accidental things disappear."
- "Requirements exist regardless of whether they are specified or not; you might as well write them down."
- "Cool URIs don't change."

When in doubt, cite a source by name and summarize the principle in fresh language.
