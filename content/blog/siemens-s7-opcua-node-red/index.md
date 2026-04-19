---
title: "Siemens S7 + OPC-UA + Node-RED — From PLC to Dashboard in 30 Minutes"
tags: [iiot, opc-ua, node-red, plc]
description: "Step-by-step tutorial: reading data from a Siemens S7-1500 PLC via OPC-UA and displaying it on a Node-RED dashboard."
date: 2026-04-25
series: ["IIoT"]
---

This is the tutorial I wish I had when I first tried connecting a Siemens PLC to Node-RED. It took me two days of frustration — fighting with certificates, firewall rules, and data type mismatches — before I got a single value to appear on a dashboard. With this guide, you'll do it in 30 minutes.

---

## Prerequisites

Before starting, make sure you have:

| Component | Minimum Version | Notes |
|-----------|----------------|-------|
| **Siemens S7-1500 or S7-1200** | FW V2.0+ (S7-1500), FW V4.2+ (S7-1200) | S7-1200 needs FW V4.2 for OPC-UA server |
| **TIA Portal** | V16 or newer | V15.1 works but has fewer OPC-UA features |
| **OPC-UA license** | Required for S7-1500 | Check: ordered as 6ES7 823-1xx00-0YA5 |
| **Node-RED** | V3.0+ | With `node-red-contrib-opcua` or `node-red-opcua-suite` |
| **UaExpert** | Latest | Free OPC-UA client for testing (Unified Automation) |
| **Network access** | — | PC and PLC on the same subnet, port 4840 open |

### Architecture Overview

```
┌─────────────┐        OPC-UA (TCP:4840)       ┌─────────────┐
│  Siemens    │                                 │             │
│  S7-1500    ├────────────────────────────────→│  Node-RED   │
│             │                                 │             │
│  OPC-UA     │                                 │  Dashboard  │
│  Server     │                                 │  (Port 1880)│
└─────────────┘                                 └─────────────┘
  192.168.1.100                                  192.168.1.50

  PLC runs the OPC-UA server.
  Node-RED is the OPC-UA client.
```

---

## Step 1: Enable the OPC-UA Server in TIA Portal

### 1.1 Open PLC Properties

In TIA Portal, navigate to your PLC in the project tree:

```
Project Tree
└── PLC_1 [CPU 1515-2 PN]
    ├── Program blocks
    ├── Technology objects
    ├── ...
    └── Properties ← double-click
```

### 1.2 Activate OPC-UA Server

In the PLC Properties, navigate to:

```
Properties → General → OPC UA
├── [✓] Activate OPC UA Server
├── Port: 4840 (default)
├── Application Name: "PLC_1 OPC-UA Server"
└── Application URI: urn:SIEMENS:S7-1500:OPC-UA:PLC_1
```

Check **"Activate OPC UA Server"** and leave the port at 4840 (default).

### 1.3 Set the Runtime License

If prompted, ensure the correct OPC-UA runtime license is assigned:

```
Properties → General → Runtime licenses
└── OPC UA: SIMATIC OPC UA S7-1500 ← must show "License assigned"
```

Without this license, the OPC-UA server won't start. The PLC will show a diagnostic event "OPC UA: License missing."

---

## Step 2: Configure OPC-UA Security and Access

### 2.1 Security Policies

For initial testing, use the simplest configuration. For production, harden later.

```
Properties → General → OPC UA → Server → Security
├── Security policies
│   ├── [✓] No security                    ← for testing only
│   ├── [✓] Basic256Sha256 - Sign          ← minimum for production
│   └── [✓] Basic256Sha256 - SignAndEncrypt ← recommended for production
└── Secure channel settings
    ├── Max. sessions: 10
    └── Session timeout: 30000 ms
```

### 2.2 User Authentication

```
Properties → General → OPC UA → Server → Security → User authentication
├── [✓] Guest authentication (anonymous)  ← for testing
├── [ ] User name and password             ← for production
└── [ ] X.509 certificate                  ← for high-security environments
```

For production: disable guest/anonymous, create user accounts:

```
Properties → General → OPC UA → Server → Security → User management
├── User 1:
│   ├── User name: nodered_client
│   ├── Password: ************
│   └── Role: Read (or ReadWrite for write-back)
└── User 2:
    ├── User name: scada_client
    ├── Password: ************
    └── Role: ReadWrite
```

### 2.3 Expose Data Blocks to OPC-UA

By default, no data blocks are visible via OPC-UA. You must explicitly mark them:

