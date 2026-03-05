---
title: "MQTT vs Sparkplug B vs NATS vs OPC-UA — Which Protocol for Industrial IoT?"
tags: [iiot, mqtt, nats, opc-ua, node-red]
description: "A practical comparison of four industrial messaging protocols — when to use which, with architecture examples and code snippets."
date: 2026-03-05
series: ["IIoT"]
---

Choosing the right messaging protocol for an Industrial IoT project is one of the most impactful architectural decisions you'll make. Pick the wrong one and you'll spend months working around its limitations. Pick the right one and data flows effortlessly from sensor to cloud.

In this post I compare **MQTT**, **Sparkplug B**, **NATS**, and **OPC-UA** — four protocols I work with daily in industrial environments. No theoretical fluff — just practical differences, real trade-offs, and concrete examples.

---

## The Quick Overview

| | MQTT | Sparkplug B | NATS | OPC-UA |
|--|------|-------------|------|--------|
| **Origin** | IBM, 1999 | Eclipse Foundation | CNCF | OPC Foundation |
| **Transport** | TCP/WebSocket | MQTT (layer on top) | TCP/WebSocket | TCP/HTTPS |
| **Pattern** | Pub/Sub | Pub/Sub | Pub/Sub, Req/Reply, Queue | Client/Server, Pub/Sub |
| **Data Model** | None (raw bytes) | Defined (metrics, types) | None (raw bytes) | Rich information model |
| **Persistence** | Retained messages | Birth/Death certificates | JetStream streams | Built-in historian |
| **Typical Latency** | 1–10 ms | 1–10 ms | < 1 ms | 5–50 ms |
| **Throughput** | ~100K msg/s | ~80K msg/s | ~10M msg/s | ~50K msg/s |
| **Best For** | Simple sensor telemetry | Standardized SCADA | Cloud-native, edge mesh | OT/automation |

---

## MQTT — The Universal Connector

MQTT is the lingua franca of IoT. Lightweight, simple, and supported by virtually every device and platform. If your sensor has a network stack, it probably speaks MQTT.

### How It Works

MQTT uses a **broker-based publish/subscribe** model. Clients publish messages to topics, and other clients subscribe to those topics. The broker handles routing.

```
Sensor A ──publish──→ ┌──────────┐ ──→ Subscriber 1
                      │  Broker  │
Sensor B ──publish──→ │ (Mosquitto)│ ──→ Subscriber 2
                      └──────────┘
```

### Example: Temperature Sensor

Publishing a temperature reading:

```python
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("broker.local", 1883)

payload = json.dumps({
    "temperature": 72.5,
    "unit": "celsius",
    "timestamp": "2026-03-05T10:30:00Z"
})

client.publish("factory/line1/machine3/temperature", payload, qos=1)
```

Subscribing to all sensors on a production line:

```python
def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    print(f"{msg.topic}: {data['temperature']}°C")

client.subscribe("factory/line1/+/temperature")
client.on_message = on_message
client.loop_forever()
```

### Strengths

- Extremely **lightweight** — runs on microcontrollers with 32KB RAM
- **QoS levels** (0, 1, 2) for delivery guarantees
- **Retained messages** — new subscribers get the last known value
- **Last Will and Testament** — automatic offline detection
- Massive ecosystem: Mosquitto, EMQX, HiveMQ, VerneMQ

### Weaknesses

- **No data model** — payload is raw bytes, you decide the format (JSON, Protobuf, etc.)
- **No topic namespace standard** — every company invents their own topic tree
- **No request/reply** — you have to build it yourself with correlated topics
- **Broker is a single point of failure** — clustering requires commercial brokers
- **No built-in persistence** — messages are gone once delivered

### When to Use MQTT

- Constrained edge devices (ESP32, Raspberry Pi)
- Simple telemetry: send sensor values to a cloud platform
- Brownfield integration where devices already speak MQTT
- When you need maximum device compatibility

---

## Sparkplug B — MQTT with an Industrial Brain

Sparkplug B is not a separate protocol — it's a **specification on top of MQTT** that solves MQTT's biggest weaknesses for industrial use: no data model, no state management, and no standardized topic namespace.

