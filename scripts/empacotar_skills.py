"""Gera um <skill>.zip por skill, no formato que o upload de skills do claude.ai aceita.

Uso, na raiz deste repositorio::

    python scripts/empacotar_skills.py dist

Cada zip tem no primeiro nivel a pasta da skill, com o ``SKILL.md`` dentro
(``juscraper/SKILL.md``, ``juscraper/references/...``). O workflow
``.github/workflows/release-skills.yml`` roda este script e anexa os zips a release.
"""

from __future__ import annotations

import sys
import zipfile
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Sobras locais que nao sao da skill (o checkout do CI nao as tem, mas uma maquina pode ter).
IGNORAR = {"__pycache__", ".DS_Store"}

# Skills que nao funcionam sozinhas num upload, com o motivo. Nao ganham zip.
SEM_ZIP = {
    "juscraper-builder-captcha": "le ../juscraper-builder/, que nao vai no zip",
}


def skills(raiz: Path) -> list[Path]:
    """Pastas ``plugins/*/skills/<skill>/`` com ``SKILL.md``, inclusive as de ``SEM_ZIP``."""
    return sorted(p.parent for p in raiz.glob("plugins/*/skills/*/SKILL.md"))


def empacotar(raiz: Path, saida: Path) -> list[Path]:
    """Zipa cada skill fora de ``SEM_ZIP`` em ``saida/<skill>.zip``."""
    pastas = [p for p in skills(raiz) if p.name not in SEM_ZIP]
    repetidos = sorted(n for n, vezes in Counter(p.name for p in pastas).items() if vezes > 1)
    if repetidos:
        raise SystemExit(f"skills com o mesmo nome em plugins diferentes, os zips colidiriam: {repetidos}")

    saida.mkdir(parents=True, exist_ok=True)
    zips = []
    for pasta in pastas:
        destino = saida / f"{pasta.name}.zip"
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
            for arquivo in sorted(pasta.rglob("*")):
                relativo = arquivo.relative_to(pasta.parent)
                if arquivo.is_file() and not IGNORAR.intersection(relativo.parts):
                    zf.write(arquivo, relativo.as_posix())
        zips.append(destino)
    return zips


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("uso: python scripts/empacotar_skills.py <pasta de saida>")
    for caminho in empacotar(RAIZ, Path(sys.argv[1])):
        print(caminho)
