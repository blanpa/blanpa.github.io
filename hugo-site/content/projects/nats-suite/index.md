---
title: "NATS Messaging Suite"
description: "Full-featured NATS integration for Node-RED with JetStream and KV store support"
tags: ["Node-RED", "JavaScript", "NATS", "IIoT"]
weight: 2
---

## The Problem

Industrial IoT systems need reliable, low-latency messaging between machines, edge devices, and cloud services. Traditional MQTT brokers work for simple pub/sub, but fall short when you need persistent message streams, exactly-once delivery, or distributed key-value storage. Building custom messaging infrastructure is complex and error-prone.

## The Solution

A comprehensive **Node-RED integration for NATS** — the cloud-native messaging system built for performance. This module brings the full power of NATS into Node-RED's visual programming environment: core messaging, persistent streaming via JetStream, and key-value storage — all without writing code.

{{< github repo="blanpa/node-red-contrib-nats-suite" >}}

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
- **Compression** — S2 compression for large values

## Embedded NATS Server

Run a full NATS server directly inside Node-RED — perfect for edge deployments:

- **Zero external dependencies** — No separate NATS installation needed
- **MQTT Bridge** — Accept MQTT connections alongside NATS
- **WebSocket Support** — Browser-based clients
- **HTTP Monitoring** — Health and metrics endpoints

## Node Types

8 purpose-built nodes: `nats-config`, `nats-publish`, `nats-subscribe`, `nats-request`, `nats-reply`, `nats-jetstream`, `nats-kv`, `nats-server`
