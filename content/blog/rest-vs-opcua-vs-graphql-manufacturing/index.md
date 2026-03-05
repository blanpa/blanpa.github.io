---
title: "REST vs OPC-UA vs GraphQL for Manufacturing Data"
tags: [iiot, opc-ua, rest-api]
description: "Choosing the right API paradigm for industrial data access — practical comparison with manufacturing examples."
date: 2026-04-11
series: ["IIoT"]
---

"Just give me the temperature and status of that machine" — simple enough, right? But the *how* matters enormously. Do you poll a REST endpoint? Subscribe via OPC-UA? Query a GraphQL schema? Each paradigm makes different trade-offs between simplicity, performance, and expressiveness, and in manufacturing those trade-offs have real consequences.

I've used all three in production factories. Here's what I've learned.

---

## The Same Query, Three Ways

Let's start with a concrete example. We want to get the current temperature and status of a CNC machine with ID `cnc-001`.

### REST

```http
GET /api/v1/machines/cnc-001?fields=temperature,status
Accept: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

HTTP/1.1 200 OK
Content-Type: application/json

{
  "machineId": "cnc-001",
  "temperature": {
    "value": 42.7,
    "unit": "°C",
    "timestamp": "2026-04-11T08:30:00Z"
  },
  "status": {
    "value": "Running",
    "timestamp": "2026-04-11T08:29:55Z"
  }
}
```

### OPC-UA

```
ReadRequest:
  NodesToRead:
    - NodeId: ns=2;s=CNC-001.Temperature
      AttributeId: Value
    - NodeId: ns=2;s=CNC-001.Status
      AttributeId: Value

ReadResponse:
  Results:
    - Value: 42.7 (Double)
      StatusCode: Good (0x00000000)
      SourceTimestamp: 2026-04-11T08:30:00.000Z
      ServerTimestamp: 2026-04-11T08:30:00.012Z
    - Value: 1 (Int32, enum: Running=1)
      StatusCode: Good (0x00000000)
      SourceTimestamp: 2026-04-11T08:29:55.000Z
      ServerTimestamp: 2026-04-11T08:29:55.008Z
```

### GraphQL

```graphql
query {
  machine(id: "cnc-001") {
    temperature {
      value
      unit
      timestamp
    }
    status {
      value
      timestamp
    }
  }
}

# Response:
{
  "data": {
    "machine": {
      "temperature": {
        "value": 42.7,
        "unit": "°C",
        "timestamp": "2026-04-11T08:30:00Z"
      },
      "status": {
        "value": "Running",
        "timestamp": "2026-04-11T08:29:55Z"
      }
    }
  }
}
```

Three paradigms, same result. The differences become interesting when the queries get complex.

---

## Deep Dive: REST

### How It Works

REST (Representational State Transfer) models everything as resources accessible via HTTP verbs. Manufacturing data maps to URLs:

```
GET    /api/v1/machines                    → List all machines
GET    /api/v1/machines/cnc-001            → Get one machine
GET    /api/v1/machines/cnc-001/telemetry  → Get sensor data
POST   /api/v1/machines/cnc-001/commands   → Send a command
GET    /api/v1/machines/cnc-001/history?from=2026-04-10&to=2026-04-11
```

### JavaScript Example

```javascript
const axios = require('axios');

async function getMachineData(machineId) {
    const response = await axios.get(
        `https://factory.local/api/v1/machines/${machineId}`,
        {
            params: { fields: 'temperature,status,spindleSpeed' },
            headers: { Authorization: `Bearer ${process.env.API_TOKEN}` },
            timeout: 5000
        }
    );
    return response.data;
}

async function getMultipleMachines(ids) {
    const promises = ids.map(id => getMachineData(id));
    return Promise.all(promises);
}

const data = await getMultipleMachines(['cnc-001', 'cnc-002', 'cnc-003']);
```

### Python Example

```python
import requests

