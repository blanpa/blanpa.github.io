#!/usr/bin/env python3
"""Convert ASCII art diagrams in markdown blog posts to Mermaid diagrams via Claude API.

Finds fenced code blocks without a language (or language `text`) that contain
box-drawing characters and rewrites them as Blowfish `{{< mermaid >}}` shortcodes.

Usage:
  ANTHROPIC_API_KEY=... python generate-diagrams.py                 # all files
  ANTHROPIC_API_KEY=... python generate-diagrams.py --dry-run       # preview only
  ANTHROPIC_API_KEY=... python generate-diagrams.py --file content/blog/foo/index.md
  ANTHROPIC_API_KEY=... python generate-diagrams.py --section blog
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5"

BOX_LINE_CHARS = set("┌┐└┘├┤┬┴┼─│╔╗╚╝╠╣╦╩╬═║")
ARROW_CHARS = set("→←↑↓↔↕")
ARROW_PATTERNS = ["──→", "──>", "<──", "═══>"]

FENCE_RE = re.compile(
    r"(?ms)^(?P<fence>```|~~~)(?P<lang>[^\n`~]*)\n(?P<body>.*?)^(?P=fence)\s*$"
)

SYSTEM_PROMPT = """You convert ASCII-art technical diagrams into clean Mermaid diagrams.

Rules:
- Output ONLY valid Mermaid source. No markdown fences, no prose, no explanations.
- Pick the best diagram type: flowchart (LR/TB), sequenceDiagram, classDiagram, erDiagram, stateDiagram-v2.
- Preserve every node, label, and connection from the original. Do not invent new ones.
- Keep labels short but readable. Use the exact text from the diagram when possible.
- Use subgraphs to group boxes that were visually grouped (e.g. "Cloud", "Factory A").
- Use --> for directed flow, --- for plain links, -.-> for dashed/optional, ==> for thick/important.
- If the original shows multiple parallel scenarios (e.g. "Normal operation:" then "Network drops:"), output ONE diagram with subgraphs labelled accordingly, OR pick the primary scenario — never output multiple Mermaid blocks.
- For protocol/sequence interactions use sequenceDiagram.
- For state machines use stateDiagram-v2.
- Default to: flowchart LR
- Keep it under ~40 nodes. Simplify if necessary while preserving the structure.
"""


def looks_like_diagram(body: str) -> bool:
    """Heuristic: does this code block look like an ASCII diagram?

    Real diagrams have actual box-drawing line characters (┌─┐│└┘) or
    classic ASCII +--+ layouts. Lone arrows (→) without boxes are usually
    just labelled lists or examples, not diagrams.
    """
    box_count = sum(1 for ch in body if ch in BOX_LINE_CHARS)
    if box_count >= 5:
        return True
    plus_pipe = body.count("+") + body.count("|")
    if plus_pipe >= 8 and ("+--" in body or "--+" in body):
        return True
    return False


def call_claude(api_key: str, ascii_block: str) -> str:
    """Send the ASCII block to Claude and return the Mermaid source."""
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 2048,
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": (
                "Convert this ASCII diagram to Mermaid. "
                "Output only the Mermaid source, nothing else.\n\n"
                f"```\n{ascii_block}\n```"
            ),
        }],
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=payload, headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())

    text = "".join(
        block.get("text", "")
        for block in data.get("content", [])
        if block.get("type") == "text"
    ).strip()

    # Strip any accidental fences
    text = re.sub(r"^```(?:mermaid)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def process_file(path: Path, api_key: str, dry_run: bool) -> tuple[int, int]:
    """Returns (converted, skipped) counts."""
    text = path.read_text(encoding="utf-8")
    converted = 0
    skipped = 0
    out_parts = []
    last = 0

    for m in FENCE_RE.finditer(text):
        out_parts.append(text[last:m.start()])
        last = m.end()

        lang = m.group("lang").strip().lower()
        body = m.group("body")

        if lang in ("mermaid", "math", "json", "yaml", "yml", "toml", "go", "python",
                    "py", "javascript", "js", "ts", "typescript", "bash", "sh", "shell",
                    "html", "css", "rust", "java", "c", "cpp", "csharp", "ruby", "php",
                    "sql", "diff", "dockerfile", "makefile", "ini", "xml", "graphql"):
            out_parts.append(m.group(0))
            continue

        if not looks_like_diagram(body):
            out_parts.append(m.group(0))
            continue

        print(f"  → diagram block at line {text[:m.start()].count(chr(10)) + 1} "
              f"({len(body)} chars)")

        if dry_run:
            print(f"    [dry-run] would convert")
            skipped += 1
            out_parts.append(m.group(0))
            continue

        try:
            mermaid_src = call_claude(api_key, body)
        except urllib.error.HTTPError as e:
            print(f"    ERROR {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
            out_parts.append(m.group(0))
            skipped += 1
            continue
        except Exception as e:
            print(f"    ERROR: {e}")
            out_parts.append(m.group(0))
            skipped += 1
            continue

        if not mermaid_src or "graph" not in mermaid_src.lower() \
                and "flowchart" not in mermaid_src.lower() \
                and "sequencediagram" not in mermaid_src.lower() \
                and "statediagram" not in mermaid_src.lower() \
                and "classdiagram" not in mermaid_src.lower() \
                and "erdiagram" not in mermaid_src.lower():
            print(f"    SKIP (response doesn't look like Mermaid): {mermaid_src[:80]}")
            out_parts.append(m.group(0))
            skipped += 1
            continue

        replacement = f"{{{{< mermaid >}}}}\n{mermaid_src}\n{{{{< /mermaid >}}}}"
        out_parts.append(replacement)
        converted += 1
        print(f"    OK ({len(mermaid_src)} chars Mermaid)")

    out_parts.append(text[last:])
    new_text = "".join(out_parts)

    if converted > 0 and not dry_run:
        backup = path.with_suffix(path.suffix + ".bak")
        if not backup.exists():
            backup.write_text(text, encoding="utf-8")
        path.write_text(new_text, encoding="utf-8")
        print(f"  wrote {path} (backup: {backup.name})")

    return converted, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="Process a single markdown file")
    ap.add_argument("--section", default="all",
                    choices=["all", "blog", "projects"],
                    help="Which content section to process")
    ap.add_argument("--dry-run", action="store_true",
                    help="Find diagrams but don't call API or write files")
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key and not args.dry_run:
        print("ERROR: ANTHROPIC_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    if args.file:
        files = [Path(args.file)]
    else:
        sections = ["blog", "projects"] if args.section == "all" else [args.section]
        files = []
        for sec in sections:
            files.extend(sorted((BASE_DIR / "content" / sec).rglob("index.md")))

    total_conv, total_skip, total_files = 0, 0, 0
    for f in files:
        if not f.exists():
            print(f"skip (missing): {f}")
            continue
        rel = f.relative_to(BASE_DIR) if f.is_absolute() else f
        # Quick pre-check: does the file contain any code fence at all?
        if "```" not in f.read_text(encoding="utf-8"):
            continue
        print(f"\n{rel}")
        c, s = process_file(f, api_key, args.dry_run)
        total_conv += c
        total_skip += s
        if c or s:
            total_files += 1

    print(f"\nDone: {total_conv} converted, {total_skip} skipped, "
          f"across {total_files} files")


if __name__ == "__main__":
    main()
