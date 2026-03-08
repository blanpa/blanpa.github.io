---
title: "i3X Manufacturing API"
description: "Node-RED integration for the i3X open manufacturing data standard by CESMII"
tags: ["Node-RED", "JavaScript", "REST API", "IIoT"]
weight: 5
date: 2024-11-01
---

## The Problem

Manufacturing data is trapped in silos. Historians, MES, MOM, and SCADA systems all speak different languages, use proprietary APIs, and require vendor-specific integrations. Connecting a new system to your existing infrastructure often means months of custom development and costly middleware licenses.

## The Solution

Node-RED nodes for the **i3X API** — an open REST specification developed by [CESMII](https://www.cesmii.org/) (the Clean Energy Smart Manufacturing Innovation Institute) that provides a **vendor-agnostic interface** to manufacturing data platforms. One API, any data source.

{{< github repo="blanpa/node-red-contrib-i3x" >}}

## What is i3X?

i3X defines a common REST API for accessing manufacturing information, regardless of the underlying platform. Instead of building separate integrations for each historian or MES system, you connect through i3X and access all data through a unified information model.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Historian   │     │     MES     │     │    SCADA    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────┬───────┴───────────────────┘
                   │
            ┌──────┴──────┐
            │   i3X API   │
            └──────┬──────┘
                   │
            ┌──────┴──────┐
            │   Node-RED  │
            └─────────────┘
```

## Data Access

- **Browse** — Explore the information model: namespaces, object types, relationships, and instances
- **Read** — Get current values from any industrial object in real-time
- **Write** — Push values back to the source system (setpoints, commands)
- **Historical Queries** — Flexible time-based queries with ISO 8601 or relative formats (`-7d`, `-24h`, `-30m`)

## Live Subscriptions

Stay up to date without polling:

- **Server-Sent Events (SSE)** — Real-time push notifications when values change
- **Automatic Polling Fallback** — If SSE is unavailable, the node switches to configurable interval polling

## Configuration & Security

- **Shared connection node** — Configure once, use across all i3X nodes in your flow
- **Authentication** — None, Basic, Bearer token, or API key
- **TLS** — Full TLS/SSL support with custom CA certificates
- **API Versioning** — Configure the target API version

## 6 Nodes

- **i3x-server** — Shared connection configuration with multiple auth methods
- **i3x-browse** — Explore namespaces, object types, relationships, and instances
- **i3x-read** — Retrieve current values from industrial objects
- **i3x-write** — Push values and historical VQT records back to source systems
- **i3x-history** — Time-series queries with ISO 8601 or relative formats
- **i3x-subscribe** — Real-time SSE streaming with automatic polling fallback

## Resilience

- Exponential backoff retry on 429/5xx errors
- 60-second TTL caching for namespaces and object types
- Client-side rate limiting (100 req/60s sliding window)
- Automatic SSE-to-polling fallback on stream failure
- Server-side subscription cleanup on stop/redeploy

## Coverage

- **20 API endpoints** across exploration, querying, updates, and subscription management
- Docker support for quick local development and testing
- Comprehensive test suite (unit + integration)