BASE_URL = "https://factory.local/api/v1"
HEADERS = {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}

def get_machine_data(machine_id: str, fields: list[str]) -> dict:
    response = requests.get(
        f"{BASE_URL}/machines/{machine_id}",
        params={"fields": ",".join(fields)},
        headers=HEADERS,
        timeout=5
    )
    response.raise_for_status()
    return response.json()

def get_all_running_machines() -> list[dict]:
    response = requests.get(
        f"{BASE_URL}/machines",
        params={"status": "Running", "limit": 100},
        headers=HEADERS,
        timeout=10
    )
    return response.json()["machines"]
```

### REST Strengths in Manufacturing

- **Universal tooling** — every language, every framework, every developer knows HTTP
- **Firewall-friendly** — port 443, works through proxies and load balancers
- **Stateless** — no persistent connections, simple retry logic
- **Caching** — HTTP caching headers work out of the box with CDNs and reverse proxies
- **API gateways** — rate limiting, auth, monitoring with off-the-shelf tools (Kong, Traefik)

### REST Weaknesses in Manufacturing

- **Over-fetching** — GET `/machines/cnc-001` returns 50 fields when you need 2
- **Under-fetching** — need machine + sensors + alarms? That's 3 requests (N+1 problem)
- **No subscriptions** — polling wastes bandwidth and adds latency
- **No standard data model** — every vendor invents their own JSON schema
- **Polling overhead** — checking 500 machines at 1-second intervals means 500 req/s

---

## Deep Dive: OPC-UA

### How It Works

OPC-UA (Open Platform Communications Unified Architecture) is the industrial automation standard. It provides a rich information model with types, methods, events, and subscriptions — all over a binary TCP protocol (or optionally HTTP/JSON).

```
OPC-UA Address Space
├── Objects
│   ├── Server (metadata, diagnostics)
│   └── Factory
│       ├── Line1
│       │   ├── CNC-001
│       │   │   ├── Temperature    (Variable, Double, EURange: 0-200°C)
│       │   │   ├── SpindleSpeed   (Variable, Double, EURange: 0-12000 RPM)
│       │   │   ├── Status         (Variable, Int32, Enum: 0=Off,1=Run,2=Err)
│       │   │   ├── PartsProduced  (Variable, Int64)
│       │   │   └── Reset()        (Method)
│       │   └── CNC-002
│       │       └── ...
│       └── Line2
│           └── ...
├── Types
│   ├── CNCMachineType
│   │   ├── Temperature  (BaseDataVariableType, Double)
│   │   ├── SpindleSpeed (AnalogItemType, Double)
│   │   └── Status       (MultiStateDiscreteType, Int32)
│   └── ...
└── Views
    └── MaintenanceView (filtered view for maintenance staff)
```

### JavaScript Example (node-opcua)

```javascript
const { OPCUAClient, AttributeIds, TimestampsToReturn } = require("node-opcua");

async function readMachineData() {
    const client = OPCUAClient.create({
        endpointMustExist: false,
        securityMode: 1,  // None (use MessageSecurityMode.SignAndEncrypt in production)
    });

    await client.connect("opc.tcp://192.168.1.100:4840");
    const session = await client.createSession();

    const nodesToRead = [
        { nodeId: "ns=2;s=CNC-001.Temperature", attributeId: AttributeIds.Value },
        { nodeId: "ns=2;s=CNC-001.Status", attributeId: AttributeIds.Value },
    ];

    const results = await session.read(nodesToRead);

    results.forEach((result, i) => {
        console.log(`${nodesToRead[i].nodeId}: ${result.value.value} [${result.statusCode.name}]`);
    });

    // Subscriptions — the real power of OPC-UA
    const subscription = await session.createSubscription2({
        requestedPublishingInterval: 500,
        maxNotificationsPerPublish: 100,
    });

    const monitoredItem = await subscription.monitor(
        { nodeId: "ns=2;s=CNC-001.Temperature", attributeId: AttributeIds.Value },
        { samplingInterval: 250, discardOldest: true, queueSize: 10 },
        TimestampsToReturn.Both
    );

    monitoredItem.on("changed", (dataValue) => {
        console.log(`Temperature changed: ${dataValue.value.value}°C`);
    });
}
```

### Python Example (asyncua)

```python
from asyncua import Client
import asyncio

