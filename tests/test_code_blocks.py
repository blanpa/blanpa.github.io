"""Every code sample in a post has to at least parse.

Readers copy these blocks. A JSON sample with a trailing comma or a YAML
sample with a bad indent is worse than no sample at all, and neither Hugo nor
a spell-check will ever notice.

Snippets are illustrative, so this checks syntax only — not that names are
defined or imports are present.
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import tomllib

import pytest
import yaml

from conftest import REPO

# Line comments are a documentation idiom in JSON samples ("// UDT member").
# Strip them before parsing rather than banning them.
JSON_LINE_COMMENT = re.compile(r'(?<!:)//(?![^"\n]*")[^\n]*')

ELIDED = "..."


def test_json_parses(json_block):
    text = json_block.code
    # Some samples show the request line above the body: "GET /v1/objects".
    text = re.sub(r"\A\s*(GET|POST|PUT|DELETE)\s+\S+[^\n]*\n", "", text)
    text = JSON_LINE_COMMENT.sub("", text)
    if ELIDED in text:
        pytest.skip("sample elides part of the payload")
    # A block may show a request body and a response separated by a blank line.
    for chunk in [c for c in re.split(r"\n\s*\n", text) if c.strip()]:
        try:
            json.loads(chunk)
        except json.JSONDecodeError as exc:
            pytest.fail(f"{json_block}: invalid JSON — {exc}")


def test_yaml_parses(yaml_block):
    try:
        list(yaml.safe_load_all(yaml_block.code))
    except yaml.YAMLError as exc:
        pytest.fail(f"{yaml_block}: invalid YAML — {exc}")


def test_toml_parses(toml_block):
    try:
        tomllib.loads(toml_block.code)
    except tomllib.TOMLDecodeError as exc:
        pytest.fail(f"{toml_block}: invalid TOML — {exc}")


def test_python_parses(python_block):
    code = python_block.code
    # Heredoc wrappers around an embedded script (python3 << 'PYEOF' ... PYEOF).
    code = re.sub(r"\A[^\n]*<<\s*'?\w+'?\n", "", code)
    code = re.sub(r"\n\w+EOF\b[^\n]*\Z", "", code)
    code = re.sub(r"^#\s.*$", "", code, flags=re.M)
    if ELIDED in code:
        pytest.skip("sample elides part of the script")
    try:
        ast.parse(code)
    except SyntaxError as exc:
        pytest.fail(f"{python_block}: invalid Python — line {exc.lineno}: {exc.msg}")


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_javascript_parses(js_block):
    code = js_block.code
    if ELIDED in code:
        pytest.skip("sample elides part of the script")
    # Node-RED function-node bodies use bare `msg`/`node`/`flow` and top-level
    # await/return; wrap them so those are syntactically legal.
    wrapped = (
        "(async function (msg, node, flow, context, global, RED) {\n" + code + "\n});"
    )
    result = subprocess.run(
        ["node", "--check", "-"], input=wrapped, capture_output=True, text=True
    )
    if result.returncode != 0:
        # ES modules can't be wrapped in a function — retry as-is.
        result = subprocess.run(
            ["node", "--input-type=module", "--check", "-"],
            input=code,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, f"{js_block}: invalid JavaScript —\n{result.stderr}"


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not installed")
def test_shell_parses(shell_block):
    code = shell_block.code
    if ELIDED in code or "<<" in code:
        pytest.skip("sample elides part of the script, or embeds a heredoc")
    result = subprocess.run(["bash", "-n"], input=code, capture_output=True, text=True)
    assert result.returncode == 0, f"{shell_block}: invalid shell —\n{result.stderr}"


def test_fence_language_is_one_we_recognise(block):
    """A typo in the fence language ("javasript") silently drops highlighting."""
    known = {
        "", "text", "console", "diff", "http", "graphql", "dbc", "gitignore",
        "ini", "markdown", "dockerfile", "mermaid", "json", "jsonc", "yaml",
        "yml", "toml", "python", "javascript", "js", "bash", "sh", "shell",
        "sql", "go", "xml", "html", "css",
    }
    assert block.lang in known, (
        f"{block}: unrecognised fence language {block.lang!r} — fix the typo, "
        f"or add it to the known set in this test"
    )


# The CAN post carries a DBC alongside a table of frames it recorded off a
# real bus, and a Python decoder for the same frames. All three describe one
# frame layout, and nothing forces them to agree — the DBC shipped with the
# signals declared Intel byte order while the prose, the table and the decoder
# all read big-endian, so the file decoded 41993 RPM where the article said
# 2468. cantools would catch this in one line, but tests/requirements.txt is
# deliberately stdlib-only, and the subset of DBC needed here is small.
DBC_SIGNAL = re.compile(
    r"^\s*SG_\s+(?P<name>\w+)\s*:\s*(?P<start>\d+)\|(?P<length>\d+)"
    r"@(?P<order>[01])(?P<sign>[+-])\s*\((?P<scale>[-\d.]+),(?P<offset>[-\d.]+)\)"
)


def _decode_motorola(data: bytes, start: int, length: int) -> int:
    """DBC big-endian (@0): `start` is the MSB, numbered so that byte n holds
    bits n*8+7 (MSB) down to n*8 (LSB)."""
    value = 0
    bit = start
    for _ in range(length):
        byte, offset = divmod(bit, 8)
        value = (value << 1) | ((data[byte] >> offset) & 1)
        bit = bit - 1 if offset else bit + 15
    return value


def test_can_dbc_decodes_the_posts_own_capture():
    post = REPO / "content/blog/can-bus-reverse-engineering-node-red/index.md"
    text = post.read_text(encoding="utf-8")

    dbc = re.search(r"^```dbc\n(.*?)^```", text, re.S | re.M)
    assert dbc, "the CAN post no longer has a dbc block"
    signals = {m["name"]: m for m in map(DBC_SIGNAL.match, dbc.group(1).splitlines()) if m}
    for name in ("MotorRPM", "DriveState"):
        assert name in signals, f"DBC no longer declares {name}"
        assert signals[name]["order"] == "0", (
            f"{name} is declared @{signals[name]['order']} (Intel). The post's "
            f"analysis, capture table and Python decoder are all big-endian."
        )

    # "| Motor 1000 RPM FWD | `00 00 03 E8 00 00 00 01` |"
    rows = re.findall(r"\|\s*Motor\s+(\d+) RPM (FWD|REV)\s*\|\s*`([0-9A-F ]+)`\s*\|", text)
    assert len(rows) >= 3, "the capture table in the CAN post has moved or changed shape"
    for rpm, direction, frame in rows:
        data = bytes.fromhex(frame.replace(" ", ""))
        got = _decode_motorola(data, int(signals["MotorRPM"]["start"]),
                               int(signals["MotorRPM"]["length"]))
        assert got == int(rpm), (
            f"DBC decodes {got} RPM from {frame}, but the table says {rpm}"
        )
        state = _decode_motorola(data, int(signals["DriveState"]["start"]),
                                 int(signals["DriveState"]["length"]))
        assert state == (1 if direction == "FWD" else 2), (
            f"DBC decodes DriveState {state} from {frame}, but the table says {direction}"
        )
