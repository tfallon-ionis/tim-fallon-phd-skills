---
name: seqspec-llm-authoring
description: Author or derive an evidence-backed Illumina seqspec profile through a source-first interview, emit a provenance sidecar, validate both artifacts, and present a graphical confirmation. Use when a user asks to create, modify, adapt, clone, document, reconstruct, or validate a sequencing-library/read structure as seqspec from an existing profile, vendor PDFs, kit webpages, protocols, or expert knowledge.
---

# Author a seqspec profile

Produce one Illumina library-format plus raw-acquisition profile per invocation. Treat physical instrument runs, lanes, SRA Runs, biosamples, and FASTQ sets as related entities—not as the profile's identity.

Seqspec describes genomics data through the sequencing-library molecule, the reads generated from it, and optional file associations. This skill deliberately emits a reusable, file-agnostic profile. The profile can annotate post-demultiplexing FASTQ data or supply structure to preprocessing and demultiplexing systems; do not call it a demultiplexing specification unless a consuming bounded context explicitly defines that application.

Read [references/sidecar-format.md](references/sidecar-format.md) before emitting files. Read [references/barcode-semantics.md](references/barcode-semantics.md) whenever the library contains an index, barcode, UMI, or other molecular identifier.
Read [references/illumina-run-metadata.md](references/illumina-run-metadata.md) when using `RunInfo.xml` or `RunParameters.xml` as run-level evidence.
Read [references/profile-composition.md](references/profile-composition.md) when deriving from an existing profile or reasoning about profile identity, siblings, or concatenated acquisitions.

## Establish the runtime

1. Require the seqspec implementation from `https://github.com/tfallon-ionis/seqspec.git` at commit `5fb682b52c7ba9ad09e7796ca97a449726076530` (`feat: support tabular onlist projection`), or a deliberately tested successor. The fork and the materially different PyPI release both report `0.4.0`, so a version check alone is insufficient. Determine the installed package version without assuming `seqspec --version` exists, and verify that `seqspec.Region.Onlist.model_fields` contains `sequence_column_index` and `skip_rows`. If the implementation is unavailable, older than `0.4.0`, or lacks either capability, continue only as a draft.
2. Read these rendered official pages during every authoring run:
   - `https://pachterlab.github.io/seqspec/seqspec-file/`
   - `https://pachterlab.github.io/seqspec/specification`
3. Use the installed schema and validator as a second authority. Before declaring a construct inexpressible, inspect both the rendered documentation and executable implementation.
4. Ask for an output root. Default to `<cwd>/skill-outputs`. Once the Seqspec assay ID is established, use `<output-root>/<seqspec-assay-id>/` as the profile output directory. The directory name must exactly equal the native `seqspec.yaml` `assay_id`; do not substitute the colloquial library-format name or another slug. If lifecycle files already exist there, warn before overwriting them.

Do not require a devcontainer or uv. Do not use generic search results in place of the rendered official documentation unless those pages fail. Do not direct the user to obsolete seqspec repositories.

For development and regression testing, run `scripts/test.sh`. It installs the supported fork commit into an isolated uv environment before invoking the suite; do not substitute unpinned `--with seqspec`.

## Choose the authoring mode

- If the request supplies or clearly names an existing profile directory, enter derivation mode automatically.
- If the request asks to modify, clone, or adapt an existing profile without identifying it, ask for the directory.
- Otherwise, enter the source-first from-scratch workflow.

State the selected mode and, for derivation, the resolved parent path before proceeding. Never silently convert a derivation request into from-scratch authoring.

## Start source-first

1. Ask first for the internal colloquial library-format name. Record it only as a potentially non-unique alias.
2. Ask for at least one authoritative source and its verbatim Zotero IEEE citation. Accept a relevant vendor PDF or product webpage. A webpage that merely lists a kit is evidence only for the fields it actually supports.
3. Open every cited source. Confirm that it is legible and supports the mapped claims. If a page is inaccessible, JavaScript-only, authenticated, or ambiguous, ask for an accessible authoritative PDF or equivalent.
4. For a supplied local PDF, calculate SHA-256 and record its basename, authoritative URL, access date, and citation. Do not copy the PDF.
5. Read the representative library-kit source before the detailed interview. Extract a proposed structure, then ask only targeted questions, one at a time.

