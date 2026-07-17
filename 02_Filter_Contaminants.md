# 02) Filter contaminant contigs

**Goal:** Identify and remove contigs derived from non-target organisms.

**Rationale:** DNA was extracted from whole-body samples, so contamination from gut
bacteria and other associated microbes is expected. Contigs are classified by BLASTing
against the NCBI nt database; contigs whose best hits fall outside Arthropoda are
candidates for removal. Rather than trusting taxonomic assignment alone, classification
is cross-checked against **read coverage**, **GC content**, and **contig length** — true
*Laupala* contigs are expected at ~48X or ~24X coverage (the latter being alternatively
phased regions), ~35% GC, and are generally long. This cross-check mattered: it caught a
contig that taxonomy alone would have wrongly discarded (see 2c below).

**Input:** `Kohalensis.v0.asm.bp.p_ctg.gfa.fasta` from [01](01_De_novo_Assembly.md)
**Output:** `FilteredKohalensis.v0.Genome.fasta` + `Kohalensis.CleanedReads.fastq`

---

## 2a) Set up the databases

Following https://blobtoolkit.genomehubs.org/install/

```sh
cd ~/Databases

# Add NCBI taxdump for using taxon information
mkdir -p taxdump
cd taxdump
curl -L ftp://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz | tar xzf -
cd ..

# Add NCBI nt database (a copy is kept on BioHPC - otherwise download from NCBI)
cp -r /shared_data/genome_db/BLAST_NCBI .

# Add BUSCO lineages
mkdir -p busco
cd busco
wget -q -O eukaryota_odb10.gz "https://busco-data.ezlab.org/v4/data/lineages/eukaryota_odb10.2020-09-10.tar.gz" \
        && tar xzf eukaryota_odb10.gz -C busco
wget -q -O insecta_odb10.gz "https://busco-data.ezlab.org/v4/data/lineages/insecta_odb10.2020-09-10.tar.gz" \
        && tar xzf insecta_odb10.gz
```

---

## 2b) Prep the assembly for BlobTools

```txt
minimap2
    -x map-hifi  settings for mapping HiFi reads to reference
    -a           output in the sam format
    -t 100       threads
samtools sort
    -T PREFIX    Write temporary files to PREFIX.nnnn.bam
samtools flagstat  counts the number of alignments for each FLAG type
blastn
    -db                                     BLAST database name
    -query                                  Query file name
    -outfmt "6 qseqid staxids bitscore std" Tabular output with the specified fields
    -max_target_seqs 10                     Number of aligned sequences to keep
    -max_hsps 1                             Max HSPs per query-subject pair
    -evalue 1e-25                           Expect value for saving hits
    -num_threads 100                        Number of threads to use
```

```sh
# Map the reads back to the hifiasm build
for MORPH in Kohalensis
do
    mkdir -p ~/Kohalensis_Genome/02_Remove_Contam
    cd ~/Kohalensis_Genome/02_Remove_Contam
    ln -s ~/Kohalensis_Genome/01_hifiasm/$MORPH/$MORPH.v0.asm.bp.p_ctg.gfa.fasta
    ln -s ~/Sequencing_Reads/DNA/Cricket_PacBio/l_kohalensis_hifi_raw_data_D01/hifi_reads/$MORPH.HiFi_reads.fq
    /programs/minimap2-2.24/minimap2 -x map-hifi -a -t 100 $MORPH.v0.asm.bp.p_ctg.gfa.fasta $MORPH\_HiFi_reads.fq | samtools view --threads 100 -b - | samtools sort -o $MORPH.to.self.bam --threads 100 -
    samtools flagstat --threads 100 $MORPH.to.self.bam > $MORPH.to.self.bam.mapstats
done

# Confirm that all reads mapped
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam
    echo "Total number of $MORPH HiFi reads" > $MORPH.mapping_check.txt
    wc -l ~/Sequencing_Reads/DNA/Cricket_PacBio/l_kohalensis_hifi_raw_data_D01/hifi_reads/$MORPH.HiFi_reads.fq | awk '{print $1/4}' >> $MORPH.mapping_check.txt
    echo "Total primary maps in $MORPH.to.self.bam" >> $MORPH.mapping_check.txt
    head -2 $MORPH.to.self.bam.mapstats | tail -1 >> $MORPH.mapping_check.txt
done

# Calculate per-contig coverage
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam
    samtools coverage $MORPH.to.self.bam > $MORPH.to.self.bam.coverage
done

# Run BUSCO on the original assembly
source /programs/miniconda3/bin/activate busco-5.2.2
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam
    busco -i $MORPH.v0.asm.bp.p_ctg.gfa.fasta --lineage_dataset ~/Databases/busco/busco_downloads/lineages/insecta_odb10 -o $MORPH.busco.preclean --mode genome --cpu 100
done
conda deactivate

# Megablast the assembly against the nt database
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam
    blastn -db ~/Databases/NCBI_nt/nt \
        -query $MORPH.v0.asm.bp.p_ctg.gfa.fasta \
        -outfmt "6 qseqid staxids bitscore std" \
        -max_target_seqs 10 \
        -max_hsps 1 \
        -evalue 1e-25 \
        -num_threads 100 \
        -out $MORPH.ncbi.blastn.out
done

# Make a yaml file to use with blobtools
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam
    echo -e "assembly:\n  level: contig\n  prefix: $MORPH\ntaxon:\n  name: Laupala kohalensis" > $MORPH.meta.yaml
done
```

