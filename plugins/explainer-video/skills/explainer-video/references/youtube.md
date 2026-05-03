# Upload no YouTube — setup OAuth e fluxo

## Setup primeira vez (passo único, ~5 minutos)

A skill faz upload via YouTube Data API v3 com OAuth. Setup:

1. Vá pra https://console.cloud.google.com/
2. Crie um projeto novo (ou use um existente). Anote o ID.
3. Em "APIs & Services" → "Library", procure "YouTube Data API v3" e habilite.
4. Em "APIs & Services" → "Credentials":
   - "Create credentials" → "OAuth client ID"
   - Application type: **Desktop app**
   - Nome: "Explainer Video Skill" (ou o que quiser)
   - Crie e clique no botão de download → vai baixar um `client_secret_XXX.json`
5. Salve o arquivo em algum lugar (ex.: `~/.config/explainer-video/client_secret.json`)
6. Exporte a env var:
   ```bash
   export YT_CLIENT_SECRET_PATH=~/.config/explainer-video/client_secret.json
   ```
   (Adicione no seu shell rc para ficar permanente.)

Na primeira vez que rodar `upload_youtube.py`, ele vai abrir o navegador pedindo pra você logar no YouTube e autorizar. Depois disso o token fica cacheado em `~/.explainer-video-yt-token.json` e os uploads seguintes são silenciosos.

### OAuth consent screen

Se for a primeira vez no projeto Google Cloud, você vai precisar configurar a "OAuth consent screen":
- User type: **External** (mesmo que use só você)
- App name: qualquer
- Adicione **seu email** como "Test user" (enquanto o app está em modo Testing — válido para uso pessoal indefinidamente, com limite de 100 users)
- Scopes: pode pular, o `youtube.upload` é solicitado em runtime

## Quotas

Padrão: 10.000 unidades/dia. Cada upload custa ~1.600 unidades. Ou seja: ~6 uploads por dia. Mais que suficiente para uso normal. Pra subir o limite, pede via formulário no Cloud Console (raramente necessário).

## Uso na skill

Depois do setup, a skill chama:

```bash
python upload_youtube.py \
    --video /caminho/final.mp4 \
    --title "Tour do MyApp" \
    --description "$(cat description.txt)" \
    --tags "demo,opensource,myapp" \
    --privacy unlisted
```

Output JSON:
```json
{"video_id": "AbCdEf12345", "url": "https://youtu.be/AbCdEf12345", "privacy": "unlisted"}
```

Você pega esse URL e entrega pro usuário.

## Categorias (`--category`)

Defaults para `28` (Science & Technology). Outras úteis:
- 22: People & Blogs
- 24: Entertainment
- 26: Howto & Style
- 27: Education
- 28: Science & Technology

## Título e descrição: defaults sensatos

Se o usuário não especificou, gere automaticamente:

**Título** (max 100 chars):
```
Demo: <Nome da Ferramenta>
```
ou para uma feature específica:
```
<Nome da Ferramenta> — <Feature>
```

**Descrição** (max 5000 chars):
```
<Descrição extraída do README, 1-2 parágrafos>

🔗 Repositório: <url do repo>
🌐 Demo ao vivo: <url live se houver>

Vídeo gerado automaticamente com a skill explainer-video.
```

Sempre **mostre o título/descrição propostos** ao usuário antes do upload. Ele pode querer ajustar.

## Quando o upload falha

| Erro | Causa | Fix |
|------|-------|-----|
| `quotaExceeded` | passou os 10k/dia | Espere até amanhã (reset 00:00 PST) |
| `unauthorized_client` | token expirou e refresh falhou | Delete `~/.explainer-video-yt-token.json` e refaça login |
| `videoChatDisabled` ou similar | conta YouTube novinha sem upload habilitado | Faça um upload manual primeiro pra "ativar" a conta |
| `client_secret.json` não achado | env var não setada | `export YT_CLIENT_SECRET_PATH=...` |

## Fallback: salvar pra upload manual

Se o usuário não quer/não pode setup OAuth:

1. Salve o `final.mp4` em outputs/
2. Gere um `youtube_metadata.txt` com o título e a descrição sugeridos
3. Diga pro usuário: "Salvei o vídeo em [link] e a descrição sugerida em [link]. Quando quiser subir manualmente: youtube.com/upload, escolha 'Não listado' na privacidade."

## Privacidade — sempre **unlisted** por default

A skill **NUNCA** sobe vídeos como `public` sem confirmação explícita. Default é `unlisted`. Se o usuário pedir `public`, confirme outra vez antes:

> "Confirmando: você quer este vídeo PÚBLICO no YouTube (visível por qualquer um, indexado pela busca)?"