async def read_machine_data():
    async with Client("opc.tcp://192.168.1.100:4840") as client:
        temp_node = client.get_node("ns=2;s=CNC-001.Temperature")
        status_node = client.get_node("ns=2;s=CNC-001.Status")

        temperature = await temp_node.read_value()
        status = await status_node.read_value()

        print(f"Temperature: {temperature}°C")
        print(f"Status: {status}")

        # Subscribe to changes
        handler = SubHandler()
        subscription = await client.create_subscription(500, handler)
        await subscription.subscribe_data_change([temp_node, status_node])

        await asyncio.sleep(3600)  # listen for 1 hour


class SubHandler:
    def datachange_notification(self, node, val, data):
        print(f"Value changed: {node} -> {val}")

asyncio.run(read_machine_data())
```

### OPC-UA Strengths in Manufacturing

- **Rich type system** — engineering units, ranges, enums, structured types built in
- **Native subscriptions** — server pushes changes, no polling needed
- **Browsable** — clients can discover the address space at runtime
- **Methods** — call functions on the server (reset counters, trigger actions)
- **Security** — X.509 certificates, encrypted transport, user authentication
- **Industry standard** — every major PLC vendor supports it

### OPC-UA Weaknesses in Manufacturing

- **Complexity** — the spec is 1400+ pages, the learning curve is steep
- **Firewall issues** — binary TCP on port 4840 doesn't traverse web proxies easily
- **Heavy client libraries** — no simple `curl` equivalent, need dedicated SDK
- **Session management** — stateful connections require keepalive handling
- **Web unfriendly** — can't use from a browser without a gateway

---

## Deep Dive: GraphQL

### How It Works

GraphQL lets the client define exactly what data it wants using a query language. The server provides a schema, and the client writes queries against it. No over-fetching, no under-fetching.

### Schema Definition

```graphql
type Machine {
  id: ID!
  name: String!
  line: Line!
  temperature: SensorReading
  spindleSpeed: SensorReading
  status: MachineStatus!
  partsProduced: Int!
  alarms(severity: Int): [Alarm!]!
  history(from: DateTime!, to: DateTime!, interval: String): [HistoryPoint!]!
}

type SensorReading {
  value: Float!
  unit: String!
  quality: Quality!
  timestamp: DateTime!
}

type Alarm {
  id: ID!
  message: String!
  severity: Int!
  timestamp: DateTime!
  acknowledged: Boolean!
}

type Query {
  machine(id: ID!): Machine
  machines(line: String, status: MachineStatus): [Machine!]!
}

type Subscription {
  machineUpdated(id: ID!): Machine!
  alarmTriggered(line: String): Alarm!
}
```

### JavaScript Example

```javascript
import { GraphQLClient, gql } from 'graphql-request';

const client = new GraphQLClient('https://factory.local/graphql', {
    headers: { Authorization: `Bearer ${process.env.API_TOKEN}` },
});

const GET_MACHINE = gql`
    query GetMachine($id: ID!) {
        machine(id: $id) {
            temperature { value unit timestamp }
            status { value timestamp }
            alarms(severity: 3) {
                message
                timestamp
            }
        }
    }
`;

const data = await client.request(GET_MACHINE, { id: 'cnc-001' });

// Get data from multiple machines in ONE request
const GET_LINE_STATUS = gql`
    query GetLineStatus($line: String!) {
        machines(line: $line) {
            id
            name
            status { value }
            temperature { value unit }
            partsProduced
        }
    }
`;

