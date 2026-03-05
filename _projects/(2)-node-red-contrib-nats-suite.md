---
name: NATS Messaging Suite
tools: [Node-RED, JavaScript, NATS, JetStream]
image: https://raw.githubusercontent.com/blanpa/node-red-contrib-nats-suite/main/docs/images/preview.png
description: Full-featured NATS integration for Node-RED with JetStream and KV store support
external_url: https://github.com/blanpa/node-red-contrib-nats-suite
---

# NATS Messaging Suite for Node-RED

A comprehensive Node-RED module for integrating with **NATS** — the cloud-native messaging system. Supports core messaging, persistent streaming via JetStream, and key-value storage.

## Key Features

**Core Messaging**
- Pub/Sub and request/reply patterns
- Queue groups for load balancing
- Subject wildcards for flexible routing
- Multiple auth methods: token, username/password, JWT, NKey

**JetStream (Persistence)**
- Stream management with configurable retention policies
- Pull and push consumers
- Message replay and delivery control

**Key-Value Storage**
- Bucket management with TTL support
- Watch for real-time change notifications
- Value compression

**Embedded Server**
- Run NATS directly within Node-RED
- Optional MQTT bridging and WebSocket support
- HTTP monitoring endpoints

8 node types covering configuration, publishing, subscribing, and specialized JetStream/KV operations.
