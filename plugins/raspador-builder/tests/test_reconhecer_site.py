"""Testes do scripts/reconhecer_site.py contra um site local.

Cada teste roda o `main()` do script com a espera zerada e confere o código de saída (2 quer
dizer "o robots.txt não permite"), o que foi impresso e quais caminhos o servidor recebeu.
A decisão sobre o robots.txt tem de ser a mesma em qualquer versão do Python: até a 3.14 o
`urllib.robotparser` da biblioteca padrão aplica a primeira regra que casa e não entende `*`
nem `$`, e a RFC 9309 manda aplicar a regra de caminho mais longo.
"""

import socket
import sys
import time

import pytest
from conftest import carregar_modulo

TEXTO = "text/plain; charset=utf-8"
HTML = "text/html; charset=utf-8"
PAGINA_DE_BUSCA = (
    "<html><body><h1>Busca</h1><p>Resultados 1 a 10 de 24</p>"
    + "<p>texto de enchimento para não parecer página montada por script</p>" * 10
    + "</body></html>"
)


@pytest.fixture
def reconhecer(monkeypatch):
    modulo = carregar_modulo("scripts/reconhecer_site.py")
    monkeypatch.setattr(modulo, "ESPERA", 0)
    return modulo


def rodar(reconhecer, monkeypatch, endereco):
    monkeypatch.setattr(sys, "argv", ["reconhecer_site.py", endereco])
    return reconhecer.main()


def montar_site(servidor, robots, tipo_robots=TEXTO):
    servidor.rotas["/robots.txt"] = (200, tipo_robots, robots)
    servidor.rotas["/busca"] = (200, HTML, PAGINA_DE_BUSCA)
    servidor.rotas["/"] = (200, HTML, '<html><body><a href="/busca">Buscar</a></body></html>')


# Cada caso: (descrição, robots.txt, caminho pedido, permitido?)
CASOS_ROBOTS = [
    ("Allow antes de Disallow: o mais longo vence", "User-agent: *\nAllow: /\nDisallow: /busca\n",
     "/busca?q=licitacao", False),
    ("curinga * no meio do caminho", "User-agent: *\nDisallow: /*?q=\n", "/busca?q=licitacao", False),
    ("âncora $ casa o fim exato", "User-agent: *\nDisallow: /busca$\n", "/busca", False),
    ("âncora $ não casa caminho mais comprido", "User-agent: *\nDisallow: /busca$\n", "/busca?q=licitacao", True),
    ("Disallow: / com Allow: /busca", "User-agent: *\nDisallow: /\nAllow: /busca\n", "/busca?q=licitacao", True),
    ("grupo do robô permite onde * proíbe",
     "User-agent: *\nDisallow: /\n\nUser-agent: raspador-de-pesquisa\nAllow: /\n", "/busca?q=licitacao", True),
    ("grupo do robô proíbe onde * permite",
     "User-agent: *\nAllow: /\n\nUser-agent: raspador-de-pesquisa\nDisallow: /busca\n", "/busca?q=licitacao", False),
    ("empate entre Allow e Disallow favorece Allow",
     "User-agent: *\nDisallow: /busca\nAllow: /busca\n", "/busca?q=licitacao", True),
    ("percent-encoding de caractere não reservado", "User-agent: *\nDisallow: /%62usca\n", "/busca?q=licitacao", False),
]


@pytest.mark.parametrize("descricao, robots, caminho, permitido", CASOS_ROBOTS, ids=[c[0] for c in CASOS_ROBOTS])
def test_decisao_do_robots_segue_a_rfc_9309(servidor, reconhecer, monkeypatch, capsys, descricao, robots, caminho,
                                            permitido):
    montar_site(servidor, robots)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + caminho)
    saida = capsys.readouterr().out
    if permitido:
        assert codigo == 0, saida
        assert caminho in servidor.pedidos
    else:
        assert codigo == 2, saida
        assert servidor.pedidos == ["/robots.txt"], "nenhum pedido depois do robots.txt que proíbe"


def test_robots_ausente_404_permite(servidor, reconhecer, monkeypatch, capsys):
    servidor.rotas["/busca"] = (200, HTML, PAGINA_DE_BUSCA)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 0, saida
    assert "Código: 404" in saida


