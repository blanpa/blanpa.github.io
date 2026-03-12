---
title: "OPC-UA Suite"
description: "Modern OPC-UA client/server suite for Node-RED with connection pooling and batch operations"
tags: ["Node-RED", "JavaScript", "OPC-UA", "IIoT"]
weight: 5
date: 2025-01-01
---

## The Problem

OPC-UA is the industry standard for machine-to-machine communication in industrial automation — but existing Node-RED OPC-UA nodes waste resources by opening a separate TCP connection per node, don't support batch operations, and make certificate management painful. There's a gap between what OPC-UA can do and what's practical in a visual programming environment.

## The Solution

A modern OPC-UA suite for Node-RED that uses **shared connections**, **batch operations**, and **drag-and-drop certificates** — from simple tag reads to event subscriptions and embedded servers.

{{< github repo="blanpa/node-red-contrib-opcua-suite" >}}

## What is OPC-UA?

**OPC Unified Architecture** is the interoperability standard for secure, reliable data exchange in industrial automation. It's platform-independent, vendor-neutral, and supported by virtually every major PLC, SCADA, and MES vendor.

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Siemens  │  │  Beckhoff │  │   ABB    │
│   PLC    │  │   PLC    │  │   DCS    │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └──────┬──────┴─────────────┘
            │    OPC-UA
     ┌──────┴──────┐
     │   Node-RED  │──→ Dashboard
     │  OPC-UA     │──→ Database
     │   Suite     │──→ Cloud/MQTT
     └─────────────┘
```

## 7 Nodes

- **opcua-endpoint** — Shared connection pooling with reference counting (one TCP connection per endpoint, not per node)
- **opcua-client** — All-in-one node for read, write, subscribe, browse, methods, history, and discovery
- **opcua-item** — Visual batch operation builder through node chaining
- **opcua-browser** — Address space navigation with recursive traversal
- **opcua-method** — Method invocation with auto-detected typed arguments
- **opcua-event** — Event subscription for alarm conditions and custom event types
- **opcua-server** — Embedded OPC-UA server for testing and integration

## Shared Connections

Unlike legacy packages that open one TCP connection per node, this suite uses **reference-counted connection pooling**. Multiple nodes pointing to the same endpoint share a single TCP connection — automatically cleaned up when the last node closes.

## Batch Operations

Single OPC-UA service calls handle multiple variables simultaneously. Chain `opcua-item` nodes to visually build batch configurations:

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐
│ item     │──→│ item     │──→│ item     │──→│ opcua-client │
│ Temp     │   │ Pressure │   │ Speed    │   │ (batch read) │
└──────────┘   └──────────┘   └──────────┘   └──────────────┘
```

## Security

- Drag-and-drop certificate upload in the editor
- Security modes: None, Sign, SignAndEncrypt
- Optional username/password authentication

## Why OPC-UA?

| Feature | Modbus | MQTT | OPC-UA |
|---------|--------|------|--------|
| Data typing | No | No | Yes (rich types) |
| Information model | No | No | Yes (browsable) |
| Security | None | TLS | TLS + certificates + auth |
| Discovery | No | No | Yes (automatic) |
| Method calls | No | No | Yes |
| Historical data | No | No | Yes (built-in) |
| Industry adoption | Legacy | IT/IoT | OT/Automation |

## Quality

- **120 unit tests** + **36 integration tests** with embedded test server
- Docker support for local development and CI
- Automatic datatype detection from JavaScript primitives
- MIT licensed
