# 05) Scaffold the contigs using linkage maps

**Goal:** Order and orient the corrected PacBio contigs into chromosome-scale scaffolds
using a previously generated linkage map.

**Rationale:** HiFi contigs are long but not chromosome-scale. With no Hi-C data for this
individual, the linkage map provides the independent long-range evidence needed to place
contigs onto chromosomes.

**Why map markers rather than the whole published assembly:** the linkage map markers are
defined by position on the existing NCBI *L. kohalensis* assembly (GCA_002313205.1). We
therefore extract a short window of sequence around each marker and align *only those
windows* to our contigs, rather than aligning the entire NCBI assembly. This deliberately
limits the influence of any misjoined scaffolds in the older, more fragmented NCBI
assembly — a misjoin there can only affect the individual markers it contains, instead of
dragging a whole scaffold's worth of alignment into the placement decision. (An earlier
approach that scaffolded from whole-assembly alignments was tested and set aside; see
[README.md](README.md).)

**Input:** `Kohalensis.contig_corrected.fa` from [04](04_Correct_Contigs.md)
**Output:** `Kohalensis_corrected_man_scaffolds.fa` + `Kohalensis.contig_corrected.manual.chr_first.agp`

**Linkage map source:** `LOD_scores (kohpar reanalysis).xlsx`, sheet `NO_PSEUDO_MARKERS`.
That sheet was exported to `.tsv` locally and uploaded to the server as `Linkage_Map.txt`.

---

## 5.1) Download and prep the NCBI genome

```sh
mkdir -p ~/Kohalensis_Genome/04_Scaffold_Contigs/01_ncbi_genome_prep
cd ~/Kohalensis_Genome/04_Scaffold_Contigs/01_ncbi_genome_prep

# Download the Laupala kohalensis genome from NCBI
/programs/ncbi_datasets/datasets download genome accession GCA_002313205.1 --include gff3,rna,cds,protein,genome,seq-report

unzip ncbi_dataset.zip

# Move the genome out of the ncbi folder structure
mv ncbi_dataset/data/GCA_002313205.1/GCA_002313205.1_ASM231320v1_genomic.fna ncbi_genome_raw.fa

# Clean up the ncbi folder structure so only the fasta remains
rm -r ncbi_data*
rm README.md

# Rename fasta headers to use the contig names used in the map (simplifies mapping steps)
awk '/^>/ {gsub(/,/, "", $6); print ">"$6; next} {print}' ncbi_genome_raw.fa | sed 's/Lko057//' > ncbi_genome_renamed.fa
```

---

## 5.2) Extract the NCBI regions containing the markers

Each marker is expanded to an 800 bp window: 200 bp before and 600 bp after the marker
position. One marker sits near the start of its scaffold (hence only 200 bp upstream) and
one scaffold is only 940 bp long (hence capping at 800 bp so the window does not
overrun).

```sh
mkdir -p ~/Kohalensis_Genome/04_Scaffold_Contigs/02_Marker_Prep
cd ~/Kohalensis_Genome/04_Scaffold_Contigs/02_Marker_Prep

ln -s ../01_ncbi_genome_prep/ncbi_genome_renamed.fa .

# Build the marker windows. One marker entry has no basepair position, which breaks the
# bed file - those lines are excluded with an inverted grep.
tail -n +2 Linkage_Map.txt | awk '{print $1}' | awk -F "_" '{print $1 "\t" $2-200 "\t" $2+600 "\t" $1"_"$2}' | grep -v "\-200" > Markers.bed

# Make a fasta of the marker regions, named by the marker from the linkage map
bedtools getfasta -fi ncbi_genome_renamed.fa -bed Markers.bed -nameOnly > Marker_Regions.fasta
```

---

## 5.3) Map the marker regions to the PacBio contigs

```sh
mkdir -p ~/Kohalensis_Genome/04_Scaffold_Contigs/03_Map_Markers_to_PacBio
cd ~/Kohalensis_Genome/04_Scaffold_Contigs/03_Map_Markers_to_PacBio

ln -s ~/Kohalensis_Genome/03_Purge_Duplicates/Kohalensis.purged.fa .
ln -s ~/Kohalensis_Genome/04_Scaffold_Contigs/02_Marker_Prep/Marker_Regions.fasta .

# Align the marker regions to the build
/programs/minimap2-2.24/minimap2 -t 90 -x asm5 Kohalensis.purged.fa Marker_Regions.fasta -o markers_to_purged.PAF

# Keep markers with >=60% of their 800 bp window matching. This threshold was checked:
# markers above 60% mapped to only a single PacBio contig, so the placement is unambiguous.
echo "Marker    PacBio_Contig   PacBio_Position %_Match" > Markers_Above_60_Match.tsv
awk '{print $1 "\t" $6 "\t" $8 "\t" ($10/800)*100}' markers_to_purged.PAF | awk '($4 >= 60)' >> Markers_Above_60_Match.tsv
```

---

