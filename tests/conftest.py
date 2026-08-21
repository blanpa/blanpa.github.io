"""Shared fixtures: parse every content page once into something testable.

The tests in this directory check the *content* of the site — front matter,
code samples, diagrams, and the technical claims in the prose. They do not
need Hugo: they read content/ directly, so they run in a second and fail with
a file and line number a human can act on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
DATA = REPO / "data"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)
FENCE = re.compile(r"^([ \t]*)```([^\n`]*)\n(.*?)^\1```[ \t]*$", re.M | re.S)


@dataclass(frozen=True)
class CodeBlock:
    lang: str
    code: str
    line: int
    page: "Page"

    def __str__(self) -> str:  # shown in pytest ids and failures
        return f"{self.page.rel}:{self.line} ({self.lang or 'no language'})"


@dataclass
class Page:
    path: Path
    meta: dict
    body: str
    rel: str = ""
    blocks: list[CodeBlock] = field(default_factory=list)

    @property
    def section(self) -> str:
        return self.path.parent.parent.name

    @property
    def slug(self) -> str:
        return self.path.parent.name

    def line_of(self, offset: int) -> int:
        """1-based line number in the file for a body offset."""
        front_lines = self.path.read_text(encoding="utf-8")[: -len(self.body)].count("\n")
        return front_lines + self.body.count("\n", 0, offset) + 1


def _load(path: Path) -> Page | None:
    raw = path.read_text(encoding="utf-8")
    match = FRONT_MATTER.match(raw)
    if not match:
        return None
    meta = yaml.safe_load(match.group(1)) or {}
    page = Page(path=path, meta=meta, body=match.group(2))
    page.rel = str(path.relative_to(REPO))
    for m in FENCE.finditer(page.body):
        page.blocks.append(
            CodeBlock(
                lang=m.group(2).strip().lower(),
                code=m.group(3),
                line=page.line_of(m.start()),
                page=page,
            )
        )
    return page


def _collect(pattern: str) -> list[Page]:
    pages = []
    for path in sorted(CONTENT.glob(pattern)):
        page = _load(path)
        if page is not None and not page.meta.get("draft"):
            pages.append(page)
    return pages


POSTS = _collect("blog/*/index.md")
PROJECTS = _collect("projects/*/index.md")
# Standalone pages: about, services, impressum, datenschutz.
SINGLES = _collect("*/index.md")
ALL_PAGES = POSTS + PROJECTS + SINGLES


# Fixture name -> the fence languages it should receive. Parametrizing per
# language keeps every test case a real check instead of a skip.
BY_LANGUAGE = {
    "json_block": {"json", "jsonc"},
    "yaml_block": {"yaml", "yml"},
    "toml_block": {"toml"},
    "python_block": {"python"},
    "js_block": {"javascript", "js"},
    "shell_block": {"bash", "sh", "shell"},
    "mermaid": {"mermaid"},
}


def pytest_generate_tests(metafunc):
    """Parametrize over pages/code blocks so each one is its own test case."""
    if "post" in metafunc.fixturenames:
        metafunc.parametrize("post", POSTS, ids=[p.slug for p in POSTS])
    if "page" in metafunc.fixturenames:
        metafunc.parametrize("page", ALL_PAGES, ids=[f"{p.section}/{p.slug}" for p in ALL_PAGES])
    if "block" in metafunc.fixturenames:
        blocks = [b for p in ALL_PAGES for b in p.blocks]
        metafunc.parametrize("block", blocks, ids=[str(b) for b in blocks])
    for name, languages in BY_LANGUAGE.items():
        if name in metafunc.fixturenames:
            blocks = [b for p in ALL_PAGES for b in p.blocks if b.lang in languages]
            metafunc.parametrize(name, blocks, ids=[str(b) for b in blocks])


@pytest.fixture(scope="session")
def posts() -> list[Page]:
    return POSTS


@pytest.fixture(scope="session")
def pages() -> list[Page]:
    return ALL_PAGES


@pytest.fixture(scope="session")
def npm_packages() -> list[dict]:
    return yaml.safe_load((DATA / "npm_packages.yml").read_text(encoding="utf-8"))
