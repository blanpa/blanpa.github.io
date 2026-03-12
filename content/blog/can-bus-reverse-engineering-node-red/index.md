---
title: "CAN Bus Reverse Engineering with Node-RED and Raspberry Pi"
tags: [iiot, can-bus, node-red, raspberry-pi, python]
description: "How to sniff, decode, and integrate CAN bus data from industrial machines using a Raspberry Pi and Node-RED."
date: 2026-05-02
series: ["IIoT"]
---

If you've ever stared at a VFD or servo drive and thought "I know this thing has useful data — I just can't get to it," CAN bus is probably the answer. Most industrial drives, controllers, and even some sensors speak CAN internally. With a Raspberry Pi, a $15 CAN hat, and some patience, you can tap into that data stream and make it visible in Node-RED.

This post walks through the entire process: hardware setup, Linux socketcan configuration, traffic sniffing, frame decoding, Python scripting, and finally Node-RED integration for real-time dashboards.

---

## What is CAN Bus?

**Controller Area Network (CAN)** was developed by Bosch in 1986 for in-vehicle communication. The idea was simple: let microcontrollers talk to each other without a central host. Every node on the bus sees every message, and hardware-level arbitration prevents collisions.

```
CAN Bus Timeline:

1986 ─── Bosch develops CAN for automotive
1991 ─── Mercedes-Benz first production car with CAN
1993 ─── ISO 11898 standard published
2012 ─── CAN-FD (Flexible Data Rate) introduced by Bosch
2015 ─── CAN-FD standardized as ISO 11898-1:2015
Today ── CAN is in cars, trucks, elevators, medical devices,
         industrial drives, agricultural equipment, and robots
```

### Automotive vs Industrial CAN

| | Automotive CAN | Industrial CAN (CANopen/DeviceNet) |
|--|----------------|-------------------------------------|
| **Speed** | 500 kbit/s typical | 125–1000 kbit/s |
| **Cable** | Twisted pair, short runs | Twisted pair, up to 1000m at 50 kbit/s |
| **Addressing** | Manufacturer-specific IDs | Standardized object dictionaries |
| **Typical nodes** | ECUs, ABS, airbag | VFDs, servos, I/O modules, sensors |
| **Frame format** | Standard (11-bit ID) | Standard or Extended (29-bit ID) |

In industrial settings, you'll most often encounter **CANopen** (used by SEW-Eurodrive, Lenze, Beckhoff) or **DeviceNet** (Rockwell/Allen-Bradley). But even when a vendor uses a proprietary profile, the physical layer is the same — which means we can sniff it.

---

## Hardware Setup

### Option A: Raspberry Pi + MCP2515 SPI CAN Hat

This is the cheapest and most flexible option. The MCP2515 is a standalone CAN controller that talks to the Pi via SPI.

```
┌─────────────────────────────────────────────┐
│                Raspberry Pi 4               │
│                                             │
│  GPIO Header                                │
│  ┌──────────────────────┐                   │
│  │ SPI0_MOSI (GPIO 10)  ├──┐               │
│  │ SPI0_MISO (GPIO 9)   ├──┤               │
│  │ SPI0_SCLK (GPIO 11)  ├──┤               │
│  │ SPI0_CE0  (GPIO 8)   ├──┤  ┌──────────┐ │
│  │ INT       (GPIO 25)  ├──┼──│ MCP2515  │ │
│  │ GND                  ├──┤  │ CAN Hat  │ │
│  │ 3.3V / 5V            ├──┘  │          │ │
│  └──────────────────────┘     │ TJA1050  │ │
│                               │ (Xcvr)   │ │
│                               └────┬─────┘ │
│                                    │        │
└────────────────────────────────────┼────────┘
                                     │
                              ┌──────┴──────┐
                              │  CAN_H      │
                              │  CAN_L      │
                              │  (to bus)   │
                              └─────────────┘
```

Popular hats: **Waveshare RS485 CAN HAT**, **PiCAN2**, **Seeed Studio 2-Channel CAN-BUS(FD) Shield**.

**Enable SPI and configure the device tree overlay:**

```bash
sudo raspi-config
# Interface Options → SPI → Enable

sudo nano /boot/config.txt
```

Add these lines:

```ini
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25
dtoverlay=spi-bcm2835-overlay
```

