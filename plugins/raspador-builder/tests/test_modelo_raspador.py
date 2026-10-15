"""Testes do assets/modelo_raspador.py contra uma API local.

O modelo traz trechos ADAPTAR que mudam de site para site; o teste faz a adaptação que o usuário
faria (endereço, onde está o total, como ler cada resultado) e roda o `main()` de verdade, com a
espera zerada. O que se confere é o que o modelo garante sem adaptação: paginação, códigos de
resposta, espera pedida pelo site e o CSV gravado.
"""

import csv
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import requests
from conftest import carregar_modulo

JSON = "application/json"
TITULOS = [f"Licitação {numero:03d}" for numero in range(1, 25)]  # 24 resultados
POR_PAGINA = 10


@pytest.fixture
def modelo(monkeypatch, servidor):
    modulo = carregar_modulo("assets/modelo_raspador.py")
    monkeypatch.setattr(modulo, "ESPERA", 0)
    monkeypatch.setattr(modulo, "ENDERECO_BUSCA", servidor.raiz + "/api/busca")
    monkeypatch.setattr(modulo, "ler_total", lambda dados: dados.get("total"))
    monkeypatch.setattr(modulo, "ler_resultados", lambda dados: [{"titulo": t} for t in dados["resultados"]])
    return modulo


def pagina_json(itens, total=None):
    corpo = {"resultados": itens}
    if total is not None:
        corpo["total"] = total
    return (200, JSON, json.dumps(corpo))


def fatia(pagina):
    inicio = (pagina - 1) * POR_PAGINA
    return TITULOS[inicio : inicio + POR_PAGINA]


def ultima_pagina_repetida(total=None):
    """API comum: a página pedida além da última devolve a última de novo."""
    ultima = (len(TITULOS) - 1) // POR_PAGINA + 1

    def responder(query):
        return pagina_json(fatia(min(int(query.get("pagina", "1")), ultima)), total)

    return responder


def rodar(modelo, monkeypatch, saida, *extras):
    monkeypatch.setattr(sys, "argv", ["raspador.py", "--pesquisa", "licitação", "--saida", str(saida), *extras])
    return modelo.main()


def linhas_do_csv(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


# --- página repetida e CSV parcial -------------------------------------------------------------


def test_total_maior_que_os_visiveis_e_ultima_pagina_repetida(servidor, modelo, monkeypatch, tmp_path, capsys):
    """Tribunal informa 27 (inclui 3 em segredo de justiça) e mostra 24; a página 4 repete a 3."""
    servidor.rotas["/api/busca"] = ultima_pagina_repetida(total=27)
    saida = tmp_path / "resultados.csv"
    codigo = rodar(modelo, monkeypatch, saida)
    assert [linha["titulo"] for linha in linhas_do_csv(saida)] == TITULOS
    assert codigo == 1  # o número de linhas não bate com o total: avisa, mas grava
    assert "não bate com o total" in capsys.readouterr().err


def test_sem_total_e_ultima_pagina_repetida(servidor, modelo, monkeypatch, tmp_path):
    servidor.rotas["/api/busca"] = ultima_pagina_repetida(total=None)
    saida = tmp_path / "resultados.csv"
    assert rodar(modelo, monkeypatch, saida) == 0
    assert [linha["titulo"] for linha in linhas_do_csv(saida)] == TITULOS


def test_site_que_ignora_a_pagina_para_com_erro_e_grava_o_parcial(servidor, modelo, monkeypatch, tmp_path, capsys):
    """Página cheia repetida não é fim: o parâmetro de página está errado. Para, mas grava."""
    servidor.rotas["/api/busca"] = lambda query: pagina_json(fatia(1))
    saida = tmp_path / "resultados.csv"
    codigo = rodar(modelo, monkeypatch, saida)
    assert codigo != 0
    assert [linha["titulo"] for linha in linhas_do_csv(saida)] == fatia(1)
    erro = capsys.readouterr().err
    assert "repetiu a anterior" in erro
    assert str(saida) in erro


def test_acesso_negado_no_meio_grava_o_parcial(servidor, modelo, monkeypatch, tmp_path, capsys):
    def responder(query):
        if query.get("pagina") == "2":
            return (403, "text/html", "<html>proibido</html>")
        return pagina_json(fatia(1), total=24)

    servidor.rotas["/api/busca"] = responder
    saida = tmp_path / "resultados.csv"
    codigo = rodar(modelo, monkeypatch, saida)
    assert codigo != 0
    assert len(linhas_do_csv(saida)) == POR_PAGINA
    assert "403" in capsys.readouterr().err


# --- Retry-After --------------------------------------------------------------------------------


def test_retry_after_acima_do_teto_para_sem_dormir(servidor, modelo, monkeypatch):
    esperas = []
    monkeypatch.setattr(modelo.time, "sleep", esperas.append)
    servidor.rotas["/api/busca"] = (429, "text/plain", "devagar", {"Retry-After": "86400"})

    with pytest.raises(RuntimeError, match="86400"):
        modelo.pedir(requests.Session(), modelo.ENDERECO_BUSCA, {"pagina": 1})
    assert max(esperas) <= modelo.TETO_ESPERA


def test_retry_after_dentro_do_teto_espera_e_tenta_de_novo(servidor, modelo, monkeypatch):
    esperas = []
    monkeypatch.setattr(modelo.time, "sleep", esperas.append)
    respostas = iter([(429, "text/plain", "devagar", {"Retry-After": "3"}), pagina_json(fatia(1), total=24)])
    servidor.rotas["/api/busca"] = lambda query: next(respostas)

    resposta = modelo.pedir(requests.Session(), modelo.ENDERECO_BUSCA, {"pagina": 1})
    assert resposta.status_code == 200
    assert 3.0 in esperas


@pytest.fixture
def fuso_de_brasilia(monkeypatch):
    """Põe o processo em UTC-3 (string POSIX, não depende de tzdata) e restaura no fim."""
    monkeypatch.setenv("TZ", "BRT3")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.mark.parametrize("sufixo", ["", " -0000"], ids=["sem fuso", "fuso desconhecido -0000"])
def test_retry_after_com_data_sem_fuso_e_lida_como_utc(modelo, fuso_de_brasilia, sufixo):
    daqui_a_30 = datetime.now(timezone.utc) + timedelta(seconds=30)  # noqa: UP017 (o teste roda no 3.10)
    resposta = SimpleNamespace(headers={"Retry-After": daqui_a_30.strftime("%a, %d %b %Y %H:%M:%S") + sufixo})
    assert 25 <= modelo.segundos_para_esperar(resposta, padrao=1.0) <= 31


# --- total informado ----------------------------------------------------------------------------


def test_sem_total_diz_uma_vez_que_o_site_nao_informou(servidor, modelo, monkeypatch, tmp_path, capsys):
    servidor.rotas["/api/busca"] = lambda query: pagina_json(fatia(int(query.get("pagina", "1"))))
    assert rodar(modelo, monkeypatch, tmp_path / "resultados.csv") == 0
    saida = capsys.readouterr()
    tudo = saida.out + saida.err
    assert "None" not in tudo
    assert saida.err.count("o site não informou o total") == 1
    assert "o site não informou o total" in saida.out


def test_com_total_informa_uma_vez(servidor, modelo, monkeypatch, tmp_path, capsys):
    servidor.rotas["/api/busca"] = lambda query: pagina_json(fatia(int(query.get("pagina", "1"))), total=24)
    assert rodar(modelo, monkeypatch, tmp_path / "resultados.csv") == 0
    saida = capsys.readouterr()
    assert saida.err.count("24 resultados") == 1
    assert "o site informou 24" in saida.out
