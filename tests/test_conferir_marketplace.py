"""Testa o scripts/conferir_marketplace.py, que o validate.yml e o pre-commit rodam."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "conferir_marketplace.py"


def conferir(repo, fontes):
    (repo / ".claude-plugin").mkdir(parents=True)
    plugins = [{"name": Path(f).name, "source": f} for f in fontes]
    (repo / ".claude-plugin" / "marketplace.json").write_text(json.dumps({"plugins": plugins}))
    return subprocess.run([sys.executable, SCRIPT], cwd=repo, capture_output=True, text=True)


def test_repo_real_passa():
    r = subprocess.run([sys.executable, SCRIPT], cwd=SCRIPT.parents[1], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_source_com_skill_passa(tmp_path):
    skill = tmp_path / "plugins" / "p" / "skills" / "s"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: s\n---\n")

    assert conferir(tmp_path, ["./plugins/p"]).returncode == 0


def test_source_inexistente_reprova(tmp_path):
    r = conferir(tmp_path, ["./plugins/sumiu"])

    assert r.returncode == 1
    assert "source ./plugins/sumiu não existe" in r.stdout


def test_plugin_sem_skill_md_reprova(tmp_path):
    (tmp_path / "plugins" / "p" / "skills" / "s").mkdir(parents=True)
    r = conferir(tmp_path, ["./plugins/p"])

    assert r.returncode == 1
    assert "nenhum SKILL.md" in r.stdout
