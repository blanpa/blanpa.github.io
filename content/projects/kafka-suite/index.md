---
title: "Kafka Suite"
description: "Comprehensive Apache Kafka integration for Node-RED with Schema Registry, dual-backend support, and managed service presets"
tags: ["Node-RED", "JavaScript", "Kafka", "IIoT"]
weight: 2
date: 2026-04-10
---

## The Problem

Apache Kafka is the de-facto standard for high-throughput event streaming in enterprise and industrial data pipelines — but getting Node-RED to talk to Kafka properly means picking a client library, wiring up Schema Registry, handling SASL/mTLS for managed services, and tuning consumer groups by hand. Existing Node-RED Kafka nodes cover the basics but fall short on schema handling, authentication variety, and production-grade connection management.

## The Solution

A comprehensive **Node-RED integration for Apache Kafka** with producer/consumer/admin nodes, Confluent-compatible **Schema Registry** support, and a choice of two backends — pure-JavaScript `kafkajs` or the native `librdkafka` binding — selectable per broker. Managed-service presets make connecting to Confluent Cloud, AWS MSK, Azure Event Hubs, Aiven, and Redpanda a one-click affair.

{{< github repo="blanpa/node-red-contrib-kafka-suite" >}}

## Producer

- **Single & batch messaging** — publish one message or many in a single call
- **Key-based partitioning** — deterministic routing via message keys
- **Headers & compression** — GZIP, Snappy, LZ4, ZSTD
- **Delivery confirmation** — success output emits `msg.kafka` metadata (topic, partition, offset)

## Consumer

- **Consumer groups** — automatic load balancing across instances
- **Offset management** — earliest/latest/explicit, commit strategies
- **Pause/resume controls** — backpressure without disconnecting
- **Flexible payload formats** — JSON, UTF-8, or raw Buffer
- **Concurrent partition consumption** — parallel processing per topic

## Admin Operations

Unified `msg.action` interface for:

- **Topic lifecycle** — create, delete, list, describe, alter configs
- **Cluster inspection** — brokers, controllers, metadata
- **Consumer group administration** — list, describe, delete, reset offsets
- **Offset manipulation** — seek to timestamp, earliest, latest

## Schema Registry

Confluent-compatible wire format for structured data:

- **Avro, JSON Schema, Protobuf** — encode and decode transparently
- **Automatic schema registration** — optional, per producer
- **Subject compatibility checking** — catches breaking changes at publish time

## Dual-Backend Architecture

| Backend | Implementation | Best For |
|---------|---------------|----------|
| `kafkajs` | Pure JavaScript | Edge devices, no C++ toolchain, easy install |
| `@confluentinc/kafka-javascript` | Native librdkafka | Higher throughput, Kafka 4.0 protocol |

Backend is selected per broker config — mix and match in the same flow.

## Managed Service Presets

Built-in one-click configurations for:

- **Confluent Cloud** — SASL/PLAIN
- **AWS MSK** — IAM and SCRAM variants
- **Azure Event Hubs** — Kafka protocol endpoint
- **Aiven** — mutual TLS
- **Redpanda** — self-hosted or cloud
- **Self-hosted clusters** — full custom SASL/TLS

## Authentication & Security

- **SASL** — PLAIN, SCRAM-SHA-256/512, OAUTHBEARER
- **Mutual TLS** — drag-and-drop certificates
- **Unauthenticated** — for dev/test clusters
- **Connection pooling** — shared connection per broker config with ref-counted lifecycle and automatic reconnection
