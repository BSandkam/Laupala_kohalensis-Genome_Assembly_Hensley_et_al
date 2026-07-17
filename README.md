# *Laupala kohalensis* genome assembly

A chromosome-scale genome assembly for the Hawaiian swordtail cricket *Laupala
kohalensis*, built from PacBio HiFi reads and scaffolded onto linkage groups using a
previously generated linkage map.

This repository documents the analysis pipeline as it was actually run. Each step is a
markdown file containing the commands, the parameters used, and the reasoning behind the
choices made. Approaches that were tested and set aside are listed in
[Approaches tested and not used](#approaches-tested-and-not-used) rather than kept inline,
so the recorded pipeline reflects the path to the published assembly.

---

## The assembly at a glance

| | |
|---|---|
| Species | *Laupala kohalensis* |
| Data type | PacBio HiFi (single individual) |
| Assembler | hifiasm (default parameters, selected from a 5-way sweep) |
| Estimated haploid genome size | ~1.6 Gb |
| Long-range scaffolding evidence | Linkage map (`NO_PSEUDO_MARKERS`) |
| Chromosomes recovered | 7 autosomes + X |
| Sequence not placed on a chromosome | 38 contigs, 61,689,142 bp (3.71%) |
| Annotated transcripts (lifted to scaffolds) | 31,039 |
| Prior reference | NCBI GCA_002313205.1 |

---

## Pipeline

Run in order. Each file names its inputs and outputs, and links to the next step.

| Step | Description |
|------|-------------|
| [01_De_novo_Assembly.md](01_De_novo_Assembly.md) | Assemble HiFi reads with hifiasm across a parameter sweep; compare builds with QUAST |
| [02_Filter_Contaminants.md](02_Filter_Contaminants.md) | Identify and remove non-arthropod contigs with BlobTools, cross-checked against coverage and GC |
| [03_Purge_Duplicates.md](03_Purge_Duplicates.md) | Remove redundant haplotypic contigs with purge_dups, using BUSCO to confirm no over-purging |
| [04_Correct_Contigs.md](04_Correct_Contigs.md) | Detect and correct misassemblies against the HiFi reads with Inspector |
| [05_Scaffolding_via_LinkageMaps.md](05_Scaffolding_via_LinkageMaps.md) | Order and orient contigs into chromosomes using linkage map markers |
| [06_Update_Gff.md](06_Update_Gff.md) | Lift the contig-level annotation onto the scaffolds and verify it |

### Supporting files

| Path | Purpose |
|------|---------|
| [scripts/fasta_to_agp.py](scripts/fasta_to_agp.py) | Convert a contig fasta into a trivial AGP so agptools can manipulate it |
| [scripts/agp_liftover_gff.py](scripts/agp_liftover_gff.py) | Lift GFF features from contig to scaffold coordinates via the AGP; handles broken contigs |
| [scripts/summarize_longest_paf_hit.py](scripts/summarize_longest_paf_hit.py) | Report the longest alignment per query in a PAF |
| [scripts/check_coding_seq.sh](scripts/check_coding_seq.sh) | Assess coding potential of lifted transcripts (TransDecoder + DIAMOND + Pfam) |
| [data/joins.txt](data/joins.txt) | Final contig order and orientation for each chromosome |
| [data/splits.txt](data/splits.txt) | The single contig break applied before joining |

---

## Approach and rationale

### Assembly

Optimal hifiasm settings depend on the repeat and TE profile of the genome and on the
characteristics of the individual sequencing run, so there is no universally correct
parameter set. We assembled under five settings — defaults, longer and shorter k-mers
(`-k 63`, `-k 39`), a more permissive high-frequency k-mer threshold (`-D 10`), and more
overlaps considered per read (`-N 150`) — and compared the resulting builds rather than
accepting defaults untested. The default build (`v0`) was carried forward.

### Contaminant removal

DNA was extracted from whole-body samples, so contamination from gut bacteria and other
associated microbes was expected. Contigs were classified by BLAST against NCBI nt, but
**taxonomic assignment alone was not treated as sufficient grounds for removal**.
Classification was cross-checked against read coverage, GC content, and contig length,
since genuine *Laupala* contigs are expected at ~48X (or ~24X for alternatively phased
regions) and ~35% GC, while the contaminant contigs were short, low-coverage, and ~50% GC.

That cross-check mattered. Contig `ptg000062l` (17.6 Mb, 44X coverage, *Laupala*-like GC)
was flagged as bacterial. Investigation showed the signal came from *Wolbachia*, but was
confined to a single horizontally transferred gene rather than a co-assembled *Wolbachia*
genome — read depth across the region was flat at ~44X, whereas a co-assembled endosymbiont
would show a coverage spike. The contig was retained explicitly. A systematic re-check
confirmed that of 114 contigs failing the taxonomic filter, only one other had >=24X
coverage, so the filter was not discarding real sequence at scale.

### Purging duplicates

De novo assembly frequently retains both haplotypes of a region as separate contigs.
BUSCO was used as the control on `purge_dups`: after purging, duplicated BUSCOs should
fall and single-copy BUSCOs should rise, while the *total* BUSCOs found stays flat. A drop
in total BUSCOs would indicate over-purging.

### Contig correction

Scaffolding propagates any error in the input contigs into the final build, and a
structural error *inside* a contig cannot be fixed by ordering contigs correctly.
Inspector was therefore run against the HiFi reads to correct misassemblies before
scaffolding, so the linkage map is applied to contigs already reconciled with the read
evidence.

### Scaffolding

With no Hi-C data for this individual, the linkage map provides the long-range evidence
needed to place contigs onto chromosomes.

The markers are defined by position on the older NCBI assembly (GCA_002313205.1). Rather
than align that whole assembly to our contigs, we extracted an 800 bp window around each
marker and aligned only those windows. This deliberately limits the influence of any
misjoined scaffolds in the older, more fragmented assembly: a misjoin there can only
affect the markers it contains, instead of pulling an entire scaffold's worth of alignment
into the placement decision. Markers were retained at >=60% of the window matching, a
threshold checked to ensure retained markers placed to a single contig unambiguously.

One contig, `ptg000005l_1`, carried markers from two linkage groups — the signature of a
misjoin. Rather than assign it arbitrarily, the HiFi read alignments were inspected
directly in IGV, and the contig was broken at position 11,965,000 before joining. Contig
order and orientation were then walked along each linkage group and reviewed manually.

### Annotation

**The gene annotation was produced by a collaborator and is an input to this repository,
not a product of it.** This repository picks the annotation up at
`Lkohalensis_braker_combined.emapper.decorated.gff`, a BRAKER-derived annotation against
the corrected contigs, and lifts it onto the scaffold coordinates.

Because scaffolding only reorders, reorients, and (in one case) breaks contigs without
altering their sequence, the annotation can be lifted arithmetically via the AGP with no
need to re-run gene prediction. The liftover was verified by extracting CDS and transcript
sequence from both coordinate systems and confirming they are byte-identical — they are.

---

## Approaches tested and not used

Recorded here so the decisions are documented, without cluttering the pipeline.

**PacBio adaptor trimming (HiFiAdapterFilt).** Tested as a preprocessing step. Only 1 read
(2.03e-05% of the total) carried adaptor sequence at >=97% match over >=44 bp, and no reads
matched the shorter adaptor. Assemblies built with and without that read were
indistinguishable, so the untrimmed reads were used and this branch was dropped.

**Scaffolding from whole-assembly alignment to the NCBI reference.** The initial approach
aligned the entire older NCBI assembly (and, in a variant, an LKo57-anchored assembly from
a collaborator) to the PacBio contigs, and inferred contig order from which old scaffolds
landed where. This was abandoned in favour of aligning linkage-map marker windows directly.
The whole-assembly approach inherited misjoins from the older assembly: 11 PacBio contigs
were assigned to more than one chromosome, versus 1 under the marker-based approach, and
several chromosomes (chrX in particular) had contig orders that could not be resolved
confidently.

**Scaffolding before contig correction.** The first scaffolding round was run on the
purged contigs directly. It was superseded by re-scaffolding the Inspector-corrected
contigs, which is the build reported here.

**QUAST's built-in BUSCO.** `--conserved-genes-finding` fails because QUAST fetches BUSCO
v3 lineage datasets that are no longer hosted. Working around this by substituting a
current dataset into QUAST's cache was attempted and did not work. BUSCO was instead run
directly against a current lineage at each pipeline stage.

**RagTag GFF liftover.** Does not handle a contig broken during scaffolding, which applies
here. Replaced by [scripts/agp_liftover_gff.py](scripts/agp_liftover_gff.py).

**tigmint / tidk.** Explored during development; not part of the reported assembly.

---

## Notes on reproducing this

Paths have been rewritten to `~` in place of the absolute paths on the machine where the
work was run (`/local/storage/Projects/...` and `/NFS4/storage/Projects/...`). The
pipeline assumes this layout:

```
~/Kohalensis_Genome/          # working directory for all pipeline steps
~/Sequencing_Reads/           # raw HiFi reads
~/Databases/                  # NCBI nt, taxdump, BUSCO lineages, Pfam, UniRef90
~/Programs/                   # locally installed tools (hifiasm, purge_dups, agptools, ...)
~/Environments/               # conda environments
```

Paths beginning `/programs/...` are shared tool installs on the Cornell BioHPC and have
been left as-is, since they pin the tool versions that were used. The relevant versions
are: hifiasm v0.7, minimap2 2.24, QUAST 5.2.0, BlobToolKit 2.6.3, BUSCO 5.2.2 (lineage
`insecta_odb10`), samtools 1.19, TransDecoder 5.5.0, HMMER 3.4.

Thread counts (`-t 90`, `-t 100`) reflect the machine used and should be adjusted.

## Data availability

The raw HiFi reads, the assembled genome, and the annotation are deposited separately;
accessions to be added on publication. The linkage map used for scaffolding derives from
`LOD_scores (kohpar reanalysis).xlsx`, sheet `NO_PSEUDO_MARKERS`.

## Citation

To be added on publication.
