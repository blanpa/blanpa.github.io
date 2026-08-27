#!/usr/bin/env python3
"""Render every ```mermaid block in content/ to a static SVG at build time.

Why: the mermaid runtime is 3.2 MB — by far the heaviest asset on the site —
and it exists only to draw pictures that never change. Rendering them once,
here, means a reader downloads the finished SVG instead of a renderer, the
diagrams show up with JavaScript disabled, and there is no layout shift while
a 3 MB bundle parses.

Two variants per diagram, because the site has a light and a dark theme and a
single SVG cannot serve both:

  light — mermaid's "base" theme fed with the site's own palette, matching
          what Blowfish's mermaid.js builds at runtime from CSS variables
  dark  — mermaid's built-in "dark" theme, which is what Blowfish uses too

Files are content-addressed by diagram source, so editing a diagram produces
a new name and re-renders while everything untouched is skipped. The palette
is tracked separately in assets/diagrams/palette.sha1 — change a colour and
every diagram re-renders, without the palette leaking into the file names
(the Hugo partial has to reproduce those, and it cannot hash a JSON blob).

    tools/render-diagrams.py            # render what is missing, prune orphans
    tools/render-diagrams.py --force    # re-render everything
    tools/render-diagrams.py --check    # exit 1 if anything is missing (no writes)

layouts/partials/mermaid-figure.html looks for these files and inlines them.
When one is missing it silently falls back to the old client-side rendering,
so an unrendered diagram is never a broken page — just a heavy one. The test
suite fails on a missing SVG, which is what keeps that from going unnoticed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
OUT = REPO / "assets" / "diagrams"

FENCE = re.compile(r"^([ \t]*)```mermaid[ \t]*\n(.*?)^\1```[ \t]*$", re.M | re.S)

# Primer, resolved from the site's CSS custom properties: a node is the page
# canvas, its outline is border.default, the connectors are fg.muted, and the
# one highlighted path is accent.fg. Nothing else carries colour, which is how
# GitHub renders a mermaid block in a README.
#
# Both variants are mermaid's "base" theme fed a palette rather than one of
# its built-ins. The dark one used to be mermaid's own "dark" theme — greys
# and purples of its own choosing, on a page that had already committed to a
# palette. Changing any value here invalidates palette.sha1 and re-renders
# every diagram.
FONT = (
    "-apple-system,BlinkMacSystemFont,Segoe UI,Noto Sans,Helvetica,Arial,"
    "sans-serif"
)
FONT_SIZE = "16px"


def palette(canvas, subtle, border, border_strong, fg, fg_muted,
            accent, accent_subtle):
    """Site colour roles -> the ~10 mermaid theme variables that show."""
    return {
        "background": subtle,
        "primaryColor": canvas,
        "primaryBorderColor": border,
        "primaryTextColor": fg,
        "secondaryColor": accent_subtle,
        "secondaryBorderColor": accent,
        "secondaryTextColor": fg,
        "tertiaryColor": subtle,
        "tertiaryBorderColor": border_strong,
        "tertiaryTextColor": fg,
        "lineColor": fg_muted,
        "textColor": fg,
        "nodeTextColor": fg,
        "titleColor": fg,
        "edgeLabelBackground": subtle,
        "fontFamily": FONT,
        "fontSize": FONT_SIZE,
    }


# assets/css/custom.css :root — keep the two in step, or a diagram stops
# matching the page it sits on.
PALETTE = palette(
    canvas="#ffffff", subtle="#f7f6f4", border="#ddd8d0",
    border_strong="#b8b1a6", fg="#1c1e22", fg_muted="#5c5952",
    accent="#a35b00", accent_subtle="#fdf3dc",
)

PALETTE_DARK = palette(
    canvas="#17191d", subtle="#1e2126", border="#33373f",
    border_strong="#4a4f59", fg="#e9e7e3", fg_muted="#9ba0a8",
    accent="#f0b429", accent_subtle="#3a2c0c",
)

VARIANTS = {
    "light": {"theme": "base", "themeVariables": PALETTE},
    "dark": {"theme": "base", "themeVariables": PALETTE_DARK},
}


def normalise(code: str) -> str:
    """The exact string the Hugo partial hashes. Both sides must agree."""
    return code.replace("\r\n", "\n").strip()


def key_for(code: str) -> str:
    """Hash of the diagram source alone.

    The palette deliberately stays out of this: mermaid-figure.html has to
    compute the same key from the same string, and reproducing a JSON blob
    byte-for-byte in a Hugo template is a trap — the first attempt hashed the
    palette here and nothing on the site ever matched. Palette changes are
    handled by the stamp file instead, see stale_palette().
    """
    return hashlib.sha1(normalise(code).encode("utf-8")).hexdigest()[:16]


PALETTE_STAMP = OUT / "palette.sha1"


def palette_signature() -> str:
    return hashlib.sha1(
        json.dumps(VARIANTS, sort_keys=True).encode("utf-8")
    ).hexdigest()


def stale_palette() -> bool:
    """True when the colours changed since the SVGs on disk were rendered."""
    if not PALETTE_STAMP.exists():
        return True
    return PALETTE_STAMP.read_text(encoding="utf-8").strip() != palette_signature()


def collect() -> dict[str, tuple[str, str]]:
    """key -> (source, "<file>:<line>") for every mermaid block in content/."""
    found: dict[str, tuple[str, str]] = {}
    for path in sorted(CONTENT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for m in FENCE.finditer(text):
            code = m.group(2)
            line = text.count("\n", 0, m.start()) + 1
            found.setdefault(
                key_for(code), (code, f"{path.relative_to(REPO)}:{line}")
            )
    return found


def render(code: str, key: str, variant: str, mmdc: str) -> None:
    config = VARIANTS[variant]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        src = tmp / "diagram.mmd"
        src.write_text(normalise(code) + "\n", encoding="utf-8")
        cfg = tmp / "config.json"
        cfg.write_text(json.dumps(config), encoding="utf-8")
        pup = tmp / "puppeteer.json"
        pup.write_text(
            '{"args": ["--no-sandbox", "--disable-dev-shm-usage"]}', encoding="utf-8"
        )
        dest = OUT / f"{key}-{variant}.svg"
        result = subprocess.run(
            [
                mmdc,
                "--input", str(src),
                "--output", str(dest),
                "--configFile", str(cfg),
                "--puppeteerConfigFile", str(pup),
                "--backgroundColor", "transparent",
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0 or not dest.exists():
            raise RuntimeError(
                f"mmdc failed for {key} ({variant}):\n{result.stderr.strip()}"
            )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="re-render everything")
    ap.add_argument(
        "--check",
        action="store_true",
        help="report missing SVGs and exit 1; write nothing",
    )
    args = ap.parse_args()

    diagrams = collect()
    OUT.mkdir(parents=True, exist_ok=True)

    wanted = {
        f"{key}-{variant}.svg" for key in diagrams for variant in VARIANTS
    }
    missing = sorted(f for f in wanted if not (OUT / f).exists())

    if args.check:
        if stale_palette():
            print(
                "render-diagrams: palette changed since the SVGs were rendered"
                " — run tools/render-diagrams.py",
                file=sys.stderr,
            )
            return 1
        if missing:
            print(
                f"render-diagrams: {len(missing)} SVG(s) missing — run "
                f"tools/render-diagrams.py",
                file=sys.stderr,
            )
            for f in missing[:10]:
                print(f"  {f}", file=sys.stderr)
            return 1
        print(f"render-diagrams: {len(diagrams)} diagrams, all rendered.")
        return 0

    mmdc = shutil.which("mmdc")
    if not mmdc:
        print(
            "render-diagrams: mmdc not found — "
            "npm install -g @mermaid-js/mermaid-cli",
            file=sys.stderr,
        )
        return 1

    force = args.force or stale_palette()
    if force and not args.force:
        print("render-diagrams: palette changed (or first run) — rendering all.")
    todo = [
        (key, variant)
        for key in diagrams
        for variant in VARIANTS
        if force or not (OUT / f"{key}-{variant}.svg").exists()
    ]
    for n, (key, variant) in enumerate(todo, 1):
        code, where = diagrams[key]
        print(f"  [{n}/{len(todo)}] {variant:5} {key}  {where}")
        render(code, key, variant, mmdc)

    # Diagrams that were edited or deleted leave their old SVGs behind.
    orphans = [p for p in OUT.glob("*.svg") if p.name not in wanted]
    for p in orphans:
        p.unlink()

    PALETTE_STAMP.write_text(palette_signature() + "\n", encoding="utf-8")

    print(
        f"render-diagrams: {len(diagrams)} diagrams, {len(todo)} rendered, "
        f"{len(orphans)} orphan(s) removed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