def test_robots_servido_como_html_vale_pelo_conteudo(servidor, reconhecer, monkeypatch, capsys):
    """Servidor mal configurado entrega o robots.txt com Content-Type text/html; as regras valem."""
    montar_site(servidor, "User-agent: *\nDisallow: /\n", tipo_robots=HTML)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    assert codigo == 2, capsys.readouterr().out
    assert servidor.pedidos == ["/robots.txt"]


def test_pagina_html_no_lugar_do_robots_nao_tem_regra(servidor, reconhecer, monkeypatch, capsys):
    """Site que responde 200 com uma página HTML qualquer em /robots.txt não declarou regra."""
    montar_site(servidor, "<!doctype html><html><body><h1>Portal</h1><p>Bem-vindo</p></body></html>", HTML)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 0, saida
    assert "nenhuma regra" in saida.lower()


def test_nenhum_pedido_a_endereco_proibido(servidor, reconhecer, monkeypatch, capsys):
    """Página inicial, scripts e API candidatos passam pela mesma conferência do robots.txt."""
    robots = "User-agent: *\nDisallow: /$\nAllow: /\nDisallow: /js/\nDisallow: /api/\n"
    montar_site(servidor, robots)
    servidor.rotas["/busca"] = (
        200,
        HTML,
        PAGINA_DE_BUSCA.replace(
            "</body>", '<script src="/js/app.js"></script><script>fetch("/api/busca?q=x")</script></body>'
        ),
    )
    servidor.rotas["/js/app.js"] = (200, "application/javascript", 'fetch("/api/outra.json")')
    servidor.rotas["/api/busca"] = (200, "application/json", '{"total": 0}')
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 0, saida
    assert servidor.pedidos == ["/robots.txt", "/busca?q=licitacao"], saida
    assert "proibido pelo robots.txt" in saida


def test_crawl_delay_do_grupo_que_vale_para_o_robo(servidor, reconhecer, monkeypatch, capsys):
    robots = (
        "User-agent: *\nCrawl-delay: 2\n\n"
        "User-agent: raspador-de-pesquisa\nCrawl-delay: 10\nDisallow: /privado\n"
    )
    montar_site(servidor, robots)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 0, saida
    # As linhas do arquivo aparecem ecoadas com "  | "; a conclusão do script vem no começo da linha.
    conclusoes = [linha for linha in saida.splitlines() if linha.startswith("Crawl-delay:")]
    assert len(conclusoes) == 1, saida
    assert conclusoes[0].startswith("Crawl-delay: 10 s"), saida


# --- codificação do robots.txt ------------------------------------------------------------------


def test_robots_text_plain_sem_charset_com_bom_e_acento_vale_como_utf8(servidor, reconhecer, monkeypatch, capsys):
    """A RFC 9309 (2.3) diz que o robots.txt é UTF-8; o `requests` lê `text/plain` sem charset como
    ISO-8859-1, e aí o BOM vira "ï»¿" e a regra acentuada vira outra palavra."""
    robots = "﻿User-agent: *\nDisallow: /licitação\n".encode()
    montar_site(servidor, robots, tipo_robots="text/plain")
    servidor.rotas["/licita%C3%A7%C3%A3o"] = (200, HTML, PAGINA_DE_BUSCA)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/licita%C3%A7%C3%A3o?q=x")
    saida = capsys.readouterr().out
    assert codigo == 2, saida
    assert servidor.pedidos == ["/robots.txt"]
    assert "Disallow: /licitação" in saida  # o eco do arquivo sai legível


def test_robots_com_bom_na_primeira_linha_nao_perde_o_grupo(servidor, reconhecer, monkeypatch, capsys):
    montar_site(servidor, "﻿User-agent: *\nDisallow: /busca\n", tipo_robots="text/plain")
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    assert codigo == 2, capsys.readouterr().out
    assert servidor.pedidos == ["/robots.txt"]


# --- redirecionamentos --------------------------------------------------------------------------

PAGINA_COM_SCRIPT_E_API = PAGINA_DE_BUSCA.replace(
    "</body>", '<script src="/js/app.js"></script><script>fetch("/api/dados.json")</script></body>'
)


def redirecionar(destino, codigo=302):
    return (codigo, HTML, "", {"Location": destino})


# Cada caso: (descrição, rota que redireciona para /privado/...)
CASOS_REDIRECIONAMENTO = [
    ("página pedida", "/busca"),
    ("página inicial", "/"),
    ("script do mesmo site", "/js/app.js"),
    ("API candidato", "/api/dados.json"),
]