## 5.4) Build per-chromosome maps

```sh
mkdir -p ~/Kohalensis_Genome/04_Scaffold_Contigs/04_Update_Maps
cd ~/Kohalensis_Genome/04_Scaffold_Contigs/04_Update_Maps

ln -s ../02_Marker_Prep/Linkage_Map.txt .
ln -s ../03_Map_Markers_to_PacBio/Markers_Above_60_Match.tsv .

# Identify which markers are being dropped
tail -n +2 Markers_Above_60_Match.tsv | awk '{print $1}' - > Good_markers.txt
tail -n +2 Linkage_Map.txt | awk '{print $1}' - > All_markers.txt
diff Good_markers.txt All_markers.txt
```

Markers dropped for failing the 60% threshold:

```txt
S002151
S003735_239754
S002034_37583
S000552_512848
S001954_7309
S002327_67820
S006400_232463
S002794_876748
S003307_279141
S001539_17190
```

```sh
# Remove the dropped markers, prefix chromosome numbers with "chr", and strip the header
grep -v "202.7001" Linkage_Map.txt | \
	grep -v "S003735_239754" | \
	grep -v "S002034_37583" | \
	grep -v "S000552_512848" | \
	grep -v "S001954_7309" | \
	grep -v "S002327_67820" | \
	grep -v "S006400_232463" | \
	grep -v "S002794_876748" | \
	grep -v "S003307_279141" | \
	grep -v "S001539_17190" | \
	awk '{print $1 "\t" "chr"$2 "\t" $3}' - | \
	tail -n+2 > Linkage_Map.chr.txt

# Make individual genetic map files for each chromosome
for CHROM in chr1 chr2 chr3 chr4 chr5 chr6 chr7 chrX
do
	mkdir $CHROM
	grep "$CHROM" Linkage_Map.chr.txt > $CHROM\/$CHROM.map
done

# For each marker (in genetic map order), record the best-matching PacBio contig
for CHROM in chr1 chr2 chr3 chr4 chr5 chr6 chr7 chrX
do
	cd $CHROM
	while IFS=$'\t' read -r word _; do
    	grep -m 1 -wF "$word" ../Markers_Above_60_Match.tsv
	done < $CHROM.map  | awk '!x[$1]++' - > $CHROM.marked
	cd ..
done

# Combine map position with PacBio contig position
for CHROM in chr1 chr2 chr3 chr4 chr5 chr6 chr7 chrX
do
	cd $CHROM
	echo -e 'PacBio_Contig\tPacBioPosition\tMarker\t%_Marker_Mapped\tMapPosition' > $CHROM.info
	paste $CHROM.marked $CHROM.map | awk '{print $2 "\t" $3 "\t" $1 "\t" $4 "\t" $7}' >> $CHROM.info
	cd ..
done
```

> [!NOTE]
> The `grep -v "202.7001"` above is what actually removes the first dropped marker
> (`S002151`) from `Linkage_Map.txt`, matching on its map position rather than its marker
> ID. It is preserved here exactly as run. See [README.md](README.md) — this is worth
> double-checking before publication, as it is the one filter whose pattern does not name
> the marker it removes.

### Verification — is any contig assigned to more than one chromosome?

```sh
for CHROM in chr1 chr2 chr3 chr4 chr5 chr6 chr7 chrX
do
	awk '{print $2}' $CHROM/$CHROM.marked | sort | uniq > $CHROM/$CHROM.contigs
done
sort */*.contigs | uniq -d
```

**Result:** yes — `ptg000005l_1`.

```sh
grep "ptg000005l_1" */*.contigs
# chr2, chr6
```

This is the signature of a misjoined contig: one contig carrying markers from two
different linkage groups. Rather than assign it arbitrarily, the HiFi read alignments
across the contig were inspected directly in IGV to find the join point.

```sh
# Generate a smaller bam and manually inspect the region locally in IGV
cd ~/Kohalensis_Genome/03_Purge_Duplicates
samtools view -h -q 40 -@ 90 -b -o Kohalensis.to.purged_ptg00005l.bam Kohalensis.to.purged.bam ptg000005l_1
```

**Result:** `ptg000005l_1` should be broken at position **11,965,000**. This break is
applied in 5.6 below.

---

## 5.5) How much sequence is captured by the scaffolds?

