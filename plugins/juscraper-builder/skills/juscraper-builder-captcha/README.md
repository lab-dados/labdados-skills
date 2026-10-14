# juscraper-builder-captcha

Skill para Claude Code que decide o que fazer quando o formulário de um tribunal brasileiro tem captcha e o raspador vai para a biblioteca [juscraper](https://github.com/jtrecenti/juscraper). Ela é um desvio da skill `juscraper-builder`, que mora ao lado no mesmo plugin: decide o captcha e devolve o fluxo para lá, usando as referências, os scripts e o template da `juscraper-builder`.

## Instalação

Vem com o plugin `juscraper-builder` do marketplace `labdados-skills`:

```
/plugin install juscraper-builder@labdados-skills
```

Instalar esta pasta sozinha não funciona, porque ela lê `../juscraper-builder/`.

## O que a skill faz

1. Classifica o captcha: imagem com texto, interativo (reCAPTCHA, hCaptcha, Turnstile) ou desafio de WAF, que não é captcha e volta para a `juscraper-builder`.
2. Testa sempre se o backend valida o captcha; se não valida, segue como tribunal sem captcha (precedentes: TJRJ e TJGO).
3. Captcha de imagem validado: resolve com `txtcaptcha`, dependência opcional com import lazy, mockado nos contratos.
4. Captcha interativo validado: para, registra o caso em `docs/captcha/` do juscraper e não gera raspador parcial.

## Estrutura

```
juscraper-builder-captcha/
├── SKILL.md                 # Desvio de captcha
├── README.md                # Este arquivo
└── references/
    └── txtcaptcha.md        # Esqueletos da função que resolve e do teste com mock
```

## Requisitos

- Os da `juscraper-builder`.
- Para captcha de imagem: `txtcaptcha`, que no juscraper entra pelo extra `[tjmg]` (`uv sync --extra dev --extra tjmg`).
