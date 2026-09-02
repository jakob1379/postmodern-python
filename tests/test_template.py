"""End-to-end tests for the Copier template."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
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


def table_position(contents: str, table_name: str) -> int:
    table_header = f"[{table_name}]"
    try:
        return contents.splitlines().index(table_header)
    except ValueError as error:
        raise AssertionError(f"Table {table_header!r} not found in generated pyproject.toml") from error


def dev_dependency_block(contents: str) -> list[str]:
    lines = contents.splitlines()
    start = lines.index("dev = [")
    end = lines.index("]", start)
    return lines[start + 1 : end]


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
    assert not (project_dir / ".pre-commit-config.yaml").exists()
    assert (project_dir / ".github" / "dependabot.yml").is_file()
    assert (project_dir / "flake.nix").is_file()

    pyproject = (project_dir / "pyproject.toml").read_text()
    config = read_pyproject(project_dir / "pyproject.toml")
    flake = (project_dir / "flake.nix").read_text()
    pr_workflow = (project_dir / ".github" / "workflows" / "pr.yml").read_text()
    security_workflow = (project_dir / ".github" / "workflows" / "security.yml").read_text()

    assert config["project"]["name"] == module
    assert config["project"]["description"] == base_answers["description"]
    assert config["project"]["dependencies"] == []
    author = config["project"]["authors"][0]
    assert author["name"] == base_answers["user_name"].title()
    assert author["email"] == base_answers["user_email"]

    scripts = config["project"]["scripts"]
    assert scripts[module] == f"{module}.hello:main"
    assert config["project"]["requires-python"] == ">=3.13"
    assert config["tool"]["tomlsort"]["sort_first"] == [
        "project",
        "build-system",
        "dependency-groups",
        "project.scripts",
    ]
    assert config["tool"]["tomlsort"]["spaces_indent_inline_array"] == 4
    assert config["tool"]["tomlsort"]["trailing_comma_inline_array"] is True
    assert config["tool"]["deptry"]["known_first_party"] == [module]
    assert config["tool"]["ruff"]["target-version"] == "py313"
    assert config["tool"]["pyrefly"]["python-version"] == "3.13"
    assert "" not in dev_dependency_block(pyproject)

    dev_group = config["dependency-groups"]["dev"]
    assert any(dep.startswith("deptry") for dep in dev_group)
    assert any(dep.startswith("complexipy") for dep in dev_group)
    assert any(dep.startswith("commitizen") for dep in dev_group)

    poe_tasks = config["tool"]["poe"]["tasks"]
    assert poe_tasks["deps"]["cmd"] == "deptry ."
    assert poe_tasks["ci:deps"]["cmd"] == "deptry ."
    assert poe_tasks["all"]["sequence"] == ["fmt", "lint", "deps", "check", "test"]
    assert "uv run --locked poe ci:deps" in pr_workflow
    uv_commands = [line for line in pr_workflow.splitlines() if "uv sync" in line or "uv run" in line]
    assert uv_commands
    assert all("--locked" in line for line in uv_commands), uv_commands
    assert "uv audit --locked" in security_workflow
    assert "github:cachix/git-hooks.nix" in flake
    assert "${pkgs.betterleaks}/bin/betterleaks" in flake
    assert "gitleaks" not in flake
    assert "uv run --locked skylos src tests --strict --format concise" in flake
    # scoped to the skylos block so commitizen-branch's pre-push stage can't
    # satisfy this by accident
    skylos_hook = flake.split("skylos = {", 1)[1].split("};", 1)[0]
    assert 'stages = [ "pre-push" ]' in skylos_hook
    assert "pass_filenames = false" in skylos_hook
    assert any(dep.startswith("skylos") for dep in dev_group)

    # skylos keeps generated scan state and user config side by side under
    # .skylos/, so assert the real ignore behaviour rather than the patterns
    subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
    for generated in (".skylos/cache/x.json", ".skylos/runs/r1/events.jsonl", ".skylos_trace"):
        assert git_ignores(project_dir, generated), generated
    for config in (".skylos/config.yaml", ".skylos/ai-contract.yml", ".skylos/rules/local.yml"):
        assert not git_ignores(project_dir, config), config
    assert not git_ignores(project_dir, "flake.lock")

    assert not (project_dir / "tests" / "conftest.py").exists()

    dependabot = (project_dir / ".github" / "dependabot.yml").read_text()
    assert "version: 2" in dependabot
    assert dependabot.count('interval: "monthly"') == 2
    assert 'package-ecosystem: "uv"' in dependabot
    assert 'package-ecosystem: "github-actions"' in dependabot
    assert 'package-ecosystem: "docker"' not in dependabot


def git_ignores(project_dir: Path, path: str) -> bool:
    """Whether the generated project's .gitignore excludes ``path``."""
    return (
        subprocess.run(
            ["git", "check-ignore", "-q", path],
            cwd=project_dir,
            check=False,
        ).returncode
        == 0
    )


