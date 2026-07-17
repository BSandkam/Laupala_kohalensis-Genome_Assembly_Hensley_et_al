#!/usr/bin/env python3
"""Generate a trivial AGP (one contig = one component) from a fasta.

Used to get the contig set into AGP form so agptools can split/join/assemble it.
"""

from Bio import SeqIO
import sys

def fasta_to_agp(fasta_path, agp_path):
    with open(agp_path, 'w') as out:
        out.write("##agp-version 2.1\n")
        for record in SeqIO.parse(fasta_path, "fasta"):
            length = len(record.seq)
            out.write(f"{record.id}\t1\t{length}\t1\tW\t{record.id}\t1\t{length}\t+\n")

if __name__ == "__main__":
    fasta_to_agp(sys.argv[1], sys.argv[2])
