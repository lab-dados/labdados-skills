#!/usr/bin/env python3
"""Valida que um scraper gerado segue as convenções do juscraper.

Uso:
    python validate_scraper.py <tribunal>

Exemplo:
    python validate_scraper.py tjmg

Roda a partir do diretório raiz do juscraper.
"""

import ast
import importlib
import sys
from pathlib import Path


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
    """Verifica convenções da classe scraper."""
    errors = []
    client_path = Path(f"src/juscraper/courts/{tribunal}/client.py")

    if not client_path.exists():
        return [f"Arquivo não encontrado: {client_path}"]

    source = client_path.read_text()
    tree = ast.parse(source)

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

    # Verificar métodos
    methods = {
        node.name
        for node in ast.walk(scraper_class)
        if isinstance(node, ast.FunctionDef)
    }

    if "__init__" not in methods:
        errors.append("Falta método __init__")

    # Verificar imports
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    if "requests" not in imports and "httpx" not in imports:
        errors.append(
            "Nem 'requests' nem 'httpx' importado. "
            "O código final deve usar requests, não Playwright/Selenium."
        )

    # Verificar se NÃO importa selenium/playwright
    bad_imports = {"selenium", "playwright"}
    found_bad = bad_imports & imports
    if found_bad:
        errors.append(
            f"Imports proibidos encontrados: {found_bad}. "
            f"Use requests ao invés de browser automation."
        )

    # Verificar se usa Session
    source_lower = source.lower()
    if "requests.session" not in source_lower:
        errors.append(
            "Não encontrei requests.Session(). "
            "Use Session para manter cookies."
        )

    # Verificar User-Agent
    if "user-agent" not in source_lower and "user_agent" not in source_lower:
        errors.append("Não encontrei User-Agent nos headers.")

    # Verificar sleep
    if "time.sleep" not in source:
        errors.append(
            "Não encontrei time.sleep(). "
            "Inclua delay entre requisições."
        )

    # Verificar tqdm
    if "tqdm" not in source:
        errors.append(
            "Não encontrei tqdm. "
            "Inclua barra de progresso no download."
        )

    # Verificar linhas longas
    for i, line in enumerate(source.split("\n"), 1):
        if len(line) > 120:
            errors.append(f"Linha {i} tem {len(line)} chars (max 120)")
            break  # Só reportar a primeira

    return errors


def check_factory_registration(tribunal: str) -> list[str]:
    """Verifica se o tribunal está registrado na factory."""
    errors = []

    init_path = Path("src/juscraper/__init__.py")
    if not init_path.exists():
        errors.append("src/juscraper/__init__.py não encontrado")
        return errors

    source = init_path.read_text()
    if tribunal not in source.lower():
        errors.append(
            f"Tribunal '{tribunal}' não encontrado em "
            f"src/juscraper/__init__.py. "
            f"Registre na factory function scraper()."
        )

    return errors


def check_tests(tribunal: str) -> list[str]:
    """Verifica convenções dos testes."""
    errors = []
    tests_dir = Path(f"tests/{tribunal}")

    if not tests_dir.exists():
        return [f"Diretório de testes não existe: {tests_dir}"]

    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        errors.append(f"Nenhum arquivo test_*.py em {tests_dir}")
        return errors

    for tf in test_files:
        source = tf.read_text()

        if "pytest.mark.integration" not in source:
            errors.append(
                f"{tf.name}: Falta @pytest.mark.integration. "
                f"Testes que acessam servidores reais devem ser marcados."
            )

        if "mock" in source.lower() or "Mock" in source:
            errors.append(
                f"{tf.name}: Encontrei 'mock' no código de testes. "
                f"Testes devem ser reais, sem mock."
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

    print("\n4. Testes de integração...")
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