The `oscillator` value depends on your hat — check the crystal frequency (8 MHz or 16 MHz). Reboot after saving.

### Option B: USB CAN Adapter

If you don't want to mess with GPIO, use a USB adapter. These are plug-and-play with Linux socketcan:

| Adapter | Price | Notes |
|---------|-------|-------|
| **PEAK PCAN-USB** | ~€230 | Industry standard, rock-solid driver |
| **Innomaker USB2CAN** | ~€25 | gs_usb driver, great value |
| **Canable / CANtact** | ~€30 | Open-source hardware, gs_usb |
| **Kvaser Leaf Light** | ~€280 | Professional, proprietary driver |

For most IIoT projects, the **Innomaker USB2CAN** is the sweet spot — cheap, reliable, and uses the mainline `gs_usb` kernel driver.

---

## Linux SocketCAN Setup

Linux has native CAN support through the **socketcan** subsystem. CAN interfaces are treated like network interfaces — you use `ip link` to manage them.

### Bring Up the Interface

```bash
# Load kernel modules (MCP2515 hat)
sudo modprobe can
sudo modprobe can_raw
sudo modprobe mcp251x

# Set bitrate and bring up interface
sudo ip link set can0 type can bitrate 250000
sudo ip link set can0 up

# Verify
ip -details link show can0
```

Output:

```
3: can0: <NOARP,UP,LOWER_UP,ECHO> mtu 16 qdisc pfifo_fast state UP ...
    link/can
    can state ERROR-ACTIVE restart-ms 0
      bitrate 250000 sample-point 0.875
      tq 250 prop-seg 6 phase-seg1 7 phase-seg2 2 sjw 1
      mcp251x: tseg1 3..16 tseg2 2..8 sjw 1..4 brp 1..64 ...
```

**Important:** The bitrate **must** match the existing bus. Common industrial bitrates: 125000, 250000, 500000, 1000000. If you get it wrong, you'll see bus errors and no valid frames.

### Auto-Start on Boot

Create a systemd service so the CAN interface comes up automatically:

```ini
# /etc/systemd/system/can0.service
[Unit]
Description=CAN0 interface
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/ip link set can0 type can bitrate 250000
ExecStartPost=/sbin/ip link set can0 up
ExecStop=/sbin/ip link set can0 down

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable can0.service
sudo systemctl start can0.service
```

---

## Sniffing CAN Traffic

### candump — Your Best Friend

`candump` is part of the `can-utils` package:

```bash
sudo apt install can-utils
```

Start sniffing:

```bash
candump can0
```

Output:

```
can0  181   [8]  00 00 09 A4 00 00 00 00
can0  281   [8]  03 E8 01 F4 00 64 00 00
can0  381   [8]  00 01 00 00 00 00 00 00
can0  181   [8]  00 00 09 A6 00 00 00 00
can0  281   [8]  03 E8 01 F4 00 65 00 00
can0  181   [8]  00 00 09 A8 00 00 00 00
```

Each line: `interface  CAN_ID  [DLC]  DATA_BYTES`

### Understanding CAN Frames

```
┌─────────────────────────── CAN Frame ────────────────────────────┐
│                                                                   │
│  ┌────────┐  ┌─────┐  ┌────────────────────────────────┐  ┌───┐ │
│  │  ID     │  │ DLC │  │         Data (0-8 bytes)       │  │CRC│ │
│  │ 11-bit  │  │     │  │  B0  B1  B2  B3  B4  B5  B6  B7 │  │   │ │
│  │ or      │  │ 0-8 │  │                                │  │   │ │
│  │ 29-bit  │  │     │  │                                │  │   │ │
│  └────────┘  └─────┘  └────────────────────────────────┘  └───┘ │
│                                                                   │
│  ID:   Identifies the message type AND priority (lower = higher) │
│  DLC:  Data Length Code — how many bytes follow                  │
│  Data: The payload — what we want to decode                      │
└───────────────────────────────────────────────────────────────────┘
```

### Filtering by ID

Most buses are noisy. Filter to specific IDs:

```bash
# Only show ID 0x181
candump can0,181:7FF

# Show IDs 0x181 and 0x281
candump can0,181:7FF,281:7FF

# Log to file with timestamps
candump -l can0
# Creates candump-2026-05-02_143022.log
```

