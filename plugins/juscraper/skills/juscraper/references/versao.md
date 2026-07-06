# Versao da skill vs versao do juscraper

Este arquivo registra ate que versao da biblioteca `juscraper` a skill esta alinhada e como ler as tags de status que aparecem ao longo das references.

## Alinhamento atual

A skill **v1.2.0** esta alinhada com a release do `juscraper` que inclui o commit `0bc0de5` de 2026-07-03.

Para confirmar a versao instalada no ambiente do usuario: `python -c "import juscraper; print(juscraper.__version__)"`.

## Tabela de bumps

| Skill | juscraper release | Snapshot de referencia | Principais inclusoes |
|---|---|---|---|
| 1.2.0 | release com `0bc0de5` | `0bc0de5` (2026-07-03) | +TRF6 (`cpopg` via eproc/txtcaptcha); `download_pecas`/`diretorio` em TRF1/TRF3/TRF5; `count_only=True` em eSAJ/TJSP; `listar_classes`/`listar_assuntos`/`listar_orgaos`/`listar_varas`; JusBR com `auth(exp)` e coluna `processo`; Datajud/ComunicaCNJ/PDPJ revisados; excecoes anti-bot (`BotChallengeBlockedError`, `TJAPSecurityCheckError`) |
| 1.1.0 | 0.3.0 (2026-05-03) | `6c5703d` (2026-05-13) | +TJGO, +TJMG (`[v0.3.0+, requer extra tjmg]`), +TJRJ, +TRF1/TRF3/TRF5, +ComunicaCNJ, +PDPJ; refactor `HTTPScraper` + `RetryExhaustedError`; singulares `classe`/`assunto`/`vara`/`tamanho_pagina`; pydantic `extra="forbid"` em todos os endpoints; auto-chunk eSAJ |
| 1.0.0 | ~0.1.x — 0.2.x | — | 22 tribunais estaduais (TJSP, TJRS, TJPR, TJDFT, TJBA, TJCE, TJES, TJMT, TJPA, TJPB, TJPE, TJPI, TJRN, TJRO, TJRR, TJSC, TJTO, TJAC, TJAL, TJAM, TJAP, TJMS) + Datajud + JusBR |

## Vocabulario de tags

Ao longo das references, recursos novos ganham tags inline:

| Tag | Significado | Acao para o usuario |
|---|---|---|
| (sem tag) | Disponivel desde versoes antigas (v0.1.x/v0.2.x), estavel no PyPI | `pip install juscraper` resolve |
| `[v0.3.0+]` | Adicionado na v0.3.0 (estavel no PyPI hoje) | `pip install juscraper>=0.3.0` |
| `[v0.3.0+, requer extra tjmg]` | Estavel no PyPI, mas requer dependencia extra | `pip install 'juscraper[tjmg]>=0.3.0'` |
| `[release com 0bc0de5]` | Disponivel na release que inclui o commit `0bc0de5` | `pip install -U juscraper` |

Quando aparecer nova release oficial, atualizar a tabela acima com nova linha de bump.

## Procedimento para os proximos bumps

Quando aparecer uma nova release no PyPI ou um delta relevante na `main`, atualizar esta skill seguindo os passos abaixo. O objetivo e manter o alinhamento rastreavel e reproduzivel.

### 1. Levantar o estado atual da biblioteca

```bash
# Ultimas versoes publicadas
pip index versions juscraper

# Ou, com mais detalhes incluindo data de publicacao:
curl -s https://pypi.org/pypi/juscraper/json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('latest:', d['info']['version'])
for v, files in sorted(d['releases'].items())[-5:]:
    if files:
        print(v, '->', files[0]['upload_time'])
"
```

### 2. Identificar o que mudou desde o ultimo alinhamento

```bash
cd ~/Desktop/dev/juscraper   # ou onde o clone estiver
git fetch --tags origin
git log --oneline v<ultima-tag>..HEAD   # delta da main
git log --oneline v<penultima>..v<ultima>   # delta da release passada
```

E ler a secao `[Unreleased]` do `CHANGELOG.md` do repositorio, que e a fonte canonica.

### 3. Atualizar arquivos da skill

Em ordem de menor para maior risco:

1. `references/versao.md` (este arquivo) — adicionar nova linha na tabela de bumps com a versao nova da skill e o que entrou.
2. `references/tribunais.md` — adicionar novos tribunais a matriz, atualizar parametros canonicos, gotchas.
3. `references/api.md` — atualizar lista de siglas do factory, adicionar construtores novos, atualizar tabela de aliases depreciados.
4. `references/agregadores.md` — se houver agregador novo ou metodo novo em agregador existente.
5. `references/tjsp.md` — se houver especificidade nova do TJSP.
6. `SKILL.md` — atualizar a nota de versao no topo, frontmatter `description` se mudou a contagem de tribunais/agregadores, secao de roteamento e tratamento de erros.
7. `.claude-plugin/marketplace.json` — bump da `version` da skill e atualizar a `description`.

### 4. Verificacao

```bash
# Conferir que toda sigla mencionada na skill bate com o factory real:
python3 -c "
import juscraper
print(sorted(getattr(juscraper, '_SCRAPERS', {}).keys()))
"
grep -hoE "'(tj[a-z]+|trf[0-9]+|datajud|jusbr|pdpj|comunica_cnj)'" \
  plugins/juscraper/skills/juscraper/SKILL.md \
  plugins/juscraper/skills/juscraper/references/*.md | sort -u
# Diff manual entre as duas saidas
```

## Decisoes de escopo registradas

- A skill cobre a release publicada do `juscraper`; o default e `pip install -U juscraper` ou `uv add -U juscraper`.
- TRF1/TRF3/TRF5/TRF6 e PDPJ sao tratados como recursos publicados na release que inclui `0bc0de5`.
- A arvore de assuntos do TJSP (`references/assuntos-tjsp.json`) foi coletada em 2026-04-16 e nao precisa ser re-coletada a cada bump da skill — a Tabela Processual Unificada do CNJ muda lentamente. Re-coletar so quando aparecer divergencia reportada por usuario ou pesquisa que use codigo desconhecido.
