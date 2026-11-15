"""Confere o marketplace: todo `source` local existe e tem SKILL.md.

O `claude plugin validate` não confere nenhum dos dois. Este script roda no validate.yml e no
hook do pre-commit, que assim pega antes do push o que o CI reprovaria.
"""

import glob
import json
import os
import sys

with open(".claude-plugin/marketplace.json", encoding="utf-8") as f:
    marketplace = json.load(f)

erros = []
for plugin in marketplace["plugins"]:
    fonte = plugin.get("source")
    if not isinstance(fonte, str) or not fonte.startswith("./"):
        continue
    if not os.path.isdir(fonte):
        erros.append(f"plugin {plugin['name']}: source {fonte} não existe")
    elif not glob.glob(os.path.join(fonte, "skills", "*", "SKILL.md")):
        erros.append(f"plugin {plugin['name']}: nenhum SKILL.md em {fonte}/skills/")

for erro in erros:
    print("ERRO:", erro)
if erros:
    sys.exit(1)
print(f"{len(marketplace['plugins'])} plugins no marketplace, todo source local tem SKILL.md.")