Do not allow user confirmation to replace missing documentary evidence. If authoritative sources conflict, present the conflict and record the user's selected claim, rejected claim, and rationale.

## Derive from an existing profile

Treat every completed parent profile as immutable. Changing its instrument, sequencing kit, flow-cell configuration, read allocation, orientation, library structure, or other technical claim creates a new Seqspec assay ID and output directory. Only byte-preserving revalidation or regeneration of derived HTML may operate in place.

1. Resolve the parent directory and validate its lifecycle pair with the current composite validator before reusing it.
2. Classify the parent:
   - A valid complete parent is an evidence-backed baseline.
   - A readable but stale or invalid parent may seed a draft; carry every inherited failure into `validation.blocking_gaps`.
   - A missing or internally inconsistent parent must be repaired or reconstructed separately.
3. Inventory the requested changes. Present an allowlisted semantic plan divided into **change**, **re-evaluate**, **preserve exactly**, and **regenerate**, and obtain confirmation.
4. Copy the parent into temporary candidate storage. Never edit the completed parent or create a child that refers to files inside its directory.
5. Reuse unchanged validated library structure, claims, barcode semantics, onlist projections, and onlist bytes. Copy local onlists byte-for-byte and verify their digests; retain authoritative public URLs.
6. Replace superseded evidence instead of accumulating it. Remove sources and claims that support only the old acquisition; add authoritative sources and claims for the child.
7. Re-evaluate instrument-dependent facts, including i5 orientation and platform-specific cycle accounting. Do not transfer a cycle-capacity rule between instrument families.
8. Treat demultiplexer extraction coordinates as run-time software configuration, not molecular-design truth. Before changing an in-read barcode/UMI boundary, corroborate the proposed geometry against authoritative design evidence such as the library protocol and design-onlist lengths. Raw-read structure and demultiplexing output may corroborate or contradict the proposal, but cannot create a design claim. If the evidence conflicts, report the discrepancy and do not encode the configured split as a library-format change.
9. Give the child a distinct, descriptive Seqspec assay ID. Include the differentiating acquisition characteristic when otherwise identical siblings would collide.
10. For an acquisition sibling, retain the common family under `variant_of`, leave `previous_version` unset unless succession is explicitly established, and add a `same_library_format` relation targeting the concrete parent.
11. Keep the child complete and standalone. Current relations express relatedness, not inheritance.

Compare parsed YAML and payload digests with the tested helper. Allow only paths approved in the semantic plan:

```bash
python <this-skill-directory>/scripts/compare_profiles.py \
  --parent <validated-parent-directory> \
  --child <candidate-directory> \
  --allow 'seqspec.assay_id' \
  --allow 'seqspec.sequence_protocol' \
  --allow 'seqspec.sequence_kit' \
  --allow 'sidecar.profile.seqspec_assay_id' \
  --allow 'sidecar.profile.relations*' \
  --allow 'sidecar.sequencing.platform' \
  --allow 'sidecar.sequencing.sequence_kit.*' \
  --allow 'sidecar.sources*' \
  --allow 'sidecar.claims*' \
  --allow 'sidecar.validation.*' \
  --allow 'files.seqspec.html'
```

Tailor the allowlist to the confirmed plan; the example is not permission to change every listed field. Review every reported allowed change. Block completion on any unexpected change.

## Capture identity and kits

Require:

- a stable, path-safe Seqspec assay ID for the concrete profile; it must be one directory-name component, not `.`, `..`, or a value containing `/` or `\`;
- a technical library-format name and any explicitly documented format version;
- a representative library-preparation kit with product name, manufacturer, catalog number, seqspec value, and sources;
- an exact public instrument model, stored as the sidecar `sequencing.platform` and identified with its manufacturer in native Seqspec `sequence_protocol`;
- a sequencing kit with product name, manufacturer, seqspec value, sources, and catalog number when documented;
- a live-verified manufacturer URI in the form `https://www.wikidata.org/entity/Q...` for every vendor;
- an optional internal sequencing-kit alias; accept `none`;
- optional internal protocol `id` and `version`—never rename version to revision.

Multiple kits may realize one library format. Record additional equivalent kits only when sources support the relationship; do not attempt an exhaustive catalog.

When a sequencing kit includes the flow cell, encode the public flow-cell configuration in the sequencing-kit product identity instead of duplicating it as another sidecar field. Do not infer an exact instrument model from kit compatibility; one kit may support several models.

Seqspec requires the native YAML field `assay_id`. In this skill's sidecar and prose, call the same value the **Seqspec assay ID** and store it as `profile.seqspec_assay_id`. This explicit qualifier contains Seqspec's overloaded terminology: never imply that the value identifies a biological assay, and never equate it with a consumer's Demultiplexing Specification ID unless that consumer establishes the mapping.

Use a natural source key: `<first-author-or-responsible-organization>_<year>_<short-title>`. Prefer publication year; otherwise use access year and record `year_basis: accessed`. Preserve the citation text and its bracket number verbatim, even when several entries contain `[1]`.

## Interview the acquisition configuration

Separate documentary facts from user choices:

- Require sources for molecule structure, primer/adaptor facts, fixedness and lengths, kit identity, and kit capability.
- Let the user choose a supported cycle allocation. Never infer PE150x150 from “300 cycles”; the same kit may support SE300 or asymmetric paired reads.
- Encode acquired raw reads. PE150x150 and PE50x50 are different profiles when separately acquired. In-silico trimming PE150x150 to PE50x50 is downstream processing and does not create another profile.
- For fixed Illumina read acquisition, set `min_len == max_len`.
- Do not validate a kit by naively summing R1, R2, I1, and I2 against advertised cycles.
- Capture I1/i7 (Index 1) and I2/i5 (Index 2) cycles when known. If unknown, omit index `Read` objects and set `index_read_configuration: unknown` in the sidecar.
- Exclude SampleSheet contents, concrete FASTQs, actual lane-pool membership, and selected sample-index pairs from the profile artifact. For an already sequenced pool, inspect SampleSheet and demultiplexing reports as run-level evidence under the rules below.

Use `index7` and `index5` only where seqspec requires those enum values. In user-facing prose use i7 (Index 1) and i5 (Index 2). Avoid `index7`, `index5`, and “sub-read” as informal terminology.

## Model regions honestly

- Use `sequence_type: random` only when a sequence is genuinely not known a priori.
- Use `sequence_type: onlist` for a finite permissible set. Do not relabel it random when the bytes are inaccessible.
- If fixedness and length are documented but bases are undisclosed, use `sequence_type: fixed` with `N` repeated to the known length and disclose `fixed_sequence_bases: undisclosed` in the sidecar. If fixedness or length is unknown, produce a draft.
- Treat an i7/i5 onlist as the design-level set from the indexing kit, not the actual lane subset.
- Record UDI pairing in the sidecar; do not pretend seqspec natively expresses the pairing relationship.

Keep three index sets distinct:

1. **Design set:** every index or allowed UDI pair supported by the documented library/indexing configuration. Encode this set in seqspec and the sidecar.
2. **Declared pool subset:** the i7/i5 pairs assigned in `SampleSheet.csv` for a concrete run. Use this to corroborate orientation and which design members were selected, but do not shrink the profile onlists to this subset.
3. **Observed distribution:** index sequences and counts in demultiplexing reports, including abundant sequences absent from the SampleSheet. Use this diagnostically to detect orientation mistakes, SampleSheet omissions, index hopping, contamination, or another pooled library. Do not add an observed sequence to the design set without documentary support.