```
Project Tree
└── PLC_1
    └── Program blocks
        └── DB_MachineData [DB10] ← right-click → Properties
            └── Attributes
                └── [✓] Accessible from HMI/OPC UA
```

Alternatively, mark individual variables:

```
DB_MachineData [DB10]
├── Temperature    Real    ← right-click → "Accessible from OPC UA"
├── SpindleSpeed   Real    ← right-click → "Accessible from OPC UA"
├── Status         Int     ← right-click → "Accessible from OPC UA"
├── PartsProduced  DInt    ← right-click → "Accessible from OPC UA"
└── InternalCounter Int    ← NOT exposed (internal use only)
```

### 2.4 Compile and Download

After configuring OPC-UA:

1. **Compile** the PLC project (Ctrl+B)
2. **Download** to the PLC
3. The PLC will restart the OPC-UA server automatically

Check the PLC diagnostics for:
```
"OPC UA: Server started successfully on port 4840"
```

If you see an error, the most common causes are:
- Missing license
- Port 4840 already in use
- Certificate generation failed

---

## Step 3: Browse with UaExpert

Before connecting Node-RED, verify the OPC-UA server works with UaExpert (free client from Unified Automation).

### 3.1 Connect to the PLC

```
UaExpert → Server → Add Server
  ├── Custom Discovery
  │   └── opc.tcp://192.168.1.100:4840
  └── Connect
      ├── Security Policy: None (for testing)
      └── Authentication: Anonymous
```

### 3.2 Browse the Address Space

After connecting, you should see:

```
Address Space
├── Objects
│   ├── Server
│   │   ├── ServerStatus
│   │   └── ...
│   └── PLC_1
│       └── DataBlocksGlobal
│           └── DB_MachineData
│               ├── Temperature      ns=3;s="DB_MachineData"."Temperature"
│               ├── SpindleSpeed     ns=3;s="DB_MachineData"."SpindleSpeed"
│               ├── Status           ns=3;s="DB_MachineData"."Status"
│               └── PartsProduced    ns=3;s="DB_MachineData"."PartsProduced"
```

**Copy the NodeId strings** — you'll need them in Node-RED. Siemens uses string NodeIds in namespace 3 (typically), formatted as:

```
ns=3;s="DB_MachineData"."Temperature"
```

The quotes around data block and variable names are part of the NodeId.

### 3.3 Read Values

Drag variables to the Data Access View. You should see live values updating:

```
┌──────────────────────────────────────────────────────────────┐
│ Variable              │ Value    │ Status │ Timestamp         │
├───────────────────────┼──────────┼────────┼───────────────────┤
│ Temperature           │ 42.7     │ Good   │ 08:30:00.123     │
│ SpindleSpeed          │ 2450.0   │ Good   │ 08:30:00.123     │
│ Status                │ 1        │ Good   │ 08:29:55.456     │
│ PartsProduced         │ 1847     │ Good   │ 08:30:00.123     │
└──────────────────────────────────────────────────────────────┘
```

If you see values, the PLC's OPC-UA server is working correctly.

---

## Step 4: Connect Node-RED

### 4.1 Install the OPC-UA Nodes

```bash
cd ~/.node-red
npm install node-red-contrib-opcua
```

Restart Node-RED after installation.

Alternative: `node-red-contrib-opcua-suite` provides a slightly different node set with more configuration options. Both work well.

### 4.2 Configure the OPC-UA Client Node

Drag an **OpcUa-Client** node onto the canvas and configure:

```
OPC-UA Client Configuration
├── Endpoint:   opc.tcp://192.168.1.100:4840
├── Security:
│   ├── Policy:   None (testing) / Basic256Sha256 (production)
│   └── Mode:     None (testing) / SignAndEncrypt (production)
├── Authentication:
│   ├── Mode:     Anonymous (testing) / UserName (production)
│   ├── User:     nodered_client
│   └── Password: ************
└── Advanced:
    ├── Request timeout:     10000 ms
    ├── Session timeout:     30000 ms
    └── Reconnect interval:  5000 ms
```

### 4.3 Read Values

Create this flow to read a single value:

```json
[
    {
        "id": "inject-trigger",
        "type": "inject",
        "repeat": "1",
        "topic": "",
        "payload": "{\"actiontype\":\"read\",\"nodeid\":\"ns=3;s=\\\"DB_MachineData\\\".\\\"Temperature\\\"\"}",
        "payloadType": "json"
    },
    {
        "id": "opcua-client",
        "type": "OpcUa-Client",
        "endpoint": "opc.tcp://192.168.1.100:4840",
        "action": "read",
        "name": "S7-1500 Read"
    },
    {
        "id": "debug-output",
        "type": "debug",
        "name": "Temperature"
    }
]
```