@pytest.mark.parametrize("descricao, origem", CASOS_REDIRECIONAMENTO, ids=[c[0] for c in CASOS_REDIRECIONAMENTO])
def test_redirecionamento_para_caminho_proibido_nao_e_seguido(servidor, reconhecer, monkeypatch, capsys, descricao,
                                                              origem):
    """O robots.txt vale para cada salto: Location que cai em caminho proibido não é pedido.

    Quando é a página pedida que leva ao caminho proibido, o script para como se ela fosse
    proibida (código 2); nos outros casos só aquele pedido fica de fora."""
    montar_site(servidor, "User-agent: *\nDisallow: /privado\n")
    servidor.rotas["/busca"] = (200, HTML, PAGINA_COM_SCRIPT_E_API)
    servidor.rotas["/js/app.js"] = (200, "application/javascript", "var x = 1;")
    servidor.rotas["/api/dados.json"] = (200, "application/json", "{}")
    servidor.rotas[origem] = redirecionar("/privado/destino")
    servidor.rotas["/privado/destino"] = (200, HTML, PAGINA_DE_BUSCA)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == (2 if origem == "/busca" else 0), saida
    assert not [p for p in servidor.pedidos if p.startswith("/privado")], servidor.pedidos
    assert "/privado/destino: proibido pelo robots.txt, não pedido" in saida


def test_pagina_pedida_que_redireciona_para_caminho_proibido_para_como_proibida(
    servidor, reconhecer, monkeypatch, capsys
):
    """Sem isso, a seção 1 dizia "permitido: sim", a seção 4 saía vazia e o código era 0: quem lê
    só a conclusão seguiria para a coleta de uma página que cai em caminho proibido."""
    montar_site(servidor, "User-agent: *\nDisallow: /privado\n")
    servidor.rotas["/busca"] = redirecionar("/privado/x")
    servidor.rotas["/privado/x"] = (200, HTML, PAGINA_DE_BUSCA)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 2, saida
    assert servidor.pedidos == ["/robots.txt", "/busca?q=licitacao"], servidor.pedidos
    secao_1 = saida.split("== 2.")[0]
    assert f"redireciona para {servidor.raiz}/privado/x, que o robots.txt não permite" in secao_1, saida


@pytest.mark.parametrize(
    "destino",
    ["/publico/../privado/x", "{raiz}/publico/../privado/x", "{raiz}/publico/%2E%2E/privado/x"],
    ids=["relativo", "absoluto", "ponto-ponto codificado"],
)
def test_destino_com_segmentos_de_ponto_e_conferido_resolvido(servidor, reconhecer, monkeypatch, capsys, destino):
    """O destino é conferido com os segmentos ".." resolvidos, como o requests o pede: o urllib3
    manda "http://site/publico/../privado/x" como "/privado/x".

    "%2E%2E" o requests decodifica depois de resolver os pontos e manda "/publico/../privado/x",
    que o servidor costuma ler como "/privado/x": a conferência olha as duas formas."""
    montar_site(servidor, "User-agent: *\nDisallow: /privado\n")
    servidor.rotas["/busca"] = redirecionar(destino.format(raiz=servidor.raiz))
    servidor.rotas["/privado/x"] = (200, HTML, PAGINA_DE_BUSCA)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 2, saida
    assert servidor.pedidos == ["/robots.txt", "/busca?q=licitacao"], servidor.pedidos
    assert "que o robots.txt não permite" in saida.split("== 2.")[0], saida


def test_redirecionamento_para_outro_site_nao_e_seguido(servidor, reconhecer, monkeypatch, capsys):
    montar_site(servidor, "User-agent: *\nAllow: /\n")
    porta = servidor.raiz.rsplit(":", 1)[1]
    # localhost e 127.0.0.1 chegam ao mesmo servidor, mas são sites diferentes para o script.
    servidor.rotas["/busca"] = redirecionar(f"http://localhost:{porta}/outra")
    servidor.rotas["/outra"] = (200, HTML, PAGINA_DE_BUSCA)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 0, saida
    assert "/outra" not in servidor.pedidos
    assert f"http://localhost:{porta}/outra: outro site, não pedido" in saida