Do not persist sample names, SampleSheet contents, actual selected pairs, or run report contents in the profile. Summarize a discrepancy only when it affects a profile claim, and record the documentary basis for the resolution.

Search first for authoritative onlist bytes. Never submit an email address or authenticate for the user. Do not accept an uncorroborated public mirror as authoritative. If an authoritative source instead prints a complete finite sequence table, transcribe it into a local onlist; absence of a vendor-published machine file is not a blocker by itself.

For a documentary transcription:

- emit a UTF-8, LF-terminated, one-sequence-per-line file beside the completed seqspec;
- preserve source order unless the source defines another canonical order;
- apply reverse complementation or workflow-specific i5 selection only when the source and instrument workflow require it, and record the operation;
- set the seqspec onlist to that local basename and compute MD5 over the emitted uncompressed bytes;
- record `availability: documentary_transcription`, SHA-256 digests, the precise page/table/column locator, and every operation in the sidecar;
- manually compare every emitted sequence against the cited source before completion;
- for UDI, emit separate i7 and i5 onlists and retain the allowed pair mapping in the sidecar, because seqspec represents the marginal sets but not their pairing constraint.

If neither authoritative bytes nor a complete authoritative table is available, produce a draft.

An authoritative onlist may be a whitespace-delimited table rather than one sequence per line. Preserve its direct vendor URL and exact bytes, and declare the native seqspec projection on the `onlist` object:

- set `sequence_column_index` to the zero-based whitespace-delimited field containing the sequence;
- set `skip_rows` to the number of physical header rows;
- leave both at their default `0` for a sequence-only file;
- keep `md5` over the exact uncompressed source bytes before projection;
- keep sidecar content and stored-artifact SHA-256 digests over the same pre-projection content and stored bytes, respectively.

Do not create a `cut`, `awk`, or normalized derivative when native projection can express the source. Verify the selected field exists on every retained nonblank row and that projected values satisfy the region length. Projection splits arbitrary whitespace; quoted CSV, embedded delimiters, or other parsing rules remain unsupported and may require an authoritative sequence-only source or a draft.

If the user supplies a vendor software archive or decompressed root:

1. Locate the member without copying it into the profile output directory.
2. Record only basenames and internal relative member paths—never the user's absolute path.
3. Compute seqspec's native MD5 over exact uncompressed bytes.
4. Compute SHA-256 for exact uncompressed content, stored member bytes when compressed, and the enclosing archive when supplied.
5. Do not normalize line endings, reorder sequences, or otherwise transform bytes before hashing.
6. When the member is tabular, record `sequence_column_index` and `skip_rows` on the vanilla seqspec onlist; do not persist a projected copy.

## Emit the pair

Use the templates and constraints in [references/sidecar-format.md](references/sidecar-format.md). Keep `seqspec.yaml` vanilla; put provenance, linked-data mappings, SHA-256 digests, lineage, semantic barcode facets, and validation status in the sidecar.

Recognize two materialization forms:

1. **Source-linked authoring form:** preserve authoritative public onlist URLs in `seqspec.yaml`; keep documentary-transcription onlists as local files beside it. This is the canonical output of this skill and the form accepted by the composite authoring validator.
2. **Offline-packaged form:** onlist URLs downloaded as text files for offline packaging, with every onlist copied as exact bytes into the package and its Seqspec URL rewritten to a package-relative local path.

Treat the offline-packaged form as a derived distribution of the source-linked form, not as a new profile or profile version, when library structure, read structure, onlist bytes and projections, and pairing constraints are unchanged. Expect the two `seqspec.yaml` files to have different SHA-256 content digests because their onlist locations differ. Preserve the original onlist provenance and content digests, compute a digest for the packaged `seqspec.yaml`, and cover every packaged payload with the consumer bundle's integrity manifest. Validate the source-linked form before packaging; verify the packaged form with its offline bundle verifier and a no-network check.

