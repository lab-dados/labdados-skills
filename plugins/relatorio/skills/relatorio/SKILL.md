---
name: relatorio
description: Gera relatórios em .docx (e Markdown) via Quarto com o template e a identidade visual da FGV/LabDados — header qmd com reference-doc, tema de gráficos plotnine FGV e o pós-processamento que aplica o stroke da última linha das tabelas. Use sempre que o usuário pedir "relatório", "gerar relatório", "relatório parcial/final", "relatório em docx", "relatório bonito/formatado", "passa isso pra docx", "monta um documento Word", "relatório executivo", "relatório acadêmico", ou quando apontar uma análise/notebook e quiser transformá-la num documento entregável. Prefira esta skill ao fluxo de docx padrão da Anthropic — os documentos saem com tipografia, paleta e tabelas consistentes. Não confundir com scrum-master (relatório semanal de gestão em HTML/PDF) nem com ata-reuniao (ata de reunião em Markdown).
---

# Relatório (Quarto + identidade FGV)

Você transforma uma análise (dados, notebook, anotações) num **relatório
entregável em `.docx`**, com a identidade visual da FGV/LabDados, usando
**Quarto**. O documento sai com tipografia institucional, paleta de cores
consistente, tabelas com fechamento correto e figuras padronizadas — bem acima
do docx genérico.

**Antes de qualquer coisa, leia `references/estilo.md`.** Ele define o padrão de
escrita, tabelas e figuras. O valor do relatório está na clareza: quem lê o
resumo já entende o essencial, e cada número aponta para uma tabela ou figura.

## O que entregar

- O **`.qmd`** (fonte do relatório, versionável).
- O **`.docx`** renderizado e **pós-processado** (com o stroke da última linha
  das tabelas).
- Opcionalmente o **`.md`** (gfm) para preview rápido / diff no git.

Ao final: mostre o caminho dos arquivos e um `git add` sugerido. **Não commite
sozinho** — quem controla o histórico é o usuário (mesmo princípio das skills
`scrum-master` e `ata-reuniao`), a menos que ele peça explicitamente.

## Pré-requisitos

- **Quarto** (`quarto --version`). Se faltar, avise e aponte
  <https://quarto.org/docs/get-started/>.
- Só se o relatório tiver **gráficos ou tabelas geradas em código**: Python com
  `pandas`, `plotnine`, `tabulate` (para `to_markdown`) e o engine `jupyter`
  (`jupyter`/`nbclient`). Relatórios só de prosa + tabelas em Markdown **não**
  precisam de Python — nesse caso remova `engine: jupyter` do header.

## Passo a passo

### 1. Preparar a pasta de trabalho

Defina onde o relatório vai morar (pasta do projeto, tipicamente `notebooks/`
ou `relatorios/`). Copie para lá os três assets do template:

```
cp assets/relatorio_template.qmd   <pasta>/<nome>.qmd
cp assets/_reference-fgv.docx      <pasta>/_reference-fgv.docx
cp assets/fgv_theme.py             <pasta>/fgv_theme.py     # só se houver gráficos
```

O `_reference-fgv.docx` **precisa** estar ao lado do `.qmd` na hora de
renderizar (o header aponta `reference-doc: _reference-fgv.docx`). O
`fgv_theme.py` só é necessário se houver chunks `{python}` com gráficos.

### 2. Escrever o conteúdo

Edite o `.qmd` seguindo `references/estilo.md` e a estrutura do template
(Resumo → Contexto → Métodos → Resultados → Conclusões → Próximas etapas).

- **Tabelas:** pipe tables Markdown ou `Markdown(df.to_markdown(index=False))`.
  Alinhe números à direita. Legenda com `{#tbl-rotulo}`; cite com `@tbl-rotulo`.
- **Figuras:** plotnine + `fgv_theme()` (importado de `fgv_theme`). Sem título
  embutido. Legenda em `#| fig-cap`; rótulo `#| label: fig-rotulo`; cite com
  `@fig-rotulo`.
- **Ajuste o header:** título, subtítulo. Mantenha os formatos `docx` + `gfm`.
  Se não houver Python, remova a linha `engine: jupyter` e o chunk de setup.

### 3. Renderizar

```
quarto render <nome>.qmd --to docx
quarto render <nome>.qmd --to gfm     # opcional, para preview/diff
```

Rode a partir da pasta onde está o `.qmd` (para achar o reference-doc e o
`fgv_theme.py`). Se o `.docx` der "permission denied", o arquivo está **aberto
no Word** — peça para fechar e tente de novo.

### 4. Pós-processar as tabelas (o stroke — NÃO PULE)

```
python scripts/fix_docx_tables.py <nome>.docx
```

Isto é o que diferencia o documento: o Pandoc deixa a **última linha das tabelas
sem borda inferior**. O script ativa o estilo de `lastRow` e iguala a borda
inferior da última linha à do cabeçalho (`sz=8`), além de zerar o espaçamento
vertical dentro das células. Sem esse passo, a tabela fica "aberta" embaixo —
é o erro mais comum e o motivo principal desta skill existir.

> Rode o script **depois** de cada render do `.docx` (o render sobrescreve o
> arquivo e desfaz o ajuste).

### 5. Entregar

Confira o `.docx` (idealmente abra para ver as tabelas fechadas e a tipografia).
Informe os caminhos e sugira o `git add`. Não commite sem o usuário pedir.

## Erros comuns

- **Última linha da tabela sem borda** → faltou o passo 4 (ou houve um novo
  render depois dele).
- **`permission denied` no `.docx`** → arquivo aberto no Word.
- **Fonte errada / sem Century Gothic** → o `_reference-fgv.docx` não estava ao
  lado do `.qmd`, ou foi usado outro reference-doc.
- **`No module named 'fgv_theme'`** → copie `fgv_theme.py` para a pasta do `.qmd`
  (ou ajuste o `sys.path` no chunk de setup).
- **`to_markdown` falha** → falta o pacote `tabulate`.

## Arquivos da skill

- `assets/relatorio_template.qmd` — esqueleto do relatório (header + exemplos de
  tabela e figura).
- `assets/_reference-fgv.docx` — reference-doc com tipografia, estilos de título,
  parágrafo e tabela da FGV.
- `assets/fgv_theme.py` — paleta de cores e `fgv_theme()` para gráficos plotnine.
- `scripts/fix_docx_tables.py` — pós-processamento das tabelas (stroke da última
  linha + espaçamento das células).
- `references/estilo.md` — guia de escrita e formatação. **Leia primeiro.**
