# Esqueletos para captcha de imagem com `txtcaptcha`

Complementam o template da `juscraper-builder` (`../juscraper-builder/assets/template_tribunal/`). Os modelos reais são `courts/tjmg/download.py` e, só na lógica do captcha, `courts/trf6/download.py`; confira neles a forma atual antes de copiar.

## Função que resolve, em `download.py`

`txtcaptcha.decrypt` recebe uma lista de caminhos de arquivo e devolve uma lista de textos, então a imagem passa por um arquivo temporário. `mask` e `length` restringem a saída quando o formato é conhecido (TJMG: 5 dígitos); sem eles, texto livre (TRF6).

```python
import importlib
import tempfile
from pathlib import Path

from juscraper.core.http import RequestFn

CAPTCHA_URL = "https://www.tjxx.jus.br/captcha.png"  # TODO: endpoint real


def resolver_captcha(request_fn: RequestFn) -> str:
    """Baixa a imagem do captcha na sessão do raspador e devolve o texto lido.

    Raises:
        ImportError: Quando o pacote opcional ``txtcaptcha`` não está instalado.
    """
    try:
        # Lazy por import_module: a dependência é opcional, e o import dentro
        # da função cairia na regra PLC0415 do ruff, que arquivo novo não dispensa.
        txtcaptcha = importlib.import_module("txtcaptcha")
    except ImportError as exc:
        raise ImportError(
            "O TJXX precisa do pacote opcional `txtcaptcha` (`pip install txtcaptcha`)."
        ) from exc

    imagem = request_fn("GET", CAPTCHA_URL, perfil="cjsg").content
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as arquivo:
        arquivo.write(imagem)
        caminho = Path(arquivo.name)
    try:
        textos = txtcaptcha.decrypt([str(caminho)], mask="[0-9]", length=5)  # TODO: formato real
    finally:
        caminho.unlink(missing_ok=True)
    return str(textos[0])
```

Os raspadores antigos usam `import txtcaptcha` dentro da função e passam no lint por dispensa herdada em `ruff.toml`; arquivo novo não tem dispensa (`CONTRIBUTING.md` > "Política de lint e adoção gradual" > "Alcance das dispensas"), daí o `import_module`. O fake em `sys.modules` dos testes continua valendo, porque `import_module` olha ali primeiro.

A nova tentativa quando o backend recusa o texto fica em volta desta função, no download: detectar a resposta de "captcha inválido", chamar `resolver_captcha` de novo até o limite `max_captcha_attempts` e registrar cada falha com `logger.warning`.

## Teste com o `txtcaptcha` mockado

```python
"""Contrato do captcha do {SIGLA}: txtcaptcha mockado, nunca invocado."""
import sys
from unittest.mock import MagicMock

import requests
import responses

from juscraper.courts.{tribunal}.download import CAPTCHA_URL, resolver_captcha


@responses.activate
def test_resolver_captcha_usa_txtcaptcha(mocker):
    fake = MagicMock()
    fake.decrypt = MagicMock(return_value=["12345"])
    mocker.patch.dict(sys.modules, {"txtcaptcha": fake})
    responses.add(responses.GET, CAPTCHA_URL, body=b"\x89PNG fake", status=200)

    def request_fn(method, url, **kwargs):
        kwargs.pop("perfil", None)
        return requests.request(method, url, **kwargs)

    assert resolver_captcha(request_fn) == "12345"
    fake.decrypt.assert_called_once()
```

No contrato do método público, a fixture com o fake fica em `tests/<xx>/conftest.py`, como `mock_txtcaptcha` em `tests/tjmg/conftest.py`, e a sequência imagem, validação e busca é registrada com `responses.registries.OrderedRegistry`.
