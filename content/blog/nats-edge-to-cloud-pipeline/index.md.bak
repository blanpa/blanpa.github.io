---
title: "Building a NATS-based Edge-to-Cloud Pipeline for Industrial IoT"
tags: [iiot, nats, node-red, docker]
description: "Architecture guide for connecting factory floor sensors to cloud analytics using NATS leaf nodes, JetStream, and key-value stores."
date: 2026-03-21
series: ["IIoT"]
---

MQTT got us far. Every IIoT project I've worked on started with Mosquitto, some topics, and QoS 1. It works — until you need message replay, exactly-once delivery, or synchronizing configuration across 30 factory sites. Then you start bolting on Kafka for persistence, Redis for key-value state, and a custom sync mechanism for edge-to-cloud. Three systems to operate, three failure modes to debug at 2 AM.

**NATS** replaces all three. It's a single binary that handles pub/sub messaging, persistent streams (JetStream), key-value stores, and edge-to-cloud synchronization (leaf nodes) — all with built-in clustering and zero external dependencies.

This post walks through a complete NATS-based architecture for industrial IoT.

---

## Architecture Overview

```
                            ┌──────────────────────┐
                            │    Cloud NATS Cluster │
                            │  ┌────┐ ┌────┐ ┌────┐│
                            │  │ N1 │ │ N2 │ │ N3 ││
                            │  └──┬─┘ └──┬─┘ └──┬─┘│
                            │     └──────┼──────┘  │
                            │            │         │
                            │    JetStream Streams  │
                            │    KV Stores          │
                            │    Object Store       │
                            └────────┬─────────────┘
                                     │
                          TLS / WebSocket
                          (NAT-friendly)
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────┴─────┐┌────┴──────┐┌────┴──────┐
              │  Factory A ││ Factory B ││ Factory C │
              │  Leaf Node ││ Leaf Node ││ Leaf Node │
              │  ┌───────┐ ││ ┌───────┐ ││ ┌───────┐ │
              │  │ NATS  │ ││ │ NATS  │ ││ │ NATS  │ │
              │  │ Edge  │ ││ │ Edge  │ ││ │ Edge  │ │
              │  └───┬───┘ ││ └───┬───┘ ││ └───┬───┘ │
              │      │     ││     │     ││     │     │
              │  ┌───┴───┐ ││ ┌───┴───┐ ││ ┌───┴───┐ │
              │  │Sensors│ ││ │Sensors│ ││ │Sensors│ │
              │  │PLCs   │ ││ │PLCs   │ ││ │PLCs   │ │
              │  │Gateways│││ │Gateways│││ │Gateways││
              │  └───────┘ ││ └───────┘ ││ └───────┘ │
              └───────────┘└───────────┘└───────────┘
```

Each factory runs a local NATS server as a **leaf node**. Sensors and PLCs publish to the local server with sub-millisecond latency. The leaf node selectively forwards messages to the cloud cluster over a single TLS connection — NAT-friendly, firewall-friendly, resumable on disconnect.

---

## Why NATS Over MQTT + Kafka?

| Capability | MQTT + Kafka | NATS (with JetStream) |
|-----------|-------------|----------------------|
| **Pub/Sub** | MQTT broker | NATS core |
| **Persistent streams** | Kafka | JetStream |
| **Key-value store** | Redis / etcd | NATS KV |
| **Edge-to-cloud sync** | Custom bridge | Leaf nodes (built-in) |
| **Clustering** | MQTT: limited, Kafka: ZooKeeper/KRaft | Built-in RAFT |
| **Message replay** | Kafka (complex consumer groups) | JetStream (simple) |
| **Exactly-once** | Kafka (idempotent producer) | JetStream (dedup window) |
| **Dependencies** | 3 systems (MQTT, Kafka, Redis) | 1 binary |
| **Memory footprint** | Kafka: 1+ GB, MQTT: 50 MB, Redis: 100 MB | 50–200 MB total |
| **Ops complexity** | High (3 systems to monitor, upgrade, backup) | Low (1 system) |

The operational argument is the strongest: running and monitoring one system is fundamentally simpler than running three.

---

## Subject Naming Convention

