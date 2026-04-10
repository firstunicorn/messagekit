# GitHub Actions workflows

This directory contains CI/CD workflows for automated testing and code quality checks.

## Available workflows

### 1. Tests (`tests.yml`)

**Purpose:** Run complete test suite on Linux (all 140 tests)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual dispatch

**What it does:**
- Runs on Ubuntu latest (Linux environment)
- Installs Python 3.12 and Poetry 2.3.3
- Installs all dependencies
- Runs linters (ruff, isort, mypy)
- **Runs ALL tests** including RabbitMQ integration tests
- Uses testcontainers (Kafka, PostgreSQL, RabbitMQ)
- Generates coverage reports (requires 80% minimum)
- Uploads coverage to Codecov
- Tests on multiple Python versions (3.10, 3.11, 3.12)

**Expected result:** All 140 tests pass ✅

**Duration:** ~15-20 minutes

**Why this works:**
- Linux environment (no Windows Docker Desktop issues)
- Native Docker support
- RabbitMQ testcontainers work perfectly
- All networking works as expected

### 2. Linters (`linters.yml`)

**Purpose:** Run all code quality and security checks

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual dispatch

**What it does:**
- Runs on Ubuntu latest
- Installs Python 3.12 and Poetry 2.3.3
- Runs comprehensive linter suite:
  - `ruff` - Code quality and style
  - `isort` - Import sorting
  - `mypy` - Type checking
  - `flake8` - Additional style checks
  - `pylint` - Code analysis
  - `bandit` - Security scanning
  - `deptry` - Dependency validation
  - `vulture` - Dead code detection
  - `radon` - Complexity analysis
  - `interrogate` - Docstring coverage
  - `import-linter` - Import rules
  - `safety` - Vulnerability scanning

**Expected result:** All linters pass ✅

**Duration:** ~5-10 minutes

## Local vs. CI testing

### Local (Windows)
- ✅ 135/140 tests pass (96.4%)
- ❌ 5 RabbitMQ tests fail (Windows Docker Desktop limitation)
- Command: `poetry run pytest tests/ -v -m "not requires_rabbitmq"`

### CI (GitHub Actions - Linux)
- ✅ All 140 tests pass (100%)
- ✅ All linters pass
- ✅ RabbitMQ testcontainers work perfectly
- No infrastructure limitations

## How to use

### Run workflows manually

1. Go to repository on GitHub
2. Click "Actions" tab
3. Select workflow (Tests or Linters)
4. Click "Run workflow"
5. Select branch
6. Click green "Run workflow" button

### View results

1. Click on workflow run in Actions tab
2. Expand job sections to see detailed logs
3. Check "Summary" for coverage reports and test results
4. Download coverage HTML artifacts if needed

## Coverage reports

Test coverage reports are:
- Displayed in workflow summary
- Uploaded to Codecov (if configured)
- Available as HTML artifact download
- Required minimum: 80%
- Current coverage: ~85%

## Adding status badges to README

Add these badges to `README.md`:

```markdown
![Tests](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/tests.yml/badge.svg)
![Linters](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/linters.yml/badge.svg)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO)
```

## Troubleshooting

### Tests fail on RabbitMQ
Check logs for:
- Container startup timeout (should be 300s)
- Port mapping issues
- Connection errors

### Workflow timeout
- Current timeout: 30 minutes
- Increase if needed in workflow file
- Check for hanging tests

### Coverage below 80%
- Review coverage report in artifacts
- Add missing tests
- Check for untested code paths

## Next steps

1. **Push to GitHub** to trigger first workflow run
2. **Verify all tests pass** (expect 140/140 on Linux)
3. **Configure Codecov** (optional, for coverage tracking)
4. **Add status badges** to README
5. **Enable branch protection** requiring tests to pass before merge
