# GitHub Actions Workflow Diagram

## Complete CI/CD Pipeline Visualization

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CIAF Watermarks CI/CD Pipeline                   │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ Development Workflow                                                  │
└──────────────────────────────────────────────────────────────────────┘

  Developer          GitHub              CI/CD              PyPI
     │                 │                   │                 │
     │                 │                   │                 │
     │─── Push PR ────>│                   │                 │
     │                 │                   │                 │
     │                 │──── Trigger ─────>│                 │
     │                 │     test.yml      │                 │
     │                 │                   │                 │
     │                 │              ┌────┴────┐            │
     │                 │              │ Tests   │            │
     │                 │              │ Ubuntu  │            │
     │                 │              │ Windows │            │
     │                 │              │ macOS   │            │
     │                 │              │ Py3.8-12│            │
     │                 │              └────┬────┘            │
     │                 │                   │                 │
     │                 │              ┌────┴────┐            │
     │                 │              │ Linters │            │
     │                 │              │ Flake8  │            │
     │                 │              │ Ruff    │            │
     │                 │              │ MyPy    │            │
     │                 │              └────┬────┘            │
     │                 │                   │                 │
     │                 │              ┌────┴────┐            │
     │                 │              │ Security│            │
     │                 │              │ Bandit  │            │
     │                 │              │ Safety  │            │
     │                 │              └────┬────┘            │
     │                 │                   │                 │
     │                 │<──── Status ──────┤                 │
     │<── PR Check ────┤                   │                 │
     │                 │                   │                 │


┌──────────────────────────────────────────────────────────────────────┐
│ Release Candidate Workflow (v*-rc*)                                  │
└──────────────────────────────────────────────────────────────────────┘

  Developer          GitHub              CI/CD            TestPyPI
     │                 │                   │                 │
     │                 │                   │                 │
     │─ Tag v1.5-rc1 ─>│                   │                 │
     │                 │                   │                 │
     │                 │──── Trigger ─────>│                 │
     │                 │  release-cand.yml │                 │
     │                 │                   │                 │
     │                 │              ┌────┴────┐            │
     │                 │              │Full Test│            │
     │                 │              │All Deps │            │
     │                 │              │Py3.8-12 │            │
     │                 │              └────┬────┘            │
     │                 │                   │                 │
     │                 │              ┌────┴────┐            │
     │                 │              │  Build  │            │
     │                 │              │ Dists   │            │
     │                 │              └────┬────┘            │
     │                 │                   │                 │
     │                 │                   │────Publish─────>│
     │                 │                   │    (auto)       │
     │                 │                   │                 │
     │<─ Test Link ────┤<─── Comment ──────┤                 │
     │                 │                   │                 │


┌──────────────────────────────────────────────────────────────────────┐
│ Production Release Workflow                                           │
└──────────────────────────────────────────────────────────────────────┘

  Developer       GitHub Release        CI/CD              PyPI
     │                 │                   │                 │
     │                 │                   │                 │
     │─ Tag v1.5.0 ───>│                   │                 │
     │                 │                   │                 │
     │─ Create Rel ───>│                   │                 │
     │                 │                   │                 │
     │                 │──── Trigger ─────>│                 │
     │                 │    publish.yml    │                 │
     │                 │                   │                 │
     │                 │              ┌────┴────┐            │
     │                 │              │  Test   │            │
     │                 │              │Py3.8-12 │            │
     │                 │              └────┬────┘            │
     │                 │                   ↓                 │
     │                 │              ┌────┴────┐            │
     │                 │              │  Build  │            │
     │                 │              │ tar.gz  │            │
     │                 │              │  .whl   │            │
     │                 │              └────┬────┘            │
     │                 │                   ↓                 │
     │                 │              ┌────┴────┐            │
     │                 │              │ Check   │            │
     │                 │              │ twine   │            │
     │                 │              └────┬────┘            │
     │                 │                   ↓                 │
     │                 │   [Require Approval - pypi env]    │
     │<─ Approval? ────┤<─────────────────┤                 │
     │                 │                   │                 │
     │─── Approve ────>│                   │                 │
     │                 │                   ↓                 │
     │                 │              ┌────┴────┐            │
     │                 │              │ Publish │            │
     │                 │              │ Trusted │───────────>│
     │                 │              │  OIDC   │            │
     │                 │              └────┬────┘            │
     │                 │                   ↓                 │
     │                 │              ┌────┴────┐            │
     │                 │              │  Sign   │            │
     │                 │              │Sigstore │            │
     │                 │              └────┬────┘            │
     │                 │                   ↓                 │
     │                 │<──── Upload ──────┤                 │
     │                 │   (artifacts)     │                 │
     │                 │                   │                 │
     │<── Complete ────┤                   │                 │
     │                 │                   │                 │


