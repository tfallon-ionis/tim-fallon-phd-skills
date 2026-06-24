# Identity and Location

Use this reference for stable identity, mutable content, logical references, storage location, database keys, natural vs surrogate identity, UUIDs, object-store paths, resolver layers, persistent IDs, metadata catalogs, physical layout decisions, and subtype-vs-category/reference-data modeling.

## Table of Contents

- Core rule
- Tidy data
- Entity vs value object switch
- Type vs instance: categories and reference data
- Grounding in gist (and its limits)
- SQL key guidance
- Object-store guidance
- Resolver guidance
- Surface legibility vs system legibility
- Review checklist

## Core Rule

Separate stable identity from perishable content or storage location whenever the content/location can change and reversal cost is high.

Do not add indirection when the identifying content is genuinely immutable and the system is small enough that the indirection would be ceremony.

Identity is sameness across change. Do not let a mutable name, status, owner, partition, path, or representation become the thing other systems depend on as identity.

## Tidy Data

Tidy data (Wickham) is the data-layer cousin of this reference: one variable per column, one observation per row, one observational unit per table. The third rule is the identity question restated — a table's observational unit is its entity, and a value object or reference datum is a tidy dimension. Untidy shapes, such as one column holding several variables or content columns repeated across tables, are the surface-vs-system-legibility traps below. The grounding table below lines up each tabular reading with its DDD term and gist instance.

## Entity vs Value Object Switch

Use the DDD distinction:

- **Entity**: identity persists while attributes change. Use a stable surrogate or opaque identity as the primary key. Keep natural attributes as unique constraints when they express real business rules.
- **Value object / immutable reference data**: identity is the value. Use the natural key if the value is genuinely immutable in the bounded context.

Apply this per bounded context. A concept can be a value object in one context and an entity in another.

## Type vs Instance: Categories and Reference Data

Identity discipline applies to the type layer too. Do not bake a classification into durable type structure (subclasses, enums, table-per-type) when it churns, or is not yet known when the instance is created. Model it as category/reference-data instances you can add, retire, or reclassify without a migration.

Use a subclass or type only when the distinction is stable and known when the instance is created. Use a category instance or reference datum when any of these hold:

- The set of categories churns faster than you want to change the schema or model.
- The subtype is not yet known when the instance is created (minted).
- An instance may belong to several categories at once, or move between them over time.
- The distinction is descriptive, and no behavior or invariant branches on it structurally.

This is the type-layer form of the durability gradient: stable structure stays in the model; perishable classification lives in data. The gist upper ontology is the worked example. It collapsed five `Address` subclasses to two and pushed the rest to category instances precisely because the kind of address often "is not always possible to know at the time of minting"; and it moved units of measure and aspects from classes to reference data, cutting class count roughly 25% so a new unit needs no model change.

## Grounding in gist (and Its Limits)

