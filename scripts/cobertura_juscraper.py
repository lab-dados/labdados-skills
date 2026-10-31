"""Sincroniza com o codigo do juscraper a cobertura descrita na skill juscraper.

Uso, na raiz deste repositorio, com um checkout do juscraper em ``../juscraper``::

    uv run --directory ../juscraper python scripts/tabela_cobertura.py --json > /tmp/cobertura.json
    python scripts/cobertura_juscraper.py /tmp/cobertura.json           # reescreve os blocos
    python scripts/cobertura_juscraper.py /tmp/cobertura.json --check   # so confere; sai com 1 se divergir

O JSON vem do ``scripts/tabela_cobertura.py`` do juscraper, que inspeciona os
raspadores registrados em ``jus.scraper()``, resolve a heranca e descarta os
metodos que so levantam ``NotImplementedError``. Este script nao repete essa
inspecao: so escreve o resultado nos blocos entre marcadores de ``BLOCOS`` e
confere se a ``description`` da skill, que decide quando ela e acionada, cita
todo raspador. O texto fora dos blocos (plataforma, tags de versao, parametros)
continua escrito a mao.

O workflow ``.github/workflows/juscraper-cobertura.yml`` roda o ``--check``
contra a ``main`` do juscraper em todo PR que toca a skill e uma vez por semana.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SKILL = RAIZ / "plugins" / "juscraper" / "skills" / "juscraper"

# Os quatro endpoints de tribunal tem coluna propria na matriz; o resto vai para "Outros metodos".
ENDPOINTS_TRIBUNAL = ("cjsg", "cjpg", "cpopg", "cposg")

Raspador = dict[str, object]
Cobertura = dict[str, list[Raspador]]


def _metodos(raspador: Raspador) -> list[str]:
    metodos = raspador["metodos"]
    assert isinstance(metodos, list)
    return [str(metodo) for metodo in metodos]


def matriz_tribunais(cobertura: Cobertura) -> list[str]:
    """Uma linha por tribunal, com ``sim``/``-`` nos quatro endpoints e os demais metodos por extenso."""
    cabecalho = ["Tribunal", *ENDPOINTS_TRIBUNAL, "Outros metodos"]
    linhas = [
        "| " + " | ".join(cabecalho) + " |",
        "|---|" + ":---:|" * len(ENDPOINTS_TRIBUNAL) + "---|",
    ]
    for tribunal in cobertura["tribunais"]:
        metodos = _metodos(tribunal)
        celulas = ["sim" if endpoint in metodos else "-" for endpoint in ENDPOINTS_TRIBUNAL]
        outros = ", ".join(f"`{metodo}`" for metodo in metodos if metodo not in ENDPOINTS_TRIBUNAL) or "-"
        linhas.append(f"| **{tribunal['nome']}** | " + " | ".join(celulas) + f" | {outros} |")
    return linhas


def metodos_agregadores(cobertura: Cobertura) -> list[str]:
    """Uma linha por agregador, com os metodos publicos."""
    linhas = ["| Agregador | Metodos |", "|---|---|"]
    for agregador in cobertura["agregadores"]:
        linhas.append(f"| **{agregador['nome']}** | " + ", ".join(f"`{m}`" for m in _metodos(agregador)) + " |")
    return linhas


def quem_tem_cada_metodo(cobertura: Cobertura) -> list[str]:
    """Para cada metodo, os raspadores que o implementam: a lista que o roteamento da SKILL.md consulta."""
    donos: dict[str, list[str]] = {}
    for raspador in [*cobertura["tribunais"], *cobertura["agregadores"]]:
        for metodo in _metodos(raspador):
            donos.setdefault(metodo, []).append(str(raspador["nome"]))
    ordem = [*ENDPOINTS_TRIBUNAL, *sorted(set(donos) - set(ENDPOINTS_TRIBUNAL))]
    return [f"- `{metodo}`: " + ", ".join(donos[metodo]) for metodo in ordem if metodo in donos]


BLOCOS: dict[tuple[Path, str], Callable[[Cobertura], list[str]]] = {
    (SKILL / "references" / "tribunais.md", "tribunais"): matriz_tribunais,
    (SKILL / "references" / "agregadores.md", "agregadores"): metodos_agregadores,
    (SKILL / "SKILL.md", "metodos"): quem_tem_cada_metodo,
}


def marcadores(nome: str) -> tuple[str, str]:
    """Marcadores de inicio e fim do bloco ``nome``."""
    return (
        f"<!-- cobertura-juscraper:{nome}:inicio (gerado por scripts/cobertura_juscraper.py; nao editar a mao) -->",
        f"<!-- cobertura-juscraper:{nome}:fim -->",
    )


def substituir(texto: str, nome: str, conteudo: list[str], caminho: Path) -> str:
    """Troca o trecho entre os marcadores de ``nome`` (inclusive) pelo bloco novo."""
    inicio, fim = marcadores(nome)
    if texto.count(inicio) != 1 or texto.count(fim) != 1:
        raise SystemExit(f"{caminho}: os marcadores do bloco {nome!r} devem aparecer uma vez cada.")
    antes, resto = texto.split(inicio)
    _, depois = resto.split(fim)
    return antes + "\n".join([inicio, "", *conteudo, "", fim]) + depois


def _normalizar(texto: str) -> str:
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def ausentes_na_descricao(cobertura: Cobertura, skill_md: str) -> list[str]:
    """Raspadores que a ``description`` do frontmatter nao cita.

    A comparacao ignora caixa e pontuacao, para ``ComunicaCNJ`` casar com
    ``comunica_cnj``, mas exige o nome inteiro: ``TJMG`` nao casa com ``TJMGS``.
    """
    frontmatter = skill_md.split("---", 2)[1]
    descricao = next(linha for linha in frontmatter.splitlines() if linha.startswith("description:"))
    palavras = {_normalizar(palavra) for palavra in re.findall(r"[\w-]+", descricao)}
    return [
        str(raspador["nome"])
        for raspador in [*cobertura["tribunais"], *cobertura["agregadores"]]
        if _normalizar(str(raspador["nome"])) not in palavras
    ]


def main(argumentos: list[str] | None = None) -> int:
    """Reescreve os blocos a partir do JSON, ou so confere com ``--check``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("json", type=Path, help="saida de `scripts/tabela_cobertura.py --json` do juscraper")
    parser.add_argument("--check", action="store_true", help="nao grava; sai com 1 se algo divergir")
    opcoes = parser.parse_args(argumentos)
    cobertura: Cobertura = json.loads(opcoes.json.read_text(encoding="utf-8"))

    textos: dict[Path, str] = {}
    for (caminho, nome), gerar in BLOCOS.items():
        texto = textos.get(caminho) or caminho.read_text(encoding="utf-8")
        textos[caminho] = substituir(texto, nome, gerar(cobertura), caminho)

    erros = []
    for caminho, atualizado in textos.items():
        if atualizado == caminho.read_text(encoding="utf-8"):
            continue
        if opcoes.check:
            erros.append(f"{caminho.relative_to(RAIZ)}: bloco gerado desatualizado")
        else:
            caminho.write_text(atualizado, encoding="utf-8")
    faltam = ausentes_na_descricao(cobertura, textos[SKILL / "SKILL.md"])
    if faltam:
        erros.append("description da SKILL.md nao cita: " + ", ".join(faltam))

    if erros:
        sys.stderr.write("\n".join(erros) + "\nRode `python scripts/cobertura_juscraper.py <json>` e revise a description.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
