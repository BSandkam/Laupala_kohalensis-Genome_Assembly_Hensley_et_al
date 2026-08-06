# Annotation 03) Gene prediction with BRAKER3 and TSEBRA

**Goal:** Predict protein-coding genes on the soft-masked genome using two independent
evidence streams, then merge them.

**Rationale:** RNA-seq and Iso-seq capture different aspects of the transcriptome
(short-read depth vs long-read full-length structure). Running BRAKER3 separately on each
and merging with TSEBRA yields a gene set supported by both, rather than favouring one
evidence type.

**Input:** `contig_corrected_softmasked.fasta` from
[01_Repeat_Masking.md](01_Repeat_Masking.md); protein evidence from
[02_Annotation_Transfer_and_Evidence.md](02_Annotation_Transfer_and_Evidence.md)
**Output:** `braker_combined.gtf` / `.gff`

`braker3.sif` is `docker://teambraker/braker3:latest` (BRAKER3 — AUGUSTUS + GeneMark +
TSEBRA bundled).

---

## 3.1) Prepare protein evidence

Combine OrthoDB Arthropoda proteins with the species-specific TransDecoder peptides.

```sh
wget https://bioinf.uni-greifswald.de/bioinf/partitioned_odb11/Arthropoda.fa.gz
gunzip Arthropoda.fa.gz

bash prot_header_modify.sh Lkoh_liftoff_tagada_transdecoder.pep
cat Arthropoda.fa Lkoh_liftoff_tagada_transdecoder.pep > proteinDB.fasta
```

## 3.2) Trim RNA-seq reads

```sh
trim_galore --paired -j 10 -q 30 \
  K10_R1.fastq.gz K10_R2.fastq.gz K3_R1.fastq.gz K3_R2.fastq.gz \
  K6_R1.fastq.gz K6_R2.fastq.gz K8_R1.fastq.gz K8_R2.fastq.gz \
  K2_R1.fastq.gz K2_R2.fastq.gz \
  SRR24757042_R1.fastq.gz SRR24757042_R2.fastq.gz \
  SRR24757044_R1.fastq.gz SRR24757044_R2.fastq.gz \
  K4_R1.fastq.gz K4_R2.fastq.gz K7_R1.fastq.gz K7_R2.fastq.gz \
  K9_R1.fastq.gz K9_R2.fastq.gz \
  SRR24757043_R1.fastq.gz SRR24757043_R2.fastq.gz \
  SRR24757045_R1.fastq.gz SRR24757045_R2.fastq.gz &
```

## 3.3) BRAKER3 — RNA-seq run

```sh
singularity exec -C \
  --env AUGUSTUS_CONFIG_PATH=$PWD/config \
  --bind ~/genome_finalize/ --pwd $PWD \
  braker3.sif braker.pl \
  --species=kohalensis_ranseq \
  --genome=~/genome_finalize/inspector_corrected/contig_corrected_softmasked.fasta \
  --threads=48 \
  --prot_seq=~/genome_finalize/annotation/orthodb/proteinDB.fasta \
  --rnaseq_sets_ids=SRR24757043,SRR24757044,SRR24757045,SRR24757042,K9,K8,K7,K6,K4,K3,K2,K10 \
  --rnaseq_sets_dirs=~/genome_finalize/annotation/trimmed_rnaseq/ \
  --workingdir=~/genome_finalize/annotation/braker/braker1_rnaseq
```

Predicted: **15,186 genes**.

## 3.4) BRAKER3 — Iso-seq run

```sh
singularity exec -C \
  --env AUGUSTUS_CONFIG_PATH=$PWD/config \
  --bind ~/genome_finalize/ --pwd $PWD \
  braker3.sif braker.pl \
  --species=kohalensis_isoseq \
  --genome=~/genome_finalize/inspector_corrected/contig_corrected_softmasked.fasta \
  --threads=48 \
  --prot_seq=~/genome_finalize/annotation/orthodb/proteinDB.fasta \
  --bam=~/genome_finalize/annotation/isoseq/isoseq_corrected_contigs_sorted.bam \
  --workingdir=~/genome_finalize/annotation/braker/braker2_isoseq
```

Predicted: **16,031 genes**.

> The Iso-seq BAM (`isoseq_corrected_contigs_sorted.bam`) is the sorted form of the
> `isoseq_corrected_contigs.sam` produced in
> [02_Annotation_Transfer_and_Evidence.md](02_Annotation_Transfer_and_Evidence.md#23-iso-seq-alignment).

## 3.5) Merge with TSEBRA

```sh
singularity exec -C \
  --env AUGUSTUS_CONFIG_PATH=$PWD/config \
  --bind ~/genome_finalize/ --pwd $PWD \
  braker3.sif tsebra.py \
  -g ~/genome_finalize/annotation/braker/braker1_rnaseq/braker.gtf,~/genome_finalize/annotation/braker/braker2_isoseq/braker.gtf \
  -e ~/genome_finalize/annotation/braker/braker1_rnaseq/hintsfile.gff,~/genome_finalize/annotation/braker/braker2_isoseq/hintsfile.gff \
  -o braker_combined
```

## 3.6) BUSCO of the final annotation

```sh
singularity exec --bind ~/genome_finalize/ --pwd $PWD /programs/agat-1.2.0/agat.sif \
  agat_sp_extract_sequences.pl \
  -g braker_combined.gtf \
  -f ~/genome_finalize/inspector_corrected/contig_corrected_softmasked.fasta \
  -t cds -p

busco -i braker_combined_aa.fasta -o busco_insecta_braker_combined_aa \
  -m protein -l insecta_odb10 -c 20
```

---

**Next:** [04_Functional_Annotation.md](04_Functional_Annotation.md)