```sh
cd ~/Kohalensis_Genome/04_Scaffold_Contigs/04_Update_Maps

# List all contigs being scaffolded
cat chr*/ch*.contigs | sort | uniq > scaffed_contigs.txt

# List all contigs
grep ">" ../03_Map_Markers_to_PacBio/Kohalensis.purged.fa | sed 's/>//' | sort > all_contigs.txt

# Find contigs that are not being scaffolded
comm -23 all_contigs.txt scaffed_contigs.txt > unscaffed_contigs.txt

# Make a fasta of the unscaffolded contigs and total their length
bioawk -cfastx 'BEGIN{while((getline k <"unscaffed_contigs.txt")>0)i[k]=1}{if(i[$name])print ">"$name"\n"$seq}' ../03_Map_Markers_to_PacBio/Kohalensis.purged.fa > unscaffed_contigs.fa
bioawk -c fastx '{ print $name, length($seq) }' unscaffed_contigs.fa | awk '{sum+=$2;} END{print sum;}'

# Make a fasta of the scaffolded contigs
bioawk -cfastx 'BEGIN{while((getline k <"scaffed_contigs.txt")>0)i[k]=1}{if(i[$name])print ">"$name"\n"$seq}' ../03_Map_Markers_to_PacBio/Kohalensis.purged.fa > scaffed_contigs.fa
```

**Result:** 38 contigs remain unscaffolded, totalling 61,689,142 bp (3.71% of the genome).

---

## 5.6) Generate the AGP and assemble the scaffolds

The contig order and orientation per chromosome were determined by walking the marker
order along each linkage group, and were reviewed manually against the map.

```sh
mkdir -p ~/Kohalensis_Genome/04_Scaffold_Contigs/05_Generate_AGP
cd ~/Kohalensis_Genome/04_Scaffold_Contigs/05_Generate_AGP

export PATH=~/Programs/agptools:$PATH

# Stage the Inspector-corrected contigs (see 04_Correct_Contigs.md)
cp ~/Kohalensis_Genome/Cleaned_Contigs_Inspector/contig_corrected.fa Kohalensis.contig_corrected.fa

# Generate an agp file from the fasta for easier manipulation
python ../../scripts/fasta_to_agp.py Kohalensis.contig_corrected.fa Kohalensis.contig_corrected.agp

# Break ptg000005l_1 at position 11965000 (see 5.4 verification)
agptools split ../../data/splits.txt Kohalensis.contig_corrected.agp > Kohalensis.contig_corrected.broken_contig5.agp

# Create a full agp with the joins
agptools join ../../data/joins.txt Kohalensis.contig_corrected.broken_contig5.agp > Kohalensis.contig_corrected.manual.agp

# Order so the chromosome scaffolds come first
sort -k1,1 -k2,2n Kohalensis.contig_corrected.manual.agp > Kohalensis.contig_corrected.manual.chr_first.agp

# Generate the fasta of the new scaffolds
agptools assemble Kohalensis.contig_corrected.fa Kohalensis.contig_corrected.manual.chr_first.agp > Kohalensis_corrected_man_scaffolds.fa
```

The contig order/orientation per chromosome is in [data/joins.txt](data/joins.txt); the
contig break is in [data/splits.txt](data/splits.txt). Note that in `joins.txt` the two
halves of the broken contig appear as `ptg000005l_1.1` (chr2) and `ptg000005l_1.2` (chr6),
which are the fragment names `agptools split` produces.

---

## 5.7) Locate the old NCBI contigs in the new assembly

Produces a translation table between the published NCBI assembly and this build, for
anyone carrying coordinates across.

```sh
mkdir -p ~/Kohalensis_Genome/04_Scaffold_Contigs/06_Locate_Old_Contigs
cd ~/Kohalensis_Genome/04_Scaffold_Contigs/06_Locate_Old_Contigs

# Link to the renamed ncbi genome, the final scaffolded build, and the contigs used
ln -s ~/Kohalensis_Genome/04_Scaffold_Contigs/01_ncbi_genome_prep/ncbi_genome_renamed.fa .
ln -s ~/Kohalensis_Genome/04_Scaffold_Contigs/05_Generate_AGP/Kohalensis_corrected_man_scaffolds.fa .
ln -s ~/Kohalensis_Genome/04_Scaffold_Contigs/05_Generate_AGP/Kohalensis.contig_corrected.fa .

# Align ncbi to the new scaffolded build
/programs/minimap2-2.24/minimap2 -t 90 -x asm5 Kohalensis_corrected_man_scaffolds.fa ncbi_genome_renamed.fa -o ncbi_to_Kohalensis_v2.PAF
# Align ncbi to the new contigs
/programs/minimap2-2.24/minimap2 -t 90 -x asm5 Kohalensis.contig_corrected.fa ncbi_genome_renamed.fa -o ncbi_to_Kohalensis_PacBio_CONTIGS.PAF

# Find the longest alignment for each of the old contigs, against the contigs
python ../../scripts/summarize_longest_paf_hit.py ncbi_to_Kohalensis_PacBio_CONTIGS.PAF
mv Contigs_BEST_LongestAln.tsv Contigs_BEST_LongestAln_TO_CONTIGS.tsv

# Find the longest alignment for each of the old contigs, against the new scaffolds
python ../../scripts/summarize_longest_paf_hit.py ncbi_to_Kohalensis_v2.PAF
mv Contigs_BEST_LongestAln.tsv Contigs_BEST_LongestAln_TO_V2.tsv
```

---

**Next step:** [06_Update_Gff.md](06_Update_Gff.md)
