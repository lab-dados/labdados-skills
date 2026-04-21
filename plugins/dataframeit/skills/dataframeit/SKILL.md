---
name: dataframeit
description: Use esta skill para aplicar um LLM linha a linha em um DataFrame (pandas ou polars) usando a biblioteca dataframeit: defina um modelo Pydantic com os campos desejados, escreva um prompt com placeholder {texto} e obtenha saida validada em escala. Cobre classificacao e extracao estruturada, preenchimento de campos faltantes, anotacao automatica para pesquisa empirica, categorizacao de respostas abertas, enriquecimento com busca web (Tavily/Exa), campos condicionais (depends_on), paralelismo com rate limit, checkpointing retomavel em runs longos, e escolha de provedor (Gemini, OpenAI, Anthropic, Groq, Mistral, Cohere, Claude Code). Acione sempre que o usuario falar em processar cada linha de um DataFrame com IA, enriquecer dados com LLM, extrair informacao estruturada de texto, classificar respostas abertas, codificar decisoes judiciais com LLM, pipeline ETL com IA, analise de sentimento em escala, anotacao automatica com Pydantic, dataframeit — mesmo que nao nomeie a biblioteca. Nao use para raspagem de dados, revisao de literatura academica ou chamadas LLM avulsas fora de um DataFrame.
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

Se `text_column=None` (padrao), o `dataframeit` **infere automaticamente** a coluna
de texto: DataFrames com uma unica coluna usam-na direto; DataFrames com varias colunas
procuram, nessa ordem, `texto`, `text`, `decisao`, `content`, `content_text`. Se
nenhuma bater, a chamada levanta `ValueError` — nao ha risco de usar silenciosamente
a coluna errada.

Mesmo assim, **prefira passar `text_column=...` explicitamente** em pipelines de
producao — a inferencia cobre convencoes comuns, mas deixa de fora nomes proprios
do seu dataset (ex: `ementa`, `acordao`, `mensagem`). Ver `references/api.md §Tipos
de entrada aceitos` para detalhes.

```python
resultado = dataframeit(df_cjpg, Modelo, "Analise: {texto}",
                        text_column="decisao")
```

## Antes de comecar

Complete este checklist antes de qualquer chamada.

### 1. Instalacao

Verifique se `dataframeit` esta instalado:
1. `pip show dataframeit` ou `python -c "import dataframeit; print(dataframeit.__version__)"`
2. Se nao instalado, instale com o extra do provedor desejado.
3. Python >= 3.10 obrigatorio.

| Extra | Comando | Quando usar |
|---|---|---|
| `[google]` | `pip install dataframeit[google]` | Padrao — Google Gemini (mais barato) |
| `[openai]` | `pip install dataframeit[openai]` | OpenAI (GPT) |
| `[anthropic]` | `pip install dataframeit[anthropic]` | Anthropic (Claude) |
| `[cohere]` | `pip install dataframeit[cohere]` | Cohere |
| `[mistral]` | `pip install dataframeit[mistral]` | Mistral |
| `[groq]` | `pip install dataframeit[groq]` | Groq — alta taxa de tokens/s e custo baixo |
| `[all]` | `pip install dataframeit[all]` | Todos os provedores |
| `[search]` | `pip install dataframeit[google,search]` | Busca web (Tavily/Exa) |
| `[polars]` | `pip install dataframeit[google,polars]` | Suporte a Polars DataFrames |
| `[excel]` | `pip install dataframeit[google,excel]` | Leitura/escrita de `.xlsx` via `openpyxl` |
| Claude Code SDK | `pip install claude-agent-sdk` | Modo `provider='claude_code'` — ver `references/modelos-parametros.md §Claude Code` |

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
| Groq | `'groq'` | `GROQ_API_KEY` | https://console.groq.com |
| **Claude Code (plano)** | `'claude_code'` | — (usa sessao Claude Code) | Plano Claude Code ativo — **perguntar ao usuario primeiro** |

Se nenhuma key estiver configurada, pergunte ao usuario:
> Para usar o dataframeit, voce precisa de uma API key de um provedor LLM.
> O Google Gemini e o padrao e mais barato. Crie uma chave em https://aistudio.google.com
> e salve como `GOOGLE_API_KEY` no `.env` do projeto.

**Modo `provider='claude_code'`**: delega as chamadas ao `claude-agent-sdk` e consome
tokens do plano Claude Code em vez de creditos de API. Nao assuma como default —
pergunte ao usuario antes. Detalhes completos (requisitos, aliases `'haiku'`/`'sonnet'`/`'opus'`,
parametros `effort`/`max_turns`/`max_budget_usd`, exemplo) em
`references/modelos-parametros.md §Claude Code`.

