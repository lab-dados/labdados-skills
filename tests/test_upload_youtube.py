"""Sem as bibliotecas do Google, o upload_youtube.py da explainer-video diz como instala-las:
com o uv no Python que roda o script, ou com o pip desse Python, sem `--break-system-packages`."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "plugins/explainer-video/skills/explainer-video/scripts/upload_youtube.py"


@pytest.mark.skipif(
    importlib.util.find_spec("googleapiclient") is not None,
    reason="o teste precisa de um Python sem as bibliotecas do Google (a suite do CI nao as tem)",
)
def test_sem_dependencias_sugere_uv_e_pip_no_python_do_script():
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--video", "v.mp4", "--title", "t"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2, r.stderr
    assert f'uv pip install --python "{sys.executable}" google-api-python-client' in r.stderr
    assert f'"{sys.executable}" -m pip install google-api-python-client' in r.stderr
    assert "--break-system-packages" not in r.stderr
