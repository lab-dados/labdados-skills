# Exemplos de workflow completo

Tres workflows de ponta a ponta. Cada um exercita uma combinacao
diferente de features.

## Indice

1. [Exemplo 1 — Classificacao de sentimento](#exemplo-1--classificacao-de-sentimento)
2. [Exemplo 2 — Extracao com busca web e campos condicionais](#exemplo-2--extracao-com-busca-web-e-campos-condicionais)
3. [Exemplo 3 — Pipeline de producao (grande volume)](#exemplo-3--pipeline-de-producao-grande-volume)

---

## Exemplo 1 — Classificacao de sentimento

Tarefa minima: Pydantic simples com `Literal`, sem busca web, sem
paralelismo. Use como template para qualquer classificacao de campo
finito.

```python
import pandas as pd
from pydantic import BaseModel
from typing import Literal
from dataframeit import dataframeit

# 1. Definir esquema de saida
class Sentimento(BaseModel):
    sentimento: Literal['positivo', 'negativo', 'neutro']
    confianca: Literal['alta', 'media', 'baixa']

# 2. Carregar dados
df = pd.DataFrame({
    'texto': [
        'Produto excelente! Superou expectativas.',
        'Pessimo atendimento, nunca mais compro.',
        'Entrega ok, produto mediano.'
    ]
})

# 3. Executar
resultado = dataframeit(df, Sentimento, "Analise o sentimento do texto: {texto}")

# 4. Verificar
print(resultado[['texto', 'sentimento', 'confianca']])
total_tokens = (
    resultado['_input_tokens']
    + resultado['_output_tokens']
    + resultado.get('_reasoning_tokens', 0)
).sum()
print(f"Tokens totais: {total_tokens:,}")
```

---

## Exemplo 2 — Extracao com busca web e campos condicionais

Pydantic mais rico: `json_schema_extra` com `depends_on`/`condition`,
busca web com `search_groups` para economizar chamadas.

```python
import pandas as pd
from pydantic import BaseModel, Field
from typing import Optional
from dataframeit import dataframeit

# 1. Esquema com busca web e campos condicionais
class EmpresaInfo(BaseModel):
    nome_empresa: str = Field(description="Nome da empresa mencionada")
    setor: str = Field(description="Setor de atuacao da empresa")

    tem_dado_financeiro: bool = Field(
        description="O texto menciona dados financeiros?"
    )
    receita_anual: Optional[str] = Field(
        description="Receita anual (se disponivel)",
        json_schema_extra={
            "depends_on": ["tem_dado_financeiro"],
            "condition": {"field": "tem_dado_financeiro", "equals": True},
            "prompt_append": "Busque a receita mais recente.",
            "search_depth": "advanced"
        }
    )
    sede: Optional[str] = Field(
        description="Localizacao da sede",
        json_schema_extra={
            "prompt_append": "Busque a localizacao da sede."
        }
    )

# 2. Carregar dados
df = pd.DataFrame({
    'texto': [
        'A empresa XYZ reportou crescimento de 30% no ultimo trimestre.',
        'Startup ABC recebeu investimento serie A de R$ 50 milhoes.',
    ]
})

# 3. Executar com busca web e search groups
resultado = dataframeit(
    df, EmpresaInfo,
    "Analise a empresa mencionada: {texto}",
    use_search=True,
    search_groups={
        "financeiro": {
            "fields": ["receita_anual"],
            "search_depth": "advanced",
            "max_results": 5
        },
        "localizacao": {
            "fields": ["sede"],
            "search_depth": "basic"
        }
    }
)

# 4. Verificar
print(resultado[['nome_empresa', 'setor', 'receita_anual', 'sede']])
```

---

## Exemplo 3 — Pipeline de producao (grande volume)

Dataset grande (~milhares de linhas) com `read_df`, paralelismo,
`rate_limit_delay`, estimativa de custo previa, reprocessamento de
erros. Template para uso em producao.

```python
import pandas as pd
from pydantic import BaseModel, Field
from typing import Literal, Optional
from dataframeit import dataframeit, read_df

# 1. Carregar dataset grande
df = read_df('ementas_tjsp.parquet')
print(f"Total de linhas: {len(df):,}")

# 2. Definir esquema
class ClassificacaoEmenta(BaseModel):
    area: Literal['civel', 'criminal', 'trabalhista', 'tributario', 'outro']
    tema_principal: str = Field(description="Tema juridico principal da ementa")
    houve_reforma: Optional[bool] = Field(
        description="A decisao reformou a sentenca de 1o grau?"
    )

# 3. Estimar custo ANTES de executar
tokens_estimados = len(df) * 500  # ~500 tokens por ementa (estimativa)
custo_gemini = tokens_estimados / 1_000_000 * 0.50  # entrada + saida
print(f"Custo estimado (Gemini): ~${custo_gemini:.2f}")
# → Confirmar com o usuario antes de prosseguir

# 4. Executar com resume (retomavel) e paralelismo
resultado = dataframeit(
    df,
    ClassificacaoEmenta,
    "Classifique esta ementa judicial: {texto}",
    parallel_requests=5,
    rate_limit_delay=0.5,
    batch_size=100,                                 # checkpointing para runs longos
    checkpoint_path='classificacao_progresso.parquet',
)

# 5. Verificar erros
# `_dataframeit_status` pode nao existir se nenhuma linha falhou
status = resultado.get('_dataframeit_status', pd.Series(dtype=str))
erros = resultado[status == 'error']
print(f"Processados: {len(resultado) - len(erros):,} | Erros: {len(erros):,}")
total_tokens = (
    resultado['_input_tokens']
    + resultado['_output_tokens']
    + resultado.get('_reasoning_tokens', 0)
).sum()
print(f"Tokens totais: {total_tokens:,}")

# 6. Reprocessar erros se necessario
if len(erros) > 0:
    resultado.loc[status == 'error', '_dataframeit_status'] = None
    resultado_final = dataframeit(
        resultado, ClassificacaoEmenta,
        "Classifique esta ementa judicial: {texto}",
        parallel_requests=3,
        rate_limit_delay=1.0,  # mais conservador na segunda tentativa
    )
    resultado_final.to_parquet('classificacao_final.parquet')
```

Para detalhes de `batch_size`/`checkpoint_path`, `reprocess_columns`,
deteccao de truncamento de saida e perfis de paralelismo, veja
`runs-longos.md`.