### 3. Hiperparametros por modelo (critico para reprodutibilidade)

Os parametros aceitos variam por modelo — nao ha regra universal.
**Consulte `references/modelos-parametros.md` antes de configurar `model_kwargs`.**
Resumo operacional:

| Modelo | Config recomendada para extracao |
|---|---|
| **Gemini 3 Flash** (`gemini-3-flash-preview`, default) | `{'temperature': 1.0, 'seed': 42}` — **nao reduzir temperature** (recomendacao Google) |
| **Claude Haiku 4.5 / Sonnet 4.6 / Opus 4.7** | `{'temperature': 0}` — Anthropic nao expoe `seed` oficial |
| **gpt-4o-mini / gpt-4.1-mini / gpt-4o** | `{'temperature': 0, 'seed': 42}` |
| **o1 / o3 / GPT-5 raciocinio** | **Nao aceita `temperature`** — nao usar para extracao |
| **Mistral Small / Large** | `{'temperature': 0, 'random_seed': 42}` |
| **Cohere Command R / R+** | `{'temperature': 0, 'seed': 42}` |
| **Gemini 2.5 Pro / Flash (legado)** | `{'temperature': 0, 'seed': 42}` |
| **Groq Llama 3.3 70B Versatile** | `{'temperature': 0, 'seed': 42}` |

```python
resultado = dataframeit(
    df, Modelo, "...",
    provider='google_genai', model='gemini-3-flash-preview',
    model_kwargs={'temperature': 1.0, 'seed': 42},   # Gemini 3 Flash
)
```

**Registrar sempre** (em pesquisa empirica): `provider`, `model`, `temperature`, `seed`,
`top_p` (se alterado) e data. Sem isso, o pipeline nao e reprodutivel mesmo com o codigo
disponivel — modelos mudam silenciosamente.

### 4. Busca web (opcional)

So necessario se a tarefa exigir enriquecimento com dados da internet (`use_search=True`).

- **Tavily** (padrao): `TAVILY_API_KEY` — https://tavily.com (1000 buscas/mes gratis)
- **Exa**: `EXA_API_KEY` — https://exa.ai (mais economico em alto volume)

Instale o extra: `pip install dataframeit[google,search]`.

Para configurar busca por campo (`search_per_field`), agrupar campos em `search_groups`,
custos detalhados e warnings de rate limit, consulte **`references/busca-web.md`**.

## Roteamento de decisao — como configurar?

### Passo 1: Qual provedor?

**Regra**: para extracao estruturada e classificacao de campos finitos
(caso de uso tipico do dataframeit), **comecar sempre com modelo pequeno**.
Escalar para modelo maior so apos esgotar refinamento de prompt — e mesmo
assim, **apenas naquele campo especifico**, via `reprocess_columns`.
Modelos de raciocinio (o1/o3/GPT-5 raciocinio) nao se aplicam a extracao
estruturada.

| Situacao | Recomendacao |
|---|---|
| **Default para qualquer extracao/classificacao** | Modelo pequeno: `provider='google_genai'` (Gemini 3 Flash), `'openai'` (gpt-4o-mini), `'anthropic'` (Claude Haiku 4.5), `'mistral'` (Mistral Small), `'cohere'` (Command R), `'groq'` (Llama 3.3 70B) |
| Inicio rapido / custo minimo | `provider='google_genai'` (Gemini 3 Flash) |
| Ecossistema OpenAI / ja tem key | `provider='openai'` com `model='gpt-4o-mini'` |
| Ja tem chave Anthropic | `provider='anthropic'` com `model='claude-haiku-4-5-20251001'` |
| **Alta vazao / latencia minima** (classificacao em lote com modelo aberto) | `provider='groq'` com `model='llama-3.3-70b-versatile'` |
| Contexto muito longo (> 1M tokens no P95 do corpus) | Escalar para Gemini 1.5/2.5 Pro |
| Campo especifico onde piloto mostra erro apos refinamento de prompt | Escalar **so naquele campo** via `reprocess_columns=['campo']` |
| Raciocinio livre (nao extracao) — ex: sumarizar argumentacao | Claude Sonnet 4.6 ou Opus 4.7 — justificar o uso |
| Usuario tem plano Claude Code **e confirmou** preferencia | `provider='claude_code'` (ver `references/modelos-parametros.md §Claude Code`) |

**NAO usar como default**:

- **Reasoning models** (o1, o3, o3-mini, GPT-5 raciocinio): nao aceitam
  `temperature` e custam 10-50× sem ganho em extracao estruturada.
  Reservar para raciocinio livre extenso. Ver
  `references/modelos-parametros.md §OpenAI`.
- **Modelos top-tier generalistas** (Opus 4.7, GPT-4o, Gemini 2.5 Pro)
  como default para extracao. Custam 10-50× sem acuracia mensuravel a
  mais em campos finitos.

**Quando voce ou o usuario acha que precisa de modelo maior**: na
grande maioria dos casos, o problema esta em `Field(description=...)`
ambigua ou categorias sobrepostas, nao no modelo. Aplique a politica
de escalacao de precisao em 5 passos **antes** de trocar de modelo —
ver `references/pydantic-patterns.md §Campo de dificuldade`.

### Passo 2: Preciso de busca web?

| Situacao | Configuracao |
|---|---|
| Informacao ja esta no texto do DataFrame | `use_search=False` (padrao) |
| Informacao precisa ser buscada na internet | `use_search=True` |
| Cada campo precisa de busca diferente | `use_search=True, search_per_field=True` |
| Campos relacionados podem compartilhar busca | `use_search=True, search_groups={...}` |

Detalhes de cada configuracao em **`references/busca-web.md`**.

### Passo 3: Processamento paralelo?

| Volume | Recomendacao |
|---|---|
| < 50 linhas | `parallel_requests=1` (padrao, sequencial) |
| 50-500 linhas | `parallel_requests=5` |
| > 500 linhas | `parallel_requests=10` + monitorar rate limit |
| > 1000 linhas | Adicionar `batch_size=50-100, checkpoint_path='...'` para tolerar quedas |

Detalhes de perfis (economico/equilibrado/rapido), `rate_limit_delay` e
checkpointing em **`references/runs-longos.md`**.

## Consciencia de custo — OBRIGATORIA

Antes de executar `dataframeit()` em datasets grandes:

1. **Estime o custo.** `len(df)` linhas × ~500 tokens/linha (estimativa conservadora) × preco do provedor.
2. **O `track_tokens=True` ja e o padrao** — apos a execucao, some as colunas:
   ```python
   entrada = resultado['_input_tokens'].sum()
   saida = resultado['_output_tokens'].sum()
   raciocinio = resultado.get('_reasoning_tokens', pd.Series([0])).sum()
   total = entrada + saida + raciocinio
   print(f"Tokens usados: {total:,}")
   ```
   Nao existe coluna `_total_tokens` — some `_input_tokens + _output_tokens + _reasoning_tokens`.
3. **Avise o usuario** se o dataset tiver mais de 1000 linhas. Mostre a estimativa de custo
   e peca confirmacao antes de prosseguir.
4. **Use `resume=True`** (padrao) para nao repagar linhas ja processadas em caso de interrupcao.
5. **Busca web custa extra.** Com `search_per_field=True`, cada campo dispara uma busca
   separada por linha — o custo multiplica rapidamente. Use `search_groups` para agrupar
   campos e reduzir chamadas. Ver `references/busca-web.md`.

Para fórmulas detalhadas de custo por provedor, deteccao de truncamento
de saida (campos finais em branco por `max_output_tokens`), perfis de
paralelismo e trace logging, consulte **`references/runs-longos.md`**.

## Projetando bons modelos Pydantic

A qualidade da extracao depende mais do modelo Pydantic do que do provedor LLM.
Hierarquia de tecnicas (cada item rende mais que trocar de modelo):

1. **`Literal[...]`** para campos com valores conhecidos — reduz alucinacoes drasticamente.
2. **`Field(description=...)`** para guiar o LLM — o investimento mais barato.
3. **`Optional[tipo]`** para campos que podem nao existir — sem Optional, o LLM inventa.
4. **`json_schema_extra`** para customizacao avancada por campo (prompt proprio, busca
   web dedicada, campos condicionais).
5. **Campos condicionais (`depends_on`)** — extrair `valor_multa` so se `tem_multa` for True.
6. **Campo de dificuldade (self-reflection)** — pedir ao LLM que sinalize ambiguidade;
   sinal valioso em pesquisa empirica.

Para os 4 padroes completos de modelo, referencia completa de `json_schema_extra`,
operadores condicionais e tecnica de self-reflection com citacao academica
(Reflexion, Shinn et al. 2023), consulte **`references/pydantic-patterns.md`**.

## Recursos avancados (quando usar)

