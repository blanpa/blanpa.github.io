# blanpa.github.io

Personal portfolio website — IIoT Software Developer building industrial connectivity solutions with Node-RED, OPC-UA, NATS, and edge computing.

## Tech Stack

- [Hugo](https://gohugo.io/) with the [Blowfish](https://blowfish.page/) theme
- Deployed via GitHub Actions to [GitHub Pages](https://blanpa.github.io)

## Local Development

The site is built with Hugo Extended. The easiest way to run it locally is via Docker (no local Hugo install required):

```bash
docker compose up
```

This serves the site with drafts enabled at http://localhost:1314.

If you have [Hugo Extended](https://gohugo.io/installation/) installed locally instead:

```bash
hugo server -D
```

> Note: CI builds with the pinned Hugo version in `.github/workflows/deploy.yml`.

## Projects

The site showcases 8 open-source npm packages (the canonical list lives in `data/npm_packages.yml`):

- **node-red-contrib-condition-monitoring** — Vibration analysis & predictive maintenance
- **node-red-contrib-nats-suite** — NATS messaging with JetStream support
- **node-red-contrib-kafka-suite** — Apache Kafka integration with Schema Registry
- **node-red-contrib-cip-suite** — Allen-Bradley PLC & EtherNet/IP communication
- **node-red-contrib-s7-suite** — Siemens S7 PLC communication
- **node-red-contrib-opcua-suite** — OPC-UA industrial data exchange
- **node-red-contrib-clab-interfaces** — CompuLab IoT Gateway hardware interfaces
- **node-red-contrib-i3x** — i3x open manufacturing API integration

## Content Tooling

Two helper scripts for authoring (both need Python 3; not part of the build):

- `generate-thumbnails.py` — generates AI hero images for blog posts via the Hugging Face Inference API (needs `HF_TOKEN` and Pillow: `pip install Pillow`)
- `generate-diagrams.py` — converts ASCII diagrams in posts to Mermaid shortcodes via the Claude API (needs `ANTHROPIC_API_KEY`)

npm download counts shown on the site are baked into `data/npm_stats.yml` by the deploy workflow (daily cron); the committed values are just a local-dev fallback baseline.

Diagrams are authored as ` ```mermaid ` fenced blocks — `layouts/_markup/render-codeblock-mermaid.html` renders them and `assets/js/ui.js` loads the mermaid runtime only when a diagram nears the viewport.

## Tests

The content tests (front matter, code samples, links, diagrams, and the technical claims in the posts) run **locally before each commit**, not in CI. Enable the hook once:

```bash
git config core.hooksPath .githooks
tests/run.sh
```

See [tests/README.md](tests/README.md) for what is covered and how to run them by hand.

## CI

- `ci.yml` builds every pull request and branch, checks internal links with lychee, and fails on unrendered diagrams or unexpanded shortcodes.
- `deploy.yml` publishes `main` to GitHub Pages and refreshes the npm stats.

## License

Code is MIT, content is CC BY 4.0 — see [LICENSE](LICENSE).
