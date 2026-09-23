# Padrões Comuns de Sites de Tribunais Brasileiros

Referência rápida sobre tecnologias e padrões encontrados nos sites
dos tribunais brasileiros. Ajuda a antecipar o que esperar antes de
fazer a engenharia reversa.

## Sistemas comuns

### eSAJ (Softplan)
- Usado por: TJSP, TJMS, TJAM, TJCE, TJAL, TJAC e outros
- No juscraper: família `courts/_esaj/`; tribunal eSAJ novo é uma
  subclasse de `EsajSearchScraper` (ver `CONTRIBUTING.md` > "Adding an
  eSAJ tribunal")
- URL tipicamente contém: `esaj.`, `consultasaj.`
- Formulário: POST com `application/x-www-form-urlencoded`
- Paginação: parâmetro `paginaConsulta` (1-based)
- Sessão: JSESSIONID cookie obrigatório
- Peculiaridade: frequentemente usa `latin-1` no encoding
- Captcha: TJSP não usa; outros podem usar

### PJe (CNJ)
- Usado por: vários TRTs, TRFs, e alguns TJs
- URL: `pje.{tribunal}.jus.br`
- API: REST com JSON
- Autenticação: pode requerer certificado digital
- Paginação: offset-based
- Peculiaridade: API bem estruturada quando acessível
- No juscraper: TRF1, TRF3 e TRF5 (`cpopg`) compartilham
  `courts/_trf/` (`TRFConsultaScraper`); o portal fica atrás do Akamai,
  que bloqueia IP de datacenter (testes de integração com marker
  `anti_bot`)

### eproc
- Usado por: TRF6 (`eproc1g.trf6.jus.br`)
- Captcha de imagem validado no backend, resolvido com `txtcaptcha`

### Sistemas próprios
- TJDFT: sistema customizado, API JSON
- TJRS: sistema customizado, HTML server-rendered
- TJPR: sistema customizado
- TJMG: sistema customizado, captcha numérico de imagem
- TJRJ: sistema customizado, frequentemente com WAF restritivo
- STF: API Elasticsearch atrás do AWS WAF (desafio JavaScript)

## Padrões de URL

```
# Jurisprudência (cjsg)
https://esaj.tjsp.jus.br/cjsg/resultadoCompleta.do
https://www.tjrs.jus.br/buscas/jurisprudencia/
https://pesquisajuris.tjdft.jus.br/
https://www5.tjmg.jus.br/jurisprudencia/

# Processos 1º grau (cpopg)
https://esaj.tjsp.jus.br/cpopg/open.do
https://www.tjrs.jus.br/buscas/processos/

# Processos 2º grau (cposg)
https://esaj.tjsp.jus.br/cposg/open.do
```

## Tratamento de encoding

Muitos tribunais usam encoding diferente de UTF-8:

```python
# Detectar encoding real
response.encoding = response.apparent_encoding

# Ou forçar se souber
response.encoding = "latin-1"  # Comum em eSAJ

# Verificar no HTML
# <meta charset="ISO-8859-1">
# <meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
```

## Headers comuns necessários

```python
# O User-Agent padrão vem do HTTPScraper; troque em _configure_session
# só quando o site exigir UA de navegador (ex.: TJRJ, STF).
headers = {
    # eSAJ frequentemente verifica Referer
    "Referer": "{url_do_formulario}",
    # Alguns sites verificam Accept
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    # Para APIs JSON
    "Accept": "application/json",
    "Content-Type": "application/json",
}
```

## Captchas conhecidos

| Tribunal | Tipo de captcha     | Status          |
|----------|---------------------|-----------------|
| TJSP     | Nenhum (cjsg/cpopg) | ✓ Funciona      |
| TJRS     | Nenhum              | ✓ Funciona      |
| TJPR     | Nenhum              | ✓ Funciona      |
| TJDFT    | Nenhum              | ✓ Funciona      |
| TJMG     | Imagem numérica, validada; `txtcaptcha` | ✓ Funciona (extra `[tjmg]`) |
| TRF6     | Imagem, validada; `txtcaptcha` | ✓ Funciona |
| TJRJ     | reCAPTCHA exibido, não validado no backend | ✓ Funciona |
| TJGO     | Campos de reCAPTCHA/Turnstile enviados vazios | ✓ Funciona |
| TJAP     | Cloudflare Turnstile, validado | ✗ Bloqueado |
| STF      | Sem captcha; desafio JavaScript do AWS WAF | ✓ Funciona (token via extra `[stf]`) |

**Nota**: Esta tabela pode estar desatualizada. Sempre verificar
na prática durante a Etapa 1 do workflow.

## Dicas de debugging

1. **Comparar com browser**: Abrir DevTools no Chrome, aba Network,
   e comparar as requisições manuais com as feitas pelo scraper

2. **Cookies**: Se o site retorna 403 ou redireciona para login,
   provavelmente falta um cookie de sessão. Fazer GET na página
   inicial primeiro.

3. **CSRF tokens**: Alguns sites embutem tokens no HTML que devem
   ser extraídos e reenviados. Procurar por campos hidden no form
   ou meta tags com nomes como `csrf`, `token`, `_token`.

4. **Rate limiting**: Se começar a receber 429 ou respostas vazias,
   aumentar o delay entre requisições.

5. **Redirect loops**: Se o site redireciona infinitamente, pode ser
   que o cookie de consentimento (LGPD) não está sendo aceito.
   Verificar se há um endpoint de aceite de cookies.
