"""The technical claims in the posts have to hold up.

These are the checks that actually earn their keep: arithmetic stated in
prose, protocol constants, and the domain formulas the posts teach. A wrong
port number or a fault frequency that doesn't follow from the bearing
geometry is the kind of error that survives every proofread and then gets
copied into somebody's plant.

Each test names the claim it guards, so a failure tells you which sentence to
go fix.
"""

from __future__ import annotations

import math
import re
import shutil
import subprocess

import pytest

# --------------------------------------------------------------------------
# Protocol constants
# --------------------------------------------------------------------------

# Every TCP/UDP port the site legitimately talks about. A number outside this
# set is far more likely to be a typo (4804 for 4840) than a new protocol.
KNOWN_PORTS = {
    22: "SSH",
    80: "HTTP",
    102: "S7comm / ISO-TSAP",
    443: "HTTPS",
    502: "Modbus TCP",
    503: "Modbus TCP (non-standard, called out as such)",
    1880: "Node-RED",
    1883: "MQTT",
    2222: "EtherNet/IP implicit I/O (UDP)",
    3000: "Grafana",
    4222: "NATS client",
    4840: "OPC-UA",
    5432: "PostgreSQL / TimescaleDB",
    6222: "NATS cluster",
    6443: "Kubernetes API",
    7422: "NATS leaf nodes",
    8081: "Schema Registry",
    8222: "NATS monitoring",
    8883: "MQTT over TLS",
    9001: "Mosquitto WebSocket / Portainer agent",
    9092: "Kafka",
    9443: "Portainer",
    44818: "EtherNet/IP explicit messaging",
    49320: "KEPServerEX OPC-UA",
    12345: "placeholder in the legal notice address",
}

PORT_CLAIM = re.compile(
    r"(?:port\s+\*{0,2}|tcp[:/]|udp[:/]|TCP:|UDP:)\s*(\d{2,5})\b", re.I
)

# Sparkplug B message types (Sparkplug 3.0, section "Topic Namespace").
SPARKPLUG_TYPES = {"NBIRTH", "DBIRTH", "NDATA", "DDATA", "NCMD", "DCMD",
                   "NDEATH", "DDEATH", "STATE"}
SPARKPLUG_TOKEN = re.compile(r"\b([ND](?:BIRTH|DATA|CMD|DEATH)S?)\b")


def test_port_numbers_are_known(page):
    """Guards against a mistyped port in prose, config, or a diagram."""
    unknown = {}
    for match in PORT_CLAIM.finditer(page.body):
        port = int(match.group(1))
        if port not in KNOWN_PORTS:
            line = page.line_of(match.start())
            unknown.setdefault(port, []).append(line)
    assert not unknown, (
        f"{page.rel}: port(s) not in the known-port table: "
        + ", ".join(f"{p} (line {ls[0]})" for p, ls in sorted(unknown.items()))
        + " — fix the typo, or add the port to KNOWN_PORTS in this test"
    )


def test_sparkplug_message_types_are_real(page):
    bad = set()
    for match in SPARKPLUG_TOKEN.finditer(page.body):
        token = match.group(1)
        if token not in SPARKPLUG_TYPES:
            bad.add(token)
    assert not bad, f"{page.rel}: not Sparkplug message types: {sorted(bad)}"


# --------------------------------------------------------------------------
# Arithmetic stated in prose
# --------------------------------------------------------------------------

HEX_CLAIM = re.compile(r"0x([0-9A-Fa-f]{2,8})\s*=\s*([\d,]+)\s*(?:decimal\b)?")


def test_hex_to_decimal_claims(page):
    """"0x09A4 = 2468 decimal" — the kind of thing that is right until it is
    edited."""
    wrong = []
    for match in HEX_CLAIM.finditer(page.body):
        hex_value = int(match.group(1), 16)
        stated = int(match.group(2).replace(",", ""))
        if hex_value != stated:
            wrong.append(
                f"line {page.line_of(match.start())}: 0x{match.group(1)} is "
                f"{hex_value}, post says {stated}"
            )
    assert not wrong, f"{page.rel}: " + "; ".join(wrong)


def _post(posts, slug):
    for post in posts:
        if post.slug == slug:
            return post
    pytest.skip(f"post {slug} not found")


def test_vibration_burst_size(posts):
    """predictive-maintenance: '25.6 kHz x 2 bytes x 10 seconds = 512 KB'."""
    post = _post(posts, "predictive-maintenance-node-red")
    burst_bytes = 25_600 * 2 * 10
    assert burst_bytes == 512_000
    assert "512 KB per burst" in post.body, (
        "the burst-size claim changed; 25.6 kHz x 2 bytes x 10 s is "
        f"{burst_bytes / 1000:.0f} KB"
    )
    # 100 machines, one burst per hour — the post rounds, so allow 10%.
    stated = re.search(r"~(\d+)\s*MB/hour", post.body)
    assert stated, "the hourly volume claim is gone — update this test"
    actual_mb = burst_bytes * 100 / 1e6
    assert float(stated.group(1)) == pytest.approx(actual_mb, rel=0.1), (
        f"100 machines x {burst_bytes / 1000:.0f} KB is {actual_mb:.1f} MB/hour, "
        f"post says ~{stated.group(1)} MB/hour"
    )


