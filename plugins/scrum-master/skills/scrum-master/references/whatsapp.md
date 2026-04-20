# Coleta de dados do WhatsApp

O usuário exporta o histórico do WhatsApp periodicamente em um `.zip` que fica na pasta do projeto. Formato típico: `WhatsApp Chat with LabDados.zip`.

## Conteúdo do zip

- `_chat.txt` (ou `WhatsApp Chat*.txt`) — texto puro com as mensagens.
- Anexos (imagens, áudios, PDFs) referenciados por nome no `_chat.txt`.

## Formato das mensagens

iOS e Android exportam em formatos ligeiramente diferentes. Exemplos:

**iOS:**
```
[15/04/2026, 14:32:07] Julio Trecenti: Pessoal, reunião amanhã cancelada
```

**Android:**
```
15/04/2026, 14:32 - Julio Trecenti: Pessoal, reunião amanhã cancelada
```

Mensagens multilinha continuam na linha seguinte sem timestamp até a próxima mensagem. Mídia aparece como `<Media omitted>` ou `<anexado: IMG-...>`.

## Como extrair

Use **sempre** o script `scripts/parse_whatsapp.py`:

```bash
python scripts/parse_whatsapp.py <caminho/para/WhatsApp Chat*.zip> --since-days 7 > /tmp/whatsapp_week.json
```

O script:
1. Procura o zip mais recente no padrão dado (ou aceita caminho direto).
2. Extrai `_chat.txt`.
3. Detecta o formato (iOS vs Android) pelo regex do header.
4. Normaliza em JSON com `{author, timestamp, text, is_media}`.
5. Filtra pelos últimos N dias.

Se o script falhar (zip corrompido, formato estranho), caia para leitura direta do `_chat.txt` e faça parse manual — não desista da fonte.

## Sinais a extrair

Olhe além do literal das mensagens:

- **Decisões** — procure verbos como "vamos", "decidido", "fechado", "ficou que", "combinamos".
- **Dúvidas em aberto** — mensagens com `?` que não receberam resposta de ninguém em até 24h.
- **Entregas anunciadas** — "subi", "pushei", "mandei", "subi o PR", "enviei".
- **Bloqueios** — "travei", "não consigo", "alguém sabe", "tá dando erro".
- **Tom** — pessoas mandando muitos `ok` curtos pode indicar desengajamento; múltiplas mensagens seguidas em tom animado indicam fluxo.
- **Ausências** — quem participava semanas anteriores e sumiu.

## Privacidade

O histórico pode ter conteúdo pessoal/fora do trabalho. **Não reproduza literalmente** no relatório mensagens que soem pessoais. Resuma em terceira pessoa. Se alguém compartilhou um número/endereço/info sensível, simplesmente não inclua. Em dúvida, pule.

## Autoria

O nome de cada autor é o nome que o contato está salvo no celular do usuário. Esses nomes podem diferir do handle do GitHub. Registre o mapeamento inferido em `weekly-plan/.team-inferred.json` para evoluir entre execuções — ex.:

```json
{
  "Julio Trecenti": {"github": "julio-trecenti", "confidence": "high"},
  "Maria": {"github": "maria-xyz?", "confidence": "low"}
}
```
