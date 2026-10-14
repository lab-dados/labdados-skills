---
name: juscraper-builder-captcha
description: >
  Desvio de captcha da skill juscraper-builder: decide o que fazer quando a
  página de consulta de um tribunal brasileiro mostra captcha e o raspador
  vai para a biblioteca juscraper. Use quando o usuário pedir um raspador
  para tribunal com captcha (imagem com texto, reCAPTCHA, hCaptcha,
  Cloudflare Turnstile) ou quando a checagem inicial da juscraper-builder
  encontrar captcha. Sempre testa primeiro se o backend valida o captcha,
  porque muitos tribunais exibem o widget e não conferem o token; captcha
  de imagem validado se resolve com o pacote txtcaptcha; captcha interativo
  validado encerra o trabalho com o registro em docs/captcha/. Também
  acionar quando um raspador existente do juscraper passar a receber
  captcha, ou com "não sou um robô", "código da imagem", "digite os
  caracteres", "verificação de segurança falhou". Fora do captcha, o fluxo
  inteiro é o da juscraper-builder, que esta skill usa.
  Não confundir com a juscraper-builder (formulário sem captcha) nem com
  desafio JavaScript de WAF sem captcha (STF, TJPE), que a juscraper-builder
  trata pelo extra juscraper[waf].
---

# Juscraper Builder (desvio de captcha)

Esta skill não repete o fluxo de construção do raspador. Ela cobre só a decisão sobre o captcha e devolve o controle à skill `juscraper-builder`, que mora ao lado, em `../juscraper-builder/` (as duas vêm no mesmo plugin). Leia `../juscraper-builder/SKILL.md` antes de começar: preparação, mapeamento de todos os campos com confirmação do usuário, captura, código, testes e documentação seguem de lá, assim como as referências, os scripts e o template em `../juscraper-builder/references/`, `../juscraper-builder/scripts/` e `../juscraper-builder/assets/`.

A convenção do juscraper vence esta skill quando divergirem. As fontes estão mapeadas em `../juscraper-builder/references/juscraper-conventions.md`.

## Onde esta skill entra

Na Etapa 1.1 da `juscraper-builder` ("Captcha primeiro"), quando o formulário ou a resposta da busca trouxer captcha. Siga os passos abaixo em ordem, sem pular o C2.

## C1. Classificar

- **De imagem com texto**: `<img>` com caracteres distorcidos e um `<input>` para digitá-los. A imagem costuma vir de um endpoint próprio (`captcha.png`, `gerarImagem`, `imagemCaptcha`) ou embutida em base64 no formulário (TRF6).
- **Interativo**: reCAPTCHA v2 ou v3, hCaptcha, Cloudflare Turnstile, FriendlyCaptcha, Arkose. Aparece como script de `google.com/recaptcha`, `hcaptcha.com` ou `challenges.cloudflare.com`, ou como div `.g-recaptcha`, `.h-captcha`, `.cf-turnstile`.
- **Desafio de WAF sem captcha** (resposta 202 com página de desafio JavaScript, cabeçalho `x-amzn-waf-action`): não é caso desta skill. Volte à `juscraper-builder`, seção "Princípio".
- **Outro desafio de bot manager sem widget** (managed challenge do Cloudflare, por exemplo): também não é captcha. Volte à `juscraper-builder`, seção "Decisões de projeto", item do site sem API acessível por `requests`.

## C2. Testar sem resolver (sempre)

Pegue a requisição de busca como a Etapa 1.3 da `juscraper-builder` descreve e reproduza com `curl` ou `requests`, sem o navegador: primeiro omitindo o campo do captcha, depois com ele vazio, depois com um valor qualquer.

A linha de base é uma busca com o captcha preenchido, e quem preenche é o usuário, no navegador dele, entregando a resposta (HTML ou HAR). Nenhum agente resolve captcha, nem num navegador automatizado da sessão. Sem essa resposta, compare as três tentativas com uma página de resultados conhecida do mesmo tribunal e com a mensagem de erro que o site mostra.

Repita o teste na página 2 e em cada endpoint que o raspador vai usar, porque há site que só valida em algumas rotas ou cuja validação expira no meio da paginação (no TJMG, a página seguinte volta com HTTP 401 e o raspador revalida).

- **Resposta igual**: o captcha é decorativo. Volte à Etapa 1.2 (Família) da `juscraper-builder` e trate o tribunal como sem captcha. No código, mande o campo como o backend aceita e diga numa docstring que o captcha aparece e não é validado. Precedentes: TJRJ (`courts/tjrj/`, reCAPTCHA exibido e não validado) e TJGO (`courts/tjgo/download.py`, `g-recaptcha-response` e `cf-turnstile-response` vazios).
- **Resposta de erro** ("captcha inválido", redirecionamento, página sem resultados que o navegador mostra com resultados): o captcha é validado. Siga para C3 ou C4 conforme o tipo.