| Recurso | Quando usar | Onde ler mais |
|---|---|---|
| `use_search=True` | Informacao nao esta no texto, precisa buscar na web | `busca-web.md` |
| `search_per_field=True` | Cada campo precisa de fontes web diferentes | `busca-web.md` |
| `search_groups={...}` | 2+ campos podem compartilhar uma busca | `busca-web.md` |
| `save_trace="full"` | Depurar extracoes inesperadas | `runs-longos.md` |
| `reprocess_columns=[...]` | Corrigir campos especificos sem reprocessar tudo | `runs-longos.md` |
| `parallel_requests=N` | Dataset com 50+ linhas | `runs-longos.md` |
| `batch_size=N, checkpoint_path=...` | Runs longos (> 1000 linhas) tolerantes a queda | `runs-longos.md` |

## Colunas de controle no resultado

| Coluna | Descricao |
|---|---|
| `_dataframeit_status` | `"processed"` ou `"error"` — **removida automaticamente quando nao ha erros**. Use `df.get("_dataframeit_status", pd.Series(dtype=str))` antes de filtrar. |
| `_error_details` | Mensagem de erro (se houver) |
| `_input_tokens` | Tokens de entrada (sempre presente com `track_tokens=True`, padrao) |
| `_output_tokens` | Tokens de saida |
| `_reasoning_tokens` | Tokens de raciocinio "invisiveis" (o1/o3, GPT-5 raciocinio, Claude adaptive thinking). `0` para modelos nao-raciocinio. |

Para o total, some `_input_tokens + _output_tokens + _reasoning_tokens`. Nao existe
coluna `_total_tokens` agregada.

## Workflow tipico do agente

1. Leia este SKILL.md (feito).
2. Execute o checklist "Antes de comecar" (instalacao, provedor, API key).
3. Entenda o que o usuario quer extrair — mapeie para campos Pydantic.
4. Aplique o roteamento de decisao (qual provedor, busca web, paralelismo).
5. **Para tarefas simples** (classificacao, extracao basica sem busca web):
   o padrao basico no topo deste arquivo e suficiente. Use-o diretamente.
6. **Para tarefas avancadas** (busca web, campos condicionais, checkpointing, etc.):
   consulte a reference tematica apropriada (ver tabela abaixo).
7. Se o dataset tiver mais de 1000 linhas, estime o custo e confirme com o usuario.
8. Execute. Os defaults ja incluem `resume=True` e `track_tokens=True`.
9. Verifique `_dataframeit_status` para erros.
10. Se houver erros, use `reprocess_columns` para reprocessar apenas os campos falhos.

## Arquivos de referencia

Cada reference e independente. Leia apenas quando a tarefa atual pedir.

| Arquivo | Consulte quando precisar de... |
|---|---|
| **`references/api.md`** | Assinatura completa de `dataframeit()` (todos os ~25 parametros), tipos de entrada aceitos, estrutura de retorno, `read_df`/`normalize_value`/`get_complex_fields`, tratamento de erros, 15 gotchas criticos |
| **`references/pydantic-patterns.md`** | Os 4 padroes de modelo (Basico, Field, json_schema_extra, condicionais), referencia completa de `json_schema_extra`, operadores condicionais (`equals`/`in`/`exists`/...), campo de dificuldade para self-reflection e politica de escalacao de precisao em 5 passos |
| **`references/busca-web.md`** | Tavily vs Exa, `search_per_field`, `search_groups` para agrupar campos, custos de busca, warnings de rate limit |
| **`references/runs-longos.md`** | `parallel_requests`, `rate_limit_delay`, perfis (economico/equilibrado/rapido), calculo de custo por provedor, resume, `batch_size`/`checkpoint_path`, deteccao de truncamento de saida e retry, trace logging |
| **`references/exemplos.md`** | 3 workflows completos de ponta a ponta (classificacao de sentimento, extracao com busca web + condicionais, pipeline de producao grande) |
| **`references/modelos-parametros.md`** | Matriz de hiperparametros aceitos por modelo (Anthropic, OpenAI, Google, Mistral, Cohere, Groq) com regras particulares; §Claude Code completo (requisitos, aliases, `model_kwargs`) |

Para tarefas simples (classificacao, extracao basica), o padrao no topo
deste SKILL.md e suficiente — nao precisa ler nenhuma reference.

## Integracao com outras skills

| Se o usuario... | Skill complementar |
|---|---|
| ...esta codificando decisoes judiciais brasileiras | Coleta via **juscraper-skill** (scrapers de TJs + Datajud + JusBR) |
| ...precisa de revisao de literatura academica | **openalex-skill** |
| ...esta desenhando um estudo empirico sobre jurisprudencia (codebook, amostragem, protocolo) | **jurimetria-skill** (o dataframeit entra na fase de codificacao) |
