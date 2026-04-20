---
title: "Docker vs K3s on the Shop Floor — Edge Deployment Strategies"
tags: [iiot, docker, kubernetes]
description: "When to use plain Docker and when to deploy K3s for industrial edge computing — with practical deployment examples."
date: 2026-04-18
series: ["IIoT"]
---

Containers on the shop floor used to be a hard sell. "Why not just install the software directly?" plant engineers would ask. After rolling back a failed manual update at 2 AM for the third time, the answer becomes obvious: reproducibility, isolation, and the ability to roll back in seconds instead of hours.

The real question isn't *whether* to use containers in industrial environments — it's whether to use **Docker Compose** or go all in with **K3s** (lightweight Kubernetes). I've deployed both. Here's when each makes sense.

---

## Why Containers on the Shop Floor?

```
Without Containers:
┌─────────────────────────────────────────────────┐
│              Industrial Edge PC                  │
│                                                  │
│  Node-RED v3.1    (depends on Node.js 18)       │
│  Grafana v10.2    (depends on libfontconfig)    │
│  PostgreSQL 15    (port conflict with legacy)   │
│  NATS Server      (manual systemd service)      │
│  Python 3.11      (but script needs 3.9)        │
│                                                  │
│  State: "works on my machine" / "don't touch it"│
└─────────────────────────────────────────────────┘

With Containers:
┌─────────────────────────────────────────────────┐
│              Industrial Edge PC                  │
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Node-RED │ │ Grafana  │ │PostgreSQL│        │
│  │  3.1     │ │  10.2    │ │   15     │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐                      │
│  │   NATS   │ │ Python   │                      │
│  │  Server  │ │   3.9    │                      │
│  └──────────┘ └──────────┘                      │
│                                                  │
│  State: version-pinned, isolated, reproducible  │
└─────────────────────────────────────────────────┘
```

The benefits are concrete:

- **Reproducibility** — the exact same image runs on dev, staging, and production
- **Isolation** — Node-RED's Node.js 18 doesn't conflict with Python 3.9
- **Rollback** — failed update? `docker compose down && docker compose up` with the previous tag
- **Portability** — works on Ubuntu, Debian, RHEL, or any Linux
- **Security** — each service runs in its own namespace with minimal privileges

---

## Docker Compose: Simple Edge Deployments

Docker Compose is the right choice when you have **one edge PC running 2–8 services**. No orchestration overhead, no cluster management, just a YAML file and `docker compose up`.

### Industrial Stack Example

```yaml
# docker-compose.yml — Complete IIoT edge stack
services:
  nodered:
    image: nodered/node-red:3.1.9
    restart: unless-stopped
    ports:
      - "1880:1880"
    volumes:
      - nodered_data:/data
      - /dev:/dev  # for serial/USB device access
    environment:
      - TZ=Europe/Berlin
      - NODE_RED_CREDENTIAL_SECRET=${CREDENTIAL_SECRET}
    networks:
      - factory
    deploy:
      resources:
        limits:
          memory: 512M

  nats:
    image: nats:2.10-alpine
    restart: unless-stopped
    ports:
      - "4222:4222"
      - "8222:8222"  # monitoring
    volumes:
      - ./nats.conf:/etc/nats/nats.conf:ro
      - nats_data:/data
    command: ["-c", "/etc/nats/nats.conf", "--js"]
    networks:
      - factory
    deploy:
      resources:
        limits:
          memory: 256M

  grafana:
    image: grafana/grafana:10.2.3
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-clock-panel
    networks:
      - factory
    deploy:
      resources:
        limits:
          memory: 256M

  postgres:
    image: timescaledb/timescaledb:2.13.1-pg15
    restart: unless-stopped
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    environment:
      - POSTGRES_DB=factory
      - POSTGRES_USER=iiot
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    networks:
      - factory
    deploy:
      resources:
        limits:
          memory: 1G

  mosquitto:
    image: eclipse-mosquitto:2.0
    restart: unless-stopped
    ports:
      - "1883:1883"
      - "9001:9001"  # WebSocket
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
      - mosquitto_data:/mosquitto/data
    networks:
      - factory

volumes:
  nodered_data:
  nats_data:
  grafana_data:
  postgres_data:
  mosquitto_data:

networks:
  factory:
    driver: bridge
```

### Host Network for Fieldbus Access

Industrial protocols often require direct network access — multicast for PROFINET discovery, broadcast for Modbus UDP, or raw sockets for EtherNet/IP. The `host` network mode gives containers direct access to the host's network interfaces:

```yaml
services:
  opcua-gateway:
    image: my-registry.local/opcua-gateway:1.2.0
    restart: unless-stopped
    network_mode: host  # direct access to all interfaces
    volumes:
      - ./certs:/app/certs:ro
    environment:
      - PLC_ADDRESS=192.168.1.100
      - OPCUA_PORT=4840
    privileged: false
    cap_add:
      - NET_RAW  # for raw socket access if needed
```

