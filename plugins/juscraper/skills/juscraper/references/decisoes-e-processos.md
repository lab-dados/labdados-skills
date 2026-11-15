# Juntar decisoes aos metadados do processo (`cjpg`/`cjsg` + `cpopg`)

Leia quando a base de decisoes (`cjpg` ou `cjsg`) precisar de informacao sobre o
processo: valor da causa, partes, classe, foro, vara, data de distribuicao,
processo principal ou assuntos adicionais. Validado no TJSP com o juscraper 0.5.0.

## Quando preferir o merge a extrair do texto

Dado que esta nos metadados do processo sai do `cpopg`, nao de regex ou LLM sobre
o texto da decisao. O metadado vem do cadastro do
tribunal, e a extracao do texto erra, custa e pode nem achar o dado. O texto da
decisao fica para o que so existe nele, como o valor da condenacao ou o resultado.

A chave e o CNJ reduzido aos 20 digitos. A coluna do CNJ muda conforme o metodo:
`id_processo` no `cjpg` e no `cpopg`, `processo` no `cjsg`. No TJSP, a apelacao
do `cjsg` traz o numero do processo de origem, e o `cpopg` com ele devolve os
metadados do 1o grau. Agravo de instrumento e outros feitos originarios do 2o grau
tem numero proprio (terminado em `.8.26.0000`), que o `cpopg` nao acha: para eles,
e para os dados do recurso, use o `cposg` (no 0.5.0 ele volta vazio; ver
`tjsp.md`).

## Custo

Uma chamada do `cpopg` por processo: no TJSP (`method='html'`), de 0,6 a 0,7 s
cada, mais a pausa entre chamadas (`sleep_time` do construtor). Com pausa de 3 s,
mil processos levam cerca de uma hora. No juscraper 0.5.0, rode um processo por
vez: a busca do `cpopg` com lista de processos perde processos
(jtrecenti/juscraper#472, corrigido na `main` pelo #473, `[unreleased]`). Para
bases grandes, grave os resultados a cada lote para nao perder a coleta se ela
parar no meio.

## Exemplo

```python
import juscraper as jus
import pandas as pd

tjsp = jus.scraper("tjsp", sleep_time=3)  # pausa de 3 s em toda chamada deste scraper

sentencas = tjsp.cjpg(
    assunto="4829",  # atraso de voo
    data_julgamento_inicio="01/03/2025",
    data_julgamento_fim="31/03/2025",
    paginas=range(1, 2),
)
sentencas["cnj"] = sentencas["id_processo"].str.replace(r"\D", "", regex=True)
sentencas["data_decisao"] = pd.to_datetime(
    sentencas["data_disponibilizacao"], format="%d/%m/%Y"
)

# Uma linha por processo antes do merge: o mesmo processo pode ter varias decisoes.
processos = (
    sentencas.groupby("cnj")
    .agg(
        id_processo=("id_processo", "first"),
        n_decisoes=("cnj", "size"),
        primeira_decisao=("data_decisao", "min"),
    )
    .reset_index()
)

basicos, partes, falhas = [], [], []
for numero in processos["id_processo"]:
    try:
        resultado = tjsp.cpopg(numero)  # dict: basicos, partes, movimentacoes, peticoes_diversas
    except ValueError:  # processo nao achado ou nao baixado
        falhas.append(numero)
        continue
    basicos.append(resultado["basicos"])
    partes.append(resultado["partes"])

metadados = pd.concat(basicos, ignore_index=True)
metadados["cnj"] = metadados["id_processo"].str.replace(r"\D", "", regex=True)

base = processos.merge(
    metadados.drop(columns="id_processo"),
    on="cnj", how="left", validate="one_to_one", indicator=True,
)
assert (base["_merge"] == "both").all(), f"processos sem metadados: {falhas}"

# valor_acao vem como texto ("R$         20.000,00")
base["valor_causa"] = pd.to_numeric(
    base["valor_acao"].str.replace(r"[^\d,]", "", regex=True).str.replace(",", "."),
    errors="coerce",
)
# data_distribuicao vem como "19/05/2023 às 16:35 - Livre"
base["data_distribuicao"] = pd.to_datetime(
    base["data_distribuicao"].str[:10], format="%d/%m/%Y", errors="coerce"
)

# partes nao traz o CNJ; liga-se a basicos por file_path
tabela_partes = pd.concat(partes, ignore_index=True).merge(
    metadados[["file_path", "cnj"]], on="file_path", how="left", validate="many_to_one"
)
```

Se o `validate=` acusar CNJ repetido em `metadados` (o `cpopg` trouxe mais de uma
pagina para o mesmo numero, por exemplo um incidente), escolha a linha do processo
antes do merge.

## Armadilhas

1. **O mesmo processo com mais de uma decisao.** O `cjpg` traz decisoes, nao
   processos, e nem toda decisao e a sentenca de merito: num teste, 3 de 7
   processos tinham mais de uma decisao (um tinha 4). No merge, os metadados se
   copiam para cada decisao, e a soma de `valor_causa` conta o mesmo processo
   varias vezes. Saida: agregar por processo antes do merge, como no exemplo, ou,
   para manter uma linha por decisao,
   `sentencas.merge(metadados.drop(columns="id_processo"), on="cnj", how="left", validate="many_to_one", suffixes=("", "_cpopg"))`
   (`classe`, `assunto`, `foro` e `vara` existem dos dois lados) e deduplicar por
   `cnj` antes de somar. O `auto_chunk`
   deduplica por `id_processo` so entre janelas (ver `tjsp.md`); dentro de uma
   janela, ou num `pd.concat` manual por ano, a repeticao continua.
2. **Cumprimento de sentenca tem CNJ proprio.** Vem sem `valor_acao` e com a data
   de distribuicao do cumprimento, nao da acao. O CNJ da acao original fica em
   `processo_principal` (coluna de `basicos` que so existe se algum processo da
   coleta a tiver). Saida: para o valor da causa, chamar o `cpopg` do principal;
   para contar processos, decidir e registrar se cumprimento e acao contam como
   um so.
3. **A mesma empresa com grafias diferentes.** Numa amostra de 20 processos, 8
   companhias reas apareceram com 12 grafias. Saida: padronizar o nome em
   `tabela_partes` (minusculas, sem acento, sem pontuacao e sem "S.A."/"Ltda", e um
   dicionario de grafias para o resto) antes de agrupar por empresa. No juscraper
   0.5.0, `nome` pode vir com a advogada colada ("Delta Air Lines Advogada: ...");
   corte a partir de " Advogada:" antes de agrupar (corrigido na `main` pelo
   jtrecenti/juscraper#476, `[unreleased]`).
4. **Partes trazem nome de pessoa fisica.** Em todos os 20 processos havia ao
   menos uma pessoa fisica (o autor), alem de advogados e juiz. Saida (ver LGPD
   na `SKILL.md`): nao versionar nem publicar `tabela_partes`
   com nomes, mascarar ou descartar pessoa fisica antes de gravar e guardar so o
   necessario a pergunta (por exemplo, a empresa re).

## Limites do `cpopg` do TJSP no juscraper 0.5.0

`movimentacoes` vem vazia (jtrecenti/juscraper#428), e a situacao do processo
nao vem; os dois estao corrigidos na `main` pelo #476 (`[unreleased]`). Ate a
correcao chegar ao PyPI, a data da sentenca vem do `cjpg`
(`data_disponibilizacao`), nao das movimentacoes.
