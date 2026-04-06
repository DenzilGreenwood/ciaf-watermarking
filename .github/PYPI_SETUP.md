# PyPI Publishing Setup Guide

Complete guide to setting up automated PyPI publishing for CIAF Watermarks.

## Prerequisites

- ✅ GitHub repository created and code pushed
- ✅ Package working and tested locally
- ✅ PyPI account created (https://pypi.org/account/register/)
- ✅ TestPyPI account created (https://test.pypi.org/account/register/)

## Step-by-Step Setup

### 1. Configure PyPI Trusted Publishing

Trusted publishing is the **recommended** method - no API tokens needed!

#### On PyPI (Production)

1. Visit: https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in:
   - **PyPI Project Name**: `ciaf-watermarks`
   - **Owner**: `DenzilGreenwood`
   - **Repository name**: `ciaf-watermarking`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
4. Click "Add"

#### On TestPyPI (Testing)

1. Visit: https://test.pypi.org/manage/account/publishing/
2. Repeat the same process:
   - **PyPI Project Name**: `ciaf-watermarks`
   - **Owner**: `DenzilGreenwood`
   - **Repository name**: `ciaf-watermarking`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `testpypi`
3. Click "Add"

### 2. Create GitHub Environments

#### Create `pypi` Environment

1. Go to: `https://github.com/DenzilGreenwood/ciaf-watermarking/settings/environments`
2. Click "New environment"
3. Name: `pypi`
4. **Environment protection rules** (recommended):
   - ✓ Required reviewers: Add yourself or team members
   - ✓ Wait timer: 5 minutes (gives time to cancel if needed)
5. Click "Save protection rules"

#### Create `testpypi` Environment

1. Click "New environment"
2. Name: `testpypi`
3. No protection rules needed (it's for testing)
4. Click "Create environment"

### 3. Test the Workflow

#### Option A: Manual Test to TestPyPI

1. Go to: `https://github.com/DenzilGreenwood/ciaf-watermarking/actions`
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. Select `main` branch
5. Click "Run workflow"
6. Wait for completion
7. Check: https://test.pypi.org/project/ciaf-watermarks/

#### Option B: Release Candidate Tag

```bash
# Create RC tag
git tag -a v1.4.0-rc1 -m "Release candidate 1 for v1.4.0"
git push origin v1.4.0-rc1

# Workflow automatically publishes to TestPyPI
# Check: https://test.pypi.org/project/ciaf-watermarks/
```

#### Test Installation from TestPyPI

```bash
# Create test environment
python -m venv test_pypi
source test_pypi/bin/activate  # Windows: test_pypi\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ciaf-watermarks

# Verify
python -c "from ciaf_watermarks import watermark_ai_output; print('Success!')"

# Cleanup
deactivate
rm -rf test_pypi
```

**Note:** The `--extra-index-url https://pypi.org/simple/` is needed because TestPyPI doesn't have all dependencies (like pydantic).

### 4. First Production Release

#### Update Version

1. Edit `pyproject.toml`:
   ```toml
   version = "1.4.0"  # Your release version
   ```

2. Commit:
   ```bash
   git add pyproject.toml
   git commit -m "Release v1.4.0"
   git push origin main
   ```

#### Create Release Tag

```bash
# Create annotated tag
git tag -a v1.4.0 -m "Release version 1.4.0 - Initial PyPI release"

# Push tag
git push origin v1.4.0
```

#### Create GitHub Release

1. Go to: `https://github.com/DenzilGreenwood/ciaf-watermarking/releases`
2. Click "Draft a new release"
3. Choose tag: `v1.4.0`
4. Release title: `v1.4.0 - Initial Release`
5. Description: Add release notes (can auto-generate)
6. Click "Publish release"

#### Workflow Automatically:

✓ Runs all tests  
✓ Builds package  
✓ Publishes to PyPI  
✓ Signs with Sigstore  
✓ Uploads artifacts to GitHub Release  

### 5. Verify Production Release

```bash
# Install from PyPI
pip install ciaf-watermarks

# Verify
python verify_install.py

# Check PyPI page
open https://pypi.org/project/ciaf-watermarks/
```

## Alternative: API Token Method (Legacy)

If you prefer API tokens over trusted publishing:

### Generate PyPI Token

1. Visit: https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Token name: `ciaf-watermarks-github-actions`
4. Scope: "Project: ciaf-watermarks" (after first manual upload) or "Entire account"
5. Click "Add token"
6. **Copy the token** (starts with `pypi-`)

### Add to GitHub Secrets

1. Go to: `https://github.com/DenzilGreenwood/ciaf-watermarking/settings/secrets/actions`
2. Click "New repository secret"
3. Name: `PYPI_TOKEN`
4. Value: Paste your PyPI token
5. Click "Add secret"

### Modify Workflow

Edit `.github/workflows/publish.yml`:

```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_TOKEN }}  # Add this line
```

## Troubleshooting

### "Could not find a version that satisfies the requirement"

**Issue:** Package hasn't propagated to PyPI index yet.

**Solution:** Wait 1-2 minutes, then try again.

### "Filename already exists"

**Issue:** Version already published.

**Solution:** Bump version in `pyproject.toml` and create new release.

### "Invalid or non-existent authentication information"

**Issue:** Trusted publishing not configured correctly.

**Solution:** 
1. Double-check PyPI publishing settings
2. Ensure environment name matches exactly: `pypi` (lowercase)
3. Verify repository name is correct

### "Workflow requires permission to publish"

**Issue:** GitHub environment needs approval.

**Solution:** Go to Actions → Workflow run → Review deployments → Approve

### Tests fail in CI but pass locally

**Issue:** Different environment or missing dependencies.

**Solution:**
1. Check workflow logs for specific error
2. Test in clean virtual environment locally
3. Verify all dependencies in `pyproject.toml`

## Best Practices

### Version Numbering

Follow Semantic Versioning (SemVer):
- **1.0.0** → **1.0.1** - Bug fixes (PATCH)
- **1.0.0** → **1.1.0** - New features, backward compatible (MINOR)
- **1.0.0** → **2.0.0** - Breaking changes (MAJOR)

### Release Checklist

Before creating a release:

- [ ] All tests passing locally
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG updated (if you have one)
- [ ] Documentation updated
- [ ] No uncommitted changes
- [ ] Tested on multiple Python versions
- [ ] Optional dependencies tested
- [ ] Release candidate tested on TestPyPI

### Security

- ✓ Use trusted publishing (no tokens in repo)
- ✓ Enable 2FA on PyPI account
- ✓ Use environment protection rules
- ✓ Review deployment before approving
- ✓ Verify package contents before publishing

## Maintenance

### Regular Updates

1. **Weekly**: Review Dependabot PRs
2. **Monthly**: Check for security advisories
3. **Quarterly**: Review and update dependencies
4. **Yearly**: Review workflow configurations

### Monitoring

Monitor:
- PyPI download statistics: https://pypistats.org/packages/ciaf-watermarks
- GitHub Actions usage: Repository → Settings → Billing
- Codecov coverage trends: https://codecov.io

## Resources

- **PyPI Trusted Publishing Guide**: https://docs.pypi.org/trusted-publishers/
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Python Packaging Guide**: https://packaging.python.org/
- **Semantic Versioning**: https://semver.org/

## Support

Need help?
- GitHub Issues: https://github.com/DenzilGreenwood/ciaf-watermarking/issues
- Email: founder@cognitiveinsight.ai
