# Procurar a API por baixo da página

Muita página de busca é montada em duas etapas: o navegador recebe um HTML quase vazio e um script pede os resultados a um endereço que devolve JSON. Quando esse endereço existe, o raspador o usa direto. Os campos chegam separados (`classe`, `data`, `numero`), o total costuma vir num campo próprio e uma mudança de layout não quebra a coleta.

Há dois caminhos para achar o endereço. O primeiro precisa do Playwright MCP; o segundo, só de `requests`. Use o primeiro quando ele estiver disponível; o segundo funciona sempre e é o que o `scripts/reconhecer_site.py` começa a fazer.

## Caminho 1: com o Playwright MCP (a aba Rede)

Confira se há ferramentas `browser_*` do Playwright MCP disponíveis na sessão. Se não houver, vá para o caminho 2; não peça ao usuário que instale nada só para isso.

```
1. browser_navigate(endereço da página de busca)
2. browser_snapshot()                 # ver o formulário e os botões
3. browser_type / browser_fill_form   # preencher a busca pedida
4. browser_click(botão de buscar)
5. browser_wait_for(resultado visível)
6. browser_network_requests()         # a lista de pedidos, como a aba Rede
7. browser_click(página 2) e browser_network_requests() de novo
```

Na lista de pedidos:

- descarte arquivos de aparência e de medição de audiência (`.css`, `.js`, imagens, fontes, Google Analytics, Tag Manager);
- prefira pedidos do tipo `fetch` ou `xhr`, com `/api/`, `busca`, `pesquisa`, `consulta`, `search`, `query` ou `graphql` no endereço;
- o pedido certo leva o termo que você digitou (na URL ou no corpo) e a resposta tem `content-type: application/json`;
- compare o pedido da página 1 com o da página 2: o que muda é o parâmetro de paginação (`pagina=2`, `page=1`, `offset=10`, `start=20`).

Anote endereço, método (GET ou POST), parâmetros, cabeçalhos que pareçam necessários (`Referer`, `Accept`, um token CSRF) e onde está o total.

O Playwright serve só para investigar. O raspador entregue não abre navegador.

## Caminho 2: sem navegador, lendo o HTML e os scripts

1. Peça a página de busca com `requests`, já com um termo, e olhe o HTML. Se os resultados estão lá (o termo, os números, as linhas da tabela), a página é montada no servidor e pode ser lida direto; ainda assim, faça o passo 2, porque o site pode ter uma API documentada.
2. Procure no HTML e nos scripts do mesmo site (os `<script src="...">` do próprio domínio):
   - chamadas `fetch(`, `axios.get(`, `axios.post(`, `$.ajax(`, `$.getJSON(`, `XMLHttpRequest`;
   - textos entre aspas com `/api/`, `.json`, `format=json`, `graphql`, `/rest/`, `/v1/`;
   - links de "API", "Dados abertos", "Desenvolvedores", "Documentação" na página inicial ou no rodapé;
   - JSON embutido no HTML (`<script type="application/json">`, `window.__INITIAL_STATE__`, `__NEXT_DATA__`): às vezes os dados já vêm na própria página.
3. Se a página mostra "Carregando..." ou uma lista vazia e os resultados não estão no HTML, é quase certo que um script os busca; o endereço está nesse script.
4. Teste cada candidato com um pedido só, com um segundo de espera entre eles, e veja o código de resposta e o `content-type`.

A seção "API candidatos" do `reconhecer_site.py` faz os passos 2 e 4 de forma automática e limitada (no máximo cinco endereços testados). Script e endereço do mesmo host escritos com `https` numa página servida por `http` (site atrás de proxy) entram na lista e são pedidos pelo `http`, o esquema do `robots.txt` lido. O que ela não acha, procure lendo os scripts.

## Confirmar o candidato antes de escrever o raspador

Um endereço que devolve JSON ainda não é a API certa. Confirme com três pedidos:

1. **Mesma busca, mesmo total.** O total do JSON (`total`, `count`, `hits.total.value`, `totalElements`, `quantidade`) é igual ao que a página de busca mostra ("Resultados 1 a 10 de 132")?
2. **A paginação funciona.** A página 2 traz registros diferentes da página 1? Se o servidor ignora o parâmetro, ele devolve a página 1 de novo, e o raspador repetiria as mesmas linhas.
3. **Os campos pedidos estão lá.** Os campos do pedido do usuário existem no JSON, com os mesmos valores que a página mostra.

```python
import time
import requests

sessao = requests.Session()
sessao.headers["User-Agent"] = "raspador-de-pesquisa/1.0 (coleta academica)"
endereco = "https://site/api/busca"  # o candidato
p1 = sessao.get(endereco, params={"q": "licitação", "page": 1}, timeout=30)
time.sleep(1)
p2 = sessao.get(endereco, params={"q": "licitação", "page": 2}, timeout=30)
print(p1.status_code, p1.headers.get("content-type"))
print(p1.json().keys())
# compare o total com o da página e o primeiro registro da página 1 com o da página 2
```

## Decidir: API ou HTML

| O que você achou | Decisão |
|---|---|
| Endereço JSON que passa nos três testes | **API.** |
| API documentada que pede chave gratuita | API, com a chave lida de variável de ambiente; explique ao usuário como obter. |
| Nenhum JSON, mas os resultados estão no HTML que o `requests` recebe | **HTML**, lido com BeautifulSoup. |
| JSON que só funciona com token que muda a cada visita, cookie gerado por script ou assinatura no pedido | HTML, se os resultados estiverem no HTML; se não, pare. |
| Resultados só aparecem rodando JavaScript e nenhum endereço os devolve | **Pare** e explique: o programa teria de abrir um navegador, o que esta skill não faz. |

Anote a decisão e o motivo em uma frase. Ela entra no relato, por exemplo: "Usei a API (`/api/v1/atos`), que o script da página de resultados chama: ela devolve os mesmos 132 atos que a página mostra, já com data e órgão em campos separados."