def test_bearing_fault_frequencies_follow_the_geometry(posts):
    """predictive-maintenance publishes BPFO/BPFI/BSF/FTF for a 6205 at
    1800 RPM. Whatever the geometry, two identities must hold:

        BPFO + BPFI = N x shaft frequency
        FTF         = BPFO / N

    They are what make the four numbers one consistent bearing rather than
    four numbers that look plausible.
    """
    post = _post(posts, "predictive-maintenance-node-red")
    block = next(
        (b for b in post.blocks if "bearing_6205_1800rpm" in b.code), None
    )
    assert block, "the bearing frequency table is gone — update this test"

    values = dict(
        (m.group(1), float(m.group(2)))
        for m in re.finditer(r'"(\w+)":\s*([\d.]+)', block.code)
    )
    n_balls = 9  # 6205 has 9 rolling elements
    shaft_hz = 1800 / 60

    assert values["BPFO"] + values["BPFI"] == pytest.approx(n_balls * shaft_hz, abs=1.0), (
        f"BPFO + BPFI should be {n_balls} x {shaft_hz:.0f} Hz = "
        f"{n_balls * shaft_hz:.0f} Hz, got "
        f"{values['BPFO']} + {values['BPFI']} = {values['BPFO'] + values['BPFI']}"
    )
    assert values["FTF"] == pytest.approx(values["BPFO"] / n_balls, abs=0.3), (
        f"FTF should be BPFO/{n_balls} = {values['BPFO'] / n_balls:.2f} Hz, "
        f"post says {values['FTF']}"
    )
    for k in (2, 3):
        key = f"{k}x_BPFO"
        if key in values:
            assert values[key] == pytest.approx(k * values["BPFO"], abs=1.0), (
                f"{key} should be {k * values['BPFO']:.0f} Hz, got {values[key]}"
            )


def test_nats_per_machine_bandwidth_adds_up(posts):
    """nats-edge-to-cloud: the per-machine table has to sum to its own total."""
    post = _post(posts, "nats-edge-to-cloud-pipeline")
    rows = re.findall(r"^\|[^|]*\|[^|]*\|[^|]*\|\s*([\d.]+)\s*B/s\s*\|", post.body, re.M)
    assert rows, "per-machine bandwidth table not found — update this test"
    total = sum(float(value) for value in rows)
    stated = re.search(r"~(\d+)\s*B/s\s*≈\s*1\s*KB/s", post.body)
    assert stated, "the stated per-machine total is gone — update this test"
    assert total == pytest.approx(float(stated.group(1)), abs=5), (
        f"per-machine rows sum to {total} B/s, post states {stated.group(1)} B/s"
    )


def test_nats_edge_buffer_math(posts):
    """nats-edge-to-cloud: the offline-buffer calculation, and the sentence
    introducing it, must use the same throughput."""
    post = _post(posts, "nats-edge-to-cloud-pipeline")
    calc = re.search(
        r"(\d+)\s*GB\s*/\s*(\d+)\s*KB/s\s*≈\s*([\d,]+)\s*seconds\s*≈\s*(\d+)\s*hours",
        post.body,
    )
    assert calc, "the edge buffer calculation is gone — update this test"
    gb, kbs, seconds, hours = (
        int(calc.group(1)),
        int(calc.group(2)),
        int(calc.group(3).replace(",", "")),
        int(calc.group(4)),
    )
    assert gb * 1e9 / (kbs * 1e3) == pytest.approx(seconds, rel=0.01), (
        f"{gb} GB / {kbs} KB/s is {gb * 1e9 / (kbs * 1e3):.0f} s, "
        f"post says {seconds} s"
    )
    assert seconds / 3600 == pytest.approx(hours, abs=1), (
        f"{seconds} s is {seconds / 3600:.1f} h, post says {hours} h"
    )

    intro = re.search(
        r"With a (\d+) GB JetStream store and (\d+) machines at (\d+) KB/s compressed",
        post.body,
    )
    assert intro, "the sentence introducing the buffer calculation changed"
    assert int(intro.group(1)) == gb, "the store size in the text and the sum disagree"
    assert int(intro.group(3)) == kbs, (
        f"the text says {intro.group(3)} KB/s compressed but the calculation "
        f"divides by {kbs} KB/s"
    )