A well-designed subject hierarchy is critical. For industrial IoT, I use this pattern:

```
{org}.{site}.{area}.{line}.{machine}.{sensor}.{metric}

Examples:
  acme.munich.hall-a.line-1.cnc-001.spindle.vibration.rms
  acme.munich.hall-a.line-1.cnc-001.spindle.vibration.spectrum
  acme.munich.hall-a.line-1.cnc-001.motor.current
  acme.munich.hall-a.line-1.cnc-001.coolant.temperature
  acme.munich.hall-a.line-1.cnc-001.status.operational_state
```

### Wildcards

NATS supports two wildcards that make this hierarchy powerful:

```
acme.munich.hall-a.line-1.*.spindle.vibration.rms
  → All machines on line 1, spindle vibration RMS

acme.munich.hall-a.>
  → Everything from Hall A (all lines, machines, sensors)

acme.*.*.*.*.*.temperature
  → All temperature readings across all sites
```

The `*` matches a single token, `>` matches one or more tokens (only at the end). This lets cloud analytics subscribe to broad patterns while edge devices publish to specific subjects.

### Reserved Subjects

```
_EVENTS.>                  → NATS system events
$JS.>                      → JetStream internal
_KV.>                      → Key-value store internal

acme.*.config.>            → Machine configuration (KV-backed)
acme.*.alert.>             → Alert messages (priority routing)
acme.*.command.>           → Commands from cloud to edge
acme.*.model.>             → ML model updates
```

---

## JetStream: Persistent Streams

Core NATS is fire-and-forget — if nobody's listening, the message is lost. JetStream adds **persistence and replay**, turning NATS into an event log.

### Stream Configuration

```json
{
  "name": "TELEMETRY",
  "subjects": ["acme.*.*.*.*.*.vibration.>", "acme.*.*.*.*.*.temperature"],
  "retention": "limits",
  "max_bytes": 10737418240,
  "max_age": 604800000000000,
  "storage": "file",
  "num_replicas": 3,
  "discard": "old",
  "duplicate_window": 120000000000,
  "compression": "s2"
}
```

This stream captures all vibration and temperature data, retains it for 7 days (or until 10 GB is reached), deduplicates messages within a 2-minute window, and replicates across 3 nodes with S2 compression.

### Consumer Types

| Consumer Type | Use Case | Behavior |
|--------------|----------|----------|
| **Push** | Real-time dashboard | NATS delivers messages as they arrive |
| **Pull** | Batch analytics | Application pulls N messages at a time |
| **Durable** | Critical processing | Survives restarts, resumes from last ack |
| **Ephemeral** | Monitoring, debugging | Disappears when client disconnects |

### Go Producer Example

```go
package main

import (
    "encoding/json"
    "fmt"
    "time"

    "github.com/nats-io/nats.go"
    "github.com/nats-io/nats.go/jetstream"
)

type TelemetryMessage struct {
    MachineID string    `json:"machine_id"`
    Sensor    string    `json:"sensor"`
    Value     float64   `json:"value"`
    Unit      string    `json:"unit"`
    Timestamp time.Time `json:"timestamp"`
    Quality   string    `json:"quality"`
}

func main() {
    nc, err := nats.Connect(
        "nats://localhost:4222",
        nats.RetryOnFailedConnect(true),
        nats.MaxReconnects(-1),
        nats.ReconnectWait(2*time.Second),
    )
    if err != nil {
        panic(err)
    }
    defer nc.Close()

    js, err := jetstream.New(nc)
    if err != nil {
        panic(err)
    }

    msg := TelemetryMessage{
        MachineID: "cnc-001",
        Sensor:    "spindle",
        Value:     2.45,
        Unit:      "mm/s",
        Timestamp: time.Now().UTC(),
        Quality:   "good",
    }

    data, _ := json.Marshal(msg)
    subject := fmt.Sprintf("acme.munich.hall-a.line-1.%s.spindle.vibration.rms",
        msg.MachineID)

    ack, err := js.Publish(subject, data,
        jetstream.WithMsgID(fmt.Sprintf("%s-%d", msg.MachineID, msg.Timestamp.UnixNano())),
    )
    if err != nil {
        panic(err)
    }
    fmt.Printf("Published seq=%d stream=%s\n", ack.Sequence, ack.Stream)
}
```