These modeling terms stay honest when anchored to a concrete instance. The gist upper ontology supplies one for some of them, and pointedly not for others — the gap is itself worth stating. Each row also gives the plain tabular reading, so the same distinction is visible at three layers: tidy data (tables), DDD (the skill's working terms), and gist (ontology).

| Term (DDD) | Plain tabular reading (tidy data) | Concrete anchor in gist |
|---|---|---|
| Reference data | a lookup / dimension table | `gist:Aspect`, `gist:UnitOfMeasure`, `gist:Category`, `gist:ControlledVocabulary` — instances kept out of the class model |
| Category / classification | a categorical variable, or its dimension table | `gist:Category` and the category paradigm |
| Entity | the observational unit — one row per thing, identity outliving its attributes | a minted-IRI individual: `gist:Person`, `gist:Organization`, `gist:PhysicalIdentifiableItem` (the *principle*, not a class named "entity") |
| Value object | a content-defined value — often several columns together (amount + unit + aspect) | `gist:Magnitude` (one exemplar; gist has no general value-object class) |
| Aggregate | no clean tabular form — a consistency boundary | none; gist's `Composite`/`Collection`/`System` are part-whole, not consistency boundaries |

Whichever layer is most intuitive — usually the tabular one — is a valid on-ramp; the DDD and gist names follow once the row is aligned.

gist models what *exists* in a domain; it is not a catalog of code patterns. It grounds identity and reference data concretely, but it does not represent DDD's code-level constructs — aggregate consistency boundaries or in-memory mutability. Keep those grounded in DDD via `$domain-modeling` and in module shape via `$codebase-design`. Forcing a gist class onto "aggregate" would be the surface-correspondence trap below.

**False friend.** The skill's **durable commitment** means a design decision you are locked into. gist's `gist:Commitment` and `gist:Agreement` are *parties' promises to one another* — a business arrangement, not a design lock-in. Same word, different concept; the matching name is the surface-correspondence trap, not a grounding.

## SQL Key Guidance

Composite natural keys are good when all of these are true:

- The key columns are genuinely immutable.
- The key is short and stable in type.
- The key represents a value object or reference datum.
- Foreign keys remain readable and manageable.
- A database constraint enforces the claimed uniqueness.

Use surrogate keys when any of these are true:

- The row is an entity.
- Any key attribute can be corrected, renamed, merged, split, or reclassified.
- The natural key would create wide foreign keys across many tables.
- The natural key embeds business process, hierarchy, status, owner, date, or location likely to change.
- References must outlive the current representation.

Preferred compromise for entities:

- Use an internal stable primary key appropriate to the database and workload.
- Use typed IDs or explicit naming in code to avoid anonymous low integers flying around.
- Add unique constraints for real natural uniqueness.
- Expose opaque public IDs when external systems or URLs need stable references.
- Avoid reusing IDs.

## Object-Store Guidance

Treat S3/object-store paths as physical layout, not domain identity.

Use semantic paths when the dataset is small, static, manually browsed, and the layout is unlikely to change.

Prefer opaque or implementation-oriented physical paths plus a metadata/catalog layer when any of these are true:

- Partitioning may evolve.
- Files will be compacted, rewritten, backfilled, or vacuumed.
- Readers need stable logical references independent of physical layout.
- Multiple producers or consumers need consistent snapshots.
- The data product is important enough that physical reorganization must not break clients.

Prefer established table formats and catalogs over bespoke resolver layers when they fit:

- Apache Iceberg
- Delta Lake
- Hudi, where appropriate
- Glue/Hive-compatible catalogs, with awareness of their limitations

## Resolver Guidance

A resolver or metadata layer is justified when it converts many brittle references into one explicit, inspectable source of truth.

It is over-engineering when it becomes critical infrastructure for a tiny static dataset, a single producer/consumer script, or a layout humans are meant to browse directly.

Right-size the resolver before inventing one. Prefer a database unique constraint, existing catalog, table format, redirect service, or manifest file when that is enough. Build bespoke resolver infrastructure only when the existing source of truth cannot express the needed stability, history, or transactional behavior.

If adding a resolver:

- Make it versioned or transactional.
- Back it up.
- Provide an inspection path for humans and agents.
- Test missing, stale, and duplicate mappings.
- Measure latency and failure modes.
- Avoid chains of resolvers unless each layer has a distinct reason to exist.
- Define the reversal path: how clients migrate if the resolver was unnecessary or the identity scheme changes.

## Surface Legibility vs System Legibility

Human-readable identifiers and paths are not automatically legible.

Surface-legible but system-illegible:

- A primary key made from mutable attributes.
- A path that includes project status, owner, partitioning strategy, or data semantics that may change.
- Foreign keys that repeat many content columns across the schema.

Surface-illegible but system-legible:

- A stable opaque ID with a clear resolver and human-readable metadata.
- A data lake table with UUID-ish files and an inspectable transaction log.
- An internal integer primary key plus constrained natural attributes and typed application code.

Prefer system legibility over surface readability when they conflict.

## Review Checklist

1. Is this thing an entity or a value object in this bounded context?
2. Which fields can change because humans, businesses, regulations, or corrections change?
3. What references break if the identifier, logical reference, or physical path changes?
4. Is the identifier carrying mutable content, storage location, status, ownership, or implementation detail?
5. Is indirection solving a real reversal-cost problem?
6. Can the resolver/catalog fail, drift, or become a hidden dependency?
7. Would a unique constraint preserve the useful natural-key property without making it the primary identity?
8. What migration path exists if the current identity choice is wrong?
