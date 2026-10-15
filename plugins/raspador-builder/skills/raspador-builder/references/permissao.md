# Pode coletar? Conferência antes do primeiro pedido de dados

Esta conferência vem antes de qualquer pedido que traga os dados. Ela leva poucos pedidos (o `robots.txt`, a página inicial, a página de busca) e responde a cinco perguntas. Qualquer "não" para a coleta e vira aviso ao usuário.

O script `scripts/reconhecer_site.py` faz a primeira passada das cinco. Ele sinaliza; quem decide é você, lendo o que ele mostrou e, na dúvida, abrindo a página.

## 1. O `robots.txt` permite?

O `robots.txt` fica sempre na raiz do domínio (`https://site.gov.br/robots.txt`), não na pasta da página. Leia o arquivo inteiro, não só a conclusão do script.

- **Não existe (404)**: o site não declarou regra para robôs. Isso não é autorização ampla; siga para os termos de uso e mantenha a coleta educada (um segundo entre pedidos, só o necessário).
- **Existe e permite o caminho**: siga. Se houver `Crawl-delay: N`, o raspador espera `max(1, N)` segundos entre pedidos.
- **Proíbe o caminho** (`Disallow` que cobre a página de busca ou a API no grupo que vale para o raspador): **pare**. Não troque o User-Agent para escapar da regra. Pela RFC 9309, vale o grupo cujo `User-agent` é o nome do raspador (`raspador-de-pesquisa`) e, se não houver, o de `User-agent: *`; dentro do grupo, vence a regra de caminho mais longo, não a primeira do arquivo (`Allow: /` antes de `Disallow: /busca` proíbe `/busca`), e no empate vence o `Allow`. `*` no caminho vale qualquer sequência e `$` marca o fim. O script já lê assim; confira à mão só quando o arquivo for confuso.
- **Redireciona para caminho proibido ou para outro site**: o script segue até cinco redirecionamentos, um a um, e não pede o destino que o `robots.txt` proíbe nem o que fica em outro domínio; a saída diz "proibido pelo robots.txt, não pedido" ou "outro site, não pedido". Se a página de busca cair em caminho proibido, trate como caminho proibido: o script diz isso já na seção 1 e sai com o mesmo código 2 do caminho proibido. Se ela for para outro site (inclusive de `site.gov.br` para `www.site.gov.br`), rode o script de novo com o endereço de destino, para que o `robots.txt` de lá seja lido.
- **Devolve outro 4xx (401, 403, 410)**: a norma do `robots.txt` (RFC 9309, seção 2.3.1.3) trata como arquivo indisponível, igual ao 404. Mas um 403 no `robots.txt` costuma vir de um bloqueio de robôs: confira se a página de busca também devolve 403 ao `requests`; se devolver, é a pergunta 4, e a coleta para.
- **Devolve 5xx ou não responde**: a mesma norma manda tratar como proibição total enquanto durar. Não colete agora; diga ao usuário para tentar mais tarde.

Duas coisas que **não** são proibição de coleta e não devem parar o trabalho:

- `<meta name="robots" content="noindex">` e o cabeçalho `X-Robots-Tag: noindex` pedem que buscadores não ponham a página no índice deles. Não falam de acesso. Registre no relato que existem.
- `Disallow` de caminhos que o raspador não usa (painel administrativo, busca interna de outra seção).

## 2. Os termos de uso permitem?

Procure, na página inicial e no rodapé, links como "Termos de uso", "Condições de uso", "Política de privacidade", "Aviso legal", "Política de dados". Leia o trecho sobre uso automatizado, robôs, raspagem, reprodução e uso comercial.

- Proíbe coleta automatizada, robôs ou raspagem: **pare**.
- Exige autorização prévia ou cadastro para uso dos dados: **pare** e diga como pedir.
- Não há termos no site: registre "sem termos de uso encontrados" e siga.

Portal de dados abertos ou página que oferece download do conjunto inteiro (CSV, planilha, API documentada) muda a resposta: use o download oficial em vez de raspar, e diga isso ao usuário.

