---
name: run-and-fix-python
description: Run every Python file in the repository, detect failures, then debug and fix them. Use when the user asks to run all Python scripts, check the repo for broken Python files, smoke-test .py files, or debug and fix failing Python code across the project.
disable-model-invocation: true
---

# Run and Fix Python

Run all Python files in the repository, find the ones that fail, then debug and fix each failure until the file runs cleanly.

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Discover Python files
- [ ] Step 2: Run each file and collect failures
- [ ] Step 3: Triage failures
- [ ] Step 4: Debug and fix each failing file
- [ ] Step 5: Re-run to verify all pass
```

### Step 1: Discover Python files

Find all `.py` files, excluding virtual environments, caches, and vendored code:

```bash
rg --files -g '*.py' \
  -g '!**/.venv/**' -g '!**/venv/**' -g '!**/env/**' \
  -g '!**/site-packages/**' -g '!**/__pycache__/**' \
  -g '!**/node_modules/**' -g '!**/build/**' -g '!**/dist/**'
```

If the repo uses `pytest`, prefer running the test suite for files under `tests/`; run standalone scripts directly (see Step 2).

### Step 2: Run each file and collect failures

Run each file and capture stdout, stderr, and the exit code. A non-zero exit code is a failure.

```bash
python file.py; echo "EXIT=$?"
```

Notes:
- Use `python3` if `python` is unavailable.
- Respect the repo's environment: activate a virtualenv or use `uv run` / `poetry run` if the project defines one.
- Give long-running or interactive scripts a timeout so the run doesn't hang:

```bash
timeout 60 python file.py; echo "EXIT=$?"
```

- Record each result as PASS or FAIL with the captured error output.

### Step 3: Triage failures

Group failures by root cause before fixing. Common categories:
- **Import/dependency errors** (`ModuleNotFoundError`): missing package or wrong import path.
- **Syntax errors** (`SyntaxError`): fix the code directly.
- **Runtime errors** (`NameError`, `TypeError`, `AttributeError`, etc.): logic or API misuse.
- **Environment/config errors**: missing env vars, files, or services. These may be expected — do not "fix" by faking data unless the user asks.

Distinguish real code defects from expected failures (e.g. a script that requires credentials or network access). Flag expected failures to the user instead of forcing a fix.

### Step 4: Debug and fix each failing file

For each failing file:
1. Read the full traceback to locate the failure.
2. Read the relevant code and surrounding context.
3. Make the smallest correct fix that addresses the root cause.
4. Re-run only that file to confirm it now passes.

Prefer minimal, targeted edits. Do not rewrite working code or change behavior beyond what the fix requires.

### Step 5: Re-run to verify all pass

After fixing, re-run the full set from Step 2. Repeat Steps 3–5 until every file passes or the only remaining failures are expected environment-dependent ones.

## Report format

Summarize results using this template:

```markdown
## Python run results

Ran N files: X passed, Y fixed, Z expected failures.

### Fixed
- `path/to/file.py` — <root cause> → <fix>

### Expected failures (not fixed)
- `path/to/file.py` — <reason, e.g. requires DB connection>
```