def test_pyproject_keeps_packaging_sections_before_tools(copie, base_answers):
    result = copie.copy(extra_answers=base_answers)

    assert result.exception is None
    assert result.project_dir is not None

    pyproject = (result.project_dir / "pyproject.toml").read_text()
    ordered_tables = [
        "project",
        "build-system",
        "dependency-groups",
        "project.scripts",
        "tool.poe.tasks",
    ]

    positions = [table_position(pyproject, table) for table in ordered_tables]
    assert positions == sorted(positions)


def test_generated_project_tests_pass(copie, base_answers):
    """Test that the generated project's full test suite passes."""
    if shutil.which("cc") is None:
        pytest.skip("cc compiler not found, skipping test that may require building dependencies")
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
    flake = (project_dir / "flake.nix").read_text()
    assert "git-hooks" not in flake
    assert "devShells.default" in flake

    pyproject = (project_dir / "pyproject.toml").read_text()
    config = read_pyproject(project_dir / "pyproject.toml")
    dev_group = config["dependency-groups"]["dev"]
    assert "" not in dev_dependency_block(pyproject)
    assert_not_in_iterable("complexipy", dev_group)
    assert_not_in_iterable("skylos", dev_group)


def test_commitizen_toggle(copie, base_answers):
    answers = dict(base_answers)
    answers["use_commitizen"] = False

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir
    config = read_pyproject(project_dir / "pyproject.toml")
    dev_group = config["dependency-groups"]["dev"]
    assert_not_in_iterable("commitizen", dev_group)

    assert "commitizen" not in (project_dir / "flake.nix").read_text()


def test_include_docs_generates_docs(copie, base_answers):
    answers = dict(base_answers)
    answers["include_docs"] = True

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir
    assert (project_dir / "zensical.toml").is_file()
    assert (project_dir / "docs").is_dir()

    dev_group = read_pyproject(project_dir / "pyproject.toml")["dependency-groups"]["dev"]
    assert any(dep.startswith("zensical") for dep in dev_group)

    zensical_config = read_pyproject(project_dir / "zensical.toml")
    assert (
        zensical_config["project"]["site_url"] == "https://test-user.github.io/postmodern-python/"
    )
    assert (
        zensical_config["project"]["repo_url"] == "https://github.com/test-user/postmodern-python"
    )
    assert (
        zensical_config["project"]["extra"]["social"][0]["link"]
        == "https://github.com/test-user/postmodern-python"
    )

    docs_index = (project_dir / "docs" / "index.md").read_text()
    assert "https://github.com/test-user/postmodern-python" in docs_index
    assert "https://pypi.org/project/postmodern/" in docs_index


def test_flake_renders_nix_interpolation(copie, base_answers):
    result = copie.copy(extra_answers=base_answers)
    assert result.exception is None and result.project_dir is not None

    flake = (result.project_dir / "flake.nix").read_text()
    # jinja must leave nix antiquotation alone
    assert "nixpkgs.legacyPackages.${system}" in flake
    assert "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt" in flake
    assert "${pre-commit.shellHook}" in flake
    assert "devShells.default" in flake


def test_copier_tasks_stage_project_for_nix(copie, base_answers):
    """Nix flakes ignore untracked files, so _tasks must leave everything staged."""
    result = copie.copy(extra_answers=base_answers)
    assert result.exception is None and result.project_dir is not None

    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=result.project_dir,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert "flake.nix" in tracked
    assert "uv.lock" in tracked


def test_include_dockerfile_and_python_version(copie, base_answers):
    answers = dict(base_answers)
    answers.update(
        {
            "include_dockerfile": True,
            "python_version": "3.12",
        }
    )

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir

    dockerfile = project_dir / "Dockerfile"
    assert dockerfile.is_file()
    assert (project_dir / ".dockerignore").is_file()
    dockerfile_content = dockerfile.read_text()
    assert f"FROM python:{answers['python_version']}-slim-bookworm" in dockerfile_content
    assert "COPY pyproject.toml ./" in dockerfile_content
    assert "uv sync --frozen --no-install-project" in dockerfile_content
    assert "uv.lock" not in dockerfile_content
    # src layout: the package lives at /app/src/<module>, not /app/<module>
    assert (
        'CMD ["/app/.venv/bin/python", "/app/src/postmodern/server.py"]'
        in dockerfile_content
    )

    dependabot = (project_dir / ".github" / "dependabot.yml").read_text()
    assert 'package-ecosystem: "docker"' in dependabot

    config = read_pyproject(project_dir / "pyproject.toml")
    assert config["project"]["requires-python"] == f">={answers['python_version']}"


