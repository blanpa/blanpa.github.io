---
title: "Node-RED vs Kepware vs Ignition — IIoT Platforms Compared"
tags: [iiot, node-red, opc-ua]
description: "An honest comparison of three popular IIoT platforms — open-source flexibility vs enterprise features vs SCADA power."
date: 2026-04-04
series: ["IIoT"]
---

Choosing an IIoT platform is one of those decisions that haunts you for years. Pick the wrong one, and you're locked into expensive licenses, limited integrations, or a tool that doesn't scale. Pick the right one — or the right *combination* — and you've built a foundation that grows with your factory.

I've worked with all three platforms extensively: Node-RED as my daily driver for data transformation, Kepware as the connectivity workhorse, and Ignition as the SCADA powerhouse. Here's my honest comparison.

---

## The Three Contenders

### Node-RED — The Open-Source Swiss Army Knife

Node-RED is a flow-based programming tool built on Node.js. Originally created by IBM for IoT prototyping, it has grown into a serious integration platform used in production environments worldwide.

```
┌─────────────────────────────────────────────────┐
│                   Node-RED                       │
│                                                  │
│  ┌─────┐   ┌──────────┐   ┌──────────┐         │
│  │ OPC │──→│ Transform │──→│   MQTT   │         │
│  │ UA  │   │ & Filter  │   │ Publish  │         │
│  └─────┘   └──────────┘   └──────────┘         │
│                                                  │
│  ┌─────┐   ┌──────────┐   ┌──────────┐         │
│  │ REST│──→│ Aggregate │──→│ Database │         │
│  │ API │   │ & Enrich  │   │  Write   │         │
│  └─────┘   └──────────┘   └──────────┘         │
│                                                  │
│  Visual flow editor │ 5000+ community nodes     │
└─────────────────────────────────────────────────┘
```

**Strengths:** Zero licensing cost, massive ecosystem, rapid prototyping, runs on anything from a Raspberry Pi to a Kubernetes cluster.

**Weaknesses:** No built-in historian, limited out-of-the-box SCADA features, quality of community nodes varies wildly.

### Kepware (KEPServerEX) — The Connectivity King

Kepware, now part of PTC's ThingWorx ecosystem, is a connectivity server that specializes in one thing: talking to industrial equipment. It supports 150+ device drivers — from Siemens S7 to Allen-Bradley to Modbus to BACnet.

```
┌──────────────────────────────────────────────────┐
│                  KEPServerEX                      │
│                                                   │
│  Drivers:                    Server Interfaces:   │
│  ┌─────────────┐            ┌─────────────┐      │
│  │ Siemens S7  │            │  OPC-UA     │      │
│  │ AB Ethernet │──→ Tags ──→│  OPC-DA     │      │
│  │ Modbus TCP  │    Store   │  MQTT       │      │
│  │ BACnet      │            │  REST API   │      │
│  │ MQTT Client │            │  ODBC       │      │
│  │ 150+ more   │            └─────────────┘      │
│  └─────────────┘                                  │
└──────────────────────────────────────────────────┘
```

**Strengths:** Unmatched driver library, battle-tested in thousands of factories, excellent PLC communication performance, certified drivers.

**Weaknesses:** Expensive licensing per driver, Windows-only, limited data transformation capabilities, no visualization.

### Ignition — The SCADA Powerhouse

Ignition by Inductive Automation is a full SCADA/MES platform with built-in historian, alarming, reporting, and visualization. It's Java-based and uses a modular architecture with unlimited client licensing.

```
┌──────────────────────────────────────────────────┐
│                    Ignition                       │
│                                                   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐      │
│  │  Vision   │ │Perspective│ │ Reporting  │      │
│  │ (Desktop) │ │  (Web UI) │ │  Module    │      │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘      │
│        └──────────┬───┘             │             │
│             ┌─────┴─────┐    ┌─────┴─────┐      │
│             │  Tag DB   │    │ Historian  │      │
│             │  + Alarm  │    │ (SQL DB)   │      │
│             └─────┬─────┘    └───────────┘      │
│             ┌─────┴─────┐                        │
│             │  OPC-UA   │                        │
│             │  Drivers  │                        │
│             └───────────┘                        │
└──────────────────────────────────────────────────┘
```

**Strengths:** Unlimited clients/tags, built-in historian, powerful HMI/SCADA designer, Perspective module for mobile-friendly web UIs, strong scripting with Python (Jython).

**Weaknesses:** Higher initial cost, steeper learning curve, Java-based (resource-heavy), limited non-SCADA integration options out of the box.

