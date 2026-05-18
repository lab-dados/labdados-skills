# Sincronização com a skill `raspe` do marketplace

Após criar uma fonte nova no repo `raspe` e validar que os testes
passam, atualize a skill `raspe` deste marketplace (em
`/home/brunodcdo/Desktop/LabDados/labdados-skills/plugins/raspe/skills/raspe/`)
para que ela ensine usuários a usar a fonte nova.

Sem essa sincronização, a biblioteca tem a fonte mas a skill que
documenta a biblioteca não — quem rodar `/plugin install raspe@labdados-skills`
não vai descobrir a nova fonte.

## Arquivos a editar

```
plugins/raspe/skills/raspe/
├── SKILL.md                             # 3 tabelas + frontmatter description
└── references/
    ├── fontes.md                        # 4 matrizes
    └── <fonte>.md                       # NOVO — assinatura, colunas, exemplos
```

## 1. `plugins/raspe/skills/raspe/SKILL.md`

Três tabelas + a `description` do frontmatter.

### Tabela "Roteamento de decisão"

Adicione uma linha:

```
| Quero {descrição curta do dado} | `raspe.{fonte}()` | {Tecnologia} | `{parametro-chave}` | {Autenticação} |
```

Onde:
- **Tecnologia**: `HTTP`, `HTTP (JSON)`, `Playwright`, ou
  `Playwright + stealth`.
- **Parametro-chave**: o nome do kwarg de busca (`pesquisa`, `termo`,
  `texto`, `assunto`).
- **Autenticação**: `nenhuma`, `API key`, ou similar.

Mantenha a ordem aproximada da tabela (legislação → órgãos → imprensa →
playwright).

### Tabela "Vocabulário do pesquisador → factory"

Adicione termos informais que o usuário pode usar para se referir à
fonte nova:

```
| "{termo informal 1}", "{termo informal 2}", ... | `{fonte}` |
```

Exemplo, se a fonte nova for Tesouro Nacional:
`| "dívida pública", "títulos do tesouro", "tesouro nacional" | tesouro |`

### Frontmatter `description`

A `description` no frontmatter lista as fontes cobertas e termos-gatilho.
Adicione menção à nova fonte. Padrão atual (extraído da `SKILL.md` da
raspe):

> Cobre legislacao federal (Presidencia, Camara, Senado), agencias
> reguladoras (ANS, ANVISA, SaudeLegis, CFM), orgaos de pesquisa e
> controle (IPEA, CNJ) e imprensa (Folha de Sao Paulo, New York Times).

Reescreva incluindo a nova fonte na categoria certa. Adicione também
termos-gatilho específicos (ex: "dívida pública", "leilões do tesouro")
no final do trecho de "use sempre que o usuario mencionar...".

### Tabela "Arquivos de referência"

No final do `SKILL.md`, há uma tabela mapeando arquivos em
`references/`. Adicione:

```
| `references/{fonte}.md` | Antes de chamar `raspe.{fonte}()`. |
```

## 2. `plugins/raspe/skills/raspe/references/fontes.md`

Quatro matrizes para atualizar (na ordem em que aparecem no arquivo):

### Matriz geral

```
| {Fonte} | `raspe.{fonte}()` | {URL oficial} | {Tecnologia} | {Auth} | `{parametro-chave}` |
```

### Colunas retornadas

```
| `{fonte}` | `{coluna1}`, `{coluna2}`, ... |
```

Liste as colunas (sem `termo_busca`, que é implícita) que o
`_parse_page` retorna. Olhar diretamente no código gerado em
`src/raspe/scrapers/<fonte>.py`.

### Limites de coleta

```
| `{fonte}` | {limite explícito} | {observação} |
```

Se não há limite documentado, registre `nenhum explicito`.

### Cobertura e volume típico

Texto livre na seção do mesmo nome. Adicione um parágrafo curto sobre o
que a fonte cobre (período histórico, tipo de documento, escopo).

