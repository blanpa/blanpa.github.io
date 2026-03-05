---
title: "Running ML Models at the Edge with ONNX and Node-RED"
tags: [iiot, node-red, machine-learning, python, raspberry-pi]
description: "How to deploy trained ML models directly on edge devices using ONNX, TensorFlow Lite, and Google Coral — no cloud required."
date: 2026-03-14
series: ["IIoT"]
---

Every time I hear "just send the data to the cloud for inference," I think about the CNC spindle that threw a bearing 200 ms after the anomaly appeared. The round-trip to AWS takes 150 ms on a good day — and that's assuming the factory Wi-Fi doesn't drop the packet. By the time the cloud responds, the spindle is already damaged.

**Edge inference** means running ML models directly on the device next to the machine. No cloud latency. No bandwidth costs. No dependency on internet connectivity. This post covers how to train a model, export it to ONNX, and deploy it on an edge device through Node-RED.

---

## Why Edge Inference?

| Factor | Cloud Inference | Edge Inference |
|--------|----------------|----------------|
| **Latency** | 50–500 ms (network dependent) | 1–50 ms (local) |
| **Bandwidth** | Raw sensor data uploaded | Only results uploaded |
| **Availability** | Requires internet | Works offline |
| **Privacy** | Data leaves the factory | Data stays on-premises |
| **Cost** | Per-inference API charges | One-time hardware cost |
| **Scalability** | Scales with cloud budget | Scales with edge devices |

For industrial IoT, the strongest arguments are **latency** and **availability**. A vibration anomaly detection model that runs in 5 ms on a Raspberry Pi beats a cloud model every time — because it works when the network doesn't.

### When Cloud Still Makes Sense

Edge inference doesn't replace cloud entirely. Model **training** still benefits from cloud GPU clusters. Complex models with billions of parameters won't fit on a Coral TPU. The sweet spot: **train in the cloud, deploy at the edge**.

---

## Model Format Comparison

Before deploying, you need to export your model to a format the edge device can execute:

| Format | Framework | Target Hardware | Size Overhead | Quantization | Edge Support |
|--------|-----------|-----------------|---------------|-------------|-------------|
| **ONNX** (.onnx) | Any → ONNX | CPU, GPU, NPU | Low | INT8, FP16 | Excellent |
| **TFLite** (.tflite) | TensorFlow/Keras | ARM CPU, Coral TPU | Very low | INT8, FP16 | Excellent |
| **TF.js** (model.json) | TensorFlow/Keras | Browser, Node.js | Medium | None native | Good |
| **scikit-learn pickle** (.pkl) | scikit-learn only | Any Python env | None | None | Limited |
| **PMML** (.pmml) | Various | Java runtimes | High (XML) | None | Niche |
| **CoreML** (.mlmodel) | Any → CoreML | Apple devices | Low | INT8, FP16 | Apple only |

**ONNX wins for industrial edge deployment** because it's framework-agnostic (train in PyTorch, scikit-learn, or TensorFlow — export to the same format) and has the broadest hardware support through ONNX Runtime.

---

## Step-by-Step: Train → Export → Deploy

### The Problem

Classify CNC machine vibration into four states:

- `normal` — machine operating within spec
- `imbalance` — rotating imbalance developing
- `misalignment` — shaft misalignment
- `bearing_fault` — bearing defect

### Step 1: Train the Model in Python

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from scipy.fft import rfft, rfftfreq

def extract_features(signal: np.ndarray, sample_rate: float = 25600.0) -> dict:
    """Extract vibration features from a raw acceleration signal."""
    spectrum = np.abs(rfft(signal)) * 2.0 / len(signal)
    freqs = rfftfreq(len(signal), 1.0 / sample_rate)

    rms = np.sqrt(np.mean(signal ** 2))
    peak = np.max(np.abs(signal))
    kurtosis = float(np.mean((signal - np.mean(signal)) ** 4) /
                      (np.std(signal) ** 4)) if np.std(signal) > 0 else 0

    bands = {
        "low": (10, 200),
        "mid": (200, 2000),
        "high": (2000, 10000),
    }
    band_energy = {}
    for name, (f_low, f_high) in bands.items():
        mask = (freqs >= f_low) & (freqs < f_high)
        band_energy[f"energy_{name}"] = float(np.sum(spectrum[mask] ** 2))

    total_energy = sum(band_energy.values())
    band_ratio = {}
    for name, energy in band_energy.items():
        band_ratio[f"ratio_{name.split('_')[1]}"] = (
            energy / total_energy if total_energy > 0 else 0
        )

    return {
        "rms": rms,
        "peak": peak,
        "crest_factor": peak / rms if rms > 0 else 0,
        "kurtosis": kurtosis,
        **band_energy,
        **band_ratio,
    }

