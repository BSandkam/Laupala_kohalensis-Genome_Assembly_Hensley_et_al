#!/usr/bin/env python3
"""Report the single longest alignment for each query sequence in a PAF.

Used to locate each contig of the old NCBI assembly in the new build.
Writes Contigs_BEST_LongestAln.tsv to the working directory.
"""

import sys
import pandas as pd

# Check for input file
if len(sys.argv) < 2:
    print("Usage: python summarize_longest_paf_hit.py <input.paf>")
    sys.exit(1)

# Read input PAF file (first 12 columns only)
input_file = sys.argv[1]
df = pd.read_csv(input_file, header=None, sep='\t', usecols=range(12))

# Name PAF columns
df.columns = [
    "old_Contig",       # Query sequence name
    "QueryLength",      # Query sequence length
    "QueryStart",       # Query start (0-based)
    "QueryEnd",         # Query end (0-based, exclusive)
    "strand",           # Strand ('+' or '-')
    "PacBio_Contig",    # Target sequence name (new assembly)
    "RefLength",        # Target sequence length
    "RefStart",         # Target start on ref (0-based)
    "RefEnd",           # Target end on ref (0-based, exclusive)
    "Matches",          # Number of matching bases
    "AlignmentLength",  # Alignment block length
    "MapQuality"        # Mapping quality (0-255)
]

# Get longest alignment for each old_Contig
longest_hits = df.loc[df.groupby("old_Contig")["AlignmentLength"].idxmax()]

# Compute percent of query covered
longest_hits["Percent_of_Query"] = (longest_hits["AlignmentLength"] / longest_hits["QueryLength"] * 100).round(2)

# Output file
output_file = "Contigs_BEST_LongestAln.tsv"
longest_hits.to_csv(output_file, sep="\t", index=False)

print(f"Saved best alignment per contig to: {output_file}")
