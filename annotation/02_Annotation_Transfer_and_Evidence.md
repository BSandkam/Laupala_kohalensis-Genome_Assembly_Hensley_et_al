# Annotation 02) Annotation transfer and transcript evidence

**Goal:** Seed the annotation by transferring the existing *L. kohalensis* gene models onto
the corrected contigs, then build transcript evidence from RNA-seq and Iso-seq for BRAKER3.

**Rationale:** Rather than annotate from scratch, the prior annotation is lifted onto the
corrected assembly (Liftoff), giving a starting gene set. RNA-seq is assembled into
transcript models with TAGADA, Iso-seq reads are aligned as long-read evidence, and ORFs
are predicted from the TAGADA models with TransDecoder. These become the protein/transcript
evidence for gene prediction.

**Input:** `contig_corrected.fa` from [../04_Correct_Contigs.md](../04_Correct_Contigs.md);
prior annotation `Lko_genes.gff`; RNA-seq and Iso-seq reads
**Output:** transferred/polished GTF, TAGADA `novel.gtf`, and TransDecoder peptides

---

## 2.1) Transfer the prior annotation with Liftoff

```sh
export PYTHONPATH=/programs/liftoff-1.6.3.2/lib64/python3.9/site-packages:/programs/liftoff-1.6.3.2/lib/python3.9/site-packages
export PATH=/programs/liftoff-1.6.3.2/bin:$PATH

liftoff \
  -g ~/genome_finalize/annotation/liftoff/Lko_genes.gff \
  -o ~/genome_finalize/annotation/liftoff/l_kohalensis_cleaned_contigs.gff3 \
  -u ~/genome_finalize/annotation/liftoff/L_kohalensis_unmapped_features.txt \
  -a 0.8 -s 0.8 -p 20 -copies -sc 1.0 \
  -mm2_options="-sr -x asm5 -a --eqx --end-bonus 5 -N 50 -p 0.5" \
  -polish \
  -m /programs/minimap2-2.27/minimap2 \
  ~/genome_finalize/inspector_corrected/contig_corrected.fa \
  ~/genome_v1/ncbi_dataset/data/GCA_002313205.1/GCA_002313205.1_ASM231320v1_genomic.fasta
```

Convert the polished GFF3 to GTF for TAGADA:

```sh
singularity run --bind $PWD --pwd $PWD /programs/agat-1.2.0/agat.sif \
  agat_convert_sp_gff2gtf.pl \
  --gff ~/genome_finalize/annotation/liftoff/l_kohalensis_cleaned_contigs.gff3_polished \
  --gtf_version 3 \
  -o L_kohalensis_cleaned_contigs_polished.gtf
```

---

## 2.2) RNA-seq transcript assembly with TAGADA

TAGADA is run through Nextflow with Singularity. `reads.txt` and `metadata.tsv` describe
the RNA-seq libraries; assembly and quantification are grouped by sex and tissue.

```sh
export PYTHONPATH=/programs/nextflow-23.10.1/lib/python3.9/site-packages
export PATH=/programs/nextflow-23.10.1/bin:$PATH

nextflow run analysis-TAGADA/main.nf \
  -r 2.1.3 \
  -profile singularity \
  -work-dir ~/temp/ \
  --output ~/genome_finalize/annotation/tagada/ \
  --reads ~/genome_finalize/annotation/tagada/reads.txt \
  --metadata ~/genome_finalize/annotation/tagada/metadata.tsv \
  --assemble-by sex,tissue \
  --quantify-by sex,tissue \
  --annotation ~/genome_finalize/annotation/tagada/L_kohalensis_cleaned_contigs_polished.gtf \
  --genome ~/genome_finalize/inspector_corrected/contig_corrected.fa \
  --max-time 144h \
  --max-cpus 20
```

Final TAGADA annotation: `~/genome_finalize/annotation/tagada/annotation/novel.gtf`

---

## 2.3) Iso-seq alignment

```sh
minimap2 -ax splice:hq -uf \
  ~/genome_finalize/inspector_corrected/contig_corrected.fa \
  isoseq_Lkoh_refined.fa \
  > isoseq_corrected_contigs.sam
```

> [!NOTE]
> The manuscript states the raw Iso-seq reads were processed with **lima v2.9.0** and
> **skera v1.2.0** (PacBio Kinnex primer removal and segmentation) to produce the refined
> Iso-seq reads (`isoseq_Lkoh_refined.fa`) used above. Those two commands are not recorded
> in the annotation notes — see [../docs/MANUSCRIPT_COVERAGE.md](../docs/MANUSCRIPT_COVERAGE.md).
> They should be added here before publication.

---

## 2.4) ORF prediction from the TAGADA models with TransDecoder

```sh
# Generate a cDNA fasta from the TAGADA GTF
/programs/TransDecoder-v5.5.0/util/gtf_genome_to_cdna_fasta.pl \
  ~/genome_finalize/annotation/tagada/annotation/novel.gtf \
  ~/genome_finalize/inspector_corrected/contig_corrected.fa \
  > transcripts_tagada_annotation.fasta

# Convert the GTF to an alignment GFF3
/programs/TransDecoder-v5.5.0/util/gtf_to_alignment_gff3.pl \
  ~/genome_finalize/annotation/tagada/annotation/novel.gtf \
  > novel.gff3

# Predict ORFs
export PATH=/programs/TransDecoder-v5.5.0:$PATH
TransDecoder.LongOrfs -t transcripts_tagada_annotation.fasta
TransDecoder.Predict  -t transcripts_tagada_annotation.fasta
```

The resulting peptides (`Lkoh_liftoff_tagada_transdecoder.pep`) are used as species-specific
protein evidence in [03_BRAKER3_and_TSEBRA.md](03_BRAKER3_and_TSEBRA.md).

---

**Next:** [03_BRAKER3_and_TSEBRA.md](03_BRAKER3_and_TSEBRA.md)
