# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Shared fixtures for hummbl-governance tests."""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_GIT_ENV_VARS = (
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
    "GIT_QUARANTINE_PATH",
)


def _remove_git_env(environ):
    """Remove repository-local Git variables and return their prior values."""
    return {var: environ.pop(var) for var in _GIT_ENV_VARS if var in environ}


def _restore_git_env(environ, saved):
    """Restore the exact pre-session state for repository-local Git variables."""
    for var in _GIT_ENV_VARS:
        environ.pop(var, None)
    environ.update(saved)


@pytest.fixture(autouse=True, scope="session")
def _strip_git_env():
    """Keep subprocess Git commands isolated from the invoking worktree."""
    saved = _remove_git_env(os.environ)
    try:
        yield
    finally:
        _restore_git_env(os.environ, saved)