### How It Differs from Plain MQTT

```
Plain MQTT:
  Topic:   factory/line1/machine3/temperature
  Payload: {"value": 72.5}  ← you decide the format

Sparkplug B:
  Topic:   spBv1.0/FactoryGroup/DDATA/Line1/Machine3
  Payload: Protobuf-encoded metrics with types, timestamps, and aliases
```

### The Birth/Death Certificate Model

Sparkplug introduces **NBIRTH** (Node Birth), **DBIRTH** (Device Birth), **NDEATH**, and **DDEATH** messages. This creates a **state-aware** system:

```
1. Edge Node connects    → publishes NBIRTH (declares all metrics)
2. Device comes online   → publishes DBIRTH (declares device metrics)
3. Data changes          → publishes DDATA (only changed metrics)
4. Device goes offline   → broker publishes DDEATH (via LWT)
5. Edge Node disconnects → broker publishes NDEATH (via LWT)
```

### Example: Sparkplug Metric

```python
from sparkplug_b import MetricDataType, Payload

payload = Payload()
metric = payload.metrics.add()
metric.name = "Temperature"
metric.datatype = MetricDataType.Float
metric.float_value = 72.5
metric.timestamp = int(time.time() * 1000)

# Alias-based updates — after BIRTH, only send alias + value
metric_update = payload.metrics.add()
metric_update.alias = 1  # "Temperature" was alias 1 in BIRTH
metric_update.float_value = 73.1
```

### Topic Namespace

Sparkplug defines a strict topic structure:

```
spBv1.0/{group_id}/{message_type}/{edge_node_id}/{device_id}

Examples:
  spBv1.0/Plant1/NBIRTH/Gateway1        → Node birth
  spBv1.0/Plant1/DBIRTH/Gateway1/PLC1   → Device birth
  spBv1.0/Plant1/DDATA/Gateway1/PLC1    → Device data
  spBv1.0/Plant1/DCMD/Gateway1/PLC1     → Device command
```

### Strengths

- **Standardized data model** — types, timestamps, metadata for every metric
- **State awareness** — always know which devices are online and what they report
- **Bandwidth efficient** — alias-based encoding, only changed values sent
- **Interoperable** — any Sparkplug-compliant client understands any Sparkplug publisher
- **SCADA integration** — Ignition, Inductive Automation, and others natively support it

### Weaknesses

- **Still relies on MQTT broker** — inherits broker limitations
- **Protobuf encoding** — harder to debug than JSON (need decoding tools)
- **More complex** than plain MQTT — birth/death lifecycle adds overhead
- **Limited ecosystem** compared to raw MQTT

### When to Use Sparkplug B

- SCADA systems where you need a standardized namespace
- Multi-vendor environments where plain MQTT becomes chaotic
- When a central application (like Ignition) needs to auto-discover devices
- Brownfield MQTT infrastructure where you want to add structure

---

## NATS — The Cloud-Native Speed Demon

