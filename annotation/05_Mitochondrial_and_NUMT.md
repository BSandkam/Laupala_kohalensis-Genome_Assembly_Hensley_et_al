# Annotation 05) Mitochondrial genome and NUMT detection

**Goal:** Assemble and annotate the mitochondrial genome, integrate it into the assembly,
and characterise the nuclear-mitochondrial insertion (NUMT) on chromosome 7.

**Status:** The manuscript describes this work and the products exist (a circularised mtDNA
sequence and an mtDNA GFF are in the annotation repo, and BlobToolKit was run on a
`..._mtDNA.fa` assembly), **but the commands were not recorded in the pipeline notes.**
The steps below document what the manuscript reports so the gap is explicit; the actual
invocations need to be supplied before publication. See
[../docs/MANUSCRIPT_COVERAGE.md](../docs/MANUSCRIPT_COVERAGE.md).

---

## 5.1) Mitochondrial genome assembly — MitoHiFi

**Manuscript:** MitoHiFi (Uliano-Silva et al. 2023) was run on the raw HiFi reads to
identify and assemble the mitochondrial genome, yielding a **16,500 bp circularised**
sequence.

**Evidence in repo:** the integrated assembly used downstream is
`Kohalensis_corrected_man_scaffolds_mtDNA.fa` (referenced in the BlobToolKit step of the
annotation notes), i.e. the nuclear scaffolds with the mtDNA contig appended.

```sh
# TODO: record the exact MitoHiFi command (reference/closest species, -r reads, etc.).
```

## 5.2) Mitochondrial annotation — MITOS2 / MFannot / EZmito2

**Manuscript:** the mtDNA was annotated with MITOS2 (Donath et al. 2019; Al Arab et al.
2017) and MFannot (Lang et al. 2023) via the Galaxy platform (Galaxy Community 2024), with
visualisation via EZmito2 (Cucini et al. 2021).

**Evidence in repo:** `final_ACTRWJ_Kohalensis_corrected_man_scaffolds_mtDNA.gff` (the
mitochondrial annotation, present as a zipped GFF in the annotation repo).

These were run through the **Galaxy web platform**, so there may be no command line to
record — in that case, document the Galaxy workflow/tool versions and parameters instead.

```text
# TODO: record MITOS2 / MFannot Galaxy tool versions and parameter settings, and the
# GenBank-to-GFF3 conversion step referenced in the annotation README.
```

## 5.3) NUMT detection

**Manuscript:** a **13,921 bp** nuclear-mitochondrial insertion (NUMT) on **chromosome 7**
was detected by aligning the mitochondrial sequence to the nuclear genome with minimap2
(Li 2018, 2021), and confirmed with mosdepth (Pedersen & Quinlan 2018) over
bedtools-generated sliding windows (a coverage-based check that the region is nuclear, not
a second copy of the true mitochondrion).

**Not yet in repo.** The tools are standard; the commands should be reconstructable but are
not recorded, so they are left as a TODO rather than guessed at.

```sh
# TODO: record the minimap2 alignment of mtDNA -> nuclear genome, the bedtools makewindows
# call, and the mosdepth command used to confirm the chr7 NUMT.
```

---

## What is well-documented vs what needs filling in

| Sub-step | Product exists? | Commands recorded? |
|----------|:---:|:---:|
| MitoHiFi assembly | ✅ (`..._mtDNA.fa`) | ❌ |
| MITOS2 / MFannot annotation | ✅ (`..._mtDNA.gff`) | ❌ (Galaxy — capture versions/params) |
| NUMT detection | ⚠️ described only | ❌ |

Filling these three in completes the manuscript-to-repo coverage; everything else the
manuscript describes is now documented.
