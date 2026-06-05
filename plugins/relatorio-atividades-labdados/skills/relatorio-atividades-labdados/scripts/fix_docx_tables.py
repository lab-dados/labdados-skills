# cópia de plugins/relatorio/skills/relatorio/scripts/fix_docx_tables.py — manter em sync
"""Pós-processa .docx para ajustar tabelas geradas pelo Pandoc.

Mudanças aplicadas:
1. Adiciona/atualiza estilo `Compact` (usado pelo Pandoc nos parágrafos dentro de
   células) com spacing.after = 0, eliminando espaçamento vertical entre linhas.
2. Altera w:lastRow="0" para w:lastRow="1" em todas as tabelas, ativando o
   estilo de borda da última linha definido no reference doc.
3. Ajusta o estilo `Table` para que a borda inferior da última linha tenha a
   mesma espessura da borda inferior do header (sz=8).

Uso:
    python scripts/fix_docx_tables.py <arquivo.docx>
"""

from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

COMPACT_STYLE = (
    '<w:style w:type="paragraph" w:customStyle="1" w:styleId="Compact">'
    '<w:name w:val="Compact"/>'
    '<w:basedOn w:val="Normal"/>'
    '<w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
    "</w:style>"
)


def _patch_table_style(xml: str) -> str:
    """Iguala a borda inferior do lastRow à borda inferior do firstRow (sz=8).

    A ordem dos atributos XML pode variar entre versões do Pandoc; só nos
    interessa o valor de ``w:sz`` dentro do ``<w:bottom .../>`` do
    ``<w:tblStylePr w:type="lastRow">``.
    """

    def _fix_bottom(block: str) -> str:
        return re.sub(
            r'(<w:bottom[^/]*w:sz=)"\d+"',
            r'\1"8"',
            block,
        )

    pattern = re.compile(
        r'<w:tblStylePr w:type="lastRow">.*?</w:tblStylePr>',
        re.DOTALL,
    )
    return pattern.sub(lambda m: _fix_bottom(m.group(0)), xml)


def _patch_styles(xml: str) -> str:
    xml = _patch_table_style(xml)
    if 'w:styleId="Compact"' in xml:
        # Atualiza spacing do Compact existente
        pattern = re.compile(
            r'(<w:style [^>]*w:styleId="Compact"[^>]*>)(.*?)(</w:style>)',
            re.DOTALL,
        )

        def _replace(m: re.Match[str]) -> str:
            inner = m.group(2)
            inner = re.sub(r"<w:spacing[^/]*/>", "", inner)
            if "<w:pPr>" in inner:
                inner = inner.replace(
                    "<w:pPr>",
                    '<w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>',
                    1,
                )
            else:
                inner = (
                    '<w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
                    + inner
                )
            return m.group(1) + inner + m.group(3)

        return pattern.sub(_replace, xml)
    # Insere novo estilo antes do </w:styles>
    return xml.replace("</w:styles>", COMPACT_STYLE + "</w:styles>")


def _patch_document(xml: str) -> str:
    """Ativa a borda da última linha só nas tabelas de dados reais.

    O Quarto embrulha cada figura e cada tabela legendada numa tabela externa de
    uma célula, que herda o estilo ``Table``. Essas tabelas-invólucro têm
    ``w:firstRow="0"`` (não têm cabeçalho), enquanto as tabelas de dados reais têm
    ``w:firstRow="1"``. Se deixarmos ``w:lastRow="1"`` no invólucro, ele desenha
    uma borda inferior, o que aparece como uma linha indesejada embaixo das figuras
    e como uma segunda linha (duplicada) embaixo das tabelas.

    Solução: alinhar ``w:lastRow`` ao ``w:firstRow``. Invólucro (firstRow=0) fica
    sem borda inferior; tabela real (firstRow=1) mantém a borda da última linha.
    """

    def _fix_look(m: re.Match[str]) -> str:
        look = m.group(0)
        first = re.search(r'w:firstRow="(\d)"', look)
        target = "1" if (first and first.group(1) == "1") else "0"
        return re.sub(r'w:lastRow="\d"', f'w:lastRow="{target}"', look)

    return re.sub(r"<w:tblLook[^>]*>", _fix_look, xml)


def main(docx_path: str) -> None:
    path = Path(docx_path)
    if not path.exists():
        raise FileNotFoundError(path)

    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(path, "r") as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.namelist():
            data = src.read(item)
            if item == "word/styles.xml":
                data = _patch_styles(data.decode("utf-8")).encode("utf-8")
            elif item == "word/document.xml":
                data = _patch_document(data.decode("utf-8")).encode("utf-8")
            dst.writestr(item, data)

    shutil.move(str(tmp), str(path))
    print(f"OK: {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python scripts/fix_docx_tables.py <arquivo.docx>", file=sys.stderr)
        sys.exit(2)
    for arg in sys.argv[1:]:
        main(arg)
