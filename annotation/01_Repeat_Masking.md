# Annotation 01) Repeat library construction and masking

**Goal:** Build a species-specific repeat library and soft-mask the corrected genome so
that BRAKER3 gene prediction is repeat-aware.

**Rationale:** *Laupala* is a large, repeat-rich genome. A de novo library from
RepeatModeler alone misses lineage-specific and structurally-defined elements, so it is
combined with structure-based finders (LTRharvest/digest, MITE-Tracker), a homology finder
(TransposonPSI), curated databases (RepBase, SINEBase, Dfam), and an Orthoptera-specific
library, then classified and de-duplicated. The final library soft-masks **47.56%** of the
genome.

**Input:** `contig_corrected.fa` from [../04_Correct_Contigs.md](../04_Correct_Contigs.md)
**Output:** `combined_library_Lko_ortho.lib.minlen50.nr.classified.fa` (included in this
directory) and `contig_corrected_softmasked.fasta`

The container `tetools.sif` is `docker://dfam/tetools:latest` (Dfam TE Tools: RepeatModeler
2.x + RepeatMasker 4.x).

---

## 1.1) RepeatModeler

```sh
singularity pull tetools.sif docker://dfam/tetools:latest

singularity run --bind ~/genome_finalize --pwd ~/genome_finalize/annotation/repeatmodeler \
  ./tetools.sif \
  BuildDatabase -name kohalensis ~/genome_finalize/inspector_corrected/contig_corrected.fa

singularity run --bind $PWD --pwd $PWD ./tetools.sif \
  RepeatModeler -database kohalensis -threads 20 -LTRStruct
```

## 1.2) TransposonPSI

```sh
perl transposonPSI.pl ~/genome_finalize/inspector_corrected/contig_corrected.fa nuc
```

## 1.3) MITE-Tracker

```sh
source /programs/miniconda3/bin/activate mitetracker
export PATH=/programs/vsearch-2.23.0/bin:$PATH

python -m MITETracker \
  -g ~/genome_finalize/inspector_corrected/contig_corrected.fa \
  -w 100 -j Lkoh_MiteTracker
```

## 1.4) LTRharvest and LTRdigest

```sh
/programs/genometools-1.5.9/bin/gt suffixerator \
  -db ~/genome_finalize/inspector_corrected/contig_corrected_ltr_headers.fa \
  -indexname kohalensis_index \
  -tis -suf -lcp -des -ssp -dna

/programs/genometools-1.5.9/bin/gt ltrharvest \
  -index kohalensis_index -v \
  -out LkoLtrHarvest.out -outinner LkoLtrHarvest.outinner -gff3 LkoLtrHarvest.gff
```

## 1.5) Combine sources, cluster, and classify

Combined sources:

- RepeatModeler
- RepBase
- SINEBase
- TransposonPSI
- MITE-Tracker
- LTRHarvest / LTRDigest
- Orthoptera-specific repeat library (Liu, Zhao et al. 2024; figshare
  `10.6084/m9.figshare.23993616.v3`)

```sh
# Remove short sequences
/programs/seqtk/seqtk seq -L 50 combined_library_Lko.lib > combined_library_Lko.lib.minlen50

# Cluster redundant sequences, then append the Orthoptera library
/programs/usearch11.0.667/usearch \
  -cluster_fast combined_library_Lko.lib.minlen50 \
  -id 0.8 -consout combined_library_Lko.lib.minlen50.nr
cat combined_library_Lko.lib.minlen50.nr Orthoptera-TElib_v3.fa > combined_library_Lko_ortho.lib.minlen50.nr

# Classify
singularity run --bind $PWD --pwd $PWD ./tetools.sif \
  RepeatClassifier \
  -consensi ~/genome_finalize/annotation/repeatmodeler/consensi.fa \
  -threads 40 \
  -repeatmasker_dir ~/genome_finalize/annotation/repeatmodeler/RepeatMasker

cp consensi.fa.classified ./repeat_libraries/combined_library_Lko.lib.minlen50.nr.classified.fa
```

### Screen "Unknown" elements against a protein database

Remove from the "Unknown" class anything that is actually a real protein rather than a TE,
by BLASTing the Unknowns against insect UniProt and keeping only hits that are *not*
transposon-related.

```sh
grep "Unknown" combined_library_Lko_ortho.lib.minlen50.nr.classified.fa > UnknownIdslist.txt
wc -l UnknownIdslist.txt         # 2570
sed -i 's/>//g' UnknownIdslist.txt

wget https://raw.githubusercontent.com/santiagosnchez/faSomeRecords/master/faSomeRecords.py
python faSomeRecords.py \
  --fasta ./combined_library_Lko_ortho.lib.minlen50.nr.classified.fa \
  --list UnknownIdslist.txt --outfile UnknownRepeats.fasta
grep -c ">" UnknownRepeats.fasta  # 2570

makeblastdb -in uniprotkb_taxonomy_id_50557_AND_reviewe_2025_03_02.fasta \
  -dbtype prot -title uniprot_insecta -out uniprot_insecta
blastx -query UnknownRepeats.fasta -db uniprot_insecta -evalue 1e-10 \
  -num_threads 20 -max_target_seqs 1 \
  -outfmt '6 qseqid sseqid evalue bitscore sgi sacc stitle' -out Blast_out.txt

# 45 unique Unknowns had a protein hit; of those, 11 were not transposon-related
awk -F "\t" '{print $1,$7}' Blast_out.txt | sort | uniq \
  | grep -i -v "transposon" | grep -i -v "Copia protein" | grep -i -v "mobile element" \
  | grep -i -v "transposable" | grep -i -v "transposase" \
  | awk '{print $1}' > Unknowns_with_Prot_hit.txt   # 11

grep -c ">" combined_library_Lko_ortho.lib.minlen50.nr.classified.fa   # 3182 total sequences
```

The final library (`combined_library_Lko_ortho.lib.minlen50.nr.classified.fa`, 3,182
sequences) is committed in this directory.

## 1.6) RepeatMasker

```sh
singularity run --bind ~/genome_finalize --pwd ~/genome_finalize/annotation/repeatmodeler \
  ./tetools.sif \
  RepeatMasker \
  -lib ./combined_library_Lko_ortho.lib.minlen50.nr.classified.fa \
  ~/genome_finalize/inspector_corrected/contig_corrected.fa \
  -pa 40
```

## 1.7) Soft-mask the genome for BRAKER3

RepeatMasker produces a hard-masked `.out`; convert its coordinates to a BED and soft-mask.

```sh
awk 'NR>3 {print $5"\t"$6"\t"$7}' \
  ~/genome_finalize/inspector_corrected/contig_corrected.fa.out > awk_hard_masked_coords.bed

bedtools maskfasta -soft \
  -fi ~/genome_finalize/inspector_corrected/contig_corrected.fa \
  -bed awk_hard_masked_coords.bed \
  -fo contig_corrected_softmasked.fasta
```

---

**Next:** [02_Annotation_Transfer_and_Evidence.md](02_Annotation_Transfer_and_Evidence.md)
