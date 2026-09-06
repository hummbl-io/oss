"""Regression tests for repository-local Git environment isolation."""

import importlib.util
from pathlib import Path


def _load_conftest():
    path = Path(__file__).with_name("conftest.py")
    spec = importlib.util.spec_from_file_location("governance_test_conftest", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_git_env_isolation_removes_local_vars_and_restores_exact_state() -> None:
    conftest = _load_conftest()
    original = {
        "PATH": "keep-me",
        "GIT_DIR": "host/.git",
        "GIT_COMMON_DIR": "host/.git",
        "GIT_CONFIG_COUNT": "1",
    }
    environ = original.copy()

    saved = conftest._remove_git_env(environ)

    assert environ == {"PATH": "keep-me"}
    assert saved == {
        "GIT_CONFIG_COUNT": "1",
        "GIT_DIR": "host/.git",
        "GIT_COMMON_DIR": "host/.git",
    }

    environ["GIT_WORK_TREE"] = "temporary/worktree"
    conftest._restore_git_env(environ, saved)

    assert environ == original


def test_git_env_isolation_tracks_every_git_local_env_var() -> None:
    conftest = _load_conftest()
    expected = {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
        "GIT_OBJECT_DIRECTORY",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_GRAFT_FILE",
        "GIT_INDEX_FILE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_REPLACE_REF_BASE",
        "GIT_PREFIX",
        "GIT_SHALLOW_FILE",
        "GIT_COMMON_DIR",
    }

    assert expected <= set(conftest._GIT_ENV_VARS)
