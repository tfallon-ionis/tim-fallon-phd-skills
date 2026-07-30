# `seqspec-llm-authoring` design

**Owner:** Tim Fallon
**Status:** approved for implementation
**Decision date:** 2026-07-15
**Minimum seqspec CLI:** `>=0.4.0`

## Purpose and boundary

Create a user-invoked LLM skill that interviews a user, interprets authoritative library-preparation and sequencing-kit sources, and emits one evidence-backed Illumina seqspec profile. A profile describes one library format and one designed raw-acquisition/read configuration. It is reusable across physical sequencing runs.

The unit is deliberately not an instrument run, lane, SRA Run, biosample, or concrete FASTQ set. One physical lane pool may contain multiple library formats best described by multiple seqspec profiles; one profile may recur across many physical runs. SRA Run is an archive file-manifest unit, not a faithful inventory of a flowcell.

V1 is Illumina-only. Non-Illumina design work is deferred outside the runtime skill.

## Runtime and grounding

- The canonical home is `skills/seqspec-llm-authoring/` in this repository.
- Do not add a devcontainer, uv project, or bundled distillation of seqspec documentation.
- Require an installed `seqspec >=0.4.0`. If it is unavailable or older, permit a draft but never report completion.
- At every authoring run, read the rendered official File Format and Technical Specification pages. Use the installed schema/validator as the fallback and as a second check before declaring a feature inexpressible.
- Do not direct the runtime agent to obsolete or alternate seqspec repositories.

## Interview and evidence workflow

1. Ask for an output directory; default to `<cwd>/skill-outputs`. Warn before overwriting existing artifacts.
2. Ask first for the internal colloquial library-format name. Treat it only as a non-unique alias.
3. Require at least one authoritative source and its verbatim Zotero IEEE entry. A relevant vendor PDF or product webpage can qualify.
4. Read the representative library-kit source before asking detailed structural questions. Extract proposals, then interview one question at a time.
5. Require a representative library-preparation kit with product name, manufacturer, catalog number, and supporting sources. Equivalent additional kits are optional and require evidence.
6. Require the sequencing kit with product name, manufacturer, catalog number when documented, and supporting sources. Ask for an optional internal colloquial kit name; `none` is allowed.
7. Require manufacturers to use verified Wikidata entity URIs. A more lenient official-company-URL fallback is a possible future policy, but is intentionally not accepted by this personal skill.
8. Require a verbatim Zotero IEEE entry for every documentary source. Preserve its bracket number, even when several independently copied entries all begin `[1]`. Use a natural machine key of `<author-or-organization>_<year>_<short-title>`.
9. Separate documentary claims from user-selected acquisition configuration. Vendor documentation must support molecular structure, kit identity, and kit capability. The user may select a supported cycle split such as SE300, PE150x150, or PE100x200; never infer PE150x150 merely from “300 cycles.”
10. If sources conflict, stop and show the conflict. Record the selected and rejected claims plus the user's rationale. User confirmation may resolve a documented conflict, but may not replace missing evidence.

Supplied PDFs are not copied. Record their basename, SHA-256, authoritative URL, access date, and Zotero entry. Other supplied artifacts are handled separately from bibliographic sources.

## seqspec semantics

