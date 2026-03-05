---
title: "i3X Manufacturing API"
description: "Node-RED integration for the i3X open manufacturing data standard by CESMII"
tags: ["Node-RED", "JavaScript", "REST API", "IIoT"]
weight: 3
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

## Coverage

- **20 API endpoints** implemented across exploration, querying, updates, and subscription management
- Docker support for quick local development and testing
- Example flows demonstrating practical usage patterns
- Comprehensive test suite (unit + integration)
