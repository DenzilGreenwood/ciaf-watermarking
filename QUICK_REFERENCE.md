# Quick Reference: Common Packaging Commands

## Development

```bash
# Install in editable mode (for development)
pip install -e .

# Install with dev tools
pip install -e .[dev]

# Install everything for full testing
pip install -e .[full,dev]
```

## Testing

```bash
# Verify installation
python verify_install.py

# Run tests
pytest test_watermarks/ -v

# Run tests with coverage
pytest test_watermarks/ --cov=. --cov-report=html

# Run linters
flake8 .
ruff check .
```

## Building

```bash
# Install build tools (first time only)
pip install --upgrade build twine

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build distributions (source + wheel)
python -m build

# Check package is valid
twine check dist/*
```

## Publishing

```bash
# Test PyPI (recommended first)
twine upload --repository testpypi dist/*

# Production PyPI
twine upload dist/*
```

## Installation

```bash
# From PyPI (once published)
pip install ciaf-watermarks

# From source
pip install .

# From wheel file
pip install dist/ciaf_watermarks-1.4.0-py3-none-any.whl

# With extras
pip install ciaf-watermarks[images,pdf,video]
```

## Version Updates

```bash
# 1. Edit pyproject.toml version number
# 2. Commit changes
git add pyproject.toml
git commit -m "Bump version to 1.5.0"

# 3. Tag release
git tag -a v1.5.0 -m "Release version 1.5.0"

# 4. Push with tags
git push origin main --tags

# 5. Build and publish
python -m build
twine upload dist/*
```

## Cleanup

```bash
# Remove build artifacts
rm -rf dist/ build/ *.egg-info __pycache__ .pytest_cache .ruff_cache

# Uninstall package
pip uninstall ciaf-watermarks
```

## Import Examples

```python
# Core functionality
from ciaf_watermarks import (
    watermark_ai_output,
    detect_artifact_type,
    build_text_artifact_evidence,
    verify_text_artifact,
)

# Specific modules
from ciaf_watermarks.images import apply_visual_watermark
from ciaf_watermarks.video import build_video_artifact_evidence
from ciaf_watermarks.models import ArtifactEvidence, WatermarkDescriptor
```

## Troubleshooting

```bash
# Check if package is installed
pip list | grep ciaf

# Check import works
python -c "import ciaf_watermarks; print(ciaf_watermarks.__file__)"

# Reinstall from scratch
pip uninstall ciaf-watermarks -y
pip install -e .
python verify_install.py
```
