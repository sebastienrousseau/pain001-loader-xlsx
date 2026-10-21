# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The scheduled suite check holds the pain001 suite to one version.

Every member ships the core's number, in the same release, so a member
published ahead of the core fails exactly like one left behind. The tree
is compared with ``pain001-loader-xlsx``'s own release, not the core's.
PyPI is never reached; the published versions are substituted.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "check_suite_consistency.py"
)

MEMBERS = (
    "pain001",
    "pain001-lsp",
    "pain001-mcp",
    "pain001-loader-mt101",
    "pain001-loader-xlsx",
)


@pytest.fixture
def script(monkeypatch):
    """The script as a module, with PyPI and the tree substituted."""
    spec = importlib.util.spec_from_file_location("suite_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def use(tree: str, published: dict[str, str | None]):
        monkeypatch.setattr(module, "tree_version", lambda: tree)
        monkeypatch.setattr(module, "published_version", published.get)
        return module.check()[0]

    return use


def _suite(version: str, **members: str) -> dict[str, str | None]:
    versions: dict[str, str | None] = dict.fromkeys(MEMBERS, version)
    versions.update({k.replace("_", "-"): v for k, v in members.items()})
    return versions


def test_a_suite_on_one_version_is_clean(script):
    assert script("0.0.74", _suite("0.0.74")) == []


def test_a_member_ahead_of_the_core_fails(script):
    """The state main was in: pain001-mcp 0.0.73, every other member 0.0.72."""
    problems = script("0.0.72", _suite("0.0.72", pain001_mcp="0.0.73"))
    assert problems == [
        "pain001-mcp: published 0.0.73, but the suite is at 0.0.72"
    ]


def test_a_member_left_behind_fails(script):
    problems = script("0.0.74", _suite("0.0.74", pain001_lsp="0.0.72"))
    assert problems == [
        "pain001-lsp: published 0.0.72, but the suite is at 0.0.74"
    ]


def test_the_core_shipping_first_is_not_enough(script):
    """The core's release does not stand in for this package's own.

    The window between the core publishing 0.0.74 and this package doing
    the same: the tree must be compared with this package on PyPI.
    """
    problems = script("0.0.74", _suite("0.0.72", pain001="0.0.74"))
    assert problems[0] == (
        "pain001-loader-xlsx: tree is 0.0.74 but PyPI has 0.0.72. Either "
        "the release was never tagged, or the tree is behind."
    )


def test_unreleased_bump_names_this_distribution(script):
    """A bump that never reached PyPI is reported against this package."""
    problems = script("0.0.74", _suite("0.0.72"))
    assert problems == [
        "pain001-loader-xlsx: tree is 0.0.74 but PyPI has 0.0.72. Either the "
        "release was never tagged, or the tree is behind."
    ]


def test_unreadable_index_is_reported(script):
    """A member PyPI cannot answer for is a problem, never a pass."""
    versions = _suite("0.0.74")
    del versions["pain001-loader-mt101"]
    assert script("0.0.74", versions) == [
        "pain001-loader-mt101: could not read PyPI"
    ]
