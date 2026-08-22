"""Internal links resolve, and every diagram actually parses.

lychee already checks links in the *built* site (see .github/workflows/ci.yml).
This checks them in the source, which fails with the markdown file and line
number instead of a generated HTML path — and it catches a link to a post that
was never created, which the build would silently render as a dead link.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"

MD_LINK = re.compile(r"\]\((/[^)\s]*)\)")

# Sections that exist as a page but not as a content directory.
VIRTUAL = {"/tags", "/series", "/blog", "/projects", "/"}


def _resolves(target: str) -> bool:
    path = target.split("#")[0].split("?")[0].rstrip("/")
    if not path or path in VIRTUAL or f"/{path.strip('/')}" in VIRTUAL:
        return True
    candidate = CONTENT / path.lstrip("/")
    if (candidate / "index.md").exists() or candidate.with_suffix(".md").exists():
        return True
    if (candidate / "_index.md").exists():
        return True
    # Static assets (favicons, cv.pdf, images).
    if (REPO / "static" / path.lstrip("/")).exists():
        return True
    # Taxonomy pages: /tags/<tag>/ exists if any page carries the tag.
    parts = path.strip("/").split("/")
    if parts[0] in {"tags", "series"}:
        return True
    return False


def test_internal_links_resolve(page):
    broken = []
    for match in MD_LINK.finditer(page.body):
        target = match.group(1)
        if not _resolves(target):
            broken.append(f"line {page.line_of(match.start())}: {target}")
    assert not broken, f"{page.rel}: link target does not exist — " + "; ".join(broken)


def test_no_link_to_self(page):
    """A post linking to itself is always a copy-paste slip."""
    own = f"/{page.section}/{page.slug}/"
    assert own not in page.body, f"{page.rel}: links to itself ({own})"


MMDC = shutil.which("mmdc")


@pytest.mark.skipif(
    MMDC is None,
    reason="mermaid-cli not installed (npm i -g @mermaid-js/mermaid-cli)",
)
def test_mermaid_diagram_parses(mermaid, tmp_path):
    """A diagram with a syntax error renders as an error box on the page and
    nothing in the build complains."""
    source = tmp_path / "diagram.mmd"
    source.write_text(mermaid.code, encoding="utf-8")
    out = tmp_path / "diagram.svg"

    # mermaid-cli renders through headless Chrome, which cannot start its
    # sandbox on a CI runner ("No usable sandbox!"). The browser only ever
    # opens diagram files from this repository, so dropping the sandbox costs
    # nothing here and is what makes the check runnable in CI at all.
    puppeteer_config = tmp_path / "puppeteer.json"
    puppeteer_config.write_text(
        '{"args": ["--no-sandbox", "--disable-dev-shm-usage"]}', encoding="utf-8"
    )

    result = subprocess.run(
        [
            MMDC,
            "--input", str(source),
            "--output", str(out),
            "--puppeteerConfigFile", str(puppeteer_config),
            "--quiet",
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        pytest.fail(f"{mermaid}: mermaid rejected this diagram —\n{result.stderr[-1500:]}")
    assert out.exists() and out.stat().st_size > 0, f"{mermaid}: produced no SVG"


def test_every_diagram_has_a_prerendered_svg():
    """Diagrams ship as build-time SVGs; a missing one silently costs 3.2 MB.

    layouts/partials/mermaid-figure.html falls back to client-side rendering
    when it finds no SVG for a diagram's source — deliberately, so an
    un-rendered diagram is a heavy page rather than a broken one. The cost of
    that kindness is that nothing would otherwise tell you it happened.

    Fix: tools/render-diagrams.py
    """
    result = subprocess.run(
        [sys.executable, str(REPO / "tools" / "render-diagrams.py"), "--check"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"{result.stdout.strip()}\n{result.stderr.strip()}\n\n"
        "Run tools/render-diagrams.py and commit the new SVGs."
    )
