# OpenAlex CLI Reference

The OpenAlex CLI (`openalex`) is the official command-line tool for **downloading** data from OpenAlex.
It is download-only — search and filtering logic uses the same filter syntax as the API, but the CLI
applies it to select what gets downloaded.

## Table of Contents

1. [Installation](#installation)
2. [Basic Commands](#basic-commands)
3. [Download Modes](#download-modes)
4. [Filter Syntax](#filter-syntax)
5. [Content Options](#content-options)
6. [Input Modes](#input-modes)
7. [Output Structure](#output-structure)
8. [Checkpointing and Resume](#checkpointing-and-resume)
9. [Performance Tuning](#performance-tuning)
10. [S3 Storage](#s3-storage)
11. [Costs](#costs)
12. [Common Recipes](#common-recipes)

---

## Installation

The OpenAlex CLI is a standalone tool. Install in an isolated environment:

```bash
# Preferred (isolated environment, like pipx)
uv tool install git+https://github.com/ourresearch/openalex-official

# Alternative
pipx install git+https://github.com/ourresearch/openalex-official

# Fallback (pip global)
pip install git+https://github.com/ourresearch/openalex-official
```

Install from GitHub until 0.3.4 reaches PyPI. The PyPI release `openalex-official` 0.3.3
works for metadata only: since 2026-07-30 `content.openalex.org` serves files directly
(HTTP 200) instead of redirecting, and 0.3.3 fails every `--content` download with
"Unexpected status: 200". 0.3.4 (GitHub) accepts the direct response and unwraps gzipped TEI.
If 0.3.3 is already installed, reinstall with `uv tool install --force git+https://github.com/ourresearch/openalex-official`.

Verify: `openalex --help`. Note that `openalex --version` prints `0.3.2` in both 0.3.3 and
0.3.4; use `uv tool list` to see the installed release.

Note: Package was previously named `openalex-content-downloader`. If installed, uninstall and switch.

## Basic Commands

```bash
# Download metadata only (JSON files)
openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./results \
  --filter "topics.id:T10325"

# Download metadata + PDFs
openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./results \
  --filter "topics.id:T10325,has_content.pdf:true" \
  --content pdf

# Download metadata + PDFs + TEI XML
openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./results \
  --filter "topics.id:T10325,has_content.pdf:true" \
  --content pdf,xml

# Check API key status and credits
openalex status --api-key $OPENALEX_API_KEY
```

## Download Modes

### By filter (most common)
```bash
openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./results \
  --filter "publication_year:2024,type:article,is_oa:true"
```

### By specific IDs or DOIs
```bash
openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./papers \
  --ids "W2741809807,10.1038/nature12373"
```

### Random sample
```bash
openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./sample \
  --filter "publication_year:2024,type:article" \
  --sample 500 --seed 42
```

`--sample N` (1-10,000) uses the API's `sample` parameter; `--seed` makes it reproducible.
Cannot be combined with `--ids` or `--stdin`.

### By list of IDs via stdin
```bash
cat work_ids.txt | openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./papers \
  --stdin
```

This is the most useful mode for agent pipelines: search via API, collect IDs,
pipe them to the CLI for download.

## Filter Syntax

Same syntax as the API. Examples:

```bash
# Recent articles
--filter "publication_year:>2020,type:article"

# Specific topic with PDFs
--filter "topics.id:T12345,has_content.pdf:true"

# From a specific institution
--filter "authorships.institutions.id:I123456789"

# Open access with Creative Commons license
--filter "is_oa:true,best_oa_location.license:cc-by"

# Combined: 2024 OA articles with PDFs
--filter "publication_year:2024,type:article,is_oa:true,has_content.pdf:true"

# Language filter
--filter "language:pt,publication_year:>2018"

# Multiple values (OR)
--filter "language:pt|en|es,publication_year:2020-2024"
```

## Content Options

```bash
--content pdf       # Download PDFs only
--content xml       # Download TEI XML only (GROBID-parsed structured text)
--content pdf,xml   # Download both
# (omit --content)  # Metadata JSON only (~$0.10 per 1,000 list requests)
```

In filter and sample modes, `--content` makes the CLI prepend a content filter on its own:
`has_content.pdf:true` for `pdf` or `pdf,xml`, and `has_content.grobid_xml:true` for `xml`.
So `--content pdf,xml` skips works that have TEI XML but no PDF.

**TEI XML is preferred for automated processing** — it's structured text with sections,
paragraphs, references, and metadata extracted by GROBID. Much easier to parse than raw PDF.

**When to use PDF**: When you need the original layout, figures, or tables as-is.

**When to use TEI XML**: When feeding text to an LLM for screening, classification, or extraction.

## Input Modes

| Mode | Flag | Use case |
|------|------|----------|
| Filter | `--filter "..."` | Download matching subset of OpenAlex |
| Explicit IDs | `--ids "W123,W456"` | Specific known works |
| Stdin | `--stdin` | Pipe IDs from another process |

### Stdin pipeline example (API search → CLI download)

```bash
# Step 1: Search via API, extract IDs
python -c "
import os, requests
r = requests.get('https://api.openalex.org/works', params={
    'search': 'health judicialization',
    'filter': 'language:pt,publication_year:>2018',
    'select': 'id',
    'per_page': 100,
    'api_key': os.environ['OPENALEX_API_KEY']
}).json()
for w in r['results']:
    print(w['id'].split('/')[-1])
" > work_ids.txt

# Step 2: Download TEI XML for those works
cat work_ids.txt | openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./corpus \
  --stdin \
  --content xml
```

## Output Structure

```
output/
├── W2741809807.json          # metadata (always saved)
├── W2741809807.pdf           # if --content pdf
├── W2741809807.tei.xml       # if --content xml
├── W1234567890.json
├── W1234567890.pdf
├── openalex-download.log     # activity log
└── .openalex-checkpoint.json # resume state (internal)
```

Metadata JSON files contain the full Work object from the API.

Default output directory (when `--output` is omitted): `./openalex-downloads`.

## Checkpointing and Resume

The CLI automatically saves progress to `.openalex-checkpoint.json`. If a download
is interrupted, just run the **exact same command** again — it will resume where it left off
without re-downloading completed files.

Checkpoint control flags:
```bash
--fresh            # Ignore checkpoint, start from scratch
--resume           # Resume from checkpoint (default: true)
--no-resume        # Disable checkpoint resume
```

## Performance Tuning

```bash
# Increase parallel workers (default: 50, range: 1-200)
openalex download --workers 150 ...

# For maximum throughput, deploy from cloud
# AWS EC2 / GCP VM near Cloudflare edge = lower latency
```

Additional flags:

| Flag | Description | Default |
|------|-------------|---------|
| `--workers N` | Parallel download workers (1-200) | `50` |
| `--sample N` | Random sample of N works (1-10,000); not with `--ids`/`--stdin` | off |
| `--seed N` | Seed for a reproducible `--sample` | none |
| `--nested` | Organize into W##/##/ subfolders (for >10K files) | `false` |
| `--quiet` / `-q` | Minimal output (log file only) | `false` |
| `--verbose` / `-v` | Debug output | `false` |

Typical speeds (content downloads are bandwidth-bound; PDFs average ~5 MB):
- Fast home connection (200-400 Mbit/s): ~5-15 files/sec, about 20,000-50,000 files/hour, a few hundred thousand a day
- Cloud VM with multi-gigabit networking: several times that
- Metadata-only runs are far faster (a few KB per record)

## S3 Storage

For very large downloads, stream directly to S3:

```bash
openalex download \
  --api-key $OPENALEX_API_KEY \
  --storage s3 \
  --s3-bucket my-corpus \
  --s3-prefix openalex/ \
  --filter "topics.id:T12345" \
  --content pdf
```

## Costs

**IMPORTANT: Always estimate and communicate costs to the user before downloading content.**
Use the API to check `meta.count` with `has_content.pdf:true`, multiply by $0.01.

| What | Cost |
|------|------|
| Metadata (JSON) | ~$0.10 per 1,000 list requests (works by ID are free) |
| PDF download | $0.01 per file |
| TEI XML download | $0.01 per file |
| Free daily allowance | $1/day (~100 content files) |

To estimate costs: count works with `has_content.pdf:true` in your filter via the API
(`meta.count`), then multiply by $0.01.

## Common Recipes

### Build a corpus for LLM screening
```bash
# Download TEI XML for a topic
openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./screening-corpus \
  --filter "fulltext.search:rare diseases litigation,language:pt|en,publication_year:>2015,has_content.grobid_xml:true" \
  --content xml
```

### Download all OA PDFs from an institution
```bash
# First find institution ID via API, then:
openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./insper-papers \
  --filter "authorships.institutions.id:I123456789,is_oa:true,has_content.pdf:true" \
  --content pdf
```

### Download specific papers after manual selection
```bash
# Save DOIs/IDs to a file (one per line)
echo "10.1038/nature12373
10.1126/science.1234567
W2741809807" > selected.txt

cat selected.txt | openalex download \
  --api-key $OPENALEX_API_KEY \
  --output ./selected-papers \
  --stdin \
  --content pdf,xml
```

## Reference Links

- CLI docs: https://help.openalex.org/access/cli/
- Full-text PDFs docs: https://help.openalex.org/access/fulltext/
- GitHub: https://github.com/ourresearch/openalex-official
- Filter reference: https://help.openalex.org/api/filtering/