const lineData = await client.request(GET_LINE_STATUS, { line: 'Line1' });
```

### Python Example

```python
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

transport = AIOHTTPTransport(
    url="https://factory.local/graphql",
    headers={"Authorization": f"Bearer {os.environ['API_TOKEN']}"}
)

client = Client(transport=transport, fetch_schema_from_transport=True)

query = gql("""
    query GetMachineWithHistory($id: ID!, $from: DateTime!, $to: DateTime!) {
        machine(id: $id) {
            temperature { value unit }
            status { value }
            history(from: $from, to: $to, interval: "1h") {
                timestamp
                temperature
                spindleSpeed
            }
            alarms(severity: 3) {
                message
                severity
                timestamp
            }
        }
    }
""")

result = client.execute(query, variable_values={
    "id": "cnc-001",
    "from": "2026-04-10T00:00:00Z",
    "to": "2026-04-11T00:00:00Z"
})
```

### GraphQL Strengths in Manufacturing

- **No over-fetching** — request exactly the fields you need
- **No under-fetching** — get machine + sensors + alarms in one query
- **Strong typing** — schema provides a contract between client and server
- **Introspection** — clients can discover the schema at runtime
- **Subscriptions** — real-time updates via WebSocket
- **Aggregation** — one query can combine data from multiple backend sources

### GraphQL Weaknesses in Manufacturing

- **Not an industry standard** — no PLC vendor exposes a GraphQL endpoint natively
- **Gateway required** — you need a server that translates GraphQL to actual data sources
- **Caching is harder** — POST requests don't cache like GET requests
- **Complexity budget** — deeply nested queries can overload the server
- **Overkill for simple reads** — if you always need the same fields, REST is simpler

---

## Comparison Table

| Aspect | REST | OPC-UA | GraphQL |
|--------|------|--------|---------|
| **Transport** | HTTP/1.1, HTTP/2 | TCP binary (or HTTP/JSON) | HTTP (queries), WebSocket (subs) |
| **Data Format** | JSON (typically) | Binary (UA Binary) | JSON |
| **Schema/Model** | OpenAPI (optional) | Built-in type system | SDL (required) |
| **Discovery** | Swagger/OpenAPI | Browse address space | Introspection |
| **Subscriptions** | SSE / WebSocket (add-on) | Native (optimized) | WebSocket (native) |
| **Authentication** | Bearer/OAuth2/API Key | X.509 certificates + user | Bearer/OAuth2/API Key |
| **Encryption** | TLS (HTTPS) | Built-in (security modes) | TLS (HTTPS) |
| **Latency** | ~10–50ms per request | ~1–5ms per read | ~10–50ms per query |
| **Bandwidth** | Medium (JSON overhead) | Low (binary encoding) | Low (exact fields only) |
| **Browser support** | Native | Requires gateway | Native |
| **Tooling** | Excellent (Postman, curl) | Moderate (UaExpert, SDKs) | Good (GraphiQL, Apollo) |
| **Learning curve** | Low | High | Medium |
| **Industry adoption** | IT systems, web apps | PLCs, SCADA, automation | Dashboards, aggregation |

---

## Real-Time Subscriptions Compared

Real-time data is critical in manufacturing. Here's how each paradigm handles it:

```
REST (Polling)
──────────────
Client                          Server
  │──GET /temperature──────────→│
  │←──{ value: 42.7 }──────────│
  │          (wait 1s)          │
  │──GET /temperature──────────→│
  │←──{ value: 42.7 }──────────│  ← wasted request, no change
  │          (wait 1s)          │
  │──GET /temperature──────────→│
  │←──{ value: 43.1 }──────────│  ← change detected after up to 1s

