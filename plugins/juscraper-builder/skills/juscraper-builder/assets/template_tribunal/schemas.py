"""Schemas pydantic dos endpoints do TJXX.

Template da skill juscraper-builder. Troque ``TJXX``/``tjxx`` pela sigla real.
Um par Input/Output por endpoint implementado. Os registros que os testes de
``tests/schemas/`` exigem estão no CONTRIBUTING.md do juscraper, seção
"Schemas pydantic".
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

    # TODO: um campo por filtro do formulário confirmado com o usuário, com o
    # nome canônico (``relator``, ``classe``, ``assunto``, ``numero_processo``).
    # Cada campo aparece como bullet em ``**kwargs`` na docstring do método
    # público (tests/schemas/test_docstring_parity.py confere a igualdade).
    relator: str | None = None
    classe: str | None = None


class OutputCJSGTJXX(OutputCJSGBase, OutputRelatoriaMixin, OutputDataPublicacaoMixin):
    """Colunas de uma linha do DataFrame de :meth:`TJXXScraper.cjsg`.

    ``processo``, ``ementa`` e ``data_julgamento`` vêm de :class:`OutputCJSGBase`;
    ``relator`` e ``orgao_julgador`` de :class:`OutputRelatoriaMixin`. Declarar
    aqui só os campos que o parser de fato entrega, todos opcionais.
    """

    classe: str | None = None
