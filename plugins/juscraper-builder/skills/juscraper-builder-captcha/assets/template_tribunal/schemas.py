"""Schemas pydantic dos endpoints do TJXX.

Template da skill juscraper-builder. Troque ``TJXX``/``tjxx`` pela sigla real.
Um par Input/Output por endpoint implementado. Registrar os dois em
``tests/schemas/test_schema_coverage.py::EXPECTED_COURT_SCHEMAS`` e
``tests/schemas/test_output_parity.py::EXPECTED_COURT_OUTPUT_SCHEMAS``.
"""
from __future__ import annotations

from typing import ClassVar

from juscraper.schemas import (
    DataJulgamentoMixin,
    DataPublicacaoMixin,
    OutputCJSGBase,
    OutputDataPublicacaoMixin,
    OutputRelatoriaMixin,
    SearchBase,
)


class InputCJSGTJXX(SearchBase, DataJulgamentoMixin, DataPublicacaoMixin):
    """Entrada aceita por :meth:`TJXXScraper.cjsg` e :meth:`TJXXScraper.cjsg_download`.

    ``pesquisa`` e ``paginas`` vêm de :class:`SearchBase` (não redeclarar
    ``paginas``), que também fixa ``extra="forbid"``: kwarg desconhecido vira
    ``TypeError`` via ``raise_on_extra_kwargs``. Herde só os mixins de data
    que o backend aceita de fato; os demais ficam rejeitados pelo ``forbid``.
    """

    # Formato que o backend espera. A entrada do usuário aceita as quatro
    # variações de data e ``datetime.date``; o pipeline converte para este formato.
    BACKEND_DATE_FORMAT: ClassVar[str] = "%d/%m/%Y"  # TODO: "%Y-%m-%d" se o backend for ISO

    # TODO: um campo por filtro do formulário, com o nome canônico
    # (``relator``, ``classe``, ``assunto``, ``numero_processo``), e cada
    # campo igual, byte a byte, a um parâmetro da assinatura pública.
    relator: str | None = None
    classe: str | None = None


class OutputCJSGTJXX(OutputCJSGBase, OutputRelatoriaMixin, OutputDataPublicacaoMixin):
    """Colunas de uma linha do DataFrame de :meth:`TJXXScraper.cjsg`.

    ``processo``, ``ementa`` e ``data_julgamento`` vêm de :class:`OutputCJSGBase`;
    ``relator`` e ``orgao_julgador`` de :class:`OutputRelatoriaMixin`. Declarar
    aqui só os campos que o parser de fato entrega, todos opcionais.
    """

    classe: str | None = None
