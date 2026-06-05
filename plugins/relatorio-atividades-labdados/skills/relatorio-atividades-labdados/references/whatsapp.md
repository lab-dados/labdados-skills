# Coleta de dados do WhatsApp (história completa)

> Adaptado de `plugins/scrum-master/.../whatsapp.md`. Aqui não filtramos por janela de
> 7 dias: lemos o histórico inteiro para extrair marcos e decisões ao longo do tempo.

O usuário exporta o histórico do WhatsApp em um `.zip` que fica na pasta do projeto.
Formato típico: `WhatsApp Chat with LabDados.zip`.

## Conteúdo do zip

- `_chat.txt` (ou `WhatsApp Chat*.txt`), texto puro com as mensagens.
- Anexos referenciados por nome no `_chat.txt`.

## Como extrair

Use **sempre** o script `scripts/parse_whatsapp.py`, **sem** `--since-days`, para pegar
todo o histórico:

```bash
python scripts/parse_whatsapp.py "<caminho/para/WhatsApp Chat*.zip>" > /tmp/whatsapp_full.json
```

O script procura o zip, extrai o `_chat.txt`, detecta o formato (iOS ou Android) e
normaliza em JSON com `{author, timestamp, text, is_media}`. Se o script falhar, leia
o `_chat.txt` direto e faça parse manual. Não desista da fonte.

Se o histórico for muito grande, processe por blocos de tempo (por mês ou por
trimestre) e vá consolidando os marcos, em vez de tentar ler tudo de uma vez.

## Sinais a extrair (visão de história)

- **Marcos e decisões** ao longo do tempo: lançamentos, eventos combinados,
  parcerias firmadas, contratações, datas de oficinas e cursos.
- **Eventos e parcerias** mencionados, com a data aproximada.
- **Processo seletivo:** mensagens sobre vagas, candidaturas, entrevistas.
- Não interessa aqui o "tom da semana" nem dúvidas em aberto de curto prazo. O foco é
  o que virou fato relevante para a prestação de contas.

## Privacidade

O histórico pode ter conteúdo pessoal ou fora do trabalho. **Não reproduza
literalmente** mensagens que soem pessoais. Resuma em terceira pessoa. Se alguém
compartilhou número, endereço ou informação sensível, não inclua. Conteúdo de
processo seletivo e de remuneração deve ser tratado de forma neutra e agregada, nunca
nominal. Em dúvida, pule.

## Autoria

O nome de cada autor é o nome salvo no celular do usuário, que pode diferir do handle
do GitHub. Faça o matching por nome quando possível e registre incertezas.
