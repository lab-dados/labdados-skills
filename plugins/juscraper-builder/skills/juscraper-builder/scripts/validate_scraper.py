#!/usr/bin/env python3
"""Valida que um scraper gerado segue as convenções do juscraper.

Uso:
    python validate_scraper.py <tribunal>

Exemplo:
    python validate_scraper.py tjmg

Roda a partir do diretório raiz do juscraper.
"""

import ast
import re
import sys
from pathlib import Path


FAMILY_BASES = {"EsajSearchScraper", "TRFConsultaScraper"}
ALLOWED_BASES = {"HTTPScraper"} | FAMILY_BASES


def _package_sources(tribunal: str) -> dict[Path, str]:
    """Lê todos os módulos .py do pacote do tribunal."""
    base = Path(f"src/juscraper/courts/{tribunal}")
    return {f: f.read_text() for f in sorted(base.glob("*.py"))}


def check_file_structure(tribunal: str) -> list[str]:
    """Verifica se os arquivos necessários existem."""
    errors = []
    base = Path(f"src/juscraper/courts/{tribunal}")

    if not base.exists():
        errors.append(f"Diretório não existe: {base}")
        return errors

    if not (base / "__init__.py").exists():
        errors.append(f"Falta: {base / '__init__.py'}")

    if not (base / "client.py").exists():
        errors.append(f"Falta: {base / 'client.py'}")

    tests_dir = Path(f"tests/{tribunal}")
    if not tests_dir.exists():
        errors.append(f"Diretório de testes não existe: {tests_dir}")
    elif not (tests_dir / "__init__.py").exists():
        errors.append(f"Falta: {tests_dir / '__init__.py'}")

    return errors


def check_class_conventions(tribunal: str) -> list[str]:
    """Verifica convenções da classe scraper e do pacote do tribunal."""
    errors = []
    client_path = Path(f"src/juscraper/courts/{tribunal}/client.py")

    if not client_path.exists():
        return [f"Arquivo não encontrado: {client_path}"]

    tree = ast.parse(client_path.read_text())

    # Encontrar a classe Scraper
    classes = [
        node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    ]

    if not classes:
        errors.append("Nenhuma classe encontrada em client.py")
        return errors

    scraper_class = None
    sigla = tribunal.upper()
    expected_name = f"{sigla}Scraper"

    for cls in classes:
        if cls.name == expected_name:
            scraper_class = cls
            break

    if scraper_class is None:
        found = [c.name for c in classes]
        errors.append(
            f"Classe {expected_name} não encontrada. "
            f"Encontradas: {found}"
        )
        return errors

    # Verificar a classe base: HTTPScraper cria a Session, monta o
    # User-Agent e oferece _request_with_retry; as famílias herdam dele.
    bases = {
        b.id if isinstance(b, ast.Name) else getattr(b, "attr", "")
        for b in scraper_class.bases
    }
    if not bases & ALLOWED_BASES:
        errors.append(
            f"{expected_name} herda de {sorted(bases) or 'object'}. "
            "Herde de juscraper.core.http.HTTPScraper (ou de "
            "EsajSearchScraper/TRFConsultaScraper, se for da família)."
        )
    familia = bool(bases & FAMILY_BASES)

    sources = _package_sources(tribunal)

    for path, source in sources.items():
        module = ast.parse(source)
        # Imports de módulo proibidos; import lazy dentro de função (ex.:
        # Playwright opcional só para token de WAF) não entra aqui.
        top_imports = set()
        for node in module.body:
            if isinstance(node, ast.Import):
                top_imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_imports.add(node.module.split(".")[0])
        found_bad = {"selenium", "playwright"} & top_imports
        if found_bad:
            errors.append(
                f"{path.name}: imports proibidos no topo do módulo: {found_bad}. "
                "Use requests ao invés de browser automation."
            )

        # User-Agent fixo do juscraper: o HTTPScraper já monta com a versão.
        if "juscraper/0." in source:
            errors.append(
                f"{path.name}: User-Agent do juscraper fixado no código. "
                "Remova; o HTTPScraper monta o header com __version__."
            )

        # Verificar linhas longas
        for i, line in enumerate(source.split("\n"), 1):
            if len(line) > 120:
                errors.append(f"{path.name}: linha {i} tem {len(line)} chars (max 120)")
                break  # Só reportar a primeira

    # Subclasse de família herda download, pausa e barra de progresso.
    if not familia:
        todo_codigo = "\n".join(sources.values())
        if "time.sleep" not in todo_codigo:
            errors.append(
                "Não encontrei time.sleep() no pacote. "
                "Inclua a pausa entre páginas (sleep_time)."
            )
        if "tqdm" not in todo_codigo:
            errors.append(
                "Não encontrei tqdm no pacote. "
                "Inclua barra de progresso no download."
            )
        if "_request_with_retry" not in todo_codigo:
            errors.append(
                "Não encontrei self._request_with_retry. "
                "Faça as requisições por ele (retry com backoff)."
            )

    return errors