- `seqspec_version` is the installed CLI's supported schema version, never a kit, SOP, or profile version.
- Native Seqspec `assay_id` identifies the concrete profile and is based on the technical library-format name/version plus acquisition configuration, with an explicit disambiguator when necessary. Mirror it as `profile.seqspec_assay_id` in the sidecar and call it the Seqspec assay ID in prose. This external-format term does not imply a biological assay or a consumer's Demultiplexing Specification ID. Never derive uniqueness from the colloquial alias.
- Encode raw acquisition. PE150x150 and PE50x50 are different profiles when those were the acquired reads. In-silico trimming PE150x150 FASTQs to PE50x50 is downstream processing and does not create another seqspec.
- For fixed Illumina acquisition, set read `min_len == max_len`.
- A sequencing kit's advertised cycle capacity does not determine the allocation among R1, R2, I1, and I2. Do not use a naive sum-of-cycles compatibility rule.
- I1 and I2 are optional when unknown. In user-facing text call them i7 (Index 1) and i5 (Index 2); `index7` and `index5` are seqspec enum values, not preferred lab names.
- Known index-cycle changes alter the acquisition profile. Internal protocols use `version`, not “revision.”
- `SampleSheet.csv`, actual lane-pool membership, selected sample-index pairs, run FASTQs, and demultiplexing assignments are outside V1.
- A fixed sequence of established length but undisclosed bases may use `sequence_type: fixed` with `N` repeated to the known length and an explicit sidecar disclosure. If fixedness or length is unknown, emit a draft.

Before claiming seqspec cannot express something, inspect both the official rendered documentation and the installed executable schema/validator. The fixed-but-undisclosed representation is the motivating guardrail: it is mechanically accepted even though it is easy to miss from a cursory documentation pass.

## Barcode semantics

Use a local, versioned, faceted vocabulary in the sidecar. It may map honestly to SAM tags, but it does not depend on Biolink, OBI, or another ontology. LinkML publication and formal ontology harmonization are later interoperability work.

- `demultiplexing_barcode` is the superclass for sequences that partition reads.
- `observed_in` records I1, I2, R1, or R2 and must agree with the seqspec read projection.
- `groups_reads_by` distinguishes `flowcell_lane_pool_member`, `library_preparation_input`, and `source_cell`.
- `index_role` distinguishes i7 and i5; UDI is a relationship/scheme joining both members, not a barcode subclass.
- A UMI is a `molecular_identifier` that groups reads by `source_molecule`, not a demultiplexing barcode.
- Do not use `sample` when the actual referent is a library-preparation input, lane-pool member, or source cell.
- Avoid “sub-read” for an R1/R2 region because that term conflicts with PacBio usage.

The closest external vocabulary is the SAM/BAM tag set (`BC`, `CB`/`CR`, `MI`, `RX`, `OX`), but it does not express the full taxonomy. Record external mappings only where the correspondence is honest.

## Onlists and access control

- `sequence_type: random` is valid without an onlist only when the sequence is genuinely not known a priori.
- A sequence drawn from a finite allowed set uses `sequence_type: onlist`. Do not relabel it `random` merely because the list is unavailable.
- Design-level i7/i5 onlists describe all permissible sequences from the cited indexing kit, not the subset used in a particular lane.
- Actual UDI pairing constraints live in the sidecar because seqspec does not model the pairing relationship directly.
- The agent searches for a directly accessible authoritative onlist. It never authenticates, submits an email address, or treats an uncorroborated public mirror as authoritative.
- If access-controlled bytes are unavailable, emit a traceable draft. If the user supplies a vendor software archive or decompressed root, locate the onlist without copying it permanently.
- Persist only the onlist basename, natural `file_id`, native seqspec MD5, uncompressed-content SHA-256, stored-artifact SHA-256 when applicable, container SHA-256 when an archive was supplied, and the internal member path. Never persist the user's absolute local path.
- Hash exact bytes without newline normalization or sequence reordering. The logical-content digest is over uncompressed bytes; stored-artifact and container digests are over their stored bytes.
- Revalidation asks the user to locate the matching archive/root again. The composite validator temporarily materializes the dependency, invokes vanilla `seqspec check`, and removes it.

## Provenance sidecar

Emit `provenance.sidecar.yaml` alongside a completed seqspec. The sidecar requires `sources_schema_version: 1.1.0`; no other schema version is supported.

The sidecar contains:

