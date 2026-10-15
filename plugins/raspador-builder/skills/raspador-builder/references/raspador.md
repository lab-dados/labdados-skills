# Escrever o raspador

O programa entregue é um arquivo `.py` só, que alguém que começa em Python consegue ler de cima a baixo. Parta de `assets/modelo_raspador.py`: copie-o para a pasta de trabalho como `raspador_<site>.py` e troque os trechos marcados com `ADAPTAR`. O resto do modelo (espera, códigos de resposta, paginação, CSV) já cumpre as regras abaixo; não o reescreva de outro jeito sem motivo.

## Regras

- **Dependências mínimas.** `requests` e `pandas`; `beautifulsoup4` só se ler HTML, com o leitor `html.parser`, que vem com o Python. Nada de Playwright, Selenium, Scrapy, `lxml` ou biblioteca de raspagem pronta. Mantenha o bloco `# /// script` do topo do modelo: ele lista as dependências, e `uv run raspador_<site>.py` as instala sozinho, sem `--with`. O docstring traz também o caminho com `pip`.
- **Uma função `coletar(...)`** com parâmetros nomeados em português que correspondem ao que o usuário pode variar: o termo de busca, os filtros que o site aceita (datas, órgão, tipo), e `max_paginas` para testes. Ela devolve um `pandas.DataFrame`. O `main()` só lê os argumentos da linha de comando, chama `coletar` e grava o CSV, para que a função possa ser importada num notebook.
- **Paginação até a última página.** Pare pelo que acontecer primeiro: o total informado foi atingido, a página veio vazia, a página não existe (404) ou o limite `max_paginas`. Uma página igual a uma página já coletada, na mesma ordem ou não, é repetição. Compare a página inteira, e não linha a linha: com só os campos pedidos, dois resultados diferentes podem dar a mesma linha, e uma página legítima pode trazer só linhas iguais a linhas já vistas. Se a repetição for na página 2, o site ignorou o parâmetro de página e devolveu a primeira: pare com erro, para não entrar em laço infinito nem duplicar linhas. Da página 3 em diante, a paginação já mostrou que funciona, e muitos sites devolvem a última página de novo, ou voltam à primeira, quando se pede uma além da última: acabou, mesmo que a última tenha vindo cheia. Sem total informado, a parada por repetição avisa que a coleta pode estar incompleta, porque nada confirma que a página repetida veio depois da última.
- **Erro no meio não perde a coleta.** Qualquer erro durante a coleta (403, 429 insistente, página 2 repetindo a 1), e também o Ctrl+C de quem a interrompe, grava o que veio até ali antes de parar, num arquivo à parte, `<saida>.parcial.csv` (`resultados.parcial.csv` para `resultados.csv`), para não apagar o CSV completo de uma rodada anterior; a mensagem diz quantas linhas ficaram salvas e em que arquivo.
- **Espera entre pedidos.** `ESPERA = 1.0` segundo antes de cada pedido, no mínimo. Se o `robots.txt` tem `Crawl-delay` maior, use-o. Não paralelize pedidos.
- **User-Agent identificável.** Diga o que é e para quê: `raspador-de-pesquisa/1.0 (coleta academica; contato: <email>)`. Se o usuário deu um e-mail, use-o; se não, tire o marcador (`raspador-de-pesquisa/1.0 (coleta academica)`) e diga no relato, em "Limites", que ele deve acrescentar o e-mail dele ao `USER_AGENT` antes de coletar de um site real. Não finja ser navegador para passar por bloqueio; se o site só responde a User-Agent de navegador sem bloquear robôs (há sites que recusam qualquer cliente desconhecido), registre isso no relato.
- **Códigos de resposta**, como no `pedir()` do modelo:
  - `200`: segue.
  - `404`: a página ou o item não existe. Na paginação, acabou; num item, registre e siga para o próximo.
  - `401` e `403`: acesso negado. Na busca, a coleta para com mensagem clara; num item isolado (processo em segredo de justiça, documento restrito), registre o item como "acesso negado" e siga, sem tentar outro caminho.
  - `429`: pedidos demais. Espere o tempo do cabeçalho `Retry-After` (em segundos ou como data) e tente de novo, até um limite de tentativas; sem o cabeçalho, espere o dobro a cada tentativa.
  - `5xx`: erro do servidor; trate como o 429.