### Sending Test Frames

Use `cansend` to inject frames (be careful on live systems!):

```bash
# Send a single frame
cansend can0 123#DEADBEEF

# Send with full 8 bytes
cansend can0 181#0000000000000000
```

---

## Decoding CAN Frames: The Detective Work

This is where reverse engineering begins. You have a stream of hex bytes — now figure out what they mean.

### Strategy 1: Correlate with Known Values

If you can see a display on the machine (RPM readout, temperature gauge), compare the CAN data to what's displayed:

```
Machine display shows: 2468 RPM

candump shows:
can0  181   [8]  00 00 09 A4 00 00 00 00
                       ^^^^
                       0x09A4 = 2468 decimal  ← match!
```

### Strategy 2: Change One Thing, Watch the Bus

1. Motor stopped → record baseline traffic
2. Start motor at 1000 RPM → note what changed
3. Increase to 2000 RPM → which bytes scaled?
4. Change direction → which bit flipped?

```
State               ID 0x181 Data
─────────────────────────────────────────
Motor stopped       00 00 00 00 00 00 00 00
Motor  500 RPM FWD  00 00 01 F4 00 00 00 01
Motor 1000 RPM FWD  00 00 03 E8 00 00 00 01
Motor 1500 RPM FWD  00 00 05 DC 00 00 00 01
Motor 1000 RPM REV  00 00 03 E8 00 00 00 02
Motor stopped       00 00 00 00 00 00 00 00

Analysis:
  Bytes 2-3: RPM value (big-endian uint16)
    01 F4 =  500
    03 E8 = 1000
    05 DC = 1500
  Byte 7: Direction (01 = FWD, 02 = REV)
```

### Strategy 3: DBC Files

If you're lucky, the manufacturer provides a **DBC file** — a database that maps CAN IDs and byte positions to named signals:

```dbc
VERSION ""

NS_ :

BS_:

BU_: Drive

BO_ 385 DriveStatus: 8 Drive
 SG_ MotorRPM : 16|16@1+ (1,0) [0|20000] "RPM" Vector__XXX
 SG_ MotorTemp : 32|16@1+ (0.1,0) [0|200] "degC" Vector__XXX
 SG_ DriveState : 0|8@1+ (1,0) [0|255] "" Vector__XXX
 SG_ FaultCode : 8|8@1+ (1,0) [0|255] "" Vector__XXX

BO_ 641 DriveCommand: 8 Drive
 SG_ TargetRPM : 16|16@1+ (1,0) [0|20000] "RPM" Vector__XXX
 SG_ Direction : 0|8@1+ (1,0) [0|2] "" Vector__XXX
```

DBC signal format: `SG_ Name : StartBit|Length@ByteOrder ValueType (Factor,Offset) [Min|Max] "Unit" Receiver`

---

## Python CAN Integration

The `python-can` library gives you programmatic access to socketcan.

### Installation

```bash
pip install python-can cantools
```

### Reading CAN Data

```python
import can
import struct

bus = can.interface.Bus(channel='can0', interface='socketcan')

print("Listening on can0...")
for msg in bus:
    if msg.arbitration_id == 0x181:
        rpm = struct.unpack('>H', msg.data[2:4])[0]
        temp_raw = struct.unpack('>H', msg.data[4:6])[0]
        temp = temp_raw * 0.1
        state = msg.data[7]

        state_map = {0: "STOPPED", 1: "RUNNING_FWD", 2: "RUNNING_REV", 3: "FAULT"}
        state_str = state_map.get(state, f"UNKNOWN({state})")

        print(f"RPM: {rpm:5d} | Temp: {temp:5.1f}°C | State: {state_str}")
```

Output:

```
Listening on can0...
RPM:  2468 | Temp:  42.3°C | State: RUNNING_FWD
RPM:  2470 | Temp:  42.3°C | State: RUNNING_FWD
RPM:  2465 | Temp:  42.4°C | State: RUNNING_FWD
```

### Using DBC Files with cantools

```python
import can
import cantools

db = cantools.database.load_file('drive.dbc')
bus = can.interface.Bus(channel='can0', interface='socketcan')

for msg in bus:
    try:
        decoded = db.decode_message(msg.arbitration_id, msg.data)
        print(f"ID 0x{msg.arbitration_id:03X}: {decoded}")
    except KeyError:
        pass
```

