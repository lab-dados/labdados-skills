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

    # TODO: perfil declarado em ``perfis_http`` do raspador; perfil inexistente
    # levanta ValueError (em cpopg, por exemplo, não é "cjsg").
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

Os raspadores antigos usam `import txtcaptcha` dentro da função e passam no lint por dispensa herdada em `ruff.toml`; arquivo novo não tem dispensa (`CONTRIBUTING.md` > "Política de lint e adoção gradual" > "Alcance das dispensas"). O `import_module` passa no ruff, mas na prática faz o papel de um `# noqa: PLC0415`, e a política de `# noqa` está em discussão no juscraper ([jtrecenti/juscraper#401](https://github.com/jtrecenti/juscraper/issues/401)). Declare a escolha no PR para o mantenedor decidir entre ela e o `noqa`. O fake em `sys.modules` dos testes vale nos dois casos, porque `import_module` olha ali primeiro.

A nova tentativa quando o backend recusa o texto fica em volta desta função, no download: detectar a resposta de "captcha inválido", chamar `resolver_captcha` de novo até o limite `max_captcha_attempts` e registrar cada falha com `logger.warning`.

## Teste com o `txtcaptcha` mockado

```python
"""Contrato do captcha do {SIGLA}: txtcaptcha mockado, nunca invocado."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests
import responses

from juscraper.courts.{tribunal}.download import CAPTCHA_URL, resolver_captcha

IMAGEM = b"\x89PNG fake"


@responses.activate(assert_all_requests_are_fired=True)
def test_resolver_captcha_le_a_imagem_da_sessao(mocker):
    lidos = []

    def decrypt(caminhos, **_kwargs):
        # O fake lê o arquivo recebido: pega imagem vazia, bytes no lugar de
        # caminho e arquivo apagado cedo demais.
        lidos.append(Path(caminhos[0]).read_bytes())
        return ["12345"]

    fake = MagicMock()
    fake.decrypt = MagicMock(side_effect=decrypt)
    mocker.patch.dict(sys.modules, {"txtcaptcha": fake})
    responses.add(responses.GET, CAPTCHA_URL, body=IMAGEM, status=200)

    sessao = requests.Session()

    def via_sessao(metodo, url, **kwargs):
        kwargs.pop("perfil", None)
        return sessao.request(metodo, url, **kwargs)

    # Spy no request_fn: a imagem tem de vir pela sessão do raspador, que
    # carrega o cookie amarrado ao captcha, e não de um requests.get solto.
    request_fn = MagicMock(side_effect=via_sessao)

    assert resolver_captcha(request_fn) == "12345"
    assert request_fn.call_args.args[:2] == ("GET", CAPTCHA_URL)
    assert lidos == [IMAGEM]
    assert not Path(fake.decrypt.call_args.args[0][0]).exists()


def test_resolver_captcha_sem_txtcaptcha(mocker):
    mocker.patch.dict(sys.modules, {"txtcaptcha": None})
    with pytest.raises(ImportError, match="txtcaptcha"):
        resolver_captcha(MagicMock())
```

No contrato do método público, a fixture com o fake fica em `tests/<xx>/conftest.py`, como `mock_txtcaptcha` em `tests/tjmg/conftest.py`, e a sequência imagem, validação e busca é registrada com `responses.registries.OrderedRegistry`.
