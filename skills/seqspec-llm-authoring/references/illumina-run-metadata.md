# Illumina run metadata → public terminology

Use an Illumina run's metadata to corroborate the as-sequenced read layout, instrument model, consumable class, and chemistry. Run metadata describes a physical execution; it does not define the reusable seqspec profile's identity or the internal geometry of a library-preparation read.

The field names below are verified for NextSeq 1000/2000. Their general roles also occur on other Illumina platforms, but platform-specific values and catalog mappings require separate verification.

## Locate the metadata

Read these files from the root of a user-supplied or otherwise authorized run folder:

- `RunInfo.xml`: read order, cycle counts, indexed-read flags, orientation, and run hardware identifiers.
- `RunParameters.xml`: instrument model, flow-cell and cartridge modes, chemistry recipe, and component part numbers.
- `SampleSheet.csv`: independently authored pool/index declarations and optional on-board demultiplexing settings.

Treat `RunInfo.xml` as authoritative for what the instrument acquired. Treat the SampleSheet as evidence for declared index assignments and on-board settings; it can drift from the executed cycle plan.

Never copy an internal storage URL, absolute path, person name, experiment name, instrument serial, flowcell ID, or run ID into this skill or a reusable profile. Refer to supplied run metadata by generic artifact type unless a separate, user-requested run record requires those identifiers.

## Derive the read layout from `RunInfo.xml`

Interpret `<Read>` elements in document order:

- `NumCycles`: acquired length.
- `IsIndexedRead="N"`: template, barcode, or UMI-bearing sequencing read.
- `IsIndexedRead="Y"`: Illumina index read.
- `IsReverseComplement`: instrument-reported orientation behavior.

Map the ordered elements to R1, I1, I2, and R2 as applicable. Encode their acquired lengths in `sequence_spec`; do not infer missing reads.

An i5 read may report `IsReverseComplement="Y"` on patterned-flow-cell instruments. Account for that orientation when comparing SampleSheet values with a documented design onlist.

`RunInfo.xml` gives physical read boundaries only. Derive an in-read barcode/UMI split from authoritative library-design evidence, never from cycle counts alone. Treat explicit on-board-demultiplexing coordinates as the software's configured extraction window, not proof of the molecule's internal boundary.

Before using configured extraction coordinates to modify a profile:

1. compare each window length with the authoritative design-onlist length;
2. compare the proposed split with the library protocol or primer design;
3. use representative raw-read structure and demultiplexing output only as corroborating or contradictory run-level evidence; and
4. stop the geometry change when the configured window conflicts with the design evidence.

Do not pad a shorter onlist, infer missing bases, or promote observed sequences into the design set to make a configured window fit.

## Interpret `RunParameters.xml`

| Field | Interpretation |
| --- | --- |
| `InstrumentType` | Authoritative instrument model; prefer it over serial-prefix heuristics. |
| `InstrumentSerialNumber` | Run-local hardware identity; do not persist it in a reusable profile. |
| `InstrumentName` | Operator-assigned local nickname; do not treat it as technical evidence. |
| `FlowCellMode` | Public flow-cell class, such as a `P1`/`P2`/`P3`/`P4` token on NextSeq 1000/2000. |
| `CartridgeMode` | Flow-cell class and total reagent-cycle capacity. |
| `RecipeName` | Chemistry recipe; distinguish XLEAP-SBS from standard SBS. |
| `FlowCellPartNumber` | Component part number for the flow cell, not necessarily an orderable kit SKU. |
| `CartridgePartNumber` | Component part number for the reagent cartridge, not necessarily an orderable kit SKU. |
| `ExperimentName` | Free text; never use it as authoritative kit or profile metadata. |

## Resolve marketed cycle count and kit identity

For NextSeq 1000/2000 XLEAP-SBS, Illumina states that cartridges include 38 extra cycles. Therefore the parenthetical total in `CartridgeMode` is greater than the marketed kit size:

| Total reagent cycles | Marketed kit size |
| --- | --- |
| 88 | 50 cycles |
| 138 | 100 cycles |
| 238 | 200 cycles |
| 338 | 300 cycles |
| 638 | 600 cycles |

Apply this subtraction only when `RecipeName` establishes XLEAP-SBS. Verify other chemistry families independently. Confirm that the sum of acquired cycles does not exceed the total reagent cycles.

Do not transfer this NextSeq 1000/2000 mapping to NovaSeq X Series merely because both use XLEAP-SBS branding. NovaSeq X run metadata may identify a marketed kit configuration through its flow-cell type and recipe even when naïve addition of R1, I1, I2, and R2 appears to exceed the marketed cycle label. Treat an executed cycle plan and its run metadata as corroborating evidence, then resolve the public product name and catalog number from the platform-specific manufacturer catalog. Never replace that evidence with a cross-platform arithmetic heuristic.

Source: [Illumina NextSeq 1000/2000 reagents](https://www.illumina.com/products/by-type/sequencing-kits/cluster-gen-sequencing-reagents/nextseq-1000-2000-reagents.html).

`RunParameters.xml` may identify separate flow-cell and cartridge components without naming the single orderable reagent-kit SKU. Resolve the public kit from:

1. instrument model;
2. flow-cell class;
3. marketed cycle count;
4. chemistry family; and
5. a current manufacturer catalog or authoritative distributor listing.

Do not extrapolate catalog numbers from neighboring SKUs.

## Use run metadata without contaminating the profile boundary

- Derive R1/I1/I2/R2 order, lengths, and orientation from `RunInfo.xml`.
- Use `RunParameters.xml` to corroborate the public instrument, flow-cell class, chemistry, and sequencing-kit identity.
- Use the SampleSheet only for declared index selections and explicit on-board settings; do not treat configured extraction windows as molecular-design truth.
- Use a library-kit source to establish molecular structure and any in-read barcode/UMI geometry.
- Do not shrink design onlists to the SampleSheet subset.
- Do not persist run-local identities or internal storage locations in the reusable seqspec profile or provenance sidecar.