Output:

```
ID 0x181: {'DriveState': 1, 'FaultCode': 0, 'MotorRPM': 2468, 'MotorTemp': 42.3}
ID 0x281: {'TargetRPM': 2500, 'Direction': 1}
```

### Publishing Decoded Data via MQTT

Bridge the gap between CAN and Node-RED by publishing decoded values to MQTT:

```python
import can
import struct
import json
import paho.mqtt.client as mqtt
from datetime import datetime, timezone

mqtt_client = mqtt.Client()
mqtt_client.connect("localhost", 1883)
mqtt_client.loop_start()

bus = can.interface.Bus(channel='can0', interface='socketcan')

for msg in bus:
    if msg.arbitration_id == 0x181:
        rpm = struct.unpack('>H', msg.data[2:4])[0]
        temp = struct.unpack('>H', msg.data[4:6])[0] * 0.1
        state = msg.data[7]

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rpm": rpm,
            "temperature": temp,
            "state": state
        }

        mqtt_client.publish(
            "factory/line1/drive01/status",
            json.dumps(payload),
            qos=1
        )
```

---

## Node-RED Integration

With decoded CAN data arriving via MQTT, Node-RED can visualize and act on it.

### Architecture

```
┌────────────┐    CAN Bus     ┌────────────────┐    MQTT      ┌──────────┐
│ Industrial │◄──────────────►│  Raspberry Pi  │─────────────►│ Node-RED │
│   Drive    │                │                │              │          │
│            │                │  python-can    │              │ Dashboard│
│  CAN_H ───┤                │  + MQTT pub    │              │ Alerts   │
│  CAN_L ───┤                │                │              │ Logging  │
└────────────┘                └────────────────┘              └──────────┘
```

### Dashboard Flow

```json
[
    {
        "id": "mqtt-in",
        "type": "mqtt in",
        "topic": "factory/line1/drive01/status",
        "qos": "1",
        "datatype": "json"
    },
    {
        "id": "split-values",
        "type": "function",
        "func": "return [\n    { payload: msg.payload.rpm },\n    { payload: msg.payload.temperature },\n    { payload: msg.payload.state }\n];",
        "outputs": 3
    },
    {
        "id": "gauge-rpm",
        "type": "ui-gauge",
        "name": "Motor RPM",
        "min": 0,
        "max": 5000,
        "unit": "RPM"
    },
    {
        "id": "chart-temp",
        "type": "ui-chart",
        "name": "Motor Temperature",
        "ymin": 0,
        "ymax": 120,
        "unit": "°C"
    }
]
```

### Alert on Overtemperature

```javascript
// Function node: Check temperature threshold
const TEMP_WARNING = 80.0;
const TEMP_CRITICAL = 95.0;

const temp = msg.payload.temperature;

if (temp >= TEMP_CRITICAL) {
    msg.payload = {
        level: "CRITICAL",
        message: `Motor temperature ${temp}°C exceeds critical threshold!`,
        value: temp
    };
    return [msg, null];
} else if (temp >= TEMP_WARNING) {
    msg.payload = {
        level: "WARNING",
        message: `Motor temperature ${temp}°C approaching limit`,
        value: temp
    };
    return [null, msg];
}
return [null, null];
```

---

## Real-World Example: SEW-Eurodrive MOVIDRIVE

Here's a concrete example from a project where I tapped into a SEW-Eurodrive MOVIDRIVE B frequency inverter via CAN.

### Bus Parameters

```
Protocol:    CANopen (DS301 + DS402 drive profile)
Bitrate:     500 kbit/s
Node ID:     0x05
Termination: 120Ω at each end of bus
```

### Key Process Data Objects (PDOs)

```
TPDO1 (0x185):  Statusword + Actual Speed
  Byte 0-1: Statusword (DS402)
  Byte 2-3: Actual speed in RPM (int16, signed)

TPDO2 (0x285):  Actual Current + DC Bus Voltage
  Byte 0-1: Motor current (uint16, 0.01 A resolution)
  Byte 2-3: DC bus voltage (uint16, 0.1 V resolution)

RPDO1 (0x205):  Controlword + Target Speed
  Byte 0-1: Controlword (DS402)
  Byte 2-3: Target speed in RPM (int16, signed)
```

