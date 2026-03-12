---
title: "S7 Communication Suite"
description: "Node-RED nodes for Siemens S7 PLC communication with dual backend support"
tags: ["Node-RED", "TypeScript", "Siemens", "IIoT"]
weight: 4
date: 2026-03-01
---

## The Problem

Siemens S7 PLCs are everywhere in industrial automation — but connecting them to Node-RED has always been a trade-off. Pure JavaScript libraries work without native compilation but lack advanced features. Native Snap7 bindings offer full protocol support but are harder to install. And during development, you often don't have a real PLC available at all.

## The Solution

A Node-RED package for Siemens S7 communication that lets you **choose your backend** — pure JS, native Snap7, or a built-in simulator — without changing your flows. Written in TypeScript for type safety and reliability.

{{< github repo="blanpa/node-red-contrib-s7-suite" >}}

## Three Backends, One API

| Backend | Compilation | Best For |
|---------|-------------|----------|
| **nodes7** | None (pure JS) | Easy install, basic S7 communication |
| **node-snap7** | Native (Snap7) | Advanced features, high performance |
| **sim** | None | Development and testing without hardware |

Switch backends in the config node — your flows stay the same.

## 6 Nodes

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ s7-read  │     │ s7-write │     │s7-trigger│
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     └───────┬────────┴────────────────┘
             │
      ┌──────┴──────┐
      │  s7-config  │──→ PLC Connection
      └─────────────┘
         │       │
  ┌──────┴──┐ ┌──┴────────┐
  │s7-browse│ │ s7-control │
  └─────────┘ └────────────┘
```

- **s7-config** — Manages PLC connections with backend selection and auto-reconnection
- **s7-read** — Read multiple PLC addresses in a single request
- **s7-write** — Write data to PLC memory with dynamic addressing
- **s7-trigger** — Polling with edge detection and deadband filtering
- **s7-browse** — Discover available data blocks with filtering
- **s7-control** — CPU control operations (start, stop, cold start)

## Supported Controllers

S7-200, S7-300, S7-400, S7-1200, S7-1500, and LOGO!

## Address Formats

Three addressing styles — use whichever you're comfortable with:

- **nodes7-style**: `DB1,REAL0`
- **IEC-style**: `DB1.DBD0`
- **Area-style**: `MW4`, `I0.1`, `QD8`

## Reliability

- Request queuing (max 100 concurrent)
- Exponential backoff reconnection
- Edge detection for boolean values
- Deadband filtering to reduce noise

## Quality

- Written in TypeScript with strict type checking
- Jest test suite with 80% coverage threshold
- Docker support for containerized deployment
