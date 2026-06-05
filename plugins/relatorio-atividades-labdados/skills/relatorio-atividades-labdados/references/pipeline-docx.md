# Pipeline de renderização para .docx

> Versão condensada do fluxo da skill `relatorio`, adaptada para gerar vários
> relatórios (os detalhados por frente e o macro) na pasta `relatorios/` do repo `adm`.

## Pré-requisitos

- **Quarto** (`quarto --version`). Se faltar, avise e aponte
  <https://quarto.org/docs/get-started/>.
- **Python** com `pandas`, `plotnine`, `tabulate` (para `to_markdown`) e o engine
  `jupyter` (`jupyter`, `nbclient`).
- **Graphviz** para os diagramas estruturais: `pip install graphviz` mais o binário
  `dot` no PATH (ver `diagramas.md`).

## Passo a passo

### 1. Preparar a pasta de trabalho

Trabalhe dentro do repo `adm`, na pasta `relatorios/`. Copie os assets de apoio para
perto dos `.qmd` (o `reference-doc` e o tema precisam estar ao lado do `.qmd` na hora
do render):

```bash
mkdir -p <adm>/relatorios/.assets
cp <skill>/assets/_reference-fgv.docx <adm>/relatorios/.assets/
cp <skill>/assets/fgv_theme.py        <adm>/relatorios/.assets/
```

Renderize com o diretório de trabalho em `relatorios/` para que `reference-doc:
.assets/_reference-fgv.docx` e `from fgv_theme import ...` (com `.assets` no
`sys.path`, ou copiando o `fgv_theme.py` para junto do `.qmd`) resolvam. O caminho
mais simples e à prova de erro: copiar `_reference-fgv.docx` e `fgv_theme.py` para a
**mesma pasta** do `.qmd` e gitignorar esses dois (ver SKILL.md, passo de git).

### 2. Escrever os `.qmd`

Parta dos templates em `assets/`:

- `relatorio_frente_template.qmd` para cada relatório detalhado (um por frente).
- `relatorio_template.qmd` para o macro consolidado.

Siga `estilo.md` (linguagem simples, sem travessões). Preencha as seções com os dados
coletados, citando a fonte.

### 3. Renderizar

Para cada `.qmd`:

```bash
quarto render <nome>.qmd --to docx
quarto render <nome>.qmd --to gfm     # opcional, para preview e diff no git
```

O `--to gfm` gera um `.md` legível para versionar e revisar no git.

### 4. Pós-processar as tabelas (sempre)

Logo após cada render de docx:

```bash
python <skill>/scripts/fix_docx_tables.py <nome>.docx
```

O script aplica o stroke da última linha das tabelas e zera o espaçamento das células.
Pular esse passo deixa a última linha das tabelas sem fechamento. Refaça após **cada**
novo render, porque o render sobrescreve o docx.

### 5. Conferência rápida

- O docx abre e tem o índice, os títulos no estilo FGV e as tabelas fechadas.
- Os três diagramas aparecem no macro.
- O texto não tem travessões.

## Nomes de arquivo

É um **único relatório consolidado**. Use a data de geração (história completa, então
datar por mês faz sentido):

- `relatorios/AAAA-MM-relatorio-labdados.{qmd,docx,md}`.

O `title` dentro do `.qmd` é "LabDados: Relatório de Atividades e Prestação de Contas".
A estrutura segue a proposta executiva, com uma seção por frente e uma subseção por
projeto (ver SKILL.md, "O que entregar").
