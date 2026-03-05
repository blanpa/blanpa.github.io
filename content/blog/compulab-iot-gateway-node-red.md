---
title: "CompuLab IoT Gateway — Embedded Linux for Industrial Edge Computing"
tags: [iiot, node-red, embedded-linux, can-bus, raspberry-pi]
description: "Setting up a CompuLab IoT gateway with Node-RED for industrial data collection — GPIO, CAN bus, RS485, and cellular connectivity."
date: 2026-03-28
series: ["IIoT"]
---

A Raspberry Pi can read a temperature sensor. It cannot survive 60°C ambient heat inside a control cabinet, run off 24V DC, talk CAN bus to a robot controller, fall back to 4G when Ethernet dies, and keep running for 10 years without maintenance. That's what industrial gateways are built for.

The **CompuLab IOT-GATE** series fills the gap between hobbyist SBCs and enterprise-grade industrial PCs. It runs standard Linux, supports Node-RED, and has the I/O interfaces that factory floors actually use. This post covers setting one up from bare metal to production-ready edge node.

---

## Hardware Overview

The IOT-GATE-iMX8 (the model I've deployed most) is based on NXP's i.MX 8M Mini SoC:

| Spec | IOT-GATE-iMX8 | Raspberry Pi 4 (comparison) |
|------|----------------|---------------------------|
| **CPU** | NXP i.MX 8M Mini, 4× Cortex-A53 @ 1.8 GHz | BCM2711, 4× Cortex-A72 @ 1.5 GHz |
| **RAM** | 2 GB DDR4 (up to 4 GB) | 1–8 GB LPDDR4 |
| **Storage** | 8 GB eMMC + SD slot | MicroSD only |
| **Ethernet** | 2× Gigabit | 1× Gigabit |
| **USB** | 2× USB 3.0, 2× USB 2.0 | 2× USB 3.0, 2× USB 2.0 |
| **Serial** | 2× RS-232/RS-485 (configurable) | None (UART via GPIO) |
| **CAN bus** | 1× CAN 2.0B (optional 2×) | None |
| **GPIO** | 8× digital I/O (isolated) | 40-pin header (not isolated) |
| **Cellular** | Mini-PCIe slot (4G/LTE modem) | None |
| **Wi-Fi/BT** | 802.11ac + BT 5.0 | 802.11ac + BT 5.0 |
| **Power** | 9–36V DC (industrial range) | 5V USB-C (consumer) |
| **Operating temp** | -40°C to +85°C | 0°C to 50°C |
| **Mounting** | DIN rail + wall mount | None standard |
| **Certifications** | CE, FCC, UL | CE, FCC |
| **Price** | ~€350–500 | ~€50–80 |

The price difference is real, but so are the capabilities. The isolated GPIO, CAN bus, RS-485, wide voltage input, and extended temperature range are non-negotiable in industrial environments.

### Why Not a Raspberry Pi?

I've deployed Raspberry Pis in factories — always with caveats:

- **SD card corruption**: Pi's SD card fails after 1–2 years of constant writes. eMMC doesn't.
- **No watchdog timer**: If the Pi freezes, it stays frozen until someone power-cycles it. Industrial gateways have hardware watchdog timers.
- **No isolation**: GPIO pins share ground with the CPU. An ESD event on a factory floor can kill the board. Isolated I/O prevents this.
- **No DIN rail**: You need a proper enclosure, which adds cost and eliminates the price advantage.
- **No RS-485/CAN**: Adding these via USB adapters works but adds failure points and cost.

For prototyping and non-critical monitoring: Pi is fine. For production deployments that need to run unattended for years: use industrial hardware.

---

## Operating System: Yocto vs Debian

CompuLab provides both options. The choice affects your entire development workflow:

| Aspect | Yocto (BSP) | Debian/Ubuntu |
|--------|------------|---------------|
| **Boot time** | 5–10 seconds | 15–30 seconds |
| **Image size** | 200–500 MB (minimal) | 2–4 GB |
| **Package management** | opkg (limited repo) | apt (full repo) |
| **Security updates** | Manual rebuild | `apt upgrade` |
| **Node-RED install** | Must include in image | `npm install` |
| **Docker** | Possible but manual | `apt install docker.io` |
| **OTA updates** | SWUpdate, RAUC | Standard Linux tools |
| **Developer experience** | Steep learning curve | Familiar to most |
| **Long-term maintenance** | Frozen, deterministic | Rolling updates |

**My recommendation**: Use **Debian** unless you have a specific reason for Yocto. The developer experience is dramatically better, Docker support is native, and security updates are a single command. Yocto's advantages (boot time, image size) rarely matter for an IoT gateway that boots once and runs for months.

### Base Debian Setup

```bash
# Flash the CompuLab Debian image to eMMC
# (from a host machine via USB recovery mode)
sudo dd if=iot-gate-imx8-debian-bookworm.img of=/dev/sdX bs=4M status=progress

# First boot — connect via serial console (115200 baud)
# or Ethernet (DHCP, find IP via router/nmap)

# Update and install essentials
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    curl git htop tmux \
    can-utils i2c-tools \
    python3-pip python3-venv \
    docker.io docker-compose-plugin

# Enable hardware watchdog
sudo apt install -y watchdog
sudo systemctl enable watchdog
```

### Read-Only Root Filesystem

For production gateways, mount the root filesystem as read-only to prevent corruption during power loss:

```bash
# /etc/fstab — add 'ro' to root mount
/dev/mmcblk0p2  /       ext4    ro,noatime      0  1
tmpfs           /tmp    tmpfs   defaults,size=100M  0  0
tmpfs           /var/log tmpfs  defaults,size=50M   0  0

# Writable data partition for Node-RED, configs, logs
/dev/mmcblk0p3  /data   ext4    defaults,noatime    0  2
```

Node-RED's user directory points to `/data/node-red/`, Docker stores layers in `/data/docker/`, and application logs go to a tmpfs that doesn't wear out the eMMC.

---

## CAN Bus: Talking to Machines

CAN bus is the lingua franca of industrial automation — robots, motor drives, and PLCs all speak it. Linux's SocketCAN interface makes it accessible like a network socket.

### Hardware Setup

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Robot       │   CAN   │  IOT-GATE    │  NATS   │  Node-RED    │
│  Controller  ├────H────┤  CAN0        ├────────→│  Dashboard   │
│  (Kuka KRC)  │   Bus   │              │         │              │
└──────────────┘   120Ω  └──────────────┘         └──────────────┘
                   term.
```

Both ends of the CAN bus need 120Ω termination resistors. The IOT-GATE has a built-in termination jumper.

### SocketCAN Configuration

```bash
# Load the CAN kernel module (usually auto-loaded on CompuLab)
sudo modprobe can
sudo modprobe can-raw

# Configure CAN interface
sudo ip link set can0 type can bitrate 500000 restart-ms 100
sudo ip link set can0 up

# Verify
ip -details link show can0

# Listen for CAN frames
candump can0

# Example output:
#   can0  18FF50E5   [8]  01 A3 00 7B 00 00 FF FF
#   can0  0CF00400   [8]  F0 7D 7D 00 00 00 F0 7D
```

### Decoding CAN Frames

Raw CAN frames are just IDs and bytes. A DBC file (CAN database) maps them to meaningful signals:

```bash
# Using cantools to decode with a DBC file
pip3 install cantools

python3 << 'PYEOF'
import cantools
import can

db = cantools.database.load_file('/data/can/robot_controller.dbc')
bus = can.interface.Bus(channel='can0', interface='socketcan')

for msg in bus:
    try:
        decoded = db.decode_message(msg.arbitration_id, msg.data)
        print(f"ID=0x{msg.arbitration_id:03X}: {decoded}")
    except KeyError:
        pass
PYEOF

# Output:
#   ID=0x185: {'joint1_position': 45.2, 'joint1_velocity': 0.3, 'joint1_torque': 12.5}
#   ID=0x285: {'joint2_position': -12.8, 'joint2_velocity': 0.0, 'joint2_torque': 5.1}
```

### CAN in Node-RED

Using `node-red-contrib-socketcan` or a custom exec node:

```javascript
const can = require('socketcan');
const channel = can.createRawChannel('can0', true);

channel.addListener('onMessage', (msg) => {
    node.send({
        payload: {
            id: msg.id,
            data: Buffer.from(msg.data),
            timestamp: Date.now(),
        },
        topic: `can/${msg.id.toString(16)}`,
    });
});

channel.start();
```

---

## RS-485 / Modbus: Legacy Device Communication

Most industrial sensors and energy meters communicate via Modbus RTU over RS-485. The IOT-GATE has two configurable serial ports.

### Serial Port Configuration

```bash
# Check available serial ports
ls -la /dev/ttyS* /dev/ttyUSB*

# Configure RS-485 mode (CompuLab-specific GPIO for direction control)
# The IOT-GATE handles RTS/CTS flow control automatically in RS-485 mode

# Set serial parameters
stty -F /dev/ttyS1 9600 cs8 -cstopb -parenb raw
```

### Modbus RTU with pymodbus

```python
from pymodbus.client import ModbusSerialClient
import struct
import time

client = ModbusSerialClient(
    port="/dev/ttyS1",
    baudrate=9600,
    parity="N",
    stopbits=1,
    bytesize=8,
    timeout=1,
)

if not client.connect():
    raise ConnectionError("Failed to connect to Modbus device")

def read_energy_meter(unit_id: int = 1) -> dict:
    """Read Eastron SDM630 energy meter via Modbus RTU."""
    registers = {
        "voltage_l1": (0x0000, 2, "f"),
        "voltage_l2": (0x0002, 2, "f"),
        "voltage_l3": (0x0004, 2, "f"),
        "current_l1": (0x0006, 2, "f"),
        "current_l2": (0x0008, 2, "f"),
        "current_l3": (0x000A, 2, "f"),
        "power_total": (0x0034, 2, "f"),
        "energy_total": (0x0156, 2, "f"),
        "frequency": (0x0046, 2, "f"),
    }

    result = {}
    for name, (address, count, fmt) in registers.items():
        response = client.read_input_registers(
            address=address, count=count, slave=unit_id
        )
        if not response.isError():
            raw = struct.pack(">HH", *response.registers)
            result[name] = round(struct.unpack(">f", raw)[0], 3)
        else:
            result[name] = None

    return result

while True:
    data = read_energy_meter(unit_id=1)
    print(f"Voltage L1: {data['voltage_l1']}V, Power: {data['power_total']}W")
    time.sleep(5)
```

### Modbus in Node-RED

The `node-red-contrib-modbus` package handles all the heavy lifting:

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│ Inject   ├───→│ Modbus Read  ├───→│ Parse Float  ├───→│ NATS     │
│ (5 sec)  │    │ FC3: 0x0000  │    │ Big-Endian   │    │ Publish  │
│          │    │ Qty: 2       │    │              │    │          │
└──────────┘    │ Unit ID: 1   │    └──────────────┘    └──────────┘
                │ Serial:      │
                │  /dev/ttyS1  │
                │  9600 8N1    │
                └──────────────┘
```

---

## GPIO: Digital I/O

The IOT-GATE provides 8 optically isolated digital I/O pins. Unlike Raspberry Pi GPIO, these can safely connect to 24V industrial signals.

### Reading Digital Inputs

```bash
# Export GPIO pins (pin numbers are CompuLab-specific)
echo 504 > /sys/class/gpio/export
echo in > /sys/class/gpio/gpio504/direction
cat /sys/class/gpio/gpio504/value
# Output: 1 (24V present) or 0 (no signal)
```

### Python GPIO with Edge Detection

```python
import select
import os

class IndustrialGPIO:
    def __init__(self, pin: int, direction: str = "in"):
        self.pin = pin
        self.path = f"/sys/class/gpio/gpio{pin}"

        if not os.path.exists(self.path):
            with open("/sys/class/gpio/export", "w") as f:
                f.write(str(pin))

        with open(f"{self.path}/direction", "w") as f:
            f.write(direction)

    def read(self) -> int:
        with open(f"{self.path}/value", "r") as f:
            return int(f.read().strip())

    def write(self, value: int):
        with open(f"{self.path}/value", "w") as f:
            f.write(str(value))

    def wait_for_edge(self, edge: str = "both", timeout_ms: int = 5000) -> bool:
        """Block until a signal edge is detected or timeout."""
        with open(f"{self.path}/edge", "w") as f:
            f.write(edge)

        fd = os.open(f"{self.path}/value", os.O_RDONLY)
        os.read(fd, 1)

        epoll = select.epoll()
        epoll.register(fd, select.EPOLLPRI)

        events = epoll.poll(timeout_ms / 1000.0)
        os.close(fd)
        epoll.close()
        return len(events) > 0

machine_running = IndustrialGPIO(504, "in")
beacon_light = IndustrialGPIO(505, "out")

if machine_running.read() == 1:
    beacon_light.write(1)
```

---

## Cellular Connectivity

For sites without reliable Ethernet, the IOT-GATE's Mini-PCIe slot accepts 4G/LTE modems (Sierra Wireless EM7455, Quectel EC25, etc.).

### Modem Setup

```bash
# Install ModemManager
sudo apt install -y modemmanager network-manager

# List detected modems
mmcli -L
#   /org/freedesktop/ModemManager1/Modem/0 [Quectel] EC25

# Check modem status
mmcli -m 0
#   Status:   connected
#   Signal:   -67 dBm (good)
#   Bearer:   /org/freedesktop/ModemManager1/Bearer/0

# Configure automatic connection via NetworkManager
sudo nmcli connection add \
    type gsm \
    con-name "factory-4g" \
    ifname cdc-wdm0 \
    gsm.apn "internet" \
    gsm.pin "" \
    connection.autoconnect yes \
    connection.autoconnect-priority 10 \
    ipv4.route-metric 700

# Ethernet gets priority (metric 100), 4G is fallback (metric 700)
sudo nmcli connection modify "Wired connection 1" \
    ipv4.route-metric 100
```

### Failover Architecture

```
                    ┌──────────────────────────┐
                    │        IOT-GATE           │
                    │                            │
                    │  ┌──────────────────────┐  │
                    │  │ NetworkManager        │  │
                    │  │                        │  │
 ┌──────────┐      │  │  eth0 (metric 100) ◄──┼──┤──── Factory LAN
 │  Cloud   │◄─────┼──┤  wwan0 (metric 700)◄──┼──┤──── 4G/LTE
 │  NATS    │      │  │                        │  │
 └──────────┘      │  │  Auto-failover:        │  │
                    │  │  eth0 down → wwan0     │  │
                    │  │  eth0 up   → eth0      │  │
                    │  └──────────────────────┘  │
                    └──────────────────────────┘
```

NetworkManager handles failover automatically. Combined with NATS leaf nodes (which reconnect transparently), the gateway switches from Ethernet to 4G without losing messages.

### Monitoring Connectivity

```bash
#!/bin/bash
# /data/scripts/connectivity-check.sh — runs every 60 seconds via cron

CLOUD_HOST="cloud-nats.company.com"
LOG="/data/logs/connectivity.log"

ETH_STATUS=$(nmcli -t -f STATE con show "Wired connection 1" 2>/dev/null | head -1)
LTE_STATUS=$(mmcli -m 0 --output-json 2>/dev/null | python3 -c \
    "import sys,json; print(json.load(sys.stdin)['modem']['generic']['state'])")

PING_MS=$(ping -c 1 -W 3 "$CLOUD_HOST" 2>/dev/null | \
    grep -oP 'time=\K[0-9.]+' || echo "timeout")

echo "$(date -Iseconds) eth=$ETH_STATUS lte=$LTE_STATUS ping=${PING_MS}ms" >> "$LOG"
```

---

## Docker on the Edge

Run Node-RED and supporting services in containers for isolation and easy updates:

```yaml
# /data/docker/docker-compose.yml
services:
  node-red:
    image: nodered/node-red:3.1-18-minimal
    restart: always
    ports:
      - "1880:1880"
    volumes:
      - /data/node-red:/data
      - /dev/ttyS1:/dev/ttyS1
    devices:
      - /dev/can0:/dev/can0
    privileged: false
    cap_add:
      - NET_ADMIN
      - SYS_RAWIO
    environment:
      - TZ=Europe/Berlin
      - NATS_URL=nats://nats:4222
    depends_on:
      - nats

  nats:
    image: nats:2.10-alpine
    restart: always
    command: >
      --name edge-gateway
      --js --sd /data
      --leafnodes "tls://cloud-nats.company.com:7422"
    volumes:
      - /data/nats:/data
      - /data/certs:/certs:ro
    ports:
      - "4222:4222"

  telegraf:
    image: telegraf:1.30-alpine
    restart: always
    volumes:
      - /data/telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro
      - /sys:/host/sys:ro
      - /proc:/host/proc:ro
    environment:
      - HOST_PROC=/host/proc
      - HOST_SYS=/host/sys
```

### Resource Limits

On a gateway with 2 GB RAM, set hard limits:

```yaml
services:
  node-red:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
        reservations:
          memory: 256M

  nats:
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.5"
```

---

## Deployment Considerations

### DIN Rail Mounting

```
┌────────────────────────────────────────┐
│            Control Cabinet             │
│                                        │
│  ┌─────────┐  ┌─────────┐  ┌───────┐  │
│  │  PLC    │  │IOT-GATE │  │ PSU   │  │
│  │ Siemens │  │ CompuLab│  │ 24V   │  │
│  │ S7-1200 │  │         │  │ 5A    │  │
│  └────┬────┘  └────┬────┘  └───┬───┘  │
│       │            │           │       │
│  ─────┴────────────┴───────────┴─────  │
│              DIN Rail (TS35)            │
│                                        │
│  Cable entries:                        │
│  • Ethernet (shielded Cat6)            │
│  • CAN bus (twisted pair, shielded)    │
│  • RS-485 (twisted pair, shielded)     │
│  • 4G antenna (SMA, external mount)    │
│  • Power (24V DC from PSU)             │
└────────────────────────────────────────┘
```

### Power

Industrial gateways run on 24V DC — the same supply that powers PLCs and sensors. Use a dedicated 24V DIN rail power supply (Mean Well NDR-120-24 or similar) with enough headroom:

| Component | Power Draw |
|-----------|-----------|
| IOT-GATE-iMX8 | 5W typical, 10W peak |
| 4G modem | 3W typical, 6W during transmit |
| USB peripherals | 2.5W per port max |
| **Total** | **~12W typical, 20W peak** |

A 24V/2.5A (60W) PSU gives comfortable margin. Add a UPS module (e.g., Mean Well DR-UPS40) for graceful shutdown during power loss.

### Temperature

The -40°C to +85°C rating covers most industrial environments, but:

- Mount the gateway in the **upper section** of the cabinet (heat rises, but it's away from the heat-generating VFDs at the bottom).
- Ensure at least 20mm clearance on each side for airflow.
- If the cabinet lacks fans, derate the maximum ambient temperature by 10°C.
- Monitor SoC temperature via sysfs and alert if it exceeds 80°C:

```bash
cat /sys/class/thermal/thermal_zone0/temp
# Output: 52000 (= 52.0°C)
```

### Security Hardening

```bash
# Disable unnecessary services
sudo systemctl disable bluetooth avahi-daemon

# Firewall: only allow SSH, Node-RED, and NATS
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 1880/tcp   # Node-RED (restrict to management VLAN)
sudo ufw allow 4222/tcp   # NATS (local only)
sudo ufw enable

# SSH hardening
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## CompuLab vs Alternatives

| Gateway | CPU | CAN | RS-485 | Cellular | Temp Range | Price |
|---------|-----|-----|--------|----------|-----------|-------|
| **CompuLab IOT-GATE-iMX8** | i.MX 8M Mini | Yes | 2× | Mini-PCIe | -40 to +85°C | ~€400 |
| Advantech UNO-2271G | Atom E3940 | Optional | 2× | M.2 | -20 to +60°C | ~€600 |
| Siemens IOT2050 | TI AM6548 | No | 1× | No | 0 to +50°C | ~€300 |
| OnLogic Factor 201 | i.MX 8M Plus | Optional | 2× | Mini-PCIe | -40 to +85°C | ~€500 |
| Raspberry Pi 4 + enclosure | BCM2711 | No | No | No | 0 to +50°C | ~€150 |

The CompuLab hits the sweet spot of price, I/O, and temperature range. The Siemens IOT2050 is a solid alternative if you don't need CAN or cellular — and it has strong Siemens ecosystem integration.

---

## Conclusion

Industrial edge computing is not about running the fanciest hardware — it's about running **reliable** hardware. A gateway that survives a 40°C summer inside a control cabinet, recovers from power loss without corrupting its filesystem, and connects to both a 1990s Modbus sensor and a modern NATS cluster is worth every euro over a Raspberry Pi.

The CompuLab IOT-GATE is one of several good options. The setup principles — read-only root filesystem, Docker isolation, hardware watchdog, cellular failover, proper grounding and shielding — apply regardless of which hardware you choose. Get these fundamentals right, and the gateway disappears into the background, doing its job for years without attention. That's the goal.
