---
name: dataframeit
description: Enriquecer DataFrames com LLMs usando a biblioteca dataframeit. Use para extrair informacao estruturada de texto, classificar registros, preencher campos faltantes, anotacao automatica com Pydantic, analise de texto em escala, ETL com IA, processamento paralelo de grandes volumes, busca web por campo. Use esta skill sempre que o usuario mencionar enriquecer dados, extrair campos de texto, classificacao com LLM, modelo Pydantic para dados, processar DataFrame com IA, categorizar respostas abertas, pipeline de extracao, dataframeit, analise de sentimento com LLM, extrair informacao estruturada, ou qualquer tarefa envolvendo aplicar um LLM linha a linha sobre um DataFrame — mesmo que nao mencione explicitamente "dataframeit".
---

# DataFrameIt Skill

dataframeit e uma biblioteca Python para enriquecer DataFrames com Large Language Models.
Voce define um modelo Pydantic com os campos desejados, fornece um DataFrame com texto,
e a biblioteca extrai informacao estruturada e validada para cada linha.

- Repositorio: https://github.com/bdcdo/dataframeit
- Documentacao: https://brunodcdo.com.br/dataframeit/

## Padrao basico (use isto para a maioria dos casos)

```python
from pydantic import BaseModel, Field
from typing import Literal
from dataframeit import dataframeit

class Sentimento(BaseModel):
    sentimento: Literal['positivo', 'negativo', 'neutro']
    confianca: Literal['alta', 'media', 'baixa']

resultado = dataframeit(df, Sentimento, "Analise o sentimento do texto: {texto}")
```

Tres elementos: (1) uma **classe Pydantic** definindo o que extrair, (2) os **dados**
como primeiro argumento, (3) um **prompt** com `{texto}` como placeholder.
Os defaults ja cobrem o caso comum: Google Gemini, resume habilitado, tracking de tokens.

### Gotcha: coluna de texto do DataFrame

Por default, `dataframeit` usa **a primeira coluna** do DataFrame como
texto a enviar ao LLM. Se o seu DataFrame tem varias colunas e o texto
nao esta na primeira, PASSE `text_column="nome"` explicitamente — caso
contrario, o LLM recebe outra coluna (ex: um id) e produz saida-lixo.
Nao ha um erro visivel: as chamadas completam, mas os campos extraidos
sao aleatorios.

```python
# DataFrames do juscraper: a coluna de texto se chama 'decisao'.
resultado = dataframeit(df_cjpg, Modelo, "Analise: {texto}",
                        text_column="decisao")
```

Regra pratica: sempre que o DataFrame tiver >1 coluna e voce nao souber
de cor qual e a primeira, passe `text_column=...` explicitamente.

## Antes de comecar

Complete este checklist antes de qualquer chamada.

### 1. Instalacao

Verifique se `dataframeit` esta instalado:
1. `pip show dataframeit` ou `python -c "import dataframeit; print(dataframeit.__version__)"`
2. Se nao instalado, instale com o extra do provedor desejado (ver tabela abaixo).
3. Python >= 3.10 obrigatorio.

| Extra | Comando | Quando usar |
|---|---|---|
| `[google]` | `pip install dataframeit[google]` | Padrao — Google Gemini (mais barato) |
| `[openai]` | `pip install dataframeit[openai]` | OpenAI (GPT) |
| `[anthropic]` | `pip install dataframeit[anthropic]` | Anthropic (Claude) |
| `[cohere]` | `pip install dataframeit[cohere]` | Cohere |
| `[mistral]` | `pip install dataframeit[mistral]` | Mistral |
| Claude Code SDK | `pip install claude-agent-sdk` | Modo `provider='claude_code'` — usa tokens do plano Claude Code do usuario |
| `[all]` | `pip install dataframeit[all]` | Todos os provedores |
| `[search]` | `pip install dataframeit[google,search]` | Busca web (Tavily/Exa) |
| `[polars]` | `pip install dataframeit[google,polars]` | Suporte a Polars DataFrames |

### 2. Provedor de LLM (escolha um)

Cada provedor requer uma API key configurada como variavel de ambiente.
Verifique nesta ordem: `echo $VARIAVEL` → `.env` do projeto → usuario ja forneceu na conversa.

