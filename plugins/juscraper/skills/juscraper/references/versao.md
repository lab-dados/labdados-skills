# Versao da skill vs versao do juscraper

Este arquivo registra ate que versao da biblioteca `juscraper` a skill esta alinhada e como ler as tags de status que aparecem ao longo das references.

## Alinhamento atual

A skill **v1.5.2** esta alinhada com o `juscraper` **0.4.0** (PyPI, 2026-09-15) e, com a **0.5.0** (PyPI, 2026-10-21, a ultima release publicada), na cobertura (quem tem cada metodo), na coleta integral e no checkpoint do STF e nos trechos revistos nas versoes 1.5.0 e 1.5.1 (`cpopg`/`cposg` do TJSP). O resto da 0.5.0 (politica HTTP, `motivo_falha` no PDPJ, `auth_govbr()` e outros) ainda nao foi revisto.

A cobertura (a matriz de tribunais, os metodos dos agregadores e a lista "Quem tem cada metodo" da `SKILL.md`) e gerada do codigo da `main` do juscraper por `scripts/cobertura_juscraper.py` e conferida no CI em todo PR que toca a skill e toda segunda-feira. A ultima conferencia foi contra o snapshot `a2a3421` (2026-11-15). O que so existe na `main`, sem release no PyPI, aparece com a tag `[unreleased]`: `baixar_acordao`/`baixar_acordaos` (TJAC e TJSP) e `baixar_sentenca`/`baixar_sentencas` (TJSP), que entraram na cobertura em `1b657e7` (plugin 1.4.2), e as correcoes do `cpopg`/`cposg` do TJSP citadas em `references/tjsp.md` e `references/decisoes-e-processos.md`.

Para confirmar a versao instalada no ambiente do usuario: `python -c "import juscraper; print(juscraper.__version__)"`.

## Tabela de bumps

