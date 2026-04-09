#!/usr/bin/env python3
"""Quick script to fix common flake8 issues."""

# import os
import re
from pathlib import Path


def fix_file(filepath):
    """Fix common linting issues in a Python file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Fix f-strings that don't need to be f-strings (F541)
    # Match f"..." or f'...' where there are no {braces}
    content = re.sub(
        r'f"([^"]*?)"',
        lambda m: f'"{m.group(1)}"' if "{" not in m.group(1) else m.group(0),
        content,
    )
    content = re.sub(
        r"f'([^']*?)'",
        lambda m: f"'{m.group(1)}'" if "{" not in m.group(1) else m.group(0),
        content,
    )

    # Remove unused ArtifactEvidence import if present
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        # Skip unused imports
        if (
            "from ciaf_watermarks.models import ArtifactEvidence" in line
            and "ArtifactEvidence" not in content.replace(line, "")
        ):
            continue
        if "from typing import Optional" in line and " Optional" not in content.replace(line, ""):
            continue
        if (
            "from concurrent.futures import ThreadPoolExecutor, as_completed" in line
            and "ThreadPoolExecutor" not in content.replace(line, "")
            and "as_completed" not in content.replace(line, "")
        ):
            continue
        if "from datetime import datetime" in line and line.strip().startswith(
            "from datetime import datetime"
        ):
            # Check if datetime is used (excluding the import itself)
            temp_content = content.replace(line, "")
            if "datetime" not in temp_content or (
                temp_content.count("datetime") <= 1 and "from datetime import" in temp_content
            ):
                continue

        new_lines.append(line)

    content = "\n".join(new_lines)

    # Fix bare except (E722) - change to except Exception
    content = re.sub(r"\bexcept\s*:\s*$", "except Exception:", content, flags=re.MULTILINE)

    # Ensure file ends with newline (W292)
    if content and not content.endswith("\n"):
        content += "\n"

    # Fix too many blank lines at start (E303)
    lines = content.split("\n")
    while len(lines) > 1 and lines[0] == "" and lines[1] == "" and lines[2] == "":
        lines.pop(0)
    content = "\n".join(lines)

    # Write back if changed
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False


def main():
    """Fix all Python files in examples directory."""
    examples_dir = Path("examples")

    fixed_count = 0
    for py_file in examples_dir.rglob("*.py"):
        if fix_file(py_file):
            fixed_count += 1

    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()
