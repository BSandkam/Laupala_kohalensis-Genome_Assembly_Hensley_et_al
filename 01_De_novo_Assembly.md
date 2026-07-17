# 01) De novo assembly of HiFi reads

**Goal:** Generate de novo assemblies from PacBio HiFi reads across a range of hifiasm
parameters, then pick the build to carry forward.

**Rationale for a parameter sweep:** optimal hifiasm settings depend on the repeat/TE
profile of the genome and on the characteristics of the individual sequencing run, so
there is no single "correct" parameter set. We assembled under several settings and
compared the resulting builds rather than accepting defaults blindly.

**Outcome:** `v0` (hifiasm defaults) was carried forward into
[02_Filter_Contaminants.md](02_Filter_Contaminants.md).

Reference: https://hifiasm.readthedocs.io/en/latest/

> **Version note.** This assembly was run with **hifiasm 0.19.8-r603** (Dec 2023). Earlier
> notes referred to "v0.7" — that is the version tag in the *test-data download URL* below
> (`releases/download/v0.7/chr11-2M.fa.gz`), not the assembler version, and predates HiFi
> support entirely. The `v0`…`v4` in the run names are build labels for the parameter
> sweep, not versions. See [docs/VERSIONS.md](docs/VERSIONS.md).

---

## Prep — install hifiasm

```sh
# In the directory you want to install and will call hifiasm from:

# Install hifiasm (requires g++ and zlib)
git clone https://github.com/chhylp123/hifiasm
cd hifiasm && make

# Verify the install against the bundled test data
cd .. && mkdir test && cd test
wget https://github.com/chhylp123/hifiasm/releases/download/v0.7/chr11-2M.fa.gz
../hifiasm/hifiasm -o test -t4 -f0 chr11-2M.fa.gz 2> test.log
```

---

## 1) Generate fastq from the HiFi bam

```txt
samtools fastq
    -@          Number of additional threads to use [0]
    -0 FILE     Write reads designated READ_OTHER to FILE
```

```sh
cd ~/Sequencing_Reads/DNA/Cricket_PacBio/l_kohalensis_hifi_raw_data_D01/hifi_reads
samtools fastq -@ 80 -0 Kohalensis.HiFi_reads.fq m84094_231201_192252_s4.hifi_reads.default.bam
```

### Note on adaptor trimming

We tested PacBio adaptor filtering (HiFiAdapterFilt) as a possible preprocessing step.
Only **1 read** (2.03e-05% of the total) carried adaptor sequence at >=97% match over
>=44 bp. Assemblies built with and without that read were indistinguishable, so the
untrimmed reads were used for all downstream work and the adaptor-trimming branch was
dropped. See [README.md](README.md) for the full list of approaches that were tested and
set aside.

---

## 1b) GenomeScope — k-mer abundance and expected genome size

Establishes the expected haploid genome size and coverage, which informs `--hg-size`
below and gives the baseline coverage expectation (~48X / ~24X for phased regions) used
to sanity-check contigs during contaminant filtering.

```sh
export PATH=/programs/jellyfish-2.3.0/bin:$PATH

for MORPH in Kohalensis
do
    mkdir -p ~/Kohalensis_Genome/00_Preliminary_Stats/GenomeScope
    cd ~/Kohalensis_Genome/00_Preliminary_Stats/GenomeScope

    # Adaptor-filtered reads are not used here - adaptor content would not change
    # k-mer distributions.
    ln -s ~/Sequencing_Reads/DNA/Cricket_PacBio/l_kohalensis_hifi_raw_data_D01/hifi_reads/Kohalensis.HiFi_reads.fq .

    jellyfish count -C -m 21 -s 900M -t 100 Kohalensis.HiFi_reads.fq -o $MORPH.reads.jf
    jellyfish histo -t 100 $MORPH.reads.jf > $MORPH.reads.histo

    source ~/Environments/Anaconda3/bin/activate
    conda activate GenomeScope

    export PATH=~/Programs/genomescope2.0:$PATH
    genomescope.R -i $MORPH.reads.histo -o $MORPH.GenomeScope_out -k 21

    conda deactivate
done
```

---

## 2) Run hifiasm across parameter sets

```txt
Overlap/Error correction:
    -k INT       k-mer length (must be <64) [51]
    -D FLOAT     drop k-mers occurring >FLOAT*coverage times [5.0]
    -N INT       consider up to max(-D*coverage,-N) overlaps for each oriented read [100]
    --hg-size    INT(k, m or g)
                 estimated haploid genome size used for inferring read coverage [auto]
```

The swept parameters were chosen because they control the three levers most likely to
matter for a repeat-rich genome: k-mer length (`-k`), how aggressively high-frequency
k-mers are discarded (`-D`), and how many overlaps are considered per read (`-N`).

