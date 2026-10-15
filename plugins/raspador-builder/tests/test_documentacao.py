"""Testes do que a documentação da skill manda o agente escrever ou rodar."""

import ast
import re

from conftest import PASTA_SKILL

# Página de tribunal com outros "de <número>" antes do total, que um padrão solto pegaria.
PAGINA_DE_TRIBUNAL = (
    "Tribunal de Justiça. Câmara de 2 instância. Consulta feita em 15 de outubro de 2026. "
    "Resultados 1 a 10 de 1.132"
)


def blocos_python(caminho):
    return re.findall(r"```python\n(.*?)```", caminho.read_text(encoding="utf-8"), flags=re.DOTALL)


def test_ler_total_da_variante_html_pega_o_total_e_nao_outro_numero():
    """O exemplo de `ler_total` em references/raspador.md tem de ancorar no texto do total.

    O bloco usa BeautifulSoup, que não está entre as dependências dos testes; por isso o teste lê o
    padrão passado a `re.search` pela árvore sintática do bloco e o aplica ao texto da página.
    """
    funcoes = [
        no
        for bloco in blocos_python(PASTA_SKILL / "references" / "raspador.md")
        for no in ast.walk(ast.parse(bloco))
        if isinstance(no, ast.FunctionDef) and no.name == "ler_total"
    ]
    assert len(funcoes) == 1
    padroes = [
        no.args[0].value
        for no in ast.walk(funcoes[0])
        if isinstance(no, ast.Call) and getattr(no.func, "attr", None) == "search"
    ]
    assert len(padroes) == 1
    achado = re.search(padroes[0], PAGINA_DE_TRIBUNAL)
    assert achado is not None
    assert int(achado.group(1).replace(".", "")) == 1132


def test_ler_total_da_variante_html_esta_marcado_para_adaptar():
    texto = (PASTA_SKILL / "references" / "raspador.md").read_text(encoding="utf-8")
    definicao = re.search(r"def ler_total\(.*?(?=\n\n\n)", texto, flags=re.DOTALL).group(0)
    assert "ADAPTAR" in definicao


def test_comando_python_vem_com_a_alternativa_python3():
    """Linux e macOS costumam ter só `python3`; comando com `python` puro precisa da alternativa.

    Vale para documentação e docstrings: um comando `python <argumento>` só passa se `python3`
    aparece no mesmo trecho (três linhas antes ou depois).
    """
    comando_python = re.compile(r"(?<![\w/.-])python (?=[-\w<.])")
    faltando = []
    for caminho in sorted(PASTA_SKILL.rglob("*")):
        if caminho.suffix not in (".md", ".py"):
            continue
        linhas = caminho.read_text(encoding="utf-8").splitlines()
        for numero, linha in enumerate(linhas):
            if comando_python.search(linha):
                vizinhanca = "\n".join(linhas[max(0, numero - 3) : numero + 4])
                if "python3" not in vizinhanca:
                    faltando.append(f"{caminho.relative_to(PASTA_SKILL)}:{numero + 1}: {linha.strip()}")
    assert not faltando, "\n".join(faltando)
