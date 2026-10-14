"""Scraper para o Tribunal de Justiça de XX (TJXX).

Template da skill juscraper-builder, montado sobre o padrão dos scrapers
``HTTPScraper`` do juscraper. Troque ``TJXX``/``tjxx`` pela sigla real e
resolva os ``TODO`` antes de abrir o PR.

Divisão dos módulos:

* ``client.py``: API pública; valida a entrada e delega.
* ``download.py``: HTTP, paginação e ``build_cjsg_payload`` público.
* ``parse.py``: respostas brutas para DataFrame com colunas canônicas.
* ``schemas.py``: ``InputCJSGTJXX``/``OutputCJSGTJXX``, fonte única dos filtros.
"""
from collections.abc import Mapping
from typing import Any, ClassVar, cast

import pandas as pd

from juscraper.core.http import HTTPScraper, RequestPolicy
from juscraper.utils.params import apply_input_pipeline_search

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

    #: Timeout e tentativas da busca. O download passa ``perfil="cjsg"`` e o
    #: usuário ajusta com ``politica={"cjsg": {...}}`` no construtor. TODO:
    #: ``retry_on_timeout=True`` se o portal pendurar conexões.
    perfis_http: ClassVar[Mapping[str, RequestPolicy]] = {
        "cjsg": RequestPolicy(timeout=30),
    }

    def __init__(
        self,
        verbose: int = 0,
        download_path: str | None = None,
        sleep_time: float = 1.0,
        **kwargs: Any,
    ) -> None:
        """Cria a sessão HTTP do TJXX com a pausa ``sleep_time`` entre páginas."""
        super().__init__(
            "TJXX",
            verbose=verbose,
            download_path=download_path,
            sleep_time=sleep_time,
            **kwargs,
        )

    # O User-Agent padrão do HTTPScraper é o identificável ``juscraper/<versão>``.
    # Se a medição mostrar que o portal só responde a cabeçalhos de navegador,
    # a um adapter TLS ou a cookies iniciais, sobrescreva aqui o hook
    # ``_configure_session(self, session)`` e diga na docstring dele o que foi
    # medido, como fazem ``courts/_trf/base.py`` e ``courts/tjpr/client.py``.

    def cjsg(
        self,
        pesquisa: str | None = None,
        paginas: int | list | range | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Busca jurisprudência no TJXX.

        Baixa as páginas pedidas e devolve o resultado já processado.

        Args:
            pesquisa (str | None): Termo de busca livre.
            paginas (int | list | range | None): Páginas 1-based; ``None`` baixa
                todas. Default ``None``.
            **kwargs: Filtros aceitos por :class:`InputCJSGTJXX` (todos
                opcionais; ``None`` = sem filtro):

                * ``relator`` (str): Nome do relator, como o portal indexa.
                * ``classe`` (str): Classe processual.
                * ``data_julgamento_inicio`` / ``data_julgamento_fim`` (str):
                  Data de julgamento.
                * ``data_publicacao_inicio`` / ``data_publicacao_fim`` (str):
                  Data de publicação.

        Aliases deprecados (popados com ``DeprecationWarning`` antes do pydantic):
            * ``query`` / ``termo`` -> ``pesquisa``
            * ``data_inicio`` / ``data_fim`` -> ``data_julgamento_inicio`` / ``_fim``
            * ``data_julgamento_de`` / ``_ate`` -> ``data_julgamento_inicio`` / ``_fim``
            * ``data_publicacao_de`` / ``_ate`` -> ``data_publicacao_inicio`` / ``_fim``

        Raises:
            TypeError: Quando todos os erros são kwargs desconhecidos.
            ValidationError: Para os demais erros de validação do schema.
            ValueError: Quando um nome canônico e seu alias deprecado são
                passados juntos, ou quando o intervalo de datas é inválido.

        Returns:
            pd.DataFrame: Uma linha por decisão, com ``processo``, ``classe``,
            ``relator``, ``orgao_julgador``, ``data_julgamento``,
            ``data_publicacao`` e ``ementa``.

        Exemplo:
            >>> import juscraper as jus
            >>> tjxx = jus.scraper("tjxx")
            >>> df = tjxx.cjsg("dano moral", paginas=range(1, 3))

        See Also:
            :class:`InputCJSGTJXX`: fonte dos filtros aceitos.
        """
        return self.cjsg_parse(self.cjsg_download(pesquisa=pesquisa, paginas=paginas, **kwargs))

    def cjsg_download(
        self,
        pesquisa: str | None = None,
        paginas: int | list | range | None = None,
        **kwargs: Any,
    ) -> list:
        """Baixa as respostas brutas da busca de jurisprudência do TJXX.

        Aceita os mesmos filtros de :meth:`cjsg`; veja lá a lista completa.

        Returns:
            list: Uma resposta bruta por página baixada.
        """
        # O pipeline resolve os aliases deprecados, converte as datas para o
        # BACKEND_DATE_FORMAT e valida no pydantic, nessa ordem. Devolve
        # ``BaseModel``; o ``cast`` dá ao download o tipo concreto que o
        # builder lê.
        inp = cast(InputCJSGTJXX, apply_input_pipeline_search(
            InputCJSGTJXX,
            "TJXXScraper.cjsg_download()",
            pesquisa=pesquisa,
            paginas=paginas,
            kwargs=kwargs,
            consume_pesquisa_aliases=True,
        ))
        return cjsg_download_manager(
            inp,
            request_fn=self._request_with_retry,
            sleep_time=self.sleep_time,
        )

    def cjsg_parse(self, resultados_brutos: list) -> pd.DataFrame:
        """Processa as respostas brutas de :meth:`cjsg_download`.

        Args:
            resultados_brutos (list): Saída de :meth:`cjsg_download`.

        Returns:
            pd.DataFrame: Mesmo formato de :meth:`cjsg`.
        """
        return cjsg_parse_manager(resultados_brutos)
