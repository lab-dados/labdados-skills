"""Copia para a skill raspe as tabelas de colunas do ``docs/colunas.md`` do raspe.

Uso, na raiz deste repositorio, com um checkout do raspe em ``../raspe``::

    python scripts/colunas_raspe.py ../raspe/docs/colunas.md           # reescreve os blocos
    python scripts/colunas_raspe.py ../raspe/docs/colunas.md --check   # so confere; sai com 1 se divergir

O raspe gera o ``docs/colunas.md`` com ``python -m raspe.schemas.documentacao``, a
partir dos schemas de saida. Cada secao com tabela, cujo titulo cita
``raspe.<fonte>()``, vai sem edicao para o bloco entre marcadores de
``references/<fonte>.md``; a secao que duas fontes dividem (ANS e ANVISA) vai para
as duas. A ``references/fontes.md`` recebe a matriz de colunas, uma linha por fonte
na ordem do documento. As fontes da secao sem tabela (raspadores ainda sem schema)
entram na matriz apontando para a reference delas, cuja tabela segue escrita a mao.

O workflow ``.github/workflows/colunas-raspe.yml`` roda o ``--check`` contra a
``main`` do raspe em todo PR que toca a skill e uma vez por semana.
"""

from __future__ import annotations

import argparse
import re
import sys
from itertools import dropwhile, takewhile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REFERENCES = RAIZ / "plugins" / "raspe" / "skills" / "raspe" / "references"

# Fonte -> linhas da tabela de colunas; lista vazia para fonte ainda sem schema de saida.
Tabelas = dict[str, list[str]]

_FONTE = re.compile(r"`raspe\.(\w+)\(\)`")


def _e_linha(linha: str) -> bool:
    return linha.startswith("|")


def ler_tabelas(documento: str) -> Tabelas:
    """Tabela de cada fonte do ``docs/colunas.md``, na ordem do documento.

    A secao com tabela cita as fontes no titulo e so a primeira tabela conta. A
    secao "Raspadores ainda sem schema de saida" cita no corpo as fontes sem
    tabela; outra secao sem tabela nao conta.
    """
    tabelas: Tabelas = {}
    for secao in re.split(r"^## ", documento, flags=re.MULTILINE)[1:]:
        titulo, _, corpo = secao.partition("\n")
        tabela = list(takewhile(_e_linha, dropwhile(lambda linha: not _e_linha(linha), corpo.splitlines())))
        if tabela:
            tabelas.update(dict.fromkeys(_FONTE.findall(titulo), tabela))
        elif "sem schema" in titulo:
            for fonte in _FONTE.findall(corpo):
                tabelas.setdefault(fonte, [])
    if not any(tabelas.values()):
        raise SystemExit("docs/colunas.md sem secao com tabela de colunas: o formato do documento mudou?")
    return tabelas


def colunas(tabela: list[str]) -> list[str]:
    """Nomes das colunas, na ordem da tabela (a primeira celula de cada linha, sem o cabecalho)."""
    return [linha.split("|")[1].strip() for linha in tabela[2:]]


def matriz(tabelas: Tabelas) -> list[str]:
    """Uma linha por fonte, com as colunas na ordem do DataFrame."""
    linhas = ["| Fonte | Colunas, na ordem do DataFrame |", "|---|---|"]
    for fonte, tabela in tabelas.items():
        celula = ", ".join(colunas(tabela)) if tabela else f"sem schema de saída; veja `references/{fonte}.md`"
        linhas.append(f"| `{fonte}` | {celula} |")
    return linhas


def marcadores(nome: str) -> tuple[str, str]:
    """Marcadores de inicio e fim do bloco ``nome``."""
    return (
        f"<!-- colunas-raspe:{nome}:inicio (gerado por scripts/colunas_raspe.py do docs/colunas.md do raspe;"
        " nao editar a mao) -->",
        f"<!-- colunas-raspe:{nome}:fim -->",
    )


def substituir(texto: str, nome: str, conteudo: list[str], caminho: Path) -> str:
    """Troca o trecho entre os marcadores de ``nome`` (inclusive) pelo bloco novo.

    Mesmo formato de bloco do ``cobertura_juscraper.substituir``: mudou um, mude o outro.
    """
    inicio, fim = marcadores(nome)
    if texto.count(inicio) != 1 or texto.count(fim) != 1:
        raise SystemExit(f"{caminho}: os marcadores do bloco {nome!r} devem aparecer uma vez cada.")
    antes, resto = texto.split(inicio)
    _, depois = resto.split(fim)
    return antes + "\n".join([inicio, "", *conteudo, "", fim]) + depois


def blocos(tabelas: Tabelas) -> dict[Path, tuple[str, list[str]]]:
    """Arquivo -> (nome do bloco, conteudo): a matriz em ``fontes.md`` e a tabela de cada fonte com schema."""
    saida = {REFERENCES / "fontes.md": ("matriz", matriz(tabelas))}
    for fonte, tabela in tabelas.items():
        if tabela:
            saida[REFERENCES / f"{fonte}.md"] = ("tabela", tabela)
    return saida


def main(argumentos: list[str] | None = None) -> int:
    """Reescreve os blocos a partir do ``docs/colunas.md``, ou so confere com ``--check``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("colunas", type=Path, help="docs/colunas.md de um checkout do raspe")
    parser.add_argument("--check", action="store_true", help="nao grava; sai com 1 se algo divergir")
    opcoes = parser.parse_args(argumentos)
    gerados = blocos(ler_tabelas(opcoes.colunas.read_text(encoding="utf-8")))

    erros = []
    # Tudo e conferido antes de gravar: marcador quebrado num arquivo nao deixa os outros meio atualizados.
    atualizados: dict[Path, str] = {}
    for caminho, (nome, conteudo) in gerados.items():
        if not caminho.exists():
            erros.append(f"{caminho.relative_to(RAIZ)}: falta a reference da fonte (veja a raspe-skill-sync.md da raspe-builder)")
            continue
        texto = caminho.read_text(encoding="utf-8")
        atualizado = substituir(texto, nome, conteudo, caminho)
        if atualizado != texto:
            atualizados[caminho] = atualizado
    if opcoes.check:
        erros += [f"{caminho.relative_to(RAIZ)}: bloco gerado desatualizado" for caminho in atualizados]
    else:
        for caminho, atualizado in atualizados.items():
            caminho.write_text(atualizado, encoding="utf-8")
    # Bloco de fonte que saiu do documento (ou perdeu o schema) ficaria congelado sem aviso.
    inicio_tabela = marcadores("tabela")[0]
    for caminho in sorted(REFERENCES.glob("*.md")):
        if caminho not in gerados and inicio_tabela in caminho.read_text(encoding="utf-8"):
            erros.append(f"{caminho.relative_to(RAIZ)}: tem bloco de colunas, mas a fonte nao tem tabela no docs/colunas.md")

    if erros:
        sys.stderr.write("\n".join(erros) + "\nRode `python scripts/colunas_raspe.py <raspe>/docs/colunas.md`.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
