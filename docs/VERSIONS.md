# Software versions

Versions used in the *L. kohalensis* assembly and annotation. These were determined by
inspecting the tools on the Cornell BioHPC server (`cbsusandkam`) where the work ran —
directory names, git tags/commit dates of locally-built tools, and the version strings
recorded in the actual run outputs (e.g. BUSCO writes its version into every summary).

**Why this needs care:** BioHPC updates the tools on the default `$PATH`, so a bare command
today (`samtools`, `bedtools`, `blastn`) does *not* necessarily resolve to the version that
ran in 2023–2024. Where the pipeline called an **explicit versioned path** (e.g.
`/programs/minimap2-2.24/minimap2`) the version is certain. Where it called a **bare
command**, the run-time version is inferred and flagged below.

## Confidence key

- **certain** — version is pinned by an explicit path in the command, or read directly from
  the run's own output.
- **strong** — only one installed version matches the run date and provenance.
- **inferred** — bare command; version is the best estimate for the run date, needs a
  glance to confirm.

---

## Assembly pipeline (steps 01–06)

| Tool | Version | Confidence | Basis |
|------|---------|:---:|-------|
| hifiasm | **0.19.8-r603** | strong | Your `hifiasm.0.19.8` build (compiled 2023-11-24); latest release tag before the 2023-12-19 run. The notes' "v0.7" is the test-data URL tag, not the assembler. |
| jellyfish | 2.3.0 | certain | explicit path `/programs/jellyfish-2.3.0` |
| GenomeScope | 2.0 | certain | your `genomescope2.0` build |
| minimap2 | 2.24 | certain | explicit path `/programs/minimap2-2.24` (assembly steps) |
| samtools | 1.19 | strong | your `samtools-1.19` build, called explicitly for `plot-depth`; contemporaneous build for the bare `samtools` mapping calls |
| BLAST+ (blastn) | 2.x (BioHPC default, early 2024) | inferred | bare `blastn`; today resolves to `/programs/bin/blast+` |
| BlobToolKit | 2.6.3 | certain | explicit path `/programs/blobtoolkit-2.6.3` |
| BUSCO | **5.2.2** | certain | read from `short_summary.specific.insecta_odb10...txt`; lineage `insecta_odb10` (2020-09-10) |
| cdbfasta / cdbyank | (BioHPC `/programs/cdbfasta`) | certain | explicit path |
| bioawk | (BioHPC `/programs/bioawk`) | certain | explicit path |
| bedtools | 2.30.0 | inferred | bare `bedtools`; 2.30.0 was the default through this period |
| purge_dups | **1.2.6** | strong | your build, git tag `v1.2.6`, HEAD from 2022 (built 2023-04) |
| assembly-stats | (BioHPC `/programs/assembly-stats`) | certain | explicit path |
| QUAST | 5.2.0 | certain | explicit path `/programs/quast-5.2.0` |
| ncbi datasets | (BioHPC `/programs/ncbi_datasets`) | certain | explicit path |
| Inspector | **1.3.1** | certain | run from `/programs/miniconda3/envs/inspector` (`Inspector_v1.3.1`) |
| agptools | commit `de30eb3` (2024-03-06) | strong | your `agptools` clone; used mid-2025 |
| bedtools (scaffolding) | 2.30.0 | inferred | `bedtools getfasta` marker step |
| AGAT | 1.2.0 | certain | explicit `/programs/agat-1.2.0/agat.sif` |
| gffread | 0.9.12 | inferred | bare `gffread` → `/programs/bin/cufflinks/gffread` |
| seqkit | 2.x | inferred | bare `seqkit`; 2.13.0 is current, an earlier 2.x ran in 2025 |
| TransDecoder | 5.5.0 | certain | explicit path `/programs/TransDecoder-5.5.0` (assembly QC) |
| DIAMOND | (your `/local/storage/Programs/diamond`) | strong | explicit path |
| HMMER | 3.4 | certain | explicit path `/programs/hmmer-3.4` |

## Annotation pipeline (`annotation/`)

| Tool | Version | Confidence | Basis |
|------|---------|:---:|-------|
| Inspector | 1.3.1 | certain | `/programs/miniconda3/envs/inspector` |
| BUSCO (annotation) | **5.5.0** | certain | explicit `busco-5.5.0` env in notes |
| Liftoff | 1.6.3.2 | certain | explicit path `/programs/liftoff-1.6.3.2` |
| minimap2 (annotation) | 2.27 | certain | explicit path `/programs/minimap2-2.27` (Liftoff `-m`) |
| AGAT | 1.2.0 | certain | explicit `/programs/agat-1.2.0/agat.sif` |
| Nextflow | 23.10.1 | certain | explicit path `/programs/nextflow-23.10.1` |
| TAGADA | 2.1.3 | certain | `-r 2.1.3` in the nextflow call |
| TransDecoder | 5.5.0 | certain | explicit path `/programs/TransDecoder-v5.5.0` |
| Dfam TE Tools (RepeatModeler/RepeatMasker/RepeatClassifier) | `dfam/tetools:latest` | certain (tag) | `docker://dfam/tetools:latest` — **pin to a digest before publication** |
| genometools (LTRharvest/digest) | 1.5.9 | certain | explicit path `/programs/genometools-1.5.9` |
| vsearch (MITE-Tracker) | 2.23.0 | certain | explicit path `/programs/vsearch-2.23.0` |
| seqtk | (BioHPC `/programs/seqtk`) | certain | explicit path |
| usearch | 11.0.667 | certain | explicit path `/programs/usearch11.0.667` |
| BRAKER3 | `teambraker/braker3:latest` | certain (tag) | `docker://teambraker/braker3:latest` — **pin to a digest before publication** |
| Trim Galore | 0.6.10 | strong | your `TrimGalore-0.6.10` build |
| InterProScan | 5.71-102.0 | certain | explicit path in notes (`interproscan-5.71-102.0`) |
| eggNOG-mapper | 2.1.12 | certain | explicit path `/programs/eggnog-mapper-2.1.12` |
| BLAST+ (blastp, makeblastdb) | 2.x (BioHPC default, 2025) | inferred | bare commands |
| lima | 2.9.0 | certain (manuscript) | Iso-seq preprocessing — command not in repo |
| skera | 1.2.0 | certain (manuscript) | Iso-seq preprocessing — command not in repo |
| MitoHiFi | (manuscript: Uliano-Silva et al. 2023) | — | mito assembly — command not in repo |
| MITOS2 / MFannot | via Galaxy | — | mito annotation — capture Galaxy tool versions |
| mosdepth | (manuscript) | — | NUMT confirmation — command not in repo |

## Container images to pin

`dfam/tetools:latest` and `teambraker/braker3:latest` were pulled by the `:latest` tag.
For a reproducible publication, resolve each to its image **digest** (`docker inspect` /
`singularity inspect`) and record it here, since `:latest` will move.

## Two "latest" not to confuse

- `/programs/hifiasm` on the server is now **0.25.0** (rebuilt 2026-05). It is **not** what
  assembled this genome; 0.19.8 was.
