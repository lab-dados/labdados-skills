# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is a **Claude Code plugin marketplace** (`labdados-skills`), maintained by
[lab-dados](https://github.com/lab-dados) for empirical legal research in Brazil.
It contains **no application code** — it is a registry of plugins, each shipping
one or more **Skills** (Markdown instruction files that Claude loads on demand).
The "code" here is the skill content, the manifests that register it, and the
assets/reference docs each skill pulls in.

Most skills are written in **Brazilian Portuguese** (with accents). Match that
language and tone when editing skill content. CHANGELOG/marketplace metadata is
sometimes written without accents — follow the surrounding file.

## Repository structure

```
.claude-plugin/marketplace.json   ← the registry: lists every plugin + its version
plugins/<plugin>/
  .claude-plugin/plugin.json       ← per-plugin manifest (name, description, keywords)
  skills/<skill>/
    SKILL.md                       ← skill entry point (frontmatter + instructions)
    references/*.md                ← progressive-disclosure docs, loaded on demand
    assets/                        ← templates, theme files, scripts shipped with the skill
```

A plugin can contain multiple skills (e.g. `juscraper-builder` ships both
`juscraper-builder` and `juscraper-builder-captcha`).

## How skills work (the core architecture)

- **`SKILL.md` frontmatter** has `name` and `description`. The `description` is
  the *trigger*: Claude reads it to decide when to invoke the skill, so it must
  enumerate concrete trigger phrases (the existing descriptions are long on
  purpose — they list user intents, synonyms, and "não confundir com" disambiguation
  against sibling skills). When adding/editing a skill, keep the description
  trigger-rich and explicitly distinguish it from neighboring skills.
- **`references/*.md`** implement progressive disclosure: SKILL.md tells Claude to
  read a specific reference only when needed (e.g. "antes de qualquer coisa, leia
  `references/estilo.md`"), keeping the always-loaded context small. Put detail in
  references, not in SKILL.md.
- **`assets/`** holds things the skill emits or applies — Quarto templates, a
  plotnine theme, docx post-processing scripts, report/ata templates.

Most skills are *wrappers around external Python libraries* (`juscraper`,
`dataframeit`, `raspe`, `labdados-sdk`) or external services (OpenAlex, Google
Drive/Gmail MCP, Playwright MCP). The skill teaches Claude how to drive the tool;
it does not vendor the tool. Per-skill prerequisites live in the README's
"Pré-requisitos por skill" section.

## Editing conventions

When you add or change a plugin/skill, these must stay in sync (there is no script
that does it for you):

1. **`.claude-plugin/marketplace.json`** — add/update the plugin entry and bump
   its `version`, and bump the top-level `metadata.version` (the marketplace
   version is what triggers Claude Code clients to re-clone).
2. **`plugins/<plugin>/.claude-plugin/plugin.json`** — keep `name`, `description`,
   `keywords` consistent with the marketplace entry.
3. **`README.md`** — the "Skills disponíveis" table and "Pré-requisitos por skill".
4. **`CHANGELOG.md`** — add an entry (Keep a Changelog format, semver).

Versioning is [SemVer](https://semver.org/). Adding a new plugin = minor bump of
`metadata.version`.

## Validation

CI is GitHub Actions (`.github/workflows/validate.yml`), run on push/PR to `main`.
It checks:

- `marketplace.json` and every `plugins/*/.claude-plugin/plugin.json` are valid JSON.
- Every plugin `source` path in `marketplace.json` exists.
- Every plugin has at least one `skills/*/SKILL.md`.
- Every plugin passes the parser and manifest checks from `claude plugin validate`.

Reproduce locally before pushing:

```powershell
python -c "import json; json.load(open('.claude-plugin/marketplace.json'))"
npx --yes @anthropic-ai/claude-code@2.1.126 plugin validate plugins/<plugin>
```

There is no build, lint, or unit-test step for this repo — validation is the
JSON/structure checks plus the Claude Code plugin validator above. (Individual *generated* scrapers, e.g. from
`raspe-builder`/`juscraper-builder`, do have offline `responses`-based tests, but
those tests live in the *target* library repos, not here.)

## Builder skills

`juscraper-builder`, `juscraper-builder-captcha`, and `raspe-builder` are
meta-skills: they use the **Playwright MCP** to reverse-engineer a website, then
generate Python scraper code (plus factory registration and offline tests) inside
a *separate* target repository (`juscraper` or `bdcdo/raspe`). `raspe-builder` also
syncs the `raspe` skill in this repo with the new source (a row in the reference
tables + a new `references/<fonte>.md`). When working on these, the output goes to
another repo whose path the skill discovers at runtime — it is not committed here.
