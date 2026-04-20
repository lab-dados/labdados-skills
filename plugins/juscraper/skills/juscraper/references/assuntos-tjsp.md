# Assuntos (Classificação Temática) do TJSP

Referência dos códigos de assunto usados pela Consulta de Julgados de 1º
Grau (`cjpg`) e pela Consulta de Jurisprudência (`cjsg`) do Tribunal de
Justiça do Estado de São Paulo.

## Metodologia desta coleta

- **Fonte**: árvore de assuntos exposta pelo endpoint
  `https://esaj.tjsp.jus.br/cjpg/assuntoTreeSelect.do`
  (o mesmo JSON/HTML usado pelo componente de busca avançada)
- **Data da coleta**: 2026-04-16
- **Total de nós extraídos**: 8.886
- **Arquivo JSON completo**: `references/assuntos-tjsp.json` (inclui
  código, label, profundidade hierárquica e `searchValue` com o caminho
  completo na árvore)
- **Script de reextração** (para atualizar periodicamente):
  ```bash
  curl -s 'https://esaj.tjsp.jus.br/cjpg/assuntoTreeSelect.do' -o tree.html
  # extrair spans com regex — ver Bash de investigação nesta skill
  ```

O TJSP adota como base a **Tabela Processual Unificada do CNJ**
(Resolução CNJ 46/2007), com extensões próprias. Os códigos numéricos
aqui listados correspondem aos do TJSP — para outros tribunais, consulte
a tabela oficial do CNJ em https://www.cnj.jus.br.

## Ramos principais (raízes da árvore)

Total de nós por ramo. Apenas os nós **selectable** (marcados com `*`
na listagem abaixo) podem ser usados como filtro efetivo — os demais
são categorias pais (agrupadores).

| Ramo | Nós | Observação |
|---|---|---|
| DIREITO CIVIL | 374 | Contratos, família, sucessões, obrigações |
| DIREITO ADMINISTRATIVO E OUTRAS MATÉRIAS DE DIREITO PÚBLICO | 774 | Inclui servidor público, tributário municipal |
| DIREITO AMBIENTAL | 6 | Muito agregado — considerar outros ramos |
| DIREITO ASSISTENCIAL | 4 | BPC, assistência social |
| DIREITO DA CRIANÇA E DO ADOLESCENTE | 600 | ECA, ato infracional, socioeducativo, adoção |
| DIREITO DA SAÚDE | 46 | **Ramo específico para judicialização da saúde** |
| DIREITO DO CONSUMIDOR | 74 | CDC, serviços, produtos |
| DIREITO DO TRABALHO | 6 | Residual — TJSP não é competente |
| DIREITO ELEITORAL | 4 | Residual — Justiça Eleitoral é competente |
| DIREITO INTERNACIONAL | 58 | Homologação, cooperação |
| DIREITO MARÍTIMO | 23 | Transporte, seguros marítimos |
| DIREITO PENAL | 678 | Crimes tipificados no CP e leis extravagantes |
| DIREITO PENAL MILITAR | 306 | Justiça Militar Estadual |
| DIREITO PREVIDENCIÁRIO | 161 | RGPS e regimes próprios |
| DIREITO PROCESSUAL CIVIL E DO TRABALHO | 492 | Cumprimento, execução, recursos |
| DIREITO PROCESSUAL PENAL | 198 | Medidas cautelares, execução penal |
| DIREITO PROCESSUAL PENAL MILITAR | 19 | Residual |
| DIREITO TRIBUTÁRIO | 280 | IPTU, ITBI, ICMS estadual, taxas |
| REGISTROS PÚBLICOS | 57 | Notariais, cartoriais |
| ASSUNTOS ANTIGOS DO SAJ | 1.334 | **Legado** — evitar em estudos novos |
| ASSUNTOS ANTIGOS DO SIP | 3.236 | **Legado** — evitar em estudos novos |

**Atenção aos legados**: cerca de metade dos 8.886 nós são de tabelas
legadas ("SAJ" e "SIP") de pré-unificação. Ao replicar estudos recentes
(>2015), filtre para os ramos modernos. Ao replicar estudos antigos
(<2010), as tabelas antigas podem ser necessárias.

**Nota de qualidade**: a árvore do TJSP contém duplicatas e erros de
digitação na raiz (ex: "DIREITO A EDUCAÇÃO" e "DREITO A EDUCACAO" como
raízes distintas). Isso é inerente ao dado oficial — documentado aqui
para o pesquisador não se surpreender.

