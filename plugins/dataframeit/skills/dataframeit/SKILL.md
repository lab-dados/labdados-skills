---
name: dataframeit
description: "Use esta skill para aplicar um LLM linha a linha em um DataFrame (pandas ou polars) com a biblioteca dataframeit: defina um modelo Pydantic com os campos desejados, escreva um prompt com placeholder {texto} e obtenha saída validada em escala. Cobre classificação e extração estruturada, preenchimento de campos faltantes, anotação automática para pesquisa empírica, categorização de respostas abertas, enriquecimento com busca web (Tavily/Exa), campos condicionais (condition), paralelismo com rate limit, checkpointing retomável em runs longos e escolha de provedor (OpenAI, Gemini, Anthropic, Groq, Mistral, Cohere, Claude Code, Codex). Acione sempre que o usuário falar em processar cada linha de um DataFrame com IA, enriquecer dados com LLM, extrair informação estruturada de texto, classificar respostas abertas, codificar decisões judiciais com LLM ou dataframeit, mesmo que não nomeie a biblioteca. Não use para raspagem de dados, revisão de literatura acadêmica ou chamadas LLM avulsas fora de um DataFrame."
---

# DataFrameIt

dataframeit é uma biblioteca Python para enriquecer DataFrames com LLMs. Você define um modelo Pydantic com os campos desejados, fornece um DataFrame com texto, e a biblioteca extrai informação estruturada e validada para cada linha.

- Repositório: https://github.com/bdcdo/dataframeit
- Documentação: https://brunodcdo.com.br/dataframeit/ (em inglês: https://brunodcdo.com.br/dataframeit/en/)

## Padrão básico (use isto para a maioria dos casos)

```python
from pydantic import BaseModel, Field
from typing import Literal
from dataframeit import dataframeit

class Sentimento(BaseModel):
    sentimento: Literal['positivo', 'negativo', 'neutro']
    confianca: Literal['alta', 'media', 'baixa']

resultado = dataframeit(df, Sentimento, "Analise o sentimento do texto: {texto}")
```

Três elementos: (1) uma **classe Pydantic** definindo o que extrair, (2) os **dados** como primeiro argumento, (3) um **prompt** com `{texto}` como placeholder.

Os defaults cobrem o caso comum: `provider='openai'`, resume habilitado e tracking de tokens. Sem `model`, cada provider usa o próprio modelo padrão, definido em `DEFAULT_MODELS` (`from dataframeit.core import DEFAULT_MODELS`); na OpenAI é o `gpt-6-luna`, que vem com raciocínio ligado. Para extração determinística, acrescente `model_kwargs={'reasoning_effort': 'none', 'temperature': 0}` (ver "Hiperparâmetros por modelo" abaixo).

### Gotcha: coluna de texto do DataFrame

Se `text_column=None` (padrão), o `dataframeit` **infere** a coluna de texto: DataFrames com uma única coluna usam-na direto; DataFrames com várias colunas procuram, nessa ordem, `texto`, `text`, `decisao`, `content`, `content_text`. Se nenhuma bater, a chamada levanta `ValueError`, então não há risco de usar em silêncio a coluna errada.

Mesmo assim, **prefira passar `text_column=...` explicitamente** em pipelines de produção: a inferência cobre convenções comuns, mas deixa de fora nomes próprios do dataset (ex.: `ementa`, `acordao`, `mensagem`). Detalhes em `references/api.md §Tipos de entrada aceitos`.

```python
resultado = dataframeit(df_cjpg, Modelo, "Analise: {texto}",
                        text_column="decisao")
```

## Antes de começar

Complete este checklist antes de qualquer chamada.

### 1. Instalação

1. `pip show dataframeit` ou `python -c "import dataframeit; print(dataframeit.__version__)"`.
2. Se não estiver instalado, instale com o extra do provedor desejado.
3. Python >= 3.10 obrigatório.