def test_redirecionamento_permitido_e_seguido_e_aparece_nos_sinais(servidor, reconhecer, monkeypatch, capsys):
    montar_site(servidor, "User-agent: *\nDisallow: /privado\n")
    servidor.rotas["/busca"] = redirecionar("/login")
    servidor.rotas["/login"] = (200, HTML, '<html><body><input type="password"></body></html>')
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 0, saida
    assert "/login" in servidor.pedidos
    assert f"redirecionou para {servidor.raiz}/login" in saida


def test_redirecionamento_em_laco_para_em_cinco_saltos(servidor, reconhecer, monkeypatch, capsys):
    montar_site(servidor, "User-agent: *\nAllow: /\n")
    # O servidor desiste do laço no 21º pedido, para que um script sem limite reprove em vez de travar.
    servidor.rotas["/busca"] = lambda query: (
        redirecionar("/busca") if servidor.pedidos.count("/busca") <= 20 else (200, HTML, PAGINA_DE_BUSCA)
    )
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca")
    saida = capsys.readouterr().out
    assert codigo == 0, saida
    assert servidor.pedidos.count("/busca") == 6  # o pedido e cinco saltos
    assert "mais de 5 redirecionamentos" in saida


def test_robots_txt_redirecionado_e_seguido(servidor, reconhecer, monkeypatch, capsys):
    """RFC 9309, 2.3.1.2: o robots.txt redirecionado vale (até cinco saltos)."""
    montar_site(servidor, "")
    servidor.rotas["/robots.txt"] = redirecionar("/novo/robots.txt", codigo=301)
    servidor.rotas["/novo/robots.txt"] = (200, TEXTO, "User-agent: *\nDisallow: /\n")
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    assert codigo == 2, capsys.readouterr().out
    assert servidor.pedidos == ["/robots.txt", "/novo/robots.txt"]


# --- percent-encoding (RFC 9309, 2.2.2) ---------------------------------------------------------


def permite(reconhecer, robots, caminho):
    return reconhecer.RegrasRobots(robots).permite(reconhecer.USER_AGENT, "http://site.gov.br" + caminho)


# A tabela de exemplos da seção 2.2.2 (figura 4): a regra escrita como "Path" casa com o endereço
# "Path to Match". A terceira linha é o caractere U+30C4, que em UTF-8 é E3 83 84. As duas últimas
# conferem o que a tabela dá a entender: o mesmo %XX dos dois lados casa, e o texto "U+E38384"
# escrito na regra é letra, não o caractere.
TABELA_RFC_9309 = [
    ("/foo/bar?baz=quz", "/foo/bar?baz=quz", False),
    ("/foo/bar?baz=https://foo.bar", "/foo/bar?baz=https%3A%2F%2Ffoo.bar", False),
    ("/foo/bar/ツ", "/foo/bar/%E3%83%84", False),
    ("/foo/bar/%E3%83%84", "/foo/bar/%E3%83%84", False),
    ("/foo/bar/%62%61%7A", "/foo/bar/baz", False),
    ("/foo/bar/%62%61%7A", "/foo/bar/%62%61%7A", False),
    ("/foo/bar/U+E38384", "/foo/bar/%E3%83%84", True),
]


@pytest.mark.parametrize(
    "regra, caminho, permitido", TABELA_RFC_9309, ids=[f"{c[0]} {c[1]}" for c in TABELA_RFC_9309]
)
def test_tabela_de_exemplos_da_rfc_9309(reconhecer, regra, caminho, permitido):
    assert permite(reconhecer, f"User-agent: *\nDisallow: {regra}\n", caminho) is permitido


def proibe(regra):
    return f"User-agent: *\nDisallow: {regra}\n"


# A regra casa com o caminho mais a consulta como uma cadeia só: o curinga atravessa o "?", e o
# "=", o "&" e a "/" que ele alcança na consulta são os da consulta.
# Cada caso: (descrição, robots.txt, caminho, permitido?)
CASOS_CURINGA_ATE_A_CONSULTA = [
    ("parâmetro depois do curinga", proibe("/*sort="), "/busca?sort=1", False),
    ("& depois do curinga", proibe("/*&page="), "/busca?q=a&page=2", False),
    ("= e âncora depois do curinga", proibe("/*=x$"), "/p?a=x", False),
    ("curinga no lugar do ?", proibe("/busca*q="), "/busca?q=1", False),
    ("barra da consulta depois do curinga", proibe("/*/b"), "/x?u=/b", False),
    ("parâmetro entre curingas", proibe("/*add-to-cart=*"), "/?add-to-cart=12", False),
    ("Allow mais longo com curinga até a consulta",
     "User-agent: *\nDisallow: /busca\nAllow: /busca*sort=\n", "/busca?sort=1", True),
]