---

## Detailed Comparison

### Licensing & Cost

| Aspect | Node-RED | Kepware (KEPServerEX) | Ignition |
|--------|----------|-----------------------|----------|
| **Base License** | Free (Apache 2.0) | ~$1,500 (base server) | ~$4,800 (Platform) |
| **Per-Driver/Module** | Free (community nodes) | $300–$1,500 per driver | $2,400–$4,800 per module |
| **Client Licenses** | N/A (web-based) | N/A (server only) | **Unlimited** |
| **Tag Limits** | None | None (licensed per driver) | None |
| **Typical 5-Machine Setup** | $0 | ~$4,000–$8,000 | ~$12,000–$20,000 |
| **Typical 50-Machine Setup** | $0 | ~$15,000–$30,000 | ~$20,000–$35,000 |
| **Annual Maintenance** | N/A | ~20% of license cost | ~20% of license cost |
| **Cloud/Hosted Option** | FlowFuse (~$50/mo) | ThingWorx (enterprise pricing) | Ignition Cloud (contact sales) |

The cost advantage of Node-RED is obvious — but "free" doesn't mean "no cost." You pay with development time, support responsibility, and the need to build features that come out-of-the-box with commercial platforms.

Ignition's unlimited client model is a game-changer. With Kepware or traditional SCADA, adding 50 operator screens means 50 licenses. With Ignition, you pay once.

### Protocol Support

| Protocol | Node-RED | Kepware | Ignition |
|----------|----------|---------|----------|
| **OPC-UA** | Community nodes (good) | Native server + client | Native server + client |
| **OPC-DA** | Via wrapper | Native | Native |
| **Modbus TCP/RTU** | Community node | Native driver | Native driver |
| **Siemens S7** | node-red-contrib-s7 | Native driver (certified) | Native driver |
| **Allen-Bradley** | Limited | Native driver (certified) | Native driver |
| **MQTT** | Core node (excellent) | MQTT Client driver | MQTT Engine module |
| **HTTP/REST** | Core node (excellent) | REST agent (limited) | Web Dev module |
| **SQL Databases** | Community nodes | ODBC interface | Native JDBC |
| **BACnet** | Community node | Native driver | Third-party module |
| **EtherNet/IP** | Limited | Native driver | Native driver |
| **PROFINET** | Not available | Native driver | Not available |

Kepware wins on PLC connectivity breadth. If you need to talk to a legacy Allen-Bradley PLC-5 over DH+, Kepware has a driver for that. Node-RED can't compete here.

Node-RED wins on IT-side protocols. REST APIs, MQTT, WebSockets, GraphQL, gRPC — the Node.js ecosystem has mature libraries for everything.

### Scalability

| Aspect | Node-RED | Kepware | Ignition |
|--------|----------|---------|----------|
| **Tags/second** | ~5,000–20,000 | ~50,000–100,000 | ~50,000–150,000 |
| **Horizontal scaling** | Easy (containerized) | Manual (multiple servers) | Gateway Network |
| **Edge deployment** | Excellent (ARM, Docker) | Limited (Windows) | Ignition Edge (licensed) |
| **High availability** | DIY (container orchestration) | Redundancy add-on | Built-in redundancy |
| **Multi-site** | Custom architecture | Enterprise licensing | Gateway Network |

### Learning Curve

```
Easy ──────────────────────────────────────── Hard

Node-RED                  Kepware        Ignition
  ●─────────────────────────●──────────────●
  │                         │              │
  │ Visual flows,           │ Tag config,  │ Jython scripting,
  │ web-based,              │ driver setup │ tag provider model,
  │ JavaScript              │              │ Vision vs Perspective
```

Node-RED is the easiest to start with. Drag nodes, connect wires, deploy. A developer with web experience is productive in hours.

Kepware requires understanding tag configuration, driver-specific parameters, and OPC concepts, but the UI is straightforward.

Ignition has the steepest learning curve. The tag model, expression language, Jython scripting, and the choice between Vision (Java client) and Perspective (web) add complexity. But Inductive University (free) is one of the best learning platforms in industrial software.

---

## When to Use Each

### Node-RED Wins When...

- You need **rapid prototyping** — get a working demo in hours, not weeks
- The project is **IT-heavy** — REST APIs, MQTT brokers, cloud services, databases
- You're running on **edge hardware** — Raspberry Pi, industrial PCs with limited resources
- Budget is **tight or zero** — startups, research projects, proof-of-concepts
- You need **custom data transformation** — complex mapping, enrichment, filtering