## 3. Precisa de login?

Sinais: a busca devolve 401 ou 403 logo no primeiro pedido, redireciona para uma página de entrada, a página tem campo de senha, ou a documentação pede chave de acesso pessoal, token ou certificado digital.

Se o dado só aparece com login, **pare**. O raspador desta skill não guarda senha, não usa sessão de alguém nem certificado. Chave de API pública e gratuita, que o próprio site distribui para esse fim, é outra coisa: explique ao usuário como obtê-la e leia-a de uma variável de ambiente, nunca escrita no código.

## 4. Há captcha ou bloqueio anti-robô?

Sinais no HTML ou nos cabeçalhos: `g-recaptcha`, `recaptcha/api.js`, `hcaptcha`, `cf-turnstile`, `challenge-platform`, a página "Just a moment..." ou "Checking your browser", cabeçalho `cf-mitigated`, 403 ou 503 com HTML de desafio, ou um 403 que aparece com `requests` e não no navegador.

Se houver, **pare**. Não tente resolver captcha, simular navegador, trocar de IP, girar User-Agent nem copiar cookies do navegador para passar pelo bloqueio. O bloqueio é a forma de o site dizer que não quer robôs ali.

Um único 429 ("pedidos demais") não é bloqueio: é o site pedindo calma, e o raspador trata esperando o `Retry-After`.

## 5. O dado é pessoal? É sensível?

Dado pessoal é o que identifica ou permite identificar uma pessoa (nome, CPF, endereço, número de processo ligado a uma parte). Coletar dado pessoal para pesquisa é possível, mas pede cuidado: colete só os campos que a pergunta de pesquisa usa e diga ao usuário que a tabela tem dados pessoais e precisa ser guardada com cuidado.

**Dado pessoal sensível** (art. 5º, II, da LGPD): origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou a organização religiosa, filosófica ou política, dado referente à saúde ou à vida sexual, dado genético ou biométrico, quando ligado a uma pessoa. Se a coleta pedida reúne esse tipo de dado sobre pessoas identificáveis, **pare** e explique: o tratamento depende de base legal específica (art. 11 da LGPD) e, em pesquisa, costuma passar por comitê de ética. Dado agregado ou anonimizado (contagem por estado, por ano) não tem esse problema.

### Decisões de tribunal: segredo de justiça

Processo em segredo de justiça (art. 189 do CPC: quando o interesse público ou social o exigir; casamento, divórcio, união estável, filiação, alimentos e guarda; dados protegidos pela intimidade; arbitragem com confidencialidade comprovada) não aparece na consulta pública, ou aparece só com o número. Ao coletar de tribunal:

- não tente obter o conteúdo de processo marcado como sigiloso ou em segredo, nem por outro endereço;
- se um pedido por processo devolve 403 ou mensagem de sigilo, registre o número como "acesso negado" e siga para o próximo, sem insistir;
- diga no relato quantos processos ficaram de fora por sigilo, se o site permitir saber;
- lembre o usuário de que nomes de partes em decisões publicadas continuam sendo dado pessoal.

## Como avisar ao parar

O aviso diz o que foi visto, onde e o que fazer em seguida. Exemplo:

> Não escrevi o raspador. O `robots.txt` de site.gov.br tem `Disallow: /consulta/`, que cobre a página de busca que você indicou, para qualquer robô. Caminhos possíveis: procurar o mesmo dado no portal de dados abertos do órgão, pedir pela Lei de Acesso à Informação (Lei 12.527/2011) ou pedir autorização ao órgão.

## O que registrar para o relato

- O que o `robots.txt` disse, com o endereço consultado e o código de resposta (inclusive "404, não existe").
- Se havia termos de uso, onde, e o que dizem sobre coleta.
- Sinais de login, captcha ou bloqueio: "nenhum encontrado" também se registra.
- Se o dado é pessoal, e se é sensível.
