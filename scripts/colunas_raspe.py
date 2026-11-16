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

Duas conferencias sem gerar nada, sobre o texto escrito a mao da skill:

- a tabela de ``text_column`` da ``fontes.md`` tem uma linha por fonte, e cada coluna
  que ela cita existe na tabela gerada da fonte (fonte sem schema nao e conferida);
- toda frase da ``SKILL.md`` e das references que diz "sem schema" nomeia, entre
  crases, exatamente as fontes sem schema de saida do documento.

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
SKILL = REFERENCES.parent / "SKILL.md"

# Fonte -> linhas da tabela de colunas; lista vazia para fonte ainda sem schema de saida.
Tabelas = dict[str, list[str]]

_FONTE = re.compile(r"`raspe\.(\w+)\(\)`")
_NOME = re.compile(r"`(\w+)`")
_BLOCO_GERADO = re.compile(r"<!-- colunas-raspe:(\w+):inicio.*?<!-- colunas-raspe:\1:fim -->", re.DOTALL)
_TITULO_TEXT_COLUMN = "## Nomes de coluna em dataframeit"


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


def conferir_text_column(tabelas: Tabelas, caminho: Path) -> list[str]:
    """Erros da tabela de ``text_column`` da ``fontes.md``: fonte faltando ou sobrando, coluna inexistente."""
    nome = caminho.relative_to(RAIZ)
    _, achou, secao = caminho.read_text(encoding="utf-8").partition(_TITULO_TEXT_COLUMN)
    tabela = list(takewhile(_e_linha, dropwhile(lambda linha: not _e_linha(linha), secao.split("\n## ")[0].splitlines())))
    if not achou or not tabela:
        return [f"{nome}: falta a tabela de text_column (secao {_TITULO_TEXT_COLUMN!r})"]
    erros, vistas = [], []
    for linha in tabela[2:]:
        _, fonte, recomendada, *_ = (celula.strip() for celula in linha.split("|"))
        fonte = fonte.strip("`")
        vistas.append(fonte)
        if fonte not in tabelas:
            erros.append(f"{nome}: text_column cita a fonte {fonte!r}, que nao esta no docs/colunas.md")
        elif tabelas[fonte]:
            existentes = colunas(tabelas[fonte])
            erros += [
                f"{nome}: text_column de {fonte!r} cita `{coluna}`, que nao e coluna da fonte"
                for coluna in _NOME.findall(recomendada)
                if f"`{coluna}`" not in existentes
            ]
    erros += [f"{nome}: falta a fonte {fonte!r} na tabela de text_column" for fonte in tabelas if fonte not in vistas]
    return erros


def conferir_sem_schema(tabelas: Tabelas, arquivos: list[Path]) -> list[str]:
    """Erros das frases que dizem "sem schema" e nao nomeiam exatamente as fontes sem schema de saida.

    Os blocos gerados ficam de fora. A frase termina em ponto ou ponto e virgula seguido
    de espaco, ou no fim da linha, para nao cortar ``references/fontes.md`` ao meio.
    """
    sem_schema = sorted(fonte for fonte, tabela in tabelas.items() if not tabela)
    erros = []
    for caminho in arquivos:
        texto = _BLOCO_GERADO.sub("", caminho.read_text(encoding="utf-8"))
        for frase in re.split(r"[.;]\s|\n", texto):
            if "sem schema" not in frase.lower():
                continue
            citadas = sorted({nome for nome in _NOME.findall(frase) if nome in tabelas})
            if citadas != sem_schema:
                erros.append(
                    f"{caminho.relative_to(RAIZ)}: a frase {frase.strip()[:80]!r}... diz \"sem schema\" e cita "
                    f"{citadas or 'nenhuma fonte'}, mas as fontes sem schema de saida sao {sem_schema or 'nenhuma'}"
                )
    return erros


def main(argumentos: list[str] | None = None) -> int:
    """Reescreve os blocos a partir do ``docs/colunas.md``, ou so confere com ``--check``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("colunas", type=Path, help="docs/colunas.md de um checkout do raspe")
    parser.add_argument("--check", action="store_true", help="nao grava; sai com 1 se algo divergir")
    opcoes = parser.parse_args(argumentos)
    tabelas = ler_tabelas(opcoes.colunas.read_text(encoding="utf-8"))
    gerados = blocos(tabelas)

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
        erros.append("Rode `python scripts/colunas_raspe.py <raspe>/docs/colunas.md`.")
    # Texto escrito a mao: o script so aponta, e a correcao e manual.
    erros += conferir_text_column(tabelas, REFERENCES / "fontes.md")
    erros += conferir_sem_schema(tabelas, [SKILL, *sorted(REFERENCES.glob("*.md"))])

    if erros:
        sys.stderr.write("\n".join(erros) + "\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