def test_tables_with_a_total_row_add_up(page):
    """Any markdown table with a **Total** row must actually total."""
    problems = []
    for table in re.findall(r"(?:^\|.*\|\s*$\n)+", page.body, re.M):
        rows = [r for r in table.strip().split("\n")]
        total_row = next((r for r in rows if re.search(r"\*\*Total\*\*", r)), None)
        if not total_row:
            continue
        def numbers(row):
            return [
                int(cell.replace(",", "").replace("**", "").strip())
                for cell in row.strip("|").split("|")
                if re.fullmatch(r"\s*\*{0,2}[\d,]+\*{0,2}\s*", cell)
            ]
        stated = numbers(total_row)
        if len(stated) != 1:
            continue  # ambiguous or multi-column total; not our business
        body_rows = [
            r for r in rows
            if r is not total_row and not re.match(r"^\|[\s:|-]+\|$", r)
        ]
        columns = [numbers(r) for r in body_rows]
        columns = [c for c in columns if len(c) == 1]
        if len(columns) < 2:
            continue
        computed = sum(c[0] for c in columns)
        if computed != stated[0]:
            problems.append(f"rows sum to {computed}, table states {stated[0]}")
    assert not problems, f"{page.rel}: " + "; ".join(problems)


NATS_TOP_LEVEL_BLOCK = re.compile(r"^(\w+)\s*\{", re.M)
NATS_BLOCKS = {"leafnodes", "jetstream", "authorization", "cluster", "websocket",
               "mqtt", "gateway", "tls", "accounts", "resolver_preload"}


def test_nats_config_declares_each_block_once(page):
    """A repeated top-level block in a NATS config silently *replaces* the
    earlier one — `nats-server -t` still calls the file valid, and a gateway
    whose second `leafnodes {}` block dropped `remotes` then never connects.
    """
    problems = []
    for block in page.blocks:
        if "nats" not in block.code and "leafnodes" not in block.code:
            continue
        names = [n for n in NATS_TOP_LEVEL_BLOCK.findall(block.code) if n in NATS_BLOCKS]
        duplicates = {n for n in names if names.count(n) > 1}
        if duplicates:
            problems.append(f"{block}: block(s) declared twice: {sorted(duplicates)}")
    assert not problems, f"{page.rel}: " + "; ".join(problems)


# --------------------------------------------------------------------------
# Cross-post consistency
# --------------------------------------------------------------------------

def test_no_superseded_dependency_names(page):
    """Names the site got wrong once, so it does not get them wrong again.

    The Kafka suite's native backend is @confluentinc/kafka-javascript.
    `node-rdkafka` is a different package by a different author — naming it
    sends a reader to install the wrong thing.
    """
    banned = {
        "node-rdkafka": "@confluentinc/kafka-javascript (the suite's actual native backend)",
    }
    found = {
        name: hint for name, hint in banned.items()
        if re.search(rf"(?<![\w/@-]){re.escape(name)}(?![\w-])", page.body)
    }
    assert not found, f"{page.rel}: " + "; ".join(
        f"{name} — use {hint}" for name, hint in found.items()
    )


def test_own_package_names_are_real(pages, npm_packages):
    """A typo in one's own package name sends readers to a 404 on npm."""
    known = {entry["pkg"] for entry in npm_packages}
    # Third-party packages the posts legitimately reference.
    external = {
        "node-red-contrib-modbus",
        "node-red-contrib-opcua",
        "node-red-contrib-opcua-suite",
        "node-red-contrib-pythonshell",
        "node-red-contrib-influxdb",
        "node-red-contrib-socketcan",
        "node-red-contrib-nats",
        "node-red-contrib-nats-streaming",
        "node-red-contrib-mqtt-sparkplug-plus",
        "node-red-contrib-healthcheck",
        "node-red-contrib-mynode",
    }
    bad = {}
    for page in pages:
        for match in re.finditer(r"node-red-contrib-[a-z0-9-]+", page.body):
            name = match.group(0).rstrip("-")
            if name not in known and name not in external:
                bad.setdefault(name, page.rel)
    assert not bad, (
        f"package names that are neither in data/npm_packages.yml nor a known "
        f"third-party package: {bad}"
    )


def test_project_npm_mapping_resolves(pages, npm_packages):
    """Project cards show a download count looked up by the page's `npm:`
    field. A typo there renders nothing at all — the card silently loses its
    evidence rather than failing — so check the name exists."""
    known = {entry["pkg"] for entry in npm_packages}
    wrong = {
        page.rel: page.meta["npm"]
        for page in pages
        if page.meta.get("npm") and page.meta["npm"] not in known
    }
    assert not wrong, (
        f"`npm:` values with no entry in data/npm_packages.yml: {wrong}"
    )


