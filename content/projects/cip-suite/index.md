---
title: "CIP / EtherNet/IP Suite"
description: "Node-RED nodes for Allen-Bradley PLCs and EtherNet/IP devices — from ControlLogix to legacy SLC/PLC-5"
tags: ["Node-RED", "TypeScript", "Allen-Bradley", "EtherNet/IP", "IIoT"]
weight: 3
date: 2026-03-12
---

## The Problem

Allen-Bradley PLCs dominate North American manufacturing — but integrating them with modern edge and IoT platforms means dealing with the CIP protocol stack, legacy PCCC addressing for older PLCs, and a completely different programming model than Siemens or OPC-UA. Existing Node-RED solutions cover only basic tag reads, leaving out legacy hardware, raw CIP access, I/O scanning, and advanced objects like motion and energy.

## The Solution

A comprehensive **Node-RED package for EtherNet/IP** that covers the full range of Rockwell Automation hardware — from modern ControlLogix and CompactLogix to legacy SLC 500, MicroLogix, and PLC-5 — plus raw CIP access for any EtherNet/IP device.

{{< github repo="blanpa/node-red-contrib-cip-suite" >}}

## Architecture

Three node families share a single CIP/EtherNet/IP transport layer and route to the right protocol for each PLC generation:

{{< mermaid >}}
flowchart TB
    subgraph NR["Node-RED Flows"]
        SYM["CIP Symbolic Nodes<br/>read / write / browse / subscribe"]
        PCCC["PCCC Nodes<br/>read / write"]
        OBJ["Advanced Object Nodes<br/>I/O · Motion · Energy · Sync · File"]
    end
    EP["cip-endpoint / cip-pccc-endpoint<br/>shared TCP session · auto-reconnect · multi-hop routing"]
    EIP["EtherNet/IP · CIP Encapsulation"]
    LOGIX["ControlLogix · CompactLogix · Micro800"]
    LEGACY["SLC 500 · MicroLogix · PLC-5"]
    DEV["Third-party CIP devices<br/>drives · I/O blocks · sensors"]
    SYM --> EP
    PCCC --> EP
    OBJ --> EP
    EP --> EIP
    EIP --> LOGIX
    EIP --> LEGACY
    EIP --> DEV
{{< /mermaid >}}

## Supported Hardware

| Platform | Protocol | Notes |
|----------|----------|-------|
| **ControlLogix** (L6x, L7x, L8x) | CIP Symbolic | Slot-based backplane routing |
| **CompactLogix** (L1x, L2x, L3x) | CIP Symbolic | Typically slot 0 |
| **Micro800** (820/850/870) | CIP Symbolic | Enable Micro800 mode |
| **SLC 500** | PCCC over CIP | File-based addressing |
| **MicroLogix** (1100/1400) | PCCC over CIP | File-based addressing |
| **PLC-5** | PCCC over CIP | File-based addressing |
| **Third-party CIP devices** | CIP Raw | Any EtherNet/IP device |

## Core CIP Nodes

8 nodes for modern Logix controllers:

- **cip-endpoint** — Shared TCP session with auto-reconnect and multi-hop routing
- **cip-read** — Read tags with bit access, array elements, ranges, and batch operations
- **cip-write** — Write tags with atomic bit operations and partial UDT merging
- **cip-browse** — Tag discovery with glob/regex filtering and program-scoped tags
- **cip-subscribe** — Cyclic multi-tag scanning with deadband filtering
- **cip-controller** — Read identity, mode, faults; execute runtime commands
- **cip-raw** — Send raw CIP service requests with Multiple Service Packet support
- **cip-discover** — UDP broadcast for network device discovery

## Legacy PCCC Nodes

3 nodes for SLC 500, MicroLogix, and PLC-5:

- **cip-pccc-endpoint** — Raw TCP session with PCCC encapsulation
- **cip-pccc-read** — Read PCCC addresses (`N7:0`, `F8:0`, `B3:0/5`, `T4:0.ACC`)
- **cip-pccc-write** — Write with bit-level read-modify-write support

## Advanced CIP Object Nodes

8 nodes for specialized CIP objects:

- **cip-io-scanner** — Implicit I/O via ForwardOpen + UDP for cyclic exchange
- **cip-security** — TLS/DTLS status and security profiles (Class 0x5D)
- **cip-sync** — IEEE 1588 PTP time synchronization (Class 0x43)
- **cip-motion** — Motion Axis: jog, move, home, stop, enable/disable (Class 0x42)
- **cip-energy** — Power/energy monitoring and electrical measurements (Class 0x4F/0x4E)
- **cip-file** — Firmware upload/download with fragmented transfer (Class 0x37)
- **cip-param** — Device parameterization with discovery scan (Class 0x0F)

## Tag Addressing

### CIP Symbolic (Logix)

```
MyTag              → Simple tag
MyDint.5           → Bit access
MyArray[3]         → Array element
MyArray[0..9]      → Array range
Program:Main.Tag   → Program-scoped
```

### PCCC (SLC/MLX/PLC-5)

```
N7:0      → Integer       T4:0.ACC  → Timer accumulator
F8:5      → Float         C5:0.ACC  → Counter accumulator
B3:0/5    → Bit           O:0/3     → Output
S:1/5     → Status        I:1/0     → Input
```

## Docker Simulation Environment

Multi-profile PLC simulator for development and testing:

| Container | Description | Port |
|-----------|-------------|------|
| plc-clx | ControlLogix simulator | 44818 |
| plc-cplx | CompactLogix simulator | 44819 |
| plc-micro | Micro800 simulator | 44820 |
| plc-mlx | MicroLogix simulator (PCCC) | 44821 |
| plc-plc5 | PLC-5 simulator (PCCC) | 44822 |
| node-red | Node-RED with test flows | 11880 |

## Reliability

- Auto-reconnect with configurable intervals
- Backpressure protection — skips requests while one is in-flight
- Atomic bit operations via CIP Read-Modify-Write (0x4E)
- Connection metrics (response times, error counts, uptime)
- Admin HTTP endpoints for tag browsing and diagnostics