### Create the BlobTools dataset

See https://github.com/blobtoolkit/blobtoolkit/issues/33 for background.

```sh
source /programs/miniconda3/bin/activate btk_env
export BTK_ROOT=/programs/blobtoolkit-2.6.3
for MORPH in Kohalensis
do
    mkdir -p ~/Kohalensis_Genome/Blob_Datasets
    cd ~/Kohalensis_Genome/Blob_Datasets

    $BTK_ROOT/blobtools2/blobtools create \
        --threads 100 \
        --fasta ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.v0.asm.bp.p_ctg.gfa.fasta \
        --replace \
        --taxdump ~/Databases/taxdump \
        --hits ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.ncbi.blastn.out \
        --meta ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.meta.yaml \
        --text ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.to.self.bam.coverage \
        --text-header \
        --text-cols '#rname=identifier,meandepth=my_reads_cov' \
        --key plot.y=my_reads_cov \
        --busco ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.busco.preclean/run_insecta_odb10/full_table.tsv \
        ~/Kohalensis_Genome/Blob_Datasets/$MORPH\_01_hifiasm
done
conda deactivate
```

The resulting dataset was inspected through the BlobToolKit web viewer.

---

## 2c) Checking for misclassified contigs

Contigs classified as contamination were generally short (<1 Mb), low coverage (<9X), and
higher GC (~50%, vs ~35% for *Laupala*).

**But one contig — `ptg000062l` — was 17.6 Mb at 44X coverage**, which looks like genuine
*Laupala* despite being flagged as bacterial. This was investigated rather than accepted.

```sh
# Pull out the contig of interest
/programs/cdbfasta/cdbyank -a ptg000062l $MORPH.v0.asm.bp.p_ctg.gfa.fasta > just_ptg000062l.fasta

# Download the blast taxa database for more informative hit descriptions
wget ftp://ftp.ncbi.nlm.nih.gov/blast/db/taxdb.tar.gz
tar -zxvf taxdb.tar.gz

blastn -db ~/Databases/NCBI_nt/nt \
        -query just_ptg000062l.fasta \
        -outfmt "6 qseqid staxids bitscore evalue sscinames sskingdoms stitle mismatch positive gapopen" \
        -max_target_seqs 10 \
        -max_hsps 1 \
        -evalue 1e-25 \
        -num_threads 10 \
        -out just_ptg000062l.ncbi.blastn.out

# Number of positively matching bases, and species of the blast hits
awk -F"\t" '{print $9 "\t" $5}' just_ptg000062l.ncbi.blastn.out
## Only ~7 kb for each blast result.

# Check this is not a hybrid assembly of Kohalensis and Wolbachia by checking coverage.
# Find the region of ptg000062l carrying the blast hits
grep "00062l" Kohalensis.ncbi.blastn.out | awk '{print $10}'
## All the blast hits start at bp 3,811,219

# Plot depth in the region of interest and across the whole contig
~/Programs/samtools-1.19/samtools index -@ 10 Kohalensis.to.self.bam
~/Programs/samtools-1.19/samtools coverage --histogram --region 'ptg000062l:3-4M' --plot-depth -A Kohalensis.to.self.bam
~/Programs/samtools-1.19/samtools coverage --histogram --region 'ptg000062l' --plot-depth -A Kohalensis.to.self.bam
# Result - coverage looked even and as expected (~44X) in both cases
```

