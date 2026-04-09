# Bandit Security Scan Results

## Summary
- **Total Issues**: 40
- **High Severity**: 1
- **Medium Severity**: 11
- **Low Severity**: 28

## High Severity Issues (1)

### B324: Use of weak MD5 hash for security
**File**: `src/ciaf_watermarks/hashing.py:131`
**Issue**: MD5 is used without `usedforsecurity=False` flag
**Fix**: Add `usedforsecurity=False` parameter to hashlib.md5()

```python
# Before:
h = hashlib.md5(token.encode("utf-8")).digest()

# After:
h = hashlib.md5(token.encode("utf-8"), usedforsecurity=False).digest()
```

**Note**: MD5 is used here for non-cryptographic purposes (token hashing), so this is safe.

---

## Medium Severity Issues (11)

### B306: Use of insecure tempfile.mktemp()
**Affected Files**:
- `src/ciaf_watermarks/audio/metadata.py` (4 occurrences)
- `src/ciaf_watermarks/audio/spectral.py` (3 occurrences)
- `src/ciaf_watermarks/gpu/fragment_selection.py` (2 occurrences)
- `src/ciaf_watermarks/gpu/perceptual_hashing.py` (2 occurrences)

**Issue**: `tempfile.mktemp()` is deprecated and insecure (race condition vulnerability)

**Fix**: Replace with `tempfile.NamedTemporaryFile()` or `tempfile.mkstemp()`

```python
# Before:
input_path = tempfile.mktemp(suffix=".mp3")

# After (Option 1 - Using NamedTemporaryFile):
with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
    input_path = tmp.name

# After (Option 2 - Using mkstemp):
fd, input_path = tempfile.mkstemp(suffix=".mp3")
os.close(fd)
```

---

## Low Severity Issues (28)

### B110: Try-except-pass (22 occurrences)
**Issue**: Catching exceptions without logging

**Recommendation**:
- Add logging to catch blocks
- Or suppress with `# nosec B110` if intentional

```python
# Current:
except Exception:
    pass

# Better:
except Exception as e:
    logger.debug(f"Failed to cleanup: {e}")
    pass

# Or suppress if intentional:
except Exception:  # nosec B110
    pass
```

### B112: Try-except-continue (4 occurrences)
**Issue**: Catching exceptions and continuing without logging

**Recommendation**: Same as B110 - add logging or suppress

### B404: subprocess module import (1 occurrence)
**Issue**: Importing subprocess module

**Recommendation**: This is acceptable - subprocess is needed for ffmpeg operations. Can be suppressed.

### B603: subprocess call without shell=True check (1 occurrence)
**Issue**: subprocess.run() call

**Recommendation**: Already safe (no shell=True used). Can be suppressed.

---

## Fixes to Apply

### Priority 1: High Severity
1. Fix MD5 usage in `hashing.py`

### Priority 2: Medium Severity
2. Replace all `tempfile.mktemp()` with secure alternatives

### Priority 3: Low Severity
3. Add logging to try-except-pass blocks OR
4. Suppress known-safe issues with `# nosec` comments

---

## Commands to Run

Check current status:
```bash
bandit -r src/ --skip B101 -f json -o bandit_results.json
```

Check after fixes:
```bash
bandit -r src/ --skip B101
```

Generate readable report:
```bash
bandit -r src/ --skip B101 -f txt
```
