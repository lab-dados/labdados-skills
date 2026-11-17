"""A description de cada skill tem de afastar as irmãs que disputam o mesmo pedido (CLAUDE.md).

Cada par abaixo é uma sobreposição conhecida: sem o nome da irmã na description, o modelo escolhe
entre as duas sem critério.
"""

import functools
import re
from pathlib import Path

import pytest
from frontmatter import descricao

RAIZ = Path(__file__).resolve().parents[1]

IRMAS = {
    "juscraper": ["juscraper-builder"],
    "juscraper-builder": ["juscraper-builder-captcha", "juscraper", "raspe-builder"],
    "juscraper-builder-captcha": ["juscraper-builder"],
    "raspe-builder": ["raspe", "juscraper-builder"],
    "raspador-builder": ["juscraper", "raspe", "juscraper-builder", "raspe-builder"],
    # raspe.capes() busca artigos no Portal de Periódicos da CAPES; a openalex só entra quando o usuário cita o OpenAlex.
    "openalex": ["raspe"],
    "raspe": ["openalex"],
}


@functools.cache
def _description(skill: str) -> str:
    (skill_md,) = RAIZ.glob(f"plugins/*/skills/{skill}/SKILL.md")
    return descricao(skill_md.read_text(encoding="utf-8"))


@pytest.mark.parametrize(("skill", "irma"), [(s, i) for s, irmas in IRMAS.items() for i in irmas])
def test_description_nomeia_a_irma(skill, irma):
    # Só conta o nome depois do aviso: "raspe" também é verbo ("colete, raspe ou baixe").
    aviso = re.search(r"(?:Não confundir com|Do not confuse with) (.*)", _description(skill))
    assert aviso, f"a description de {skill} não avisa de nenhuma irmã"
    assert re.search(rf"(?<![\w-]){re.escape(irma)}(?![\w-])", aviso.group(1)), (
        f"a description de {skill} não diz quando usar {irma} no lugar dela"
    )
