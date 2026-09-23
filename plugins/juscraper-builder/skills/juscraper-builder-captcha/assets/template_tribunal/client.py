"""Scraper para o Tribunal de Justiça de XX (TJXX).

Template da skill juscraper-builder, montado sobre o padrão dos scrapers
``HTTPScraper`` do juscraper (ex.: ``courts/tjro/``). Troque ``TJXX``/``tjxx``
pela sigla real e resolva os ``TODO`` antes de abrir o PR.

Divisão dos módulos:

* ``client.py``: API pública; valida a entrada e delega.
* ``download.py``: HTTP, paginação e ``build_cjsg_payload`` público.
* ``parse.py``: respostas brutas para DataFrame com colunas canônicas.
* ``schemas.py``: ``InputCJSGTJXX``/``OutputCJSGTJXX``, fonte única dos filtros.
"""
from typing import Any

import pandas as pd

from juscraper.core.http import HTTPScraper
from juscraper.utils.params import apply_input_pipeline_search, resolve_deprecated_alias

from .download import cjsg_download_manager
from .parse import cjsg_parse_manager
from .schemas import InputCJSGTJXX


class TJXXScraper(HTTPScraper):
    """Scraper para o Tribunal de Justiça de XX (TJXX).

    ``HTTPScraper`` cria ``self.session`` com o User-Agent do juscraper,
    guarda ``self.sleep_time`` e oferece ``self._request_with_retry`` (backoff
    exponencial para 403/429/5xx, respeitando ``Retry-After``).
    """

    BASE_URL = "https://www.tjxx.jus.br"  # TODO

    def __init__(
        self,
        verbose: int = 0,
        download_path: str | None = None,
        sleep_time: float = 1.0,
        **kwargs: Any,
    ):
        super().__init__(
            "TJXX",
            verbose=verbose,
            download_path=download_path,
            sleep_time=sleep_time,
            **kwargs,
        )

    # Descomente só se o site exigir: adapter TLS, cookies iniciais ou um
    # User-Agent de navegador no lugar do padrão do juscraper.
    # def _configure_session(self, session: requests.Session) -> None:
    #     session.headers.update({"User-Agent": "Mozilla/5.0 ..."})

    def cjsg(
        self,
        pesquisa: str | None = None,
        paginas: int | list | range | None = None,
        relator: str | None = None,
        classe: str | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Busca jurisprudência no TJXX.

        Baixa as páginas pedidas e devolve o resultado já processado.

        Args:
            pesquisa (str): Termo de busca livre.
            paginas (int | list | range | None): Páginas 1-based; ``None`` baixa
                todas. Default ``None``.
            relator (str | None): Nome do relator. Aceita o alias deprecado
                ``magistrado``.
            classe (str | None): Classe processual.
            **kwargs: Filtros aceitos pelo schema :class:`InputCJSGTJXX`.
                Listados abaixo (todos opcionais; ``None`` = sem filtro):

                * ``data_julgamento_inicio`` / ``data_julgamento_fim`` (str):
                  ``DD/MM/AAAA``.
                * ``data_publicacao_inicio`` / ``data_publicacao_fim`` (str):
                  ``DD/MM/AAAA``.

        Aliases deprecados (popados com ``DeprecationWarning`` antes do pydantic):
            * ``query`` / ``termo`` -> ``pesquisa``
            * ``magistrado`` -> ``relator``
            * ``data_inicio`` / ``data_fim`` -> ``data_julgamento_inicio`` / ``_fim``
            * ``data_julgamento_de`` / ``_ate`` -> ``data_julgamento_inicio`` / ``_fim``
            * ``data_publicacao_de`` / ``_ate`` -> ``data_publicacao_inicio`` / ``_fim``

        Raises:
            TypeError: Quando um kwarg desconhecido é passado.
            ValueError: Quando um nome canônico e seu alias deprecado são
                passados juntos, ou quando o intervalo de datas é inválido.
            ValidationError: Quando um filtro tem formato inválido.

        Returns:
            pd.DataFrame: Uma linha por decisão, com ``processo``, ``classe``,
            ``relator``, ``orgao_julgador``, ``data_julgamento``,
            ``data_publicacao`` e ``ementa``.

        Exemplo:
            >>> import juscraper as jus
            >>> tjxx = jus.scraper("tjxx")
            >>> df = tjxx.cjsg("dano moral", paginas=range(1, 3))

        See also:
            :class:`InputCJSGTJXX`: schema pydantic, fonte da verdade dos
            filtros aceitos.
        """
        return self.cjsg_parse(self.cjsg_download(
            pesquisa=pesquisa,
            paginas=paginas,
            relator=relator,
            classe=classe,
            **kwargs,
        ))

    def cjsg_download(
        self,
        pesquisa: str | None = None,
        paginas: int | list | range | None = None,
        relator: str | None = None,
        classe: str | None = None,
        **kwargs,
    ) -> list:
        """Baixa as respostas brutas da busca de jurisprudência do TJXX.

        Aceita os mesmos filtros de :meth:`cjsg`; veja lá a lista completa.

        Returns:
            list: Uma resposta bruta por página baixada.
        """
        # Aliases específicos do tribunal saem antes do pipeline; senão o
        # pydantic os rejeita como ``extra_forbidden``.
        relator = resolve_deprecated_alias(kwargs, "magistrado", "relator", relator)
        inp = apply_input_pipeline_search(
            InputCJSGTJXX,
            "TJXXScraper.cjsg_download()",
            pesquisa=pesquisa,
            paginas=paginas,
            kwargs=kwargs,
            consume_pesquisa_aliases=True,
            relator=relator,
            classe=classe,
        )
        return cjsg_download_manager(
            inp.pesquisa,
            inp.paginas,
            request_fn=self._request_with_retry,
            sleep_time=self.sleep_time,
            relator=inp.relator or "",
            classe=inp.classe or "",
            data_julgamento_inicio=inp.data_julgamento_inicio or "",
            data_julgamento_fim=inp.data_julgamento_fim or "",
            data_publicacao_inicio=inp.data_publicacao_inicio or "",
            data_publicacao_fim=inp.data_publicacao_fim or "",
        )

    def cjsg_parse(self, resultados_brutos: list) -> pd.DataFrame:
        """Processa as respostas brutas de :meth:`cjsg_download`.

        Args:
            resultados_brutos (list): Saída de :meth:`cjsg_download`.

        Returns:
            pd.DataFrame: Mesmo formato de :meth:`cjsg`.
        """
        return cjsg_parse_manager(resultados_brutos)
