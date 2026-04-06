# Packaging and Distribution Guide

## Package Structure

This package is structured as a standard Python package with modern packaging practices:

```
ciaf-watermarking/
├── pyproject.toml          # Modern package configuration (PEP 517/518)
├── setup.py                # Backward compatibility
├── MANIFEST.in             # Non-Python files to include
├── requirements.txt        # Dependencies (alternative format)
├── README.md               # Package documentation
├── LICENSE                 # BUSL-1.1 license
├── SCHEMA.md               # Complete data model specification
│
├── *.py                    # Core modules (root level)
├── text/                   # Text watermarking subpackage
├── images/                 # Image watermarking subpackage
├── video/                  # Video watermarking subpackage
├── audio/                  # Audio watermarking subpackage
├── pdf/                    # PDF watermarking subpackage
├── binary/                 # Binary watermarking subpackage
├── gpu/                    # GPU acceleration subpackage
└── test_watermarks/        # Test suite (excluded from distribution)
```

## Installation Methods

### For Users

#### Basic Installation (PyPI - future)
```bash
pip install ciaf-watermarks
```

#### From Source
```bash
git clone https://github.com/DenzilGreenwood/pyciaf.git
cd pyciaf/ciaf-watermarking
pip install .
```

#### With Optional Dependencies
```bash
# Images and PDF support
pip install .[images,pdf]

# All features including video/audio
pip install .[full]

# Lightweight (text only)
pip install .
```

#### Using requirements.txt
```bash
pip install -r requirements.txt
```

### For Developers

#### Editable Installation
```bash
pip install -e .                # Minimal
pip install -e .[dev]           # With dev tools
pip install -e .[full,dev]      # Everything
```

#### Install with Development Tools
```bash
pip install -e .[dev]

# This includes:
# - pytest, pytest-cov, pytest-mock, pytest-asyncio
# - flake8, ruff, black, mypy
```

## Building Distribution Packages

### Prerequisites
```bash
pip install --upgrade build twine
```

### Build Source and Wheel Distributions
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build distributions
python -m build

# This creates:
# - dist/ciaf_watermarks-1.4.0.tar.gz (source)
# - dist/ciaf_watermarks-1.4.0-py3-none-any.whl (wheel)
```

### Verify Package Contents
```bash
# Check wheel contents
unzip -l dist/ciaf_watermarks-1.4.0-py3-none-any.whl

# Check source distribution
tar -tzf dist/ciaf_watermarks-1.4.0.tar.gz
```

### Test Installation Locally
```bash
# Create test virtual environment
python -m venv test_venv
source test_venv/bin/activate  # On Windows: test_venv\Scripts\activate

# Install from wheel
pip install dist/ciaf_watermarks-1.4.0-py3-none-any.whl

# Test import
python -c "from ciaf_watermarks import watermark_ai_output; print('Success!')"

# Deactivate and cleanup
deactivate
rm -rf test_venv
```

## Publishing to PyPI

### Test PyPI (Recommended First)
```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ ciaf-watermarks
```

### Production PyPI
```bash
# Upload to PyPI
twine upload dist/*

# Users can now install with:
pip install ciaf-watermarks
```

## Package Versioning

Version numbers follow Semantic Versioning (SemVer):
- **MAJOR.MINOR.PATCH** (e.g., 1.4.0)
- Increment MAJOR for breaking API changes
- Increment MINOR for new features (backward compatible)
- Increment PATCH for bug fixes

### Update Version

1. **Update pyproject.toml**:
   ```toml
   [project]
   version = "1.5.0"
   ```

2. **Update setup.py docstring** (if needed)

3. **Update version in code** (if you have a __version__ anywhere)

4. **Tag the release**:
   ```bash
   git tag -a v1.5.0 -m "Release version 1.5.0"
   git push origin v1.5.0
   ```

## Import Name vs Package Name

**Important:** The package has different names in different contexts:

- **PyPI/pip name**: `ciaf-watermarks` (with hyphen)
- **Import name**: `ciaf_watermarks` (with underscore)
- **Distribution name**: `ciaf_watermarks-1.4.0-py3-none-any.whl`

This is configured in `pyproject.toml`:
```toml
[project]
name = "ciaf-watermarks"  # PyPI name (kebab-case)

[tool.setuptools.package-dir]
ciaf_watermarks = "."      # Import name (snake_case)
```

Usage:
```bash
pip install ciaf-watermarks    # Install using PyPI name
```

```python
from ciaf_watermarks import watermark_ai_output  # Import using Python name
```

## Integration with Main CIAF Package

This standalone package can also be integrated into the main `pyciaf` package as a namespace submodule:

**Standalone**: 
```python
from ciaf_watermarks import watermark_ai_output
```

**Integrated in pyciaf**:
```python
from ciaf.watermarks import watermark_ai_output
```

## Testing Before Release

### Run Full Test Suite
```bash
pytest test_watermarks/ -v --cov=. --cov-report=html
```

### Run Linters
```bash
flake8 .
ruff check .
```

### Check Package Metadata
```bash
python -m build
twine check dist/*
```

## Continuous Integration

For automated testing and publishing, consider GitHub Actions:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI
on:
  release:
    types: [published]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
```

## Troubleshooting

### Package not found after installation
- Check if installed: `pip list | grep ciaf`
- Verify import name: `ciaf_watermarks` not `ciaf-watermarks`

### Missing dependencies
- Install optional dependencies: `pip install ciaf-watermarks[images,pdf]`

### Import errors with relative imports
- Ensure `__init__.py` files exist in all subpackages
- Check that package is installed (not just in PYTHONPATH)

### FFmpeg errors (video/audio)
- FFmpeg must be installed separately (not via pip)
- Download from: https://ffmpeg.org/download.html
- Add to system PATH

## License Considerations

This package uses **Business Source License 1.1 (BUSL-1.1)**:

- ✅ Free for non-production use
- ✅ Modify and create derivatives
- ✅ Redistribute with attribution
- ❌ Production use requires commercial license (before 2029-01-01)
- ✅ Converts to Apache 2.0 on January 1, 2029

When publishing to PyPI, ensure license is correctly specified:

```toml
[project]
license = {text = "BUSL-1.1"}

classifiers = [
    "License :: Other/Proprietary License",
]
```

## Additional Resources

- PEP 517 (Building): https://peps.python.org/pep-0517/
- PEP 518 (pyproject.toml): https://peps.python.org/pep-0518/
- PEP 621 (Project metadata): https://peps.python.org/pep-0621/
- Setuptools docs: https://setuptools.pypa.io/
- PyPI publishing guide: https://packaging.python.org/tutorials/packaging-projects/
