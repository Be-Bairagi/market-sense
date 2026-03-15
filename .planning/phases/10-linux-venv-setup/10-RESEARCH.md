# Phase 10: Linux venv Setup - Research

**Researched:** 2026-03-02
**Domain:** Python virtual environment setup
**Confidence:** HIGH

## Summary

This phase involves creating Linux-compatible Python virtual environments (`venv_linux`) for both the MarketSense backend and frontend applications. The research confirms using Python 3.11 is essential due to binary wheel availability for key dependencies (pandas, numpy, streamlit).

**Primary recommendation:** Use `python3.11 -m venv venv_linux` for both projects, install dependencies via `pip install -r requirements.txt`, and verify with import checks.

## Standard Stack

### Python Version
| Version | Purpose | Why Required |
|---------|---------|--------------|
| Python 3.11 | Runtime | Binary wheels available for pandas, streamlit, numpy. Python 3.14 lacks binary wheels. |

### Virtual Environment
| Tool | Purpose | Command |
|------|---------|---------|
| venv (built-in) | Create isolated Python environment | `python3.11 -m venv venv_linux` |

### Verification Tools
| Tool | Purpose | Command |
|------|---------|---------|
| pip | Install dependencies | `pip install -r requirements.txt` |
| python -c "import X" | Verify package | `python -c "import fastapi"` |

## Architecture Patterns

### Recommended Setup Pattern
```
# 1. Navigate to project directory
cd MarketSense-backend  # or Marketsense-frontend

# 2. Create venv (or remove existing and recreate)
python3.11 -m venv venv_linux

# 3. Activate (for manual testing)
source venv_linux/bin/activate

# 4. Upgrade pip (important for binary wheels)
pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Verify key packages
python -c "import fastapi, yfinance, prophet"

# 7. Deactivate
deactivate
```

### Directory Structure After
```
MarketSense-backend/
├── venv/              # Original Windows venv
├── venv_311/          # Python 3.11 venv
├── venv_linux/        # NEW: Linux-compatible venv ←
├── requirements.txt
└── ...

Marketsense-frontend/
├── venv_311/          # Python 3.11 venv
├── venv_linux/        # NEW: Linux-compatible venv ←
├── requirements.txt
└── ...
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Virtual environment | Build custom isolation | `venv` (built-in) | Python's standard, well-tested |
| Dependency installation | Manually list packages | `pip install -r requirements.txt` | Ensures exact version match |

## Common Pitfalls

### Pitfall 1: Wrong Python Version
**What goes wrong:** `venv_linux` created with Python 3.14, packages fail to install
**Why it happens:** Python 3.14 lacks binary wheels for pandas, numpy, streamlit
**How to avoid:** Always use `python3.11 -m venv` not just `python -m venv`
**Warning signs:** `Building wheel for pandas (PEP 517)` messages during install

### Pitfall 2: Missing pip upgrade
**What goes wrong:** Old pip version fails to install modern packages
**Why it happens:** pip < 21.0 doesn't support modern wheel formats
**How to avoid:** Always run `pip install --upgrade pip` before installing requirements
**Warning signs:** `ERROR: Could not find a version that satisfies the requirement`

### Pitfall 3: Activation in Wrong Directory
**What goes wrong:** Packages installed in wrong venv or system Python
**Why it happens:** Forgetting to `cd` to correct directory before activating
**How to avoid:** Always verify with `which python` after activation
**Warning signs:** `python` points to `/usr/bin/python` instead of `./venv_linux/bin/python`

## Code Examples

### Creating Backend venv_linux
```bash
# Navigate to backend
cd MarketSense-backend

# Remove existing if present (optional - fresh start)
rm -rf venv_linux

# Create with Python 3.11
python3.11 -m venv venv_linux

# Activate
source venv_linux/bin/activate

# Upgrade pip and install
pip install --upgrade pip
pip install -r requirements.txt

# Verify
python -c "import fastapi, yfinance, prophet; print('OK')"

# Deactivate
deactivate
```

### Creating Frontend venv_linux
```bash
# Navigate to frontend
cd Marketsense-frontend

# Create with Python 3.11
python3.11 -m venv venv_linux

# Activate
source venv_linux/bin/activate

# Upgrade pip and install
pip install --upgrade pip
pip install -r requirements.txt

# Verify
python -c "import streamlit, plotly, pandas; print('OK')"

# Deactivate
deactivate
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| System Python | venv (isolated) | Standard practice | Prevents dependency conflicts |
| pip install individually | pip install -r | Standard practice | Reproducible environments |
| Python 3.9-3.10 | Python 3.11 | Current | Better binary wheel support |

## Open Questions

1. **Should venv_linux be committed to git?**
   - What we know: .gitignore typically ignores `venv*/` directories
   - What's unclear: Project convention
   - Recommendation: Add to .gitignore, document setup process

2. **Should existing venvs be removed?**
   - What we know: Backend has venv, venv_311, venv_linux
   - What's unclear: Whether to clean up old venvs
   - Recommendation: Keep for reference, new venv_linux is primary

## Validation Architecture

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| VENV-01 | venv_linux exists in backend | file exists | `ls MarketSense-backend/venv_linux/bin/python` |
| VENV-02 | venv_linux exists in frontend | file exists | `ls Marketsense-frontend/venv_linux/bin/python` |
| VENV-01 | Backend packages importable | smoke | `MarketSense-backend/venv_linux/bin/python -c "import fastapi,yfinance,prophet"` |
| VENV-02 | Frontend packages importable | smoke | `Marketsense-frontend/venv_linux/bin/python -c "import streamlit,plotly,pandas"` |

### Wave 0 Gaps
None — simple file/command verification, no test framework needed.

## Sources

### Primary (HIGH confidence)
- Python venv documentation - https://docs.python.org/3/library/venv.html
- pip requirements file format - https://pip.pypa.io/en/stable/reference/requirements-file-format/

### Secondary (MEDIUM confidence)
- Python 3.14 binary wheel availability (community reports)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python venv is well-documented standard
- Architecture: HIGH - Simple setup pattern, no complexity
- Pitfalls: HIGH - Known Python version issues

**Research date:** 2026-03-02
**Valid until:** 2026-09-02 (stable domain)
