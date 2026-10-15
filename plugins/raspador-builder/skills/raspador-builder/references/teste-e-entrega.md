# Testar e entregar

## Teste

O raspador só é entregue depois de rodar a coleta pedida inteira. A sequência:

1. **Primeiro uma página.** `python3 raspador_<site>.py --pesquisa "<termo>" --max-paginas 1 --saida teste.csv` (no Windows, `python` no lugar de `python3`). Abra o CSV: as colunas pedidas estão preenchidas, com os mesmos valores que a página do site mostra para os primeiros resultados?
2. **Depois a coleta inteira.** Rode sem `--max-paginas`, com a saída final. Guarde o que o programa imprimiu.
3. **Confira**, com um trecho curto de pandas:

```python
import pandas as pd

tabela = pd.read_csv("resultados.csv")
print(len(tabela), "linhas")                                   # igual ao total que o site informa?
print(tabela.duplicated().sum(), "linhas repetidas")           # sem id entre os campos, podem ser processos diferentes
print(tabela["<identificador>"].duplicated().sum(), "ids repetidos")  # tem de ser 0
print(tabela.isna().sum())                                      # campos pedidos vazios?
print(tabela.head())
```

4. **Compare com o site.** O total que o site informa (na página de busca ou no campo de total da API) é igual ao número de linhas. Se não bater, investigue antes de entregar: a última página foi lida? A paginação começa em 0 ou em 1? O site esconde resultados em segredo de justiça ou restritos (e então o total pode incluir o que não aparece)? Diferença explicada vai para o relato; diferença sem explicação é defeito.
5. **Confira a espera.** A coleta de N páginas tem de levar pelo menos N segundos. Meça (`time python3 ...`, ou o horário de início e de fim) e diga no relato.
6. **Se der erro**, leia a mensagem, corrija e rode de novo. 429 durante o teste quer dizer que a espera está curta para aquele site: aumente `ESPERA`.

Não faça mais pedidos do que o teste precisa. Uma coleta de teste e uma coleta final bastam; não rode a coleta inteira várias vezes só para conferir.

## Entrega

Responda ao usuário com estas partes, em linguagem simples, nesta ordem:

1. **O que foi coletado.** Arquivo CSV, número de linhas, colunas, e o total que o site informa. Ex.: "`resultados.csv`, 132 linhas com `data`, `orgao` e `titulo`; o site informa 132 resultados para 'licitação'."
2. **De onde e como.** API ou HTML, com o endereço, e por quê, em uma ou duas frases.
3. **Permissão.** O que o `robots.txt` disse (inclusive "não existe"), o que os termos de uso dizem, ou que não foram encontrados, e se há dado pessoal na tabela. **Em tribunal, fale sempre do segredo de justiça**: processos em segredo não aparecem na consulta pública (ou o site recusa o acesso a eles), então a tabela cobre só os públicos, e o raspador não tenta obter os sigilosos; se o site informar quantos ficaram de fora, diga o número.
4. **Como foi a coleta.** Quantos pedidos, a espera entre eles, quanto tempo levou, e se apareceu 429, 403 ou 404.
5. **Limites.** O que a coleta não cobre: campos que o site não oferece, resultados que o site esconde, a data em que foi feita (o site muda), a dependência do formato atual da página ou da API, e, se o usuário não deu e-mail, o pedido para ele acrescentar o dele ao `USER_AGENT`.
6. **Como rodar de novo.** O comando exato, com `uv run raspador_<site>.py ...` (que lê as dependências do bloco `# /// script`) e com `python3 -m pip install` + `python3`, e como mudar a busca ou o arquivo de saída.

Se a coleta parou numa das condições de `permissao.md`, a entrega é o aviso daquele arquivo, sem programa.