- profile identity, aliases, relations, and component versions;
- separately modeled technical library-format, commercial kit, and internal SOP versions;
- an always-present concrete profile lineage, with component predecessor links only when established by evidence or the user;
- independent `previous_version` and `variant_of` relations—either or both may apply, and neither is inferred from field differences;
- verified vendor/Wikidata identities;
- representative library and sequencing kits;
- verbatim Zotero IEEE sources;
- supplied artifact identities;
- field-level claims whose basis is `documentary` or `user_supplied`;
- barcode roles, index schemes, conflicts, accepted warnings, and validation attestation.

Use linked-data mappings where useful: `dcterms:isVersionOf`, `pav:version`, and `pav:previousVersion`. These mappings do not create runtime dependencies.

## Validation and completion

The authoritative entry point is `scripts/validate.py`, which:

1. Requires `seqspec >=0.4.0`.
2. Validates the sidecar against schema version 1.1.0.
3. Resolves supplied onlist archives/roots into temporary storage.
4. Verifies content, stored-artifact, and container digests.
5. Runs vanilla `seqspec check` on the unchanged YAML in the temporary view.
6. Cross-checks kit values, source identifiers, field-level claim coverage, vendor identifiers, onlist identities, and barcode/read projections.
7. In preflight mode, leaves the attestation untouched so the user can inspect the visualization. After explicit confirmation, a final identical pass records the validation attestation with CLI version, schema version, timestamp, status, and explicitly accepted warnings.

Completion additionally requires:

- every cited source was opened and checked for the claimed support;
- all Wikidata manufacturer entities were live-verified;
- `seqspec info` was shown to the user;
- `seqspec print -f seqspec-html -o seqspec.html seqspec.yaml` generated a self-contained graphical summary;
- the user explicitly confirmed the summary.

Warnings block until corrected or explicitly accepted with a recorded rationale. Errors and missing hard-gate evidence cannot be waived.

Use lifecycle-consistent filenames:

| State | seqspec | sidecar | visualization |
| --- | --- | --- | --- |
| Complete | `seqspec.yaml` | `provenance.sidecar.yaml` | `seqspec.html` |
| Draft | `seqspec.draft.yaml` | `provenance.draft.sidecar.yaml` | `seqspec.draft.html` |

Draft HTML must carry a conspicuous `DRAFT — NOT VALIDATED` banner and list blocking gaps. Promotion to the complete names occurs only after the composite gate passes.

Build a completion candidate under the completed basenames in temporary storage, run the composite gate there, and move the pair into the requested output directory only after success. This preserves vanilla relative-path behavior during validation without exposing an unvalidated `seqspec.yaml` in the output directory.

## Duplicate and relationship checks

Search only the canonical `pachterlab/seqspec` examples under `docs/examples/assays`. Existing examples are advisory and never replace authoritative evidence.

- `equivalent_seqspec`: same library structure, acquisition/read configuration, onlist contents, and UDI pairing constraints.
- `same_library_format`: the same technical library format with a meaningful implementation difference such as another index vocabulary.
- `related_library_format`: related structure with another platform, primer/orientation, or read length.

Always emit the requested local validated artifact even when an equivalent canonical example exists; record the relationship instead of silently reusing it.

## Version and variant lineage

A concrete profile always has a lineage record. Library-format, commercial-kit, and internal-SOP versions are recorded separately, but predecessor graphs are optional unless established.

`previous_version` is evidence-driven history of a managed artifact. It may legitimately connect profiles whose only difference is read or index configuration. `variant_of` expresses technical family membership or parallel alternatives. Relationships do not imply compatibility or equivalence, and every version remains a complete standalone profile rather than a delta.

## Deferred work

- Upstream seqspec proposal for structured manufacturer, catalog, authoritative-source, checksum, barcode-role, UDI-pairing, reusable-profile, and run-realization fields. Begin with an issue before a PR.
- Biolink-compatible shapes without a Biolink dependency; consider a LinkML vocabulary only when a real knowledge-graph consumer exists.
- Formal ontology mappings and a published barcode-role vocabulary.
- Non-Illumina platform guidance.
