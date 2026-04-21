# Modelos Pydantic — padroes para dataframeit

Este arquivo cobre **como desenhar o modelo Pydantic** que voce passa
para `dataframeit()`. A qualidade da extracao depende mais do desenho
do modelo do que do provedor LLM — um Pydantic bem escrito com Gemini
Flash supera um Pydantic mal escrito com Opus.

## Indice

1. [Hierarquia de tecnicas](#hierarquia-de-tecnicas)
2. [Padroes de modelo](#padroes-de-modelo)
   - [Padrao 1 — Basico](#padrao-1--basico)
   - [Padrao 2 — Com Field(description=)](#padrao-2--com-fielddescription)
   - [Padrao 3 — Com json_schema_extra](#padrao-3--com-json_schema_extra)
   - [Padrao 4 — Campos condicionais (depends_on)](#padrao-4--campos-condicionais-depends_on)
3. [json_schema_extra — referencia completa](#json_schema_extra--referencia-completa)
4. [Operadores condicionais](#operadores-condicionais)
5. [Campo de dificuldade (self-reflection)](#campo-de-dificuldade-self-reflection)

---

## Hierarquia de tecnicas

Siga esta ordem — cada item rende mais que trocar de modelo:

1. **`Literal[...]`** para campos com valores conhecidos — reduz
   alucinacoes drasticamente. `Literal['civel', 'criminal']` e muito
   mais robusto que `str` com descricao "civel ou criminal".
2. **`Field(description=...)`** para guiar o LLM — e o investimento
   mais barato. Uma boa descricao ("Valor da causa em reais. None se
   nao informado") melhora mais que trocar de provedor.
3. **`Optional[tipo]`** para campos que podem nao existir — sem
   `Optional`, o LLM inventa um valor.
4. **`json_schema_extra`** para customizacao avancada por campo:
   prompt proprio, busca web dedicada, campos condicionais.
5. **Campos condicionais (`depends_on`)** — extrair `valor_multa` so
   se `tem_multa` for `True`. Economiza tokens e melhora coerencia.
6. **Campo de dificuldade (self-reflection)** — pedir ao LLM que
   sinalize ambiguidade; ver ultima secao deste arquivo.

---

## Padroes de modelo

### Padrao 1 — Basico

```python
from pydantic import BaseModel
from typing import Literal

class Sentimento(BaseModel):
    sentimento: Literal['positivo', 'negativo', 'neutro']
    confianca: Literal['alta', 'media', 'baixa']

resultado = dataframeit(df, Sentimento, "Analise o sentimento do texto: {texto}")
```

Use `Literal` para restringir valores. Use `Optional[str]` para campos
que podem nao existir no texto.

### Padrao 2 — Com Field(description=)

```python
from pydantic import BaseModel, Field
from typing import Optional

class Processo(BaseModel):
    numero_cnj: str = Field(description="Numero do processo no formato CNJ")
    tribunal: str = Field(description="Sigla do tribunal (ex: TJSP, TJRS)")
    classe: str = Field(description="Classe processual (ex: Apelacao Civel)")
    valor_causa: Optional[float] = Field(
        description="Valor da causa em reais. None se nao informado"
    )
```

`Field(description=...)` e o investimento mais barato para melhorar a
qualidade da extracao. Descricoes ambiguas sao a causa #1 de erros
sistematicos em um campo.

### Padrao 3 — Com json_schema_extra

Configuracao por campo: prompt proprio, busca web dedicada, profundidade
de busca especifica.

```python
from pydantic import BaseModel, Field

class MedicamentoInfo(BaseModel):
    principio_ativo: str = Field(description="Principio ativo do medicamento")

    doenca_rara: str = Field(
        description="Classificacao de doenca rara",
        json_schema_extra={
            "prompt": "Busque em Orphanet (orpha.net). Analise: {texto}"
        }
    )

    avaliacao_conitec: str = Field(
        description="Avaliacao da CONITEC",
        json_schema_extra={
            "prompt_append": "Busque APENAS no site da CONITEC (gov.br/conitec)."
        }
    )

    estudos_clinicos: str = Field(
        description="Estudos clinicos relevantes",
        json_schema_extra={
            "prompt_append": "Busque estudos clinicos recentes.",
            "search_depth": "advanced",
            "max_results": 10
        }
    )
```

Para as chaves suportadas em `json_schema_extra`, veja a proxima secao.

### Padrao 4 — Campos condicionais (depends_on)

```python
from pydantic import BaseModel, Field
from typing import Optional

class AnaliseMulta(BaseModel):
    tem_multa: bool = Field(description="O texto menciona aplicacao de multa?")

    valor_multa: Optional[float] = Field(
        description="Valor da multa em reais",
        json_schema_extra={
            "depends_on": ["tem_multa"],
            "condition": {"field": "tem_multa", "equals": True}
        }
    )

    fundamentacao: Optional[str] = Field(
        description="Fundamentacao legal da multa",
        json_schema_extra={
            "depends_on": ["tem_multa"],
            "condition": {"field": "tem_multa", "equals": True}
        }
    )
```

O campo-pai (`tem_multa`) deve ser definido **antes** dos campos-filhos
no modelo — se invertido, a condicao nao funciona.

---

## json_schema_extra — referencia completa

Chaves suportadas dentro de `json_schema_extra={}` no `Field()`:

| Chave | Tipo | Descricao |
|---|---|---|
| `prompt` | str | Substitui o prompt principal para este campo. Usa `{texto}` como placeholder |
| `prompt_append` | str | Adiciona texto ao final do prompt principal para este campo |
| `search_depth` | `"basic"` \| `"advanced"` | Profundidade de busca web para este campo |
| `max_results` | int (1-20) | Max resultados de busca para este campo |
| `depends_on` | list[str] \| str | Campo(s) que devem ser extraidos antes deste |
| `condition` | dict | Condicao para extrair este campo (ver operadores abaixo) |

### Formato da `condition`

```python
"condition": {
    "field": "nome_do_campo",    # campo a avaliar (suporta dot notation: "endereco.cidade")
    "equals": valor              # OU um dos operadores abaixo
}
```

---

## Operadores condicionais

| Operador | Descricao | Exemplo |
|---|---|---|
| `equals` | Valor e igual | `{"field": "tipo", "equals": "criminal"}` |
| `not_equals` | Valor e diferente | `{"field": "tipo", "not_equals": "civil"}` |
| `in` | Valor esta na lista | `{"field": "uf", "in": ["SP", "RJ", "MG"]}` |
| `not_in` | Valor nao esta na lista | `{"field": "uf", "not_in": ["AC", "RR"]}` |
| `exists` | Campo tem valor (nao None) | `{"field": "email", "exists": True}` |

---

## Campo de dificuldade (self-reflection)

Inclua um campo `dificuldade: Optional[str]` pedindo ao LLM que
sinalize, em 1-2 frases, quando a classificacao foi dificil:

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class CodificacaoDecisao(BaseModel):
    area: Literal['civel', 'criminal', 'trabalhista', 'tributario']
    houve_reforma: Optional[bool]

    dificuldade: Optional[str] = Field(
        default=None,
        description="Sinalize em 1-2 frases se o caso tiver ambiguidade "
                    "relevante que tornou a classificacao dificil; deixe "
                    "None quando a classificacao foi clara."
    )
```

**Para que serve** (tecnica self-reflection; Reflexion, Shinn et al.
2023):

1. **Diagnostico do codebook** — se > 15% das linhas tem o campo
   preenchido, algum `Field(description=...)` esta ambiguo.
2. **Sinal de qualidade por linha** — a distribuicao indica a
   "zona-cinza" do corpus.
3. **Primeiro passo da politica de escalacao de precisao** antes de
   trocar para modelo caro — ler os textos sinalizados revela o que
   refinar.

**Custo muito baixo**: em codebooks bem calibrados, > 80% das linhas
retornam `None`.

**Politica de escalacao de precisao em 5 passos** (antes de trocar de
modelo): (1) refinar `Field(description=...)` → (2) adicionar few-shot
no prompt → (3) ler o campo `dificuldade` dos casos errados → (4)
decompor o campo problema em sub-campos → (5) so entao trocar de modelo,
e **apenas naquele campo**, via `reprocess_columns=['campo']` com
`provider`/`model` diferentes.