df = pd.read_parquet("vibration_training_data.parquet")

feature_cols = ["rms", "peak", "crest_factor", "kurtosis",
                "energy_low", "energy_mid", "energy_high",
                "ratio_low", "ratio_mid", "ratio_high"]
X = df[feature_cols].values
y = df["label"].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = GradientBoostingClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    random_state=42,
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
```

Output:

```
              precision    recall  f1-score   support

      normal       0.97      0.98      0.98       412
   imbalance       0.94      0.93      0.93       198
misalignment       0.91      0.89      0.90       156
bearing_fault      0.96      0.95      0.96       234

    accuracy                           0.95      1000
   macro avg       0.95      0.94      0.94      1000
weighted avg       0.95      0.95      0.95      1000
```

### Step 2: Export to ONNX

```python
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnx

initial_type = [("features", FloatTensorType([None, len(feature_cols)]))]

onnx_model = convert_sklearn(
    model,
    initial_types=initial_type,
    target_opset=13,
    options={id(model): {"zipmap": False}},
)

onnx.save_model(onnx_model, "vibration_classifier.onnx")

import os
size_kb = os.path.getsize("vibration_classifier.onnx") / 1024
print(f"Model size: {size_kb:.1f} KB")
# Model size: 284.3 KB
```

The `zipmap=False` option is important — it forces the model to output raw probability arrays instead of dictionaries, which ONNX Runtime handles much more efficiently.

### Step 3: Validate the ONNX Model

Always validate that the ONNX model produces identical results to the original:

```python
import onnxruntime as ort
import numpy as np

session = ort.InferenceSession("vibration_classifier.onnx")

input_name = session.get_inputs()[0].name
label_name = session.get_outputs()[0].name
prob_name = session.get_outputs()[1].name

test_input = X_test[:5].astype(np.float32)

onnx_labels = session.run([label_name], {input_name: test_input})[0]
sklearn_labels = model.predict(test_input)

assert np.array_equal(onnx_labels, sklearn_labels), "ONNX output mismatch!"
print("Validation passed: ONNX output matches scikit-learn")
```

### Step 4: Deploy in Node-RED

The inference node calls ONNX Runtime via a Python subprocess:

```python
#!/usr/bin/env python3
"""ONNX inference server for Node-RED — runs as a persistent subprocess."""
import sys
import json
import onnxruntime as ort
import numpy as np

LABELS = ["normal", "imbalance", "misalignment", "bearing_fault"]

session = ort.InferenceSession(
    "vibration_classifier.onnx",
    providers=["CPUExecutionProvider"],
)
input_name = session.get_inputs()[0].name

for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        features = np.array(data["features"], dtype=np.float32).reshape(1, -1)

        labels, probabilities = session.run(None, {input_name: features})

        result = {
            "prediction": LABELS[int(labels[0])],
            "confidence": round(float(np.max(probabilities)), 4),
            "probabilities": {
                label: round(float(p), 4)
                for label, p in zip(LABELS, probabilities[0])
            },
        }
        print(json.dumps(result), flush=True)
    except Exception as e:
        print(json.dumps({"error": str(e)}), flush=True)
```

The Node-RED flow:

```
┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│ MQTT In  ├───→│ Feature      ├───→│ ONNX Inference├───→│ Route by     │
│ raw      │    │ Extraction   │    │ (Python)      │    │ prediction   │
│ vibration│    │ (function)   │    └───────────────┘    └──────┬───────┘
└──────────┘    └──────────────┘                               │
                                                    ┌──────────┼──────────┐
                                                    ▼          ▼          ▼
                                              [Dashboard] [Alert if   [Log to
                                                          abnormal]   InfluxDB]