When to use host networking:
- OPC-UA discovery via multicast
- Modbus on non-standard ports or UDP
- PROFINET or EtherCAT (require Layer 2 access)
- Any protocol that uses broadcast/multicast discovery

### USB and Serial Device Access

Many industrial devices connect via USB or serial. Pass devices through to containers:

```yaml
services:
  modbus-serial:
    image: my-registry.local/modbus-reader:1.0.0
    restart: unless-stopped
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0  # USB-to-RS485 adapter
    group_add:
      - dialout  # serial port access group
```

### Update Strategy with Docker Compose

```bash
#!/bin/bash
# update.sh — Safe update with automatic rollback

COMPOSE_FILE="docker-compose.yml"
BACKUP_TAG=$(date +%Y%m%d_%H%M%S)

echo "Pulling new images..."
docker compose pull

echo "Backing up current state..."
docker compose config > "backup_${BACKUP_TAG}.yml"

echo "Rolling update (one service at a time)..."
for service in nats postgres mosquitto grafana nodered; do
    echo "Updating ${service}..."
    docker compose up -d --no-deps "${service}"

    echo "Waiting for ${service} to be healthy..."
    sleep 10

    if ! docker compose ps "${service}" | grep -q "Up"; then
        echo "ERROR: ${service} failed to start! Rolling back..."
        docker compose up -d --no-deps "${service}"
        exit 1
    fi
done

echo "All services updated."
docker compose ps
```

---

## K3s: Multi-Node Edge Clusters

When a single edge PC isn't enough — multiple machines, high availability requirements, 10+ services, or fleet management across sites — K3s brings Kubernetes to the shop floor without the resource overhead.

### What is K3s?

K3s is a certified Kubernetes distribution optimized for edge and IoT:

```
Full Kubernetes (K8s)              K3s
─────────────────────              ───
~600MB RAM minimum                 ~512MB RAM minimum
etcd (heavy)                       SQLite or embedded etcd
Multiple binaries                  Single ~70MB binary
Complex installation               curl | sh
```

### Resource Comparison (ARM64, Raspberry Pi 4)

| Component | Docker + Compose | K3s (single node) | K3s (3-node cluster) |
|-----------|------------------|--------------------|-----------------------|
| **Base RAM** | ~50 MB | ~512 MB | ~512 MB per node |
| **CPU idle** | ~1% | ~3–5% | ~3–5% per node |
| **Disk** | ~500 MB (engine) | ~200 MB (binary) | ~200 MB per node |
| **5-service stack RAM** | ~1.2 GB total | ~1.8 GB total | ~2.5 GB total |
| **Startup time** | ~10 seconds | ~30 seconds | ~60 seconds |
| **Complexity** | Low | Medium | High |

K3s adds ~500 MB RAM overhead over plain Docker. On a 4 GB Raspberry Pi, that's significant. On an 8+ GB industrial PC, it's negligible.

### K3s Installation

```bash
# Server node (control plane)
curl -sfL https://get.k3s.io | sh -s - \
    --write-kubeconfig-mode 644 \
    --disable traefik \
    --disable servicelb \
    --node-name edge-server-01

# Get the join token
cat /var/lib/rancher/k3s/server/node-token

# Agent nodes (workers)
curl -sfL https://get.k3s.io | K3S_URL=https://edge-server-01:6443 \
    K3S_TOKEN=<token> sh -s - --node-name edge-worker-01
```

### Industrial Stack on K3s

#### Namespace and Secrets

```yaml
# 00-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: factory-edge
---
# 01-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: factory-secrets
  namespace: factory-edge
type: Opaque
stringData:
  db-password: "${DB_PASSWORD}"
  grafana-password: "${GRAFANA_PASSWORD}"
  credential-secret: "${CREDENTIAL_SECRET}"
```

#### TimescaleDB StatefulSet

```yaml
# 02-timescaledb.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: timescaledb
  namespace: factory-edge
spec:
  serviceName: timescaledb
  replicas: 1
  selector:
    matchLabels:
      app: timescaledb
  template:
    metadata:
      labels:
        app: timescaledb
    spec:
      containers:
        - name: timescaledb
          image: timescaledb/timescaledb:2.13.1-pg15
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: factory
            - name: POSTGRES_USER
              value: iiot
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: factory-secrets
                  key: db-password
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              memory: 512Mi
              cpu: 250m
            limits:
              memory: 1Gi
              cpu: 1000m
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: timescaledb
  namespace: factory-edge
spec:
  selector:
    app: timescaledb
  ports:
    - port: 5432
      targetPort: 5432
```

#### Node-RED Deployment

