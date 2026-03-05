---
title: "Lessons Learned: Publishing 5 npm Packages for Industrial IoT"
tags: [node-red, javascript, iiot]
description: "What I learned building and maintaining open-source Node-RED packages — from first commit to 2,000+ downloads."
date: 2026-05-23
series: ["IIoT"]
---

Over the past two years, I've published five npm packages for Node-RED, all targeting the IIoT space. Some took off, some needed multiple rewrites, and all taught me things I couldn't have learned from tutorials alone. This post is the honest rundown: what worked, what didn't, and what I'd do differently.

---

## The Five Packages

| Package | Purpose | Tests | Downloads |
|---------|---------|-------|-----------|
| **node-red-contrib-condition-monitoring** | Vibration analysis, FFT, alarm thresholds | 135 | 2,100+ |
| **node-red-contrib-nats-suite** | NATS messaging (pub/sub, request/reply, JetStream) | 48 | 900+ |
| **node-red-contrib-opcua-suite** | OPC-UA client with browse, read, write, subscribe | 62 | 1,400+ |
| **node-red-contrib-clab-interfaces** | Interfaces for the Siemens cLab platform | 28 | 350+ |
| **node-red-contrib-i3x** | CESMII i3x open manufacturing API | 41 | 600+ |

Each one started the same way: I needed something for a project, couldn't find a good existing solution, and built it myself.

---

## Architecture Decisions

### Monorepo vs Separate Repos

I started with separate repos for each package. After the third package, I considered a monorepo but decided against it. Here's why:

```
Monorepo (Lerna / npm workspaces):
  ┌──────────────────────────────────┐
  │  packages/                       │
  │  ├── condition-monitoring/       │
  │  ├── nats-suite/                 │
  │  ├── opcua-suite/                │
  │  ├── clab-interfaces/            │
  │  └── i3x/                        │
  │                                  │
  │  ✓ Shared dev dependencies       │
  │  ✓ Cross-package changes atomic  │
  │  ✗ Complex CI/CD                 │
  │  ✗ Intimidating for contributors │
  │  ✗ Version coupling risk         │
  └──────────────────────────────────┘

Separate repos:
  ┌─────────────────────┐  ┌─────────────────────┐
  │ condition-monitoring│  │ nats-suite          │
  │ v1.3.2              │  │ v0.8.1              │
  │ Own CI, own issues  │  │ Own CI, own issues  │
  └─────────────────────┘  └─────────────────────┘
  ┌─────────────────────┐  ┌─────────────────────┐
  │ opcua-suite         │  │ i3x                 │
  │ v0.5.0              │  │ v0.3.0              │
  └─────────────────────┘  └─────────────────────┘

  ✓ Simple CI/CD per package
  ✓ Independent versioning
  ✓ Lower contributor barrier
  ✗ Duplicated boilerplate
  ✗ Shared fixes need N commits
```

**My recommendation:** Use separate repos unless your packages genuinely share significant code. IIoT packages rarely do — a NATS client has nothing in common with a vibration analysis module.

### When to Split a Node into Multiple Nodes

My first version of `opcua-suite` had a single "OPC-UA" node that tried to do everything: browse, read, write, subscribe, monitor. It was a mess — the configuration panel had 30 fields.

I split it into focused nodes:

```
Before (v0.1):                     After (v0.3):
┌──────────────────────┐           ┌───────────────────┐
│   opcua-all-in-one   │           │ opcua-connection  │ (config node)
│                      │           ├───────────────────┤
│  Browse? Read? Write?│           │ opcua-browse      │
│  Subscribe? Monitor? │           │ opcua-read        │
│                      │           │ opcua-write       │
│  30 config fields    │           │ opcua-subscribe   │
│  Confused users      │           │ opcua-method-call │
└──────────────────────┘           └───────────────────┘
                                   Each: 5-8 config fields
                                   Clear purpose
```

**Rule of thumb:** If a node needs a dropdown to select its mode of operation, split it. Each node should do one thing well.

### Config Nodes for Connections

Every package that connects to an external service (NATS broker, OPC-UA server, i3x API) uses a **config node** for the connection. The config node manages the connection lifecycle, and operation nodes reference it:

