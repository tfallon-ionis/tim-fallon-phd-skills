# Deferred non-Illumina design

This file is design-only and intentionally not referenced by the runtime skill.

seqspec exposes sequencing-protocol values for PacBio and Oxford Nanopore, but its public examples and guidance are substantially stronger for Illumina-style short-read structures. V1 therefore refuses to author non-Illumina profiles rather than extrapolating Illumina lane, index-read, and primer assumptions.

A later design pass should independently model:

- PacBio polymerase reads, subreads, circular consensus/HiFi output, SMRTbell adapters, and multiplexing;
- Oxford Nanopore reads, motor/adaptor orientation, kit-specific barcoding, POD5/FAST5/FASTQ relationships, and duplex/simplex distinctions;
- whether raw acquisition, basecalled output, and processed consensus each require distinct profile types;
- platform-specific kit catalog and manufacturer provenance using the same sidecar principles;
- terminology that cannot be safely shared with Illumina (especially “subread”).

Do not enable these platforms merely because the seqspec schema accepts their protocol names. Require authoritative platform documentation, representative examples, and executable validation first.
