# Exemplos de workflow completo

Três workflows de ponta a ponta. Cada um exercita uma combinação diferente de recursos.

## Índice

1. [Exemplo 1: classificação de sentimento](#exemplo-1-classificação-de-sentimento)
2. [Exemplo 2: extração com busca web e campos condicionais](#exemplo-2-extração-com-busca-web-e-campos-condicionais)
3. [Exemplo 3: pipeline de produção (grande volume)](#exemplo-3-pipeline-de-produção-grande-volume)

---

## Exemplo 1: classificação de sentimento

Tarefa mínima: Pydantic simples com `Literal`, sem busca web, sem paralelismo. Use como molde para qualquer classificação de campo finito.

```python
import pandas as pd
from pydantic import BaseModel
from typing import Literal
from dataframeit import dataframeit

# 1. Definir o esquema de saída
class Sentimento(BaseModel):
    sentimento: Literal['positivo', 'negativo', 'neutro']
    confianca: Literal['alta', 'media', 'baixa']

# 2. Carregar os dados
df = pd.DataFrame({
    'texto': [
        'Produto excelente! Superou expectativas.',
        'Péssimo atendimento, nunca mais compro.',
        'Entrega ok, produto mediano.',
    ]
})

# 3. Executar
resultado = dataframeit(df, Sentimento, "Analise o sentimento do texto: {texto}")

# 4. Verificar
print(resultado[['texto', 'sentimento', 'confianca']])
if '_dataframeit_status' in resultado.columns:   # só existe se alguma linha falhou ou registrou detalhe
    print(resultado.loc[resultado['_dataframeit_status'] == 'error', '_error_details'])
# _reasoning_tokens já está contido em _output_tokens
total_tokens = (resultado['_input_tokens'] + resultado['_output_tokens']).sum()
print(f"Tokens totais: {total_tokens:,}")
```

---

## Exemplo 2: extração com busca web e campos condicionais

Pydantic mais rico: `json_schema_extra` com `condition` e busca web por campo. As chaves de configuração por campo (`prompt`, `prompt_replace`, `prompt_append`, `search_depth`, `max_results`, `max_search_calls`) e as condicionais (`condition`, `depends_on`) exigem `use_search=True, search_per_field=True`; sem isso, `ValueError`.

```python
import pandas as pd
from pydantic import BaseModel, Field
from typing import Optional
from dataframeit import dataframeit

# 1. Esquema com busca web e campos condicionais
class EmpresaInfo(BaseModel):
    nome_empresa: str = Field(description="Nome da empresa mencionada")
    setor: str = Field(description="Setor de atuação da empresa")

    tem_dado_financeiro: bool = Field(
        description="O texto menciona dados financeiros?"
    )
    receita_anual: Optional[str] = Field(
        default=None,
        description="Receita anual (se disponível)",
        json_schema_extra={
            "condition": {"field": "tem_dado_financeiro", "equals": True},
            "prompt_append": "Busque a receita mais recente.",
            "search_depth": "advanced",
            "max_search_calls": 3,
        },
    )
    sede: Optional[str] = Field(
        default=None,
        description="Localização da sede",
        json_schema_extra={"prompt_append": "Busque a localização da sede."},
    )

# 2. Carregar os dados
df = pd.DataFrame({
    'texto': [
        'A empresa XYZ reportou crescimento de 30% no último trimestre.',
        'Startup ABC recebeu investimento série A de R$ 50 milhões.',
    ]
})

# 3. Executar com busca por campo: um agente por campo e por linha,
#    cada um com até max_search_calls buscas (padrão 10)
resultado = dataframeit(
    df, EmpresaInfo,
    "Analise a empresa mencionada: {texto}",
    use_search=True,
    search_per_field=True,
    max_search_calls=5,           # teto global; receita_anual usa o próprio (3)
)

# Para economizar, search_groups junta campos num agente só, e a condição
# continua valendo dentro dos grupos. Campo com prompt_append ou
# search_depth próprios, como receita_anual e sede, não pode entrar em
# grupo (ValueError): escolha entre configurar o campo ou o grupo.

# 4. Verificar
print(resultado[['nome_empresa', 'setor', 'receita_anual', 'sede', '_search_credits']])
```

Campo com condição falsa fica `None` e não gasta busca. Dependência circular ou condição sobre campo inexistente levanta `ValueError` antes da primeira linha.

---

## Exemplo 3: pipeline de produção (grande volume)

Dataset grande (milhares de linhas) com `read_df`, `text_column` explícita, paralelismo, `rate_limit_delay`, amostra para estimar custo, checkpoint e reprocessamento de erros. Molde para uso em produção.

```python
import pandas as pd
from pydantic import BaseModel, Field
from typing import Literal, Optional
from dataframeit import dataframeit, read_df

PROMPT = "Classifique esta ementa judicial: {texto}"
CONFIG = dict(
    text_column='ementa',                            # nome próprio do dataset: passar explícito
    provider='openai',
    model='gpt-6-luna',                              # fixar e registrar o modelo
    model_kwargs={'reasoning_effort': 'none', 'temperature': 0},
)

# 1. Carregar o dataset
df = read_df('ementas_tjsp.parquet')
print(f"Total de linhas: {len(df):,}")

# 2. Definir o esquema
class ClassificacaoEmenta(BaseModel):
    area: Literal['civel', 'criminal', 'trabalhista', 'tributario', 'outro']
    tema_principal: str = Field(description="Tema jurídico principal da ementa")
    houve_reforma: Optional[bool] = Field(
        default=None,
        description="A decisão reformou a sentença de 1º grau? None se não houver informação",
    )

# 3. Estimar o custo ANTES com uma amostra
amostra = dataframeit(df.sample(30, random_state=42), ClassificacaoEmenta, PROMPT, **CONFIG)
tokens_amostra = (amostra['_input_tokens'] + amostra['_output_tokens']).sum()
tokens_estimados = tokens_amostra * len(df) / 30
print(f"Tokens estimados para o dataset: {tokens_estimados:,.0f}")
# Aplicar o preço atual do modelo (página de provedores da documentação)
# e confirmar com o usuário antes de prosseguir

# 4. Executar com checkpoint e paralelismo (5 workers × 60 / 0,5 s = até 600 req/min)
resultado = dataframeit(
    df, ClassificacaoEmenta, PROMPT, **CONFIG,
    parallel_requests=5,
    rate_limit_delay=0.5,
    batch_size=100,
    checkpoint_path='classificacao_progresso.parquet',
)
# Se cair no meio: df = read_df('classificacao_progresso.parquet', ClassificacaoEmenta)
# e rodar a mesma chamada de novo (resume=True é o padrão)

# 5. Verificar e reprocessar erros
if '_dataframeit_status' in resultado.columns:
    mascara = resultado['_dataframeit_status'] == 'error'
    print(f"Erros: {mascara.sum():,}")
    print(resultado.loc[mascara, '_error_details'].value_counts().head())
    if mascara.any():
        resultado.loc[mascara, ['_dataframeit_status', '_error_details']] = None
        resultado = dataframeit(
            resultado, ClassificacaoEmenta, PROMPT, **CONFIG,   # mesma configuração da 1ª rodada
            parallel_requests=3,
            rate_limit_delay=1.0,                               # mais conservador na segunda passada
        )
else:
    print("Nenhuma linha falhou.")

total_tokens = (resultado['_input_tokens'] + resultado['_output_tokens']).sum()
print(f"Tokens totais: {total_tokens:,}")
resultado.to_parquet('classificacao_final.parquet')
# Não rode dataframeit de novo sobre esta saída se ela não tiver coluna de status:
# todas as linhas seriam reprocessadas e pagas outra vez.
```

Para `batch_size`/`checkpoint_path`, `reprocess_columns`, truncamento de saída e perfis de paralelismo, veja `runs-longos.md`.