def test_every_project_declares_its_package(pages):
    """Every project here ships as an npm package; a missing `npm:` means a
    card without a download count."""
    missing = [
        page.rel for page in pages
        if page.section == "projects" and not page.meta.get("npm")
    ]
    assert not missing, f"project pages without an `npm:` field: {missing}"


def test_shared_figures_agree_across_posts(pages):
    """A number quoted in two posts must be the same number in both."""
    claims = {
        "OPC-UA specification length": re.compile(r"spec(?:ification)? is ([\d,]+)\+? pages"),
        "i3x endpoint count": re.compile(r"\*\*(\d+) API endpoints\*\*"),
    }
    for label, pattern in claims.items():
        found = {}
        for page in pages:
            for match in pattern.finditer(page.body):
                found.setdefault(match.group(1).replace(",", ""), []).append(page.slug)
        assert len(found) <= 1, f"{label} is quoted inconsistently: {found}"


# --------------------------------------------------------------------------
# The code samples produce the results the prose claims
# --------------------------------------------------------------------------

def _run_node(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["node", "--input-type=commonjs", "-"],
        input=script,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_modbus_decoding_helpers_produce_documented_values(posts):
    """The Modbus post documents '65436 -> -10.0 degC' and the four word
    orders. Run its own helpers and check."""
    post = _post(posts, "modbus-node-red")
    int16 = next((b for b in post.blocks if "function toInt16" in b.code), None)
    float32 = next((b for b in post.blocks if "function toFloat32" in b.code), None)
    assert int16 and float32, "the Modbus decoding helpers moved — update this test"

    script = (
        int16.code.replace("const temp =", "//")
        + "\n"
        + float32.code
        + """
const assert = require("assert");
// Documented in the post: 65436 -> -10.0 degC after the x0.1 scale.
assert.strictEqual(Number((toInt16(65436) * 0.1).toFixed(1)), -10.0);
assert.strictEqual(toInt16(32767), 32767);
assert.strictEqual(toInt16(32768), -32768);
assert.strictEqual(toInt16(427), 427);

// 42.7 as IEEE-754 single precision is 0x422ACCCD.
const hi = 0x422A, lo = 0xCCCD;
assert.ok(Math.abs(toFloat32([hi, lo], 0, "ABCD") - 42.7) < 1e-4,
          "ABCD (big-endian) must decode the standard layout");
assert.ok(Math.abs(toFloat32([lo, hi], 0, "CDAB") - 42.7) < 1e-4,
          "CDAB must undo a word swap");
console.log("ok");
"""
    )
    result = _run_node(script)
    assert result.returncode == 0, f"Modbus helpers failed:\n{result.stderr}"


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_temperature_node_matches_its_own_test_expectations(posts):
    """The CI/CD post ships a converter node and a test suite asserting
    100C -> 212F, 32F -> 0C and 0C -> 32F. Run the node against them."""
    post = _post(posts, "cicd-node-red-flows")
    node = next(
        (b for b in post.blocks if "TemperatureConvertNode" in b.code), None
    )
    assert node, "the temperature-convert node moved — update this test"

    expectations = re.findall(
        r'unit:\s*"(c_to_f|f_to_c)".*?receive\(\{\s*payload:\s*(-?[\d.]+)\s*\}\)',
        post.body,
        re.S,
    )
    equals = re.findall(r"expect\(msg\.payload\)\.to\.equal\((-?[\d.]+)\)", post.body)
    assert expectations and equals, "the documented conversions moved"

    script = (
        """
const assert = require("assert");
const RED = {
  nodes: {
    createNode(node, config) { node.on = (evt, fn) => { node._handler = fn; }; },
    registerType(name, ctor) { RED._ctor = ctor; },
  },
};
"""
        + node.code.replace("module.exports = function(RED)", "const factory = function(RED)")
        + """
factory(RED);
function convert(unit, value) {
  const node = {};
  RED.nodes.createNode(node, {});
  const instance = new RED._ctor({ unit });
  return null;
}
// Drive the registered constructor directly.
let out = null;
const node = { on(evt, fn) { this._fn = fn; }, error() {} };
RED.nodes.createNode = function (n, config) { Object.assign(n, node); n.on = node.on.bind(n); };
function run(unit, payload) {
  const n = {};
  RED.nodes.createNode(n, { unit });
  RED._ctor.call(n, { unit });
  let result;
  n._fn({ payload }, (msg) => { result = msg.payload; }, () => {});
  return result;
}
assert.strictEqual(run("c_to_f", 100), 212, "100 C must be 212 F");
assert.strictEqual(run("f_to_c", 32), 0, "32 F must be 0 C");
assert.strictEqual(run("c_to_f", 0), 32, "0 C must be 32 F");
console.log("ok");
"""
    )
    result = _run_node(script)
    assert result.returncode == 0, (
        f"the converter in the post does not produce the values its own test "
        f"section claims:\n{result.stderr}"
    )
