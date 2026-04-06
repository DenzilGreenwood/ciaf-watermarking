# Release Quick Reference

Quick commands for common release operations.

## Standard Release

```bash
# 1. Update version in pyproject.toml
version = "1.5.0"

# 2. Commit, tag, and push
git add pyproject.toml
git commit -m "Bump version to 1.5.0"
git push origin main
git tag -a v1.5.0 -m "Release version 1.5.0"
git push origin v1.5.0

# 3. Create GitHub Release
gh release create v1.5.0 --generate-notes

# Workflow automatically publishes to PyPI ✓
```

## Release Candidate

```bash
# Create and push RC tag
git tag -a v1.5.0-rc1 -m "Release candidate 1"
git push origin v1.5.0-rc1

# Workflow automatically publishes to TestPyPI ✓

# Test installation
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            ciaf-watermarks

python verify_install.py
```

## Manual TestPyPI Push

```bash
# Via GitHub UI:
# Actions → Publish to PyPI → Run workflow → Select branch → Run

# Or via CLI:
gh workflow run publish.yml
```

## Check Workflow Status

```bash
# List recent runs
gh run list --workflow=publish.yml

# Watch active run
gh run watch

# View specific run
gh run view <run-id> --log
```

## Emergency: Cancel Release

```bash
# Cancel running workflow
gh run cancel <run-id>

# Delete tag (before workflow completes)
git tag -d v1.5.0
git push origin :refs/tags/v1.5.0

# Delete release
gh release delete v1.5.0
```

## View Published Package

```bash
# PyPI page
open https://pypi.org/project/ciaf-watermarks/

# TestPyPI page
open https://test.pypi.org/project/ciaf-watermarks/

# Download stats
open https://pypistats.org/packages/ciaf-watermarks
```

## Verify Release

```bash
# Create clean environment
python -m venv verify_env
source verify_env/bin/activate  # Windows: verify_env\Scripts\activate

# Install from PyPI
pip install ciaf-watermarks

# Run verification
python -c "from ciaf_watermarks import watermark_ai_output; print('✓ Success!')"

# Cleanup
deactivate
rm -rf verify_env
```

## Version Numbering

```
1.2.3
│ │ └─ PATCH: Bug fixes (1.2.3 → 1.2.4)
│ └─── MINOR: New features, backward compatible (1.2.3 → 1.3.0)
└───── MAJOR: Breaking changes (1.2.3 → 2.0.0)
```

## Pre-Release Checklist

- [ ] All tests passing locally
- [ ] Version bumped in pyproject.toml
- [ ] README updated if needed
- [ ] No uncommitted changes
- [ ] RC tested on TestPyPI (recommended)

## Troubleshooting

```bash
# Re-run failed workflow
gh run rerun <run-id>

# Re-run failed jobs only
gh run rerun <run-id> --failed

# View workflow file
cat .github/workflows/publish.yml

# Check environments
gh api repos/DenzilGreenwood/ciaf-watermarking/environments
```

## Useful Links

- Workflows: https://github.com/DenzilGreenwood/ciaf-watermarking/actions
- PyPI: https://pypi.org/project/ciaf-watermarks/
- TestPyPI: https://test.pypi.org/project/ciaf-watermarks/
- Releases: https://github.com/DenzilGreenwood/ciaf-watermarking/releases
