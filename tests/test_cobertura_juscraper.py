"""Testa o sincronizador da cobertura da skill juscraper sem rede e sem o juscraper instalado.

O JSON daqui imita o formato de `scripts/tabela_cobertura.py --json` do juscraper. A conferencia
contra o juscraper de verdade e o passo `--check` do workflow `juscraper-cobertura`.
"""

import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("cobertura_juscraper", RAIZ / "scripts" / "cobertura_juscraper.py")
assert _spec is not None
assert _spec.loader is not None
cobertura_juscraper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cobertura_juscraper)

COBERTURA = {
    "tribunais": [
        {"sigla": "stf", "nome": "STF", "metodos": ["contar_decisoes", "listar_decisoes"]},
        {"sigla": "tjmg", "nome": "TJMG", "metodos": ["cposg", "cjsg"]},
        {"sigla": "trf3", "nome": "TRF3", "metodos": ["cpopg", "cjsg"]},
    ],
    "agregadores": [
        {"sigla": "comunica_cnj", "nome": "ComunicaCNJ", "metodos": ["listar_comunicacoes"]},
        {"sigla": "falcao", "nome": "Falcao", "metodos": ["listar_decisoes"]},
    ],
}


def test_matriz_tribunais():
    linhas = cobertura_juscraper.matriz_tribunais(COBERTURA)
    assert linhas[0] == "| Tribunal | cjsg | cjpg | cpopg | cposg | Outros metodos |"
    assert "| **TJMG** | sim | - | - | sim | - |" in linhas
    assert "| **STF** | - | - | - | - | `contar_decisoes`, `listar_decisoes` |" in linhas


def test_quem_tem_cada_metodo_junta_tribunais_e_agregadores():
    linhas = cobertura_juscraper.quem_tem_cada_metodo(COBERTURA)
    assert linhas[0] == "- `cjsg`: TJMG, TRF3"
    assert "- `listar_decisoes`: STF, Falcao" in linhas
    # Metodo que ninguem tem nao gera linha.
    assert not any(linha.startswith("- `cjpg`") for linha in linhas)


@pytest.mark.parametrize(
    ("descricao", "faltam"),
    [
        ("Cobre STF, TJMG, TRF3, ComunicaCNJ e Falcao.", []),
        ("Cobre STF, TJMGX, TRF3 e Falcao.", ["TJMG", "ComunicaCNJ"]),
    ],
)
def test_ausentes_na_descricao(descricao, faltam):
    skill_md = f"---\nname: juscraper\ndescription: {descricao}\n---\n\nTJMG ComunicaCNJ no corpo nao conta.\n"
    assert cobertura_juscraper.ausentes_na_descricao(COBERTURA, skill_md) == faltam


def _preparar(tmp_path, monkeypatch, descricao="STF, TJMG, TRF3, ComunicaCNJ, Falcao"):
    inicio, fim = cobertura_juscraper.marcadores("metodos")
    skill = tmp_path / "SKILL.md"
    skill.write_text(f"---\ndescription: {descricao}\n---\nantes\n{inicio}\n- velho\n{fim}\ndepois\n", encoding="utf-8")
    entrada = tmp_path / "cobertura.json"
    entrada.write_text(json.dumps(COBERTURA), encoding="utf-8")
    monkeypatch.setattr(cobertura_juscraper, "RAIZ", tmp_path)
    monkeypatch.setattr(cobertura_juscraper, "SKILL", tmp_path)
    monkeypatch.setattr(cobertura_juscraper, "BLOCOS", {(skill, "metodos"): cobertura_juscraper.quem_tem_cada_metodo})
    return skill, entrada


def test_check_reprova_e_escrita_corrige(tmp_path, monkeypatch, capsys):
    skill, entrada = _preparar(tmp_path, monkeypatch)

    assert cobertura_juscraper.main([str(entrada), "--check"]) == 1
    assert "SKILL.md: bloco gerado desatualizado" in capsys.readouterr().err
    assert "- velho" in skill.read_text(encoding="utf-8")

    assert cobertura_juscraper.main([str(entrada)]) == 0
    texto = skill.read_text(encoding="utf-8")
    assert texto.startswith("---\ndescription:")
    assert texto.endswith("\ndepois\n")
    assert "- `cposg`: TJMG" in texto
    assert cobertura_juscraper.main([str(entrada), "--check"]) == 0


def test_check_reprova_descricao_sem_raspador(tmp_path, monkeypatch, capsys):
    _, entrada = _preparar(tmp_path, monkeypatch, descricao="STF, TJMG, TRF3, ComunicaCNJ")
    assert cobertura_juscraper.main([str(entrada)]) == 1
    assert "nao cita: Falcao" in capsys.readouterr().err


def test_marcadores_ausentes(tmp_path):
    with pytest.raises(SystemExit, match="marcadores"):
        cobertura_juscraper.substituir("sem marcadores", "metodos", ["x"], tmp_path / "x.md")