### Decoding Script

```python
import can
import struct
import json
import paho.mqtt.client as mqtt

NODE_ID = 0x05

TPDO1_ID = 0x180 + NODE_ID  # 0x185
TPDO2_ID = 0x280 + NODE_ID  # 0x285

DS402_STATES = {
    0x0000: "NOT_READY",
    0x0040: "SWITCH_ON_DISABLED",
    0x0021: "READY_TO_SWITCH_ON",
    0x0023: "SWITCHED_ON",
    0x0027: "OPERATION_ENABLED",
    0x0007: "QUICK_STOP_ACTIVE",
    0x000F: "FAULT_REACTION_ACTIVE",
    0x0008: "FAULT",
}

def decode_statusword(raw):
    masked = raw & 0x006F
    return DS402_STATES.get(masked, f"UNKNOWN(0x{raw:04X})")

mqtt_client = mqtt.Client()
mqtt_client.connect("localhost", 1883)
mqtt_client.loop_start()

bus = can.interface.Bus(channel='can0', interface='socketcan', bitrate=500000)

for msg in bus:
    if msg.arbitration_id == TPDO1_ID:
        statusword = struct.unpack('<H', msg.data[0:2])[0]
        speed = struct.unpack('<h', msg.data[2:4])[0]

        payload = {
            "statusword": statusword,
            "state": decode_statusword(statusword),
            "speed_rpm": speed
        }
        mqtt_client.publish("factory/sew/drive05/tpdo1", json.dumps(payload))

    elif msg.arbitration_id == TPDO2_ID:
        current = struct.unpack('<H', msg.data[0:2])[0] * 0.01
        voltage = struct.unpack('<H', msg.data[2:4])[0] * 0.1

        payload = {
            "current_a": round(current, 2),
            "dc_voltage_v": round(voltage, 1)
        }
        mqtt_client.publish("factory/sew/drive05/tpdo2", json.dumps(payload))
```

---

## Safety Considerations

CAN bus reverse engineering in industrial environments requires caution:

### Do's

- **Listen passively first** — use `candump` in read-only mode before sending anything
- **Use a separate CAN interface** — don't disturb the existing bus segment if possible
- **Add proper termination** — CAN requires 120Ω resistors at each physical end of the bus
- **Document everything** — record which IDs map to which signals
- **Test during maintenance windows** — never experiment on a running production line

### Don'ts

- **Never send frames on a production bus** without understanding the consequences — a wrong controlword can start a motor unexpectedly
- **Never remove termination resistors** from an existing bus — it causes communication errors for all nodes
- **Don't assume byte order** — some devices use big-endian, others little-endian, some even mix them
- **Don't ignore bus errors** — if `ip -s link show can0` shows TX/RX errors, something is wrong with the physical layer

### Electrical Safety

```
DANGER: Industrial CAN buses may share cable trays with
high-voltage power cables. Always verify isolation before
touching CAN wiring.

CAN signal levels are low voltage (0-5V differential),
but the equipment connected to the bus may operate at
24VDC, 400VAC, or higher.
```

---

## Debugging CAN Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| No frames at all | Wrong bitrate | Try 125k, 250k, 500k, 1M |
| Frames appear then stop | Missing termination | Add 120Ω between CAN_H and CAN_L |
| Bus error count increasing | Wiring issue, noise | Check cable, shielding, ground |
| Random invalid data | Wrong byte order | Try swapping endianness |
| CAN interface goes to "BUS-OFF" | Too many errors | Check bitrate, cable, termination |

Check bus statistics:

```bash
ip -s -d link show can0
```

Relevant counters: `bus-error`, `error-warning`, `error-passive`, `bus-off`, `restarts`.

---

## Conclusion

CAN bus is one of the most rewarding protocols to reverse engineer. The physical layer is simple — two wires. The frames are small — 8 bytes max. And the data is real-time — you see exactly what the machine is doing, right now.

The combination of a Raspberry Pi for CAN sniffing and Python decoding, MQTT for transport, and Node-RED for visualization gives you a complete, low-cost monitoring stack that can integrate machines that were never designed to be "connected."

Start with `candump`, be patient with the decoding phase, and always keep safety first. The hex bytes will start making sense faster than you think.