```javascript
// Node-RED function node: Transform PLC data for cloud upload
const machines = msg.payload;

msg.payload = machines
    .filter(m => m.status === "Running")
    .map(m => ({
        machineId: m.id,
        oee: calculateOEE(m.availability, m.performance, m.quality),
        timestamp: new Date().toISOString(),
        alarms: m.alarms.filter(a => a.severity > 3)
    }));

return msg;
```

### Kepware Wins When...

- You have **diverse PLC brands** — Siemens, Allen-Bradley, Mitsubishi, Omron on the same floor
- You need **certified drivers** — automotive/pharma environments with validation requirements
- The project is primarily **OPC-UA server** — expose PLC data to any OPC-UA client
- **Legacy equipment** is involved — serial Modbus, DH+, DF1, older protocols
- IT wants a **supported product** with phone support and SLAs

### Ignition Wins When...

- You need a **full SCADA/HMI** — operator screens, alarming, trending, reporting
- **Historical data** is critical — built-in historian with proper compression and query
- You're deploying **unlimited operator screens** — Ignition's licensing model shines
- The project spans **multiple sites** — Gateway Network handles multi-site natively
- You need **MES features** — production tracking, recipe management, batch control

---

## The Combination Play

In practice, the best architectures often combine all three. Each platform handles what it does best:

```
Shop Floor                    Edge / Server Room               Cloud / Enterprise
─────────────                 ────────────────                 ──────────────────

┌───────────┐
│ Siemens   │                 ┌─────────────┐
│ S7-1500   ├────OPC-UA──────→│             │
└───────────┘                 │  Kepware    │
                              │  KEPServer  │──OPC-UA──┐
┌───────────┐                 │             │          │
│ AB        │                 │  (PLC       │          │
│ ControlL. ├────EtherNet/IP─→│   Drivers)  │          │
└───────────┘                 └─────────────┘          │
                                                       │
┌───────────┐                 ┌─────────────┐          │     ┌──────────────┐
│ Temp      │                 │             │          ├────→│              │
│ Sensors   ├────Modbus──────→│  Node-RED   │          │     │   Ignition   │
└───────────┘                 │             │──MQTT───→│     │   SCADA      │
                              │  (Transform │          │     │              │
┌───────────┐                 │   + Route)  │          │     │  - HMI       │
│ IoT       │                 │             │──REST───→│────→│  - Historian │
│ Gateway   ├────MQTT────────→│             │          │     │  - Alarming  │
└───────────┘                 └─────────────┘          │     │  - Reporting │
                                                       │     └──────────────┘
                              ┌─────────────┐          │
                              │  Grafana +  │          │     ┌──────────────┐
                              │  PostgreSQL │←─────────┘     │  Cloud       │
                              │  (IT-side   │                │  Analytics   │
                              │   dashboards)│───REST──────→│  (Azure/AWS) │
                              └─────────────┘                └──────────────┘
```

### Architecture Pattern 1: Kepware + Node-RED

**Use case:** You need reliable PLC connectivity but want flexible data routing.

Kepware handles the PLC drivers — it's simply the best at this. Node-RED subscribes to Kepware's OPC-UA server and handles all data transformation, routing, and cloud uploads.

```yaml
# docker-compose.yml — Node-RED as Kepware's data processor
services:
  nodered:
    image: nodered/node-red:latest
    ports:
      - "1880:1880"
    volumes:
      - nodered_data:/data
    environment:
      - KEPWARE_HOST=192.168.1.100
      - KEPWARE_PORT=49320
      - MQTT_BROKER=nats.factory.local

volumes:
  nodered_data:
```

### Architecture Pattern 2: Ignition + Node-RED

**Use case:** Ignition handles SCADA/HMI, Node-RED handles IT integrations that Ignition struggles with (REST APIs, cloud services, custom protocols).

```
Ignition Gateway                    Node-RED
┌──────────────────┐               ┌──────────────────┐
│                  │               │                  │
│  Tags + Historian│───OPC-UA────→│  Cloud Upload    │
│                  │               │  (Azure IoT Hub) │
│  SCADA Screens   │               │                  │
│                  │←──MQTT───────│  ERP Integration │
│  Alarming        │               │  (SAP REST API)  │
│                  │               │                  │
│  Reporting       │───SQL────────→│  Custom Reports  │
│                  │               │  (Email + PDF)   │
└──────────────────┘               └──────────────────┘
```

### Architecture Pattern 3: All Three

**Use case:** Large multi-vendor factory with SCADA requirements AND complex IT integration.