- **Uma sessão (`requests.Session()`)** para a coleta inteira. Ela guarda o cookie que o site entrega no primeiro pedido e o devolve nos seguintes, como o navegador faz. Alguns sites contam os pedidos por cookie de sessão; outros exigem o cookie para responder.
- **Só os campos pedidos**, com nomes de coluna em português e sem acento (`numero`, `classe`, `data_decisao`). Guarde o valor como o site entrega; se precisar de uma versão formatada, acrescente outra coluna. Inclua um identificador único quando o site tiver um, porque ele serve para conferir duplicatas.
- **CSV em `utf-8-sig`**, sem o índice do pandas, e uma linha final na tela: "N linhas salvas em arquivo.csv; o site informou M."
- **Comentários em português** que explicam o porquê das escolhas (por que esperar, por que a sessão, de onde vem o total), não o que cada linha faz.

## Variante HTML

Quando não há API, os trechos `ADAPTAR` leem o HTML com BeautifulSoup. Acrescente `beautifulsoup4` ao bloco `# /// script` e troque `resposta.json()` por `resposta.text` em `coletar`:

```python
import re

from bs4 import BeautifulSoup


def ler_total(pagina_html):
    """O total vem num texto como "Resultados 1 a 10 de 132"; sem esse texto, devolve None."""
    texto = BeautifulSoup(pagina_html, "html.parser").get_text(" ")
    # ADAPTAR: o padrão ancora no texto do total, porque a página tem outros "de <número>"
    # ("15 de outubro de 2026", "Tribunal de 2ª instância") que um padrão solto pegaria.
    achado = re.search(r"Resultados\s+\d+\s+a\s+\d+\s+de\s+([\d.]+)", texto)
    return int(achado.group(1).replace(".", "")) if achado else None


def ler_resultados(pagina_html):
    sopa = BeautifulSoup(pagina_html, "html.parser")
    linhas = []
    for bloco in sopa.select("CSS DE CADA RESULTADO"):  # ADAPTAR
        linhas.append({
            "titulo": bloco.select_one("CSS DO TÍTULO").get_text(strip=True),  # ADAPTAR
            "data": campo_rotulado(bloco, "Data"),
        })
    return linhas


def campo_rotulado(bloco, rotulo):
    """Lê o valor depois de um rótulo em negrito, como "<strong>Classe:</strong> Apelação"."""
    for forte in bloco.find_all("strong"):
        if forte.get_text(strip=True).rstrip(":") == rotulo:
            return forte.next_sibling.strip() if forte.next_sibling else ""
    return ""
```

Antes de escrever os seletores, abra o HTML salvo de uma página de resultados e localize: o elemento que se repete uma vez por resultado, onde está cada campo pedido dentro dele, e onde a página diz o total. Teste os seletores no HTML salvo antes de rodar a coleta inteira.

Encoding: se os acentos saírem quebrados, o site provavelmente responde em `latin-1`; ponha `resposta.encoding = resposta.apparent_encoding` antes de ler `resposta.text`.

## Busca por formulário (POST)

Se o site busca por POST, troque `sessao.get(endereco, params=...)` por `sessao.post(endereco, data=...)` (formulário) ou `json=...` (corpo JSON), conforme o pedido que você viu. Se o formulário tem um campo escondido com token (`csrf`, `_token`, `__VIEWSTATE`), faça um GET na página do formulário, leia o token e mande-o junto; é o que o navegador faz. Token que muda por script a cada clique é sinal para voltar a `encontrar-api.md` e reconsiderar.

## Coleta em duas etapas (lista e depois detalhe)

Quando a lista não traz os campos pedidos e é preciso abrir cada resultado:

- colete primeiro a lista inteira (identificadores) e grave-a;
- depois peça o detalhe de cada um, com a mesma espera, tratando 404 e 403 por item (registre e siga);
- avise o usuário do tempo: 1.000 itens a um segundo cada são uns 17 minutos;
- se a coleta for longa, grave o CSV parcial de tempos em tempos para não perder o trabalho se cair.

## Filtros

Mapeie para parâmetros de `coletar` só os filtros que o usuário pediu ou que mudam o resultado de forma óbvia (datas, órgão, tipo de documento). Datas entram como texto no formato do site e são documentadas no docstring. Filtro que o usuário não pediu fica de fora; o relato pode citar que existe.