```

Node-RED function node for feature extraction:

```javascript
const samples = msg.payload.samples;
const n = samples.length;

let sum = 0, sumSq = 0, peak = 0;
for (let i = 0; i < n; i++) {
    sum += samples[i];
    sumSq += samples[i] * samples[i];
    if (Math.abs(samples[i]) > peak) peak = Math.abs(samples[i]);
}
const mean = sum / n;
const rms = Math.sqrt(sumSq / n);
const crestFactor = peak / rms;

let m4 = 0;
for (let i = 0; i < n; i++) {
    m4 += Math.pow(samples[i] - mean, 4);
}
const std = Math.sqrt(sumSq / n - mean * mean);
const kurtosis = std > 0 ? (m4 / n) / Math.pow(std, 4) : 0;

msg.payload = {
    features: [rms, peak, crestFactor, kurtosis,
               msg.payload.energy_low, msg.payload.energy_mid,
               msg.payload.energy_high, msg.payload.ratio_low,
               msg.payload.ratio_mid, msg.payload.ratio_high]
};
return msg;
```

---

## Google Coral Edge TPU Acceleration

The [Coral Edge TPU](https://coral.ai/) is a USB or M.2 accelerator that runs quantized TensorFlow Lite models at high speed with minimal power consumption.

### Performance Benchmarks

Inference time for a vibration classification model (10 features → 4 classes):

| Platform | Model Format | Inference Time | Power |
|----------|-------------|---------------|-------|
| Raspberry Pi 4 (CPU) | ONNX | 12 ms | 5W |
| Raspberry Pi 4 (CPU) | TFLite | 8 ms | 5W |
| Raspberry Pi 4 + Coral USB | TFLite (INT8) | 0.7 ms | 7W |
| CompuLab IOT-GATE + Coral M.2 | TFLite (INT8) | 0.5 ms | 10W |
| Jetson Nano (GPU) | ONNX | 2 ms | 10W |
| Cloud API (AWS) | ONNX | 80–200 ms | N/A |

The Coral TPU is **10–15× faster** than CPU inference for quantized models. For a simple classifier this doesn't matter much, but for CNN-based models processing spectrograms, the difference is enormous.

### Deploying to Coral

The workflow: TensorFlow → TFLite → INT8 Quantization → Edge TPU Compilation.

```python
import tensorflow as tf
import numpy as np

keras_model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation="relu", input_shape=(10,)),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(4, activation="softmax"),
])
keras_model.compile(optimizer="adam", loss="sparse_categorical_crossentropy")
keras_model.fit(X_train, y_train_encoded, epochs=50, batch_size=32, verbose=0)

def representative_dataset():
    for i in range(100):
        yield [X_train[i:i+1].astype(np.float32)]