Wire: `inject → OpcUa-Client → debug`

The debug output should show:

```json
{
    "value": {
        "value": 42.7,
        "dataType": "Float",
        "statusCode": { "value": 0, "name": "Good" },
        "sourceTimestamp": "2026-04-25T08:30:00.123Z",
        "serverTimestamp": "2026-04-25T08:30:00.135Z"
    },
    "nodeId": "ns=3;s=\"DB_MachineData\".\"Temperature\""
}
```

### 4.4 Read Multiple Values

Use an inject node with an array of node IDs:

```json
{
    "actiontype": "readmultiple",
    "nodeid": [
        "ns=3;s=\"DB_MachineData\".\"Temperature\"",
        "ns=3;s=\"DB_MachineData\".\"SpindleSpeed\"",
        "ns=3;s=\"DB_MachineData\".\"Status\"",
        "ns=3;s=\"DB_MachineData\".\"PartsProduced\""
    ]
}
```

### 4.5 Use Subscriptions (Recommended)

Polling every second works but wastes resources. OPC-UA subscriptions are far more efficient — the PLC pushes changes to Node-RED:

```json
[
    {
        "id": "opcua-item",
        "type": "OpcUa-Item",
        "item": "ns=3;s=\"DB_MachineData\".\"Temperature\"",
        "datatype": "Float",
        "name": "Temperature"
    },
    {
        "id": "opcua-browser",
        "type": "OpcUa-Client",
        "action": "subscribe",
        "interval": 500,
        "name": "S7-1500 Subscribe"
    },
    {
        "id": "function-transform",
        "type": "function",
        "func": "msg.payload = {\n    value: msg.payload,\n    topic: msg.topic,\n    timestamp: new Date().toISOString()\n};\nreturn msg;"
    }
]
```

Wire: `OpcUa-Item → OpcUa-Client → function → (dashboard or debug)`

The subscription node will emit a message every time the value changes on the PLC side. No polling, no wasted bandwidth.

---

## Step 5: Build the Dashboard

### 5.1 Install Dashboard Nodes

```bash
cd ~/.node-red
npm install @flowfuse/node-red-dashboard
```

### 5.2 Dashboard Layout

Create a dashboard with gauges, charts, and status indicators:

```json
[
    {
        "id": "gauge-temp",
        "type": "ui-gauge",
        "group": "machine-status",
        "name": "Temperature",
        "min": 0,
        "max": 200,
        "segments": [
            { "from": 0, "to": 60, "color": "#4CAF50" },
            { "from": 60, "to": 80, "color": "#FF9800" },
            { "from": 80, "to": 200, "color": "#F44336" }
        ],
        "unit": "°C"
    },
    {
        "id": "gauge-spindle",
        "type": "ui-gauge",
        "group": "machine-status",
        "name": "Spindle Speed",
        "min": 0,
        "max": 12000,
        "unit": "RPM"
    },
    {
        "id": "chart-temp",
        "type": "ui-chart",
        "group": "trends",
        "name": "Temperature Trend",
        "chartType": "line",
        "xAxisType": "time",
        "duration": "1h",
        "yMin": 0,
        "yMax": 100
    },
    {
        "id": "text-status",
        "type": "ui-text",
        "group": "machine-status",
        "name": "Machine Status",
        "label": "Status"
    },
    {
        "id": "text-parts",
        "type": "ui-text",
        "group": "machine-status",
        "name": "Parts Produced",
        "label": "Parts Today"
    }
]
```

### 5.3 Status Mapping Function

The PLC sends status as an integer. Map it to human-readable text with color:

```javascript
const STATUS_MAP = {
    0: { text: "OFF",         color: "#9E9E9E" },
    1: { text: "RUNNING",     color: "#4CAF50" },
    2: { text: "ERROR",       color: "#F44336" },
    3: { text: "MAINTENANCE", color: "#FF9800" },
    4: { text: "STANDBY",     color: "#2196F3" }
};

const status = STATUS_MAP[msg.payload] || { text: "UNKNOWN", color: "#9E9E9E" };

msg.payload = status.text;
msg.ui_update = { color: status.color };
return msg;
```

### 5.4 Complete Flow

Here's the complete flow connecting all pieces:

