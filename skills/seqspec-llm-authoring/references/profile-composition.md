# Profile derivation and future composition

## Current model

A completed profile combines one library-format definition with one raw-acquisition configuration. Treat it as immutable. To change an instrument, sequencing kit, flow-cell configuration, read allocation, orientation, or other acquisition fact, emit another complete profile rather than editing the completed parent.

Use the current relations literally:

- `variant_of` identifies technical family membership or a parallel alternative.
- `same_library_format` links concrete profiles that share a library format but differ in acquisition or another implementation detail.
- `previous_version` identifies an explicitly managed successor.

None of these relations means inheritance, composition, or field reuse. A derived sibling must remain a standalone, fully materialized profile.

## MVP derivation

Use a validated parent as an evidence-backed baseline. Preserve unchanged library structure, barcode semantics, onlist bytes and projections, and their documentary claims. Replace superseded acquisition evidence. Link an acquisition sibling to its concrete parent with `same_library_format`, retain the common family under `variant_of`, and leave `previous_version` unset unless the user establishes succession.

This duplication is an interoperability materialization required by Seqspec's flat document model, not the desired long-term domain model.

## Design debt: separate library and acquisition

Library format and acquisition configuration vary independently. It is routine to sequence the same physical library format on several instruments or consumable configurations. Reads from multiple acquisitions may also be concatenated into the same FASTQ file, so one file cannot always be described truthfully by choosing a single acquisition sibling.

A future model should provide:

1. a canonical library-definition identity for molecule structure, regions, onlists, and barcode semantics;
2. an acquisition-definition identity for instrument model, sequencing kit, orientation, and acquired read lengths;
3. explicit composition or materialization provenance connecting those definitions to a complete Seqspec document; and
4. file/run associations that may reference multiple acquisition definitions while sharing one library definition.

Existing `variant_of` and `same_library_format` links can bridge current siblings to that future model, but must not be silently reinterpreted as overlay semantics. Introduce explicit component identities and composition relations before reducing the duplicated materializations.