def check_factory_registration(tribunal: str) -> list[str]:
    """Verifica se o tribunal está registrado em _SCRAPERS."""
    errors = []

    init_path = Path("src/juscraper/__init__.py")
    if not init_path.exists():
        errors.append("src/juscraper/__init__.py não encontrado")
        return errors

    source = init_path.read_text()
    if not re.search(rf'["\']{re.escape(tribunal)}["\']\s*:', source):
        errors.append(
            f"Tribunal '{tribunal}' não encontrado em _SCRAPERS de "
            f"src/juscraper/__init__.py. Acrescente "
            f'"{tribunal}": "juscraper.courts.{tribunal}.client:{tribunal.upper()}Scraper".'
        )

    return errors


def check_tests(tribunal: str) -> list[str]:
    """Verifica contratos offline, samples, captura e registro de schemas."""
    errors = []
    tests_dir = Path(f"tests/{tribunal}")

    if not tests_dir.exists():
        return [f"Diretório de testes não existe: {tests_dir}"]

    contratos = sorted(tests_dir.glob("test_*_contract.py"))
    if not contratos:
        errors.append(
            f"Nenhum test_*_contract.py em {tests_dir}. "
            "Contrato offline por método público é obrigatório."
        )

    for tf in contratos:
        source = tf.read_text()
        if "pytest.mark.integration" in source:
            errors.append(
                f"{tf.name}: contrato marcado como integration. "
                "Contratos rodam offline, sem esse marker."
            )

    if contratos and not any("responses" in tf.read_text() for tf in contratos):
        errors.append(
            "Nenhum contrato usa responses. "
            "Contratos servem os samples capturados via responses."
        )

    for tf in sorted(tests_dir.glob("test_*_integration.py")):
        if "pytest.mark.integration" not in tf.read_text():
            errors.append(
                f"{tf.name}: falta @pytest.mark.integration. "
                "Testes que acessam servidores reais devem ser marcados."
            )

    if not (tests_dir / "samples").exists():
        errors.append(f"Falta: {tests_dir / 'samples'} (samples capturados)")

    capture = Path(f"tests/fixtures/capture/{tribunal}.py")
    if not capture.exists():
        errors.append(f"Falta: {capture} (script de captura dos samples)")

    for registro in (
        Path("tests/schemas/test_schema_coverage.py"),
        Path("tests/schemas/test_output_parity.py"),
    ):
        if registro.exists() and f'("{tribunal}",' not in registro.read_text():
            errors.append(
                f"Tribunal '{tribunal}' não registrado em {registro}."
            )

    return errors


def main():
    if len(sys.argv) < 2:
        print("Uso: python validate_scraper.py <tribunal>")
        print("Exemplo: python validate_scraper.py tjmg")
        sys.exit(1)

    tribunal = sys.argv[1].lower()

    print(f"Validando scraper para: {tribunal.upper()}")
    print("=" * 50)

    all_errors = []

    print("\n1. Estrutura de arquivos...")
    errs = check_file_structure(tribunal)
    all_errors.extend(errs)
    print(f"   {'✓ OK' if not errs else f'✗ {len(errs)} problema(s)'}")
    for e in errs:
        print(f"   - {e}")

    print("\n2. Convenções da classe...")
    errs = check_class_conventions(tribunal)
    all_errors.extend(errs)
    print(f"   {'✓ OK' if not errs else f'✗ {len(errs)} problema(s)'}")
    for e in errs:
        print(f"   - {e}")

    print("\n3. Registro na factory...")
    errs = check_factory_registration(tribunal)
    all_errors.extend(errs)
    print(f"   {'✓ OK' if not errs else f'✗ {len(errs)} problema(s)'}")
    for e in errs:
        print(f"   - {e}")

    print("\n4. Testes e schemas...")
    errs = check_tests(tribunal)
    all_errors.extend(errs)
    print(f"   {'✓ OK' if not errs else f'✗ {len(errs)} problema(s)'}")
    for e in errs:
        print(f"   - {e}")

    print("\n" + "=" * 50)
    if all_errors:
        print(f"RESULTADO: {len(all_errors)} problema(s) encontrado(s)")
        sys.exit(1)
    else:
        print("RESULTADO: ✓ Tudo OK!")
        sys.exit(0)


if __name__ == "__main__":
    main()
