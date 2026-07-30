# `provenance.sidecar.yaml` format

Use `sources_schema_version: 1.1.0`. Validate against `schemas/seqspec-sources.schema.json` and then run `scripts/validate.py` for semantic and cross-file checks. No other sidecar schema version is supported.

## Illustrative complete shape

This is a field-layout example, not a ready-to-validate fixture. Replace every example or placeholder value with verified data.

```yaml
sources_schema_version: 1.1.0
status: complete

profile:
  seqspec_assay_id: full-length-brb-seq-illumina-pe150
  internal_colloquial_names:
    - BRB
  family_id: full-length-brb-seq
  version: null
  previous_version: null
  variant_of: full-length-brb-seq
  linked_data:
    is_version_of: http://purl.org/dc/terms/isVersionOf
    version: http://purl.org/pav/version
    previous_version: http://purl.org/pav/previousVersion

library_format:
  technical_name: Full-Length BRB-seq
  version: null
  family_id: full-length-brb-seq
  representative_kit:
    seqspec_value: Full-Length BRB-seq kit
    product_name: Full-Length BRB-seq kit
    manufacturer_id: alithea_genomics
    catalog_number: EXAMPLE-CATALOG
    version: null
    source_ids: [alithea_genomics_2026_full_length_brb_seq_user_guide]

sequencing:
  platform: NovaSeq X Plus
  index_read_configuration: known
  reads:
    - read_id: R1
      cycles: 150
      basis: user_supplied
    - read_id: R2
      cycles: 150
      basis: user_supplied
  sequence_kit:
    seqspec_value: NovaSeq X Series 1.5B Reagent Kit
    product_name: NovaSeq X Series 1.5B Reagent Kit (300 Cyc)
    internal_colloquial_name: 1.5B-300
    manufacturer_id: illumina
    catalog_number: "20104705"
    catalog_number_status: documented
    version: null
    source_ids: [illumina_2026_novaseq_x_reagents_20104705]

vendors:
  - vendor_id: illumina
    name: Illumina
    wikidata_uri: https://www.wikidata.org/entity/Q2068984
    verified_at: 2026-07-15
  - vendor_id: alithea_genomics
    name: Alithea Genomics
    wikidata_uri: REPLACE_WITH_LIVE_VERIFIED_WIKIDATA_ENTITY_URI
    verified_at: 2026-07-15

sources:
  - source_id: alithea_genomics_2026_full_length_brb_seq_user_guide
    authority: authoritative
    title: Full-Length BRB-seq kit User Guide
    url: https://example.org/vendor-guide.pdf
    accessed: 2026-07-15
    year_basis: accessed
    zotero_ieee: '[1] “Full-Length-BRB-seq-kit-User-Guide-2.” Accessed: Jan. 14, 2026. [Online]. Available: https://alitheagenomics.com/hubfs/Full-Length-BRB-seq-kit-User-Guide-2.pdf'
  - source_id: illumina_2026_novaseq_x_reagents_20104705
    authority: authoritative
    title: NovaSeq X Series Reagents
    url: https://www.illumina.com/products/by-type/sequencing-kits/cluster-gen-sequencing-reagents/novaseq-x-series-reagent-kits.html#tabgroup-1-tab2
    accessed: 2026-07-15
    year_basis: accessed
    zotero_ieee: '[1] “NovaSeq X Series Reagents | Sustainable design meets streamlined NGS.” Accessed: Jul. 15, 2026. [Online]. Available: https://www.illumina.com/products/by-type/sequencing-kits/cluster-gen-sequencing-reagents/novaseq-x-series-reagent-kits.html#tabgroup-1-tab2'

artifacts: []
onlists: []

claims:
  - claim_id: sequencing-platform
    target: sequencing.platform
    basis: documentary
    source_ids: [illumina_2026_novaseq_x_reagents_20104705]
  - claim_id: library-kit-product
    target: library_format.representative_kit.product_name
    basis: documentary
    source_ids: [alithea_genomics_2026_full_length_brb_seq_user_guide]
  - claim_id: library-kit-manufacturer
    target: library_format.representative_kit.manufacturer_id
    basis: documentary
    source_ids: [alithea_genomics_2026_full_length_brb_seq_user_guide]
  - claim_id: library-kit-catalog
    target: library_format.representative_kit.catalog_number
    basis: documentary
    source_ids: [alithea_genomics_2026_full_length_brb_seq_user_guide]
  - claim_id: sequence-kit-product
    target: sequencing.sequence_kit.product_name
    basis: documentary
    source_ids: [illumina_2026_novaseq_x_reagents_20104705]
  - claim_id: sequence-kit-manufacturer
    target: sequencing.sequence_kit.manufacturer_id
    basis: documentary
    source_ids: [illumina_2026_novaseq_x_reagents_20104705]
  - claim_id: sequence-kit-catalog
    target: sequencing.sequence_kit.catalog_number
    basis: documentary
    source_ids: [illumina_2026_novaseq_x_reagents_20104705]
  - claim_id: r1-cycles
    target: sequencing.reads.R1.cycles
    basis: user_supplied
    source_ids: []

barcode_semantics:
  vocabulary_version: 1.1.0
  regions: []
  index_schemes: []

conflicts: []
validation:
  status: complete
  validated_at: 2026-07-15T00:00:00Z
  seqspec_cli_version: 0.4.0
  sidecar_schema_version: 1.1.0
  accepted_warnings: []
  blocking_gaps: []
  user_confirmation:
    status: confirmed
    confirmed_at: 2026-07-15T00:00:00Z
```