### Nomes de coluna em dataframeit / análise textual

```
| `{fonte}` | `{coluna_recomendada}` |
```

Recomende a coluna com texto significativo (ementa, descrição, resumo).
Para fontes só de metadados, recomende `titulo` com nota explicando que
não há abstract.

### Combinação com outras fontes

Se a fonte nova se combina naturalmente com alguma já existente (ex:
agência reguladora setorial que dialoga com SaudeLegis), adicione na
seção "Quando combinar fontes".

## 3. `plugins/raspe/skills/raspe/references/<fonte>.md`

Crie no padrão dos arquivos existentes. Os outros references por fonte
(`presidencia.md`, `ipea.md`, `folha.md`, etc.) seguem este esqueleto:

```markdown
# {Nome longo da fonte} — `raspe.{fonte}()`

Resumo curto: o que o site cobre, motivo de existir essa fonte no raspe.

## Assinatura

```python
raspe.{fonte}().raspar(
    pesquisa: str | list[str],         # ou termo/texto/assunto conforme o caso
    paginas: range | int | None = None,
    {outros parametros opcionais}: {tipo} = {default},
) -> pd.DataFrame
```

## Parâmetros

- `pesquisa` (obrigatório): {descrição}.
- `paginas` (opcional): {descrição padrão, 1-based, default None}.
- `{outro}`: {descrição}.

## Colunas retornadas

| Coluna | Tipo | Descrição |
|---|---|---|
| `titulo` | str | ... |
| `link` | str | URL absoluta para o item |
| ... | ... | ... |
| `termo_busca` | str | Adicionado automaticamente pelo BaseScraper |

## Exemplos

### Busca simples

```python
import raspe
df = raspe.{fonte}().raspar(pesquisa="meio ambiente", paginas=range(1, 4))
print(df.shape)
```

### {Outro caso útil}

```python
df = raspe.{fonte}().raspar(...)
```

## Limites e quirks

- {Limite específico, se houver}
- {Quirk de paginação ou encoding, se houver}
- {Recomendação de horário / divisão por data, se aplicável}

## Erros comuns

- `ValidationError: ...` quando ...
- `APIError: ...` quando ...

## Recomendação para dataframeit

`text_column = "{coluna_recomendada}"`
```

Use as references existentes (`references/presidencia.md` etc.) como
modelo de tom, formato e profundidade.

## 4. Atualizar `marketplace.json` da skill `raspe`?

Não. A `version` do plugin `raspe` em `.claude-plugin/marketplace.json`
**pode** ser bumpada (1.0.0 → 1.1.0) se o sync representar uma
contribuição significativa. Para fonte nova, recomendo bump minor.
Atualize também o `CHANGELOG.md` raiz do marketplace mencionando essa
expansão.

Mas isso é decisão de release — geralmente fazer em PR separado ou
quando juntar várias mudanças.

## Checklist do sync

- [ ] Linha adicionada em `SKILL.md` → tabela "Roteamento de decisão"
- [ ] Linha adicionada em `SKILL.md` → tabela "Vocabulário do pesquisador"
- [ ] Linha adicionada em `SKILL.md` → tabela "Arquivos de referência"
- [ ] `frontmatter > description` em `SKILL.md` menciona a nova fonte
- [ ] Linha adicionada em `references/fontes.md` → matriz geral
- [ ] Linha adicionada em `references/fontes.md` → colunas retornadas
- [ ] Linha adicionada em `references/fontes.md` → limites
- [ ] Parágrafo em `references/fontes.md` → cobertura e volume típico
- [ ] Linha adicionada em `references/fontes.md` → text_column para dataframeit
- [ ] Arquivo novo `references/<fonte>.md` criado no padrão dos demais

Após o sync, gere um commit dedicado:
`docs(raspe): adiciona referência da fonte <fonte>` (separado do PR no
repo raspe).
