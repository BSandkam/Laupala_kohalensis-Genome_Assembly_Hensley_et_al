# Annotation 04) Functional annotation

**Goal:** Attach functional information — protein domains, GO terms, orthology, and putative
gene names — to the predicted gene set.

**Rationale:** Three complementary sources are combined: InterProScan (domain/GO from member
databases), eggNOG-mapper (orthology-based GO and descriptions), and reciprocal-best-hit
BLAST against the well-annotated *Drosophila melanogaster* proteome (for gene names). AGAT
then integrates all three onto the gene models.

**Input:** `braker_combined_aa.fasta` and `braker_combined.gff` from
[03_BRAKER3_and_TSEBRA.md](03_BRAKER3_and_TSEBRA.md)
**Output:** `Lkohalensis_braker_combined.emapper.decorated.gff` (input to
[../06_Update_Gff.md](../06_Update_Gff.md)) and the fully integrated annotation

---

## 4.1) InterProScan

```sh
./interproscan-5.71-102.0/interproscan.sh \
  -b Kohalensis_braker_combined \
  -f TSV,XML,GFF3 \
  -i ~/genome_finalize/annotation/braker/braker_combined_aa.fasta \
  --goterms --pathways --disable-precalc \
  -t p -T ./
```

## 4.2) eggNOG-mapper

```sh
export PYTHONPATH=/programs/eggnog-mapper-2.1.12/lib64/python3.9/site-packages:/programs/eggnog-mapper-2.1.12/lib/python3.9/site-packages
export PATH=/programs/eggnog-mapper-2.1.12/bin:$PATH

download_eggnog_data.py -M --dbname 'Insecta' --data_dir ~/genome_finalize/annotation/eggnogg/database
create_dbs.py -m diamond --dbname insecta --taxa Insecta --data_dir ./database
create_dbs.py -m mmseqs --dbname mmseqs_insecta --taxa Insecta --data_dir ./database

emapper.py \
  --cpu 40 -m mmseqs \
  -i ~/genome_finalize/annotation/braker/braker_combined_aa.fasta \
  -d ~/genome_finalize/annotation/eggnogg/database/mmseqs_insecta.mmseqs \
  --report_orthologs --report_no_hits \
  --go_evidence non-electronic \
  --decorate_gff ~/genome_finalize/annotation/braker/braker_combined.gff \
  --data_dir ~/genome_finalize/annotation/eggnogg/database \
  -o Lkohalensis_braker_combined \
  --allow_overlaps strand --dbmem
```

Produces `Lkohalensis_braker_combined.emapper.decorated.gff`.

## 4.3) Reciprocal BLAST against the *Drosophila* proteome

```sh
makeblastdb \
  -in ../eggnogg/database/uniprotkb_proteome_UP000000803_2025_05_23.fasta \
  -dbtype prot -out drosophila_db

blastp -db drosophila_db \
  -query ../braker/braker_combined_aa.fasta \
  -outfmt 6 -evalue 1e-6 -max_target_seqs 10 \
  -out forward_lkoh_to_dmel.out -num_threads 20
```

The forward and reverse BLAST are reduced to reciprocal-best-hits
(`filtered_query_RBH.outfmt6`) used in the AGAT integration below.

## 4.4) Integrate all functional evidence with AGAT

```sh
singularity exec --bind ~/genome_finalize/ --pwd $PWD /programs/agat-1.2.0/agat.sif \
  agat_sp_manage_functional_annotation.pl \
  -f ~/genome_finalize/annotation/eggnogg/Lkohalensis_braker_combined.emapper.decorated.gff \
  -b ~/genome_finalize/annotation/reciprocal_blast/filtered_query_RBH.outfmt6 \
  -db ~/genome_finalize/annotation/eggnogg/database/uniprotkb_proteome_UP000000803_2025_05_23.fasta \
  -i ~/genome_finalize/annotation/interproscan/Kohalensis_braker_combined.tsv \
  -o Kohalensis_braker_combined_decorated_annotated \
  -idau -v
```

## 4.5) Annotation statistics

```sh
singularity exec --bind ~/genome_finalize/ --pwd $PWD /programs/agat-1.2.0/agat.sif \
  agat_sp_statistics.pl \
  -gff ~/genome_finalize/annotation/reciprocal_blast/Kohalensis_braker_combined_decorated_annotated/Lkohalensis_braker_combined.emapper.decorated.gff \
  -g ~/genome_finalize/inspector_corrected/contig_corrected_softmasked.fasta \
  -d -o Lkohalensis_braker_combined_statistics.txt
```

---

The decorated annotation (`Lkohalensis_braker_combined.emapper.decorated.gff`) is the
annotation, in **corrected-contig coordinates**, that is lifted onto the scaffolds in
[../06_Update_Gff.md](../06_Update_Gff.md).

This is subsequently been modified manually and using the python script clean_dbxref_to_note.py to make it more user-friendly and is avaiable as `annotation_with_gene_id.gff3.zip`

**Next:** [05_Mitochondrial_and_NUMT.md](05_Mitochondrial_and_NUMT.md)
