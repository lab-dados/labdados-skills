"""Testa a leitura da description no frontmatter das SKILL.md, sem rede."""

import frontmatter
import pytest


def test_descricao_le_so_o_frontmatter():
    skill_md = '---\nname: x\ndescription: "Usar quando: a --- b"\n---\n\ndescription: do corpo\n'
    assert frontmatter.descricao(skill_md) == '"Usar quando: a --- b"'


@pytest.mark.parametrize(
    "skill_md",
    [
        "---\nname: x\n---\n\ndescription: do corpo\n",
        "---\ndescription: a\ndescription: b\n---\n",
        "# Titulo\ndescription: do corpo\n---\n",
        "---\ndescription: sem fechamento\n",
    ],
)
def test_descricao_falha_sem_frontmatter_com_uma_description(skill_md):
    with pytest.raises(ValueError):
        frontmatter.descricao(skill_md)
