# Barcode and identifier semantics

Use sidecar vocabulary version `1.1.0`; no other vocabulary version is supported. Keep seqspec's native `region_type` unchanged and add these facets by referencing `region_id`.

## Facets

`semantic_type`:

- `demultiplexing_barcode`: partitions reads into groups.
- `molecular_identifier`: identifies/groups source molecules; use for a UMI.

`observed_in`:

- `R1`
- `R2`
- `I1`
- `I2`

Derive this facet from the seqspec read projection and cross-check it. Do not store the vague value `inline`; use `R1` or `R2`. Do not use “sub-read.”

`groups_reads_by`:

- `flowcell_lane_pool_member`: use for Illumina i7/i5 indexes that distinguish pooled library instances.
- `library_preparation_input`: use for an in-R1/R2 barcode that distinguishes biosample-derived inputs entering library preparation.
- `source_cell`: use for a cell barcode.
- `source_molecule`: use for a UMI/molecular identifier.

`index_role`:

- `i7`
- `i5`

Use `alternate_name: Index 1` for i7 and `alternate_name: Index 2` for i5. Never present seqspec's internal enum names `index7` and `index5` as preferred lab terminology.

## Examples

```yaml
barcode_semantics:
  vocabulary_version: 1.1.0
  regions:
    - region_id: demux_barcode
      semantic_type: demultiplexing_barcode
      observed_in: R1
      groups_reads_by: library_preparation_input
    - region_id: cell_barcode
      semantic_type: demultiplexing_barcode
      observed_in: R1
      groups_reads_by: source_cell
      external_mappings:
        - vocabulary: SAM
          term: CB/CR
    - region_id: i7
      semantic_type: demultiplexing_barcode
      observed_in: I1
      index_role: i7
      alternate_name: Index 1
      groups_reads_by: flowcell_lane_pool_member
    - region_id: i5
      semantic_type: demultiplexing_barcode
      observed_in: I2
      index_role: i5
      alternate_name: Index 2
      groups_reads_by: flowcell_lane_pool_member
    - region_id: umi
      semantic_type: molecular_identifier
      observed_in: R1
      groups_reads_by: source_molecule
      external_mappings:
        - vocabulary: SAM
          term: RX/OX/MI
  index_schemes:
    - scheme_id: dual-index
      type: unique_dual_index
      members: [i7, i5]
      pair_sequence_basis: seqspec_region
      allowed_pairs:
        - pair_id: UDI01
          i7: AAAAAAAA
          i5: CCCCCCCC
        - pair_id: UDI02
          i7: GGGGGGGG
          i5: TTTTTTTT
```

## Interpretation rules

- `demultiplexing_barcode` is intentionally broad. Specificity comes from orthogonal facets.
- i7 and i5 are roles within a demultiplexing scheme, not synonyms for every barcode.
- UDI is a constraint on the pair of i7 and i5 values. It is not a subclass of barcode.
- For `unique_dual_index`, enumerate `allowed_pairs`. Each value must occur in the corresponding seqspec region onlist; two marginal onlists alone do not encode the constraint.
- `pair_sequence_basis: seqspec_region` means pair values use the same 5′→3′ molecular representation as their seqspec regions. Normalize SampleSheet and demultiplexing-report values through the documented instrument/index workflow before comparing them.
- A cell barcode also performs demultiplexing, but its grouping target is `source_cell`, not `sample`.
- Avoid `identifies: sample`. In this domain `sample` ordinarily means the biosample upstream of library preparation.
- A generic `region_id: demux_barcode` is acceptable when the source provides no more specific conventional name.

## External alignment

SAM/BAM tags provide partial mappings: `BC` for sample/library barcode, `CB`/`CR` for cell barcodes, and `MI`/`RX`/`OX` for molecular identifiers. These mappings are informative, not exact replacements for the local facets.

Biolink Model is too high-level for these leaf roles. OBI can supply broad assay/process/entity concepts but does not replace this taxonomy. Keep V1 local and versioned. A future LinkML publication may map to external terms without making Biolink or OBI a runtime dependency.
