"""Testa o sincronizador das colunas da skill raspe sem rede e sem o raspe.

O documento daqui imita o `docs/colunas.md` do raspe. A conferencia contra o raspe de verdade
e o passo `--check` do workflow `colunas-raspe`.
"""

import colunas_raspe
import pytest

DOCUMENTO = """# Colunas devolvidas por `raspar()`

Texto de abertura que cita `raspe.folha()` sem tabela nenhuma.

## `raspe.ans()` e `raspe.anvisa()`

Schema: `OutputDatalegis`.

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `url` | texto | Endereço do ato. | https://exemplo |
| `termo_busca` | texto | Termo de busca. | natjus |

## `raspe.cfm()`

Schema: `OutputCFM`.

| Coluna | Tipo | Descrição | Exemplo |
| --- | --- | --- | --- |
| `tipo` | texto | Tipo da norma. | Resolução |
| `termo_busca` | texto | Termo de busca. | natjus |

## Raspadores ainda sem schema de saída

`raspe.camara()`, `raspe.senado()`. As colunas deles estão no README.
"""


def test_ler_tabelas():
    tabelas = colunas_raspe.ler_tabelas(DOCUMENTO)
    assert list(tabelas) == ["ans", "anvisa", "cfm", "camara", "senado"]
    assert tabelas["ans"] == tabelas["anvisa"]
    assert tabelas["cfm"][2] == "| `tipo` | texto | Tipo da norma. | Resolução |"
    assert tabelas["camara"] == tabelas["senado"] == []


def test_so_a_secao_sem_schema_lista_fontes_sem_tabela():
    documento = DOCUMENTO + "\n## Observações\n\n`raspe.cfm()` e `raspe.folha()` aceitam filtros.\n"
    assert colunas_raspe.ler_tabelas(documento) == colunas_raspe.ler_tabelas(DOCUMENTO)


def test_so_a_primeira_tabela_da_secao_conta():
    documento = DOCUMENTO.replace("## Raspadores", "Valores de `tipo`:\n\n| Valor |\n| --- |\n| Parecer |\n\n## Raspadores")
    assert colunas_raspe.colunas(colunas_raspe.ler_tabelas(documento)["cfm"]) == ["`tipo`", "`termo_busca`"]


def test_documento_sem_tabela_falha():
    with pytest.raises(SystemExit, match="formato"):
        colunas_raspe.ler_tabelas("# Colunas\n\n## `raspe.cfm()`\n\nSem tabela.\n")


def test_matriz():
    assert colunas_raspe.matriz(colunas_raspe.ler_tabelas(DOCUMENTO)) == [
        "| Fonte | Colunas, na ordem do DataFrame |",
        "|---|---|",
        "| `ans` | `url`, `termo_busca` |",
        "| `anvisa` | `url`, `termo_busca` |",
        "| `cfm` | `tipo`, `termo_busca` |",
        "| `camara` | sem schema de saída; veja `references/camara.md` |",
        "| `senado` | sem schema de saída; veja `references/senado.md` |",
    ]


def _preparar(tmp_path, monkeypatch, fontes=("fontes", "ans", "anvisa", "cfm")):
    """Skill falsa com blocos vazios em ``fontes`` e o documento em ``colunas.md``."""
    monkeypatch.setattr(colunas_raspe, "RAIZ", tmp_path)
    monkeypatch.setattr(colunas_raspe, "REFERENCES", tmp_path)
    for fonte in fontes:
        inicio, fim = colunas_raspe.marcadores("matriz" if fonte == "fontes" else "tabela")
        (tmp_path / f"{fonte}.md").write_text(f"# {fonte}\n\n{inicio}\n{fim}\n\nfim\n", encoding="utf-8")
    documento = tmp_path / "colunas.md"
    documento.write_text(DOCUMENTO, encoding="utf-8")
    return str(documento)


def test_grava_e_depois_confere(tmp_path, monkeypatch):
    documento = _preparar(tmp_path, monkeypatch)
    antes = (tmp_path / "cfm.md").read_text(encoding="utf-8")
    assert colunas_raspe.main([documento, "--check"]) == 1
    assert (tmp_path / "cfm.md").read_text(encoding="utf-8") == antes  # --check nao grava

    assert colunas_raspe.main([documento]) == 0
    cfm = (tmp_path / "cfm.md").read_text(encoding="utf-8")
    assert "| `tipo` | texto | Tipo da norma. | Resolução |" in cfm
    assert cfm.startswith("# cfm\n\n<!-- colunas-raspe:tabela:inicio") and cfm.endswith("fim -->\n\nfim\n")
    assert "| `camara` | sem schema" in (tmp_path / "fontes.md").read_text(encoding="utf-8")
    assert colunas_raspe.main([documento, "--check"]) == 0


def test_fonte_sem_reference(tmp_path, monkeypatch, capsys):
    documento = _preparar(tmp_path, monkeypatch, fontes=("fontes", "ans", "cfm"))
    assert colunas_raspe.main([documento]) == 1
    assert "anvisa.md: falta a reference" in capsys.readouterr().err


def test_bloco_de_fonte_fora_do_documento(tmp_path, monkeypatch, capsys):
    documento = _preparar(tmp_path, monkeypatch, fontes=("fontes", "ans", "anvisa", "cfm", "capes"))
    assert colunas_raspe.main([documento]) == 1
    assert "capes.md: tem bloco de colunas" in capsys.readouterr().err


def test_marcadores_ausentes_nao_grava_nada(tmp_path, monkeypatch):
    documento = _preparar(tmp_path, monkeypatch)
    (tmp_path / "cfm.md").write_text("sem marcadores\n", encoding="utf-8")
    antes = (tmp_path / "fontes.md").read_text(encoding="utf-8")
    with pytest.raises(SystemExit, match="marcadores"):
        colunas_raspe.main([documento])
    # fontes.md vem antes de cfm.md e ficaria gravado se a escrita fosse arquivo a arquivo.
    assert (tmp_path / "fontes.md").read_text(encoding="utf-8") == antes