## DIREITO DA SAÚDE — listagem completa

Ramo mais útil para replicar estudos de judicialização da saúde
(Boarati et al. 2025; Ferraz 2020; Scheffer 2013; Trettel, Kozan &
Scheffer 2018). Estrutura hierárquica com sub-ramos "Pública" e
"Suplementar":

```
[  6683]   DIREITO DA SAÚDE
  [  7003] * Autorização para Interrupção de Gravidez (Aborto)
  [  6724] * Doação e transplante de órgãos, tecidos ou partes
  [  9287] * Doença Rara
  [  6723] * Genética / Células Tronco
  [  6719]   Mental
  [  6684]   Pública                                   (agrupador)
  [  6713]   Suplementar                               (agrupador)
    [  6694] * Fornecimento de insumos
    [  6688] * Fornecimento de medicamentos
    [  6720] * Internação compulsória
    [  6721] * Internação involuntária
    [  6722] * Internação voluntária
    [  6685]   Internação/Transferência Hospitalar     (agrupador)
    [  6714]   Planos de saúde                         (agrupador)
    [  6704]   Sistema Único de Saúde (SUS)            (agrupador)
    [  6925] * Tratamento Domiciliar (Home Care)
    [  6926] * Tratamento Domiciliar (Home Care)       (duplicata)
    [  6698]   Tratamento médico-hospitalar            (agrupador)
    [  6712] * Vigilância Sanitária e Epidemológica
      [  6696] * Cadeira de rodas / cadeira de banho / cama hospitalar
      [  6700]   Cirurgia                              (agrupador)
      [  6699] * Consulta
      [  6711] * Controle Social e Conselhos de Saúde
      [  6705] * Convênio médico com o SUS
      [  6695] * Curativos/Bandagem
      [  6703] * Diálise/Hemodiálise
      [  6706] * Financiamento do SUS
      [  6718] * Fornecimento de insumos
      [  6715] * Fornecimento de medicamentos
      [  6697] * Fraldas
      [  6686] * Leito de enfermaria / leito oncológico
      [  6693] * Oncológico
      [  6716] * Reajuste contratual
      [  6707] * Reajuste da tabela do SUS
      [  6689]   Registrado na ANVISA                  (agrupador)
      [  6708] * Repasse de verbas do SUS
      [  6709] * Ressarcimento do SUS
      [  6692] * Sem registro na ANVISA
      [  6710] * Terceirização do SUS
      [  6717] * Tratamento médico-hospitalar
      [  6687] * Unidade de terapia intensiva (UTI) / unidade de cuidados intensivos (UCI)
        [  6701] * Eletiva
        [  6691] * Não padronizado
        [  6690] * Padronizado
        [  6702] * Urgência
```

### IMPORTANTE: a busca por assunto no TJSP NÃO é hierárquica

**Erro comum** — passar o código-raiz `6683` para `cjpg(assuntos=['6683'])`
esperando capturar todos os filhos. Isso **retorna zero resultados**. O
filtro de assunto do `cjpg`/`cjsg` do TJSP é por **valor exato** e aceita
apenas os nós marcados como `selectable=True` no `assuntos-tjsp.json`
(folhas e algumas sub-folhas). Nós com `selectable=False` são
agrupadores visuais da UI do eSAJ e não são aceitos como filtro.

No ramo DIREITO DA SAÚDE (46 nós), **36 são `selectable=True`** e 10 são
agrupadores. Para capturar "tudo do ramo", passe a lista completa dos 36
códigos selecionáveis no parâmetro `assuntos`:

```python
import json
from pathlib import Path
import juscraper as jus

p = Path.home() / '.claude/skills/juscraper-skill/references/assuntos-tjsp.json'
arvore = json.loads(p.read_text())

# Todos os códigos selectable do ramo Direito da Saúde
codigos_saude = [
    n['codigo']
    for n in arvore['DIREITO DA SAUDE']
    if n['selectable']
]
assert len(codigos_saude) == 36

scraper = jus.scraper('tjsp')
df = scraper.cjpg(
    assuntos=codigos_saude,
    data_julgamento_inicio='01/01/2022',
    data_julgamento_fim='31/01/2022',
    paginas=range(1, 2),
)
# Retorna sentenças com qualquer um dos 36 assuntos folhas.
```

Para outros ramos, o mesmo padrão se aplica: filtre por `selectable=True`
na lista plana do ramo desejado no `assuntos-tjsp.json`.

