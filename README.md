# blanpa.github.io

Personal portfolio website — IIoT Software Developer writing about industrial
connectivity with Node-RED, OPC-UA, NATS, and edge computing.

The site and the npm packages it documents are private open-source work,
unrelated to my employment, published under the MIT licence.

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

> Note: both workflows pin the Hugo version in their own `HUGO_VERSION` env
> (currently 0.154.5, in `ci.yml` and `deploy.yml`). `docker-compose.yml` pins
> the same version — keep the three in step when upgrading.

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

## Case Studies

`content/case-studies/` is scaffolded but unpublished — the section index and
the template both carry `draft: true`, so production builds skip them entirely.
[content/case-studies/README.md](content/case-studies/README.md) describes how
to publish one, including the rule that every figure has to be a measured one.

## Content Tooling

Two helper scripts for authoring (both need Python 3; not part of the build):

- `tools/generate-thumbnails.py` — generates AI hero images for blog posts via the Hugging Face Inference API (needs `HF_TOKEN` and Pillow: `pip install Pillow`)
- `tools/generate-diagrams.py` — converts ASCII diagrams in posts to Mermaid shortcodes via the Claude API (needs `ANTHROPIC_API_KEY`)
- `tools/render-diagrams.py` — renders the mermaid blocks to static SVG (see below); needs mermaid-cli
- `tools/check-forks.sh` — compares the forked theme layouts against their recorded upstream versions

npm download counts shown on the site are baked into `data/npm_stats.yml` by the deploy workflow (daily cron); the committed values are just a local-dev fallback baseline.

Diagrams are authored as ` ```mermaid ` fenced blocks and rendered to static SVG at build time:

```bash
tools/render-diagrams.py          # render what changed, prune orphans
tools/render-diagrams.py --force  # re-render everything (e.g. after a palette change)
```

Each diagram becomes `assets/diagrams/<key>-light.svg` and `-dark.svg`, content-addressed by source and palette; `layouts/partials/mermaid-figure.html` inlines both and CSS shows the one matching the theme. That keeps the 3.2 MB mermaid runtime out of the page entirely and makes the diagrams work without JavaScript.

Edit a diagram and forget to re-render, and the partial falls back to client-side rendering — a heavy page, not a broken one. The content tests fail on a missing SVG so it does not go unnoticed. Needs mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`).

## Tests

The content tests (front matter, code samples, links, diagrams, and the technical claims in the posts) run **locally before each commit**, not in CI. Enable the hook once:

```bash
git config core.hooksPath .githooks
tests/run.sh
```

See [tests/README.md](tests/README.md) for what is covered and how to run them by hand.

## CI

- `ci.yml` builds every pull request and every branch except `main`, checks internal links with lychee, and fails on unrendered diagrams or unexpanded shortcodes. It deliberately does not run the content tests — those are local (see below).
- It also runs `tools/check-forks.sh`. Eight files under `layouts/` override a file of the same name in the theme; overriding is silent, so when Dependabot bumps the submodule and upstream has rewritten one of them, nothing would otherwise notice. The script compares each theme original against the hash recorded in `tools/forks.sha256` and fails with the exact `git diff` to run. Accept a reviewed change with `tools/check-forks.sh --update`.
- `deploy.yml` publishes `main` to GitHub Pages and refreshes the npm stats.

## License

Code is MIT, content is CC BY 4.0 — see [LICENSE](LICENSE).
