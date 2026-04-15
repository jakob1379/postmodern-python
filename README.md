# postmodern-python

[![Copier Template](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json)](https://github.com/copier-org/copier)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Zero-config Python projects with modern tooling. One command, done.

Built for developers who want to ship faster without the configuration headache. Based on [postmodern-python](https://github.com/carderne/postmodern-python) by @carderne — read the philosophy in ["Beyond Hypermodern: Python is easy now"](https://rdrn.me/postmodern-python/).

## Quickstart (30 seconds)

Prerequisites: [uv](https://docs.astral.sh/uv/) installed.

```bash
# Generate project (uses --trust for Copier hooks)
uvx --with cookiecutter copier copy --trust https://github.com/jakob1379/postmodern-python my-project

# Enter and setup
cd my-project && uv run poe setup

# Start coding
uv run poe all  # format + lint + type-check + test
```

**What just happened?** Copier generated a complete Python project with all tooling configured. The `--trust` flag allows the template to run setup hooks (git init, pre-commit install, etc.).

Keep updated: `uvx copier update`

## What You Get

| Tool | Purpose |
|------|---------|
| [uv](https://docs.astral.sh/uv/) | Package management and scripting (10-100x faster than pip) |
| [Ruff](https://docs.astral.sh/ruff/) | Linting and formatting (Black + isort + Flake8 in one) |
| [Pyrefly](https://pyrefly.org/) | Type checking (next-gen, fast) |
| [pytest](https://docs.pytest.org/) | Testing with coverage |
| [Poe the Poet](https://poethepoet.natn.io/) | Task runner (`poe fmt`, `poe test`, etc.) |
| GitHub Actions | CI/CD for PR checks and PyPI releases |
| **Optional** | pre-commit · Docker · Zensical docs · Commitizen |

## Generated Structure

```text
my-project/
├── .github/
│   └── workflows/
│       ├── pr.yml
│       └── release.yml
├── docs/
│   ├── index.md
│   └── reference.md
├── src/module_name/
│   ├── __init__.py
│   ├── __main__.py
│   ├── adder.py
│   ├── cli.py
│   ├── hello.py
│   └── server.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_import.py
├── .copier-answers.yml
├── .dockerignore
├── .envrc
├── .gitignore
├── .pre-commit-config.yaml
├── CONTRIBUTING.md
├── Dockerfile
├── LICENSE
├── pyproject.toml
├── README.md
├── uv.lock
└── zensical.toml
```

## Template Options

During generation, you'll be prompted for:

| Option | Description | Default |
|--------|-------------|---------|
| `project_name` | Display name for your project | — |
| `module_name` | Python package name (auto-slugified) | `project_name` |
| `python_version` | Target Python version | 3.13 |
| `include_precommit` | Pre-commit hooks via prek, including Betterleaks secret scanning | yes |
| `use_commitizen` | Conventional commits workflow | yes |
| `include_dockerfile` | Container image setup | no |
| `include_docs` | Documentation via Zensical | no |
| `include_direnv` | Auto-load .envrc with direnv | yes |

See [copier.yml](copier.yml) for all options and defaults.

## After Generation

Common development tasks use Poe the Poet:

```bash
uv run poe fmt     # Format code with Ruff
uv run poe lint    # Lint with Ruff
uv run poe check   # Type-check with Pyrefly
uv run poe test    # Run pytest suite
uv run poe all     # Run all checks
```

## Credits

- Original template: [carderne/postmodern-python](https://github.com/carderne/postmodern-python)
- Template engine: [Copier](https://copier.readthedocs.io)
