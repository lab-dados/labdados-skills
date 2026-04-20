---
name: openalex
description: Search, filter, and download scholarly works, authors, and full-text content from OpenAlex (460M+ academic works). Use for literature search, systematic reviews, bibliometric analysis, citation networks, downloading research papers/PDFs, or any academic database task.
---

# OpenAlex Skill

OpenAlex is a fully open catalog of 460M+ scholarly works, authors, sources, institutions, topics,
publishers, and funders. Two complementary tools cover all use cases:

- **API** — search, filter, retrieve metadata
- **CLI** — bulk download of metadata + PDFs + TEI XML

## Before you start

Complete this checklist before any API call or CLI command.

### 1. API key

Check if `OPENALEX_API_KEY` exists in the environment:
1. `echo $OPENALEX_API_KEY`
2. Check `.env` in the project
3. Check if the user already provided it in the conversation

If not found, ask the user:
> You need an OpenAlex API key (free, 30 seconds).
> Register at https://openalex.org/settings/api — gives $1/day in free credits.
> Save as `OPENALEX_API_KEY` in your `.env`.

Do NOT proceed without a configured key.

### 2. CLI (if needed)

Only for download tasks. Check if `openalex` is available:
- Preferred: `uv tool install openalex-official`
- Alternative: `pipx install openalex-official`
- Fallback: `pip install openalex-official`

The CLI is a standalone tool — do NOT install inside the project venv with `uv add`.

## Cost awareness — MANDATORY

Before running any content download (PDF or TEI XML):

1. **Estimate cost.** Query the API to get `meta.count` of works with
   `has_content.pdf:true` or `has_content.grobid_xml:true`, multiply by $0.01.
2. **Warn the user.** Show count and estimated cost BEFORE running the download.
   Example: "This filter found 2,340 works with PDF. Download will cost ~$23.40 in credits. Proceed?"
3. **Wait for explicit confirmation** before executing.

Metadata downloads (JSON without `--content`) are free — no warning needed.
The free tier gives $1/day (~100 files). Warn if cost exceeds the daily limit.

## When to use what

> **Recommended at the start of any new systematic case-law study** —
> before formalizing a codebook, run a literature review with this
> skill. A codebook that does not engage with existing research is
> weaker and may duplicate work.

| I need to... | Use | Reference |
|---|---|---|
| Search works by keyword, abstract, or fulltext | API | `references/api.md` |
| Filter works by year, topic, institution, OA status | API | `references/api.md` |
| ~~Find semantically similar papers~~ | ~~API~~ | Deprecated — use keyword search or citation network |
| Retrieve metadata for specific DOIs/IDs | API | `references/api.md` |
| Analyze citation networks | API | `references/api.md` |
| Trace forward/backward citations | API | `references/api.md` |
| Aggregate data (works per year, per topic) | API | `references/api.md` |
| Download PDFs or TEI XML in bulk | CLI | `references/cli.md` |
| Download metadata as JSON files | CLI | `references/cli.md` |
| Download specific papers by ID/DOI | CLI | `references/cli.md` |
| Build a local corpus for LLM screening | Both | API to search → CLI to download |
| Literature review at the start of a systematic case-law study | Both | API for discovery, CLI for downloads |

## Key concepts

**Entities**: works, authors, sources, institutions, topics, keywords, publishers, funders.

**Abstracts**: Stored as inverted index (not plaintext) due to legal constraints. API search
works on them natively; reconstruct to plaintext only if you need the text for LLM processing.

**Full-text content**: ~60M works have cached PDFs; ~43M have TEI XML (structured text via GROBID).
TEI XML is preferred for automated processing. Content downloads cost $0.01 each.

**Two-step lookup**: Never filter by entity names. Always resolve to an OpenAlex ID first,
then filter by that ID. Example: search `/authors?search=Einstein` → get ID → filter
`/works?filter=authorships.author.id:A5023888391`.

**Citation direction (`cites` vs `cited_by`)**: Filter names describe the relationship of the *returned works* to the given ID.
- `cites:W123` → "works that cite W123" = incoming citations (forward)
- `cited_by:W123` → "works cited by W123" = outgoing references (backward)
- Mnemonic: `cites:X` = "who cites X?"; `cited_by:X` = "what does X cite?"

**Rate limits**: 100 req/sec hard limit. Free: $1/day (resets midnight UTC).
Singleton lookups free; list+filter $0.10/1K; search $1/1K; content $0.01/file.
Check usage: `GET /rate-limit?api_key=KEY`

**Deprecated**: Concepts (use Topics), `/text` endpoint, `.search` filters
(display_name.search, abstract.search, title.search — use the `search` parameter instead).

## Coverage limitations (especially for Brazilian legal research)

OpenAlex indexes 460M+ works from journals, preprint servers, books,
and theses. Coverage is strongest where publications are indexed in
Scopus / Web of Science / Crossref / DOAJ. For **Brazilian legal
research**, part of the production lives outside those sources:

- **Journals not indexed in international databases**: many Brazilian
  law journals (especially those linked to law schools) are in Scielo,
  Latindex, or local portals but not in Scopus/WoS — some are still
  reached by OpenAlex via Crossref DOIs, but coverage is uneven.
- **Conference proceedings (anais de congressos)**: a non-trivial
  share of empirical legal research in Brazil appears in congress
  proceedings (CONPEDI, IBRASPP, etc.) — often not indexed in OpenAlex.
- **Books and book chapters**: Brazilian legal doctrine relies heavily
  on books and edited volumes; OpenAlex includes many but coverage of
  Portuguese-language Brazilian publishers is partial.
- **Theses and dissertations**: Catalogo de Teses CAPES and
  institutional repositories may have works not in OpenAlex.

**Practical recommendation** for critical literature reviews in
Brazilian law:

1. Start with OpenAlex (this skill) for international literature and
   for works with DOI.
2. **Cross-check** with Scielo (`https://search.scielo.org`), Catalogo
   de Teses CAPES (`https://catalogodeteses.capes.gov.br`), and Google
   Scholar for Brazilian-specific sources.
3. Document the search strategy per source in your research protocol.

## Reference files

Read the appropriate reference before making API calls or running CLI commands:

- **`references/api.md`** — Complete API reference: endpoints, search, filters, pagination,
  cursor pagination, batch lookups, group_by, error handling.
  Read this when doing any search, filter, or metadata retrieval task.

- **`references/cli.md`** — Complete CLI reference: download commands, filter syntax,
  content options, checkpointing, performance tuning, output structure, costs.
  Read this when downloading files (PDFs, XML, metadata JSONs) in bulk.

## Typical agent workflow

1. Read this SKILL.md (done).
2. Run the "Before you start" checklist (API key, tool installation).
3. If the task involves **searching or retrieving metadata** → read `references/api.md`.
4. If the task involves **downloading files** → read `references/cli.md`.
5. If it's a **pipeline** (search then download) → read both, API first.
6. If downloading content (PDF/XML), **estimate cost and warn the user** before executing.
7. Execute the task.
