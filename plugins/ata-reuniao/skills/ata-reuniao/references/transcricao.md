# Transcrição via labdados-sdk

Quando só há áudio/gravação (sem transcrição pronta), use o pacote Python [`labdados`](https://github.com/lab-dados/labdados-sdk) — SDK oficial dos serviços do escritório de apoio.

## Instalação

```bash
pip install labdados        # base — modo nuvem do escritório (não processa local)
```

O modo nuvem não exige extras: o processamento pesado roda nos servidores do escritório (Azure, São Paulo).

## API key

A transcrição em nuvem precisa de uma API key (`sk_lab_...`), obtida no portal:

<https://labdados-frontend.livelydesert-3e3e3dd8.brazilsouth.azurecontainerapps.io/consultoria/api-key>

Preferência de origem da key, nesta ordem:
1. Variável de ambiente `LABDADOS_API_KEY`.
2. Passada pelo usuário na conversa.
3. Se não houver, **não trave**: registre na ata "transcrição automática indisponível (sem API key)" e peça o arquivo de transcrição ou anotações ao usuário.

Nunca imprima a key no relatório, em logs ou na ata. Trate como senha.

## Chamada

```python
import labdados

labdados.transcricao(
    arquivos="reuniao.m4a",          # arquivo único, lista ou pasta
    api_key="sk_lab_...",
    modelo="whisperx",               # WhisperX = transcrição + diarização
    diarizacao=True,
    saida="transcricao_out/",
)
```

A função faz upload, dispara o processamento, faz polling até concluir e baixa um `.zip` em `saida/`. Extraia o zip; dentro há a transcrição (texto e/ou `.vtt`/`.json` com falantes `SPEAKER_00`, `SPEAKER_01`, …). Mapeie os falantes a nomes reais pelo contexto (quem fala de quê) e, se acessível, pelo `weekly-plan/.team-inferred.json` da skill `scrum-master`.

## Privacidade

O serviço usa máquina na Azure em São Paulo e **apaga o arquivo em 72h** (informado pelo Julio à equipe). Ainda assim, reuniões podem ter conteúdo sensível (remuneração, processo seletivo, avaliação de pessoas): a ata resume de forma factual e neutra, não reproduz fala literal delicada. Em dúvida, omita.

## Fallback

Serviço fora do ar, timeout, sem key, ou áudio corrompido: não desista da ata. Gere-a a partir do que houver (anotações do usuário, transcrição parcial, pauta + insumos de chat) e marque claramente a limitação no campo **Fonte** e no rodapé. Uma ata honesta e parcial é útil; uma ata inventada não.
