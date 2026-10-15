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
    parcial = tmp_path / "resultados.parcial.csv"
    assert [linha["titulo"] for linha in linhas_do_csv(parcial)] == fatia(1)
    assert not saida.exists()
    erro = capsys.readouterr().err
    assert "a página 2 só trouxe linhas da página 1" in erro
    assert str(parcial) in erro


@pytest.mark.parametrize("total", [None, 30, 33], ids=["sem total", "total 30", "total 33"])
def test_ultima_pagina_cheia_repetida_encerra_a_coleta(servidor, modelo, monkeypatch, tmp_path, capsys, total):
    """30 resultados, múltiplo de 10: a última página veio cheia, e a página 4 a repete. As páginas
    1 a 3 diferem, então o parâmetro de página funciona; a repetição é o fim, não erro."""
    trinta = [f"Contrato {numero:03d}" for numero in range(1, 31)]

    def responder(query):
        pagina = min(int(query.get("pagina", "1")), 3)
        return pagina_json(trinta[(pagina - 1) * POR_PAGINA : pagina * POR_PAGINA], total)

    servidor.rotas["/api/busca"] = responder
    saida = tmp_path / "resultados.csv"
    codigo = rodar(modelo, monkeypatch, saida)
    erro = capsys.readouterr().err
    assert [linha["titulo"] for linha in linhas_do_csv(saida)] == trinta
    assert codigo == (1 if total == 33 else 0), erro
    assert "confira o parâmetro" not in erro
    if total == 33:
        assert "só trouxe linhas já coletadas" in erro


def test_site_que_ignora_a_pagina_e_muda_a_ordem_para_com_erro(servidor, modelo, monkeypatch, tmp_path, capsys):
    """O site ignora o número da página e devolve a primeira com a ordem girada a cada pedido
    (ordenação por relevância com empate). A página 2 não repete a 1 na ordem, mas só traz
    linhas que já vieram: é o parâmetro de página que está errado."""
    primeira = fatia(1)

    def responder(query):
        giro = int(query.get("pagina", "1")) % POR_PAGINA
        return pagina_json(primeira[giro:] + primeira[:giro], total=20)

    servidor.rotas["/api/busca"] = responder
    saida = tmp_path / "resultados.csv"
    codigo = rodar(modelo, monkeypatch, saida)
    assert codigo == 2
    erro = capsys.readouterr().err
    assert "confira o parâmetro de paginação" in erro
    parcial = tmp_path / "resultados.parcial.csv"
    assert sorted(linha["titulo"] for linha in linhas_do_csv(parcial)) == sorted(primeira)


def resultados_com_campos(dados):
    """`ler_resultados` de quem pediu só a data e a classe: processos diferentes dão a mesma linha."""
    return [{"data": item["data"], "classe": item["classe"]} for item in dados["resultados"]]


def processo(data, classe):
    return {"data": data, "classe": classe}


A, B, C, D, E, F = (processo(f"2026-0{mes}-01", "Apelação") for mes in range(1, 7))


def paginas_fixas(paginas):
    """Site sem total que devolve `paginas` e, além da última, a última de novo."""

    def responder(query):
        numero = min(int(query.get("pagina", "1")), len(paginas))
        return pagina_json(paginas[numero - 1])

    return responder


def test_pagina_legitima_com_linhas_ja_vistas_nao_encerra_a_coleta(servidor, modelo, monkeypatch, tmp_path, capsys):
    """A página 3 só traz linhas iguais a linhas já vistas, mas não repete página nenhuma inteira:
    é página nova. Comparando linha a linha, a coleta parava ali com 4 das 8 linhas e saída 0."""
    monkeypatch.setattr(modelo, "ler_resultados", resultados_com_campos)
    servidor.rotas["/api/busca"] = paginas_fixas([[A, B], [C, D], [A, D], [E, F]])
    saida = tmp_path / "resultados.csv"
    assert rodar(modelo, monkeypatch, saida) == 0
    assert [(linha["data"], linha["classe"]) for linha in linhas_do_csv(saida)] == [
        (item["data"], item["classe"]) for item in [A, B, C, D, A, D, E, F]
    ]
    assert "página 5 repete a página 4" in capsys.readouterr().err


def test_parada_por_pagina_repetida_sem_total_avisa_que_pode_estar_incompleta(
    servidor, modelo, monkeypatch, tmp_path, capsys
):
    """A página 3 repete a 1 inteira. Sem total, isso não se distingue de um site que volta à
    primeira página quando se pede além da última: a coleta para, mas não em silêncio."""
    monkeypatch.setattr(modelo, "ler_resultados", resultados_com_campos)
    servidor.rotas["/api/busca"] = paginas_fixas([[A, B], [C, D], [A, B], [E, F]])
    saida = tmp_path / "resultados.csv"
    assert rodar(modelo, monkeypatch, saida) == 0
    assert len(linhas_do_csv(saida)) == 4
    erro = capsys.readouterr().err
    assert "página 3 repete a página 1" in erro
    assert "pode estar incompleta" in erro