```yaml
# 03-nodered.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodered
  namespace: factory-edge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nodered
  template:
    metadata:
      labels:
        app: nodered
    spec:
      containers:
        - name: nodered
          image: nodered/node-red:3.1.9
          ports:
            - containerPort: 1880
          env:
            - name: TZ
              value: Europe/Berlin
            - name: NODE_RED_CREDENTIAL_SECRET
              valueFrom:
                secretKeyRef:
                  name: factory-secrets
                  key: credential-secret
          volumeMounts:
            - name: data
              mountPath: /data
          resources:
            requests:
              memory: 256Mi
              cpu: 250m
            limits:
              memory: 512Mi
              cpu: 500m
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: nodered-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nodered-data
  namespace: factory-edge
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: Service
metadata:
  name: nodered
  namespace: factory-edge
spec:
  selector:
    app: nodered
  ports:
    - port: 1880
      targetPort: 1880
```

#### NATS with JetStream

```yaml
# 04-nats.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nats
  namespace: factory-edge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nats
  template:
    metadata:
      labels:
        app: nats
    spec:
      containers:
        - name: nats
          image: nats:2.10-alpine
          args: ["-js", "-m", "8222"]
          ports:
            - containerPort: 4222
              name: client
            - containerPort: 8222
              name: monitor
          resources:
            requests:
              memory: 64Mi
              cpu: 100m
            limits:
              memory: 256Mi
              cpu: 500m
---
apiVersion: v1
kind: Service
metadata:
  name: nats
  namespace: factory-edge
spec:
  selector:
    app: nats
  ports:
    - name: client
      port: 4222
      targetPort: 4222
    - name: monitor
      port: 8222
      targetPort: 8222
```

---

## Fleet Management

### Docker: Portainer

Portainer provides a web UI for managing Docker hosts across multiple sites:

```yaml
# On each edge PC:
services:
  portainer-agent:
    image: portainer/agent:2.19
    restart: unless-stopped
    ports:
      - "9001:9001"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/volumes:/var/lib/docker/volumes

# Central Portainer server:
services:
  portainer:
    image: portainer/portainer-ce:2.19
    restart: unless-stopped
    ports:
      - "9443:9443"
    volumes:
      - portainer_data:/data
```

```
┌──────────────────────────────────────────────────────┐
│                 Portainer Server                      │
│                 (Central Office)                      │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Site Overview                                  │ │
│  │                                                 │ │
│  │  Munich    ● Online   5 containers   CPU: 23%  │ │
│  │  Berlin    ● Online   4 containers   CPU: 15%  │ │
│  │  Hamburg   ● Offline  -              CPU: -    │ │
│  │  Dresden   ● Online   6 containers   CPU: 31%  │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
         │            │            │
    ┌────┴───┐   ┌────┴───┐   ┌───┴────┐
    │ Agent  │   │ Agent  │   │ Agent  │
    │ Munich │   │ Berlin │   │Dresden │
    └────────┘   └────────┘   └────────┘
```

### K3s: Rancher

Rancher manages multiple K3s clusters from a single dashboard:

```bash
# Install Rancher on a central server
docker run -d --restart=unless-stopped \
    -p 80:80 -p 443:443 \
    --privileged \
    rancher/rancher:latest

# Then import each K3s cluster via the Rancher UI
```

Rancher adds:
- **Cluster monitoring** — Prometheus + Grafana pre-configured
- **RBAC** — role-based access per cluster, namespace, or workload
- **App catalog** — Helm charts for common industrial applications
- **Backup/Restore** — automated cluster state backups

---

## Persistent Storage

Industrial data must survive container restarts, node reboots, and even hardware failures.

### Docker: Named Volumes

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/ssd/postgres  # dedicated SSD partition
```

### K3s: Local Path Provisioner (default)

K3s includes a local-path provisioner that automatically creates PersistentVolumes on the node's filesystem:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: historian-data
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: local-path  # K3s default
  resources:
    requests:
      storage: 100Gi
```

For multi-node clusters, consider **Longhorn** (also by Rancher) for replicated block storage:

```bash
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.6.0/deploy/longhorn.yaml
```

---

## OTA Updates & Rollback

### Docker Compose Rollback

```bash
# Current state
docker compose ps
# NAME       IMAGE                    STATUS
# nodered    nodered/node-red:3.1.9   Up 5 days

# Update
docker compose pull nodered
docker compose up -d --no-deps nodered

# Something broke? Rollback immediately:
docker compose up -d --no-deps nodered  # uses cached previous image

# Or pin explicitly:
# In docker-compose.yml, change:  image: nodered/node-red:3.1.8
docker compose up -d --no-deps nodered
```

### K3s Rolling Updates

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodered
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    spec:
      containers:
        - name: nodered
          image: nodered/node-red:3.1.9
```

```bash
# Update the image
kubectl set image deployment/nodered nodered=nodered/node-red:3.2.0 -n factory-edge

