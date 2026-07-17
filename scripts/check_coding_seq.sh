#!/bin/bash
# Assess coding potential of the lifted transcripts with TransDecoder, retaining ORFs
# with DIAMOND (protein homology) or Pfam (domain) support.
set -euo pipefail

# Input
FA=Kohalensis.SCAFFOLDS.transcripts.sorted.fa
BLAST_DB=~/Databases/UniRef90_07-30-2025/uniref90_no_transposase.fasta
PFAM_DB=~/Databases/Pfam-A/Pfam-A.hmm

# Threads
THREADS=90

###############################################
# 1. Find long ORFs
###############################################
TransDecoder.LongOrfs -t "$FA"

###############################################
# 2. Homology search (multi-threaded)
###############################################
# DIAMOND was used in place of BLASTP for speed.
# diamond makedb --in "$BLAST_DB" -d blastdb
/programs/diamond/diamond blastp \
    -q ${FA}.transdecoder_dir/longest_orfs.pep \
    -d ${BLAST_DB} \
    -o blastp.outfmt6 \
    -k 1 \
    --very-sensitive \
    -e 1e-5 \
    -p $THREADS

# Pfam search with HMMER
/programs/hmmer-3.4/bin/hmmscan \
    --cpu $THREADS \
    --domtblout pfam.domtblout \
    "$PFAM_DB" \
    ${FA}.transdecoder_dir/longest_orfs.pep \
    > pfam.log

###############################################
# 3. Predict coding regions using all evidence
###############################################
/programs/TransDecoder-5.5.0/TransDecoder.Predict \
    -t "$FA" \
    --retain_pfam_hits pfam.domtblout \
    --retain_blastp_hits blastp.outfmt6 \
    --cpu $THREADS

###############################################
# 4. Quick QC
###############################################
grep -c "type:complete" ${FA}.transdecoder.gff3
grep -c "type:internal" ${FA}.transdecoder.gff3
grep -c "type:5prime_partial" ${FA}.transdecoder.gff3
grep -c "type:3prime_partial" ${FA}.transdecoder.gff3
