"""Os scripts de ``scripts/`` nao sao pacote: rodam como arquivo solto (``python scripts/x.py``),
e o Python poe a pasta deles no ``sys.path``. Os testes fazem o mesmo, para importa-los pelo nome.

O ``tests/__init__.py`` faz este arquivo ser importado como ``tests.conftest``. Sem ele, os dois
``conftest`` da suite (este e o de ``plugins/raspador-builder/tests``) disputariam o nome
``conftest``, e o ``from conftest import ...`` dos testes da raspador-builder acharia o errado.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