┌──────────────────────────────────────────────────────────────────────┐
│ Manual TestPyPI Workflow                                              │
└──────────────────────────────────────────────────────────────────────┘

  Developer          GitHub              CI/CD            TestPyPI
     │                 │                   │                 │
     │                 │                   │                 │
     │─ Run Manual ───>│                   │                 │
     │   Workflow      │                   │                 │
     │                 │                   │                 │
     │                 │──── Trigger ─────>│                 │
     │                 │   (dispatch)      │                 │
     │                 │                   │                 │
     │                 │    [Same as Production Release]    │
     │                 │                   │                 │
     │                 │   But publishes to TestPyPI ───────>│
     │                 │                   │    only         │
     │                 │                   │                 │


┌──────────────────────────────────────────────────────────────────────┐
│ Automated Maintenance (Dependabot)                                   │
└──────────────────────────────────────────────────────────────────────┘

  Schedule           GitHub              Dependabot        Developer
     │                 │                   │                 │
     │                 │                   │                 │
  Every Mon           │                   │                 │
  9am UTC             │                   │                 │
     │                 │                   │                 │
     ├────────────────>│─── Trigger ─────>│                 │
     │                 │                   │                 │
     │                 │              ┌────┴────┐            │
     │                 │              │  Check  │            │
     │                 │              │  Deps   │            │
     │                 │              └────┬────┘            │
     │                 │                   │                 │
     │                 │                   ↓                 │
     │                 │              ┌────┴────┐            │
     │                 │              │Updates? │            │
     │                 │              └────┬────┘            │
     │                 │                   │                 │
     │                 │                   ↓ Yes             │
     │                 │              ┌────┴────┐            │
     │                 │              │ Create  │            │
     │                 │              │   PR    │            │
     │                 │              └────┬────┘            │
     │                 │                   │                 │
     │                 │<──── New PR ──────┤                 │
     │                 │                   │                 │
     │                 │                   │────Notify──────>│
     │                 │                   │                 │
     │                 │                   │  <─Review/Merge─│
     │                 │                   │                 │


┌──────────────────────────────────────────────────────────────────────┐
│ Key Components                                                        │
└──────────────────────────────────────────────────────────────────────┘

  Workflows:
    • test.yml            → PR/Push testing
    • publish.yml         → Production releases
    • release-candidate.yml → RC testing

  Security:
    ✓ Trusted Publishing  → No tokens in repo
    ✓ Environment Protection → Approval required
    ✓ Sigstore Signing    → Artifact verification
    ✓ Security Scanning   → Vulnerability checks

  Automation:
    ✓ Multi-OS Testing    → Ubuntu, Windows, macOS
    ✓ Multi-Python Testing → 3.8, 3.9, 3.10, 3.11, 3.12
    ✓ Dependency Updates  → Dependabot weekly
    ✓ Coverage Tracking   → Codecov integration


┌──────────────────────────────────────────────────────────────────────┐
│ Workflow Triggers Summary                                             │
└──────────────────────────────────────────────────────────────────────┘

  Event                  Workflow              Action
  ──────────────────────────────────────────────────────────
  Push to main/develop   test.yml             Run tests
  Pull Request           test.yml             Run tests + lint
  Tag v*-rc*             release-candidate    Publish TestPyPI
  GitHub Release         publish.yml          Publish PyPI
  Manual Dispatch        publish.yml          Publish TestPyPI
  Monday 9am UTC         dependabot           Check for updates


┌──────────────────────────────────────────────────────────────────────┐
│ Status Checks Required Before Merge                                  │
└──────────────────────────────────────────────────────────────────────┘

  ✓ Tests (Ubuntu, Py 3.11)         REQUIRED
  ✓ Tests (Windows, Py 3.11)        REQUIRED
  ✓ Tests (macOS, Py 3.11)          OPTIONAL
  ✓ Linting                         REQUIRED
  ✓ Build Test                      REQUIRED
  ○ Security Scan                   INFORMATIONAL
```

## Quick Navigation

- **Setup Guide**: `.github/PYPI_SETUP.md`
- **Commands**: `.github/RELEASE_COMMANDS.md`
- **Documentation**: `.github/README.md`
- **Summary**: `GITHUB_ACTIONS_COMPLETE.md`

## Live Monitoring

Once workflows are running:

- **Actions**: https://github.com/DenzilGreenwood/ciaf-watermarking/actions
- **PyPI**: https://pypi.org/project/ciaf-watermarks/
- **TestPyPI**: https://test.pypi.org/project/ciaf-watermarks/
- **Coverage**: https://codecov.io/gh/DenzilGreenwood/ciaf-watermarking