def test_include_direnv_toggle(copie, base_answers):
    # Test with include_direnv=True
    answers = dict(base_answers)
    answers["include_direnv"] = True

    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir
    assert (project_dir / ".envrc").is_file()
    envrc_content = (project_dir / ".envrc").read_text()
    expected_lines = [
        "# shellcheck shell=bash",
        "# shellcheck disable=SC2034 # VIRTUAL_ENV is consumed by `layout python`",
        "use flake",
        'VIRTUAL_ENV=".venv"',
        "layout python",
        "dotenv_if_exists .env",
    ]
    assert envrc_content.strip().splitlines() == expected_lines

    # Test with include_direnv=False
    answers["include_direnv"] = False
    result = copie.copy(extra_answers=answers)
    assert result.exception is None and result.project_dir is not None

    project_dir = result.project_dir
    assert not (project_dir / ".envrc").exists()


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
    # Invalid versions should be rejected by the copier validator.
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
    assert result.exception is not None
    assert result.project_dir is None

    answers["python_version"] = "3"
    result = copie.copy(extra_answers=answers)
    assert result.exception is not None
    assert result.project_dir is None

    # Test valid version
    answers["python_version"] = "3.12"
    result = copie.copy(extra_answers=answers)
    assert result.exception is None
    project_dir = result.project_dir
    config = read_pyproject(project_dir / "pyproject.toml")
    assert config["project"]["requires-python"] == ">=3.12"
    assert config["tool"]["ruff"]["target-version"] == "py312"
    assert config["tool"]["pyrefly"]["python-version"] == "3.12"
    assert 'requires-python = ">=3.12"' in (project_dir / "uv.lock").read_text()

    answers["python_version"] = "3.12.1"
    result = copie.copy(extra_answers=answers)
    assert result.exception is None
    project_dir = result.project_dir
    config = read_pyproject(project_dir / "pyproject.toml")
    assert config["project"]["requires-python"] == ">=3.12.1"
    assert config["tool"]["ruff"]["target-version"] == "py312"
    assert config["tool"]["pyrefly"]["python-version"] == "3.12.1"


def test_interactive_copy_prompts_user_name_before_slug(tmp_path):
    destination = tmp_path / "who-speaks"
    answers = "\n".join(
        [
            "who-speaks",
            "who-speaks",
            "",
            "Test User",
            "test-user",
            "user@example.com",
            "",
            "",
            "",
            "",
            "",
            "",
        ]
    )

    completed = subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--trust", ".", str(destination)],
        cwd=Path(__file__).resolve().parents[1],
        input=f"{answers}\n",
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert (destination / "pyproject.toml").is_file()


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
    (
        "include_dockerfile",
        "include_docs",
        "include_precommit",
        "use_commitizen",
        "include_direnv",
    ),
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
    copie,
    base_answers,
    include_dockerfile,
    include_docs,
    include_precommit,
    use_commitizen,
    include_direnv,
):
    """Test that various combinations of optional features work correctly."""
    answers = dict(base_answers)
    answers.update(
        {
            "include_dockerfile": include_dockerfile,
            "include_docs": include_docs,
            "include_precommit": include_precommit,
            "use_commitizen": use_commitizen,
            "include_direnv": include_direnv,
        }
    )
    result = copie.copy(extra_answers=answers)
    assert result.exception is None
    assert result.project_dir is not None
    project_dir = result.project_dir

    # Check expected files exist or not
    assert (project_dir / "Dockerfile").exists() == include_dockerfile
    assert (project_dir / ".dockerignore").exists() == include_dockerfile
    assert (project_dir / "zensical.toml").exists() == include_docs
    assert (project_dir / "docs").exists() == include_docs
    assert not (project_dir / ".pre-commit-config.yaml").exists()
    assert ("git-hooks" in (project_dir / "flake.nix").read_text()) == include_precommit
    assert (project_dir / ".envrc").exists() == include_direnv

    # Check dependencies in pyproject.toml
    config = read_pyproject(project_dir / "pyproject.toml")
    dev_group = config["dependency-groups"]["dev"]
    assert any(dep.startswith("deptry") for dep in dev_group)
    if include_precommit:
        assert any(dep.startswith("skylos") for dep in dev_group)
    else:
        assert not any(dep.startswith("skylos") for dep in dev_group)
    if use_commitizen:
        assert any(dep.startswith("commitizen") for dep in dev_group)
    else:
        assert not any(dep.startswith("commitizen") for dep in dev_group)
    if include_docs:
        assert any(dep.startswith("zensical") for dep in dev_group)
    else:
        assert not any(dep.startswith("zensical") for dep in dev_group)