## DIREITO DO CONSUMIDOR — principais assuntos (profundidade ≤ 2)

```
[  1156]   DIREITO DO CONSUMIDOR
  [  3717] * Cláusulas Abusivas
  [ 11554] * Combustíveis e derivados
  [  7771] * Contratos de Consumo
  [  5243]   Cursos Extracurriculares                  (agrupador)
  [ 11499] * Dever de Informação
  [  5204]   Direito Coletivo                          (agrupador)
  [ 11550] * Irregularidade no atendimento
  [ 11552] * Jogos / Sorteios / Promoções comerciais
  [ 11501] * Oferta e Publicidade
  [ 11500] * Práticas Abusivas
  [  6220] * Responsabilidade do Fornecedor
  [  8103] * Superendividamento
  [ 11551] * Vendas casadas
```

Para o detalhamento completo (incluindo sub-ramos de cada linha acima),
consulte `assuntos-tjsp.json`.

## Como usar na busca

### Via juscraper

No momento da redação desta skill, `cjpg`/`cjsg` aceitam o filtro de
assunto como parte da string de busca ou em parâmetro próprio
(consulte `references/api.md` e `references/tribunais.md` para a
assinatura atual). Quando o parâmetro próprio não estiver disponível,
use a URL de busca direta do TJSP e cole na `pesquisa=` a sintaxe que
o portal expõe.

### Verificando volume antes de coletar

Sempre teste o volume de retorno com uma janela temporal curta antes
de rodar o corpus inteiro. O parâmetro correto é `assuntos` (lista) —
`codigo_assunto` singular não existe:

```python
import juscraper as jus
s = jus.scraper('tjsp')
teste = s.cjpg(
    assuntos=['6688'],                     # Fornecimento de medicamentos - Suplementar
    data_julgamento_inicio='01/01/2022',
    data_julgamento_fim='31/01/2022',
    paginas=range(1, 2),
)
print(f"Página 1: {len(teste)} resultados")
```

### Combinando assunto com busca textual

Filtro primário por assunto + refinamento textual para conceitos
específicos que não têm código dedicado:

```python
# 1. Frame amostral via um ou mais códigos selectable
#    (ex: todos os ramos de suplementar + fornecimento)
s.cjpg(assuntos=['6688', '6694', '6714'], paginas=None)

# 2. Filtro pós-coleta com regex no texto da decisão
df_filtro = df[df['decisao'].str.contains(r'\b(?:TEA|autismo|TDAH)\b',
                                          case=False, regex=True)]
```

## Acesso programático ao JSON completo

```python
import json
from pathlib import Path

# Caminho relativo à skill
p = Path.home() / '.claude' / 'skills' / 'juscraper-skill' / \
    'references' / 'assuntos-tjsp.json'
assuntos = json.loads(p.read_text())

# Pesquisa de texto livre
import re
pat = re.compile(r'medicamento', re.IGNORECASE)
hits = [(ramo, item) for ramo, lista in assuntos.items()
        for item in lista if pat.search(item['label'])]
for ramo, item in hits[:20]:
    print(f"[{item['codigo']:>6}] {ramo} → {item['label']}")
```

## Limitações

1. Lista obtida em 2026-04-16 — o TJSP adiciona/remove assuntos
   periodicamente. Para pesquisa de longo prazo, registre a data da
   coleta no protocolo.
2. Alguns assuntos são "legados" (SAJ/SIP) e não são mais usados em
   distribuições novas; são mantidos para processos antigos.
3. A classificação é feita pelo(a) serventuário(a) no momento da
   distribuição e **pode estar incorreta** em casos individuais. Em
   estudos sistemáticos, isso introduz ruído aleatório — mas é
   metodologicamente mais robusto que busca textual, que introduz ruído
   **sistemático** (por variação de redação).
4. Outros tribunais (TJRJ, TJMG, TJPR etc.) têm suas próprias árvores,
   derivadas da Tabela CNJ mas com extensões locais. Este arquivo
   cobre apenas o TJSP.

## Trabalho futuro (issues)

- Coletar equivalentes para TJRJ, TJMG, TJPR, TJRS e demais TJs
  suportados pelo juscraper.
- Padronizar a saída: mesmo schema JSON para todos.
- Disponibilizar utilitário `juscraper.assuntos(tribunal='tjsp')` que
  retorna a árvore como pandas DataFrame.