```
┌──────────────────────────────────────────────────────────┐
│                     Node-RED Flow                         │
│                                                           │
│  ┌──────────┐     ┌──────────┐     ┌────────────────┐   │
│  │ OPC-UA   │     │ OPC-UA   │     │ Gauge:         │   │
│  │ Item:    ├────→│ Client:  ├────→│ Temperature    │   │
│  │ Temp     │     │Subscribe │     └────────────────┘   │
│  └──────────┘     │          │     ┌────────────────┐   │
│                   │          ├────→│ Chart:         │   │
│  ┌──────────┐     │          │     │ Temp Trend     │   │
│  │ OPC-UA   │     │          │     └────────────────┘   │
│  │ Item:    ├────→│          │                           │
│  │ Spindle  │     │          │     ┌────────────────┐   │
│  └──────────┘     │          ├────→│ Gauge:         │   │
│                   │          │     │ Spindle Speed  │   │
│  ┌──────────┐     │          │     └────────────────┘   │
│  │ OPC-UA   │     │          │                           │
│  │ Item:    ├────→│          │     ┌──────┐ ┌────────┐  │
│  │ Status   │     │          ├────→│ Map  ├→│ Status │  │
│  └──────────┘     │          │     │ Func │ │ Text   │  │
│                   │          │     └──────┘ └────────┘  │
│  ┌──────────┐     │          │                           │
│  │ OPC-UA   │     │          │     ┌────────────────┐   │
│  │ Item:    ├────→│          ├────→│ Text:          │   │
│  │ Parts    │     │          │     │ Parts Count    │   │
│  └──────────┘     └──────────┘     └────────────────┘   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## S7 Data Types to OPC-UA Mapping

This table saves hours of debugging. S7 data types don't always map intuitively to OPC-UA types:

| S7 Data Type | S7 Size | OPC-UA Type | OPC-UA NodeId DataType | Notes |
|-------------|---------|-------------|----------------------|-------|
| **Bool** | 1 bit | Boolean | i=1 | Direct mapping |
| **Byte** | 8 bit | Byte | i=3 | Unsigned 0–255 |
| **Word** | 16 bit | UInt16 | i=5 | Unsigned 0–65535 |
| **DWord** | 32 bit | UInt32 | i=7 | Unsigned |
| **Int** | 16 bit | Int16 | i=4 | Signed -32768 to 32767 |
| **DInt** | 32 bit | Int32 | i=6 | Signed |
| **LInt** | 64 bit | Int64 | i=8 | S7-1500 only |
| **Real** | 32 bit | Float | i=10 | IEEE 754 single precision |
| **LReal** | 64 bit | Double | i=11 | IEEE 754 double precision |
| **String** | variable | String | i=12 | Max 254 chars (S7 String) |
| **WString** | variable | String | i=12 | Unicode, max 16382 chars |
| **Date** | 16 bit | DateTime | i=13 | Converted to UTC |
| **Time** | 32 bit | Duration | — | Milliseconds |
| **DTL** | 12 byte | DateTime | i=13 | Date and Time Long |
| **Array** | variable | Array of X | — | Preserves element type |
| **Struct (UDT)** | variable | ExtensionObject | — | Complex type mapping |

### Common Pitfall: Real vs LReal

S7 `Real` maps to OPC-UA `Float` (32-bit). If you see values like `42.70000076293945` instead of `42.7`, that's floating-point precision — `Real` only has ~7 significant digits. Use `LReal` (64-bit `Double`) for values that need more precision.

### Common Pitfall: String Encoding

S7 strings have a 2-byte header (max length + actual length). OPC-UA handles the conversion automatically, but if you read raw bytes via S7comm instead of OPC-UA, you'll see garbage characters at the start of every string.

---

## Common Pitfalls & Troubleshooting

### Problem 1: "Connection refused" on Port 4840

```
Checklist:
  [ ] OPC-UA server activated in TIA Portal? (Step 1.2)
  [ ] Project compiled AND downloaded to PLC?
  [ ] PLC in RUN mode?
  [ ] Firewall on the Node-RED PC allows outbound TCP:4840?
  [ ] Windows Firewall on engineering PC not blocking?
  [ ] Correct IP address? (ping 192.168.1.100)
  [ ] Port not blocked by industrial switch/firewall?
```

### Problem 2: "BadSecurityChecksFailed"

This happens when the client and server can't agree on a security policy.

```
Fix for testing:
  1. In TIA Portal → OPC UA → Security → enable "No security"
  2. In Node-RED → OPC-UA Client → Security Policy: None
  3. Recompile + Download to PLC