### Python Consumer Example

```python
import asyncio
import json
import nats
from nats.js.api import ConsumerConfig, DeliverPolicy

async def main():
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()

    config = ConsumerConfig(
        durable_name="analytics-consumer",
        deliver_policy=DeliverPolicy.LAST_PER_SUBJECT,
        filter_subject="acme.munich.hall-a.>",
        ack_wait=30,
        max_deliver=3,
    )

    sub = await js.subscribe(
        "acme.munich.hall-a.>",
        stream="TELEMETRY",
        config=config,
    )

    async for msg in sub.messages:
        data = json.loads(msg.data.decode())
        print(f"{msg.subject}: {data['value']} {data['unit']}")
        await msg.ack()

asyncio.run(main())
```

---

## KV Store: Machine Configuration

NATS KV is a key-value store built on JetStream. Perfect for storing machine configuration that needs to sync between edge and cloud:

```python
import asyncio
import json
import nats

async def main():
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()

    kv = await js.create_key_value(
        name="MACHINE_CONFIG",
        history=5,
        ttl=0,
    )

    config = {
        "machine_id": "cnc-001",
        "vibration": {
            "sample_rate": 25600,
            "fft_size": 1024,
            "alert_threshold_rms": 4.5,
            "bearing_type": "6205",
        },
        "maintenance": {
            "last_service": "2026-02-15",
            "next_scheduled": "2026-04-15",
            "operating_hours": 4280,
        },
    }

    await kv.put("cnc-001", json.dumps(config).encode())

    entry = await kv.get("cnc-001")
    data = json.loads(entry.value.decode())
    print(f"Machine: {data['machine_id']}, Hours: {data['maintenance']['operating_hours']}")

    watcher = await kv.watch("cnc-*")
    async for update in watcher:
        if update is None:
            continue
        print(f"Config changed: {update.key} rev={update.revision}")

asyncio.run(main())
```

When a maintenance engineer updates machine configuration in the cloud dashboard, the KV change propagates to the edge leaf node automatically. The edge Node-RED flow watches for KV changes and reconfigures the monitoring pipeline on the fly.

---

## Leaf Nodes: Edge-to-Cloud Sync

Leaf nodes are the killer feature for industrial IoT. A leaf node is a local NATS server that connects to a remote cluster and **selectively synchronizes** subjects:

### Edge NATS Configuration

```
# /etc/nats/edge-server.conf

server_name: factory-munich-edge

listen: 0.0.0.0:4222

jetstream {
    store_dir: /data/nats/jetstream
    max_mem: 256MB
    max_file: 5GB
}

leafnodes {
    remotes [
        {
            url: "tls://cloud-nats.company.com:7422"
            credentials: "/etc/nats/creds/factory-munich.creds"

            # Only forward these subjects to the cloud
            deny_imports: ["_INBOX.>"]
            deny_exports: []
        }
    ]
}

authorization {
    users: [
        { user: "node-red", password: "$NODERED_PASS",
          permissions: {
            publish: ["acme.munich.>"]
            subscribe: ["acme.munich.>", "acme.*.config.>", "acme.*.command.>"]
          }
        },
        { user: "plc-gateway", password: "$PLC_PASS",
          permissions: {
            publish: ["acme.munich.hall-a.>"]
            subscribe: []
          }
        }
    ]
}

# Store-and-forward when cloud connection drops
leafnodes {
    reconnect_delay: "5s"
}
```

### What Happens When the Network Drops?

This is where NATS shines compared to MQTT bridges:

```
Normal operation:
  [Edge] ──publish──→ [Local NATS] ──leaf──→ [Cloud NATS] ──→ [Analytics]

Network drops:
  [Edge] ──publish──→ [Local NATS] ──X──  [Cloud NATS]
                        │
                        └── JetStream stores messages locally
                            (up to 5 GB / configured limit)

Network recovers:
  [Edge]               [Local NATS] ──leaf──→ [Cloud NATS] ──→ [Analytics]
                        │                        │
                        └── Replays buffered ────┘
                            messages in order
```