| Extra | Comando | Quando usar |
|---|---|---|
| `[openai]` | `pip install dataframeit[openai]` | Padrão, OpenAI (GPT) |
| `[google]` | `pip install dataframeit[google]` | Google Gemini |
| `[anthropic]` | `pip install dataframeit[anthropic]` | Anthropic (Claude) |
| `[groq]` | `pip install dataframeit[groq]` | Groq, alta taxa de tokens/s e custo baixo |
| `[claude-code]` | `pip install dataframeit[claude-code]` | `provider='claude_code'` (instala o `claude-agent-sdk`), ver `references/modelos-parametros.md §Claude Code` |
| `[codex]` | `pip install dataframeit[codex]` | `provider='codex'`, experimental (SDK Python oficial do Codex), ver `references/modelos-parametros.md §Codex`. Fica fora do `[all]` |
| `[all]` | `pip install dataframeit[all]` | OpenAI, Google, Anthropic, Groq, Claude Code, Tavily, Exa, polars e excel |
| `[search]` | `pip install dataframeit[openai,search]` | Busca web com Tavily |
| `[search-exa]` | `pip install dataframeit[openai,search-exa]` | Busca web com Exa |
| `[search-all]` | `pip install dataframeit[openai,search-all]` | Busca web com Tavily e Exa |
| `[polars]` | `pip install dataframeit[openai,polars]` | Entrada e saída em polars (traz `pyarrow`, que também serve ao checkpoint `.parquet`) |
| `[excel]` | `pip install dataframeit[openai,excel]` | Leitura e checkpoint em `.xlsx` via `openpyxl` |
| Outro provedor do LangChain | `pip install dataframeit langchain-mistralai` (ou `langchain-cohere` etc.) | Mistral, Cohere e qualquer provedor aceito pelo `init_chat_model` do LangChain. Não existem extras `[mistral]` nem `[cohere]`: o pip ignora extra inexistente com um aviso e o pacote de integração fica faltando |

### 2. Provedor de LLM (escolha um)

Cada provedor via LangChain requer uma API key numa variável de ambiente. O dataframeit repassa `provider` ao `init_chat_model` do LangChain, então os nomes válidos são os do LangChain. Verifique a chave nesta ordem: `echo $VARIAVEL`, depois o `.env` do projeto, depois se o usuário já a forneceu na conversa.

