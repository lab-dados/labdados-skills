"""As skills que mandam instalar pacote Python com pip sugerem tambem o uv (#8)."""

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SKILLS = sorted(RAIZ.glob("plugins/*/skills/*/SKILL.md"))
PIP = re.compile(r"(?<!uv )pip install")
UV = re.compile(r"\buv (add|pip install|tool install)\b")
COM_PIP = [s for s in SKILLS if PIP.search(s.read_text(encoding="utf-8"))]


def test_ha_skills_com_pip():
    assert COM_PIP, "nenhuma SKILL.md manda usar o pip: o teste abaixo nao confere nada"


@pytest.mark.parametrize("skill", COM_PIP, ids=lambda s: s.parent.name)
def test_skill_com_pip_sugere_uv(skill):
    assert UV.search(skill.read_text(encoding="utf-8")), (
        f"{skill.relative_to(RAIZ)} manda instalar com pip e nao sugere o uv "
        "(`uv add` num projeto, `uv pip install` fora dele, `uv tool install` para CLI)"
    )