converter = tf.lite.TFLiteConverter.from_keras_model(keras_model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.uint8
converter.inference_output_type = tf.uint8

tflite_model = converter.convert()

with open("vibration_classifier_quant.tflite", "wb") as f:
    f.write(tflite_model)
```

Then compile for the Edge TPU (requires the `edgetpu_compiler`):

```bash
edgetpu_compiler vibration_classifier_quant.tflite
# Output: vibration_classifier_quant_edgetpu.tflite
```

Python inference on Coral:

```python
from pycoral.utils.edgetpu import make_interpreter
import numpy as np

interpreter = make_interpreter("vibration_classifier_quant_edgetpu.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_scale, input_zero = input_details[0]["quantization"]
features_quant = np.uint8(features / input_scale + input_zero)

interpreter.set_tensor(input_details[0]["index"], features_quant.reshape(1, -1))
interpreter.invoke()

output = interpreter.get_tensor(output_details[0]["index"])
output_scale, output_zero = output_details[0]["quantization"]
probabilities = (output.astype(np.float32) - output_zero) * output_scale

predicted_class = LABELS[np.argmax(probabilities)]
confidence = float(np.max(probabilities))
```

---

## Model Lifecycle Management

Deploying a model once is not enough. Models degrade as operating conditions change — a phenomenon called **model drift**. A production system needs a full lifecycle:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Train   ├───→│  Export   ├───→│  Deploy  ├───→│  Monitor ├───→│ Retrain  │
│          │    │  (ONNX/   │    │  (Edge   │    │  (Drift  │    │  (New    │
│  (Cloud) │    │   TFLite) │    │  Device) │    │  Detect) │    │  Data)   │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘    └────┬─────┘
                                                     │               │
                                                     └───────────────┘
                                                      Feedback Loop
```

### Model Versioning

Track every deployed model with metadata:

```json
{
  "model_id": "vib-classifier-v3",
  "framework": "scikit-learn",
  "format": "onnx",
  "created": "2026-03-10T14:00:00Z",
  "training_data": {
    "samples": 12400,
    "date_range": ["2025-09-01", "2026-02-28"],
    "machines": ["cnc-001", "cnc-002", "cnc-003"]
  },
  "metrics": {
    "accuracy": 0.952,
    "f1_macro": 0.944
  },
  "deployed_to": ["gateway-hall-a", "gateway-hall-b"],
  "deployed_at": "2026-03-12T08:00:00Z"
}
```

### Drift Detection

Monitor prediction distributions over time. If the model starts predicting "normal" 99.5% of the time when it used to predict 92%, either all machines magically healed or the input distribution shifted:

```python
from scipy.stats import ks_2samp

def detect_drift(
    reference_predictions: np.ndarray,
    current_predictions: np.ndarray,
    threshold: float = 0.05,
) -> dict:
    """Kolmogorov-Smirnov test for prediction distribution drift."""
    statistic, p_value = ks_2samp(reference_predictions, current_predictions)
    return {
        "drift_detected": p_value < threshold,
        "ks_statistic": round(float(statistic), 4),
        "p_value": round(float(p_value), 4),
    }
```

### OTA Model Updates

When a new model version is ready, push it to edge devices without downtime:

```
┌─────────────────────────────────────────────────────────────┐
│                    Model Update Flow                         │
│                                                              │
│  [Model Registry]──→[NATS/MQTT]──→[Edge Gateway]            │
│   (S3 / MinIO)       "model.update"  │                       │
│                                      ▼                       │
│                              [Download .onnx]                │
│                                      │                       │
│                              [Validate locally]              │
│                                      │                       │
│                              [Hot-swap model]                │
│                                      │                       │
│                              [Report new version]            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

The Node-RED flow listens for model update messages, downloads the new ONNX file, validates it against a test dataset stored locally, and swaps it into the inference pipeline — all without restarting the flow.

---

## Practical Tips

**Start small.** A Gradient Boosting classifier with 10 features runs in microseconds on any hardware. Don't jump to CNNs unless your problem genuinely needs spatial/temporal pattern recognition on raw signals.

**Quantize aggressively.** INT8 models are 4× smaller than FP32 and run faster on every platform. Accuracy loss for tabular classifiers is typically < 0.5%.

**Batch when possible.** If you're processing vibration bursts (1024 samples every 5 seconds), you have time to batch multiple sensors into a single inference call. ONNX Runtime handles batches much more efficiently than single predictions.

**Profile memory.** A Raspberry Pi 4 has 4 GB RAM. ONNX Runtime's session overhead is ~50 MB. A typical model is < 1 MB. But if you load 20 models simultaneously, memory adds up — especially with Python's baseline footprint.

**Test on the target device.** A model that runs in 5 ms on your laptop might take 50 ms on an ARM CPU. Always benchmark on the actual edge hardware before committing to an architecture.

---

## Conclusion

The cloud is not the answer for every ML inference problem. When latency matters, when connectivity is unreliable, or when data privacy is non-negotiable, edge inference is the right choice. ONNX provides the bridge between training convenience (use any framework you want) and deployment flexibility (run anywhere ONNX Runtime runs).

The toolchain is mature: scikit-learn → ONNX → ONNX Runtime on ARM takes about 20 lines of code. The hard part isn't the deployment — it's collecting enough labeled training data and building the monitoring pipeline to detect when the model needs retraining.

Start with a simple classifier. Deploy it on a Pi. Prove the value. Then add Coral acceleration, OTA updates, and drift detection. The factory floor doesn't need a PhD — it needs a model that works at 3 AM when the internet is down.