| Provedor | `provider=` | Variavel de ambiente | Obtencao |
|---|---|---|---|
| Google Gemini (padrao) | `'google_genai'` | `GOOGLE_API_KEY` | https://aistudio.google.com |
| OpenAI | `'openai'` | `OPENAI_API_KEY` | https://platform.openai.com |
| Anthropic | `'anthropic'` | `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| Cohere | `'cohere'` | `COHERE_API_KEY` | https://dashboard.cohere.com |
| Mistral | `'mistral'` | `MISTRAL_API_KEY` | https://console.mistral.ai |
| **Claude Code (plano)** | `'claude_code'` | — (usa sessao Claude Code) | Plano Claude Code ativo — **perguntar ao usuario primeiro** (ver §2a) |

Se nenhuma key estiver configurada, pergunte ao usuario:
> Para usar o dataframeit, voce precisa de uma API key de um provedor LLM.
> O Google Gemini e o padrao e mais barato. Crie uma chave em https://aistudio.google.com
> e salve como `GOOGLE_API_KEY` no `.env` do projeto.

### 2a. Modo Claude Code (`provider='claude_code'`) — requer confirmacao

Se voce esta rodando dentro do Claude Code e o usuario tem plano Claude Code
ativo (Pro/Max), `provider='claude_code'` e uma alternativa aos provedores
de API. Este modo delega as chamadas LLM ao `claude-agent-sdk` e consome
**tokens do plano do usuario** em vez de creditos de API. Zero custo
incremental de API, mas consome quota do plano.

**NAO assumir como default.** Antes de configurar, faca a pergunta:

> "Para a codificacao via LLM, voce prefere: (a) usar tokens do seu plano
> Claude Code via `provider='claude_code'` (zero custo de API, consome
> quota do plano), ou (b) pagar via API tradicional com um provedor
> especifico (Gemini/OpenAI/Anthropic)?"

Alguns usuarios preferem (b) por razoes de billing (separar custos de
desenvolvimento de custos de pipelines de dados). Outros preferem (a)
por aproveitar melhor o plano.

**Requisitos** do modo `claude_code`:
- `pip install claude-agent-sdk`
- Rodar dentro de um ambiente Claude Code com subscription ativa
- Nao suporta `use_search=True` (para busca web, use `google_genai`/`openai`)

**Exemplo**:
```python
resultado = dataframeit(
    df, Codificacao, "Codifique: {texto}",
    provider='claude_code',
    model='claude-haiku-4-5-20251001',   # ou claude-sonnet-4-6 / claude-opus-4-7
)
```

**Defaults de protecao de custo**: `max_turns=1`, `max_budget_usd=0.50`
por linha. Ajuste via `model_kwargs={'max_budget_usd': N, 'max_turns': M}`
quando a codificacao exigir raciocinio mais longo.

### 3. Hiperparametros por modelo (critico para reprodutibilidade)

Os parametros aceitos variam por modelo — nao ha regra universal.
Consulte `references/modelos-parametros.md` antes de configurar.
Resumo operacional:

| Modelo | Config recomendada para extracao |
|---|---|
| **Gemini 3 Flash** | `{'temperature': 1.0, 'seed': 42}` — **nao reduzir temperature** (recomendacao Google) |
| **Claude Haiku 4.5 / Sonnet 4.6 / Opus 4.7** | `{'temperature': 0}` — Anthropic nao expoe `seed` oficial |
| **gpt-4o-mini / gpt-4.1-mini / gpt-4o** | `{'temperature': 0, 'seed': 42}` |
| **o1 / o3 / GPT-5 raciocinio** | **Nao aceita `temperature`** — nao usar para extracao |
| **Mistral Small / Large** | `{'temperature': 0, 'random_seed': 42}` |
| **Cohere Command R / R+** | `{'temperature': 0, 'seed': 42}` |
| **Gemini 2.5 Pro / Flash (legado)** | `{'temperature': 0, 'seed': 42}` |

Passar via `model_kwargs`:

```python
resultado = dataframeit(
    df, Modelo, "...",
    provider='google_genai', model='gemini-3.0-flash',
    model_kwargs={'temperature': 1.0, 'seed': 42},   # Gemini 3 Flash
)
```

**Registrar sempre**: `provider`, `model`, `temperature`, `seed`,
`top_p` (se alterado) e data. Sem isso, o pipeline nao e reprodutivel
mesmo com o codigo disponivel — modelos mudam silenciosamente.

### 4. Busca web (opcional)

So necessario se a tarefa exigir enriquecimento com dados da internet (`use_search=True`).

- **Tavily** (padrao): `TAVILY_API_KEY` — https://tavily.com (1000 buscas/mes gratis)
- **Exa**: `EXA_API_KEY` — https://exa.ai (mais economico em alto volume)

Instale o extra de busca: `pip install dataframeit[google,search]`

## Roteamento de decisao — como configurar?

### Passo 1: Qual provedor?

**Regra**: para extracao estruturada e classificacao de campos finitos
(caso de uso tipico do dataframeit), **comecar sempre com modelo
pequeno**. Escalar para modelo maior so apos esgotar refinamento de
prompt — e mesmo assim, **apenas naquele campo especifico**, via
`reprocess_columns`. Modelos de raciocinio (o1/o3/GPT-5 raciocinio)
nao se aplicam a extracao estruturada.

| Situacao | Recomendacao |
|---|---|
| **Default para qualquer extracao/classificacao** | Modelo pequeno: `provider='google_genai'` (Gemini 3 Flash), `'openai'` (gpt-4o-mini), `'anthropic'` (Claude Haiku 4.5), `'mistral'` (Mistral Small), `'cohere'` (Command R) |
| Inicio rapido / custo minimo | `provider='google_genai'` (Gemini 3 Flash) |
| Ecossistema OpenAI / ja tem key | `provider='openai'` com `model='gpt-4o-mini'` |
| Ja tem chave Anthropic | `provider='anthropic'` com `model='claude-haiku-4-5-20251001'` |
| Contexto muito longo (> 1M tokens no P95 do corpus) | Escalar para Gemini 1.5/2.5 Pro. Abaixo disso, modelos pequenos cobrem |
| Campo especifico onde piloto mostra erro apos refinamento de prompt | Escalar **so naquele campo** via `reprocess_columns=['campo']` com provider/model diferentes |
| Raciocinio livre (nao extracao) — ex: sumarizar argumentacao | Claude Sonnet 4.6 ou Opus 4.7 — justificar o uso |
| Usuario tem plano Claude Code **e confirmou** preferencia | `provider='claude_code'` (ver §2a) |

**NAO usar como default**:

- **Reasoning models** (o1, o3, o3-mini, GPT-5 raciocinio): nao aceitam
  `temperature` e custam 10-50× sem ganho em extracao estruturada.
  Reservar para raciocinio livre extenso. Ver
  `references/modelos-parametros.md` §OpenAI.
- **Modelos top-tier generalistas** (Opus 4.7, GPT-4o, Gemini 2.5 Pro)
  como default para extracao. Custam 10-50× sem acuracia mensuravel a
  mais em campos finitos.

**Quando voce ou o usuario acha que precisa de modelo maior**: na
grande maioria dos casos, o problema esta em `Field(description=...)`
ambigua ou categorias sobrepostas, nao no modelo. Aplique a politica
de escalacao de precisao em 5 passos **antes** de trocar de modelo:
refinar description → few-shot → adicionar campo de ambiguidade →
decompor campo → so entao trocar.

### Passo 2: Preciso de busca web?

| Situacao | Configuracao |
|---|---|
| Informacao ja esta no texto do DataFrame | `use_search=False` (padrao) |
| Informacao precisa ser buscada na internet | `use_search=True` |
| Cada campo precisa de busca diferente | `use_search=True, search_per_field=True` |
| Campos relacionados podem compartilhar busca | `use_search=True, search_groups={...}` |

### Passo 3: Processamento paralelo?

| Volume | Recomendacao |
|---|---|
| < 50 linhas | `parallel_requests=1` (padrao, sequencial) |
| 50-500 linhas | `parallel_requests=5` |
| > 500 linhas | `parallel_requests=10` + monitorar rate limit |

## Consciencia de custo — OBRIGATORIA

Antes de executar `dataframeit()` em datasets grandes:

1. **Estime o custo.** `len(df)` linhas × ~500 tokens/linha (estimativa conservadora) × preco do provedor.
2. **O `track_tokens=True` ja e o padrao** — apos a execucao, verifique:
   ```python
   total = resultado['_total_tokens'].sum()
   print(f"Tokens usados: {total:,}")
   ```
3. **Avise o usuario** se o dataset tiver mais de 1000 linhas. Mostre a estimativa de custo
   e peca confirmacao antes de prosseguir.
4. **Use `resume=True`** (padrao) para nao repagar linhas ja processadas em caso de interrupcao.
5. **Busca web custa extra.** Tavily: 1 credito/busca (basic) ou 2 creditos/busca (advanced).
   Com `search_per_field=True`, cada campo dispara uma busca separada por linha — o custo
   multiplica rapidamente. Use `search_groups` para agrupar campos e reduzir chamadas.
6. **Robustez a fim de tokens (truncamento de saida)**. Distinto do
   problema de contexto de **entrada**, o output pode ser truncado ao
   atingir `max_output_tokens`. Sinais: campos finais em branco,
   strings cortadas, listas aninhadas com contagem suspeita (sempre 5
   pedidos). O Pydantic pode passar na validacao se os campos
   obrigatorios foram preenchidos — o truncamento fica invisivel.

   **Deteccao e retry**:
   ```python
   LIMITE_OUTPUT = 2000   # ajustar ao model_kwargs['max_output_tokens']
   resultado['_trunc_suspeito'] = resultado['_output_tokens'] >= int(LIMITE_OUTPUT * 0.95)
   mascara_erro = resultado['_error_details'].fillna('').str.contains(
       'max_tokens|length_limit|stop_reason.*length', case=False, regex=True
   )

   precisa_retry = resultado[resultado['_trunc_suspeito'] | mascara_erro]

   if len(precisa_retry) > 0:
       resultado_fix = dataframeit(
           precisa_retry, Modelo, "...",
           reprocess_columns=[...],                           # so campos afetados
           model_kwargs={'max_output_tokens': 4000},          # dobrar limite
       )
   ```

   **Prevencao**: dimensione `max_output_tokens` com folga de 2× antes
   da rodada. Para Pydantic com ~8 campos + justificativa, ~800 tokens
   bastam; para `List[Pedido]` com ~3 pedidos medios, ~1500 tokens;
   com folga, 3000-4000.

Referencia de precos (aproximados, verificar no site do provedor):

| Provedor | Modelo default | Entrada (USD/1M) | Saida (USD/1M) |
|---|---|---|---|
| Google Gemini | gemini-3.0-flash | ~$0.10 | ~$0.40 |
| OpenAI | gpt-4o-mini | ~$0.15 | ~$0.60 |
| Anthropic | claude-haiku-4-5 | ~$1.00 | ~$5.00 |
| Mistral | mistral-small-latest | ~$0.20 | ~$0.60 |
| Cohere | command-r | ~$0.15 | ~$0.60 |

Precos mudam frequentemente. Consulte o site do provedor antes de estimar.

## Projetando bons modelos Pydantic

A qualidade da extracao depende mais do modelo Pydantic do que do provedor LLM.
Siga esta hierarquia de tecnicas:

1. **`Literal[...]`** para campos com valores conhecidos — reduz alucinacoes drasticamente.
2. **`Field(description=...)`** para guiar o LLM — e o investimento mais barato.
   Uma boa descricao ("Valor da causa em reais. None se nao informado") melhora mais
   que trocar de provedor.
3. **`Optional[tipo]`** para campos que podem nao existir — sem Optional, o LLM inventa.
4. **`json_schema_extra`** para customizacao avancada por campo — prompt proprio,
   busca web dedicada, campos condicionais. Ver `references/api.md` para todas as opcoes.
5. **Campos condicionais (`depends_on`)** — extrair "valor_multa" so se "tem_multa" for True.
   O campo-pai deve vir **antes** no modelo. Operadores: `equals`, `not_equals`, `in`, `not_in`, `exists`.
6. **Campo de ambiguidade/dificuldade** — incluir um campo
   `dificuldade: Optional[str]` pedindo ao LLM que sinalize, em 1-2
   frases, quando a classificacao foi dificil:

   ```python
   dificuldade: Optional[str] = Field(
       default=None,
       description="Sinalize em 1-2 frases se o caso tiver ambiguidade "
                   "relevante que tornou a classificacao dificil; deixe "
                   "None quando a classificacao foi clara."
   )
   ```

   **Para que serve** (tecnica self-reflection; Reflexion, Shinn et al.
   2023): (a) **diagnostico do codebook** — se > 15% das linhas tem o
   campo preenchido, algum Field description esta ambiguo; (b) **sinal
   de qualidade por linha** — distribuicao indica a "zona-cinza" do
   corpus; (c) **primeiro passo da politica de escalacao de precisao**
   antes de trocar para modelo caro — ler os textos sinalizados revela
   o que refinar. Custo muito baixo: em codebooks bem calibrados, >80%
   das linhas retornam None.

## Recursos avancados (quando usar)

| Recurso | Quando usar | Custo adicional |
|---|---|---|
| `use_search=True` | Informacao nao esta no texto, precisa buscar na web | Tavily: 1-2 creditos/busca |
| `search_per_field=True` | Cada campo precisa de fontes web diferentes | Multiplica buscas por campo |
| `search_groups={...}` | 2+ campos podem compartilhar uma busca | Reduz chamadas (economia) |
| `save_trace="full"` | Depurar extracoes inesperadas | Nenhum (apenas volume de dados) |
| `reprocess_columns=[...]` | Corrigir campos especificos sem reprocessar tudo | Tokens apenas dos campos |
| `parallel_requests=N` | Dataset com 50+ linhas | Nenhum (mesmo custo, mais rapido) |

## Colunas de controle no resultado

| Coluna | Descricao |
|---|---|
| `_dataframeit_status` | `"processed"` ou `"error"` — **a coluna e removida automaticamente quando nao ha erros**. Use `df.get("_dataframeit_status", pd.Series(dtype=str))` antes de filtrar. |
| `_error_details` | Mensagem de erro (se houver) |
| `_input_tokens` | Tokens de entrada (sempre presente, `track_tokens=True` por padrao) |
| `_output_tokens` | Tokens de saida |
| `_total_tokens` | Total de tokens |

## Workflow tipico do agente

1. Leia este SKILL.md (feito).
2. Execute o checklist "Antes de comecar" (instalacao, provedor, API key).
3. Entenda o que o usuario quer extrair — mapeie para campos Pydantic.
4. Aplique o roteamento de decisao (qual provedor, busca web, paralelismo).
5. **Para tarefas simples** (classificacao, extracao basica sem busca web):
   o padrao basico no topo deste arquivo e suficiente. Use-o diretamente.
6. **Para tarefas com busca web, campos condicionais, search_groups, ou configuracao avancada**:
   leia `references/api.md` para parametros exatos e exemplos detalhados.
7. Se o dataset tiver mais de 1000 linhas, estime o custo e confirme com o usuario.
8. Execute. Os defaults ja incluem `resume=True` e `track_tokens=True`.
9. Verifique `_dataframeit_status` para erros.
10. Se houver erros, use `reprocess_columns` para reprocessar apenas os campos falhos.

## Arquivos de referencia

- **`references/api.md`** — Referencia completa da API com indice navegavel.
  Consulte quando precisar de:
  - Assinatura completa da funcao (todos os ~25 parametros com tipos e defaults)
  - Exemplos detalhados de `json_schema_extra`, campos condicionais, `search_groups`
  - Configuracao de provedores e modelos padrao
  - Funcoes utilitarias (`read_df`, `normalize_value`, `normalize_complex_columns`)
  - Workflows completos (classificacao, busca web, pipeline de producao)
  - Gotchas criticos

  Para tarefas simples (classificacao, extracao basica), o padrao no topo deste
  SKILL.md e suficiente — nao precisa ler api.md.

- **`references/modelos-parametros.md`** — Matriz de hiperparametros
  aceitos por modelo (temperature, seed, top_p, max_output_tokens,
  reasoning_effort). Consulte quando configurar `model_kwargs`. Cobre
  Anthropic (Haiku 4.5, Sonnet 4.6, Opus 4.7), OpenAI (gpt-4o-mini,
  gpt-4.1-mini, o1/o3 raciocinio), Google (Gemini 3 Flash, 2.5 Pro),
  Mistral, Cohere. Inclui regras particulares: Gemini 3 Flash **nao
  reduzir temperature**; reasoning models nao aceitam temperature.

## Integracao com outras skills

| Se o usuario... | Skill complementar |
|---|---|
| ...esta codificando decisoes judiciais brasileiras | Coleta via **juscraper-skill** (scrapers de TJs + Datajud + JusBR) |
| ...precisa de revisao de literatura academica | **openalex-skill** |

**Nota especial para pesquisa empirica**: se o usuario tem plano Claude
Code (Pro/Max), pergunte se ele prefere usar `provider='claude_code'`
(consome tokens do plano) ou um provedor de API (custo separado). Ver §2a.

**Pattern de flagging de ambiguidade e politica de escalacao de
precisao**: em pesquisa empirica ou qualquer uso de dataframeit onde a
qualidade da classificacao importa, incluir sempre o campo
`dificuldade: Optional[str]` no Pydantic (ver §Projetando bons modelos
Pydantic, item 6). Para erros sistematicos em um campo, aplicar a
politica de escalacao em 5 passos — **antes** de trocar de modelo:
refinar Field description → few-shot → ler o campo de ambiguidade →
decompor campo → so entao trocar modelo (e apenas naquele campo, via
`reprocess_columns`).
