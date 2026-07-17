# *Laupala kohalensis* genome assembly and annotation

A chromosome-scale genome assembly and annotation for the Hawaiian swordtail cricket
*Laupala kohalensis*, built from PacBio HiFi reads, scaffolded onto linkage groups, and
annotated with RNA-seq and Iso-seq evidence.

This repository is the merged record of two workflows that were developed as separate
GitHub repositories:

- **Assembly** (steps 01–06) — B. Sandkam
- **Annotation** ([`annotation/`](annotation/)) — Niko Hensley, originally
  [NikoHensley/Laupala_genome_assembly_annotation_CNL_Lkoh_2.0](https://github.com/NikoHensley/Laupala_genome_assembly_annotation_CNL_Lkoh_2.0)

Each step file contains the commands as run, the parameters, and the reasoning behind the
choices. Approaches that were tested and set aside are listed under
[Approaches tested and not used](#approaches-tested-and-not-used) rather than kept inline.

---

## The assembly at a glance

Assembly statistics were re-verified on the server with `assembly-stats`.

| | |
|---|---|
| Species | *Laupala kohalensis* |
| Data type | PacBio HiFi (single male), Revio — 4,919,653 reads / 144 Gb |
| Assembler | hifiasm 0.19.8 (defaults, chosen from a parameter sweep) |
| Genome size | 1.66 Gb |
| Scaffolds | 46 (7 autosomes + X, plus unplaced) |
| Scaffold N50 / L50 | 267.6 Mb / 3 |
| Largest scaffold | 302.1 Mb |
| Sequence not placed on a chromosome | 61.7 Mb (3.71%) |
| Genome BUSCO (insecta_odb10, post-purge) | C:98.6% [S:95.2%, D:3.4%] |
| Repeat content (soft-masked) | 47.56% |
| Annotated genes | 17,866 (see [coverage note](docs/MANUSCRIPT_COVERAGE.md) on 17,670) |
| Mitochondrial genome | 16,500 bp, circular |

---

## Pipeline

The corrected contigs (step 04) feed **two parallel branches** — scaffolding and annotation
— which rejoin when the annotation is lifted onto the scaffolds (step 06).

```
01 Assembly ─ 02 Filter ─ 03 Purge ─ 04 Correct ─┬─ 05 Scaffolding ───────────┐
                                                  │                            │
                                                  └─ annotation/ ──────────────┤
                                                                               ▼
                                                                        06 Update GFF
                                                                   (annotation on scaffolds)
```

### Assembly (B. Sandkam)

| Step | Description |
|------|-------------|
| [01_De_novo_Assembly.md](01_De_novo_Assembly.md) | hifiasm parameter sweep; QUAST comparison |
| [02_Filter_Contaminants.md](02_Filter_Contaminants.md) | Remove non-arthropod contigs (BlobTools), cross-checked against coverage/GC |
| [03_Purge_Duplicates.md](03_Purge_Duplicates.md) | Remove redundant haplotigs (purge_dups), BUSCO-controlled |
| [04_Correct_Contigs.md](04_Correct_Contigs.md) | Correct misassemblies against the HiFi reads (Inspector) — hand-off to annotation |
| [05_Scaffolding_via_LinkageMaps.md](05_Scaffolding_via_LinkageMaps.md) | Order/orient contigs into chromosomes using linkage-map markers |
| [06_Update_Gff.md](06_Update_Gff.md) | Lift the annotation onto scaffold coordinates and verify it |

### Annotation (N. Hensley) — [`annotation/`](annotation/)

| Step | Description |
|------|-------------|
| [01_Repeat_Masking.md](annotation/01_Repeat_Masking.md) | Custom repeat library + soft-masking |
| [02_Annotation_Transfer_and_Evidence.md](annotation/02_Annotation_Transfer_and_Evidence.md) | Liftoff transfer; TAGADA + Iso-seq evidence; TransDecoder |
| [03_BRAKER3_and_TSEBRA.md](annotation/03_BRAKER3_and_TSEBRA.md) | Two BRAKER3 runs merged with TSEBRA |
| [04_Functional_Annotation.md](annotation/04_Functional_Annotation.md) | InterProScan, eggNOG, BLAST vs *Drosophila*, AGAT |
| [05_Mitochondrial_and_NUMT.md](annotation/05_Mitochondrial_and_NUMT.md) | Mito genome + NUMT (⚠️ commands pending — see coverage doc) |

### Reference docs

| File | Purpose |
|------|---------|
| [docs/VERSIONS.md](docs/VERSIONS.md) | Every tool's version, with how it was determined and confidence level |
| [docs/MANUSCRIPT_COVERAGE.md](docs/MANUSCRIPT_COVERAGE.md) | Manuscript-method-to-repository cross-check, discrepancies, and pre-submission action items |

### Supporting files

| Path | Purpose |
|------|---------|
| [scripts/](scripts/) | AGP/GFF helper scripts (`fasta_to_agp.py`, `agp_liftover_gff.py`, `summarize_longest_paf_hit.py`, `check_coding_seq.sh`) |
| [data/joins.txt](data/joins.txt), [data/splits.txt](data/splits.txt) | Contig order/orientation and the single contig break for scaffolding |
| [annotation/combined_library_Lko_ortho.lib.minlen50.nr.classified.fa](annotation/) | Final custom repeat library (3,182 sequences) |

---

## Approach and rationale

### Assembly

Optimal hifiasm settings depend on the repeat/TE profile of the genome and the individual
sequencing run, so we assembled under several settings — defaults plus variants of k-mer
length (`-k 63`, `-k 39`), the high-frequency k-mer threshold (`-D 10`), and overlaps per
read (`-N 150`) — and compared builds rather than accepting defaults untested. The default
build was carried forward.

### Contaminant removal

DNA came from a whole-body sample, so microbial contamination was expected. Contigs were
classified by BLAST against NCBI nt, but taxonomy alone was not treated as sufficient
grounds for removal: classification was cross-checked against read coverage, GC, and
length. This caught contig `ptg000062l` (17.6 Mb, 44X, *Laupala*-like GC) which was flagged
bacterial — the signal proved to be a single horizontally-transferred *Wolbachia* gene, not
a co-assembled endosymbiont (coverage was flat, not spiked), and the contig was retained.

### Purging duplicates

`purge_dups` removes redundant haplotypic contigs. BUSCO was the control: duplicated BUSCOs
should fall and single-copy rise while total BUSCOs stays flat — a drop in total would mean
over-purging. Post-purge completeness was C:98.6%.

### Contig correction

Scaffolding and annotation both propagate errors in the input contigs, so Inspector was run
against the HiFi reads to correct misassemblies first. Both downstream branches build on the
corrected contigs.

### Scaffolding

With no Hi-C for this individual, a linkage map provides the long-range evidence. Markers
are defined on the older NCBI assembly; we aligned only 800 bp windows around each marker
(not the whole assembly) to limit the influence of misjoins in that older, fragmented
assembly. One contig (`ptg000005l_1`) carried markers from two linkage groups — a misjoin —
and was broken at 11,965,000 after inspecting the HiFi alignments in IGV.

### Annotation

Annotation runs on the corrected contigs: a custom repeat library soft-masks 47.56% of the
genome; the prior annotation is transferred with Liftoff; RNA-seq (TAGADA) and Iso-seq
evidence feed two BRAKER3 runs merged with TSEBRA; and function is added from InterProScan,
eggNOG, and reciprocal BLAST against *Drosophila*. The result is lifted onto scaffold
coordinates in step 06, and verified by confirming CDS/transcript sequences are identical
between contig and scaffold coordinate systems.

---

## Approaches tested and not used

**PacBio adaptor trimming (HiFiAdapterFilt).** Only 1 read carried adaptor sequence;
assemblies with and without it were indistinguishable, so untrimmed reads were used.

**Scaffolding from whole-assembly alignment.** An initial approach aligned the entire older
NCBI (and an LKo57-anchored) assembly to the contigs. It inherited the older assembly's
misjoins — 11 contigs assigned to multiple chromosomes vs 1 under the marker-based approach
— and was abandoned.

**Scaffolding before contig correction.** The first scaffolding round ran on the purged
contigs directly; it was superseded by re-scaffolding the Inspector-corrected contigs.

**QUAST built-in BUSCO.** Fails fetching de-hosted BUSCO v3 datasets; BUSCO was run directly
against current lineages instead.

**RagTag GFF liftover.** Doesn't handle a broken contig; replaced by
[scripts/agp_liftover_gff.py](scripts/agp_liftover_gff.py).

---

## Reproducing this

Server-specific absolute paths have been rewritten to `~` (from `/local/storage/Projects/…`
and, for the annotation, `/local/workdir/Hensley/…` and `/home/nh392/…`). Paths beginning
`/programs/…` are shared BioHPC tool installs left as-is because they pin versions.
**Tool versions and how they were determined are in [docs/VERSIONS.md](docs/VERSIONS.md)** —
read that before assuming a bare command reproduces the original, since BioHPC updates the
default `$PATH`. Two Singularity containers (`dfam/tetools:latest`, `teambraker/braker3:latest`)
were pulled by `:latest` and should be pinned to digests.

Thread counts (`-t 90`, `--threads 48`, etc.) reflect the machines used and should be adjusted.

## Data availability

| Item | Accession |
|---|---|
| BioProject | PRJNA1306088 |
| PacBio HiFi reads | SRR37501604 |
| Short-read RNA-seq | SRR37605704–SRR37605711 |
| Iso-seq reads | SRR37532061 |
| Assembly (GenBank) | JBYTER000000000 · BioSample SAMN55867830 |

The linkage map used for scaffolding derives from `LOD_scores (kohpar reanalysis).xlsx`,
sheet `NO_PSEUDO_MARKERS`. Large annotation result files (the full decorated GFF and the
hard-masked coordinate BED) are deposited with the genome rather than committed here.

## Citation

To be added on publication.
