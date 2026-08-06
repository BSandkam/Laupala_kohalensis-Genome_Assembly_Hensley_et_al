# Manuscript ↔ repository coverage

Cross-check of every method described in the manuscript draft against what this repository
documents. Purpose: ensure nothing the paper claims is undocumented, and flag numbers that
disagree.

**Legend:** ✅ documented · ⚠️ partial / needs a value confirmed · ❌ described in
manuscript but not documented as code.

---

## Sequencing and assembly

| Manuscript method | Status | Where / note |
|---|:---:|---|
| DNA extraction (NEB Monarch kit) | n/a | wet-lab; not code |
| PacBio Revio, 4,919,653 HiFi reads, 144 Gb | ✅ | data; reads are input to [01](../01_De_novo_Assembly.md) |
| hifiasm, parameter-sensitivity rounds | ✅ | [01](../01_De_novo_Assembly.md) documents **5 builds** (v0 default + v1–v4). Manuscript says "**four** separate rounds." Reconcile the wording: four parameter *variants* on top of the default, or state five builds. | Wording has been reconciled to reflect 5 rounds.
| BlobTools contamination screening | ✅ | [02](../02_Filter_Contaminants.md) |
| Inspector structural repair | ✅ | [04](../04_Correct_Contigs.md) (commands now merged from the annotation notes) |
| Linkage-map anchoring, 500 N separators | ✅ | [05](../05_Scaffolding_via_LinkageMaps.md); 500 bp `N` gaps confirmed in the AGP |
| GenomeScope | ✅ | [01 §1b](../01_De_novo_Assembly.md) |
| BUSCO | ✅ | [02](../02_Filter_Contaminants.md), [03](../03_Purge_Duplicates.md), [annotation/03](../annotation/03_BRAKER3_and_TSEBRA.md) |
| QUAST | ✅ | [01 §3](../01_De_novo_Assembly.md) |
| Final: 46 scaffolds, 1.67 Gb, 8 chr, N50 ~268 Mb, L50 3 | ✅ | **verified on server** — assembly-stats reports sum 1,662,784,927, n=46, N50 267,643,161, L50 3 |

## Mitochondrial genome

| Manuscript method | Status | Where / note |
|---|:---:|---|
| MitoHiFi, 16,500 bp circular mtDNA | ✅ | product exists (`..._mtDNA.fa`); command not recorded — [annotation/05 §5.1](../annotation/05_Mitochondrial_and_NUMT.md) |
| NUMT: 13,921 bp on chr7, minimap2 + mosdepth + bedtools windows | ✅ | described only; commands not recorded — [annotation/05 §5.3](../annotation/05_Mitochondrial_and_NUMT.md) |
| mtDNA annotation: MITOS2, MFannot (Galaxy), EZmito2 | ❌ | product exists (`..._mtDNA.gff`); Galaxy tool versions/params not recorded — [annotation/05 §5.2](../annotation/05_Mitochondrial_and_NUMT.md) |

## Repeat masking

| Manuscript method | Status | Where / note |
|---|:---:|---|
| RepeatModeler + RepeatMasker | ✅ | [annotation/01](../annotation/01_Repeat_Masking.md) |
| RepBase, SINEBase, Dfam, TransposonPSI, MITE-Tracker, LTRharvest/digest, Orthoptera lib | ✅ | [annotation/01](../annotation/01_Repeat_Masking.md) |
| 3,182-sequence library, 47.56% soft-masked | ✅ | library committed in `annotation/`; figure stated in [annotation/01](../annotation/01_Repeat_Masking.md) |

## RNA / Iso-seq

| Manuscript method | Status | Where / note |
|---|:---:|---|
| Short-read RNA-seq (NovaSeq, 8 males + SRA sets) | ✅ | evidence used in [annotation/02–03](../annotation/02_Annotation_Transfer_and_Evidence.md) |
| Iso-seq library (Kinnex), PacBio Revio | ✅ | evidence used in [annotation/02](../annotation/02_Annotation_Transfer_and_Evidence.md) |
| Iso-seq preprocessing: **lima 2.9.0, skera 1.2.0** | ❌ | produces `isoseq_Lkoh_refined.fa`; commands not recorded — [annotation/02 §2.3](../annotation/02_Annotation_Transfer_and_Evidence.md) |

## Structural and functional annotation

| Manuscript method | Status | Where / note |
|---|:---:|---|
| Liftoff transfer of prior annotation | ✅ | [annotation/02](../annotation/02_Annotation_Transfer_and_Evidence.md) |
| TAGADA gene-model update | ✅ | [annotation/02](../annotation/02_Annotation_Transfer_and_Evidence.md) |
| TransDecoder | ✅ | [annotation/02](../annotation/02_Annotation_Transfer_and_Evidence.md) |
| OrthoDB Arthropoda protein evidence | ✅ | [annotation/03](../annotation/03_BRAKER3_and_TSEBRA.md) |
| BRAKER3 ×2 (RNA-seq 15,186; Iso-seq 16,031 genes) | ✅ | [annotation/03](../annotation/03_BRAKER3_and_TSEBRA.md) — counts match notes |
| TSEBRA merge → final gene set | ⚠️ | **count mismatch:** notes say **17,866**, manuscript says **17,670**. Reconcile — likely a post-TSEBRA filter not recorded. [annotation/03 §3.5](../annotation/03_BRAKER3_and_TSEBRA.md) |
| InterProScan | ✅ | [annotation/04](../annotation/04_Functional_Annotation.md) |
| eggNOG-mapper | ✅ | [annotation/04](../annotation/04_Functional_Annotation.md) |
| BLAST-P vs *Drosophila* proteome | ✅ | [annotation/04](../annotation/04_Functional_Annotation.md) |
| AGAT integration | ✅ | [annotation/04](../annotation/04_Functional_Annotation.md) |

## Data accessions (from manuscript — add to the top-level README on acceptance)

| Item | Accession |
|---|---|
| BioProject | PRJNA1306088 |
| PacBio HiFi reads | SRR37501604 |
| Short-read RNA-seq | SRR37605704–SRR37605711 |
| Iso-seq reads | SRR37532061 |
| Assembly (GenBank) | JBYTER000000000 (BioSample SAMN55867830) |

---

## Action items before submission

1. **Fill the three mitochondrial/NUMT gaps** (❌ above) — the single biggest coverage hole.
   Products exist; the commands (or Galaxy tool versions) just need recording.
2. **Add the Iso-seq lima/skera commands** to
   [annotation/02 §2.3](../annotation/02_Annotation_Transfer_and_Evidence.md).
3. **Reconcile the final gene count** — 17,866 (notes) vs 17,670 (manuscript).
4. **Settle the hifiasm rounds wording** — five builds documented vs "four rounds."
5. **Pin the two `:latest` containers** (tetools, braker3) to digests — see
   [VERSIONS.md](VERSIONS.md).
6. **Confirm the inferred bare-command versions** in [VERSIONS.md](VERSIONS.md) (blastn,
   bedtools, gffread, seqkit).
7. **Fix the AGP linkage-evidence field** before NCBI submission — the final
   `...manual.chr_first.agp` has gap lines with `linkage=yes` but `evidence=na`, which is
   invalid AGP 2.1. Your `fix_agp_linkage_evidence.py` (sets `na`→`map`) was applied to the
   earlier round but not the final one.
