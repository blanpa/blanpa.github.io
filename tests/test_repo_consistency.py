"""Checks on the repository itself, not on the articles.

Same principle as the content tests: guard a class of error rather than a
sentence. What these catch is the second copy of a fact drifting away from the
first — the kind of thing nobody re-reads because it was correct when written.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# `- **name** — description` in the README's Projects list.
README_PKG = re.compile(r"^- \*\*(?P<pkg>[^*]+)\*\* — (?P<desc>.+)$", re.M)


def test_readme_package_list_matches_the_canonical_data(npm_packages):
    """The README calls data/npm_packages.yml canonical, then repeats it.

    Two copies of one list: adding a ninth package means editing both, and
    nothing but this test notices when only one of them happens.
    """
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    listed = [(m.group("pkg"), m.group("desc")) for m in README_PKG.finditer(readme)]
    canonical = [(entry["pkg"], entry["desc"]) for entry in npm_packages]

    assert listed, (
        "no package list found in README.md — the expected shape is "
        "`- **node-red-contrib-x** — description`. Update this test if the "
        "README's format changed on purpose."
    )
    assert listed == canonical, (
        "README.md and data/npm_packages.yml disagree.\n"
        f"  README:    {listed}\n"
        f"  canonical: {canonical}\n"
        "data/npm_packages.yml is the source of truth — fix the README to match."
    )


def test_readme_package_count_matches(npm_packages):
    """The prose says "8 open-source npm packages" a line above the list."""
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    stated = re.search(r"showcases (\d+) open-source npm packages", readme)
    assert stated, "the README no longer states how many packages there are"
    assert int(stated.group(1)) == len(npm_packages), (
        f"README says {stated.group(1)} packages, data/npm_packages.yml has "
        f"{len(npm_packages)}"
    )
