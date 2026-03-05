---
name: i3X Manufacturing API
tools: [Node-RED, JavaScript, REST API, CESMII]
image: https://raw.githubusercontent.com/blanpa/node-red-contrib-i3x/main/docs/images/preview.png
description: Node-RED integration for the i3X open manufacturing data standard by CESMII
external_url: https://github.com/blanpa/node-red-contrib-i3x
---

# i3X Manufacturing API for Node-RED

Node-RED nodes for the **i3X API** — an open REST specification by CESMII that standardizes access to manufacturing data platforms like historians, MES, and MOM systems.

## Key Features

**Data Access**
- Browse the i3X information model (namespaces, object types, relationships)
- Read current and historical values from industrial objects
- Write real-time values or historical time-series data
- Query with flexible time formats (ISO 8601 or relative like `-7d`)

**Live Subscriptions**
- Subscribe to value changes via Server-Sent Events
- Automatic polling fallback for compatibility

**Configuration**
- Shared connection node with base URL, API version, and TLS settings
- Authentication: none, basic, bearer, or API key

Covers 20 API endpoints across exploration, querying, updates, and subscription management. Includes Docker support and example flows.
