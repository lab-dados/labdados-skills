"""Leitura do frontmatter das SKILL.md, para os scripts e os testes deste repositorio."""


def descricao(skill_md: str) -> str:
    """Texto da linha ``description:`` do frontmatter de uma SKILL.md, sem a chave e com as aspas.

    O frontmatter vai da primeira linha do arquivo, ``---``, ate a proxima ``---``. Levanta
    ``ValueError`` se nao houver frontmatter ou se ele nao tiver exatamente uma ``description:``.
    """
    linhas = skill_md.splitlines()
    if linhas[:1] != ["---"]:
        raise ValueError("a SKILL.md nao comeca com a linha --- do frontmatter")
    frontmatter = linhas[1 : linhas.index("---", 1)]  # sem o --- de fechamento, ValueError
    descricoes = [linha for linha in frontmatter if linha.startswith("description:")]
    if len(descricoes) != 1:
        raise ValueError(f"o frontmatter tem {len(descricoes)} linhas description:, e devia ter 1")
    return descricoes[0].removeprefix("description:").strip()
