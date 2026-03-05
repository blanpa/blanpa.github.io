---
title: "CompuLab IoT Gateway Interfaces"
description: "Node-RED nodes for CompuLab IoT Gateway hardware — GPIO, serial, CAN, cellular, and more"
tags: ["Node-RED", "JavaScript", "CAN Bus", "Embedded Linux", "IIoT"]
weight: 4
---

## The Problem

Industrial IoT gateways come with powerful hardware — GPIO, serial ports, CAN bus, cellular modems, GPS — but accessing these interfaces from Node-RED requires custom scripts, shell commands, and deep knowledge of Linux device drivers. This makes rapid prototyping and deployment of edge applications unnecessarily complex.

## The Solution

A Node-RED package that exposes **all hardware interfaces** of CompuLab IoT Gateways as drag-and-drop nodes. No shell scripts, no driver code — just connect, configure, and deploy.

{{< github repo="blanpa/node-red-contrib-clab-interfaces" >}}

## Supported Devices

| Gateway | Processor | Use Case |
|---------|-----------|----------|
| **IOT-GATE-iMX8** | NXP i.MX8M | High-performance edge computing |
| **IOT-GATE-RPi** | Broadcom BCM2711 | Cost-effective IoT gateway |
| **IOT-LINK** | Intel Atom | x86 edge computing |
| **IOT-DIN-IMX8PLUS** | NXP i.MX8M Plus | DIN-rail industrial gateway |

## 13 Node Categories

### Industrial I/O
- **GPIO** — Digital input/output with configurable pull-up/down and edge detection
- **Analog Inputs** — Read 4-20mA current loops, 0-10V voltage signals, PT100/PT1000 temperature sensors
- **CAN Bus** — Send and receive CAN frames for vehicle and machine communication
- **RS232 / RS485** — Serial communication with Modbus RTU devices, PLCs, and legacy equipment

### Device Management
- **System** — Query device info, read/set RTC, configure watchdog, access TPM security chip
- **LEDs** — Control user LEDs (on/off/blink) for visual status indication
- **Bluetooth** — Scan, connect, and communicate with BLE devices and beacons
- **GPS** — Read position, speed, altitude, and satellite data from the built-in GNSS module

### Connectivity
- **Cellular/LTE** — Manage the modem: connect, monitor signal strength (RSSI/RSRP), switch carriers
- **WiFi** — Scan networks, connect to access points, or create a WiFi hotspot
- **Ethernet** — Configure static/DHCP, monitor link status
- **Network Diagnostics** — Ping, DNS lookup, traceroute, port checks — all from Node-RED

## Scalability

The **IOT-DIN-IMX8PLUS** supports stacking up to **8 I/O expansion modules**, enabling massive I/O capacity per gateway:

| Resource | Per Module | 8 Modules Stacked |
|----------|-----------|-------------------|
| Analog channels | 8 | **64** |
| Digital inputs | 8 | **64** |
| Digital outputs | 8 | **64** |

This makes it possible to monitor an entire production line from a single gateway without external I/O hardware.

## Use Cases

- **Brownfield Retrofitting** — Connect legacy machines via RS485/CAN without replacing controllers
- **Remote Site Monitoring** — Use cellular + GPS for assets in the field (wind turbines, pumping stations)
- **Environmental Monitoring** — Read temperature, humidity, and air quality sensors via analog inputs
- **Fleet Tracking** — GPS + cellular for vehicle or mobile equipment tracking
