# Exemplos ponta a ponta — raspe

Tres workflows realistas. Cada um mostra **instalacao → coleta → filtro/transformacao → export**. Adapte termos e paginas conforme o pedido do usuario.

## Exemplo 1 — Legislacao federal sobre um tema (Presidencia + Camara + Senado)

**Objetivo**: levantar o corpus de leis e proposicoes sobre "reforma tributaria" considerando a Presidencia, a Camara e o Senado, consolidar num DataFrame unico e salvar em parquet.

```python
import pandas as pd
import raspe

termo = "reforma tributaria"

# Coleta em cada fonte — comecamos com range pequeno para ver o volume
df_pres = raspe.presidencia().raspar(pesquisa=termo, paginas=range(1, 4))
df_cam  = raspe.camara().raspar(pesquisa=termo, paginas=range(1, 4))
df_sen  = raspe.senado().raspar(pesquisa=termo, paginas=range(1, 4))

# Normaliza coluna "link" para facilitar concat
df_pres = df_pres.rename(columns={"nome": "titulo", "descricao": "ementa"})
df_cam  = df_cam.rename(columns={"descricao": "ementa"})
df_sen  = df_sen.rename(columns={"link_norma": "link", "trecho_descricao": "ementa"})

# Adiciona coluna indicando a fonte
df_pres["fonte"] = "presidencia"
df_cam["fonte"]  = "camara"
df_sen["fonte"]  = "senado"

# Concatena (pandas preenche com NaN campos que so existem em uma das fontes)
df = pd.concat([df_pres, df_cam, df_sen], ignore_index=True)

# Snapshot da data da coleta (reprodutibilidade)
df["data_coleta"] = pd.Timestamp.today().isoformat()

# Salva
df.to_parquet("legislacao_reforma_tributaria.parquet")
print(df.groupby("fonte").size())
```

**Saida esperada**: dezenas a centenas de linhas por fonte. A coluna `termo_busca` fica preenchida com "reforma tributaria" em todas.

**Proximo passo com `dataframeit-skill`**: rodar um classificador que extraia (`tema_especifico`, `fase_processo`, `ano_provavel`) a partir de `ementa`.

## Exemplo 2 — Atos da ANVISA sobre dispositivo medico (Playwright + filtro por situacao)

**Objetivo**: coletar atos normativos vigentes da ANVISA sobre "dispositivo medico", separar revogados de vigentes e salvar em Excel.

```python
import pandas as pd
import raspe

# IMPORTANTE: ANVISA requer o extra [browser]. Se faltar:
#   pip install "raspe[browser] @ git+https://github.com/bdcdo/raspe.git"
#   python -m playwright install chromium

# Coleta (comecar com 3 paginas — cada pagina Playwright leva ~20s)
df = raspe.anvisa().raspar(termo="dispositivo medico", paginas=range(1, 4))

print(f"Total coletado: {len(df)}")
print(df["situacao"].value_counts(dropna=False))

# Filtra vigentes (a coluna 'situacao' vem com None quando o ato esta vigente,
# ou com um rotulo como 'Revogado'/'Revogado Tacitamente' quando nao)
vigentes = df[df["situacao"].isna()].copy()
revogados = df[df["situacao"].notna()].copy()

# Export
with pd.ExcelWriter("anvisa_dispositivo_medico.xlsx") as w:
    vigentes.to_excel(w, sheet_name="vigentes", index=False)
    revogados.to_excel(w, sheet_name="revogados", index=False)

print(f"Vigentes: {len(vigentes)} | Revogados: {len(revogados)}")
```

**Saida esperada**: coleta ~30-60 registros nas 3 primeiras paginas. Se o usuario pedir a colecao completa, ajuste para `paginas=None` (ate 100 paginas, ~30 min).

**Alerta**: se aparecer `DriverNotInstalledError` ou `BrowserError: Timeout`, consulte `references/playwright.md`.

## Exemplo 3 — Cobertura midiatica (Folha + NYT) com `dataframeit` depois

**Objetivo**: comparar como Folha e NYT cobriram "reforma tributaria" em 2024, extrair temas com um LLM e exportar em Excel.

```python
import os
import pandas as pd
import raspe

# NYT precisa de API key — obtenha em developer.nytimes.com/get-started
os.environ.setdefault("NYT_API_KEY", "sua-chave-aqui")

termo_pt = "reforma tributaria"
termo_en = "Brazil tax reform"

# Coleta
df_folha = raspe.folha().raspar(
    pesquisa=termo_pt,
    site="online",
    data_inicio="2024-01-01",
    data_fim="2024-12-31",
    paginas=range(1, 6),  # 5 paginas x 25 = ate 125 materias
)

df_nyt = raspe.nyt().raspar(
    texto=termo_en,
    data_inicio="2024-01-01",
    data_fim="2024-12-31",
    paginas=range(1, 6),  # 5 paginas x 10 = ate 50 artigos (NYT e mais lento por rate limit)
)

# Normaliza colunas
df_folha = df_folha.rename(columns={"link": "url", "resumo": "snippet"})
df_folha["veiculo"] = "Folha"

df_nyt = df_nyt[["titulo", "url", "data_publicacao", "resumo"]].rename(
    columns={"data_publicacao": "data", "resumo": "snippet"}
)
df_nyt["veiculo"] = "NYT"

df = pd.concat([df_folha, df_nyt], ignore_index=True)
df["data_coleta"] = pd.Timestamp.today().isoformat()
df.to_excel("cobertura_reforma_tributaria_2024.xlsx", index=False)
print(df.groupby("veiculo").size())
```

**Saida esperada**: ~50 materias da Folha, ~50 do NYT. A coleta da Folha leva ~1 min; a do NYT leva ~6 min (5 req/min x 5 paginas).

**Proximo passo com `dataframeit-skill`**: classificar cada materia em (`enfoque`, `stakeholder_principal`, `tom`). Passe `text_column="snippet"` explicitamente — o default de `dataframeit` usa a primeira coluna, que aqui e `titulo` e pode ser curta demais para classificacao.

```python
# Pseudo-codigo — veja dataframeit-skill para detalhes
from dataframeit import dataframeit
from pydantic import BaseModel, Field
from typing import Literal

class Classificacao(BaseModel):
    enfoque: Literal["economico", "politico", "juridico", "social"]
    tom: Literal["positivo", "neutro", "negativo", "ambiguo"] = Field(...)

df_enriquecido = dataframeit(
    df,
    Classificacao,
    "Leia a materia abaixo e classifique.\n\nTitulo: {titulo}\nResumo: {snippet}",
    text_column="snippet",
)
```

## Padrao recorrente: snapshot da coleta

Em todos os exemplos, vale adicionar `data_coleta`:

```python
df["data_coleta"] = pd.Timestamp.today().isoformat()
```

Sites mudam conteudo e layout ao longo do tempo. Registrar quando a coleta aconteceu e essencial para reprodutibilidade em pesquisa.
