"""Testa o empacotamento das skills em zips para o upload no claude.ai, sem rede."""

import re
import zipfile
from pathlib import Path

import empacotar_skills

RAIZ = Path(__file__).resolve().parents[1]

TODAS = [p.name for p in empacotar_skills.skills(RAIZ)]
SKILLS = [s for s in TODAS if s not in empacotar_skills.SEM_ZIP]


def test_um_zip_por_skill_com_a_pasta_da_skill_no_topo(tmp_path):
    zips = empacotar_skills.empacotar(RAIZ, tmp_path)

    assert sorted(z.stem for z in zips) == SKILLS
    for caminho in zips:
        skill = caminho.stem
        with zipfile.ZipFile(caminho) as zf:
            nomes = zf.namelist()
        # O uploader do claude.ai espera <skill>/SKILL.md no primeiro nivel do zip.
        assert f"{skill}/SKILL.md" in nomes
        assert all(n.startswith(f"{skill}/") for n in nomes), nomes


def test_zip_leva_references_e_assets_e_deixa_lixo_local_de_fora(tmp_path):
    repo = tmp_path / "repo"
    skill = repo / "plugins" / "p" / "skills" / "s"
    (skill / "references").mkdir(parents=True)
    (skill / "__pycache__").mkdir()
    (skill / "SKILL.md").write_text("---\nname: s\n---\n")
    (skill / "references" / "a.md").write_text("a")
    (skill / "__pycache__" / "x.pyc").write_bytes(b"")
    (skill / ".DS_Store").write_bytes(b"")

    [caminho] = empacotar_skills.empacotar(repo, tmp_path / "dist")

    with zipfile.ZipFile(caminho) as zf:
        assert sorted(zf.namelist()) == ["s/SKILL.md", "s/references/a.md"]


def test_skill_com_zip_nao_le_outra_skill():
    # Zip leva so a pasta da skill: uma referencia a ../<outra-skill>/ quebraria no claude.ai.
    for pasta in empacotar_skills.skills(RAIZ):
        if pasta.name in empacotar_skills.SEM_ZIP:
            continue
        for arquivo in pasta.rglob("*"):
            if arquivo.is_file() and arquivo.suffix in {".md", ".py"}:
                texto = arquivo.read_text(encoding="utf-8")
                assert not [s for s in TODAS if f"../{s}/" in texto], arquivo


def test_skill_sem_zip_existe():
    # Entrada velha em SEM_ZIP (skill renomeada ou removida) esconderia uma skill nova do mesmo nome.
    assert set(empacotar_skills.SEM_ZIP) <= set(TODAS)


def test_readme_linka_exatamente_os_zips_gerados():
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    linkados = re.findall(r"releases/latest/download/([\w-]+)\.zip", readme)
    assert sorted(set(linkados)) == SKILLS