**Result:** The bacterial signal comes from *Wolbachia*, but it is confined to a single
horizontally transferred gene (~7 kb of matching sequence), not a co-assembled *Wolbachia*
genome. If a *Wolbachia* genome had been misassembled into this contig, coverage in that
region would spike relative to the rest of the contig (the ratio of *Wolbachia* cells to
*Laupala* cells is unlikely to be 1:1); coverage was instead flat at ~44X. **`ptg000062l`
is a genuine *Laupala* contig** and is explicitly retained during filtering below.

### Confirming no other contigs were misclassified

```sh
# Re-blast the contigs with more informative output
cd ~/Kohalensis_Genome/02_Remove_Contam
for MORPH in Kohalensis
do
    blastn -db ~/Databases/NCBI_nt/nt \
        -query $MORPH.v0.asm.bp.p_ctg.gfa.fasta \
        -outfmt "6 qseqid length pident evalue bitscore sskingdoms sscinames stitle slen sacc mismatch positive gapopen" \
        -max_target_seqs 10 \
        -max_hsps 1 \
        -evalue 1e-25 \
        -num_threads 30 \
        -out $MORPH.INFORMATIVE.ncbi.blastn.out
done

echo "Query_sequence_ID   Alignment_length    Percentage_of_identical_matches Expect_value    Bit_score   Subject_Super_Kingdom   Subject_Scientific_Name Subject_Title   Subject_sequence_length Subject_accession   Number_of_mismatches    Num_positive_scoring_matches    Num_gap_openings" > Headers_for_blast.txt
```

**1) Find contigs with blast hits to multiple kingdoms.**

```sh
awk '{print $1 "\t" $6}' Kohalensis.INFORMATIVE.ncbi.blastn.out | sort | uniq -c | sort -k1,2 -n | awk '($1 != 10)'
```

Result — only 4 contigs had hits to multiple kingdoms:

| Contig_ID | Num_hits | Kingdom |
| ------- | --------------- | ---------------- |
| ptg000106l | 1 | Eukaryota |
| ptg000173l | 1 | N/A |
| ptg000173l | 9 | Bacteria |
| ptg000062l | 2 | Eukaryota |
| ptg000062l | 4 | Bacteria |
| ptg000062l | 4 | Viruses |

**2) Find contigs that would be filtered out but still have >=24X coverage.**

```sh
awk '($6!="Arthropoda" && $6!="no-hit")' Kohalensis.BlobTable.tsv | wc -l
awk '($6!="Arthropoda" && $6!="no-hit")' Kohalensis.BlobTable.tsv | awk '($5 >= 24)'
```

Result: 114 contigs were not classified as `Arthropoda` or `no-hit`, but **only
`ptg000106l` also had >=24X coverage**. The pipeline is therefore not discarding
substantial genuine sequence.

---

## 2d) Filter the contaminants

```txt
samtools view
    -b          Output in bam format
    -L          Filter for overlap (BED) regions in FILE
    -@          Number of threads to use
bioawk
    -c fastx    input format is fastx
```

```sh
# Generate tables from the blob database
source /programs/miniconda3/bin/activate btk_env
export BTK_ROOT=/programs/blobtoolkit-2.6.3
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam

    $BTK_ROOT/blobtools2/blobtools filter \
    --table $MORPH.BlobTable.tsv \
    --table-fields gc,length,my_reads_cov,bestsumorder_phylum,bestsumorder_family,bestsumorder_class \
    ~/Kohalensis_Genome/Blob_Datasets/$MORPH\_01_hifiasm/$MORPH
done
conda deactivate

# Filter reads and contigs to remove contaminants and contigs with no coverage
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam

    # Index the de novo assembly
    /programs/cdbfasta/cdbfasta $MORPH.v0.asm.bp.p_ctg.gfa.fasta

    # Keep contigs that were classified Arthropoda or 'no-hit', plus ptg000062l (the
    # Wolbachia-HGT contig shown above to be genuine Laupala). Drop 'no-hit' contigs
    # that also had zero read coverage.
    awk '($6=="Arthropoda" || $6=="no-hit" || $2 =="ptg000062l")' $MORPH.BlobTable.tsv | awk '{if($6=="no-hit" && $5==0) {next} else {print $2}}' | /programs/cdbfasta/cdbyank $MORPH.v0.asm.bp.p_ctg.gfa.fasta.cidx > Filtered$MORPH.v0.Genome.fasta

    # Make a bed file of only the contigs being kept
    /programs/bioawk/bioawk -c fastx '{print $name,"1",length($seq)}' Filtered$MORPH.v0.Genome.fasta | tr " " "\t" > $MORPH.KeeperContigs.bed

    # Filter the bam for kept contigs and extract those reads as fastq (these are the
    # cleaned reads, free of contaminant-derived sequence)
    samtools view -b -@ 100 -L $MORPH.KeeperContigs.bed $MORPH.to.self.bam | samtools fastq -@ 100 - > $MORPH.CleanedReads.fastq
done
```

