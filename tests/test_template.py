"""End-to-end tests for the Copier template."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

import pytest

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for <3.11
    import tomli as tomllib  # type: ignore[assignment]


def read_pyproject(path: Path) -> dict:
    return tomllib.loads(path.read_text())


def assert_not_in_iterable(item: str, values: Iterable[str]) -> None:
    assert all(item not in value for value in values)


def test_default_project_smoke(copie, base_answers):
    result = copie.copy(extra_answers=base_answers)

    assert result.exception is None
    assert result.project_dir is not None

    project_dir = result.project_dir
    assert project_dir.is_dir()

    module = base_answers["module_name"]

    assert (project_dir / "pyproject.toml").is_file()
    assert (project_dir / "src" / module / "hello.py").is_file()
    assert (project_dir / "tests" / "test_import.py").is_file()
    assert (project_dir / ".pre-commit-config.yaml").is_file()

    config = read_pyproject(project_dir / "pyproject.toml")

    assert config["project"]["name"] == module
    assert config["project"]["description"] == base_answers["description"]
    author = config["project"]["authors"][0]
    assert author["name"] == base_answers["user_name"].title()
    assert author["email"] == base_answers["user_email"]

    scripts = config["project"]["scripts"]
    assert scripts[module] == f"{module}.hello:main"
    assert config["project"]["requires-python"] == ">=3.13"

    dev_group = config["dependency-groups"]["dev"]
    assert any(dep.startswith("prek") for dep in dev_group)
    assert any(dep.startswith("commitizen") for dep in dev_group)


def test_generated_project_tests_pass(copie, base_answers):
    """Test that the generated project's full test suite passes."""
    if shutil.which("cc") is None:
        pytest.skip("cc compiler not found, skipping test that requires building pydantic-core")
    answers = dict(base_answers)
    answers["include_precommit"] = True

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir

    env = os.environ.copy()
    env.setdefault("UV_PYTHON_PREFERENCE", "managed")

    completed = subprocess.run(
        ["uv", "run", "pytest"],
        cwd=project_dir,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr


def test_precommit_toggle(copie, base_answers):
    answers = dict(base_answers)
    answers["include_precommit"] = False

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir
    assert not (project_dir / ".pre-commit-config.yaml").exists()

    config = read_pyproject(project_dir / "pyproject.toml")
    dev_group = config["dependency-groups"]["dev"]
    assert_not_in_iterable("prek", dev_group)


def test_commitizen_toggle(copie, base_answers):
    answers = dict(base_answers)
    answers["use_commitizen"] = False

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir
    config = read_pyproject(project_dir / "pyproject.toml")
    dev_group = config["dependency-groups"]["dev"]
    assert_not_in_iterable("commitizen", dev_group)

    pre_commit_file = project_dir / ".pre-commit-config.yaml"
    assert pre_commit_file.is_file()
    assert "commitizen" not in pre_commit_file.read_text()


def test_include_mkdocs_generates_docs(copie, base_answers):
    answers = dict(base_answers)
    answers["include_mkdocs"] = True

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir
    assert (project_dir / "mkdocs.yml").is_file()
    assert (project_dir / "docs").is_dir()

    dev_group = read_pyproject(project_dir / "pyproject.toml")["dependency-groups"]["dev"]
    assert any(dep.startswith("mkdocs") for dep in dev_group)


def test_include_dockerfile_and_python_version(copie, base_answers):
    answers = dict(base_answers)
    answers.update({
        "include_dockerfile": True,
        "python_version": "3.12",
    })

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir

    dockerfile = project_dir / "Dockerfile"
    assert dockerfile.is_file()
    assert (project_dir / ".dockerignore").is_file()
    assert f"FROM python:{answers['python_version']}-slim-bookworm" in dockerfile.read_text()

    config = read_pyproject(project_dir / "pyproject.toml")
    assert config["project"]["requires-python"] == f">={answers['python_version']}"

def test_include_direnv_toggle(copie, base_answers):
    # Test with include_direnv=True
    answers = dict(base_answers)
    answers['include_direnv'] = True

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir
    assert (project_dir / '.envrc').is_file()
    envrc_content = (project_dir / '.envrc').read_text()
    expected_lines = [
        'VIRTUAL_ENV=".venv"',
        'layout python',
        'dotenv_if_exists .env'
    ]
    assert envrc_content.strip().splitlines() == expected_lines

    # Test with include_direnv=False
    answers['include_direnv'] = False
    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir
    assert not (project_dir / '.envrc').exists()


def test_project_name_slugify(copie):
    """Test that module_name defaults to slugified project_name."""
    answers = {
        "project_name": "My Awesome Project",
        "description": "Test",
        "user_name": "Test User",
        "user_full_name": "Test User",
        "user_email": "user@example.com",
    }
    # Do not provide module_name, let default
    result = copie.copy(extra_answers=answers)
    assert result.exception is None
    assert result.project_dir is not None
    
    project_dir = result.project_dir
    # module_name should be slugified project_name
    expected_module = "my-awesome-project"
    assert (project_dir / "src" / expected_module).is_dir()
    config = read_pyproject(project_dir / "pyproject.toml")
    assert config["project"]["name"] == expected_module


def test_python_version_rendering(copie):
    """Test that python_version is correctly used in generated files."""
    # Test invalid version still renders (validation may be bypassed)
    answers = {
        "project_name": "test",
        "module_name": "test",
        "description": "Test",
        "user_name": "Test User",
        "user_full_name": "Test User",
        "user_email": "user@example.com",
        "python_version": "invalid",
    }
    result = copie.copy(extra_answers=answers)
    # Should still render without exception
    assert result.exception is None
    assert result.project_dir is not None
    project_dir = result.project_dir
    config = read_pyproject(project_dir / "pyproject.toml")
    # requires-python should contain the exact string
    assert config["project"]["requires-python"] == ">=invalid"
    
    # Test valid version
    answers["python_version"] = "3.12"
    result = copie.copy(extra_answers=answers)
    assert result.exception is None
    project_dir = result.project_dir
    config = read_pyproject(project_dir / "pyproject.toml")
    assert config["project"]["requires-python"] == ">=3.12"


def test_generated_project_builds(copie, base_answers):
    """Test that the generated project can be built with uv build."""
    result = copie.copy(extra_answers=base_answers)
    assert result.exception is None and result.project_dir is not None
    
    project_dir = result.project_dir
    env = os.environ.copy()
    env.setdefault("UV_PYTHON_PREFERENCE", "managed")
    
    completed = subprocess.run(
        ["uv", "build"],
        cwd=project_dir,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert (project_dir / "dist").is_dir()
    # Check that a wheel file exists
    wheels = list((project_dir / "dist").glob("*.whl"))
    assert len(wheels) > 0


@pytest.mark.parametrize(
    ("include_dockerfile", "include_mkdocs", "include_precommit", "use_commitizen", "include_direnv"),
    [
        (True, True, True, True, True),
        (False, False, False, False, False),
        (True, False, False, False, False),
        (False, True, False, False, False),
        (False, False, True, False, False),
        (False, False, False, True, False),
        (False, False, False, False, True),
    ],
)
def test_optional_features_combination(
    copie, base_answers, include_dockerfile, include_mkdocs, include_precommit, use_commitizen, include_direnv
):
    """Test that various combinations of optional features work correctly."""
    answers = dict(base_answers)
    answers.update({
        "include_dockerfile": include_dockerfile,
        "include_mkdocs": include_mkdocs,
        "include_precommit": include_precommit,
        "use_commitizen": use_commitizen,
        "include_direnv": include_direnv,
    })
    result = copie.copy(extra_answers=answers)
    assert result.exception is None
    assert result.project_dir is not None
    project_dir = result.project_dir
    
    # Check expected files exist or not
    assert (project_dir / "Dockerfile").exists() == include_dockerfile
    assert (project_dir / ".dockerignore").exists() == include_dockerfile
    assert (project_dir / "mkdocs.yml").exists() == include_mkdocs
    assert (project_dir / "docs").exists() == include_mkdocs
    assert (project_dir / ".pre-commit-config.yaml").exists() == include_precommit
    assert (project_dir / ".envrc").exists() == include_direnv
    
    # Check dependencies in pyproject.toml
    config = read_pyproject(project_dir / "pyproject.toml")
    dev_group = config["dependency-groups"]["dev"]
    if include_precommit:
        assert any(dep.startswith("prek") for dep in dev_group)
    else:
        assert not any(dep.startswith("prek") for dep in dev_group)
    if use_commitizen:
        assert any(dep.startswith("commitizen") for dep in dev_group)
    else:
        assert not any(dep.startswith("commitizen") for dep in dev_group)
    if include_mkdocs:
        assert any(dep.startswith("mkdocs") for dep in dev_group)
    else:
        assert not any(dep.startswith("mkdocs") for dep in dev_group)
