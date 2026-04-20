"""Scraper para o {NOME_COMPLETO} ({SIGLA}).

Gerado automaticamente pela skill juscraper-builder.
Revisar e ajustar conforme necessário.
"""

import logging
import time
import tempfile
from pathlib import Path
from typing import Optional, Union

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from juscraper.utils.params import normalize_params

logger = logging.getLogger(__name__)


class {SIGLA}Scraper:
    """Scraper para o {NOME_COMPLETO} ({SIGLA})."""

    BASE_URL = "{BASE_URL}"
    SEARCH_URL = "{SEARCH_URL}"
    ITEMS_PER_PAGE = {ITEMS_PER_PAGE}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "juscraper/0.1 "
                "(https://github.com/jtrecenti/juscraper; "
                "pesquisa academica)"
            ),
            # TODO: Adicionar headers extras se necessário
        })

    # ---- Sessão / cookies ----

    def _init_session(self):
        """Obtém cookies de sessão necessários."""
        # TODO: Se o site exige GET prévio para cookies/CSRF, fazer aqui
        # resp = self.session.get(self.BASE_URL)
        # resp.raise_for_status()
        pass

    # ---- cjsg (jurisprudência) ----

    def cjsg(
        self,
        pesquisa: str,
        paginas: Optional[Union[int, list, range]] = None,
        # TODO: Adicionar parâmetros específicos do tribunal
        # data_julgamento_inicio: Optional[str] = None,
        # data_julgamento_fim: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Consulta de jurisprudência do {SIGLA}.

        Parameters
        ----------
        pesquisa : str
            Termo de busca.
        paginas : int, list, range, or None
            Páginas a baixar (1-based). None = todas.

        Returns
        -------
        pd.DataFrame
            Tabela com resultados da consulta.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            pasta = self.cjsg_download(
                pesquisa, paginas=paginas, diretorio=tmpdir, **kwargs
            )
            return self.cjsg_parse(pasta)

    def cjsg_download(
        self,
        pesquisa: str,
        paginas: Optional[Union[int, list, range]] = None,
        diretorio: str = ".",
        # TODO: parâmetros específicos do tribunal
        **kwargs,
    ) -> Path:
        """Baixa arquivos brutos da jurisprudência do {SIGLA}.

        Parameters
        ----------
        pesquisa : str
            Termo de busca.
        paginas : int, list, range, or None
            Páginas a baixar (1-based).
        diretorio : str
            Pasta para salvar os arquivos.

        Returns
        -------
        Path
            Caminho da pasta com os arquivos baixados.
        """
        self._init_session()

        # Normalizar parâmetros
        params = normalize_params(
            pesquisa=pesquisa, paginas=paginas, **kwargs
        )
        paginas_range = params.pop("paginas_range")

        # Criar pasta de saída
        pasta = Path(diretorio) / f"cjsg_{SIGLA_LOWER}"
        pasta.mkdir(parents=True, exist_ok=True)

        for pagina in tqdm(paginas_range, desc="Baixando páginas"):
            try:
                response = self._fetch_page(
                    pesquisa, pagina, **params
                )
                response.raise_for_status()

                # Salvar arquivo bruto
                arquivo = pasta / f"pagina_{pagina:04d}.html"
                arquivo.write_text(
                    response.text, encoding="utf-8"
                )

            except requests.RequestException as e:
                logger.warning(
                    "Erro na página %d: %s. Tentando novamente...",
                    pagina, e,
                )
                # Retry com backoff
                for tentativa in range(1, 4):
                    time.sleep(tentativa * 2)
                    try:
                        response = self._fetch_page(
                            pesquisa, pagina, **params
                        )
                        response.raise_for_status()
                        arquivo = pasta / f"pagina_{pagina:04d}.html"
                        arquivo.write_text(
                            response.text, encoding="utf-8"
                        )
                        break
                    except requests.RequestException:
                        if tentativa == 3:
                            logger.error(
                                "Falha definitiva na página %d",
                                pagina,
                            )
                            raise

            time.sleep(1)  # Rate limiting

        return pasta

    def _fetch_page(
        self, pesquisa: str, pagina: int, **kwargs
    ) -> requests.Response:
        """Faz a requisição para uma página específica.

        TODO: Implementar conforme engenharia reversa do site.
        """
        # TODO: Adaptar método (GET/POST), endpoint, e parâmetros
        # Exemplo para POST com form data:
        data = {
            # "pesquisaLivre": pesquisa,
            # "pagina": pagina,
            # TODO: mapear parâmetros reais
        }

        response = self.session.post(
            self.SEARCH_URL,
            data=data,
        )
        response.encoding = response.apparent_encoding
        return response

    def cjsg_parse(
        self, diretorio: Union[str, Path]
    ) -> pd.DataFrame:
        """Lê e processa arquivos brutos de cjsg_download.

        Parameters
        ----------
        diretorio : str or Path
            Pasta com os arquivos brutos.

        Returns
        -------
        pd.DataFrame
            Tabela com resultados processados.
        """
        pasta = Path(diretorio)
        arquivos = sorted(pasta.glob("pagina_*.html"))

        if not arquivos:
            logger.warning("Nenhum arquivo encontrado em %s", pasta)
            return pd.DataFrame()

        resultados = []
        for arquivo in arquivos:
            html = arquivo.read_text(encoding="utf-8")
            registros = self._parse_page(html)
            resultados.extend(registros)

        if not resultados:
            return pd.DataFrame()

        return pd.DataFrame(resultados)

    def _parse_page(self, html: str) -> list[dict]:
        """Extrai registros de uma página HTML.

        TODO: Implementar conforme estrutura do HTML do tribunal.
        """
        soup = BeautifulSoup(html, "lxml")
        registros = []

        # TODO: Adaptar seletores CSS conforme o HTML real
        # Exemplo:
        # for item in soup.select(".resultado-item"):
        #     registro = {
        #         "ementa": item.select_one(".ementa").get_text(strip=True),
        #         "relator": item.select_one(".relator").get_text(strip=True),
        #         "data_julgamento": item.select_one(".data").get_text(strip=True),
        #         "numero_processo": item.select_one(".processo").get_text(strip=True),
        #     }
        #     registros.append(registro)

        return registros