---

## 2e) Compare builds before and after filtering

```txt
busco
    -i SEQUENCE_FILE
    --force                     Force rewriting of existing files
    --lineage_dataset LINEAGE   BUSCO lineage to use
    --mode genome               for genome assemblies (DNA)
    --cpu 100                   Number of threads/cores to use
```

```sh
# Run BUSCO on the cleaned assembly
source /programs/miniconda3/bin/activate busco-5.2.2
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam
    busco -i Filtered$MORPH.v0.Genome.fasta --force --lineage_dataset ~/Databases/busco/busco_downloads/lineages/insecta_odb10 -o $MORPH.busco.postclean --mode genome --cpu 100
done
conda deactivate

# Map the cleaned reads back to the cleaned assembly
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam
    /programs/minimap2-2.24/minimap2 -x map-hifi -a -t 100 Filtered$MORPH.v0.Genome.fasta $MORPH.CleanedReads.fastq | samtools view --threads 100 -b - | samtools sort -o $MORPH.to.filtered.bam --threads 100 -
    samtools flagstat --threads 100 $MORPH.to.filtered.bam > $MORPH.to.filtered.bam.mapstats
done

# Calculate coverage and write a yaml for blobtools
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam
    samtools coverage $MORPH.to.filtered.bam > $MORPH.to.filtered.bam.coverage
    echo -e "assembly:\n  level: contig\n  prefix: $MORPH.filtered_for_contam\ntaxon:\n  name: Laupala kohalensis" > $MORPH.filtered.meta.yaml
done

# Megablast the cleaned assembly against nt
for MORPH in Kohalensis
do
    cd ~/Kohalensis_Genome/02_Remove_Contam
    blastn -db ~/Databases/NCBI_nt/nt \
        -query Filtered$MORPH.v0.Genome.fasta \
        -outfmt "6 qseqid staxids bitscore std" \
        -max_target_seqs 10 \
        -max_hsps 1 \
        -evalue 1e-25 \
        -num_threads 100 \
        -out $MORPH.cleaned.ncbi.blastn.out
done

# Build a post-filtering blob dataset for comparison
source /programs/miniconda3/bin/activate btk_env
export BTK_ROOT=/programs/blobtoolkit-2.6.3
for MORPH in Kohalensis
do
    mkdir -p ~/Kohalensis_Genome/Blob_Datasets
    cd ~/Kohalensis_Genome/Blob_Datasets

    $BTK_ROOT/blobtools2/blobtools create \
        --threads 100 \
        --fasta ~/Kohalensis_Genome/02_Remove_Contam/FilteredKohalensis.v0.Genome.fasta \
        --replace \
        --taxdump ~/Databases/taxdump \
        --hits ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.cleaned.ncbi.blastn.out \
        --meta ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.filtered.meta.yaml \
        --text ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.to.self.bam.coverage \
        --text-header \
        --text-cols '#rname=identifier,meandepth=my_reads_cov' \
        --key plot.y=my_reads_cov \
        --busco ~/Kohalensis_Genome/02_Remove_Contam/$MORPH.busco.postclean/run_insecta_odb10/full_table.tsv \
        ~/Kohalensis_Genome/Blob_Datasets/$MORPH\_02_removed_contam
done
conda deactivate
```

---

**Next step:** [03_Purge_Duplicates.md](03_Purge_Duplicates.md)
