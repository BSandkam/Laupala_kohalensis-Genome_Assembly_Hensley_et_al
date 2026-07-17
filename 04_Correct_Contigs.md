# 04) Correct contigs with Inspector

**Goal:** Detect and correct assembly errors in the purged contigs before scaffolding and
annotation.

**Rationale:** Scaffolding and annotation both propagate any error present in the input
contigs, and a structural error inside a contig cannot be fixed by ordering contigs
correctly. Inspector uses the raw HiFi reads to independently identify misassemblies and
emit a corrected contig set. Everything downstream — scaffolding
([05](05_Scaffolding_via_LinkageMaps.md)) and the entire annotation
([annotation/](annotation/)) — is built on these corrected contigs.

**Input:** `Kohalensis.purged.fa` from [03](03_Purge_Duplicates.md) + the raw HiFi reads
**Output:** `contig_corrected.fa`

Reference: Chen et al. 2021 — https://github.com/Maggi-Chen/Inspector

> This step was run by Niko Hensley and is reproduced from his annotation notes. It is the
> hand-off point between the assembly pipeline and the annotation pipeline.

---

## Run Inspector

```sh
source /programs/miniconda3/bin/activate inspector

# Evaluate the purged contigs against the raw HiFi reads
inspector.py \
  -c ~/genome_finalize/genome/Kohalensis.purged.fa \
  -r ~/genome_v2/Shaw-NH-15308_2023_12_01/l_kohalensis_hifi_raw_data_D01/hifi_reads/raw_reads.fastq \
  -d hifi \
  -t 20 \
  -o ~/genome_finalize/inspector

# Produce the corrected contigs from the evaluation
inspector-correct.py \
  -i ~/genome_finalize/inspector \
  --datatype pacbio-hifi \
  -o ~/genome_finalize/inspector_corrected/
```

Corrected assembly output:

```text
~/genome_finalize/inspector_corrected/contig_corrected.fa
```

The corrected contigs were then staged for scaffolding:

```sh
cd ~/Kohalensis_Genome/04_Scaffold_Contigs/05_Generate_AGP
cp ~/genome_finalize/inspector_corrected/contig_corrected.fa Kohalensis.contig_corrected.fa
```

---

## BUSCO before and after correction

Confirms correction did not remove genuine gene content.

```sh
source /programs/miniconda3/bin/activate busco-5.5.0

# Pre-correction
busco -i ~/genome_finalize/genome/Kohalensis.purged.fa \
  -o purged_contigs -m genome -l insecta_odb10

# Post-correction
busco -i ~/genome_finalize/inspector_corrected/contig_corrected.fa \
  -o corrected_contigs -m genome -l insecta_odb10
```

The correction changed the assembly negligibly at the sequence level — total length moved
by ~200 bp (1,662,753,223 → 1,662,753,427) and contig count stayed at 108 — while fixing
local structural errors flagged against the reads.

---

**Next steps:** the corrected contigs feed two parallel branches that rejoin at the GFF
liftover:
- **Scaffolding:** [05_Scaffolding_via_LinkageMaps.md](05_Scaffolding_via_LinkageMaps.md)
- **Annotation:** [annotation/README.md](annotation/README.md)