OPC-UA (Subscription)
─────────────────────
Client                          Server
  │──CreateSubscription────────→│
  │──MonitoredItemCreate───────→│
  │←──Publish(42.7)────────────│  ← initial value
  │                             │  (server monitors internally)
  │←──Publish(43.1)────────────│  ← pushed immediately on change
  │←──Publish(43.8)────────────│  ← pushed immediately on change

GraphQL (WebSocket Subscription)
────────────────────────────────
Client                          Server
  │──WS: subscribe { temp }───→│
  │←──{ value: 42.7 }─────────│  ← initial value
  │                             │  (server pushes on change)
  │←──{ value: 43.1 }─────────│  ← pushed on change
  │←──{ value: 43.8 }─────────│  ← pushed on change
```

OPC-UA subscriptions are the most efficient — the server samples internally and only sends changes that exceed a deadband (configurable). This is critical when you have thousands of tags.

GraphQL subscriptions work well but depend on the gateway implementation. If the gateway polls the data source underneath, you've just moved the polling problem.

---

## Data Modeling Comparison

How each paradigm represents a CNC machine with engineering metadata:

### REST: Flat JSON (you define the schema)

```json
{
  "machineId": "cnc-001",
  "machineName": "CNC Mill #1",
  "temperature": 42.7,
  "temperatureUnit": "°C",
  "temperatureMin": 0,
  "temperatureMax": 200,
  "spindleSpeed": 2450,
  "spindleSpeedUnit": "RPM",
  "status": "Running",
  "statusOptions": ["Off", "Running", "Error", "Maintenance"]
}
```

No standard. Every API inventor reinvents how to represent units, ranges, and enums. Consumer must read docs.

### OPC-UA: Typed Address Space (standardized)

```
CNC-001 (CNCMachineType)
├── Temperature
│   ├── Value:          42.7 (Double)
│   ├── EngineeringUnits: °C (EUInformation)
│   ├── EURange:        { Low: 0.0, High: 200.0 }
│   ├── InstrumentRange: { Low: -40.0, High: 250.0 }
│   └── Description:    "Coolant temperature"
├── SpindleSpeed
│   ├── Value:          2450.0 (Double)
│   ├── EngineeringUnits: RPM
│   └── EURange:        { Low: 0.0, High: 12000.0 }
└── Status
    ├── Value:          1 (Int32)
    └── EnumStrings:    ["Off", "Running", "Error", "Maintenance"]
```

Rich, standardized metadata. Any OPC-UA client knows how to interpret `EURange` and `EngineeringUnits` without reading documentation.

### GraphQL: Schema-Defined (you define it, but it's explicit)

```graphql
type SensorReading {
  value: Float!
  unit: String!
  min: Float
  max: Float
  quality: Quality!
  timestamp: DateTime!
}

