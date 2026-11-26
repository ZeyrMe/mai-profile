#!/usr/bin/env python3
"""Run the same repository checks locally and in CI without rewriting source or example configuration."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_text_files():
    """Validate tracked text according to Git attributes, including checkout EOL."""
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    attributes = (
        subprocess.check_output(["git", "check-attr", "-z", "--stdin", "text", "eol"], input=paths, cwd=ROOT)
        .decode()
        .split("\0")
    )
    settings = {}
    for index in range(0, len(attributes) - 1, 3):
        path, attribute, value = attributes[index : index + 3]
        settings.setdefault(path, {})[attribute] = value
    errors = []
    for name, attrs in settings.items():
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or attrs["text"] == "unset":
            continue
        data = path.read_bytes()
        if attrs["text"] == "auto" and b"\0" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{name}: text must use UTF-8")
            continue
        if text.startswith("\ufeff"):
            errors.append(f"{name}: remove UTF-8 BOM")
        if attrs["eol"] == "crlf":
            if b"\n" in data.replace(b"\r\n", b"") or b"\r" in data.replace(b"\r\n", b""):
                errors.append(f"{name}: use CRLF line endings")
        elif b"\r" in data:
            errors.append(f"{name}: use LF line endings")
        if data and not data.endswith(b"\n"):
            errors.append(f"{name}: add a final newline")
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            errors.append(f"{name}: remove trailing whitespace")
    if errors:
        raise SystemExit("\n".join(errors))


def main():
    check_text_files()
    for args in (
        ["-m", "ruff", "check", "."],
        ["-m", "ruff", "format", "--check", "."],
        ["-m", "pytest", "-q", "--tb=short"],
    ):
        subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
