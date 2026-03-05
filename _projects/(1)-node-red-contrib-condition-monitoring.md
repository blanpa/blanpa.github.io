---
name: Condition Monitoring Suite
tools: [Node-RED, JavaScript, Python, ONNX, TensorFlow, Machine Learning]
image: https://raw.githubusercontent.com/blanpa/node-red-contrib-condition-monitoring/main/docs/images/preview.png
description: Industrial-grade predictive maintenance and anomaly detection for Node-RED
external_url: https://github.com/blanpa/node-red-contrib-condition-monitoring
---

# Condition Monitoring Suite for Node-RED

A Node-RED module providing industrial-grade monitoring capabilities for **predictive maintenance** and **anomaly detection**. 9 specialized nodes for real-time sensor analysis and machine health assessment.

## Key Features

**Anomaly Detection**
- 10 algorithms including Z-Score, IQR, CUSUM, Isolation Forest, and PCA
- Hysteresis mechanisms to prevent false alarm triggers

**Signal Processing**
- High-performance FFT (Radix-4 Cooley-Tukey), vibration analysis, and envelope detection
- Cepstrum analysis for gearbox diagnostics
- ISO 10816-3 vibration severity assessment

**Predictive Maintenance**
- Remaining Useful Life (RUL) calculation with Weibull distribution modeling
- Trend prediction using linear regression and exponential smoothing
- Multi-sensor health aggregation with dynamic weighting

**ML Inference**
- Support for ONNX, TensorFlow.js, Keras, scikit-learn, and TFLite models
- Google Coral / Edge TPU hardware acceleration
- Training data collection with automatic export to CSV/JSONL

Covered by 135 comprehensive unit tests.
