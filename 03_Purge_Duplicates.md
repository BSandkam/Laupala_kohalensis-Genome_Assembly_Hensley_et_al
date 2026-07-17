# 03) Purge duplicate contigs

**Goal:** Remove redundant/haplotypic contigs remaining after assembly.

**Rationale:** De novo assembly frequently retains both haplotypes of a region as
separate contigs. hifiasm performs some purging internally, but a meaningful number of
redundant contigs typically remain. `purge_dups` maps the assembly against itself to
identify and remove redundant sequence.

**How we know it worked (and didn't overshoot):** BUSCO is the control. After purging we
want the number of **duplicated** BUSCOs to fall and **single-copy** BUSCOs to rise,
while the **total** number of BUSCOs found stays flat. A drop in total BUSCOs found would
mean we had over-purged and thrown away real sequence. This before/after comparison is
made explicit in `Busco_Improvements.txt` below.

**Input:** `FilteredKohalensis.v0.Genome.fasta` + `Kohalensis.CleanedReads.fastq` from [02](02_Filter_Contaminants.md)
**Output:** `Kohalensis.purged.fa`

Reference: https://github.com/dfguan/purge_dups#--pipeline-guide

---

## 3a) Run purge_dups

```txt
minimap2
    -x map-hifi     settings for mapping HiFi reads
    -t 90           number of threads
    -xasm5          asm-to-ref mapping, for ~0.1% sequence divergence
    -D              If query sequence name/length are identical to the target, ignore
                    diagonal anchors; also reduces DP-based extension along the diagonal
    -P              Retain all chains, don't attempt to set primary chains
purge_dups
    -2              2 rounds chaining
    -T              cutoffs file
    -c              base-level coverage file
```

```sh
for MORPH in Kohalensis
do
    ## Make directory and add the cleaned scaffolds and cleaned reads
    mkdir -p ~/Kohalensis_Genome/03_Purge_Duplicates/Purge_Dups_run1
    cd ~/Kohalensis_Genome/03_Purge_Duplicates/Purge_Dups_run1

    # Link to the contigs
    ln -s ~/Kohalensis_Genome/02_Remove_Contam/FilteredKohalensis.v0.Genome.fasta Filtered$MORPH.Genome.fasta

    # Link to the cleaned reads (after contamination removal)
    ln -s ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.CleanedReads.fastq .

    # Map the cleaned reads to the filtered build
    /programs/minimap2-2.24/minimap2 -t 90 -x map-hifi Filtered$MORPH.Genome.fasta $MORPH.CleanedReads.fastq | gzip -c - > $MORPH.mapped.paf.gz

    # Make PB.base.cov and PB.stat files with pbcstat
    ~/Programs/purge_dups/bin/pbcstat $MORPH.mapped.paf.gz
    ~/Programs/purge_dups/bin/calcuts PB.stat > cutoffs 2>calcults.log

    # Split the assembly and run a self-self alignment
    ~/Programs/purge_dups/bin/split_fa Filtered$MORPH.Genome.fasta > Filtered$MORPH.Genome.fasta.split
    /programs/minimap2-2.24/minimap2 -xasm5 -t 90 -DP Filtered$MORPH.Genome.fasta.split Filtered$MORPH.Genome.fasta.split | gzip -c - > Filtered$MORPH.Genome.fasta.split.self.paf.gz

    # Purge haplotigs and overlaps
    ~/Programs/purge_dups/bin/purge_dups -2 -T cutoffs -c PB.base.cov Filtered$MORPH.Genome.fasta.split.self.paf.gz > dups.$MORPH.bed 2> purge_dups.$MORPH.log

    # Get the purged primary and haplotig sequences
    ~/Programs/purge_dups/bin/get_seqs -e dups.$MORPH.bed Filtered$MORPH.Genome.fasta
    cp purged.fa ../$MORPH.purged.fa
done
```

---

## 3b) Confirm it did not over-purge

```txt
busco
    -i SEQUENCE_FILE
    --force                     Force rewriting of existing files
    --lineage_dataset LINEAGE   BUSCO lineage to use
    --mode genome               for genome assemblies (DNA)
    --cpu 90                    Number of threads/cores to use
minimap2
    -x map-hifi  settings for mapping HiFi reads to reference
    -a           output in the sam format
    -t 90        threads
samtools flagstat  counts the number of alignments for each FLAG type
```

```sh
# Run BUSCO on the purged assembly
source /programs/miniconda3/bin/activate busco-5.2.2
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/03_Purge_Duplicates
    busco -i $MORPH.purged.fa --force --lineage_dataset ~/Databases/busco/busco_downloads/lineages/insecta_odb10 -o $MORPH.postpurge.busco --mode genome --cpu 90
done
conda deactivate

# Compare BUSCO before cleaning and after purging duplicates
cd ~/Kohalensis_Genome/03_Purge_Duplicates
for MORPH in Kohalensis
do
    echo "$MORPH Differences between   <<<<< precleaned <<<<<    and    >>>>>   post purge_dups >>>>>" >> Busco_Improvements.txt
    diff -y ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.busco.preclean/short_summary.specific.insecta_odb10.$MORPH.* ~/Kohalensis_Genome/03_Purge_Duplicates/$MORPH.postpurge.busco/short_summary.specific.insecta_odb10.$MORPH.*  >> Busco_Improvements.txt
    echo -e "\n\n\n" >> Busco_Improvements.txt
done
head -n -3 Busco_Improvements.txt > tmp.txt && mv tmp.txt Busco_Improvements.txt

# Map the cleaned reads back to the purged assembly
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/03_Purge_Duplicates
    /programs/minimap2-2.24/minimap2 -x map-hifi -a -t 90 $MORPH.purged.fa ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.CleanedReads.fastq | samtools view --threads 90 -b - | samtools sort -o $MORPH.to.purged.bam --threads 90 -
    samtools flagstat --threads 90 $MORPH.to.purged.bam > $MORPH.to.purged.bam.mapstats
done

# Calculate coverage and write a yaml for blobtools
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/03_Purge_Duplicates
    samtools coverage $MORPH.to.purged.bam > $MORPH.to.purged.bam.coverage
    echo -e "assembly:\n  level: contig\n  prefix: $MORPH.purged\ntaxon:\n  name: Laupala kohalensis" > $MORPH.meta.yaml
done

# Build a post-purge blob dataset
mkdir -p ~/Kohalensis_Genome/Blob_Datasets
cd ~/Kohalensis_Genome/Blob_Datasets

source /programs/miniconda3/bin/activate btk_env
export BTK_ROOT=/programs/blobtoolkit-2.6.3

for MORPH in Kohalensis
do
    $BTK_ROOT/blobtools2/blobtools create \
        --threads 90 \
        --fasta ~/Kohalensis_Genome/03_Purge_Duplicates/$MORPH.purged.fa \
        --replace \
        --taxdump ~/Databases/taxdump \
        --meta ~/Kohalensis_Genome/03_Purge_Duplicates/$MORPH.meta.yaml \
        --text ~/Kohalensis_Genome/03_Purge_Duplicates/$MORPH.to.purged.bam.coverage \
        --text-header \
        --text-cols '#rname=identifier,meandepth=my_reads_cov' \
        --key plot.y=my_reads_cov \
        --busco ~/Kohalensis_Genome/03_Purge_Duplicates/$MORPH.postpurge.busco/run_insecta_odb10/full_table.tsv \
        ~/Kohalensis_Genome/Blob_Datasets/$MORPH\_03_post_purge_dups
done
conda deactivate
```

---

**Next step:** [04_Correct_Contigs.md](04_Correct_Contigs.md)
