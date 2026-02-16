# postmodern-python (Copier template)

A productive, batteries-included Python project template delivered via Copier.

Key features included in the generated project:
- uv for Python installation, virtualenvs, dependency management, and script running
- Ruff for formatting and linting (replaces Black, isort, and Flake8)
- Pytest for tests
- GitHub Actions for CI (format, lint, type-check, test) and releases to PyPI
- Optional Dockerfile for containerized runs
- Optional pre-commit hooks
- Optional Zensical for docs
- Starter Python modules and CLI scaffolding

## Quickstart (with Copier)

1) Scaffold a new project from this repo using Copier
```bash
# cookiecutter is for slugify
uvx --with cookiecutter \
  copier copy --trust https://github.com/jakob1379/postmodern-python my_project
```
1) Enter the new project and install dependencies
```bash
cd my_project
uv run poe setup
```

1) update your project if anything new pops up in here
```bash
uvx --with cookiecutter copier update
```
## Important Copier options

These map directly to copier.yml and control how your project is generated:

- project_name (str): Your project’s display name.
- module_name (str, default: project_name): Python package/module name used for src layout.
- description (str, default: ""): Short description for your project (used in metadata).
- user_name (str): Your full name (used in metadata, LICENSE, etc.).
- user_email (str): Your email (used in metadata).
- python_version (str, default: 3.13): Target Python version. Valid formats: X, X.Y, or X.Y.Z with digits only (e.g., 3, 3.13, 3.13.4).
- include_dockerfile (bool, default: yes): Include a Dockerfile in the generated project.
- use_commitizen (bool, default: yes): Configure Commitizen for conventional commits and release management.
- include_precommit (bool, default: yes): Include a pre-commit config to auto-run linters and checks on commit.
- include_docs (bool, default: no): Include Zensical configuration for easy docs hosting.

Internal template settings (for reference):
- `_subdirectory`: template
- `_exclude`: .venv/, .git/
- `_jinja_extensions`: cookiecutter.extensions.SlugifyExtension

## After generation

From the command line (examples shown for a project with module name "postmodern"):
```bash
python -m postmodern
# or, if project.scripts defines an entry point:
postmodern
```

From Python:
```python
from postmodern import hello
hello()
```

Common development workflow using uv:
```bash
uv run poe fmt
uv run poe lint
uv run poe check
uv run poe test
uv run poe all
```

## CI/CD

The generated project includes GitHub Actions workflows for:
- Pull request CI (format, lint, type-check, test)
- Releases to PyPI (via a dedicated workflow you can enable as you prefer)

## Docker (optional)

If you selected include_dockerfile:
```bash
docker build --tag my-project-image .
docker run --rm -it my-project-image
```

## Origin and credits

Maintained by Jakob Stender Guldberg (@jakob1379): https://github.com/jakob1379/postmodern-python
This template is based on and extends:
- postmodern-python by @carderne: https://github.com/carderne/postmodern-python
- The accompanying article "Beyond Hypermodern: Python is easy now": https://rdrn.me/postmodern-python/

What's different here:
- Delivered via Copier rather than GitHub's template feature
- Exposes key options in copier.yml for customization (Dockerfile, pre-commit, Commitizen, Zensical, Python version, and more)
- Keeps the same core tooling choices (uv, Ruff, Pyright, Pytest) with a streamlined, configurable bootstrap
