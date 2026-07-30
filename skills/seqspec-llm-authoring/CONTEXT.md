# Domain model

## Core terms

### seqspec profile

One complete library structure plus one designed raw-acquisition/read configuration. A profile describes how resulting sequencing reads are structured and interpreted; it may support post-demultiplexing data reuse or be consumed by preprocessing and demultiplexing systems, but it is not intrinsically a demultiplexing specification.

### Seqspec assay ID

The identifier stored in Seqspec's required `assay_id` field and mirrored as `seqspec_assay_id` in this skill's provenance model. The name belongs to the external Seqspec format; it does not imply a biological-assay identity or equal a consumer's Demultiplexing Specification ID.

### profile output directory

The directory containing one profile's Seqspec, provenance sidecar, visualization, and local onlists. It is named exactly for the Seqspec assay ID and lives directly under the selected output root: `<output-root>/<seqspec-assay-id>/`.

### demultiplexing application

Consumer-specific use of a seqspec profile to derive rules for partitioning pooled sequencing reads. It is one possible application of the profile, not the profile's universal identity or boundary.

### instrument run

One physical execution of a sequencing instrument. It may contain multiple lanes and multiple seqspec profiles.

### SRA Run

An archive manifest/accession for files from one SRA Experiment. It is not synonymous with an instrument run.

### lane pool

The collection of library instances sequenced in one flowcell lane. Illumina libraries within the lane share the instrument read-cycle recipe but may have different library formats.

### library preparation input

One biosample-derived aliquot entering one library-preparation instance. Use this rather than `sample` when describing an in-read barcode that partitions library-preparation inputs.

### demultiplexing barcode

A synthetic sequence used to partition reads. Facets state where it is observed and what it groups; the superclass alone does not imply a sample, cell, or lane-pool role.

### onlist

A finite set of permissible sequences for a region. Its authoritative source bytes may be a whitespace-delimited table projected natively with a zero-based sequence column and skipped physical header rows. Digests describe the source before projection. An unavailable onlist remains finite and must not be represented as random.

### source-linked seqspec

The canonical authoring materialization of a seqspec profile. Authoritative public onlists retain their source URLs, while documentary transcriptions remain local artifacts beside the seqspec.

### offline-packaged seqspec

A derived materialization with onlist URLs downloaded as text files for offline packaging and rewritten to package-relative local paths. It represents the same profile when the onlist bytes, projections, library structure, read structure, and pairing constraints are unchanged, even though its `seqspec.yaml` content digest differs.

## Version relationships

- `previous_version`: an explicitly established successor/predecessor relationship between managed artifacts.
- `variant_of`: technical family membership or a parallel alternative.
- Technical library-format, commercial-kit, internal-SOP, and concrete-profile versions are distinct values. A change in one never automatically increments another.

## Invariants

1. One profile describes one library format and one acquisition configuration.
2. One instrument run may instantiate multiple profiles; one profile may recur in multiple runs.
3. Documentary facts require cited evidence. User-selected cycle allocation is recorded as user supplied.
4. Every manufacturer uses a live-verified Wikidata entity URI.
5. A completed profile passes both vanilla seqspec validation and sidecar/cross-file validation.
6. Exact equivalence includes onlist contents and pairing constraints.
7. A consumer may assign its own identifier to an application of a profile; that identifier is not automatically the Seqspec assay ID.
8. Changing only between source-linked and offline-packaged materializations does not create a new profile version.
9. One profile output directory is named exactly for its Seqspec assay ID.