NATS comes from the cloud-native world (it's a CNCF project) but is increasingly used in industrial IoT for its raw speed, operational simplicity, and built-in persistence via JetStream.

### Architecture

Unlike MQTT's broker model, NATS uses a **mesh of servers** that form a cluster. There's no single point of failure.

```
                    ┌──────────┐
Edge Device 1 ───→ │  NATS-1  │ ←─── Cloud Service A
                    └────┬─────┘
                         │ cluster
                    ┌────┴─────┐
Edge Device 2 ───→ │  NATS-2  │ ←─── Cloud Service B
                    └────┬─────┘
                         │ cluster
                    ┌────┴─────┐
Edge Device 3 ───→ │  NATS-3  │ ←─── Dashboard
                    └──────────┘
```

### Example: Pub/Sub

```go
nc, _ := nats.Connect("nats://nats.local:4222")

// Publish
nc.Publish("factory.line1.machine3.temperature",
    []byte(`{"value": 72.5, "unit": "celsius"}`))

// Subscribe with wildcards
nc.Subscribe("factory.line1.*.temperature", func(msg *nats.Msg) {
    fmt.Printf("Received: %s\n", string(msg.Data))
})
```

### Example: Request/Reply (built-in)

Something MQTT can't do natively:

```go
// Service: responds to recipe requests
nc.Subscribe("recipe.get", func(msg *nats.Msg) {
    recipe := loadRecipe(string(msg.Data))
    msg.Respond([]byte(recipe))
})

// Client: request with timeout
reply, err := nc.Request("recipe.get", []byte("product-42"), 2*time.Second)
fmt.Println(string(reply.Data))
```

### JetStream — Persistent Streaming

JetStream adds persistence, replay, and exactly-once delivery:

```go
js, _ := nc.JetStream()

// Create a stream that retains messages
js.AddStream(&nats.StreamConfig{
    Name:      "SENSORS",
    Subjects:  []string{"factory.>"},
    Retention: nats.LimitsPolicy,
    MaxAge:    24 * time.Hour,
})

// Publish (persisted)
js.Publish("factory.line1.machine3.temperature",
    []byte(`{"value": 72.5}`))

// Durable consumer — survives restarts
sub, _ := js.PullSubscribe("factory.line1.>", "analytics-consumer")
msgs, _ := sub.Fetch(10)
```

### Key-Value Store

NATS includes a distributed key-value store — no need for Redis or etcd:

```go
kv, _ := js.CreateKeyValue(&nats.KeyValueConfig{
    Bucket: "machine-config",
})

kv.Put("machine3.setpoint", []byte("72.5"))
entry, _ := kv.Get("machine3.setpoint")
fmt.Println(string(entry.Value()))

// Watch for changes in real-time
watcher, _ := kv.Watch("machine3.*")
for update := range watcher.Updates() {
    fmt.Printf("%s = %s\n", update.Key(), string(update.Value()))
}
```

### Strengths

- **Blazing fast** — 10M+ messages/second
- **Request/Reply** — native, not hacked on top
- **JetStream** — persistence, replay, exactly-once delivery built-in
- **Key-Value Store** — distributed config without external dependencies
- **Clustering** — true HA with no single point of failure
- **Leaf Nodes** — edge NATS servers that sync with cloud clusters
- **Embedded server** — run NATS inside your application

### Weaknesses

- **No data model** — same as MQTT, payload is raw bytes
- **No OT industry standard** — not recognized by automation vendors (yet)
- **Less device support** — no ESP32 or microcontroller clients
- **Less tooling** — fewer GUI management tools than MQTT

### When to Use NATS

- High-throughput data pipelines (vibration data, high-frequency sensors)
- Edge-to-cloud mesh architectures with leaf nodes
- Microservice communication on the edge
- When you need request/reply patterns
- When you want persistence without external databases

---

## OPC-UA — The Industrial Standard

OPC-UA is the **established standard** in factory automation. Every major PLC vendor supports it: Siemens, Beckhoff, Allen-Bradley, ABB, B&R, Mitsubishi. If you work in OT, you can't avoid it.

### Information Model

OPC-UA's killer feature is its **rich information model**. It's not just values — it's a browsable tree of objects with types, relationships, and metadata:

```
Root
├── Objects
│   ├── Server (diagnostics, capabilities)
│   └── Factory
│       ├── Line1
│       │   ├── Machine3
│       │   │   ├── Temperature (Float, °C, range: 0-200)
│       │   │   ├── Speed (Int32, RPM, range: 0-3000)
│       │   │   ├── Status (Enum: Running, Stopped, Error)
│       │   │   └── Methods
│       │   │       ├── Start()
│       │   │       └── Stop()
│       │   └── Machine4
│       └── Line2
└── Types
    └── MachineType (defines the structure above)
```

### Example: Reading Values

```python
from opcua import Client

client = Client("opc.tcp://plc.local:4840")
client.connect()

# Browse the address space
root = client.get_root_node()
objects = client.get_objects_node()

# Read a specific node
temp_node = client.get_node("ns=2;s=Machine3.Temperature")
value = temp_node.get_value()
data_type = temp_node.get_data_type_as_variant_type()
print(f"Temperature: {value} (type: {data_type})")

# Read with full metadata
data_value = temp_node.get_data_value()
print(f"Value: {data_value.Value.Value}")
print(f"Status: {data_value.StatusCode}")
print(f"Timestamp: {data_value.SourceTimestamp}")
```

### Example: Subscriptions

```python
class SubHandler:
    def datachange_notification(self, node, val, data):
        print(f"{node} changed to {val}")

handler = SubHandler()
subscription = client.create_subscription(500, handler)  # 500ms interval

# Monitor multiple nodes
nodes = [
    client.get_node("ns=2;s=Machine3.Temperature"),
    client.get_node("ns=2;s=Machine3.Speed"),
    client.get_node("ns=2;s=Machine3.Status"),
]
subscription.subscribe_data_change(nodes)
```

### Example: Calling Methods

```python
# Call a method on the PLC
machine = client.get_node("ns=2;s=Machine3")
method = client.get_node("ns=2;s=Machine3.Start")

# Start the machine with parameters
result = machine.call_method(method, 1500)  # target speed: 1500 RPM
print(f"Method result: {result}")
```

### Strengths

- **Rich information model** — self-describing, browsable, typed
- **Industry standard** — every PLC vendor supports it
- **Security** — X.509 certificates, user authentication, encrypted transport
- **Methods** — call functions on PLCs remotely
- **Historical data** — built-in historian access
- **Discovery** — servers announce themselves on the network
- **Companion specifications** — standardized models for robotics, CNC, packaging, etc.

### Weaknesses

- **Complex** — the specification is 1,200+ pages
- **Slower** — higher latency than MQTT or NATS
- **Heavy** — not suitable for constrained devices
- **Client/Server** — no native pub/sub across systems (OPC-UA Pub/Sub exists but adoption is low)
- **Licensing** — some SDKs are expensive

### When to Use OPC-UA

- PLC and SCADA integration (this is what it's built for)
- Multi-vendor automation (Siemens + Beckhoff + ABB in one factory)
- When you need typed, self-describing data with browse capability
- Compliance-driven environments (Industrie 4.0, RAMI 4.0)

---

## Decision Matrix

```
                    ┌─────────────────────────────────────────────┐
                    │        What's your primary use case?        │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
             Sensor Telemetry    PLC Integration    High-Throughput
             (edge devices)      (automation)       Data Pipeline
                    │                  │                  │
              ┌─────┴─────┐           │            ┌─────┴─────┐
              ▼           ▼           ▼            ▼           ▼
          Simple?    Need SCADA    OPC-UA       Need        Cloud-
              │      standard?        │        Persistence?  native?
              │           │           │            │           │
          ┌───┴──┐   ┌───┴──┐        │       ┌───┴──┐   ┌───┴──┐
          ▼      ▼   ▼      ▼        │       ▼      ▼   ▼      ▼
        MQTT  Spark  Spark  MQTT     Done    NATS   MQTT  NATS  NATS
              plug   plug                   (JS)   (+DB)
```

## Combining Protocols

In practice, most industrial architectures use **multiple protocols**. Here's a pattern I use frequently:

```
┌─────────┐  OPC-UA   ┌───────────┐  NATS    ┌───────────┐
│ Siemens ├──────────→│           ├─────────→│   Cloud   │
│   PLC   │           │  Node-RED │          │ Analytics │
└─────────┘           │  (Edge)   │  MQTT    ┌───────────┐
┌─────────┐  MQTT     │           ├─────────→│ Dashboard │
│  ESP32  ├──────────→│           │          └───────────┘
│ Sensors │           └───────────┘
└─────────┘
```

- **OPC-UA** talks to the PLCs (typed data, methods, browse)
- **MQTT** collects data from constrained sensors
- **NATS** moves everything to the cloud (fast, persistent, scalable)

The key insight: **protocols are tools, not religions**. Use each where it excels.

---

## Conclusion

| Choose... | When... |
|-----------|---------|
| **MQTT** | You need maximum device compatibility and simplicity |
| **Sparkplug B** | You have MQTT but need structure, state management, and SCADA integration |
| **NATS** | You need speed, request/reply, persistence, and cloud-native architecture |
| **OPC-UA** | You're integrating with PLCs and need typed, self-describing industrial data |

There's no single "best" protocol. The best industrial IoT architecture uses the right protocol at each layer — and Node-RED makes it easy to bridge between all of them.
