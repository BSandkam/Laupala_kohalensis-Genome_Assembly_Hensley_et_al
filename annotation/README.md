# Annotation

Structural and functional annotation of the *Laupala kohalensis* genome, performed by
**Niko Hensley**. This section was originally maintained as a separate repository
([NikoHensley/Laupala_genome_assembly_annotation_CNL_Lkoh_2.0](https://github.com/NikoHensley/Laupala_genome_assembly_annotation_CNL_Lkoh_2.0))
and is merged here so the assembly and its annotation live in one place.

## Where this sits in the pipeline

Annotation is performed on the **Inspector-corrected contigs**
(`contig_corrected.fa`, from [../04_Correct_Contigs.md](../04_Correct_Contigs.md)), *not*
on the scaffolds. This is deliberate: gene prediction runs against the corrected contigs,
and the resulting annotation is then lifted onto the chromosome-scale scaffold coordinates
as the final step ([../06_Update_Gff.md](../06_Update_Gff.md)). Because scaffolding only
reorders/reorients/breaks contigs without changing their sequence, the annotation transfers
to scaffold coordinates arithmetically.

```
04_Correct_Contigs (contig_corrected.fa)
        │
        ├── 05_Scaffolding ─────────────┐
        │                               │
        └── annotation/ (this section)  │
                    │                   ▼
                    └────────► 06_Update_Gff (annotation lifted onto scaffolds)
```

## Steps

| Step | Description |
|------|-------------|
| [01_Repeat_Masking.md](01_Repeat_Masking.md) | Build a custom repeat library and soft-mask the genome (RepeatModeler, TransposonPSI, MITE-Tracker, LTRharvest/digest, RepeatClassifier, RepeatMasker) |
| [02_Annotation_Transfer_and_Evidence.md](02_Annotation_Transfer_and_Evidence.md) | Transfer the prior annotation (Liftoff), integrate RNA-seq/Iso-seq evidence (TAGADA, minimap2), and predict ORFs (TransDecoder) |
| [03_BRAKER3_and_TSEBRA.md](03_BRAKER3_and_TSEBRA.md) | Two BRAKER3 runs (RNA-seq and Iso-seq evidence) merged with TSEBRA |
| [04_Functional_Annotation.md](04_Functional_Annotation.md) | InterProScan, eggNOG-mapper, reciprocal BLAST vs *Drosophila*, AGAT integration |
| [05_Mitochondrial_and_NUMT.md](05_Mitochondrial_and_NUMT.md) | Mitochondrial genome assembly/annotation and NUMT detection |

## Key outputs

| File | Description |
|------|-------------|
| `combined_library_Lko_ortho.lib.minlen50.nr.classified.fa` | Final custom repeat library (3,182 sequences) — included here |
| `Lkohalensis_braker_combined.emapper.decorated.gff` | Functionally decorated annotation on corrected contigs — the input to [../06_Update_Gff.md](../06_Update_Gff.md) |
| `Kohalensis_scaffolds.gff` | Final annotation lifted onto scaffold coordinates (produced in step 06) |

The large result files (the full decorated annotation GFF and the hard-masked coordinate
BED) are deposited with the genome under BioProject **PRJNA1306088** rather than committed
here; see [../README.md](../README.md#data-availability).

## Data inputs (not products of this repo)

- **Prior annotation** transferred by Liftoff: `Lko_genes.gff` — the existing
  *L. kohalensis* annotation (NCBI GCA_002313205.1).
- **RNA-seq**: 12 short-read sets (8 lab samples + SRR24757042–45).
- **Iso-seq**: `isoseq_Lkoh_refined.fa` (Kinnex full-length RNA-seq, PacBio Revio).
- **Protein evidence**: OrthoDB Arthropoda (`Arthropoda.fa`).