Replace placeholder values; never emit a fake Wikidata identifier.

## Sources and artifacts

Every documentary source requires a verbatim Zotero IEEE entry. Keep the citation's bracket number untouched. `source_id` supplies stable linkage.

Artifacts are files rather than bibliography entries. Link each artifact to at least one cited source that establishes its distribution or provenance. An artifact need not have a fabricated Zotero entry of its own.

`profile.seqspec_assay_id` must equal the native Seqspec `assay_id`. The qualified sidecar name makes the external origin of “assay” explicit; it is not a claim that the identifier names a biological assay or a consumer's Demultiplexing Specification.

Use `sequencing.platform` for the exact public instrument model, such as `NovaSeq X Plus`, not for the manufacturer alone. Identify the manufacturer through `vendors` and native Seqspec `sequence_protocol`. When the sequencing kit includes its flow cell, keep the flow-cell configuration in the sequencing-kit product identity rather than duplicating it as another sidecar field.

Store the completed or draft artifact set in `<output-root>/<seqspec-assay-id>/`, where the final path component exactly equals both identifiers above. Keep the Seqspec, provenance sidecar, visualization, and any local onlists together so relative onlist paths remain valid.

```yaml
artifacts:
  - artifact_id: full_length_brb_guide_pdf
    filename: Full-Length-BRB-seq-kit-User-Guide-2.pdf
    media_type: application/pdf
    sha256: <64 lowercase hex>
    source_ids: [alithea_genomics_2026_full_length_brb_seq_user_guide]
```

## Onlists

### Materialization forms

A profile may have two Seqspec materializations:

1. **Source-linked authoring form:** authoritative public onlists retain their direct source URLs; documentary transcriptions remain local files beside `seqspec.yaml`. `scripts/validate.py` validates this form together with `provenance.sidecar.yaml`.
2. **Offline-packaged form:** onlist URLs downloaded as text files for offline packaging. Store exact source bytes inside the package, rewrite only the Seqspec onlist `url` and `urltype` needed to resolve the local files, and leave projection metadata and native MD5 values unchanged.

The sidecar's `availability`, source links, and content digests describe origin and exact content, so do not relabel an `authoritative_public` onlist merely because a consumer has vendored it. Keep `provenance.sidecar.yaml` byte-identical between forms. If packaging changes only onlist locations, the two Seqspec files have different byte-level digests but represent the same profile. The composite authoring validator governs the source-linked form; `scripts/offline_bundle.py verify` governs the packaged form.

Place the derived distribution at `<output-root>/offline-bundles/<seqspec-assay-id>/`, separate from the canonical `<output-root>/<seqspec-assay-id>/` directory. Every packaged native onlist must use `urltype: local` and `url: onlists/<filename>`. The verifier rejects drafts, unsafe or colliding filenames, undeclared files, stale or tampered payloads, semantic changes beyond `url` and `urltype`, and network-dependent `seqspec check` behavior. A supplied-container onlist still requires the matching archive or decompressed root when the offline bundle is first materialized.

Keep tabular projection metadata in vanilla seqspec, not duplicated in this sidecar. For example, a vendor plate map with a header and sequences in its second whitespace-delimited field uses:

```yaml
onlist:
  file_id: vendor-plate.tsv
  filename: vendor-plate.tsv
  filetype: tsv
  filesize: 1234
  url: https://example.org/vendor-plate.tsv
  urltype: https
  md5: <md5 of exact uncompressed vendor bytes>
  sequence_column_index: 1
  skip_rows: 1
```

The sidecar `content_digest` remains the SHA-256 of the exact uncompressed source bytes before projection. `stored_artifact_digest` remains the SHA-256 of the fetched or stored artifact bytes. Native projection is a view of authoritative content, not a derived artifact, so do not add a normalized file or transformation-lineage record.

When an authoritative document prints the complete finite sequence set but supplies no machine-readable file, emit a local one-sequence-per-line transcription beside `seqspec.yaml`:

```yaml
onlist:
  file_id: mf-udi-i7.txt
  filename: mf-udi-i7.txt
  filetype: txt
  filesize: 36
  url: mf-udi-i7.txt
  urltype: local
  md5: <md5 of emitted LF-terminated bytes>
  sequence_column_index: 0
  skip_rows: 0

onlists:
  - file_id: mf-udi-i7.txt
    filename: mf-udi-i7.txt
    availability: documentary_transcription
    source_ids: [alithea_genomics_2026_full_length_brb_seq_user_guide]
    content_digest:
      algorithm: sha256
      value: <sha256 of emitted bytes>
    stored_artifact_digest:
      algorithm: sha256
      value: <same sha256 for an uncompressed emitted file>
    derivation:
      kind: documentary_transcription
      source_locator: Page N, MF.UDI table, i7 column
      operations:
        - Transcribe the four i7 sequences in source row order.
        - Write one uppercase sequence per line using LF and a terminal newline.
      verification: manually_compared_to_source
```

Use separate i7 and i5 files for UDI marginal onlists. Record allowed pairs under `barcode_semantics.index_schemes`; do not imply that two independent onlists permit every Cartesian-product pair. Select or reverse-complement i5 values only when the cited source and instrument workflow support that operation, and state it in `derivation.operations`.

The cited document—not the emitted text file—is the authority. `documentary_transcription` is allowed only when the source discloses the complete finite set and every emitted sequence has been manually checked. A partial table, SampleSheet subset, or observed demultiplexing output is not a design onlist.

For public authoritative files, the vanilla seqspec URL may be remote. For a file inside a user-supplied archive/root, persist no absolute path:

```yaml
onlists:
  - file_id: 3M-february-2018.txt.gz
    filename: 3M-february-2018.txt.gz
    availability: supplied_container
    source_ids: [tenx_genomics_2026_cell_ranger_release]
    content_digest:
      algorithm: sha256
      value: <sha256 of exact uncompressed bytes>
    stored_artifact_digest:
      algorithm: sha256
      value: <sha256 of exact .gz bytes>
    container:
      kind: archive
      filename: cellranger-x.y.z.tar.gz
      sha256: <sha256 of archive bytes>
      member_path: cellranger-x.y.z/lib/python/cellranger/barcodes/3M-february-2018.txt.gz
```

For a decompressed root, use `container.kind: directory`, omit `container.sha256`, retain the root basename as `container.filename`, and record the root-relative `member_path`. This explicitly records that container-level integrity was unavailable while still checking the selected file.

For inaccessible bytes:

```yaml
status: draft
onlists:
  - file_id: 3M-february-2018.txt.gz
    filename: 3M-february-2018.txt.gz
    availability: access_controlled_unavailable
    source_ids: [tenx_genomics_2026_cell_ranger_release]
validation:
  status: draft
  blocking_gaps:
    - code: onlist_bytes_unavailable
      message: The finite cell-barcode onlist is distributed inside an access-controlled Cell Ranger package.
  user_confirmation:
    status: pending
    confirmed_at: null
```

Do not promote this draft by changing the seqspec region to `random`.

## Run-level index evidence

For an already sequenced pool, distinguish evidence from the profile's design vocabulary:

- `SampleSheet.csv` gives the declared i7/i5 pairs selected for that run.
- Demultiplexing reports give observed index sequences and counts, including abundant combinations not declared in the SampleSheet.
- The seqspec onlists remain the complete documented design sets for the library/indexing configuration.

Use declared and observed values to check index orientation and diagnose SampleSheet omissions, index hopping, contamination, or mixed library configurations. Do not persist sample identities, the selected-pair subset, or report contents in this profile sidecar. Do not promote unexpected observed sequences into the design onlist without an authoritative design source.

## Claims

Use field-level targets that another agent can follow. `documentary` claims require one or more source IDs. `user_supplied` claims may have an empty source list and must describe a choice, not a claim that should have documentary support.

Examples of documentary targets:

- `library_format.representative_kit.catalog_number`
- `library_spec.<region_id>.min_len`
- `library_spec.<region_id>.sequence_type`
- `sequencing.platform`
- `sequencing.sequence_kit.catalog_number`

Examples of user-supplied targets:

- `sequencing.reads.R1.cycles`
- `sequencing.reads.R2.cycles`
- `internal_protocol.version`

## Warnings and conflicts

Warnings block completion until fixed or explicitly accepted:

```yaml
validation:
  accepted_warnings:
    - code: <validator-warning-code>
      rationale: <verbatim user rationale>
```

Record source conflicts without deleting rejected evidence:

```yaml
conflicts:
  - conflict_id: barcode-length-conflict
    target: library_spec.demux_barcode.min_len
    selected:
      value: 14
      source_ids: [vendor_2026_guide]
    rejected:
      - value: 12
        source_ids: [vendor_2024_webpage]
    rationale: <user-confirmed rationale>
```

## Validation attestation

The attestation describes the most recent composite validation. Exclude it from equivalence comparisons. Do not label a draft complete or populate a successful timestamp before all automated gates pass and the final summary is confirmed.
