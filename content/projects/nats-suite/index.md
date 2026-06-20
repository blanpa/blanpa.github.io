---
title: "NATS Messaging Suite"
description: "Full-featured NATS integration for Node-RED with JetStream and KV store support"
tags: ["Node-RED", "JavaScript", "NATS", "IIoT"]
weight: 2
date: 2025-12-03
---

## The Problem

Industrial IoT systems need reliable, low-latency messaging between machines, edge devices, and cloud services. Traditional MQTT brokers work for simple pub/sub, but fall short when you need persistent message streams, exactly-once delivery, or distributed key-value storage. Building custom messaging infrastructure is complex and error-prone.

## The Solution

A comprehensive **Node-RED integration for NATS** — the cloud-native messaging system built for performance. This module brings the full power of NATS into Node-RED's visual programming environment: core messaging, persistent streaming via JetStream, and key-value storage — all without writing code.

{{< github repo="blanpa/node-red-contrib-nats-suite" >}}

## Architecture

The 8 nodes cover the three NATS surfaces — core messaging, persistent JetStream, and the KV store — and can run against an external cluster or an embedded server right inside Node-RED:

{{< mermaid >}}
flowchart LR
    subgraph NR["Node-RED Flow"]
        PUB["nats-suite-publish<br/>(pub · request/reply)"]
        SUB["nats-suite-subscribe"]
        JSP["nats-suite-stream-publisher"]
        JSC["nats-suite-stream-consumer"]
        KVG["nats-suite-kv-get"]
        KVP["nats-suite-kv-put"]
        SRVM["nats-suite-server-manager<br/>(embedded)"]
    end
    CFG["nats-suite-server<br/>auth · TLS · cluster failover"]
    CORE["Core NATS<br/>pub/sub · req/rep · queue groups"]
    JSE["JetStream<br/>streams · consumers · replay"]
    KVE["KV Store<br/>watch · history · TTL"]
    MQTT["MQTT clients"]
    WS["WebSocket clients"]
    PUB --> CFG
    SUB --> CFG
    JSP --> CFG
    JSC --> CFG
    KVG --> CFG
    KVP --> CFG
    CFG --> CORE
    CFG --> JSE
    CFG --> KVE
    SRVM -. provides .-> CORE
    SRVM -. provides .-> JSE
    SRVM -. provides .-> KVE
    MQTT --> SRVM
    WS --> SRVM
{{< /mermaid >}}

## Why NATS over MQTT?

| Feature | MQTT | NATS |
|---------|------|------|
| Pub/Sub | Yes | Yes |
| Request/Reply | No | Yes |
| Message persistence | Requires external DB | Built-in (JetStream) |
| Key-Value store | No | Built-in |
| Queue groups | Limited | Native |
| Performance | ~100K msg/s | ~10M msg/s |
| Auth methods | Username/Password, TLS | Token, JWT, NKey, TLS |

## Core Messaging

- **Pub/Sub** — Publish to subjects, subscribe with wildcards (`sensor.>`, `factory.*.temperature`)
- **Request/Reply** — Synchronous RPC patterns for command-and-control flows
- **Queue Groups** — Automatic load balancing across multiple consumers
- **Message Headers & TTL** — Metadata and automatic expiration
- **Automatic Reconnection** — Handles network failures gracefully with cluster failover

## JetStream — Persistent Streaming

For when messages must not be lost:

- **Stream Management** — Create, update, delete streams with configurable retention (limits, interest, work queue)
- **Pull & Push Consumers** — Flexible consumption patterns for different use cases
- **Message Replay** — Replay from a specific sequence, time, or "last per subject"
- **Delivery Guarantees** — At-least-once and exactly-once semantics

## Key-Value Storage

A distributed key-value store for configuration, state, and metadata:

- **CRUD Operations** — Get, put, delete, purge
- **Watch** — Real-time notifications when values change
- **TTL** — Automatic expiration of stale entries
- **History** — Configurable revision history per key
- **Compression** — Value compression for large values

## Embedded NATS Server

Run a full NATS server directly inside Node-RED — perfect for edge deployments:

- **Zero external dependencies** — No separate NATS installation needed
- **MQTT Bridge** — Accept MQTT connections alongside NATS
- **WebSocket Support** — Browser-based clients
- **HTTP Monitoring** — Health and metrics endpoints

## Node Types

8 purpose-built nodes: `nats-suite-server`, `nats-suite-publish` (publish plus request/reply mode), `nats-suite-subscribe`, `nats-suite-stream-publisher`, `nats-suite-stream-consumer`, `nats-suite-kv-get`, `nats-suite-kv-put`, `nats-suite-server-manager`
