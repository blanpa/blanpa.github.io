---
title: "Condition Monitoring Suite"
description: "Industrial-grade predictive maintenance and anomaly detection for Node-RED"
tags: ["Node-RED", "JavaScript", "Python", "Machine Learning", "IIoT"]
weight: 1
date: 2024-09-01
---

## The Problem

Unplanned machine downtime costs manufacturing companies thousands of euros per hour. Traditional maintenance approaches — either reactive (fix when broken) or calendar-based (replace after X months) — are either too late or too wasteful. Sensors generate massive amounts of data, but without the right tools, operators can't act on it in time.

## The Solution

A **Node-RED module** that turns raw sensor data into actionable maintenance insights — directly on the factory floor, without cloud dependency. 9 specialized nodes cover the full predictive maintenance pipeline: from data ingestion and anomaly detection to ML inference and health scoring.

{{< github repo="blanpa/node-red-contrib-condition-monitoring" >}}

## Architecture

The suite is designed as a modular pipeline where each node handles one responsibility:

```
Sensors → Signal Analyzer → Anomaly Detector → Health Index → Dashboard/Alert
                ↓                   ↓
        Training Data          Trend Predictor
          Collector               (RUL)
```

## Anomaly Detection

10 statistical algorithms to catch deviations before they become failures:

| Algorithm | Best For |
|-----------|----------|
| Z-Score | Normally distributed sensor data |
| IQR | Outlier detection with skewed distributions |
| CUSUM | Detecting small, gradual shifts |
| Isolation Forest | Unsupervised ML, no training labels needed |
| PCA | Multivariate anomaly detection across correlated sensors |

All detectors support **hysteresis** — preventing alarm floods from noisy signals oscillating near thresholds.

## Signal Processing

- **FFT** (Radix-4 Cooley-Tukey) for frequency analysis of vibration data
- **Envelope detection** for bearing fault diagnosis
- **Cepstrum analysis** for gearbox diagnostics
- **ISO 10816-3** vibration severity classification (zones A-D)
- **Butterworth filtering** with zero-phase processing

## Predictive Maintenance

- **Remaining Useful Life (RUL)** — Weibull distribution modeling predicts when a component will likely fail
- **Trend prediction** — Linear regression and exponential smoothing forecast sensor trajectories
- **Health Index** — Multi-sensor aggregation with dynamic weighting produces a single 0-100 health score

## ML Inference at the Edge

Run trained models directly in Node-RED without cloud roundtrips:

- **ONNX**, **TensorFlow.js**, **Keras**, **scikit-learn**, **TFLite**
- **Google Coral / Edge TPU** hardware acceleration for real-time inference
- Persistent Python subprocess bridge for efficient repeated inference
- Built-in **Training Data Collector** exports labeled datasets to CSV/JSONL for model retraining

## Quality

- **135 unit tests** covering all nodes and edge cases
- State persistence across Node-RED restarts
- Dynamic runtime configuration via message objects
- MIT licensed, production-ready
