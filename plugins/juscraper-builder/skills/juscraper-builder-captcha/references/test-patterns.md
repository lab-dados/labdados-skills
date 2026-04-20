# Padrões de Testes de Integração

Referência para gerar testes de integração reais (sem mock) para
scrapers do juscraper.

## Princípios

1. **Sem mock**: Testes fazem requisições reais ao site do tribunal
2. **Marcados como integration**: `@pytest.mark.integration`
3. **Idempotentes**: Não dependem de estado anterior
4. **Resistentes a variações**: Não assumem contagem exata de
   resultados (usar `assert len(df) > 0`, não `assert len(df) == 47`)
5. **Rápidos dentro do possível**: Testar com 1-2 páginas, não todas

## Estrutura de arquivo

```
tests/{tribunal}/
├── __init__.py                    # OBRIGATÓRIO (vazio)
├── test_{tribunal}_cjsg.py        # Testes de jurisprudência
├── test_{tribunal}_cpopg.py       # Testes de processos 1º grau
└── test_{tribunal}_cposg.py       # Testes de processos 2º grau
```

## Template de teste para cjsg

```python
"""Testes de integração para cjsg do {SIGLA}."""

import pandas as pd
import pytest

import juscraper as jus


@pytest.mark.integration
class TestCJSG{SIGLA}:
    """Testes de integração para consulta de jurisprudência."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Inicializa o scraper."""
        self.scraper = jus.scraper("{tribunal}")

    def test_busca_simples(self):
        """Busca genérica retorna DataFrame não-vazio."""
        df = self.scraper.cjsg("direito", paginas=1)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_colunas_esperadas(self):
        """Resultado contém colunas mínimas do tribunal."""
        df = self.scraper.cjsg("direito", paginas=1)
        # ADAPTAR: verificar quais colunas o tribunal retorna
        # Exemplos comuns: ementa, relator, orgao_julgador,
        # data_julgamento, numero_processo
        assert len(df.columns) >= 3

    def test_paginacao_multiplas_paginas(self):
        """Duas páginas retornam mais resultados que uma."""
        df1 = self.scraper.cjsg("dano moral", paginas=1)
        df2 = self.scraper.cjsg("dano moral", paginas=range(1, 3))
        assert len(df2) > len(df1)

    def test_paginas_distintas(self):
        """Página 2 tem conteúdo diferente da página 1."""
        df1 = self.scraper.cjsg("dano moral", paginas=range(1, 2))
        df2 = self.scraper.cjsg("dano moral", paginas=range(2, 3))
        # Se ambos têm coluna de ementa ou decisão, comparar
        if "ementa" in df1.columns and len(df1) > 0 and len(df2) > 0:
            assert df1["ementa"].iloc[0] != df2["ementa"].iloc[0]

    def test_filtro_data(self):
        """Filtro de data retorna resultados."""
        df = self.scraper.cjsg(
            "direito",
            data_inicio="2024-01-01",
            data_fim="2024-06-30",
            paginas=1,
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_download_cria_arquivos(self, tmp_path):
        """cjsg_download cria arquivos no diretório."""
        pasta = self.scraper.cjsg_download(
            "direito", paginas=1, diretorio=str(tmp_path)
        )
        # Deve ter criado pelo menos 1 arquivo
        arquivos = list(Path(pasta).glob("*"))
        assert len(arquivos) > 0

    def test_parse_apos_download(self, tmp_path):
        """cjsg_parse lê corretamente arquivos do download."""
        pasta = self.scraper.cjsg_download(
            "direito", paginas=1, diretorio=str(tmp_path)
        )
        df = self.scraper.cjsg_parse(pasta)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_paginas_int_equivale_range(self):
        """paginas=2 é equivalente a range(1, 3)."""
        df_int = self.scraper.cjsg("direito", paginas=2)
        df_range = self.scraper.cjsg("direito", paginas=range(1, 3))
        assert len(df_int) == len(df_range)

    def test_pesquisa_sem_resultado(self):
        """Busca por termo inexistente retorna DataFrame vazio."""
        df = self.scraper.cjsg(
            "xyzzy_termo_inexistente_12345", paginas=1
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
```

## Template de teste para cpopg

```python
"""Testes de integração para cpopg do {SIGLA}."""

import pytest

import juscraper as jus


@pytest.mark.integration
class TestCPOPG{SIGLA}:
    """Testes de integração para consulta de processos 1º grau."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.scraper = jus.scraper("{tribunal}")

    def test_consulta_processo(self):
        """Consulta por número retorna dict com dados."""
        # ADAPTAR: usar um número de processo real e público
        resultado = self.scraper.cpopg("NNNNNNN-DD.AAAA.J.TT.OOOO")
        assert isinstance(resultado, dict)
        assert len(resultado) > 0

    def test_dados_basicos(self):
        """Resultado contém dados básicos do processo."""
        resultado = self.scraper.cpopg("NNNNNNN-DD.AAAA.J.TT.OOOO")
        # ADAPTAR: verificar chaves esperadas
        assert "dados_basicos" in resultado or "partes" in resultado

    def test_download_parse(self, tmp_path):
        """Download + parse produz mesmo resultado."""
        pasta = self.scraper.cpopg_download(
            "NNNNNNN-DD.AAAA.J.TT.OOOO", diretorio=str(tmp_path)
        )
        resultado = self.scraper.cpopg_parse(pasta)
        assert isinstance(resultado, dict)
        assert len(resultado) > 0
```

## Dicas

- Use termos de busca genéricos que garantidamente retornam
  resultados: "direito", "dano moral", "contrato"
- Para cpopg, use números de processos públicos e conhecidos
- Não teste contagens exatas — sites mudam seus dados
- Não confie que a ordem dos resultados será estável
- Use `tmp_path` fixture do pytest para diretórios temporários
- Cada classe de teste pode ter seu próprio `setup` via fixture
