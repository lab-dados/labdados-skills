"""Testes do scripts/reconhecer_site.py contra um site local.

Cada teste roda o `main()` do script com a espera zerada e confere o código de saída (2 quer
dizer "o robots.txt não permite"), o que foi impresso e quais caminhos o servidor recebeu.
A decisão sobre o robots.txt tem de ser a mesma em qualquer versão do Python: até a 3.14 o
`urllib.robotparser` da biblioteca padrão aplica a primeira regra que casa e não entende `*`
nem `$`, e a RFC 9309 manda aplicar a regra de caminho mais longo.
"""

import sys

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
    robots = "﻿User-agent: *\nDisallow: /licitação\n".encode("utf-8")
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
    """O robots.txt vale para cada salto: Location que cai em caminho proibido não é pedido."""
    montar_site(servidor, "User-agent: *\nDisallow: /privado\n")
    servidor.rotas["/busca"] = (200, HTML, PAGINA_COM_SCRIPT_E_API)
    servidor.rotas["/js/app.js"] = (200, "application/javascript", "var x = 1;")
    servidor.rotas["/api/dados.json"] = (200, "application/json", "{}")
    servidor.rotas[origem] = redirecionar("/privado/destino")
    servidor.rotas["/privado/destino"] = (200, HTML, PAGINA_DE_BUSCA)
    codigo = rodar(reconhecer, monkeypatch, servidor.raiz + "/busca?q=licitacao")
    saida = capsys.readouterr().out
    assert codigo == 0, saida
    assert not [p for p in servidor.pedidos if p.startswith("/privado")], servidor.pedidos
    assert "/privado/destino: proibido pelo robots.txt, não pedido" in saida


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
    servidor.rotas["/busca"] = redirecionar("/busca")
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