| Provedor | `provider=` | Variável de ambiente | Obtenção |
|---|---|---|---|
| OpenAI (padrão) | `'openai'` | `OPENAI_API_KEY` | https://platform.openai.com |
| Google Gemini | `'google_genai'` | `GOOGLE_API_KEY` | https://aistudio.google.com |
| Anthropic | `'anthropic'` | `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| Groq | `'groq'` | `GROQ_API_KEY` | https://console.groq.com |
| Cohere | `'cohere'` | `COHERE_API_KEY` | https://dashboard.cohere.com |
| Mistral | `'mistralai'` (não `'mistral'`) | `MISTRAL_API_KEY` | https://console.mistral.ai |
| **Claude Code** | `'claude_code'` | Login local do Claude Code, ou `ANTHROPIC_API_KEY`; `api_key` é ignorado | **Perguntar ao usuário primeiro** |
| **Codex (experimental)** | `'codex'` | `auth.json` criado pelo Codex CLI; `api_key` é recusado | **Perguntar ao usuário primeiro** |

Se nenhuma key estiver configurada, pergunte ao usuário:
> Para usar o dataframeit, você precisa de uma API key de um provedor LLM. A OpenAI é o padrão. Crie uma chave em https://platform.openai.com e salve como `OPENAI_API_KEY` no `.env` do projeto.

**`provider='claude_code'`**: delega as chamadas ao `claude-agent-sdk`, com a autenticação do Claude Code instalado na máquina. Não assuma como default: pergunte antes. Requisitos, aliases `'haiku'`/`'sonnet'`/`'opus'`, `model_kwargs` (`effort`, `max_turns`, `max_budget_usd`) e o custo informado no resumo estão em `references/modelos-parametros.md §Claude Code`.

**`provider='codex'`** (experimental): usa o SDK Python oficial do Codex e a credencial local do Codex CLI. Mesma regra: pergunte antes. Em `model_kwargs`, só `effort`. Detalhes em `references/modelos-parametros.md §Codex`.

Nenhum dos dois aceita `use_search=True`.

### 3. Hiperparâmetros por modelo (crítico para reprodutibilidade)

Os parâmetros aceitos variam por modelo, e não há regra universal. **Consulte `references/modelos-parametros.md` antes de configurar `model_kwargs`.** O essencial:

- O dataframeit não envia parâmetro de amostragem: o cliente recebe só o que vier em `model_kwargs`.
- Não passe `temperature` a modelo que a rejeita (Claude Sonnet 5 e Opus mais novos, GPT-6 com raciocínio ligado, série o, Gemini 3.5 Flash-Lite e 3.6 Flash ou mais novo): a chamada volta com erro 400, ou o parâmetro está deprecado.
- Nos modelos que aceitam, passe `temperature` (e `seed`, quando existir) explicitamente; sem isso vale o default do provedor, em geral maior que 0.

```python
resultado = dataframeit(
    df, Modelo, "...",
    provider='openai', model='gpt-6-luna',
    model_kwargs={'reasoning_effort': 'none', 'temperature': 0},   # GPT-6 Luna sem raciocínio
)
```

**Registrar sempre** (em pesquisa empírica): `provider`, `model`, `temperature`, `seed`, `top_p` (se alterado) e data. Sem isso, o pipeline não é reprodutível mesmo com o código disponível, porque modelos mudam em silêncio.

### 4. Busca web (opcional)

Só é necessária se a informação não está no texto (`use_search=True`). Funciona apenas com providers via LangChain.

- **Tavily** (padrão): `TAVILY_API_KEY`, https://tavily.com (1000 buscas/mês grátis)
- **Exa**: `EXA_API_KEY`, https://exa.ai

Instale o extra do buscador: `pip install dataframeit[openai,search]` para Tavily, `[openai,search-exa]` para Exa ou `[openai,search-all]` para os dois.

Com busca, cada linha é resolvida por um agente que decide quando buscar, com até `max_search_calls` buscas (padrão 10). Busca por campo (`search_per_field`), grupos (`search_groups`), limites por grupo e por campo, custos e rate limit estão em **`references/busca-web.md`**.

## Roteamento de decisão: como configurar?

### Passo 1: qual provedor?

**Regra**: para extração estruturada e classificação de campos finitos (o caso típico do dataframeit), **comece sempre com modelo pequeno**. Escale para modelo maior só depois de esgotar o refinamento de prompt, e mesmo assim **apenas no campo específico**, via `reprocess_columns`.

| Situação | Recomendação |
|---|---|
| **Default para qualquer extração/classificação** | Modelo pequeno: `provider='openai'` (`gpt-6-luna` sem raciocínio), `'google_genai'` (Gemini Flash ou Flash-Lite), `'anthropic'` (`claude-haiku-4-5`), `'groq'` (`openai/gpt-oss-20b` ou `-120b`), `'mistralai'` (Mistral Small) |
| Início rápido | `provider='openai'` sem `model`, o padrão da biblioteca. Desligue o raciocínio para extração |
| Já tem chave Anthropic | `provider='anthropic'` com `model='claude-haiku-4-5'`: o padrão do provider (`DEFAULT_MODELS`) não é modelo pequeno |
| **Alta vazão / latência mínima** (classificação em lote com modelo aberto) | `provider='groq'` |
| Campo específico em que o piloto mostra erro após refinar o prompt | Escalar **só naquele campo** via `reprocess_columns=['campo']` |
| Raciocínio livre (não extração), ex.: sumarizar argumentação | Modelo maior do mesmo provider, com o uso justificado |
| Usuário tem Claude Code ou Codex **e confirmou** a preferência | `provider='claude_code'` ou `'codex'` (ver `references/modelos-parametros.md`) |

Os modelos atuais, preços e o padrão de cada provider estão na página de provedores da documentação (https://brunodcdo.com.br/dataframeit/guides/providers/); as regras de parâmetro por família, em `references/modelos-parametros.md`.

**Não use como default**:

- **Modelos de raciocínio** (série o, GPT-5/GPT-6 com raciocínio ligado): não aceitam `temperature` e custam muito mais sem ganho em extração estruturada.
- **Modelos top-tier generalistas** (Claude Opus, GPT-6 Astra, Gemini Pro) como default para extração: custam 10 a 50 vezes mais sem acurácia mensurável a mais em campos finitos.

**Quando você ou o usuário acha que precisa de modelo maior**: na grande maioria dos casos, o problema está num `Field(description=...)` ambíguo ou em categorias sobrepostas, não no modelo. Aplique a política de escalação de precisão em 5 passos **antes** de trocar de modelo (ver `references/pydantic-patterns.md §Campo de dificuldade`).

### Passo 2: preciso de busca web?

| Situação | Configuração |
|---|---|
| A informação já está no texto do DataFrame | `use_search=False` (padrão) |
| A informação precisa ser buscada na internet | `use_search=True` |
| Cada campo precisa de busca diferente | `use_search=True, search_per_field=True` |
| Campos relacionados podem compartilhar busca | `use_search=True, search_per_field=True, search_groups={...}` |

Detalhes em **`references/busca-web.md`**.

### Passo 3: processamento paralelo?

| Volume | Recomendação |
|---|---|
| < 50 linhas | `parallel_requests=1` (padrão, sequencial) |
| 50-500 linhas | `parallel_requests=3` a `5` |
| > 500 linhas | `parallel_requests=5` a `10` e monitorar rate limit |
| > 1000 linhas | Acrescentar `batch_size=50-100, checkpoint_path='...'` para tolerar quedas |

`rate_limit_delay` é a pausa de cada worker depois de cada linha bem-sucedida, não um intervalo global: a taxa máxima é `parallel_requests × 60 / rate_limit_delay` requisições por minuto. Perfis, cálculo do delay e checkpointing em **`references/runs-longos.md`**.

## Consciência de custo (obrigatória)

Antes de executar `dataframeit()` em datasets grandes:

1. **Rode uma amostra** (`df.sample(30)`) e leia o resumo de estatísticas impresso ao fim, que mostra tokens e, com busca, créditos. Multiplique pela razão entre o tamanho do dataset e o da amostra. Sem amostra, estime `len(df)` linhas × ~500 tokens/linha × preço do provedor.
2. **`track_tokens=True` já é o padrão.** Depois da execução, some as colunas:
   ```python
   entrada = resultado['_input_tokens'].sum()
   saida = resultado['_output_tokens'].sum()
   print(f"Tokens usados: {entrada + saida:,}")
   ```
   Não existe coluna `_total_tokens`. Não some `_reasoning_tokens` nem `_cached_input_tokens` de novo: o primeiro já está contido em `_output_tokens`, e o segundo, em `_input_tokens`. Com `claude_code`, o resumo também mostra o custo em USD informado pelo SDK.
3. **Avise o usuário** se o dataset tiver mais de 1000 linhas. Mostre a estimativa de custo e peça confirmação antes de prosseguir.
4. **Use `resume=True`** (padrão) para não pagar de novo linhas já processadas depois de uma interrupção. Rodar de novo sobre uma saída sem erros, porém, reprocessa tudo (ver `references/runs-longos.md §Resume e reprocessamento`).
5. **Busca web custa extra.** Cada agente pode fazer até `max_search_calls` buscas, e com `search_per_field=True` há um agente por campo e por linha. Use `search_groups` e reduza `max_search_calls`. Ver `references/busca-web.md`.

Fórmulas de custo, detecção de truncamento de saída, perfis de paralelismo e trace em **`references/runs-longos.md`**.

## Projetando bons modelos Pydantic

A qualidade da extração depende mais do modelo Pydantic do que do provedor LLM. Hierarquia de técnicas (cada item rende mais que trocar de modelo):

1. **`Literal[...]`** para campos com valores conhecidos: reduz alucinações drasticamente.
2. **`Field(description=...)`** para guiar o LLM: o investimento mais barato.
3. **`Optional[tipo]`** para campos que podem não existir: sem `Optional`, o LLM inventa.
4. **`json_schema_extra`** para configuração por campo (prompt próprio, busca dedicada, campos condicionais).
5. **Campos condicionais (`condition`)**: extrair `valor_multa` só se `tem_multa` for `True`. Exigem `use_search=True, search_per_field=True`, com ou sem `search_groups`; fora desse modo, `condition` ou `depends_on` levanta `ValueError`.
6. **Campo de dificuldade (self-reflection)**: pedir ao LLM que sinalize ambiguidade, sinal valioso em pesquisa empírica.

Os 4 padrões de modelo, a referência de `json_schema_extra`, os operadores condicionais e a técnica de self-reflection (Reflexion, Shinn et al. 2023) estão em **`references/pydantic-patterns.md`**.

Uma resposta que não passa na validação do modelo Pydantic, inclusive em validadores próprios, ganha nova tentativa, e nos providers do LangChain essa tentativa leva ao modelo a resposta recusada e os erros por campo, pedindo correção.

## Recursos avançados (quando usar)

| Recurso | Quando usar | Onde ler mais |
|---|---|---|
| `use_search=True` | A informação não está no texto e precisa vir da web | `busca-web.md` |
| `search_per_field=True` | Cada campo precisa de fontes web diferentes | `busca-web.md` |
| `search_groups={...}` | 2+ campos podem compartilhar um agente de busca (exige `search_per_field=True`) | `busca-web.md` |
| `max_search_calls=N` | Limitar as buscas de cada agente (padrão 10; também por grupo e por campo) | `busca-web.md` |
| `save_trace="full"` | Depurar extrações inesperadas com busca | `runs-longos.md` |
| `reprocess_columns=[...]` | Corrigir campos específicos sem reprocessar tudo | `runs-longos.md` |
| `parallel_requests=N` | Dataset com 50+ linhas | `runs-longos.md` |
| `batch_size=N, checkpoint_path=...` | Runs longos tolerantes a queda | `runs-longos.md` |

## Colunas de controle no resultado

| Coluna | Descrição |
|---|---|
| `_dataframeit_status` | `'processed'`, `'error'` ou `None` (linha ainda não processada). **Removida quando nenhuma linha falhou e nenhuma registrou detalhe**; com retry, `_error_details` guarda `"Sucesso após N retry(s)"` e as duas colunas ficam. Confira `'_dataframeit_status' in resultado.columns` antes de filtrar |
| `_error_details` | Mensagem de erro, `"Sucesso após N retry(s)"` ou `"Texto ausente"`. Removida junto com a de status |
| `_input_tokens` | Tokens de entrada, incluindo os lidos de cache (com `track_tokens=True`, padrão) |
| `_cached_input_tokens` | Parcela de `_input_tokens` lida do cache do provedor |
| `_output_tokens` | Tokens de saída |
| `_reasoning_tokens` | Parcela de `_output_tokens` usada em raciocínio; `0` em modelos sem raciocínio |
| `_search_credits` | Créditos de busca gastos na linha. Só com `use_search=True` |
| `_trace`, `_trace_{campo}`, `_trace_{grupo}` | Trace do agente em JSON. Só com `save_trace` |

As colunas de token ficam nulas quando o provider não informa uso; quando informa o total mas não cache ou raciocínio, a parcela fica em zero. Linhas com texto vazio ou nulo não vão ao modelo: recebem status `'error'` e o detalhe `"Texto ausente"`.

## Workflow típico do agente

1. Leia este SKILL.md (feito).
2. Execute o checklist "Antes de começar" (instalação, provedor, API key).
3. Entenda o que o usuário quer extrair e mapeie para campos Pydantic.
4. Aplique o roteamento de decisão (provedor, busca web, paralelismo).
5. **Para tarefas simples** (classificação, extração básica sem busca web), o padrão básico do topo deste arquivo basta.
6. **Para tarefas avançadas** (busca web, campos condicionais, checkpointing etc.), consulte a reference temática (tabela abaixo).
7. Se o dataset tiver mais de 1000 linhas, rode uma amostra, estime o custo e confirme com o usuário.
8. Execute. Os defaults já incluem `resume=True` e `track_tokens=True`.
9. Verifique os erros, só se a coluna de status existir:
   ```python
   if '_dataframeit_status' in resultado.columns:
       erros = resultado[resultado['_dataframeit_status'] == 'error']
   ```
10. Para refazer as linhas com erro, limpe `_dataframeit_status` e `_error_details` delas e rode de novo: com `resume=True`, linha `'error'` fica como está (ver `references/runs-longos.md §Reprocessar linhas com erro`).

## Arquivos de referência

Cada reference é independente. Leia apenas quando a tarefa pedir.

| Arquivo | Consulte quando precisar de... |
|---|---|
| **`references/api.md`** | Assinatura completa de `dataframeit()`, tipos de entrada, estrutura de retorno, `read_df`/`normalize_value`/`get_complex_fields`, exceções exportadas, tratamento de erros e retry, gotchas críticos |
| **`references/pydantic-patterns.md`** | Os 4 padrões de modelo, referência de `json_schema_extra`, operadores condicionais, campo de dificuldade e política de escalação de precisão |
| **`references/busca-web.md`** | Tavily e Exa, `search_per_field`, `search_groups`, `max_search_calls`, custos, rate limit da busca |
| **`references/runs-longos.md`** | `parallel_requests`, `rate_limit_delay`, perfis, custo por provedor, resume, `batch_size`/`checkpoint_path`, truncamento de saída, trace |
| **`references/exemplos.md`** | 3 workflows completos (classificação de sentimento, extração com busca web e condicionais, pipeline de produção grande) |
| **`references/modelos-parametros.md`** | Hiperparâmetros aceitos por família de modelo, com §Claude Code e §Codex completos |

## Integração com outras skills

| Se o usuário... | Skill complementar |
|---|---|
| ...está codificando decisões judiciais brasileiras | Coleta via **juscraper** (scrapers de tribunais, Datajud, JusBR) |
| ...precisa de revisão de literatura acadêmica | **openalex** |
| ...precisa coletar dados de fontes oficiais ou da imprensa | **raspe** |
