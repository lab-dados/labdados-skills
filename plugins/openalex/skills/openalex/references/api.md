# OpenAlex API Reference

Base URL: `https://api.openalex.org`

## Table of Contents

1. [Authentication](#authentication)
2. [Entity Endpoints](#entity-endpoints)
3. [Query Parameters](#query-parameters)
4. [Search](#search)
5. [Filter Syntax](#filter-syntax)
6. [Key Work Filters](#key-work-filters)
7. [Two-Step Lookup Pattern](#two-step-lookup-pattern)
8. [External IDs](#external-ids)
9. [Pagination](#pagination)
10. [Cursor Pagination](#cursor-pagination)
11. [Batch ID Lookups](#batch-id-lookups)
12. [Group By / Aggregation](#group-by)
13. [Select Fields](#select-fields)
14. [Autocomplete](#autocomplete)
15. [Semantic Search](#semantic-search)
16. [Abstracts](#abstracts)
17. [Full-Text Content via API](#full-text-content-via-api)
18. [Response Structure](#response-structure)
19. [Rate Limits and Pricing](#rate-limits-and-pricing)
20. [Error Handling](#error-handling)
21. [Common Workflow Examples](#common-workflow-examples)
22. [Critical Gotchas](#critical-gotchas)

---

## Authentication

Always include your API key, as a query parameter or as a bearer token (both work identically):
```
https://api.openalex.org/works?api_key=$OPENALEX_API_KEY
curl -H "Authorization: Bearer $OPENALEX_API_KEY" "https://api.openalex.org/works"
```

Without a key the API still answers, but the budget is only $0.10/day (a tenth of the
free key's $1/day); once it is spent, requests return HTTP 429. Content downloads
(`content.openalex.org`) return 401 without a key.

> **No polite pool.** The `mailto=`/`email=` parameter was replaced by API keys in
> February 2026 and is now ignored: it gives no extra budget. Do NOT use `mailto` as a
> free fallback when the key is missing. Ask the user for a key instead.

## Entity Endpoints

```
/works          — 320M+ scholarly documents in the default corpus; 460M+ with `corpus=all`
/authors        — Researcher profiles with disambiguated identities
/sources        — Journals, repositories, conferences (~250K)
/institutions   — Universities, research organizations
/topics         — Subject classifications (3-level hierarchy)
/keywords       — Short phrases from works
/publishers     — Publishing organizations
/funders        — Funding agencies
```

> **Deprecated**: `/text` (text classification) — endpoint deprecated.
> **Deprecated**: Concepts endpoint — replaced by Topics.

## Query Parameters

```
api_key=        — Your API key (or send `Authorization: Bearer <key>`)
filter=         — Filter results (see syntax below)
search=         — Full-text search across title/abstract/fulltext
search.exact=   — Same, without stemming (needed for wildcards)
search.semantic= — Search by meaning (see Semantic Search)
sort=           — Sort results (e.g., cited_by_count:desc)
per_page=       — Results per page (default: 25, max: 100; 200 is legacy and deprecated)
page=           — Page number for pagination
cursor=         — Cursor for deep pagination (see Cursor Pagination)
sample=         — Random results (e.g., sample=50; max 10,000)
seed=           — Seed for reproducible sampling
select=         — Limit returned fields (e.g., select=id,title)
group_by=       — Aggregate results by a field
```

## Search

The `search=` parameter searches across title, abstract, AND fulltext simultaneously:

```
/works?search=machine+learning
/works?search=climate+AND+change
/works?search=CRISPR+OR+gene+editing
/works?search=neural+NOT+network
/works?search=(elmo AND "sesame street") NOT (cookie OR monster)
```

Boolean operators `AND`, `OR`, `NOT` must be uppercase; words without an operator are
treated as `AND`. The search is stemmed ("possums" also matches "possum").

```
# Exact phrase
/works?search="fierce creatures"
# Proximity: words within N positions of each other
/works?search="climate change"~5
# Unstemmed search; wildcards (*, ?) only work here
/works?search.exact=machin*
```

Only one search parameter per request: `search`, `search.exact`, or `search.semantic`.

**URL length limit**: the whole request URL is limited to about 4 KB (4,094 bytes).
Longer URLs, typically long Boolean `OR` lists in systematic reviews, return `400`
"Request URL too long". Split the `OR` list into chunks, run each, and take the union
of the returned IDs client-side (same result set, each chunk billed separately).

> **Deprecated**: Field-specific `.search` filters (`title.search`, `abstract.search`,
> `display_name.search`, `fulltext.search`) still work but are not recommended. Use the
> `search=` parameter instead. Exception: to mix stemmed and wildcard terms in one query,
> use the filter form, e.g. `filter=fulltext.search:treatment,fulltext.search.exact:psoriat*`.

## Filter Syntax

```
# Single filter
?filter=publication_year:2024

# Multiple filters (AND)
?filter=publication_year:2024,is_oa:true

# OR within same attribute (pipe, up to 100 values)
?filter=type:article|book|dataset

# Negation
?filter=type:!paratext

# Comparison operators
?filter=cited_by_count:>100
?filter=publication_year:<2020
?filter=publication_year:2020-2024

# AND within same attribute
?filter=institutions.country_code:us+gb
```

**Important**: OR only works WITHIN a filter. You cannot do cross-filter OR.
Workaround: make separate queries and combine results.

Boolean values must be lowercase: `is_oa:true` not `is_oa:True`.
Python `str(True)` returns `"True"` — always use string literals `"true"`/`"false"`.

## Key Work Filters

```
publication_year                    — Year (integer or range)
is_oa                               — Open access (boolean)
type                                — article, book, dataset, etc.
has_abstract                        — Has abstract (boolean)
has_fulltext                        — Has searchable fulltext (boolean)
has_content.pdf                     — Has downloadable PDF (boolean)
has_content.grobid_xml              — Has downloadable TEI XML (boolean)
has_doi                             — Has DOI (boolean)
cited_by_count                      — Citation count (integer)
language                            — ISO 639-1 code (pt, en, es)
authorships.author.id               — Author OpenAlex ID
authorships.institutions.id         — Institution OpenAlex ID
primary_location.source.id          — Source/journal OpenAlex ID
topics.id                           — Topic OpenAlex ID
open_access.oa_status               — gold, green, hybrid, diamond, closed
best_oa_location.license            — cc-by, cc-by-nc, cc0, etc.
cites                               — Filter results to works that cite a given work ID (incoming citations)
cited_by                            — Filter results to works that are cited by a given work ID (outgoing references)
```

Other entity filters:
```
# Authors
last_known_institution.id, works_count, cited_by_count, orcid

# Sources
host_organization, type (journal, repository), is_oa

# Institutions
type (education, healthcare, company), country_code, continent
```

## Two-Step Lookup Pattern

**CRITICAL: Never filter by entity name. Always resolve to ID first.**

```
# WRONG — will fail or return wrong results
/works?filter=author_name:Einstein

# CORRECT — two steps
# Step 1: Get the ID
/authors?search=Einstein
# Response: "id": "https://openalex.org/A5023888391"

# Step 2: Filter by ID
/works?filter=authorships.author.id:A5023888391
```

This applies to: authors, institutions, sources, topics, publishers, funders.

## External IDs

You can look up entities directly by external identifiers:

```
# Works
/works/https://doi.org/10.7717/peerj.4375
/works/pmid:29844763

# Authors
/authors/https://orcid.org/0000-0003-1613-5981

# Institutions
/institutions/https://ror.org/042nb2s44

# Sources
/sources/issn:0028-0836
```

## Pagination

```
# Use max page size for efficiency (4x faster than default)
/works?filter=publication_year:2024&per_page=100&page=1

# Total count is in meta.count
# Pages needed: ceil(meta.count / per_page)
```

**Page-based pagination has a hard cap of 10,000 results** (`page × per_page` must not exceed 10,000).
For larger result sets, use cursor pagination (see below).

## Cursor Pagination

For results above 10,000, use cursor pagination (no upper limit):

```python
import os, requests, time

API_KEY = os.environ["OPENALEX_API_KEY"]
BASE = "https://api.openalex.org"

params = {
    "filter": "publication_year:2024,is_oa:true",
    "per_page": 100,
    "cursor": "*",
    "api_key": API_KEY,
}
all_results = []
while True:
    data = requests.get(f"{BASE}/works", params=params, timeout=30).json()
    results = data.get("results", [])
    if not results:
        break
    all_results.extend(results)
    next_cursor = data["meta"].get("next_cursor")
    if not next_cursor:
        break
    params["cursor"] = next_cursor
    time.sleep(0.1)
```

Page-based (`?page=N`) has a hard cap of 10,000 results. Use cursor for any bulk retrieval.

**Efficient counting**: Use `per_page=1` and read `meta.count` to check result size
before committing to a full download:
```
/works?filter=publication_year:2024,is_oa:true&per_page=1&api_key=$OPENALEX_API_KEY
# Response: {"meta": {"count": 48230, ...}, "results": [...]}
# → 48,230 works. At $0.10/1K list calls, full retrieval ≈ 483 pages × $0.10/1K ≈ $0.05
# → If downloading PDFs: 48,230 × $0.01 = $482.30 in content credits
```
Always count first to estimate cost, especially for content downloads.

## Batch ID Lookups

**Do not loop through IDs one by one.** Use pipe separator (up to 100 per request):

```
/works?filter=doi:https://doi.org/10.1371/journal.pone.0266781|https://doi.org/10.1371/journal.pone.0267149&per_page=100
```

## Group By

```
/works?group_by=publication_year
/works?group_by=topics.id
/works?filter=publication_year:>2020&group_by=open_access.oa_status
```

Only ONE group_by per request. For multi-dimensional analysis, make separate queries
per dimension and combine client-side.

## Select Fields

Return only what you need (significantly faster):

```
/works?select=id,title,publication_year,cited_by_count,doi&per_page=100
```

**Limitation**: `select` only works on top-level fields. You can request `open_access`
(returns the whole object) but not `open_access.is_oa` (will error).

## Autocomplete

Fast type-ahead (~200ms):
```
/autocomplete/works?q=neural+networks
/autocomplete/authors?q=einstein
/autocomplete/institutions?q=USP
```


## Semantic Search

Finds works closest in meaning to the query (embeddings of title and abstract), even when
the wording differs. Useful with long inputs such as an abstract or a research question.

```
/works?search.semantic=predicting drug toxicity from molecular structure
/works?search.semantic=mRNA vaccine immunogenicity in older adults&filter=publication_year:>2020,is_oa:true&select=id,title,relevance_score
```

| Constraint | Value |
|------------|-------|
| Max input length | 2,000 characters (longer input is truncated) |
| Max results | 50 per query |
| Rate limit | 1 request per second |
| Cost | $1 / 1,000 calls (same as keyword search) |

Only a whitelist of filters is supported; other filters return `400` listing the
allowed ones (observed on 2026-09-23): `author.id`, `authorships.author.id`,
`authorships.institutions.id`, `authorships.institutions.lineage`, `funders.id`,
`has_abstract`, `has_fulltext`, `institution.id`, `institutions.id`, `is_oa`,
`is_retracted`, `language`, `open_access.is_oa`, `primary_location.license`,
`primary_location.source.id`, `publication_year`, `type`. Not supported include
`cited_by_count`, `topics.id`, `has_content.*`, `cites`/`cited_by` and `from_publication_date`.

## Abstracts

Stored as **inverted index** (not plaintext):
```json
"abstract_inverted_index": {
  "Despite": [0], "growing": [1], "interest": [2], "in": [3, 57]
}
```

Reconstruct to plaintext in Python:
```python
def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(word for _, word in word_positions)
```

Note: API search works on abstracts natively. Only reconstruct when you need the
text for downstream processing (e.g., feeding to an LLM).

## Full-Text Content via API

Works with `has_content.pdf:true` or `has_content.grobid_xml:true` have downloadable content.

Direct content URLs (also listed in each work's `content_urls` field):
```
https://content.openalex.org/works/{WORK_ID}.pdf?api_key=$OPENALEX_API_KEY
https://content.openalex.org/works/{WORK_ID}.grobid-xml?api_key=$OPENALEX_API_KEY
```

TEI XML is served with `Content-Encoding: gzip`. `requests`/`httpx` decode it
transparently; with `curl`, pass `--compressed` or you get raw gzip bytes:
```
curl --compressed "https://content.openalex.org/works/W3038568908.grobid-xml?api_key=$OPENALEX_API_KEY"
```

```
# Find works with PDFs
/works?filter=has_content.pdf:true,publication_year:2024

# Filter by license
/works?filter=has_content.pdf:true,best_oa_location.license:cc-by
```

Each content download costs $0.01. For bulk downloads, use the CLI instead.

**Always warn the user about costs before downloading content.**

## Response Structure

**List endpoints** return:
```json
{
  "meta": {"count": 240523418, "page": 1, "per_page": 25},
  "results": [{ /* entity objects */ }]
}
```

**Single entity** returns the object directly (no meta/results wrapper).

**Group by** returns:
```json
{
  "meta": {"count": 100},
  "group_by": [
    {"key": "https://openalex.org/T10001", "key_display_name": "AI", "count": 15234}
  ]
}
```

## Rate Limits and Pricing

**Free daily allowance:** $1/day with a free key ($0.10/day without a key), resets at midnight UTC.
More budget: prepaid usage in $1 increments, or annual plans (Member $20/day, Member+ $100/day, Partner $200+/day).

| Operation | Cost | Free tier daily |
|-----------|------|-----------------|
| Get singleton (by ID/DOI) | Free | Unlimited |
| List + Filter | $0.10 / 1,000 calls | ~10,000 calls |
| Search (keyword + semantic) | $1 / 1,000 calls | ~1,000 calls |
| Content download (PDF/XML) | $10 / 1,000 ($0.01 each) | ~100 files |

**Hard limit:** 100 requests/second (semantic search: 1/second). Exceeding it, or
exhausting the daily budget, triggers HTTP 429.

**Rate limit headers** (in every response):
- `X-RateLimit-Limit` — daily budget
- `X-RateLimit-Remaining` — remaining today
- `X-RateLimit-Credits-Used` — this request's cost
- `X-RateLimit-Reset` — seconds until midnight UTC reset

**Check usage:** `GET /rate-limit?api_key=$OPENALEX_API_KEY`

## Error Handling

```
200 OK           — Success
400 Bad Request  — Invalid parameter (check filter syntax)
404 Not Found    — Entity doesn't exist
429 Too Many     — Rate limit exceeded (check X-RateLimit headers)
500 Server Error — Retry with backoff
503 Unavailable  — Retry with backoff
```

Always implement exponential backoff:
```python
import os, requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def create_openalex_session():
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 503])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session

def fetch_with_retry(url):
    session = create_openalex_session()
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()
```

## Common Workflow Examples

### Systematic Review Search
```python
import os, requests, time

API_KEY = os.environ["OPENALEX_API_KEY"]
BASE = "https://api.openalex.org"

def search_all(query, filters=None, per_page=100):
    params = {
        "search": query, "per_page": per_page, "api_key": API_KEY,
        "select": "id,doi,title,abstract_inverted_index,publication_year,cited_by_count,type,is_oa",
        "cursor": "*",
    }
    if filters:
        params["filter"] = filters
    all_results = []
    while True:
        data = requests.get(f"{BASE}/works", params=params, timeout=30).json()
        results = data.get("results", [])
        if not results:
            break
        all_results.extend(results)
        next_cursor = data["meta"].get("next_cursor")
        if not next_cursor:
            break
        params["cursor"] = next_cursor
        time.sleep(0.1)
    return all_results, data["meta"]["count"]

works, total = search_all("health judicialization", "publication_year:>2018,language:pt|en")
```

### Citation Network
```python
import os, requests, time

API_KEY = os.environ["OPENALEX_API_KEY"]
BASE = "https://api.openalex.org"

work_id = "W2741809807"
work = requests.get(f"{BASE}/works/{work_id}?api_key={API_KEY}").json()

# --- Forward citations: works that cite this paper ---
# cites:W123 → "who cites W123?" = incoming citations
# Use cursor pagination to collect ALL citing works (not just first page)
citing_works = []
params = {
    "filter": f"cites:{work_id}",
    "per_page": 100,
    "select": "id,title,publication_year,cited_by_count,doi",
    "cursor": "*",
    "api_key": API_KEY,
}
while True:
    data = requests.get(f"{BASE}/works", params=params, timeout=30).json()
    results = data.get("results", [])
    if not results:
        break
    citing_works.extend(results)
    next_cursor = data["meta"].get("next_cursor")
    if not next_cursor:
        break
    params["cursor"] = next_cursor
    time.sleep(0.1)

# --- Backward references: works cited by this paper ---
# cited_by:W123 → "what does W123 cite?" = outgoing references
references = []
params = {
    "filter": f"cited_by:{work_id}",
    "per_page": 100,
    "select": "id,title,publication_year,cited_by_count,doi",
    "cursor": "*",
    "api_key": API_KEY,
}
while True:
    data = requests.get(f"{BASE}/works", params=params, timeout=30).json()
    results = data.get("results", [])
    if not results:
        break
    references.extend(results)
    next_cursor = data["meta"].get("next_cursor")
    if not next_cursor:
        break
    params["cursor"] = next_cursor
    time.sleep(0.1)

# --- Combined: seed → forward → backward (2-hop network) ---
# Collect all unique work IDs from both directions
seen_ids = {work_id}
for w in citing_works + references:
    seen_ids.add(w["id"].split("/")[-1])
```

### Iterative Collection with Deduplication
```python
import os, requests, time

API_KEY = os.environ["OPENALEX_API_KEY"]
BASE = "https://api.openalex.org"

def collect_all_works(filter_str, select="id,title,publication_year,cited_by_count,doi"):
    """Collect all works matching a filter, with cursor pagination and deduplication."""
    seen_ids = set()
    all_works = []
    params = {
        "filter": filter_str, "per_page": 100, "select": select,
        "cursor": "*", "api_key": API_KEY,
    }
    while True:
        data = requests.get(f"{BASE}/works", params=params, timeout=30).json()
        for w in data.get("results", []):
            wid = w["id"].split("/")[-1]
            if wid not in seen_ids:
                seen_ids.add(wid)
                all_works.append(w)
        next_cursor = data["meta"].get("next_cursor")
        if not next_cursor or not data["results"]:
            break
        params["cursor"] = next_cursor
        time.sleep(0.1)
    return all_works

# Example: collect all citations of a work
citations = collect_all_works(f"cites:W2741809807")
```

### Institution Research Output
```python
import os, requests

API_KEY = os.environ["OPENALEX_API_KEY"]
BASE = "https://api.openalex.org"

# Step 1: Find institution ID
inst = requests.get(f"{BASE}/institutions?search=Insper&api_key={API_KEY}").json()
inst_id = inst["results"][0]["id"].split("/")[-1]

# Step 2: Aggregate by year
for year in range(2020, 2027):
    r = requests.get(f"{BASE}/works?filter=authorships.institutions.id:{inst_id},publication_year:{year}&per_page=1&api_key={API_KEY}").json()
    print(f"{year}: {r['meta']['count']} works")
```

## Critical Gotchas

1. **Never filter by entity names** — always two-step lookup via ID
2. **Use per_page=100** for bulk (4x faster than default 25)
3. **Pipe (|) for batch lookups** — up to 100 IDs per request, don't loop
4. **Abstract is inverted index**, not plaintext — reconstruct only when needed
5. **One group_by per request** — multiple queries for cross-tabulation
6. **Always include api_key** for rate limit access
7. **Implement exponential backoff** — errors are common at scale
8. **Use select=** to limit fields — much faster responses
9. **Use sample= for random sampling**, not arbitrary page numbers
10. **Content downloads cost credits** ($0.01 each); metadata list calls cost $0.10/1K, only lookups by ID are free
11. **Use cursor pagination** for >10K results — page-based caps at 10K
12. **Booleans must be lowercase** — `true`/`false`, not `True`/`False`
13. **`cites` vs `cited_by` direction** — `cites:W123` = "who cites W123?" (forward/incoming); `cited_by:W123` = "what does W123 cite?" (backward/outgoing). The filter name describes the *returned* works' relationship to the ID.
14. **Python boolean in f-strings** — `str(True)` → `"True"` which the API silently ignores (returns unfiltered results). Always use string literals: `f"is_oa:true"` not `f"is_oa:{is_open_access}"`. Common mistake: `params["filter"] = f"is_oa:{True}"` → sends `is_oa:True` → silently wrong.
15. **`language` field uses ISO 639-1 codes** — `language:en`, `language:pt`, `language:es`. Common mistake: `language:portuguese` or `language:English` → returns zero results with no error.

## Reference Links

- Full docs: https://help.openalex.org (formerly developers.openalex.org, which now redirects there)
- Authentication and limits: https://help.openalex.org/api/authentication/
- Filter reference: https://help.openalex.org/api/filtering/
- Search reference: https://help.openalex.org/api/searching/
- Semantic search: https://help.openalex.org/api/semantic-search/

> **Note:** The `pyalex` library (unofficial Python wrapper) exists. This skill
> focuses on the official REST API and the `openalex-official` CLI.