def test_site_que_volta_a_primeira_pagina_encerra_sem_duplicar(servidor, modelo, monkeypatch, tmp_path):
    """Pedida além da última, a página volta à primeira (e segue o ciclo). A página 4 repete a 1,
    não a 3: comparar só com a página anterior duplicaria a primeira página. Depois da página 12 o
    servidor responde 404, para que um raspador que não pare reprove em vez de travar."""

    def responder(query):
        pagina = int(query.get("pagina", "1"))
        if pagina > 12:
            return (404, JSON, "{}")
        return pagina_json(fatia((pagina - 1) % 3 + 1))

    servidor.rotas["/api/busca"] = responder
    saida = tmp_path / "resultados.csv"
    assert rodar(modelo, monkeypatch, saida) == 0
    assert [linha["titulo"] for linha in linhas_do_csv(saida)] == TITULOS


def test_acesso_negado_no_meio_grava_o_parcial(servidor, modelo, monkeypatch, tmp_path, capsys):
    def responder(query):
        if query.get("pagina") == "2":
            return (403, "text/html", "<html>proibido</html>")
        return pagina_json(fatia(1), total=24)

    servidor.rotas["/api/busca"] = responder
    saida = tmp_path / "resultados.csv"
    codigo = rodar(modelo, monkeypatch, saida)
    assert codigo != 0
    assert len(linhas_do_csv(tmp_path / "resultados.parcial.csv")) == POR_PAGINA
    assert "403" in capsys.readouterr().err


def test_parcial_nao_sobrescreve_o_csv_completo_anterior(servidor, modelo, monkeypatch, tmp_path, capsys):
    """Quem roda de novo e cai num erro não perde o CSV completo da rodada anterior."""
    saida = tmp_path / "resultados.csv"
    saida.write_text("titulo\nresultado completo de ontem\n", encoding="utf-8-sig")

    def responder(query):
        if query.get("pagina") == "2":
            return (403, "text/html", "<html>proibido</html>")
        return pagina_json(fatia(1), total=24)

    servidor.rotas["/api/busca"] = responder
    codigo = rodar(modelo, monkeypatch, saida)
    assert codigo == 2
    assert linhas_do_csv(saida) == [{"titulo": "resultado completo de ontem"}]
    parcial = tmp_path / "resultados.parcial.csv"
    assert len(linhas_do_csv(parcial)) == POR_PAGINA
    assert f"salvas em {parcial}" in capsys.readouterr().err


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


def test_ultima_tentativa_nao_dorme_antes_de_desistir(servidor, modelo, monkeypatch):
    """Depois da última tentativa não há outra: esperar o Retry-After só atrasaria o erro."""
    esperas = []
    monkeypatch.setattr(modelo.time, "sleep", esperas.append)
    servidor.rotas["/api/busca"] = (503, "text/plain", "fora do ar", {"Retry-After": "7"})

    with pytest.raises(RuntimeError, match="503"):
        modelo.pedir(requests.Session(), modelo.ENDERECO_BUSCA, {"pagina": 1})
    assert esperas.count(7.0) == modelo.TENTATIVAS - 1
    assert esperas[-1] == modelo.ESPERA  # a última espera é a de antes do último pedido


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


# --- interrupção e última tentativa -------------------------------------------------------------


def test_ctrl_c_grava_o_parcial(servidor, modelo, monkeypatch, tmp_path, capsys):
    """KeyboardInterrupt não é Exception: sem tratá-lo, Ctrl+C no meio perdia o que já tinha vindo."""
    servidor.rotas["/api/busca"] = lambda query: pagina_json(fatia(int(query.get("pagina", "1"))), total=24)
    pedir_original = modelo.pedir
    chamadas = []

    def pedir_e_interromper(*argumentos):
        chamadas.append(argumentos)
        if len(chamadas) == 3:
            raise KeyboardInterrupt
        return pedir_original(*argumentos)

    monkeypatch.setattr(modelo, "pedir", pedir_e_interromper)
    saida = tmp_path / "resultados.csv"
    assert rodar(modelo, monkeypatch, saida) == 2
    assert [linha["titulo"] for linha in linhas_do_csv(tmp_path / "resultados.parcial.csv")] == TITULOS[:20]
    assert "Ctrl+C" in capsys.readouterr().err
