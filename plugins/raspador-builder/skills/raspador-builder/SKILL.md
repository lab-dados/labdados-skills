---
name: raspador-builder
description: >
  Constrói do zero um programa Python autônomo que coleta os dados de um site
  (raspador, scraper, web scraping, robô de coleta) e salva em CSV. Use quando
  pedirem um programa ou script que colete, raspe, baixe ou extraia resultados
  de uma busca, uma lista ou uma tabela de um site, em todas as páginas, para
  pesquisa ou planilha, inclusive de tribunal, órgão público, diário oficial ou
  portal de transparência que nenhuma biblioteca cobre. Confere robots.txt e
  termos antes de coletar, procura a API por baixo da página antes de raspar o
  HTML, usa só requests com pausa entre pedidos e testa a contagem contra o
  total que o site informa. Não exige repositório clonado nem Playwright. Não
  confundir com juscraper e raspe (usar o que essas bibliotecas já coletam;
  prefira-as quando cobrem o site), juscraper-builder (adicionar tribunal novo à
  biblioteca juscraper) e raspe-builder (adicionar fonte oficial ou de imprensa
  à biblioteca raspe), que exigem o repositório da biblioteca clonado.
---

# Raspador Builder

Esta skill entrega um **programa Python de um arquivo só**, que roda sem
biblioteca de raspagem nenhuma (só `requests`, `pandas` e, se precisar ler
HTML, o BeautifulSoup), e o **CSV** que ele produziu. Quem pede costuma estar
começando em programação: o código vem comentado em português, com nomes de
variável em português, e o relato final explica as escolhas em palavras
simples.

## Princípios

1. **Permissão antes de coleta.** Nenhum pedido de dados sai antes de ler o
   `robots.txt` e procurar os termos de uso. Se a coleta for proibida, exigir
   login, esbarrar em captcha ou bloqueio anti-robô, ou envolver dado pessoal
   sensível, a skill **para e avisa**. Não contorna nada.
2. **API antes de HTML.** Muita página de busca é preenchida por um endereço
   que devolve JSON. Quando ele existe, o raspador pede o JSON: os campos já
   vêm separados, e uma mudança de layout não quebra a coleta.
3. **Sem navegador no programa final.** Playwright, Selenium e afins podem
   ajudar a investigar o site, mas o raspador entregue usa só `requests`. Se o
   dado só aparece rodando JavaScript e não há endereço que o devolva, a skill
   para e explica.
4. **Só está pronto depois de rodar.** O raspador roda inteiro antes da
   entrega, e o número de linhas é conferido contra o total que o site informa.

## Etapa 0: entender o pedido

Anote, antes de abrir o site: o endereço, a busca e os filtros, os campos
pedidos (ex.: data, órgão e título), se são todas as páginas e o formato de saída.
Se o site é coberto pelo `juscraper` (tribunais) ou pelo `raspe` (fontes
oficiais e imprensa), diga isso ao usuário, porque a biblioteca já resolve o
caso; siga com o programa avulso se for isso que ele quer. Com o pedido
completo, não pergunte: decida e registre a decisão no relato.

## Etapa 1: pode coletar?

Leia `references/permissao.md` e rode o reconhecimento que acompanha a skill,
com o caminho completo da pasta desta skill (o diretório base que aparece ao
carregá-la):

```bash
python <pasta desta skill>/scripts/reconhecer_site.py "<endereço da página de busca>"
```

Onde o comando `python` não existe (Linux e macOS costumam ter só `python3`),
use `python3`. Ele precisa só de `requests`; com `uv`,
`uv run <pasta desta skill>/scripts/reconhecer_site.py ...` instala sozinho.

Ele lê o `robots.txt`, procura links de termos de uso, sinais de login, de
captcha e de bloqueio anti-robô, e lista endereços de API candidatos. Leia a
saída inteira e confira por conta própria o que ela sinalizar. Pare e avise o
usuário nos casos listados em `references/permissao.md`. Registre o que o
`robots.txt` disse, inclusive "não existe", porque isso entra no relato.