```sh
for MORPH in Kohalensis
do
    mkdir -p ~/Kohalensis_Genome/01_hifiasm/$MORPH
    cd ~/Kohalensis_Genome/01_hifiasm/$MORPH
    ln -s ~/Sequencing_Reads/DNA/Cricket_PacBio/l_kohalensis_hifi_raw_data_D01/hifi_reads/Kohalensis.HiFi_reads.fq .

    # Run v0 - Default hifiasm settings
    ~/Programs/hifiasm/hifiasm --hg-size 1.6g -t 40 -o $MORPH.v0.asm $MORPH.HiFi_reads.fq
    # Run v1 - kmer length of 63 (default 51)
    ~/Programs/hifiasm/hifiasm -k 63 --hg-size 1.6g -t 40 -o $MORPH.v1.asm $MORPH.HiFi_reads.fq
    # Run v2 - kmer length of 39 (default 51)
    ~/Programs/hifiasm/hifiasm -k 39 --hg-size 1.6g -t 40 -o $MORPH.v2.asm $MORPH.HiFi_reads.fq
    # Run v3 - -D (drop k-mers occurring >FLOAT*coverage) set to 10 (default 5)
    ~/Programs/hifiasm/hifiasm -D 10 --hg-size 1.6g -t 40 -o $MORPH.v3.asm $MORPH.HiFi_reads.fq
    # Run v4 - -N (max overlaps considered per oriented read) set to 150 (default 100)
    ~/Programs/hifiasm/hifiasm -N 150 --hg-size 1.6g -t 40 -o $MORPH.v4.asm $MORPH.HiFi_reads.fq

    for VERSION in v0 v1 v2 v3 v4
    do
        # Make fasta files of the primary contigs from the gfa files
        awk '/^S/{print ">"$2;print $3}' $MORPH.$VERSION.asm.bp.p_ctg.gfa > $MORPH.$VERSION.asm.bp.p_ctg.gfa.fasta

        echo "$MORPH $VERSION Just Primary Contigs" >> PrimaryContigsStats.txt
        /programs/assembly-stats/assembly-stats $MORPH.$VERSION.asm.bp.p_ctg.gfa.fasta >> PrimaryContigsStats.txt
        echo -e "\n" >> PrimaryContigsStats.txt
    done
done
```

---

## 3) Compare builds with QUAST

Reference: https://quast.sourceforge.net/docs/manual.html

```txt
    -o                          Output directory
    -t                          Number of threads to run
    --circos                    Draw Circos plot
    --eukaryote                 Is a eukaryote
    --conserved-genes-finding   Count conserved orthologs using BUSCO (only on Linux)
    --est-ref-size 1600000000   Estimated reference genome size (1.6 Gb)
    --k-mer-stats               Compute k-mer-based quality metrics
    --k-mer-size [default]      Size of k used in --k-mer-stats [default: 101]
    --gene-finding              Predicts genes using GeneMark-ES (when using --eukaryote)
    --pacbio FILE               File with PacBio reads (FASTQ, may be gzipped)
```

```sh
export PYTHONPATH=/programs/quast-5.2.0/lib64/python3.9/site-packages:/programs/quast-5.2.0/lib/python3.9/site-packages
export PATH=/programs/quast-5.2.0/bin:$PATH
export PATH=/programs/circos-0.69-9/bin:$PATH

for MORPH in Kohalensis
do
    # Compare all versions to one another, without a reference.
    cd ~/Kohalensis_Genome/01_hifiasm/$MORPH

    quast.py -o Quast_RelSelf -t 40 --circos --eukaryote --gene-finding --conserved-genes-finding --k-mer-stats --pacbio $MORPH.HiFi_reads.fq --est-ref-size 1600000000 \
        $MORPH.v0.asm.bp.p_ctg.gfa.fasta \
        $MORPH.v1.asm.bp.p_ctg.gfa.fasta \
        $MORPH.v2.asm.bp.p_ctg.gfa.fasta \
        $MORPH.v3.asm.bp.p_ctg.gfa.fasta \
        $MORPH.v4.asm.bp.p_ctg.gfa.fasta
done
```

**Note:** QUAST's built-in BUSCO step (`--conserved-genes-finding`) fails because it
tries to fetch BUSCO v3 lineage datasets that are no longer hosted. BUSCO was therefore
run directly against a current lineage dataset at each stage of the pipeline (see
[02_Filter_Contaminants.md](02_Filter_Contaminants.md) and
[03_Purge_Duplicates.md](03_Purge_Duplicates.md)) rather than through QUAST.

---

**Next step:** [02_Filter_Contaminants.md](02_Filter_Contaminants.md)
