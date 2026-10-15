"""Peças comuns dos testes da skill raspador-builder.

Os dois programas da skill não são pacote: o script de reconhecimento e o modelo de raspador são
arquivos soltos que o usuário copia ou roda direto. Por isso os testes os carregam pelo caminho do
arquivo, e cada teste recebe uma cópia nova do módulo, para que um `monkeypatch` num teste não
vaze para o seguinte.

O servidor HTTP roda numa thread, na porta que o sistema escolher (porta 0), e guarda o caminho
de cada pedido recebido, para que o teste confira o que foi e o que não foi pedido.
"""

import importlib.util
import itertools
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

PASTA_SKILL = Path(__file__).resolve().parent.parent / "skills" / "raspador-builder"
_contador_modulos = itertools.count()


def carregar_modulo(caminho_relativo):
    caminho = PASTA_SKILL / caminho_relativo
    nome = f"_modulo_em_teste_{next(_contador_modulos)}"
    especificacao = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


class ServidorDeTeste:
    """Servidor local com rotas definidas pelo teste.

    `rotas` liga o caminho (sem a query) a uma tupla `(codigo, tipo, corpo)` ou
    `(codigo, tipo, corpo, cabecalhos)`, ou a uma função que recebe a query como dicionário e
    devolve uma dessas tuplas. Caminho sem rota devolve 404.
    """

    def __init__(self):
        self.rotas = {}
        self.pedidos = []
        servidor = self

        class Atendente(BaseHTTPRequestHandler):
            def log_message(self, *argumentos):
                pass

            def do_GET(self):
                servidor.pedidos.append(self.path)
                partes = urlsplit(self.path)
                rota = servidor.rotas.get(partes.path)
                if rota is None:
                    resposta = (404, "text/html; charset=utf-8", "<html><body>não achei</body></html>")
                elif callable(rota):
                    resposta = rota({chave: valor[0] for chave, valor in parse_qs(partes.query).items()})
                else:
                    resposta = rota
                codigo, tipo, corpo = resposta[:3]
                cabecalhos = resposta[3] if len(resposta) > 3 else {}
                bruto = corpo.encode("utf-8") if isinstance(corpo, str) else corpo
                self.send_response(codigo)
                self.send_header("Content-Type", tipo)
                self.send_header("Content-Length", str(len(bruto)))
                for nome, valor in cabecalhos.items():
                    self.send_header(nome, valor)
                self.end_headers()
                self.wfile.write(bruto)

        self._http = ThreadingHTTPServer(("127.0.0.1", 0), Atendente)
        self._thread = threading.Thread(target=self._http.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)

    @property
    def raiz(self):
        return f"http://127.0.0.1:{self._http.server_address[1]}"

    def iniciar(self):
        self._thread.start()
        return self

    def parar(self):
        self._http.shutdown()
        self._http.server_close()
        self._thread.join(timeout=5)


@pytest.fixture
def servidor():
    local = ServidorDeTeste().iniciar()
    yield local
    local.parar()
