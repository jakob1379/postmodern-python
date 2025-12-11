"""Test configuration for Copier template checks."""

from __future__ import annotations

from typing import Dict

import pytest


_BASE_ANSWERS: Dict[str, object] = {
    "project_name": "postmodern-python",
    "module_name": "postmodern",
    "description": "Example project scaffolded by tests",
    "user_name": "Test User",
    "user_full_name": "Test User",
    "user_email": "user@example.com",
}


@pytest.fixture()
def base_answers() -> Dict[str, object]:
    """Return a fresh copy of the baseline answers for copier."""

    return dict(_BASE_ANSWERS)