| Skill | juscraper release | Snapshot de referencia | Principais inclusoes |
|---|---|---|---|
| 1.5.2 | 0.5.0 (2026-10-21) + `main` | `a2a3421` (main) | Correcao: a tabela de alinhamento e a tag `[unreleased]` deixam o snapshot `5ebde28`, que ja esta na 0.5.0; os recursos do STF que ele trazia (coleta integral acima de 10.000 registros, `checkpoint_dir`/`resume`) passam a `[v0.5.0+]` |
| 1.5.1 | 0.5.0 (2026-10-21) + `main` | `a2a3421` (main) | `cposg` do TJSP devolve DataFrame, vazio no 0.5.0 (corrigido na `main`, `[unreleased]`); limites do `cpopg` no 0.5.0 reunidos em `references/tjsp.md`; `method='api'` deixa de ser oferecido |
| 1.5.0 | 0.5.0 (2026-10-21) + `main` | nao registrado | Nova `references/decisoes-e-processos.md`: juntar `cjpg`/`cjsg` aos metadados do `cpopg` pelo CNJ, conferido ao vivo no 0.5.0; correcoes do `cpopg` so na `main` (#473, #476) com `[unreleased]` |
| 1.4.2 | 0.5.0 (2026-10-21), so cobertura | `1b657e7` (main) | Cobertura regenerada: `baixar_acordao`/`baixar_acordaos` em TJAC/TJSP e `baixar_sentenca`/`baixar_sentencas` em TJSP, `[unreleased]` |
| 1.4.1 | como a 1.4.0 | como a 1.4.0 | So a `description` da skill, sem mudanca de alinhamento |
| 1.4.0 | 0.5.0 (2026-10-21), so cobertura | `main` | Cobertura gerada do codigo e travada no CI. Da 0.5.0: TJMG `cposg`, TJPE `cpopg`, TRF3 `cjsg`, agregador Falcao; PDPJ recusa token vencido |
| 1.3.1 | 0.4.0 (2026-09-15) + `main` | `5ebde28` (main) | Correcao: `comarca`, `tipo_decisao` e `count_only` valem para toda a familia eSAJ, e nao so para o TJSP |
| 1.3.0 | 0.4.0 (2026-09-15) + `main` | `5ebde28` (main) | Primeira publicacao depois da 1.1.0 (a 1.2.0 ficou so em branch, nunca publicada, e foi fundida aqui). Da 0.4.0: +TRF1/TRF3/TRF5/TRF6 (`cpopg`; TRF6 via eproc/`txtcaptcha`), `download_pecas`/`diretorio` em TRF1/TRF3/TRF5, +PDPJ, +STF (`listar_decisoes`/`contar_decisoes`, extra `stf`); `count_only=True` em eSAJ/TJSP; `listar_classes`/`listar_assuntos`/`listar_orgaos`/`listar_varas`; migracao para `HTTPScraper` + `RetryExhaustedError`; singulares `classe`/`assunto`/`vara`; JusBR com `auth(exp)`, coluna `processo` e validacao em `download_documents`; excecoes anti-bot (`BotChallengeBlockedError`, `TJAPSecurityCheckError`); `pyarrow` fora das dependencias base; contrato de `paginas` validado antes do HTTP; Datajud respeita `range(3, 6)`. `[unreleased]`: STF com `checkpoint_dir`/`resume` e coleta integral acima de 10.000 registros |
| 1.1.0 | 0.3.0 (2026-05-03) + `main` | `6c5703d` (2026-05-13) | Na skill: +TJGO, +TJMG, +TJRJ (na biblioteca desde a 0.2.1). Da 0.3.0: extra `[tjmg]` (`[v0.3.0+, requer extra tjmg]`), +ComunicaCNJ; `tamanho_pagina` canonico; pydantic `extra="forbid"` nos endpoints wired; auto-chunk eSAJ. Da `main` em `6c5703d`, publicados so na 0.4.0: +TRF1/TRF3/TRF5, +PDPJ, migracao para `HTTPScraper` + `RetryExhaustedError`, singulares `classe`/`assunto`/`vara` (TJSP `cjpg`, TJBA, Datajud) |
| 1.0.0 | ~0.1.x — 0.2.x | — | 22 tribunais estaduais (TJSP, TJRS, TJPR, TJDFT, TJBA, TJCE, TJES, TJMT, TJPA, TJPB, TJPE, TJPI, TJRN, TJRO, TJRR, TJSC, TJTO, TJAC, TJAL, TJAM, TJAP, TJMS) + Datajud + JusBR |

## Vocabulario de tags

Ao longo das references, recursos novos ganham tags inline:

| Tag | Significado | Acao para o usuario |
|---|---|---|
| (sem tag) | Disponivel desde versoes antigas (v0.1.x/v0.2.x), estavel no PyPI | `pip install juscraper` resolve |
| `[v0.3.0+]` | Adicionado na v0.3.0 (estavel no PyPI hoje) | `pip install juscraper>=0.3.0` |
| `[v0.3.0+, requer extra tjmg]` | Estavel no PyPI, mas requer dependencia extra | `pip install 'juscraper[tjmg]>=0.3.0'` |
| `[v0.4.0+]` | Adicionado na v0.4.0 (PyPI, 2026-09-15) | `pip install -U 'juscraper>=0.4.0'` |
| `[v0.5.0+]` | Adicionado na v0.5.0 (PyPI, 2026-10-21) | `pip install -U 'juscraper>=0.5.0'` |
| `[unreleased]` | So na `main` do repositorio, posterior a ultima release do PyPI (ver §Alinhamento atual) | `pip install "git+https://github.com/jtrecenti/juscraper.git"` (com extra: `pip install "juscraper[stf] @ git+https://github.com/jtrecenti/juscraper.git"`) |

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
cd juscraper   # clone local do repositorio
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
grep -hoE "'(tj[a-z]+|trf[0-9]+|stf|datajud|jusbr|pdpj|comunica_cnj)'" \
  plugins/juscraper/skills/juscraper/SKILL.md \
  plugins/juscraper/skills/juscraper/references/*.md | sort -u
# Diff manual entre as duas saidas
```

## Decisoes de escopo registradas

- A skill cobre a ultima release publicada do `juscraper` (hoje a 0.5.0, revista em parte; ver §Alinhamento atual); o default e `pip install -U juscraper` ou `uv add -U juscraper`. O que so existe na `main` entra com `[unreleased]` e instalacao via `git+https://github.com/jtrecenti/juscraper.git`; ao sair nova release, essas tags viram `[v0.X.0+]`.
- TRF1/TRF3/TRF5/TRF6, PDPJ e STF sao `[v0.4.0+]`; a coleta integral e o checkpoint do STF, `[v0.5.0+]`.
- A arvore de assuntos do TJSP (`references/assuntos-tjsp.json`) foi coletada em 2026-04-16 e nao precisa ser re-coletada a cada bump da skill — a Tabela Processual Unificada do CNJ muda lentamente. Re-coletar so quando aparecer divergencia reportada por usuario ou pesquisa que use codigo desconhecido.