Require `sources_schema_version: 1.1.0` and `barcode_semantics.vocabulary_version: 1.1.0`. Reject every other sidecar schema or barcode vocabulary version; no backward compatibility is supported.

Keep these version concepts independent:

- seqspec schema version;
- concrete profile version;
- technical library-format version;
- commercial kit version;
- internal protocol version.

Always model concrete profile lineage. Add component predecessor links only when a source or the user establishes them. `previous_version` records managed history; `variant_of` records technical relatedness. Either or both may apply. Never infer a predecessor solely from similarity, dates, version-looking names, or changed cycles. Do not implement inheritance: every profile is complete.

Write lifecycle-consistent names:

- Complete: `seqspec.yaml`, `provenance.sidecar.yaml`, `seqspec.html`
- Draft: `seqspec.draft.yaml`, `provenance.draft.sidecar.yaml`, `seqspec.draft.html`

Place these files and any local onlists together in `<output-root>/<seqspec-assay-id>/`. For example:

```text
skill-outputs/
└── mercurius-full-length-brb-seq-illumina-r1-28-i1-8-i2-8-r2-90-v1/
    ├── seqspec.yaml
    ├── provenance.sidecar.yaml
    ├── seqspec.html
    ├── mf-udi-i7.txt
    └── mf-udi-i5.txt
```

Draft sidecars must enumerate blocking gaps. Draft HTML must visibly state `DRAFT — NOT VALIDATED` and list those gaps.

For a completion attempt, build candidate `seqspec.yaml` and `provenance.sidecar.yaml` in temporary storage, validate them there, and move them into the profile output directory only after success. This prevents an unvalidated candidate from occupying the completed filenames. Revalidation of an existing completed pair may operate in place.

## Check for related canonical examples

Search only `pachterlab/seqspec` under `docs/examples/assays`. Treat examples as advisory, never as authoritative evidence. Always emit the requested local artifact.

Classify relationships:

- `equivalent_seqspec`: same library structure, acquisition configuration, onlist content, and pairing constraints;
- `same_library_format`: same technical format with a meaningful implementation difference such as an index vocabulary;
- `related_library_format`: related structure with another platform, primer/orientation, or read length.

## Validate and confirm

Run a preflight composite validation against the temporary candidate:

```bash
python <this-skill-directory>/scripts/validate.py \
  --seqspec <candidate>/seqspec.yaml \
  --sidecar <candidate>/provenance.sidecar.yaml \
  --onlist-container <archive-or-root-if-needed> \
  --no-write-attestation
```

The validator resolves external onlists temporarily, verifies documentary-transcription files in place, validates the sidecar and cross-file links, and invokes vanilla `seqspec check`. It must not persist supplied paths or externally resolved onlist bytes. Revalidation of documentary transcriptions uses the emitted files; revalidation of container-backed onlists requires the matching archive/root again.

Treat errors and missing hard-gate evidence as non-waivable. Surface warnings and block until fixed or explicitly accepted by the user with a rationale stored in `validation.accepted_warnings`.

After preflight validation:

1. For a derivation, run `compare_profiles.py` with the confirmed allowlist and review every allowed change.
2. Run `seqspec info` and show the result.
3. Generate `seqspec.html` using `seqspec print -f seqspec-html -o seqspec.html seqspec.yaml`.
4. Present the graphical summary and, for a derivation, its semantic diff; request explicit confirmation.
5. Set `validation.user_confirmation.status: confirmed` and record its UTC `confirmed_at` timestamp.
6. Run the same composite validator again without `--no-write-attestation`. This final pass records status, validation timestamp, seqspec CLI version, sidecar schema version, and accepted warnings.
7. For a derivation, repeat the semantic comparison after attestation; only attestation and confirmed generated-output changes may be newly different.
8. Move the attested pair, confirmed HTML, and any documentary-transcription onlists from temporary storage into `<output-root>/<seqspec-assay-id>/`.
9. Report completion only after automated validation, semantic comparison when applicable, and user confirmation.

If any gate remains unresolved, retain draft filenames and state the precise blocker.
