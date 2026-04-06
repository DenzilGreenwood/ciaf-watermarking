# GitHub Actions Workflows

This directory contains CI/CD workflows for the CIAF Watermarks package.

## Workflows

### 1. `publish.yml` - PyPI Publishing

**Triggers:**
- On GitHub release publication
- Manual workflow dispatch

**Jobs:**
1. **Test** - Run full test suite across Python 3.8-3.12
2. **Build** - Build source and wheel distributions
3. **Publish to TestPyPI** - Publish to test repository (manual trigger only)
4. **Publish to PyPI** - Publish to production PyPI (on release)
5. **GitHub Release** - Sign packages and attach to release

**Requirements:**
- GitHub repository secrets configured (see below)
- Trusted publishing enabled on PyPI

**Usage:**
```bash
# Create a new release on GitHub
git tag -a v1.5.0 -m "Release version 1.5.0"
git push origin v1.5.0

# Or create release via GitHub UI
# The workflow will automatically publish to PyPI
```

### 2. `test.yml` - Continuous Testing

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**
1. **Test** - Run tests on multiple OS (Ubuntu, Windows, macOS) and Python versions
2. **Lint Only** - Run linters and type checking
3. **Build Test** - Test package build and installation
4. **Security Scan** - Run security vulnerability scans

**Coverage:**
- Uploads coverage reports to Codecov
- Generates coverage badges

### 3. `release-candidate.yml` - RC Testing

**Triggers:**
- Push tags matching `v*-rc*` (e.g., `v1.5.0-rc1`)

**Jobs:**
1. **Test** - Full test suite with all optional dependencies
2. **Build** - Build RC distributions
3. **Publish to TestPyPI** - Automatically publish RC to TestPyPI

**Usage:**
```bash
# Create release candidate
git tag -a v1.5.0-rc1 -m "Release candidate 1 for v1.5.0"
git push origin v1.5.0-rc1

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ ciaf-watermarks==1.5.0rc1
```

## Setup Instructions

### 1. PyPI Trusted Publishing (Recommended)

**For PyPI:**
1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher:
   - PyPI Project Name: `ciaf-watermarks`
   - Owner: `DenzilGreenwood`
   - Repository: `ciaf-watermarking`
   - Workflow: `publish.yml`
   - Environment: `pypi`

**For TestPyPI:**
1. Go to https://test.pypi.org/manage/account/publishing/
2. Add the same configuration but use environment: `testpypi`

### 2. GitHub Environment Setup

Create environments in your repository:

**Settings → Environments → New environment**

**Environment: `pypi`**
- Protection rules: Require reviewers (optional but recommended)
- Environment secrets: None needed (using trusted publishing)

**Environment: `testpypi`**
- No protection rules needed

### 3. Alternative: API Token Setup (Legacy)

If not using trusted publishing:

1. Generate PyPI API token at https://pypi.org/manage/account/token/
2. Add to GitHub Secrets: `Settings → Secrets → Actions → New repository secret`
   - Name: `PYPI_TOKEN`
   - Value: Your PyPI token

3. Modify `publish.yml` to use token:
   ```yaml
   - name: Publish to PyPI
     uses: pypa/gh-action-pypi-publish@release/v1
     with:
       password: ${{ secrets.PYPI_TOKEN }}
   ```

### 4. Codecov Integration (Optional)

1. Sign up at https://codecov.io
2. Add repository
3. Get upload token
4. Add to GitHub Secrets as `CODECOV_TOKEN`

## Release Process

### Standard Release

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG** (if you have one)
3. **Commit changes:**
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 1.5.0"
   git push origin main
   ```

4. **Create and push tag:**
   ```bash
   git tag -a v1.5.0 -m "Release version 1.5.0"
   git push origin v1.5.0
   ```

5. **Create GitHub Release:**
   - Go to repository → Releases → Draft a new release
   - Choose tag: `v1.5.0`
   - Generate release notes
   - Publish release

6. **Workflow automatically:**
   - Runs tests
   - Builds package
   - Publishes to PyPI
   - Signs artifacts
   - Uploads to GitHub Release

### Release Candidate Process

1. **Tag release candidate:**
   ```bash
   git tag -a v1.5.0-rc1 -m "Release candidate 1"
   git push origin v1.5.0-rc1
   ```

2. **Workflow automatically:**
   - Runs full tests
   - Publishes to TestPyPI

3. **Test installation:**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ ciaf-watermarks
   python verify_install.py
   ```

4. **If issues found:**
   - Fix issues
   - Create new RC: `v1.5.0-rc2`

5. **When ready:**
   - Follow standard release process

## Workflow Status Badges

Add to README.md:

```markdown
![Tests](https://github.com/DenzilGreenwood/ciaf-watermarking/workflows/Tests/badge.svg)
![Publish](https://github.com/DenzilGreenwood/ciaf-watermarking/workflows/Publish%20to%20PyPI/badge.svg)
[![codecov](https://codecov.io/gh/DenzilGreenwood/ciaf-watermarking/branch/main/graph/badge.svg)](https://codecov.io/gh/DenzilGreenwood/ciaf-watermarking)
```

## Manual Workflow Triggers

### Test PyPI Publishing (Manual)

1. Go to Actions → Publish to PyPI
2. Click "Run workflow"
3. Select branch
4. Run workflow
5. Package published to TestPyPI only

## Troubleshooting

### Build fails with FFmpeg errors

**Solution:** FFmpeg is installed in CI workflows. If local tests fail, install FFmpeg:
- Ubuntu: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: `choco install ffmpeg`

### PyPI publishing fails with "Invalid credentials"

**Solution:** Ensure trusted publishing is configured correctly or check API token.

### Tests timeout on Windows

**Solution:** Windows runners can be slower. Increase timeout or reduce test matrix.

### Package verification fails

**Solution:** Run `python verify_install.py` locally first. Check all dependencies are installed.

## Maintenance

### Updating Workflow Dependencies

Dependabot (if configured) will automatically create PRs for:
- GitHub Actions versions
- Python package versions

Review and merge these PRs regularly.

### Security Best Practices

1. ✓ Use trusted publishing (no API tokens in secrets)
2. ✓ Enable branch protection on `main`
3. ✓ Require status checks before merging
4. ✓ Use environment protection rules for PyPI
5. ✓ Sign releases with Sigstore
6. ✓ Run security scans in CI

## Contact

For workflow issues or questions:
- Open an issue on GitHub
- Contact: Denzil James Greenwood (founder@cognitiveinsight.ai)