```
┌─────────────────────────────────────────┐
│  Node-RED Flow                          │
│                                         │
│  ┌────────────┐    ┌────────────┐       │
│  │ nats-pub   ├───►│ nats-conn  │       │
│  └────────────┘    │ (config)   │       │
│                    │            │       │
│  ┌────────────┐    │ host: ...  │       │
│  │ nats-sub   ├───►│ port: ...  │       │
│  └────────────┘    │ creds: ... │       │
│                    └──────┬─────┘       │
│  ┌────────────┐           │             │
│  │ nats-req   ├───────────┘             │
│  └────────────┘                         │
│                                         │
│  3 operation nodes, 1 shared connection │
└─────────────────────────────────────────┘
```

This pattern prevents connection sprawl (ten nodes opening ten separate TCP connections) and centralizes credential management.

---

## Testing

### node-red-node-test-helper

The `node-red-node-test-helper` package is the official way to unit test Node-RED nodes. It creates a lightweight Node-RED runtime in memory, loads your nodes, and lets you send messages and check outputs.

### Testing Industrial Protocols is Hard

The challenge with IIoT nodes: they interact with real hardware and services. You can't run an OPC-UA server in CI (well, you can, but it's brittle). You can't plug in a CAN bus adapter on GitHub Actions.

My approach: **three testing layers**.

```
┌────────────────────────────────────────┐
│  Layer 1: Pure Logic Tests (fast)      │
│  - Data parsing, encoding, validation  │
│  - Math (FFT, RMS, thresholds)         │
│  - No external dependencies            │
│  - 80% of tests live here              │
├────────────────────────────────────────┤
│  Layer 2: Node Behavior Tests (medium) │
│  - node-red-node-test-helper           │
│  - Mocked connections                  │
│  - Input/output message validation     │
│  - Status and error handling           │
├────────────────────────────────────────┤
│  Layer 3: Integration Tests (slow)     │
│  - Docker Compose with real services   │
│  - NATS server, OPC-UA simulator       │
│  - End-to-end message flow             │
│  - Run manually or nightly in CI       │
└────────────────────────────────────────┘
```

### Example: Testing the Condition Monitoring FFT Node

The condition monitoring package does real signal processing — Fast Fourier Transform, RMS calculation, threshold-based alarms. The math must be correct.

```javascript
// test/fft_spec.js
const { expect } = require("chai");
const { computeFFT, findPeaks, calculateRMS } = require("../lib/signal");

describe('Signal Processing', function() {
    describe('FFT', function() {
        it('should detect a 50Hz component in a 1kHz sampled signal', function() {
            const sampleRate = 1000;
            const duration = 1;
            const samples = [];

            for (let i = 0; i < sampleRate * duration; i++) {
                const t = i / sampleRate;
                samples.push(Math.sin(2 * Math.PI * 50 * t));
            }

            const result = computeFFT(samples, sampleRate);
            const peaks = findPeaks(result.magnitudes, result.frequencies, {
                threshold: 0.1
            });

            expect(peaks).to.have.length(1);
            expect(peaks[0].frequency).to.be.closeTo(50, 1);
        });

        it('should detect multiple frequency components', function() {
            const sampleRate = 1000;
            const samples = [];

            for (let i = 0; i < sampleRate; i++) {
                const t = i / sampleRate;
                samples.push(
                    1.0 * Math.sin(2 * Math.PI * 25 * t) +
                    0.5 * Math.sin(2 * Math.PI * 75 * t) +
                    0.3 * Math.sin(2 * Math.PI * 150 * t)
                );
            }

            const result = computeFFT(samples, sampleRate);
            const peaks = findPeaks(result.magnitudes, result.frequencies, {
                threshold: 0.05
            });

            expect(peaks).to.have.length(3);
            expect(peaks[0].frequency).to.be.closeTo(25, 1);
            expect(peaks[1].frequency).to.be.closeTo(75, 1);
            expect(peaks[2].frequency).to.be.closeTo(150, 1);
        });
    });

    describe('RMS', function() {
        it('should calculate RMS of a sine wave', function() {
            const samples = [];
            for (let i = 0; i < 1000; i++) {
                samples.push(Math.sin(2 * Math.PI * i / 1000));
            }
            const rms = calculateRMS(samples);
            expect(rms).to.be.closeTo(1 / Math.sqrt(2), 0.01);
        });

        it('should return 0 for all-zero input', function() {
            const rms = calculateRMS(new Array(100).fill(0));
            expect(rms).to.equal(0);
        });
    });
});
```