Local edge applications (Node-RED dashboards, local alerts) continue working because they subscribe to the local NATS server. The cloud just receives data late — but in order and without gaps.

---

## Docker Compose: Local Development Cluster

Test the full architecture locally:

```yaml
services:
  nats-cloud-1:
    image: nats:2.10-alpine
    command: >
      --name cloud-1
      --cluster_name cloud
      --cluster nats://0.0.0.0:6222
      --routes nats://nats-cloud-2:6222,nats://nats-cloud-3:6222
      --js
      --sd /data
      --leafnodes nats://0.0.0.0:7422
    volumes:
      - cloud1-data:/data
    ports:
      - "4222:4222"
      - "8222:8222"

  nats-cloud-2:
    image: nats:2.10-alpine
    command: >
      --name cloud-2
      --cluster_name cloud
      --cluster nats://0.0.0.0:6222
      --routes nats://nats-cloud-1:6222,nats://nats-cloud-3:6222
      --js
      --sd /data
    volumes:
      - cloud2-data:/data

  nats-cloud-3:
    image: nats:2.10-alpine
    command: >
      --name cloud-3
      --cluster_name cloud
      --cluster nats://0.0.0.0:6222
      --routes nats://nats-cloud-1:6222,nats://nats-cloud-2:6222
      --js
      --sd /data
    volumes:
      - cloud3-data:/data

  nats-edge-munich:
    image: nats:2.10-alpine
    command: >
      --name edge-munich
      --js
      --sd /data
      --leafnodes "nats://nats-cloud-1:7422"
    volumes:
      - edge-munich-data:/data
    ports:
      - "4223:4222"
    depends_on:
      - nats-cloud-1

  nats-edge-berlin:
    image: nats:2.10-alpine
    command: >
      --name edge-berlin
      --js
      --sd /data
      --leafnodes "nats://nats-cloud-1:7422"
    volumes:
      - edge-berlin-data:/data
    ports:
      - "4224:4222"
    depends_on:
      - nats-cloud-1

  node-red:
    image: nodered/node-red:latest
    ports:
      - "1880:1880"
    volumes:
      - nodered-data:/data
    depends_on:
      - nats-edge-munich
    environment:
      - NATS_URL=nats://nats-edge-munich:4222

volumes:
  cloud1-data:
  cloud2-data:
  cloud3-data:
  edge-munich-data:
  edge-berlin-data:
  nodered-data:
```

```bash
docker compose up -d

# Verify cluster health
docker exec -it $(docker compose ps -q nats-cloud-1) \
  nats server list

# Create the telemetry stream
docker exec -it $(docker compose ps -q nats-cloud-1) \
  nats stream add TELEMETRY \
    --subjects "acme.>" \
    --retention limits \
    --max-bytes 1GB \
    --max-age 7d \
    --storage file \
    --replicas 3 \
    --compression s2

# Publish from "edge munich" and consume from "cloud"
docker exec -it $(docker compose ps -q nats-edge-munich) \
  nats pub acme.munich.hall-a.line-1.cnc-001.spindle.vibration.rms \
    '{"value": 2.45, "unit": "mm/s"}'

docker exec -it $(docker compose ps -q nats-cloud-1) \
  nats sub "acme.munich.>"
```

---

## Bandwidth Calculations

Industrial telemetry can generate significant data volumes. Plan your leaf node connections accordingly:

### Per-Machine Data Budget

| Data Type | Message Size | Frequency | Bandwidth |
|-----------|-------------|-----------|-----------|
| Vibration RMS | 100 bytes | 1/sec | 100 B/s |
| Vibration spectrum (512 bins) | 4 KB | 1/5 sec | 800 B/s |
| Temperature | 80 bytes | 1/10 sec | 8 B/s |
| Current draw | 80 bytes | 1/sec | 80 B/s |
| Status change | 120 bytes | Event-driven (~1/min) | 2 B/s |
| **Total per machine** | | | **~990 B/s ≈ 1 KB/s** |

### Factory Scale

