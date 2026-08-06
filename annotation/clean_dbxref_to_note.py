#!/usr/bin/env python3
"""
Clean GFF3 Dbxref= fields against NCBI's allowed /db_xref database list.

- Keeps Dbxref entries whose DB prefix is in the allowed list.
- Moves invalid Dbxref entries to Note= (preserving the original "DB:ID" strings).
- Preserves other attributes.
- Writes a TSV report of moved dbxrefs.

NCBI allowed list source:
https://www.ncbi.nlm.nih.gov/genbank/collab/db_xref/
(case-sensitive)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen


NCBI_DBXREF_URL = "https://www.ncbi.nlm.nih.gov/genbank/collab/db_xref/"

# Extract DB names from examples like: /db_xref="CDD:02194"
# DB names can include characters like / (e.g., AceView/WormGenes) and parentheses.
DBNAME_RE = re.compile(r'db_xref="([^":]+):')


def fetch_allowed_db_names(url: str = NCBI_DBXREF_URL, timeout: int = 30) -> set[str]:
    with urlopen(url, timeout=timeout) as r:
        html = r.read().decode("utf-8", errors="replace")
    dbs = set(DBNAME_RE.findall(html))
    if not dbs:
        raise RuntimeError(
            "Failed to parse any db_xref database names from NCBI page. "
            "NCBI page structure may have changed."
        )
    return dbs


def parse_attrs(attr_field: str) -> List[Tuple[str, str]]:
    """
    Parse GFF3 9th column into ordered (key, value) pairs.
    Minimal parser: splits on ';' and first '='.
    Keeps unknown/unkeyed pieces as key='' to preserve if present.
    """
    parts = attr_field.strip()
    if not parts:
        return []
    out: List[Tuple[str, str]] = []
    for item in parts.split(";"):
        if item == "":
            continue
        if "=" in item:
            k, v = item.split("=", 1)
            out.append((k, v))
        else:
            # malformed / unkeyed; preserve as-is
            out.append(("", item))
    return out


def format_attrs(pairs: List[Tuple[str, str]]) -> str:
    # Rebuild column 9. Keep unkeyed items verbatim.
    chunks = []
    for k, v in pairs:
        if k == "":
            chunks.append(v)
        else:
            chunks.append(f"{k}={v}")
    return ";".join(chunks)


def get_first(pairs: List[Tuple[str, str]], key: str) -> Optional[int]:
    for i, (k, _) in enumerate(pairs):
        if k == key:
            return i
    return None


def split_dbxref_value(v: str) -> List[str]:
    # Dbxref entries are comma-separated per NCBI genome GFF guidance
    # (and commonly produced that way).
    return [x for x in (s.strip() for s in v.split(",")) if x]


def classify_dbxref_entries(entries: List[str], allowed_db: set[str]) -> Tuple[List[str], List[str]]:
    kept: List[str] = []
    moved: List[str] = []
    for e in entries:
        # Only classify things that look like DB:ID. If malformed, treat as invalid and move to Note.
        if ":" not in e:
            moved.append(e)
            continue
        db = e.split(":", 1)[0]
        if db in allowed_db:
            kept.append(e)
        else:
            moved.append(e)
    return kept, moved


def append_to_note(existing_note: Optional[str], additions: List[str]) -> str:
    # Keep it readable and deterministic.
    # Use comma+space separation; preserve original DB:ID tokens.
    add_txt = ", ".join(additions)
    if not existing_note or existing_note.strip() == "":
        return add_txt
    # Avoid duplicating separators if note already ends with punctuation
    if existing_note.endswith((";", ",", " ")):
        return existing_note + add_txt
    return existing_note + "; " + add_txt


@dataclass
class MoveRecord:
    seqid: str
    ftype: str
    line_no: int
    moved: List[str]


def process_gff(
    in_path: str,
    out_path: str,
    report_path: str,
    allowed_db: set[str],
    dbxref_key: str = "Dbxref",
    note_key: str = "Note",
) -> None:
    moved_records: List[MoveRecord] = []
    total_dbxref_entries = 0
    moved_entries = 0

    with open(in_path, "r", encoding="utf-8", errors="replace") as fin, open(
        out_path, "w", encoding="utf-8"
    ) as fout:
        for line_no, line in enumerate(fin, 1):
            if not line.strip() or line.startswith("#"):
                fout.write(line)
                continue

            cols = line.rstrip("\n").split("\t")
            if len(cols) != 9:
                fout.write(line)
                continue

            seqid, source, ftype, start, end, score, strand, phase, attrs = cols

            pairs = parse_attrs(attrs)

            idx = get_first(pairs, dbxref_key)
            if idx is None:
                fout.write(line)
                continue

            k, v = pairs[idx]
            entries = split_dbxref_value(v)
            total_dbxref_entries += len(entries)

            kept, moved = classify_dbxref_entries(entries, allowed_db)
            moved_entries += len(moved)

            # Update Dbxref
            if kept:
                pairs[idx] = (dbxref_key, ",".join(kept))
            else:
                # remove Dbxref key entirely
                pairs.pop(idx)

            # Move invalid to Note
            if moved:
                note_idx = get_first(pairs, note_key)
                if note_idx is None:
                    pairs.append((note_key, ", ".join(moved)))
                else:
                    nk, nv = pairs[note_idx]
                    pairs[note_idx] = (nk, append_to_note(nv, moved))
                moved_records.append(MoveRecord(seqid=seqid, ftype=ftype, line_no=line_no, moved=moved))

            cols[8] = format_attrs(pairs)
            fout.write("\t".join(cols) + "\n")

    with open(report_path, "w", encoding="utf-8") as rep:
        rep.write("line_no\tseqid\tfeature_type\tmoved_dbxrefs\n")
        for r in moved_records:
            rep.write(f"{r.line_no}\t{r.seqid}\t{r.ftype}\t{','.join(r.moved)}\n")

    sys.stderr.write(
        f"[done] total_dbxref_entries={total_dbxref_entries} moved_entries={moved_entries} "
        f"moved_features={len(moved_records)}\n"
        f"[out]  {out_path}\n"
        f"[report] {report_path}\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True, help="Input GFF3")
    ap.add_argument("--out", dest="out_path", required=True, help="Output cleaned GFF3")
    ap.add_argument(
        "--report",
        dest="report_path",
        default="moved_dbxrefs.tsv",
        help="TSV report of moved dbxrefs (default: moved_dbxrefs.tsv)",
    )
    ap.add_argument(
        "--dbxref-key",
        default="Dbxref",
        help="Attribute key to treat as dbxref list (default: Dbxref)",
    )
    ap.add_argument(
        "--note-key",
        default="Note",
        help="Attribute key to append invalid dbxrefs to (default: Note)",
    )
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help="Do not fetch allowed list; instead read allowed DB names from stdin (one per line).",
    )
    args = ap.parse_args()

    if args.no_fetch:
        allowed = set(x.strip() for x in sys.stdin if x.strip())
        if not allowed:
            raise SystemExit("No allowed DB names provided on stdin.")
    else:
        allowed = fetch_allowed_db_names()

    process_gff(
        in_path=args.in_path,
        out_path=args.out_path,
        report_path=args.report_path,
        allowed_db=allowed,
        dbxref_key=args.dbxref_key,
        note_key=args.note_key,
    )


if __name__ == "__main__":
    main()