@pytest.mark.parametrize(
    "descricao, robots, caminho, permitido",
    CASOS_CURINGA_ATE_A_CONSULTA,
    ids=[c[0] for c in CASOS_CURINGA_ATE_A_CONSULTA],
)
def test_curinga_atravessa_para_a_consulta(reconhecer, descricao, robots, caminho, permitido):
    assert permite(reconhecer, robots, caminho) is permitido


# O endereço é conferido como o requests o manda: "|" e '"' vão como %7C e %22, o "%" solto vai como
# %25 e "/publico/../privado" vai como "/privado". "*" e "$" do endereço são letras, e casam com o
# %2A e o %24 da regra.
# Cada caso: (descrição, regra, caminho, permitido?)
CASOS_COMO_ENVIADO = [
    ("| na regra, %7C no endereço", "/a|b", "/a%7Cb", False),
    ("%7C na regra, | no endereço", "/a%7Cb", "/a|b", False),
    ('" na regra, %22 no endereço', '/a"b', "/a%22b", False),
    ('%22 na regra, " no endereço', "/a%22b", '/a"b', False),
    ("% solto no endereço vai como %25", "/a%25zz", "/a%zz", False),
    ("% solto dos dois lados", "/a%zz", "/a%zz", False),
    ("%25 não é decodificado duas vezes", "/A", "/%2541", True),
    ("segmento .. resolvido", "/privado", "/publico/../privado/x", False),
    ("* do endereço é letra e casa com %2A", "/a%2A", "/a*", False),
    ("$ no fim do endereço é letra e casa com %24", "/a%24", "/a$", False),
    ("* da regra é curinga e casa com %2A", "/a*b", "/a%2Axb", False),
    ("%3F da regra não abre a consulta", "/a%3Fb", "/a?b", True),
    ("? da regra casa com o %3F de dentro da consulta", "/a?b?c", "/a?b%3Fc", False),
    ("= da regra não casa com %3D na consulta", "/a?b=c", "/a?b%3Dc", True),
    ("& da regra casa com %26 no caminho", "/a&b", "/a%26b", False),
]


@pytest.mark.parametrize(
    "descricao, regra, caminho, permitido", CASOS_COMO_ENVIADO, ids=[c[0] for c in CASOS_COMO_ENVIADO]
)
def test_endereco_conferido_como_o_requests_o_manda(reconhecer, descricao, regra, caminho, permitido):
    assert permite(reconhecer, proibe(regra), caminho) is permitido


# Caractere reservado escrito por extenso de um lado e codificado do outro é o mesmo caractere.
# Cada caso: (descrição, regra, caminho, permitido?)
CASOS_RESERVADOS = [
    ("regra codificada, endereço por extenso", "/%3A", "/:", False),
    ("regra por extenso, endereço codificado", "/:", "/%3A", False),
    ("regra por extenso, endereço codificado em minúscula", "/:", "/%3a", False),
    ("barra na consulta", "/?q=/", "/?q=%2F", False),
    ("Allow codificado vence Disallow: /", "/%3A", "/:", True),
    # Na parte do caminho, "/" separa segmentos e "%2F" é uma letra do segmento: não se confundem.
    ("barra codificada no caminho não é separador", "//", "/%2f", True),
    ("barra codificada no caminho, os dois codificados", "/a%2fb", "/a%2Fb", False),
    # Na consulta, "&" e "=" separam os parâmetros; codificados, são parte do valor.
    ("& codificado na consulta não é separador", "/?a=1&b", "/?a=1%26b", True),
]


@pytest.mark.parametrize("descricao, regra, caminho, permitido", CASOS_RESERVADOS, ids=[c[0] for c in CASOS_RESERVADOS])
def test_caractere_reservado_codificado_ou_por_extenso(reconhecer, descricao, regra, caminho, permitido):
    if descricao.startswith("Allow"):
        robots = f"User-agent: *\nDisallow: /\nAllow: {regra}\n"
    else:
        robots = f"User-agent: *\nDisallow: {regra}\n"
    assert permite(reconhecer, robots, caminho) is permitido


# --- casos da RFC 9309 que nenhum teste acima prendia -------------------------------------------

