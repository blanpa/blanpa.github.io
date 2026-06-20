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

- **node-red-contrib-condition-monitoring** — Condition monitoring nodes for Node-RED
- **node-red-contrib-nats-suite** — NATS messaging integration for Node-RED
- **node-red-contrib-i3x** — i3x gateway nodes for Node-RED
- **node-red-contrib-clab-interfaces** — Containerlab interface nodes for Node-RED
- **node-red-contrib-opcua-suite** — OPC-UA communication nodes for Node-RED
- **Conveyor Belt Sorting System** — Automated sorting with PLC and image recognition
- **Automated Table Soccer** — University project with 3D-printed components and Raspberry Pi

## License

See [LICENSE](LICENSE) for details.