## Etapa 2: procurar a API

Leia `references/encontrar-api.md`. Com o Playwright MCP disponível, abra a
página, faça a busca e olhe os pedidos que ela dispara (como a aba Rede do
navegador). Sem ele, leia o HTML e os scripts da página com `requests` e
procure endereços que devolvem JSON; a seção "API candidatos" do
reconhecimento já faz a primeira passada. Confirme o candidato com um pedido
de teste: a resposta é JSON, o total bate com o da página e a página 2 traz
resultados diferentes da página 1. Decida **API ou HTML** e anote o porquê.

## Etapa 3: escrever o raspador

Leia `references/raspador.md` e parta de `assets/modelo_raspador.py`. O
programa tem de ter:

- uma função `coletar(...)` com parâmetros claros (a busca, os filtros, um
  limite opcional de páginas) que devolve um `pandas.DataFrame`;
- paginação até a última página, parando pelo total informado ou pela página
  vazia, e nunca em laço infinito;
- **um segundo de espera entre pedidos**, no mínimo (mais, se o `robots.txt`
  pedir `Crawl-delay` maior);
- User-Agent que identifica o programa e o propósito;
- tratamento de 404 (não existe: segue ou termina), 401/403 (acesso negado:
  para e explica, sem tentar contornar) e 429 (espera o `Retry-After` e tenta
  de novo, com limite de tentativas);
- saída em CSV (`utf-8-sig`, que o Excel abre com acento) e uma linha final
  com quantas linhas foram salvas e quantas o site informou.

Salve na pasta de trabalho do usuário como `raspador_<site>.py`.

## Etapa 4: testar antes de entregar

Leia `references/teste-e-entrega.md`. Rode o programa com a busca pedida, do
começo ao fim. Confira que o CSV tem o número de linhas que o site informa,
sem repetição, com as colunas pedidas preenchidas, e que houve espera entre os
pedidos. Se algo não bater, corrija e rode de novo. Não entregue raspador que
não rodou.

## Etapa 5: entregar

Responda com o resumo descrito em `references/teste-e-entrega.md`: o que foi
coletado (linhas, colunas, total do site), de onde (API ou HTML, e por quê), o
que o `robots.txt` e os termos dizem, em tribunal o que o segredo de justiça
deixa de fora, os limites da coleta e o comando para rodar de novo.

## Quando parar e avisar

- `robots.txt` proíbe o caminho, ou os termos proíbem coleta automatizada.
- O dado só aparece com login, senha, certificado ou token pessoal.
- Há captcha, desafio do Cloudflare ou outro bloqueio anti-robô.
- O dado é pessoal sensível (saúde, origem racial ou étnica, religião,
  opinião política, vida sexual, dado genético ou biométrico, filiação
  sindical) ou, em tribunal, vem de processo em segredo de justiça.
- O dado só existe depois de rodar JavaScript e nenhum endereço o devolve.

Ao parar, diga o que foi visto, onde, e o que o usuário pode fazer (pedir o
dado ao órgão, usar a Lei de Acesso à Informação, procurar dados abertos).

## Arquivos de referência

| Arquivo | Quando ler |
|---|---|
| `references/permissao.md` | Etapa 1, sempre, antes do primeiro pedido de dados. |
| `references/encontrar-api.md` | Etapa 2, com ou sem Playwright MCP. |
| `references/raspador.md` | Etapa 3, junto com `assets/modelo_raspador.py`. |
| `references/teste-e-entrega.md` | Etapas 4 e 5. |
| `scripts/reconhecer_site.py` | Etapa 1 e começo da 2: robots.txt, termos, bloqueios e API candidatos. |
| `assets/modelo_raspador.py` | Etapa 3: o esqueleto do programa entregue. |