CASOS_GRUPOS = [
    # RFC 9309, 2.2.1: o nome do robô se compara sem diferença de caixa.
    ("nome do robô sem diferença de caixa",
     "User-agent: *\nAllow: /\n\nUser-agent: Raspador-De-Pesquisa\nDisallow: /busca\n", False),
    # RFC 9309, 2.2.2: "Disallow:" sem caminho não proíbe nada.
    ("Disallow vazio não proíbe", "User-agent: *\nDisallow:\n", True),
    # RFC 9309, 2.2.1: grupos com o mesmo nome de robô se somam.
    ("grupos com o mesmo nome se somam", "User-agent: *\nDisallow: /outra\n\nUser-agent: *\nDisallow: /busca\n", False),
]


@pytest.mark.parametrize("descricao, robots, permitido", CASOS_GRUPOS, ids=[c[0] for c in CASOS_GRUPOS])
def test_grupos_e_regras_do_robots(servidor, reconhecer, monkeypatch, capsys, descricao, robots, permitido):
    montar_site(servidor, robots)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == (0 if permitido else 2), saida
    assert ("/busca?q=licitacao" in servidor.pedidos) is permitido


def test_robots_com_erro_do_servidor_proibe_tudo(servidor, reconhecer, monkeypatch, capsys):
    """RFC 9309, 2.3.1.4: 5xx no robots.txt quer dizer "inalcançável", e aí tudo é proibido."""
    montar_site(servidor, "")
    servidor.rotas["/robots.txt"] = (503, "text/plain", "manutenção")
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 2, saida
    assert servidor.pedidos == ["/robots.txt"]
    assert "Erro do servidor" in saida


def test_robots_sem_resposta_proibe_tudo(reconhecer, monkeypatch, capsys):
    """Sem resposta (erro de rede) o robots.txt também é inalcançável: nada se pede depois."""
    with socket.socket() as soquete:  # porta que acabou de ficar livre: ninguém atende nela
        soquete.bind(("127.0.0.1", 0))
        porta = soquete.getsockname()[1]
    pedidos = []
    original = reconhecer.Visitante.get

    def registrar(visitante, endereco, *argumentos, **nomeados):
        pedidos.append(endereco)
        return original(visitante, endereco, *argumentos, **nomeados)

    monkeypatch.setattr(reconhecer.Visitante, "get", registrar)
    codigo = rodar(reconhecer, monkeypatch, f"http://127.0.0.1:{porta}/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 2, saida
    assert pedidos == [f"http://127.0.0.1:{porta}/robots.txt"]
    assert "Sem resposta" in saida


def test_regra_com_muitos_curingas_nao_trava(reconhecer):
    """Com expressão regular, cada `*` vira `.*` e o retrocesso cresce como potência do tamanho
    do endereço: oito curingas contra 41 letras levavam segundos, e um robots.txt hostil travaria
    o script. O casamento tem de ser linear."""
    robots = "User-agent: *\nDisallow: /" + "*a" * 8 + "*b\n"
    inicio = time.perf_counter()
    assert permite(reconhecer, robots, "/" + "a" * 40)
    assert time.perf_counter() - inicio < 0.5


# Cada caso: (regra, caminho, casa?). Conferem o casamento por partes entre curingas.
CASOS_CURINGA = [
    ("/a*b*c", "/aXbYc", True),
    ("/a*b*c", "/aXcYb", False),
    ("/a*b$", "/abab", True),
    ("/a*b$", "/abba", False),
    ("/*.pdf$", "/x.pdf.pdf", True),
    ("/*ab*ab$", "/ab", False),
    ("/*ab*ab$", "/abab", True),
    ("/a**b", "/ab", True),
    ("*", "/qualquer", True),
    ("/*$", "/", True),
    # Cada trecho do meio é procurado depois do anterior: o "b" do meio não pode ser o de "/ab".
    ("/ab*b*c", "/abc", False),
    ("/ab*b*c", "/abbc", True),
    # "/" e "?" do alvo também passam pelo casamento com classes.
    ("/a*?b*/c$", "/a?b/c", True),
    ("/a*?b*/c$", "/a?c/b", False),
]


@pytest.mark.parametrize("regra, caminho, casa", CASOS_CURINGA, ids=[f"{c[0]} {c[1]}" for c in CASOS_CURINGA])
def test_casamento_com_curinga_e_ancora(reconhecer, regra, caminho, casa):
    assert reconhecer.casa(regra, caminho) is casa