### Mocking Industrial Protocols

For node behavior tests, I mock the protocol clients:

```javascript
// test/nats-publish_spec.js
const helper = require("node-red-node-test-helper");
const sinon = require("sinon");
const natsNode = require("../nodes/nats-publish");
const natsConnNode = require("../nodes/nats-connection");

helper.init(require.resolve('node-red'));

describe('nats-publish Node', function() {
    let connectStub;

    beforeEach(function() {
        connectStub = sinon.stub().resolves({
            publish: sinon.stub(),
            drain: sinon.stub().resolves(),
            close: sinon.stub().resolves(),
            status: sinon.stub().returns({ data: 'connected' }),
        });
    });

    afterEach(function() {
        helper.unload();
        sinon.restore();
    });

    it('should publish a message to the configured subject', function(done) {
        const flow = [
            {
                id: "conn1",
                type: "nats-connection",
                name: "Test NATS",
                server: "nats://localhost:4222"
            },
            {
                id: "n1",
                type: "nats-publish",
                name: "Publish",
                connection: "conn1",
                subject: "factory.line1.status",
                wires: []
            }
        ];

        helper.load([natsConnNode, natsNode], flow, function() {
            const n1 = helper.getNode("n1");
            const conn = helper.getNode("conn1");

            conn.client = connectStub();

            n1.receive({ payload: { status: "running" } });

            setTimeout(function() {
                try {
                    expect(conn.client.publish.calledOnce).to.be.true;
                    done();
                } catch(err) {
                    done(err);
                }
            }, 100);
        });
    });
});
```

### Test Count: 135 Tests in Condition Monitoring

The condition monitoring package has the most tests because it does the most math. Here's the breakdown:

```
test/
├── fft_spec.js              ── 28 tests (FFT accuracy, edge cases)
├── rms_spec.js              ── 12 tests (RMS calculation)
├── threshold_spec.js        ── 24 tests (alarm logic)
├── envelope_spec.js         ── 18 tests (envelope analysis)
├── trend_spec.js            ── 15 tests (trend detection)
├── node_behavior_spec.js    ── 22 tests (Node-RED node I/O)
├── config_validation_spec.js── 10 tests (configuration checks)
└── integration_spec.js      ──  6 tests (end-to-end flow)
                             ─────
                              135 total
```

Running them:

```bash
$ npm test

  Signal Processing
    FFT
      ✓ should detect a 50Hz component (12ms)
      ✓ should detect multiple frequency components (15ms)
      ✓ should handle power-of-2 sample sizes (8ms)
      ✓ should zero-pad non-power-of-2 inputs (11ms)
      ...

  Threshold Alarms
    ✓ should trigger WARNING when value exceeds warning threshold
    ✓ should trigger CRITICAL when value exceeds critical threshold
    ✓ should clear alarm when value returns below threshold
    ✓ should support hysteresis to prevent alarm flapping
    ...

  135 passing (2.8s)
```

---

## Documentation

### README as Marketing

Your README is the first thing anyone sees. For IIoT packages, the README needs to answer three questions immediately:

1. **What does this do?** (one sentence)
2. **How do I install it?** (one command)
3. **What does it look like?** (screenshot or example)

```markdown
# node-red-contrib-condition-monitoring

Vibration analysis and condition monitoring nodes for Node-RED.
FFT, RMS, envelope analysis, and threshold-based alarms — 
built for predictive maintenance on industrial machines.

## Install

\`\`\`bash
cd ~/.node-red
npm install node-red-contrib-condition-monitoring
\`\`\`

## Nodes

| Node | Purpose |
|------|---------|
| **fft-analysis** | Compute FFT spectrum from time-domain samples |
| **rms-monitor** | Calculate running RMS with configurable window |
| **threshold-alarm** | Trigger alarms based on configurable thresholds |
| **envelope-analysis** | Bearing fault detection via envelope analysis |
| **trend-detect** | Detect upward/downward trends over time |

## Example Flow

[Screenshot here]
[Importable flow JSON here]
```

### Example Flows

Every package includes at least one importable example flow. Node-RED has a built-in example import feature — if you put example flows in the right directory, users can import them from `Import → Examples → your-package-name`:

```
your-package/
├── examples/
│   ├── basic-fft-analysis.json
│   ├── multi-axis-monitoring.json
│   └── mqtt-to-alarm-pipeline.json
├── nodes/
│   └── ...
└── package.json
```

In `package.json`:

```json
{
  "node-red": {
    "version": ">=2.0.0",
    "nodes": {
      "fft-analysis": "nodes/fft-analysis.js"
    },
    "examples": {
      "basic-fft": "examples/basic-fft-analysis.json",
      "multi-axis": "examples/multi-axis-monitoring.json",
      "mqtt-alarm": "examples/mqtt-to-alarm-pipeline.json"
    }
  }
}
```

### Clear API Documentation

For every node, I document:

- **Inputs:** what `msg` properties are expected
- **Outputs:** what `msg` properties are set
- **Configuration:** what each config field means
- **Errors:** what can go wrong and how to fix it

This goes in the node's HTML help panel (the sidebar in the Node-RED editor) and in the README.

---

## Publishing

### npm Publish Workflow

My publishing checklist:

```
1. Update version in package.json (follow semver)
2. Update CHANGELOG.md
3. Run full test suite: npm test
4. Build if needed (most Node-RED nodes don't need a build step)
5. Dry run: npm publish --dry-run
6. Publish: npm publish
7. Create GitHub release with tag
8. Post update to Node-RED forum
```

### Semantic Versioning

| Version Bump | When | Example |
|-------------|------|---------|
| **Patch** (0.0.x) | Bug fixes, no API changes | Fixed FFT window function edge case |
| **Minor** (0.x.0) | New features, backward compatible | Added envelope analysis node |
| **Major** (x.0.0) | Breaking changes | Changed message output format |

I learned this the hard way — see "Mistakes" section below.

### Automated Publishing with GitHub Actions

```yaml
# .github/workflows/publish.yml
name: Publish to npm

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'

      - run: npm ci
      - run: npm test

      - run: npm publish --provenance --access public
        env:
          NODE_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Workflow: create a GitHub Release → tag triggers the action → tests run → npm publish.

---

## Community

### Handling Issues

Most issues fall into three categories:

```
Issue type           Frequency   Response
──────────────────────────────────────────────────────
Installation help    40%         Point to docs, ask for
                                 Node-RED and Node.js version

"How do I..."        35%         Answer if quick, point to
                                 examples if complex

Actual bugs          20%         Reproduce, fix, release patch

Feature requests     5%          Discuss, add to backlog or
                                 explain why not
```

**Key lesson:** Respond quickly, even if the response is "I'll look into this next week." Silence kills open-source projects.

### Pull Requests from Strangers

I've received about 15 PRs across all packages. Most were small fixes (typos, README improvements). A few were significant features. For every PR:

1. Thank the contributor (always, even if you can't merge)
2. Review within a week
3. If changes needed, be specific — "could you add a test for this case?" not "needs work"
4. Merge and release quickly after approval

### The Node-RED Forum

The [Node-RED Discourse forum](https://discourse.nodered.org/) is the primary community hub. Posting about your package in the "Share your nodes" category is the single best way to get initial users. The community is welcoming, constructive, and full of people building real things.

---

## Mistakes I Made

### Over-Engineering v1

My first version of `condition-monitoring` had a plugin architecture, configurable processing pipelines, and abstract signal processor classes. It was flexible enough to analyze anything. Nobody understood how to use it.

```
v0.1 (over-engineered):

  User → Configure Pipeline:
    1. Select windowing function
    2. Choose FFT algorithm
    3. Set overlap percentage
    4. Define frequency bands
    5. Configure peak detection params
    6. Set alarm thresholds per band
    7. Enable/disable envelope analysis

  User reaction: "I just want to know if my motor is vibrating too much"
```

v0.2 was a complete rewrite with sensible defaults:

```
v0.2 (simplified):

  User → Drop FFT node → Set sample rate → Connect to chart
  (3 clicks, works immediately with defaults)

  Advanced? Open settings → tweak parameters
