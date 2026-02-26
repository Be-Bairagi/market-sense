---
phase: 1
plan: 01-02
name: Lint & Style Configuration
type: cleanup
wave: 1
depends_on: []
autonomous: true
requirements: [QUA-04]
---

# Plan 01-02: Lint & Style Configuration

## Objective

Update linting configuration to match Black formatting (88 char line length) and run code formatting.

## Context

The project has:
- ~78 flake8 violations in backend
- ~107 flake8 violations in frontend
- Current `.flake8` uses max-line-length 79
- Black uses max-line-length 88 by default

## Tasks

### Task 1: Update Backend .flake8
- **File:** `Marketsense-backend/.flake8`
- **Fix:** Change `max-line-length = 79` to `max-line-length = 88`
- **Verification:** File contains `max-line-length = 88`

### Task 2: Update Frontend .flake8
- **File:** `Marketsense-frontend/.flake8`
- **Fix:** Change `max-line-length = 79` to `max-line-length = 88`
- **Verification:** File contains `max-line-length = 88`

### Task 3: Format Backend Code
- **Command:** `cd Marketsense-backend && black . && isort .`
- **Verification:** Code formatted, no black/isort errors

### Task 4: Format Frontend Code
- **Command:** `cd Marketsense-frontend && black . && isort .`
- **Verification:** Code formatted, no black/isort errors

## Success Criteria

- [ ] Backend .flake8 has max-line-length = 88
- [ ] Frontend .flake8 has max-line-length = 88
- [ ] Backend code formatted with black
- [ ] Frontend code formatted with black
- [ ] Imports sorted with isort in both projects

## Output

Files modified:
- `Marketsense-backend/.flake8`
- `Marketsense-frontend/.flake8`
- Python files in both projects (formatted)