- **Kepware** → PLC connectivity layer (all drivers)
- **Ignition** → SCADA/HMI/Historian (operator-facing)
- **Node-RED** → IT integration layer (cloud, ERP, custom APIs)

This is the most common architecture I see in large manufacturing environments with 50+ machines and multiple PLC brands.

---

## Decision Matrix

Use this matrix to guide your platform choice. Score each criterion 1–5 for your project and see which platform fits best:

| Criterion | Weight | Node-RED | Kepware | Ignition |
|-----------|--------|----------|---------|----------|
| Budget constraint | High | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ |
| PLC driver variety | — | ★★☆☆☆ | ★★★★★ | ★★★★☆ |
| IT integration (REST, MQTT) | — | ★★★★★ | ★★☆☆☆ | ★★★☆☆ |
| SCADA/HMI screens | — | ★★☆☆☆ | ☆☆☆☆☆ | ★★★★★ |
| Historical data | — | ★★☆☆☆ | ☆☆☆☆☆ | ★★★★★ |
| Edge deployment | — | ★★★★★ | ★☆☆☆☆ | ★★★☆☆ |
| Rapid prototyping | — | ★★★★★ | ★★★☆☆ | ★★★☆☆ |
| Enterprise support | — | ★★☆☆☆ | ★★★★★ | ★★★★★ |
| Alarming | — | ★★☆☆☆ | ☆☆☆☆☆ | ★★★★★ |
| Custom logic/scripting | — | ★★★★★ | ★☆☆☆☆ | ★★★★☆ |
| Multi-site management | — | ★★★☆☆ | ★★★☆☆ | ★★★★★ |

---

## Pricing Deep Dive (2026)

### Node-RED

| Item | Cost |
|------|------|
| Node-RED runtime | Free |
| Community nodes | Free |
| FlowFuse managed hosting | $50–$500/month |
| FlowFuse enterprise (self-hosted) | Contact sales |
| Your development time | $$$ (the hidden cost) |

### Kepware KEPServerEX

| Item | Cost |
|------|------|
| Base server license | ~$1,500 |
| Siemens S7 Suite driver | ~$1,200 |
| Allen-Bradley Suite driver | ~$1,200 |
| Modbus driver | ~$300 |
| MQTT agent | ~$600 |
| OPC-UA Client driver | ~$600 |
| IoT Gateway (REST/MQTT) | ~$1,200 |
| Annual maintenance (20%) | ~$600–$1,500/year |

### Ignition

| Item | Cost |
|------|------|
| Ignition Platform | ~$4,800 |
| Perspective module (web HMI) | ~$4,800 |
| Historian (Tag Historian) | ~$4,800 |
| Alarm Notification module | ~$4,800 |
| Reporting module | ~$4,800 |
| OPC-UA module (included) | Free with platform |
| SQL Bridge module | ~$4,800 |
| Ignition Edge (per device) | ~$1,200–$2,400 |
| Annual maintenance (20%) | varies |

Ignition's pricing looks high, but remember: **zero per-client fees**. A 100-screen deployment costs the same as a 5-screen deployment for the server modules.

---

## Community & Ecosystem

| Aspect | Node-RED | Kepware | Ignition |
|--------|----------|---------|----------|
| **Community size** | Very large (open source) | Medium (enterprise forums) | Large (active forum + exchange) |
| **Learning resources** | npm, YouTube, blogs | PTC documentation | Inductive University (free, excellent) |
| **Extension model** | npm packages (5000+ nodes) | Drivers (PTC/partners) | Modules (marketplace + SDK) |
| **Custom development** | JavaScript/TypeScript | Limited (API scripting) | Python (Jython) + Java SDK |
| **Forum activity** | discourse.nodered.org (daily) | PTC community (moderate) | forum.inductiveautomation.com (daily) |

---

## My Recommendation

If I had to pick **one platform** for a new project:

- **Small factory, tight budget, IT-heavy** → Node-RED
- **Large factory, many PLC brands, need support** → Ignition + Kepware
- **Proof-of-concept, any size** → Node-RED (always start here)

If I had to pick a **combination**:

- **Best for most factories:** Kepware (connectivity) + Node-RED (transformation) + Grafana (visualization)
- **Best for SCADA-heavy projects:** Ignition (everything) + Node-RED (IT integration)
- **Best for multi-vendor large plants:** All three — Kepware (PLC drivers) + Ignition (SCADA) + Node-RED (cloud/IT glue)

The good news: these platforms play well together. OPC-UA and MQTT are the common languages that let you mix and match without vendor lock-in. Start with what solves your immediate problem, and expand from there.