```

**Lesson:** Ship the simplest thing that works. Add complexity when users ask for it, not when you imagine they might need it.

### Breaking Changes Without Major Version Bumps

In `nats-suite` v0.4.0, I changed the output message format from `msg.payload` as a string to `msg.payload` as a parsed object. This broke existing flows for everyone who upgraded.

I should have:
1. Released it as v1.0.0 (breaking change = major bump)
2. Added a migration guide
3. Kept backward compatibility with a config option

Instead, I got five frustrated issues in one week. Don't do this.

### Ignoring Edge Cases

The OPC-UA suite worked perfectly with Siemens PLCs — which is what I tested against. Then someone tried it with a Beckhoff TwinCAT system that returns `null` for disconnected sensors instead of a status code. Crash.

Another user had a PLC that returned arrays of 50,000 values in a single read. Out of memory.

```
What I tested:                What users did:
────────────────────          ──────────────────
10 variables                  500 variables
English node names            Chinese node names (UTF-8 handling)
Single server                 3 servers simultaneously
Clean data                    null, NaN, Infinity, empty strings
Fast network                  Satellite link with 800ms latency
Linux                         Windows (path separator issues)
```

**Lesson:** Every assumption you make about the environment will be violated by at least one user.

### Not Writing Tests First

For the first two packages, I wrote tests after the code. This meant:
- Tests only covered the happy path (because I unconsciously tested what I knew worked)
- Refactoring was scary (no safety net during the rewrite)
- Edge cases were discovered in production, not in CI

For `condition-monitoring`, I wrote tests first. The difference was dramatic — I caught 12 bugs during development that would have shipped otherwise.

---

## What Drove Growth

### Download Numbers Over Time

```
node-red-contrib-condition-monitoring:

Downloads
  250 ┤
      │                                          ╭──
  200 ┤                                     ╭────╯
      │                                 ╭───╯
  150 ┤                            ╭────╯
      │                       ╭────╯
  100 ┤                  ╭────╯
      │             ╭────╯
   50 ┤        ╭────╯
      │   ╭────╯
    0 ┤───╯
      └──┬──────┬──────┬──────┬──────┬──────┬──────┬──
        Month  Month  Month  Month  Month  Month  Month
          1      3      6      9     12     18     24

Key moments:
  Month 1:  Published, posted on Node-RED forum         → 30 downloads
  Month 3:  Someone blogged about it                    → 80/month
  Month 6:  Added example flows, improved README        → 120/month
  Month 9:  v1.0 release with 135 tests                 → 160/month
  Month 18: Referenced in a conference talk              → 210/month
```

### What Drove Downloads

| Factor | Impact | Notes |
|--------|--------|-------|
| Node-RED forum post | High | First wave of users always came from here |
| Good README with screenshot | High | People install what they can understand |
| Example flows | High | Lowers the "how do I start" barrier |
| Consistent publishing | Medium | Regular updates signal the project is alive |
| Responding to issues | Medium | Builds trust, users recommend to others |
| Blog posts about the package | Medium | SEO brings in organic search traffic |
| Conference mentions | Highest | Single biggest spike in downloads |

### What Did NOT Drive Downloads

- Twitter/X posts (IIoT people aren't on tech Twitter)
- Complex feature additions (users want simplicity)
- README badges (nobody cares about your coverage badge)

---

## What's Next

| Package | Next Steps |
|---------|------------|
| **condition-monitoring** | Bearing defect frequency calculator, ISO 10816 presets |
| **nats-suite** | KV store support, object store integration |
| **opcua-suite** | Alarms & conditions, method call improvements |
| **clab-interfaces** | Alignment with cLab v2 API changes |
| **i3x** | Historical data aggregation, batch operations |

The overarching theme: **do fewer things, better.** Every package has a feature request backlog longer than what I'll ever build. The discipline is saying no to complexity and yes to reliability.

---

## Advice for First-Time Package Authors

1. **Start with your own itch.** Build what you need, then generalize.
2. **Ship early.** A working v0.1 with three nodes beats a perfect v1.0 that never ships.
3. **Write tests from day one.** Future you will thank present you.
4. **README is marketing.** Spend as much time on the README as on the code.
5. **Semantic versioning is a promise.** Breaking that promise breaks trust.
6. **Respond to issues.** A one-sentence acknowledgment within 48 hours goes a long way.
7. **Don't chase downloads.** Solve a real problem well, and users will find you.
8. **Accept that most code will be rewritten.** v1 exists to teach you what v2 should be.

Two years, five packages, 314 tests, and roughly 4,800 downloads later — the most valuable thing I've built isn't the code. It's the practice of building, shipping, and maintaining software that other people depend on. That practice transfers to every project, every team, every role. Start your own package. Today.
