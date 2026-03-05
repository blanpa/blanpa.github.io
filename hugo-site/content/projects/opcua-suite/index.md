---
title: "OPC-UA Suite"
description: "OPC-UA integration suite for Node-RED enabling standardized industrial data exchange"
tags: ["Node-RED", "JavaScript", "OPC-UA", "IIoT"]
weight: 5
---

## The Problem

OPC-UA is the industry standard for machine-to-machine communication in industrial automation — but existing Node-RED OPC-UA nodes are either too basic (only reading/writing single values) or too complex (requiring deep protocol knowledge). There's a gap between what OPC-UA can do and what's accessible in a visual programming environment.

## The Solution

An OPC-UA integration suite for Node-RED that makes the full protocol accessible through intuitive, well-documented nodes — from simple tag reads to complex subscriptions and method calls.

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

## Use Cases

- **Multi-vendor data collection** — Read data from Siemens, Beckhoff, Allen-Bradley, and others through one protocol
- **Shopfloor to Cloud** — Bridge OPC-UA data to MQTT, NATS, or REST APIs for cloud analytics
- **Recipe Management** — Write setpoints and parameters back to PLCs
- **Alarming** — Subscribe to OPC-UA alarms and conditions for real-time notifications