# Watch the rollout
kubectl rollout status deployment/nodered -n factory-edge

# Something broke? One command:
kubectl rollout undo deployment/nodered -n factory-edge

# Check rollout history
kubectl rollout history deployment/nodered -n factory-edge
# REVISION  CHANGE-CAUSE
# 1         Initial deployment
# 2         Image update to 3.2.0
# 3         Rollback to 3.1.9
```

K3s rollback is more powerful — Kubernetes keeps revision history and can roll back to any previous state.

---

## Networking Considerations

### Docker Networking

```
Docker Bridge Network (default)
┌──────────────────────────────────────┐
│  docker0 (172.17.0.0/16)            │
│                                      │
│  ┌────────┐  ┌────────┐  ┌────────┐ │
│  │Node-RED│  │  NATS  │  │Grafana │ │
│  │ .2     │  │  .3    │  │  .4    │ │
│  └───┬────┘  └───┬────┘  └───┬────┘ │
│      └──────┬────┘           │       │
│             │  Service discovery     │
│             │  via container names   │
│             │                        │
└─────────────┼────────────────────────┘
              │
         Host Network
    ┌─────────┴─────────┐
    │  eth0: 192.168.1.50│ ←── factory LAN
    │  eth1: 10.0.0.50   │ ←── PLC network (isolated)
    └────────────────────┘
```

### K3s Networking

K3s uses Flannel (VXLAN) by default. For industrial environments, consider `--flannel-backend=host-gw` (no encapsulation overhead) or `--flannel-backend=none` with a custom CNI for advanced network policies:

```bash
curl -sfL https://get.k3s.io | sh -s - \
    --flannel-backend=host-gw \
    --node-name edge-server-01
```

### Dual-NIC Setup (IT/OT Separation)

Industrial edge PCs typically have two network interfaces — one for the IT network (dashboards, cloud) and one for the OT/PLC network:

```yaml
# Docker: use macvlan for OT network access
networks:
  ot-network:
    driver: macvlan
    driver_opts:
      parent: eth1  # OT-facing NIC
    ipam:
      config:
        - subnet: 10.0.0.0/24
          gateway: 10.0.0.1
```

---

## Decision Matrix

| Criterion | Docker Compose | K3s |
|-----------|----------------|-----|
| **Number of services** | 2–8 | 8+ |
| **Number of nodes** | 1 | 1–50+ |
| **High availability** | No (DIY) | Yes (multi-server) |
| **Auto-healing** | `restart: unless-stopped` | Full pod rescheduling |
| **Rolling updates** | Manual (script) | Built-in |
| **Rollback** | Manual | `kubectl rollout undo` |
| **Secret management** | `.env` files | Kubernetes Secrets (or Vault) |
| **Service discovery** | Container names | DNS + Services |
| **Load balancing** | None (or Traefik external) | Built-in |
| **Resource limits** | `deploy.resources` | requests/limits (enforced) |
| **Learning curve** | Low | Medium–High |
| **RAM overhead** | ~50 MB | ~512 MB |
| **Team required** | 1 developer | 1–2 with K8s experience |
| **Minimum hardware** | Raspberry Pi 3 (1GB) | Raspberry Pi 4 (4GB) |

### My Rule of Thumb

```
 1 edge PC, ≤5 services       →  Docker Compose
 1 edge PC, 5-10 services     →  Docker Compose (still fine)
 2+ edge PCs, same site       →  K3s
 Multiple sites, fleet mgmt   →  K3s + Rancher
 HA requirement (99.9%+)      →  K3s (multi-server)
 Raspberry Pi / 2GB RAM       →  Docker Compose
 Industrial PC / 8GB+ RAM     →  Either (your choice)
```

---

## Security Hardening

### Docker

```yaml
services:
  nodered:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
    cap_drop:
      - ALL
```

### K3s

```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
    - name: nodered
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
```

---

## Practical Recommendation

**Start with Docker Compose.** It's simpler, uses fewer resources, and covers 80% of edge deployment scenarios. A single `docker-compose.yml` file is easy to version, backup, and transfer between sites.

**Graduate to K3s when** you hit one of these triggers:
- You need to manage more than 3 edge nodes at a single site
- High availability is a requirement (production-critical systems)
- You're managing 5+ sites and need fleet management
- Your team already knows Kubernetes

The transition from Docker Compose to K3s is not trivial but also not dramatic — the container images stay the same. You're mainly translating `docker-compose.yml` into Kubernetes manifests. Tools like `kompose` can automate most of the conversion:

```bash
kompose convert -f docker-compose.yml -o k3s-manifests/
```

Whatever you choose, the key principle stays the same: **treat edge infrastructure as code**. Version your compose files or K3s manifests in Git, automate your deployments, and never SSH into an edge PC to manually install software again.