enum MachineStatus {
  OFF
  RUNNING
  ERROR
  MAINTENANCE
}
```

Explicit contract, but you have to build it. No industrial standard exists for GraphQL schemas in manufacturing (yet).

---

## Performance Comparison

Benchmarked on a typical industrial edge PC (Intel i5, 16GB RAM, Gigabit LAN):

| Scenario | REST | OPC-UA | GraphQL |
|----------|------|--------|---------|
| **Read 1 value** | ~15ms | ~2ms | ~20ms |
| **Read 100 values** | ~15ms (batch) or ~800ms (100 calls) | ~5ms (batch read) | ~25ms (one query) |
| **Read 1000 values** | ~100ms (batch) | ~15ms (batch read) | ~80ms (one query) |
| **Subscription (1000 tags, 1s)** | 1000 req/s (polling) | ~50 notifications/s (on change) | ~50 messages/s (on change) |
| **Network bandwidth (1000 tags/s)** | ~500 KB/s (JSON polling) | ~20 KB/s (binary, on change) | ~100 KB/s (JSON, on change) |

OPC-UA is dramatically more efficient for high-volume, real-time data — binary encoding and change-based subscriptions reduce both latency and bandwidth.

REST scales fine for moderate loads but hits limits when polling hundreds of values per second.

GraphQL sits in the middle — efficient queries but JSON overhead and no binary encoding.

---

## When Each Paradigm Wins

### REST Wins When...

- Building **web dashboards** — every JavaScript framework has HTTP built in
- Integrating with **cloud services** — Azure IoT Hub, AWS IoT, all REST-based
- The data consumer is a **mobile app** or **SPA**
- You need **simple integration** — `curl` is your debugging tool
- **Caching** is important — CDN, browser cache, reverse proxy
- The **update rate is slow** — readings every 5+ seconds

### OPC-UA Wins When...

- Connecting to **PLCs and automation controllers** — it's the native language
- **Real-time subscriptions** with sub-second latency are required
- The data model has **rich engineering metadata** (units, ranges, types)
- You need **methods** — calling functions on equipment
- **Security** requirements are strict (X.509 mutual auth)
- You're building **OT-to-OT** integrations (SCADA, DCS, historian)

### GraphQL Wins When...

- Building a **unified data layer** over multiple backends
- Dashboards need **flexible queries** — different screens show different fields
- You have **multiple data sources** — PLCs + MES + ERP + historian
- The frontend team wants **exact data, no more, no less**
- You're building a **manufacturing data platform** or **digital twin UI**

---

## Hybrid Architecture

In practice, most factories use a combination:

```
┌─────────────────────────────────────────────────────────────┐
│                       Shop Floor                             │
│                                                              │
│   PLC ──OPC-UA──→ Edge Gateway ──MQTT──→ Broker             │
│   PLC ──OPC-UA──→ Edge Gateway ──MQTT──→ Broker             │
│                                                              │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────┐
│                    Server Room │                              │
│                                │                             │
│   ┌────────────┐     ┌────────┴───────┐    ┌─────────────┐  │
│   │  Historian  │←───│  Data Platform  │──→│  REST API   │  │
│   │  (OPC-UA    │    │  (Node-RED /    │   │  (External) │  │
│   │   HDA)      │    │   Custom)       │   └─────────────┘  │
│   └────────────┘     └────────┬───────┘                     │
│                               │                              │
│                      ┌────────┴───────┐                      │
│                      │  GraphQL API   │                      │
│                      │  (Aggregation) │                      │
│                      └────────┬───────┘                      │
│                               │                              │
└───────────────────────────────┼──────────────────────────────┘
                                │
┌───────────────────────────────┼──────────────────────────────┐
│                          Cloud │                              │
│                                │                             │
│   ┌────────────┐     ┌────────┴───────┐    ┌─────────────┐  │
│   │  Dashboard  │←───│  API Gateway   │──→│  ML Pipeline │  │
│   │  (React)    │    │  (REST/GraphQL)│   │  (Python)    │  │
│   └────────────┘     └───────────────┘    └─────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**OPC-UA** handles the PLC-to-edge layer where performance and type safety matter. **MQTT** carries data from edge to server. **GraphQL** provides a flexible query layer for dashboards and applications. **REST** exposes simple endpoints for external integrations and cloud services.

---

## Practical Advice

1. **Don't fight the ecosystem.** If your data lives in PLCs, use OPC-UA. If it lives in databases, use REST or GraphQL. Don't force a paradigm where it doesn't belong.

2. **Gateway pattern.** Build a gateway that speaks OPC-UA to PLCs and exposes REST/GraphQL to applications. This decouples OT from IT and lets each side use its native tools.

3. **Start with REST.** If you're unsure, REST is the safest default. Every tool and every developer understands it. You can add OPC-UA or GraphQL later when the limitations become clear.

4. **GraphQL is a luxury, not a necessity.** If you always query the same fields, REST is simpler. GraphQL shines when you have many different consumers with different data needs.

5. **OPC-UA subscriptions are worth learning.** The setup is complex, but for real-time manufacturing data, nothing beats OPC-UA's efficiency. The investment pays off at scale.
