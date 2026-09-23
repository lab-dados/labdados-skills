"""Parser das respostas brutas da busca de jurisprudência do TJXX.

Template da skill juscraper-builder. O parser renomeia as chaves do backend
para os nomes canônicos (``processo``, ``classe``, ``assunto``, ``relator``)
antes de montar o DataFrame; o Output schema reflete essas colunas.
"""
import pandas as pd

from juscraper.core.parse_utils import clean_html, coerce_date_columns


def cjsg_parse_manager(resultados_brutos: list) -> pd.DataFrame:
    """Converte as respostas brutas de ``cjsg_download_manager`` em DataFrame.

    Args:
        resultados_brutos (list): Uma resposta JSON por página.

    Returns:
        pd.DataFrame: Uma linha por decisão; vazio quando não há resultados.
    """
    registros = []
    for resposta in resultados_brutos:
        # TODO: caminho real até a lista de itens e nomes reais das chaves.
        for item in resposta.get("itens", []):
            registros.append({
                "processo": item.get("numeroProcesso"),
                "classe": item.get("classe"),
                "relator": item.get("relator"),
                "orgao_julgador": item.get("orgaoJulgador"),
                "data_julgamento": item.get("dataJulgamento"),
                "data_publicacao": item.get("dataPublicacao"),
                "ementa": clean_html(item.get("ementa")),
            })

    df = pd.DataFrame(registros)
    if df.empty:
        return df
    coerce_date_columns(df, ["data_julgamento", "data_publicacao"])
    return df
