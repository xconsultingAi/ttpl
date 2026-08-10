# Contributing to TTPL

Thank you for your interest in contributing to TTPL! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork into a bench:

   ```bash
   cd $PATH_TO_YOUR_BENCH
   bench get-app https://github.com/<your-username>/ttpl --branch version-16
   bench --site your-site.com install-app ttpl
   ```

3. **Add the upstream remote:**

   ```bash
   cd apps/ttpl
   git remote add upstream https://github.com/xconsultingAi/ttpl.git
   ```

4. **Create a new branch** from `version-16`:

   ```bash
   git checkout -b feat/your-feature-name version-16
   ```

## Development Setup

### Prerequisites

| Dependency       | Version |
| ---------------- | ------- |
| Python           | >= 3.10 |
| Node.js          | >= 20   |
| Frappe Framework | v16     |
| ERPNext          | v16     |

ERPNext is a hard dependency: TTPL customizes ERPNext doctypes and overrides the
`Payment Entry` controller.

### Branches

| Branch       | Purpose                                            |
| ------------ | -------------------------------------------------- |
| `version-16` | Active development against Frappe/ERPNext v16       |
| `develop`    | Legacy branch, kept for reference only              |

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality before every commit:

```bash
cd apps/ttpl
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

### Backend Development

```bash
cd $PATH_TO_YOUR_BENCH
bench start                        # Start the Frappe development server
bench --site your-site.com migrate # Apply schema/patch changes
bench build --app ttpl             # Rebuild the desk JS bundle
```

## Making Changes

- Keep changes focused. A single PR should address a single concern.
- Write or update tests for any new functionality.
- Ensure all linters pass before submitting:

  ```bash
  ruff check ttpl/
  ruff format --check ttpl/
  pre-commit run --all-files
  ```

- Run the test suite:

  ```bash
  bench --site your-site.com run-tests --app ttpl
  ```

## Commit Guidelines

All commits **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This enables automated versioning and changelog generation.

### Format

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

### Allowed Types

| Type       | Description                              |
| ---------- | ---------------------------------------- |
| `feat`     | A new feature                            |
| `fix`      | A bug fix                                |
| `docs`     | Documentation only changes               |
| `style`    | Formatting, missing semicolons, etc.     |
| `refactor` | Code change that neither fixes nor adds  |
| `perf`     | Performance improvement                  |
| `test`     | Adding or updating tests                 |
| `build`    | Build system or dependency changes       |
| `ci`       | CI configuration changes                 |
| `chore`    | Other changes that don't modify src/test |
| `revert`   | Reverts a previous commit                |

### Examples

```
feat: add supplier column to tax withholding report
fix: correct rounding in contribution margin report
docs: document the stock dashboard number cards
refactor(payment-entry): extract tax withholding helper
test: add unit tests for banking detail report
```

## Pull Request Process

1. **Sync your branch** with the latest `version-16`:

   ```bash
   git fetch upstream
   git rebase upstream/version-16
   ```

2. **Push** your branch and open a Pull Request against the `version-16` branch.

3. Fill out the PR template completely - describe what changed and why.

4. Ensure all CI checks pass (linting, semantic commits, tests).

5. A maintainer will review your PR. Address any feedback and push updates to the same branch.

6. Once approved, a maintainer will merge your PR.

## Reporting Bugs

Use the [Bug Report](https://github.com/xconsultingAi/ttpl/issues/new?template=bug_report.md) issue template. Please include:

- Steps to reproduce
- Expected vs. actual behavior
- Screenshots or error logs if applicable
- Your environment (Frappe/ERPNext version, browser, OS)

## Requesting Features

Use the [Feature Request](https://github.com/xconsultingAi/ttpl/issues/new?template=feature_request.md) issue template. Describe:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

---

Thank you for contributing to TTPL!
