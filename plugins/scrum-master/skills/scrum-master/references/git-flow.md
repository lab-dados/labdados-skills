# Fluxo git para o relatório semanal

O `.md` do relatório **entra no repositório** (é artefato útil e rastreável). O `.html` e o `.pdf` **não** (são derivados e pesariam o histórico).

## Passos concretos

### 1. Confirmar que é um repositório git

```bash
git -C <dir> rev-parse --is-inside-work-tree
```

Se não for, avise o usuário ou registre "Sem repositório git; relatório salvo como arquivo avulso em `./weekly-plan/`" e pule os passos git.

### 2. Garantir a pasta `weekly-plan/`

```bash
mkdir -p <repo>/weekly-plan
```

### 3. Manter o `.gitignore`

Garanta que essas linhas existam no `.gitignore` da raiz do repo:

```
weekly-plan/*.html
weekly-plan/*.pdf
weekly-plan/.team-inferred.json
```

Se o arquivo não existir, crie. Se já existir mas não tiver essas linhas, **append** sem duplicar. Nunca reescreva um `.gitignore` do zero — pode remover coisas importantes.

Script mental em pseudocódigo:
```python
needed = {"weekly-plan/*.html", "weekly-plan/*.pdf", "weekly-plan/.team-inferred.json"}
existing = set(Path(".gitignore").read_text().splitlines()) if exists else set()
to_add = needed - existing
if to_add:
    with open(".gitignore", "a") as f:
        if existing and not ends_with_newline:
            f.write("\n")
        f.write("\n# Skill scrum-master\n")
        for line in to_add:
            f.write(line + "\n")
```

### 4. Salvar os arquivos

- `weekly-plan/YYYY-MM-DD-weekly.md` — versão completa do relatório (para Julio, com cards propostos).
- `weekly-plan/YYYY-MM-DD-weekly.html` — versão executiva visual (gerada a partir do template).
- `weekly-plan/YYYY-MM-DD-weekly.pdf` — renderizada por `scripts/render_pdf.py` a partir do `.html`, entregue ao coordenador Daniel Wang.
- `weekly-plan/.team-inferred.json` — mapeamento inferido de pessoas (não commitado).

Use a **data da segunda-feira da semana coberta** no nome do arquivo (não a data da execução), para ficar previsível.

### 5. Fazer `git add` mas **não commitar**

```bash
git -C <repo> add weekly-plan/*.md .gitignore
```

Mostre o resultado ao usuário:
```bash
git -C <repo> status weekly-plan/ .gitignore
```

E sugira o comando de commit:
```
git commit -m "weekly plan 2026-04-20"
git push
```

**Por que não commitar sozinho:** o Julio quer controlar o histórico do repo. Commits automáticos silenciosos criam confusão quando ele depois precisa fazer rebase ou revisar mudanças. Se o scheduled task rodar sozinho, os arquivos ficam prontos com `git add` feito, aguardando ele abrir e commitar.

### 6. Em modo scheduled task

Mesmo em modo automático, **não commite**. Deixe os arquivos prontos no working tree com `git add` aplicado. O Julio verá a mudança quando abrir o repo (via `git status` ou na UI do editor).

### 7. Casos de borda

- **Repo com working tree sujo** (mudanças não relacionadas): o `git add` só adiciona os arquivos do weekly-plan + `.gitignore`, então não pisa no resto. Só avise no relatório que havia mudanças pendentes — isso pode ser sinal que o usuário esqueceu algo.
- **Arquivo `.md` já existe** (execução repetida na mesma semana): sobrescreva sem perguntar se estiver em scheduled. Em modo interativo, pergunte se o usuário quer sobrescrever ou adicionar sufixo `-v2`.
- **Conflito em `.gitignore`**: se detectar que o `.gitignore` tem conflito não resolvido (`<<<<<<<`), não toque nele. Registre como ponto a confirmar.
