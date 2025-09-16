#!/usr/bin/env python3
"""Structure validation script for the cron user processor."""

from __future__ import annotations

import ast
import os
from typing import Iterable


def validate_file_structure() -> bool:
    """Validate presence of required files."""
    required_files = [
        "lambda_handler.py",
        "processor.py",
        "clients.py",
        "logging_config.py",
        "utils.py",
        "cloudflare_handler.py",
        "requirements.txt",
        "Dockerfile",
        "test_local.py",
        "config/__init__.py",
        "config/settings.py",
        "bs/__init__.py",
        "bs/scrape.py",
    ]

    print("📁 File Structure Validation")
    print("=" * 40)

    missing_files = []
    for path in required_files:
        if os.path.exists(path):
            print(f"✅ {path}")
        else:
            print(f"❌ {path} - MISSING")
            missing_files.append(path)

    return not missing_files


def validate_python_syntax(file_path: str) -> tuple[bool, str | None]:
    """Validate Python file has valid syntax."""
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        ast.parse(content)
        return True, None
    except SyntaxError as exc:
        return False, str(exc)
    except Exception as exc:  # pragma: no cover - defensive logging
        return False, f"Could not read file: {exc}"


def validate_syntax() -> bool:
    """Validate syntax of all core Python files."""
    python_files = [
        "lambda_handler.py",
        "processor.py",
        "clients.py",
        "logging_config.py",
        "utils.py",
        "cloudflare_handler.py",
        "test_local.py",
        "bs/scrape.py",
    ]

    print("🐍 Python Syntax Validation")
    print("=" * 40)

    all_valid = True
    for path in python_files:
        if os.path.exists(path):
            is_valid, error = validate_python_syntax(path)
            if is_valid:
                print(f"✅ {path}")
            else:
                print(f"❌ {path} - {error}")
                all_valid = False
        else:
            print(f"⚠️  {path} - File not found")
            all_valid = False
    return all_valid


def validate_contains(path: str, search_terms: Iterable[str]) -> bool:
    """Helper to verify required terms exist within a file."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        return all(term in content for term in search_terms)
    except OSError as exc:  # pragma: no cover - defensive logging
        print(f"❌ Error reading {path}: {exc}")
        return False


def validate_critical_structures() -> bool:
    """Check for critical classes and functions in key files."""
    print("🔧 Critical Structure Validation")
    print("=" * 40)

    checks = [
        ("lambda_handler.py", ["def lambda_handler"], "Lambda handler missing"),
        ("processor.py", ["class UserProcessor"], "UserProcessor class missing"),
        ("clients.py", ["class ApiClient", "def get_clients"], "API client helpers missing"),
        ("logging_config.py", ["def setup_logger"], "Logging helper missing"),
    ]

    all_valid = True
    for path, terms, message in checks:
        if not os.path.exists(path):
            print(f"⚠️  {path} - File not found")
            all_valid = False
            continue

        if validate_contains(path, terms):
            print(f"✅ {path} contains required definitions")
        else:
            print(f"❌ {path} - {message}")
            all_valid = False

    return all_valid


def validate_import_patterns() -> bool:
    """Check for corrected import patterns."""
    print("📦 Import Pattern Validation")
    print("=" * 40)

    path = "bs/scrape.py"
    if not os.path.exists(path):
        print(f"⚠️  {path} - File not found")
        return False

    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()

    if "from logging_config import setup_logger" in content:
        print("✅ bs/scrape.py uses shared logging helper")
        return True

    print("❌ bs/scrape.py logger import pattern incorrect")
    return False


def validate_requirements() -> bool:
    """Check requirements.txt lists mandatory dependencies."""
    print("📋 Requirements Validation")
    print("=" * 40)

    path = "requirements.txt"
    if not os.path.exists(path):
        print("❌ requirements.txt missing")
        return False

    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()

    required_deps = ["boto3", "beautifulsoup4", "requests", "python-dotenv", "urllib3"]
    missing = []
    for dep in required_deps:
        if dep in content:
            print(f"✅ {dep} found in requirements")
        else:
            print(f"❌ {dep} missing from requirements")
            missing.append(dep)

    return not missing


def main() -> None:
    """Run all validations."""
    print("🚀 Lambda User Processor Structure Validation")
    print("=" * 60)

    results = [
        ("File Structure", validate_file_structure()),
        ("Python Syntax", validate_syntax()),
        ("Critical Structures", validate_critical_structures()),
        ("Import Patterns", validate_import_patterns()),
        ("Requirements", validate_requirements()),
    ]

    print("📊 Validation Summary")
    print("=" * 40)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{name:<22}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("✅ All validations passed!")
    else:
        print("❌ Some validations failed. Please review the logs above.")


if __name__ == "__main__":
    main()
