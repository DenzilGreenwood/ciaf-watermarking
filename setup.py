"""
CIAF Watermarks - Setup Configuration

Forensic provenance and watermark verification for AI-generated artifacts.

This setup.py exists for backward compatibility with older pip versions.
The package is primarily configured using pyproject.toml (PEP 517/518).

For modern pip (>= 21.3), pyproject.toml is sufficient.
This file enables editable installs: pip install -e .

Installation:
    pip install .                    # Standard installation
    pip install -e .                 # Editable/development installation
    pip install .[images,pdf,video]  # With optional dependencies
    pip install .[full]              # All features
    pip install .[dev]               # Development tools

Created: 2026-04-06
Author: Denzil James Greenwood
Version: 1.4.0
"""

from setuptools import setup
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read schema documentation as additional context
schema_file = Path(__file__).parent / "SCHEMA.md"
if schema_file.exists():
    long_description += "\n\n## Schema Documentation\n\n"
    long_description += "See SCHEMA.md in the package for complete data model specification."

if __name__ == "__main__":
    setup(
        # Minimal configuration - most settings in pyproject.toml
        long_description=long_description,
        long_description_content_type="text/markdown",
        # Include package data
        include_package_data=True,
        # Zip safe
        zip_safe=False,
        # Python version requirement
        python_requires=">=3.8",
    )