Guarde as respostas desse teste: são a evidência que o PR e o registro em `docs/captcha/` vão citar.

## C3. Imagem validada: `txtcaptcha`

O pacote [`txtcaptcha`](https://github.com/jtrecenti/txtcaptcha), do mesmo autor do juscraper, decodifica captchas de imagem de tribunais brasileiros. Modelos no juscraper:

- `courts/tjmg/download.py`: captcha numérico de 5 dígitos sobre `HTTPScraper` com `request_fn`, validado por uma chamada DWR antes da busca, com novas tentativas quando o OCR erra e revalidação quando a sessão expira. Copie dele só a lógica do captcha: o arquivo não tem payload builder público, depende de dispensas herdadas no `ruff.toml` e deixa o limite de tentativas interno, e por isso está entre os que `../juscraper-builder/references/juscraper-conventions.md` manda não usar como modelo.
- `courts/trf6/download.py`: imagem em base64 no próprio formulário, texto livre. O TRF6 herda `BaseScraper` e cria a própria sessão; copie dele também só a lógica do captcha, e dele vem o limite como parâmetro do raspador.

Regras do fluxo:

1. **Dependência opcional.** `txtcaptcha` nunca entra em `dependencies`. O juscraper hoje o oferece pelo extra `[tjmg]` do `pyproject.toml`; pergunte ao mantenedor se o tribunal novo reusa esse extra ou ganha outro. Para desenvolver: `uv sync --extra dev --extra tjmg`.
2. **Import lazy** dentro da função que resolve, com `ImportError` que diz como instalar.
3. **Mesma sessão** para baixar a imagem, validar e buscar, porque o cookie de sessão amarra o captcha.
4. **Nova tentativa semântica** quando o backend recusar o texto: baixar outro captcha, com limite exposto como parâmetro do raspador (`max_captcha_attempts` no TRF6, default 3, o mesmo número que o TJMG usa) e `logger.warning` a cada falha. Esse laço é separado do retry HTTP do `_request_with_retry`.
5. **De volta ao fluxo.** Depois de decidir o captcha, volte à Etapa 1.2 (Família) da `juscraper-builder`, porque há família com captcha própria (o eSAJ tem marcador de captcha e manda `uuidCaptcha` vazio), e siga para o mapeamento de todos os campos e a confirmação do usuário, que continuam obrigatórios. O campo do captcha entra no corpo, não no schema.
6. **Rede do modelo.** Na primeira chamada, `txtcaptcha.decrypt` baixa o modelo do Hugging Face Hub e o guarda em `~/.cache/huggingface/hub`. O script de captura e a integração precisam dessa rede; os contratos, com o fake, não.

Esqueleto da função e dos testes em `references/txtcaptcha.md`.

**Testes.** O `txtcaptcha` é mockado nos contratos e nunca roda neles (`CONTRIBUTING.md` do juscraper, "Adding a new tribunal", item de captchas e libs externas): injete um fake em `sys.modules` (fixture `mock_txtcaptcha` em `tests/tjmg/conftest.py`) ou substitua a função que resolve (`solve_captcha` em `tests/trf6/test_cpopg_contract.py`). Fluxo com ordem obrigatória (imagem, validação, busca) usa `responses.registries.OrderedRegistry`. Capture também a resposta de "captcha inválido" e teste o caminho da nova tentativa. Só o script de captura e a integração opcional rodam o `txtcaptcha` de verdade; se ele errar demais no tribunal, avise o usuário antes de seguir.

## C4. Interativo validado: parar

Não use serviço pago de resolução, não automatize clique no widget e não tire token por navegador no código final. Avise o usuário com o tipo detectado, a URL e a evidência do C2, e registre o caso em `docs/captcha/<xx>_captcha.md`, em inglês como o resto de `docs/`, no formato de `docs/captcha/tjse_captcha.md` (Turnstile) e `docs/captcha/tjma_captcha.md` (reCAPTCHA v2 invisível). Não gere raspador parcial.

Se o captcha aparecer num tribunal que o juscraper já raspa, o precedente é o TJAP: o método levanta uma exceção própria com a explicação (`TJAPSecurityCheckError`, em `courts/tjap/exceptions.py`) em vez de devolver vazio, e o aviso de indisponibilidade aparece no `README.md` e no `docs/index.qmd` do juscraper.
