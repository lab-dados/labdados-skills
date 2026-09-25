# Modelos Pydantic: padrões para dataframeit

Este arquivo cobre **como desenhar o modelo Pydantic** que você passa para `dataframeit()`. A qualidade da extração depende mais do desenho do modelo do que do provedor LLM: um Pydantic bem escrito com um modelo pequeno supera um Pydantic mal escrito com um modelo grande.

## Índice

1. [Hierarquia de técnicas](#hierarquia-de-técnicas)
2. [Padrões de modelo](#padrões-de-modelo)
   - [Padrão 1: básico](#padrão-1-básico)
   - [Padrão 2: com Field(description=)](#padrão-2-com-fielddescription)
   - [Padrão 3: com json_schema_extra](#padrão-3-com-json_schema_extra)
   - [Padrão 4: campos condicionais (condition)](#padrão-4-campos-condicionais-condition)
3. [json_schema_extra: referência completa](#json_schema_extra-referência-completa)
4. [Operadores condicionais](#operadores-condicionais)
5. [Validação e nova tentativa](#validação-e-nova-tentativa)
6. [Campo de dificuldade (self-reflection)](#campo-de-dificuldade-self-reflection)

---

## Hierarquia de técnicas

Siga esta ordem; cada item rende mais que trocar de modelo:

1. **`Literal[...]`** para campos com valores conhecidos: reduz alucinações drasticamente. `Literal['civel', 'criminal']` é muito mais robusto que `str` com a descrição "cível ou criminal".
2. **`Field(description=...)`** para guiar o LLM: o investimento mais barato. Uma boa descrição ("Valor da causa em reais. None se não informado") melhora mais que trocar de provedor.
3. **`Optional[tipo]`** para campos que podem não existir: sem `Optional`, o LLM inventa um valor.
4. **`json_schema_extra`** para configuração por campo: prompt próprio, busca web dedicada, campos condicionais.
5. **Campos condicionais (`condition`)**: extrair `valor_multa` só se `tem_multa` for `True`. Economiza chamadas e melhora a coerência. Exige busca por campo (Padrão 4).
6. **Campo de dificuldade (self-reflection)**: pedir ao LLM que sinalize ambiguidade (última seção).

Nome de campo igual ao da coluna de texto levanta `ValueError`, porque a resposta sobrescreveria o texto de entrada.

---

## Padrões de modelo

### Padrão 1: básico

```python
from pydantic import BaseModel
from typing import Literal

class Sentimento(BaseModel):
    sentimento: Literal['positivo', 'negativo', 'neutro']
    confianca: Literal['alta', 'media', 'baixa']

resultado = dataframeit(df, Sentimento, "Analise o sentimento do texto: {texto}")
```

### Padrão 2: com Field(description=)

```python
from pydantic import BaseModel, Field
from typing import Optional

class Processo(BaseModel):
    numero_cnj: str = Field(description="Número do processo no formato CNJ")
    tribunal: str = Field(description="Sigla do tribunal (ex.: TJSP, TJRS)")
    classe: str = Field(description="Classe processual (ex.: Apelação Cível)")
    valor_causa: Optional[float] = Field(
        default=None,
        description="Valor da causa em reais. None se não informado",
    )
```

Descrições ambíguas são a causa número 1 de erros sistemáticos num campo.

### Padrão 3: com json_schema_extra

Configuração por campo: prompt próprio, busca web dedicada, profundidade e limite de busca específicos. **Só funciona com `use_search=True, search_per_field=True`**; fora desse modo, qualquer uma dessas chaves levanta `ValueError`.

```python
from pydantic import BaseModel, Field

class MedicamentoInfo(BaseModel):
    principio_ativo: str = Field(description="Princípio ativo do medicamento")

    doenca_rara: str = Field(
        description="Classificação de doença rara",
        json_schema_extra={
            "prompt": "Busque em Orphanet (orpha.net). Analise: {texto}",
        },
    )

    avaliacao_conitec: str = Field(
        description="Avaliação da CONITEC",
        json_schema_extra={
            "prompt_append": "Busque APENAS no site da CONITEC (gov.br/conitec).",
        },
    )

    estudos_clinicos: str = Field(
        description="Estudos clínicos relevantes",
        json_schema_extra={
            "prompt_append": "Busque estudos clínicos recentes.",
            "search_depth": "advanced",
            "max_results": 10,
            "max_search_calls": 3,
        },
    )

resultado = dataframeit(df, MedicamentoInfo, "Analise o medicamento: {texto}",
                        use_search=True, search_per_field=True)
```

As chaves da biblioteca saem do schema enviado ao LLM; só `description` e o tipo chegam a ele.

### Padrão 4: campos condicionais (condition)

Referência oficial: https://brunodcdo.com.br/dataframeit/examples/conditional-fields/.

```python
from pydantic import BaseModel, Field
from typing import Optional

class AnaliseMulta(BaseModel):
    tem_multa: bool = Field(description="O texto menciona aplicação de multa?")

    valor_multa: Optional[float] = Field(
        default=None,
        description="Valor da multa em reais",
        json_schema_extra={"condition": {"field": "tem_multa", "equals": True}},
    )

    fundamentacao: Optional[str] = Field(
        default=None,
        description="Fundamentação legal da multa",
        json_schema_extra={"condition": {"field": "tem_multa", "equals": True}},
    )

resultado = dataframeit(df, AnaliseMulta, "Analise: {texto}",
                        use_search=True, search_per_field=True)
```

**Quando a condição é avaliada.** Só com `use_search=True, search_per_field=True`, com ou sem `search_groups`: é o modo em que os campos saem em chamadas separadas. Fora dele, `condition` ou `depends_on` no modelo levanta `ValueError`. Campo com condição falsa fica `None` e não é pedido ao agente, nem gasta busca; por isso, declare-o como opcional com default `None`. Com `search_groups`, a condição de um campo agrupado é avaliada antes da chamada do grupo; se ela depende de outro campo do mesmo grupo, é avaliada com a resposta do grupo, e o campo com condição falsa fica `None`.

**Onde a condição pode ficar.** Só em campo de nível superior. `condition` ou `depends_on` num campo de modelo aninhado ou de item de lista levanta `ValueError` antes de processar, em qualquer modo. A condição pode **ler** um campo aninhado com notação de ponto (`"endereco.cidade"`), e a dependência derivada é o campo raiz.

**Ordem.** A ordem de declaração no modelo não importa: a biblioteca ordena os campos, e os grupos, pelas dependências. Entre campos independentes vale a ordem do modelo. Dependência circular (inclusive entre um grupo e um campo de fora dele) ou condição sobre campo inexistente levanta `ValueError` antes da primeira linha.

**`condition` callable e `depends_on`.** Com `condition` dict, a dependência vem do `field` da condição, e `depends_on` é dispensável. Quando a condição combina vários campos, use uma função que recebe os campos já preenchidos e devolve bool, e declare os campos lidos em `depends_on`; sem ele, a ordem não é garantida e a biblioteca emite aviso. `depends_on` sem `condition` não afeta a ordem e só emite aviso.

```python
class PedidoInfo(BaseModel):
    tipo_cliente: str = Field(description="Tipo do cliente: 'novo' ou 'vip'")
    valor_pedido: float = Field(description="Valor total do pedido")
    desconto: float | None = Field(
        default=None,
        description="Desconto aplicado",
        json_schema_extra={
            "depends_on": ["tipo_cliente", "valor_pedido"],
            "condition": lambda dados: (
                dados.get("tipo_cliente") == "vip"
                and (dados.get("valor_pedido") or 0) > 1000
            ),
        },
    )
```

**Depuração.** A ordem de execução e a avaliação de cada condição saem em DEBUG, e os campos pulados em INFO, nos loggers `dataframeit.conditional` e `dataframeit.agent`.

---

## json_schema_extra: referência completa

Chaves da biblioteca dentro de `json_schema_extra={}` no `Field()`. Todas exigem `use_search=True, search_per_field=True`.

| Chave | Tipo | Descrição |
|---|---|---|
| `prompt` | str | Substitui o prompt principal para este campo. Sem `{texto}`, o texto da linha é anexado ao fim |
| `prompt_replace` | str | Sinônimo de `prompt` (se os dois vierem, vale `prompt`) |
| `prompt_append` | str | Acrescenta texto ao fim do prompt principal para este campo |
| `search_depth` | `"basic"` \| `"advanced"` | Profundidade de busca deste campo (só Tavily) |
| `max_results` | int (1-20) | Resultados por busca deste campo |
| `max_search_calls` | int >= 1 | Buscas do agente deste campo |
| `condition` | dict \| callable | Condição para extrair o campo (operadores abaixo) |
| `depends_on` | list[str] \| str | Campos lidos por uma `condition` callable; dispensável com `condition` dict |

Nos overrides, só a ausência (`None`) cai no valor global; `max_results=0` ou `search_depth=''` levantam `ValueError`. Campo que está num grupo de `search_groups` não pode ter chave de busca própria.

### Formato da `condition` dict

```python
"condition": {
    "field": "nome_do_campo",    # campo a avaliar (aceita notação de ponto: "endereco.cidade")
    "equals": valor,             # ou um dos operadores abaixo
}
```

---

## Operadores condicionais

| Operador | Descrição | Exemplo |
|---|---|---|
| `equals` | Valor é igual | `{"field": "tipo", "equals": "criminal"}` |
| `not_equals` | Valor é diferente | `{"field": "tipo", "not_equals": "civel"}` |
| `in` | Valor está na lista | `{"field": "uf", "in": ["SP", "RJ", "MG"]}` |
| `not_in` | Valor não está na lista | `{"field": "uf", "not_in": ["AC", "RR"]}` |
| `exists` | Campo tem valor (não é None) | `{"field": "email", "exists": True}` |

---

## Validação e nova tentativa

Validadores próprios (`field_validator`, `model_validator`) valem na extração. Uma resposta que não passa na validação, ou que não é JSON válido, ganha nova tentativa dentro de `max_retries`. Nos providers do LangChain, essa tentativa leva ao modelo a resposta recusada e a lista de erros, cada um com o caminho do campo e o valor recusado, e pede correção. Os tokens das tentativas recusadas entram nas colunas da linha quando uma seguinte dá certo. Se todas falham, a linha fica `'error'` e `_error_details` diz o campo e a regra de cada erro.

Isso torna validadores um jeito barato de impor regras que `Literal` não expressa (soma de percentuais, datas coerentes), desde que a regra seja clara o bastante para o modelo corrigir.

---

## Campo de dificuldade (self-reflection)

Inclua um campo `dificuldade: Optional[str]` pedindo ao LLM que sinalize, em 1 ou 2 frases, quando a classificação foi difícil:

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class CodificacaoDecisao(BaseModel):
    area: Literal['civel', 'criminal', 'trabalhista', 'tributario']
    houve_reforma: Optional[bool] = None

    dificuldade: Optional[str] = Field(
        default=None,
        description="Sinalize em 1-2 frases se o caso tiver ambiguidade "
                    "relevante que tornou a classificação difícil; deixe "
                    "None quando a classificação foi clara.",
    )
```

**Para que serve** (técnica de self-reflection; Reflexion, Shinn et al. 2023):

1. **Diagnóstico do codebook**: se mais de 15% das linhas têm o campo preenchido, algum `Field(description=...)` está ambíguo.
2. **Sinal de qualidade por linha**: a distribuição indica a zona cinzenta do corpus.
3. **Primeiro passo da política de escalação de precisão**, antes de trocar para modelo caro: ler os textos sinalizados revela o que refinar.

**Custo muito baixo**: em codebooks bem calibrados, mais de 80% das linhas retornam `None`.

**Política de escalação de precisão em 5 passos** (antes de trocar de modelo): (1) refinar `Field(description=...)`; (2) acrescentar few-shot no prompt; (3) ler o campo `dificuldade` dos casos errados; (4) decompor o campo problemático em subcampos; (5) só então trocar de modelo, e **apenas naquele campo**, via `reprocess_columns=['campo']` com outro `provider`/`model`.
