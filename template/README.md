# {{ project_name }}

{% if description %}{{ description }}{% else %}A productive, batteries-included Python project scaffolded with Copier.{% endif %}

Requires Python {{ python_version }}+ and uses uv for environment and dependency management.

## Getting started

1) Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2) Install dependencies
```bash
uv sync
```

3) Run the app
```bash
uv run python -m {{ module_name }}
```
If a console script entry point was generated, you can also use:
```bash
uv run {{ module_name }}
```

4) Try the sample code from Python
```python
from {{ module_name }} import hello
hello()
```

## Development

Common tasks are provided via Poe the Poet:
```bash
uv run poe fmt     # format with Ruff
uv run poe lint    # lint with Ruff
uv run poe check   # type-check with Pyright
uv run poe test    # run tests with Pytest
uv run poe all     # run all the above sequentially
```

{% if include_precommit %}
### Pre-commit hooks
Install and enable pre-commit hooks:
```bash
uv run pre-commit install
```
Run on all files:
```bash
uv run pre-commit run --all-files
```
{% endif %}

## CI/CD

GitHub Actions workflows are included for:
- Pull requests: formatting, linting, type checking, and tests
- Releases to PyPI

You can find them under .github/workflows in this repository.

{% if include_mkdocs %}
## Documentation (MkDocs)

Serve docs locally:
```bash
uv run mkdocs serve -a 127.0.0.1:8000
```
Build static site:
```bash
uv run mkdocs build
```
{% endif %}

{% if include_dockerfile %}
## Docker

Build an image:
```bash
docker build --tag {{ module_name }}:dev .
```

Run it:
```bash
docker run --rm -it {{ module_name }}:dev
```
{% endif %}

## Project structure

- src/{{ module_name }}/: Your Python package
- tests/: Pytest test suite
- pyproject.toml: Project configuration (dependencies, tools, tasks)
- .github/workflows/: CI pipelines

## License

This project is distributed under the terms of the LICENSE file included in this repository.

## Origin

This project was generated from the “postmodern-python” Copier template maintained by Jakob Stender Guldberg (@jakob1379): https://github.com/jakob1379/postmodern-python, which builds on:
- postmodern-python by @carderne: https://github.com/carderne/postmodern-python
- Article: “Beyond Hypermodern: Python is easy now” — https://rdrn.me/postmodern-python/

This template keeps the same core tooling (uv, Ruff, Pyright, Pytest) with sensible defaults and optional extras (pre-commit, Docker, MkDocs).
