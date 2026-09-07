# Rivanna Storage Options

A reference for the storage locations available to Dremel Lab members on UVA's Rivanna HPC, when to use each one, real measured I/O performance, and the scripts we run to keep `/scratch` clean and to track how full each location is.

> **Status:** Work in progress — this guide will be revised as we gather more data and scripts. Feedback welcome.

## Overview

Rivanna exposes several distinct storage locations, each with different quotas, sharing rules, snapshot policies, and (critically) very different I/O performance. Picking the wrong one for a workload is a common source of "why is this pipeline so slow" reports — see [Key Points](#key-points) below.

## Storage Locations

| Storage Location | Size/Quota   | Shareable | Snapshots     | Automatic Purge                    | Recommended Use            |
| ----------------- | ------------ | --------- | ------------- | ----------------------------------- | --------------------------- |
| `/home`            | 200 GB       | No        | Daily, 1 week | No                                  | Code, scripts, documents    |
| `/scratch`         | 10 TB        | No        | None          | Files inactive for 90 days deleted  | Active HPC computations     |
| `/project`         | 1 TB+ leased | Yes       | Daily, 1 week | No                                  | Shared HPC project data     |
| `/standard`        | 1 TB+ leased | Yes       | None          | No                                  | Long term research storage  |

Dremel Lab's shared paths follow this pattern:
- `/project/dremel_lab` — shared, fast, used for active pipeline I/O and shared tooling (e.g. `/project/dremel_lab/scripts`)
- `/standard/dremel_lab` — shared, slow, used for long-term archival of raw data and finished results
- `/scratch/<username>` — per-user scratch for transient pipeline working directories

## Pipeline Data Workflow

Given the quota/sharing/performance tradeoffs above, Dremel Lab pipelines (HAROLD, Chroma2, etc.) follow a consistent storage pattern rather than reading/writing any one location for everything:

```
/standard/dremel_lab        /project/dremel_lab
  (raw FASTQs, archival)      (pipelines, reference genomes/indices — shared, fast)
        │                              │
        │ Globus transfer              │ used throughout
        ▼                              ▼
  /scratch/<user>  ◄── manifest points here ──► pipeline run (workdir on scratch)
        │
        │ on completion
        ▼
       S3  (final results — hot/cold tiers)
```

1. **Raw FASTQs live on `/standard`** — write-once, read-rarely archival storage; this is where sequencing data lands and stays long-term.
2. **Pipeline code and references live on `/project`** — Snakemake/Nextflow pipelines, conda/mamba envs, reference genomes and indices are shared, need fast I/O, and are reused across many runs, so they belong on `/project`, not `/standard`.
3. **Before a run, FASTQs are Globus-transferred from `/standard` to `/scratch/<user>`** — this makes a fast working copy so the pipeline never has to read raw input at `/standard` speeds (see [I/O Performance](#io-performance-standard-vs-project) below).
4. **The sample manifest/samplesheet points at the `/scratch` copy**, not the `/standard` original — this is what actually puts the pipeline on the fast path; a manifest still pointing at `/standard` paths would silently reintroduce the 15-20x slowdown.
5. **The pipeline's working directory (`WORKDIR`, intermediate/temp files) is also on `/scratch`** — `/scratch` has the room (10 TB) and speed for heavy read/write during a run, and its 90-day auto-purge plus [`cleanup_uuid_dir`](#scratch-cleanup) keep it from filling up with stale run artifacts.
6. **On completion, final results are transferred to S3**, not back to `/standard` — see the S3 hot/cold storage strategy ([seqinfomics_eln#88](https://github.com/dremellab/seqinfomics_eln/issues/88)) and per-pipeline S3 deposit work ([HAROLD#44](https://github.com/dremellab/HAROLD/issues/44), [chroma2#15](https://github.com/dremellab/chroma2/issues/15)). This keeps finished outputs off Rivanna's leased/quota'd storage entirely.

**Why not run pipelines directly off `/standard` or `/project`?** `/standard` is far too slow for active I/O (see below). `/project` is shared and leased (limited, costs money to expand) — it's kept for code and references, not bulk per-run working data, so heavy pipeline I/O doesn't compete with everyone else's shared tooling or eat into the lease.

## I/O Performance: `/standard` vs `/project`

We benchmarked `/standard` against `/project` (and `$HOME` as a baseline) after noticing pipelines and even `conda env list` hanging when reading/writing under `/standard`. Full write-up: [seqinfomics_eln#41 — Slowness in loading conda env](https://github.com/dremellab/seqinfomics_eln/issues/41).

Test: `dd` with `bs=1G count=1` and `oflag=direct`/`iflag=direct` (bypasses page cache, so this reflects real filesystem throughput).

| Operation | Path                    | Time (s) | Speed     |
| --------- | ------------------------ | -------- | --------- |
| Write     | `/standard/dremel_lab/`  | 12.2573  | 87.6 MB/s |
| Write     | `/project/dremel_lab/`   | 0.5856   | 1.8 GB/s  |
| Write     | `$HOME/`                 | 0.8339   | 1.3 GB/s  |
| Read      | `/standard/dremel_lab/`  | 15.0694  | 71.3 MB/s |
| Read      | `/project/dremel_lab/`   | 0.8339   | 1.3 GB/s  |
| Read      | `$HOME/`                 | 0.8784   | 1.2 GB/s  |

**Takeaway:** `/standard` is roughly **15-20x slower** than `/project` or `$HOME` for both reads and writes. This makes sense given `/standard` isn't designed for active I/O (no snapshots either — see table above), but it means:
- Never point active pipeline `WORKDIR`/temp directories at `/standard`
- Never run tools (e.g. `conda`/`mamba` envs) directly out of `/standard`
- Use `/standard` only for data that is written once and read rarely (long-term archival)
- Stage data to `/project` or `/scratch` before compute-heavy read/write steps, then move final results back to `/standard` for archival

## Scratch Cleanup

`/scratch` auto-purges files inactive for 90 days, but pipeline runs (Snakemake `.snakemake` work dirs, tool temp dirs, etc.) commonly leave behind UUID-named temp directories well before that. We run a scheduled cleanup script for these:

**[`cleanup_uuid_dir`](https://github.com/dremellab/scripts/blob/develop/bin/cleanup_uuid_dir)** — scans `/scratch/$USER` and `/scratch/$USER/tmpdir` for directories named as UUIDs (`^[0-9a-fA-F]{8}-...`) that are older than 10 days, reports total space that would be freed, and deletes them when run with `--delete` (dry-run by default).

**Location on Rivanna:** `/project/dremel_lab/scripts/bin/cleanup_uuid_dir`

```bash
cleanup_uuid_dir            # dry run — reports what would be deleted
cleanup_uuid_dir --delete   # actually deletes
```

Scheduled nightly via Slurm `scrontab` (see [`config/scrontab.conf`](https://github.com/dremellab/scripts/blob/develop/config/scrontab.conf)):

```
0 0 * * * /project/dremel_lab/scripts/bin/cleanup_uuid_dir --delete
```

## Storage Usage Reporting

Two companion scripts track how full each storage location is over time:

**[`storage_usage`](https://github.com/dremellab/scripts/blob/develop/bin/storage_usage)** — measures `/scratch/$USER`, `$HOME`, `/standard/dremel_lab`, and `/project/dremel_lab` in parallel using [`dust`](https://github.com/bootandy/dust) (run `nice`/`ionice`'d so it doesn't hog I/O), and appends a timestamped row per location to `$HOME/storage_usage.tsv`. Falls back to the last cached measurement for a location if a scan times out (default 600s) or fails, so the log always has a value even when a directory is too large to fully walk in time.

**Location on Rivanna:** `/project/dremel_lab/scripts/bin/storage_usage`

Run nightly via `scrontab`:
```
0 1 * * * /project/dremel_lab/scripts/bin/storage_usage
```

**[`storage_usage_report`](https://github.com/dremellab/scripts/blob/develop/bin/storage_usage_report)** — reads `storage_usage.tsv` and prints a colorized table of the latest measurement for a given day (defaults to today), color-coding `NA`/failed measurements and marking cached (stale) values distinctly from live ones.

**Location on Rivanna:** `/project/dremel_lab/scripts/bin/storage_usage_report`

```bash
storage_usage_report                        # today's snapshot, from $HOME/storage_usage.tsv
TARGET_DATE=2026-09-01 storage_usage_report  # a specific date
```

**Example output:**

```
Authorized Use Only!
Welcome to UVA_HPC
Storage Usage Snapshot 2026-09-07 01:00:15
+----------+--------------------------+--------------+-------+--------+
| Location | Path                     | Bytes        | TB    | Source |
+----------+--------------------------+--------------+-------+--------+
| scratch  | /scratch/cud2td          | 9940442107904| 9.940 | live   |
| home     | /home/cud2td             |   34784303616| 0.035 | live   |
| standard | /standard/dremel_lab     | 6180420809216| 6.180 | live   |
| project  | /project/dremel_lab      | 9702184099328| 9.702 | live   |
+----------+--------------------------+--------------+-------+--------+
```

In a terminal, each `Location` row is color-coded (scratch/home/standard/project), and the `Bytes`/`TB`/`Source` columns are colored green for a live measurement, yellow for a cached (stale) fallback, and red for `NA`/failed — so a scan at a glance shows which locations are running low on quota and whether the numbers are fresh.

All three scripts live under `/project/dremel_lab/scripts/bin` on Rivanna, and are made available on `$PATH` to every `dremel_lab` group member who sources `.sh_common` in their `~/.bashrc`:

```bash
source /project/dremel_lab/scripts/.sh_common
```

(see the [scripts repo README](https://github.com/dremellab/scripts/blob/develop/README.md)) — once sourced, you can just run `cleanup_uuid_dir`, `storage_usage`, or `storage_usage_report` from anywhere without the full path.

## Key Points

- `/standard` is 15-20x slower than `/project` or `$HOME` for I/O — archival only, never active compute
- `/project` is the workhorse for shared, active pipeline I/O and shared tooling
- `/scratch` auto-purges after 90 days, but `cleanup_uuid_dir` proactively removes stale pipeline temp dirs after 10 days
- `storage_usage` + `storage_usage_report` give a daily, per-location usage snapshot — check before a large job to avoid quota surprises
