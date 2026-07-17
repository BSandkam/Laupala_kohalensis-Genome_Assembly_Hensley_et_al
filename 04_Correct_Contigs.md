# 04) Evaluate and correct contigs with Inspector

**Goal:** Detect and correct assembly errors in the purged contigs before scaffolding.

**Rationale:** Scaffolding propagates any error present in the input contigs into the
final chromosome-scale build, and a structural error inside a contig cannot be fixed by
ordering contigs correctly. Inspector uses the raw HiFi reads to independently identify
misassemblies in the contigs and emit a corrected set. Running it *before* scaffolding
means the linkage map is applied to contigs that have already been reconciled with the
read evidence.

**Input:** `Kohalensis.purged.fa` from [03](03_Purge_Duplicates.md) + `Kohalensis.CleanedReads.fastq` from [02](02_Filter_Contaminants.md)
**Output:** `contig_corrected.fa` → carried forward as `Kohalensis.contig_corrected.fa`

Reference: Chen et al. 2021 — https://github.com/Maggi-Chen/Inspector

---

## Install

```sh
conda create --name ins
conda activate ins
conda install -c bioconda inspector
```

## Evaluate the purged contigs against the HiFi reads

```sh
source ~/Environments/Anaconda3/bin/activate inspector

ln -s ~/Kohalensis_Genome/02_Remove_Contam/Kohalensis.CleanedReads.fastq .

inspector.py \
    --contig Kohalensis.purged.fa \
    --read Kohalensis.CleanedReads.fastq \
    --thread 90 \
    -o inspector_out/ \
    --datatype hifi
```

## Produce the corrected contigs

Inspector's evaluation step (above) writes its results to `inspector_out/`. The corrected
contig set, `contig_corrected.fa`, is produced by Inspector's separate correction step,
which reads that output directory.

> [!IMPORTANT]
> **This command is not recorded in the original lab notebook and needs to be filled in
> before publication.** The corrected contigs (`contig_corrected.fa`) are the direct input
> to scaffolding, so this step is load-bearing for the final assembly, but only the
> *evaluation* command above was written down. Please confirm the exact correction command
> and datatype flag that were run and record them here — per Inspector's documentation it
> is `inspector-correct.py` operating on the `inspector_out/` directory, but the precise
> invocation used has been deliberately left blank rather than guessed at.

```sh
# TODO: record the exact inspector-correct.py command that was run.
```

The corrected contigs were then staged for scaffolding:

```sh
cd ~/Kohalensis_Genome/04_Scaffold_Contigs/05_Generate_AGP
cp ~/Kohalensis_Genome/Cleaned_Contigs_Inspector/contig_corrected.fa Kohalensis.contig_corrected.fa
```

---

**Next step:** [05_Scaffolding_via_LinkageMaps.md](05_Scaffolding_via_LinkageMaps.md)