| Scale | Machines | Raw Bandwidth | With Compression (S2) |
|-------|----------|--------------|----------------------|
| Small line | 10 | 10 KB/s | ~3 KB/s |
| Large line | 50 | 50 KB/s | ~15 KB/s |
| Single factory | 200 | 200 KB/s | ~60 KB/s |
| 10 factories | 2,000 | 2 MB/s | ~600 KB/s |

Even 10 factories with 200 machines each only generate ~600 KB/s to the cloud cluster — well within a single 4G cellular connection (typically 5–50 Mbps). NATS S2 compression and JetStream deduplication keep the overhead minimal.

### Edge Buffer Sizing

How long can the edge operate offline? With a 5 GB JetStream store and 200 machines at 200 KB/s compressed:

```
5 GB / 60 KB/s ≈ 83,333 seconds ≈ 23 hours
```

Twenty-three hours of offline buffering. Enough to survive a full business day of internet outage.

---

## NATS in Node-RED

Use the `node-red-contrib-nats-streaming` or a custom NATS node to integrate:

```
┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐
│ OPC-UA   ├───→│ Transform    ├───→│ NATS     ├───→│ Local    │
│ Client   │    │ to JSON      │    │ Publish  │    │ NATS     │
│          │    │              │    │          │    │ Server   │
└──────────┘    └──────────────┘    └──────────┘    └────┬─────┘
                                                         │
                                                    Leaf Node
                                                         │
                                                    ┌────┴─────┐
                                                    │ Cloud    │
                                                    │ NATS     │
                                                    │ Cluster  │
                                                    └──────────┘
```

Node-RED function node for NATS subject construction:

```javascript
const site = flow.get("site") || "munich";
const area = msg.payload.area || "hall-a";
const line = msg.payload.line || "line-1";
const machine = msg.payload.machine_id;
const sensor = msg.payload.sensor_type;
const metric = msg.payload.metric;

msg.topic = `acme.${site}.${area}.${line}.${machine}.${sensor}.${metric}`;

msg.payload = {
    value: msg.payload.value,
    unit: msg.payload.unit,
    timestamp: new Date().toISOString(),
    quality: msg.payload.quality || "good",
};

return msg;
```

---

## Topology Comparison

Three ways to connect edge to cloud — and when to use each:

```
Star Topology (Leaf Nodes):          Mesh Topology:
                                    
     ┌─Edge A─┐                       ┌─Edge A─┐
     └───┬────┘                        └───┬────┘
         │                                 │╲
     ┌───┴────┐                        ┌───┴────┐
     │ Cloud  │                        │ Cloud  │
     └───┬────┘                        └───┬────┘
         │                                 │╱
     ┌───┴────┐                        ┌───┴────┐
     └─Edge B─┘                        └─Edge B─┘

Best for: Most IIoT              Best for: Edge-to-edge
  (simple, scalable)               communication needed


Gateway Tree:

     ┌─Sensor─┐   ┌─Sensor─┐
     └───┬────┘   └───┬────┘
         └─────┬──────┘
          ┌────┴─────┐
          │ Line GW  │
          └────┬─────┘
          ┌────┴─────┐
          │ Factory  │
          │ Edge     │
          └────┬─────┘
          ┌────┴─────┐
          │  Cloud   │
          └──────────┘

Best for: Large factories
  with many sensors per line
```

For most industrial IoT deployments, the **star topology with leaf nodes** is the right choice. It's simple, scales linearly, and the cloud cluster never becomes a single point of failure for local operations.

---

## Conclusion

NATS simplifies the IIoT messaging stack from three systems (MQTT + Kafka + Redis) down to one. Leaf nodes solve the edge-to-cloud synchronization problem that has plagued industrial IoT architectures for years — with automatic store-and-forward, subject-based filtering, and zero custom bridge code.

The subject naming convention is worth spending time on. Get it right at the start, and every downstream system — from dashboards to ML pipelines to alerting rules — becomes a simple wildcard subscription. Get it wrong, and you're refactoring message routing across 30 factories.

Start with the docker-compose setup above. Publish some test data from the edge. Subscribe from the cloud. Kill the network connection and watch the messages buffer. Bring it back and watch them replay. That demo alone is more convincing than any architecture slide deck.
