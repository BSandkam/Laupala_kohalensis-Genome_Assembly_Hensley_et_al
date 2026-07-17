#!/usr/bin/env python3
"""Lift GFF features from contig coordinates to scaffold coordinates using an AGP.

Written because RagTag's liftover does not handle a contig that has been broken during
scaffolding, which is the case here (ptg000005l_1 is split). Features are mapped onto the
correct contig fragment and clipped to that fragment's bounds; fragments placed in '-'
orientation have their coordinates and strand reversed.
"""

import sys
import csv
from collections import defaultdict

def parse_agp(agp_file):
    agp_map = defaultdict(list)
    with open(agp_file) as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                continue
            parts = line.strip().split("\t")
            if parts[4] != "W":
                continue  # skip gaps
            scaffold, s_start, s_end, part_number, type_, contig, c_start, c_end, strand = parts
            agp_map[contig].append({
                "scaffold": scaffold,
                "s_start": int(s_start),
                "s_end": int(s_end),
                "c_start": int(c_start),
                "c_end": int(c_end),
                "strand": strand
            })
    return agp_map

def lift_feature(contig, start, end, strand, agp_entries):
    lifted = []
    for entry in agp_entries:
        # Only keep features within this fragment of the contig
        if end < entry["c_start"] or start > entry["c_end"]:
            continue
        # Clip to bounds of fragment
        frag_start = max(start, entry["c_start"])
        frag_end = min(end, entry["c_end"])
        offset = frag_start - entry["c_start"]
        length = frag_end - frag_start + 1
        if entry["strand"] == "+":
            s_start = entry["s_start"] + offset
            s_end = s_start + length - 1
            new_strand = strand
        else:
            s_end = entry["s_end"] - offset
            s_start = s_end - length + 1
            new_strand = "-" if strand == "+" else "+" if strand == "-" else strand
        lifted.append((entry["scaffold"], s_start, s_end, new_strand))
    return lifted

def liftover_gff(agp_map, gff_file, output_file):
    with open(gff_file) as infile, open(output_file, "w") as out:
        for line in infile:
            if line.startswith("#") or line.strip() == "":
                out.write(line)
                continue
            parts = line.strip().split("\t")
            seqid, source, feature_type, start, end, score, strand, phase, attributes = parts
            start, end = int(start), int(end)
            if seqid not in agp_map:
                # Not scaffolded? Output as-is
                out.write(line)
                continue
            lifted_coords = lift_feature(seqid, start, end, strand, agp_map[seqid])
            for scaffold, new_start, new_end, new_strand in lifted_coords:
                new_parts = [
                    scaffold, source, feature_type,
                    str(new_start), str(new_end), score,
                    new_strand, phase, attributes
                ]
                out.write("\t".join(new_parts) + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python agp_liftover_gff.py <input.agp> <input.gff> <output.gff>")
        sys.exit(1)
    agp_file = sys.argv[1]
    gff_file = sys.argv[2]
    output_file = sys.argv[3]

    agp_map = parse_agp(agp_file)
    liftover_gff(agp_map, gff_file, output_file)
