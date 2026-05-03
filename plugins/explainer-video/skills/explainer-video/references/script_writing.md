# Como escrever um bom roteiro

Esse é o documento mais importante. Roteiro ruim → vídeo ruim, mesmo com produção perfeita.

## Princípios

**1. Pense em segundos, não em palavras.** Conte mentalmente: "isso vai durar quanto?" 150 palavras/minuto é um ritmo confortável de narração em PT-BR. Se você tem 90s de orçamento, isso são ~225 palavras totais — pouco. Corte sem dó.

**2. Cada cena = uma ideia.** Se uma cena tem dois conceitos, divida em duas cenas. O motivo: o `merge_av.py` sincroniza por cena, então cada bloco fica coeso e a edição fica natural.

**3. Mostre, não fale.** Se você está narrando "agora clico no botão de login", o espectador VÊ você clicando. Narração redundante é cansativa. Em vez disso: narre o **porquê**, não o **o quê**. "O login usa SSO do Google porque o público-alvo são times pequenos" é melhor que "clico em login com Google".

**4. Comece com o problema/contexto.** Os primeiros 10 segundos importam mais que tudo. "Esse projeto resolve X" pega muito mais atenção que "essa é a tela inicial".

## Estrutura recomendada por duração

### Vídeo curto (30-60s) — uma feature
- **Hook (5s)**: o problema que essa feature resolve
- **Demo (20-40s)**: você usando a feature, narrando o **porquê** das decisões de design
- **Fecho (5-10s)**: como acessar / próximo passo

### Vídeo overview (60-120s) — ferramenta inteira
- **Hook (10s)**: o que a ferramenta faz, em uma frase
- **Tour rápido (60-90s)**: 3-4 features principais, ~20-30s cada
- **Fecho (10-15s)**: link, repo, como contribuir

### Vídeo longo (2-3min) — só com confirmação
Mesma estrutura, mas com uma seção de "casos de uso" ou "exemplos avançados" no meio.

## Anatomia de uma cena no script.json

```json
{
  "narration": "Aqui você usa filtros pra restringir por data e tipo de evento. Ele aplica em tempo real, sem reload.",
  "actions": [
    {"type": "goto", "url": "/dashboard"},
    {"type": "wait", "ms": 1200},
    {"type": "highlight", "selector": ".filter-bar"},
    {"type": "click", "selector": "button[data-filter='date']"},
    {"type": "wait", "ms": 800},
    {"type": "click", "selector": ".date-preset-7d"},
    {"type": "wait", "ms": 1500}
  ],
  "duration_hint_seconds": 9
}
```

Notas:
- `narration` deve ter ~22 palavras se a cena dura ~9s (150wpm)
- `actions` deve consumir aproximadamente o mesmo tempo da narração — use `wait` para preencher se necessário
- `highlight` é ótimo no início de uma cena para focar a atenção antes do clique

## Dicas de pacing

- **Sempre dê `wait` de 800-1500ms entre clique e ação seguinte.** Sem isso o vídeo vira piscar de janela.
- **Para `type`**: use `delay_ms: 60` ou mais. Digitação instantânea parece bug.
- **Cenas de 5-12s funcionam bem.** Cenas <4s são piscadas; >15s perde o ritmo.
- **Use silêncio em transições.** Uma cena curta sem narração (apenas `narration: ""`) entre dois blocos densos dá fôlego.

## Exemplos de narração ruim → boa

**Ruim:** "Agora clico no botão chamado 'Novo Projeto', que abre um modal."
**Boa:** "A criação de projeto é feita inline — sem sair da tela inicial."

**Ruim:** "Aqui está a página de configurações onde você pode mudar várias coisas."
**Boa:** "As configurações ficam por workspace, não por usuário — útil para times com várias contas."

**Ruim:** "Vamos digitar 'exemplo@email.com' no campo de email e a senha no próximo."
**Boa:** "Login passwordless: só pedimos o email e mandamos um link mágico."

## Validando antes de gravar

Antes de chamar `record_demo.py` no vídeo final:

1. **Leia a narração em voz alta.** Cronometre. Bateu com `duration_hint_seconds` total? Se passou muito, corte.
2. **Tire screenshots dos pontos-chave.** Modifique temporariamente o script.json para ter só `goto` + `screenshot` em cada cena. Verifica que os seletores funcionam ANTES de gravar 2 minutos de vídeo.
3. **Mostre o roteiro pro usuário.** Em formato legível (não JSON). Ele provavelmente vai querer reescrever 30% — melhor descobrir agora.

## Output do roteiro: dois formatos

Sempre produza DOIS artefatos:

1. **`script.json`** — formato máquina, consumido pelos scripts
2. **`script.md`** — formato legível pra humano revisar (use isso pra mostrar ao usuário)

Exemplo de `script.md`:

```markdown
# Roteiro: MyApp Dashboard Tour
**Duração estimada**: 75 segundos

## Cena 1 (0-10s) — Hook
> O MyApp resolve o problema de monitorar dezenas de pipelines em uma tela só.

[Ações: abrir homepage, esperar logo carregar]

## Cena 2 (10-30s) — Filtros
> Os filtros aplicam em tempo real, sem reload — útil pra debug rápido.

[Ações: clicar filter bar, aplicar preset 7d]
```

Esse formato espelha as cenas do JSON e deixa o usuário rever a narração + saber quais ações vão acontecer.
