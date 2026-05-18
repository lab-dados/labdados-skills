# Registro da factory em `src/raspe/__init__.py`

Após criar `src/raspe/scrapers/<fonte>.py`, registre a factory pública
em `src/raspe/__init__.py`. **Leia o arquivo antes de editar** — a ordem
e estilo das entradas têm padrão a manter.

## Padrão atual (resumido)

O arquivo tem três blocos:

1. **Imports** (no topo): scrapers HTTP importados diretamente. Scrapers
   Playwright **não** são importados aqui — eles têm import lazy dentro
   da factory para não quebrar quando `[browser]` não está instalado.

2. **Factories públicas**: uma função por fonte com docstring.

3. **`__all__`**: lista categorizada (Scrapers HTTP, Scrapers Browser,
   Utilitários, Exceções).

## Para fontes HTTP (HTML ou JSON)

### Passo 1 — Import no topo

```python
from .scrapers.{fonte} import Scraper{Fonte}
```

Mantenha ordem alfabética dentro do grupo. Veja como `presidencia`,
`ipea`, `senado`, etc. estão organizados.

### Passo 2 — Função factory

```python
def {fonte}(**kwargs):
    """
    Cria um raspador para {descrição da fonte}.

    Args:
        pesquisa: Termo de busca.
        {outros parâmetros específicos}: ...

    Returns:
        Scraper{Fonte}: Instância configurada do raspador.
    """
    return Scraper{Fonte}(**kwargs)
```

Espelhe o estilo de docstring de `presidencia()` ou `ipea()` (curto e
direto). Se a fonte exige API key (estilo NYT), receba `api_key` como
parâmetro nomeado:

```python
def {fonte}(api_key: str | None = None, **kwargs):
    """..."""
    return Scraper{Fonte}(api_key=api_key, **kwargs)
```

### Passo 3 — `__all__`

Adicionar `"{fonte}"` na seção `# Scrapers HTTP` da lista `__all__`.

## Para fontes Playwright

### Passo 1 — **NÃO** importar no topo

O extra `[browser]` é opcional. Importar `Scraper{Fonte}` no topo faria
`import raspe` falhar quando Playwright não está instalado. Em vez disso,
o import vive dentro da factory.

### Passo 2 — Função factory com import lazy

Modelo: `saudelegis()`, `ans()`, `anvisa()`.

```python
def {fonte}(**kwargs):
    """
    Cria um raspador para {descrição}.

    Este scraper usa Playwright para automação de navegador.
    Requer instalação das dependências: pip install raspe[browser]

    Args:
        termo: Termo de busca.
        headless: Se True, executa em modo headless (default: True).
        debug: Se True, mantém arquivos baixados (default: True).

    Returns:
        Scraper{Fonte}: Instância configurada do raspador.

    Raises:
        DriverNotInstalledError: Se Playwright não estiver instalado.

    Exemplo:
        >>> import raspe
        >>> df = raspe.{fonte}().raspar(termo="X")
    """
    from .scrapers.{fonte} import Scraper{Fonte}
    return Scraper{Fonte}(**kwargs)
```

A docstring obrigatoriamente menciona:
- Que usa Playwright.
- O comando `pip install raspe[browser]`.
- `DriverNotInstalledError` em `Raises:`.
- Exemplo `>>> df = raspe.{fonte}()...`.

### Passo 3 — `__all__`

Adicionar `"{fonte}"` na seção `# Scrapers Browser (Playwright)` da
lista `__all__`.

## Exemplo completo de PR no `__init__.py`

Diff conceitual ao adicionar uma fonte HTTP nova chamada `tesouro`:

```python
# Topo do arquivo, após os imports existentes
from .scrapers.tesouro import ScraperTesouro

# Após a última factory existente (mantenha ordem alfabética se possível)
def tesouro(**kwargs):
    """
    Cria um raspador para o Tesouro Nacional.

    Args:
        pesquisa: Termo de busca.

    Returns:
        ScraperTesouro: Instância configurada do raspador.
    """
    return ScraperTesouro(**kwargs)

# Na lista __all__, dentro da seção HTTP:
__all__ = [
    # Scrapers HTTP
    "presidencia",
    "ipea",
    ...
    "tesouro",        # ← nova entrada
    # Scrapers Browser (Playwright)
    "saudelegis",
    ...
]
```

## Validação

Depois de editar, valide:

```bash
cd /home/brunodcdo/Desktop/dev/raspe
python -c "import raspe; print(raspe.{fonte})"
python -c "import raspe; assert '{fonte}' in raspe.__all__"
```

Se o segundo falhar, você esqueceu a entrada em `__all__`.

Para Playwright, valide adicionalmente que importar `raspe` **sem**
`[browser]` ainda funciona:

```bash
python -c "import raspe; raspe.{fonte}"  # acessar a função (não chama)
# Deve passar sem ImportError, mesmo sem playwright instalado.

python -c "raspe.{fonte}()"  # tentar instanciar
# Aqui deve levantar DriverNotInstalledError se não tiver playwright.
```

## Cuidados

- **Nunca remova entradas existentes** ao adicionar a nova — `__all__` é
  contrato público.
- Ordem dentro de cada categoria não é estritamente alfabética hoje,
  mas tente manter algo razoável.
- Se você criar um alias retrocompatível (renomeou uma fonte), mantenha
  o nome antigo apontando para a mesma classe — veja `SeleniumError`
  em `exceptions.py` como referência.