Fix for production:
  1. Both sides must use the same policy (e.g., Basic256Sha256)
  2. Exchange certificates:
     - Export PLC's server certificate from TIA Portal
     - Import it as trusted in Node-RED's OPC-UA client
     - Export Node-RED's client certificate
     - Import it as trusted in TIA Portal
```

### Problem 3: "BadNodeIdUnknown"

The NodeId you're trying to read doesn't exist in the PLC's address space.

```
Common causes:
  [ ] Data block not marked "Accessible from OPC UA" (Step 2.3)
  [ ] Wrong namespace index (ns=3 is typical, but verify with UaExpert)
  [ ] Typo in NodeId string (quotes are part of the NodeId!)
  [ ] Optimized block access enabled (disable it — see below)

Correct:   ns=3;s="DB_MachineData"."Temperature"
Wrong:     ns=3;s=DB_MachineData.Temperature        ← missing quotes
Wrong:     ns=2;s="DB_MachineData"."Temperature"    ← wrong namespace
```

### Problem 4: Optimized Block Access

S7-1500 data blocks use "Optimized block access" by default. This is efficient for the PLC but can cause issues with OPC-UA access for some older TIA Portal versions.

```
Fix:
  DB_MachineData → Properties → Attributes
  └── [ ] Optimized block access  ← UNCHECK this

  Note: Disabling optimized access changes how the PLC stores
  the DB internally. Recompile and download required.

  Modern TIA Portal (V17+) handles optimized blocks via OPC-UA
  without issues. Only uncheck if you experience problems.
```

### Problem 5: Values Update Slowly

```
Check subscription settings:
  PLC side:
    Properties → OPC UA → Server → Subscriptions
    ├── Min. publishing interval:  100 ms  ← lower = faster
    └── Min. sampling interval:    50 ms   ← lower = faster

  Node-RED side:
    OPC-UA Client → Subscription interval: 500 ms  ← match or higher
```

The PLC's minimum sampling interval limits how fast values update via OPC-UA. Default is 100 ms. For most manufacturing use cases, 500 ms–1 s is sufficient. Going below 100 ms increases PLC CPU load noticeably.

### Problem 6: Certificate Trust

For production with `SignAndEncrypt`:

```bash
# Node-RED generates a self-signed certificate on first connection
# Find it in:
ls ~/.node-red/opcua-certificates/

# The PLC will reject it initially. In TIA Portal:
# Properties → OPC UA → Server → Security → Certificate management
# → Trusted clients → Import → select the Node-RED client certificate

# Similarly, export the PLC's server certificate and add it to:
# ~/.node-red/opcua-certificates/trusted/
```

---

## Production Checklist

Before going live, make sure:

```
Security:
  [ ] Anonymous access disabled
  [ ] User authentication configured
  [ ] Security policy: Basic256Sha256 - SignAndEncrypt
  [ ] Certificates exchanged and trusted
  [ ] Unused security policies disabled

Performance:
  [ ] Subscription intervals appropriate (not too fast)
  [ ] Only needed variables exposed via OPC-UA
  [ ] Session timeout set appropriately
  [ ] Max sessions limited (prevent resource exhaustion)

Reliability:
  [ ] Node-RED auto-reconnect configured
  [ ] Watchdog flow to detect connection loss
  [ ] Dashboard shows connection status indicator
  [ ] Alerts on prolonged disconnection (email/SMS)

Network:
  [ ] Firewall rules documented
  [ ] PLC and Node-RED on dedicated VLAN (OT network)
  [ ] No direct internet exposure of OPC-UA port
  [ ] Consider OPC-UA reverse proxy for DMZ scenarios
```

---

## Next Steps

Once you have the basic PLC-to-dashboard flow working:

1. **Add historical storage** — wire OPC-UA data to TimescaleDB via Node-RED for trend analysis
2. **Set up alerting** — use Node-RED's built-in switch nodes to trigger email/SMS on alarm conditions
3. **Build OEE calculations** — combine status, part counts, and cycle times for real OEE
4. **Scale to multiple PLCs** — create separate OPC-UA subscriptions per PLC, each with its own reconnect logic
5. **Containerize** — run the whole stack (Node-RED + Grafana + TimescaleDB) in Docker for reproducible deployments

The Siemens S7 + OPC-UA + Node-RED combination is one of the most practical IIoT stacks I've worked with. Siemens provides the industrial-grade PLC, OPC-UA provides the standardized protocol, and Node-RED provides the flexibility to connect it to anything — dashboards, databases, cloud services, ERP systems, or machine learning pipelines. The hardest part is getting that first connection working. After that, everything else is flow programming.
