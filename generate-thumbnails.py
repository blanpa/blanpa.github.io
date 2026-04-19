#!/usr/bin/env python3
"""Generate AI thumbnails for blog posts using Hugging Face Inference API (FLUX.1-schnell)."""

import os
import json
import urllib.request
import urllib.parse
import time
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIDTH = 1200
HEIGHT = 640  # FLUX prefers multiples of 64

HF_TOKEN = os.environ.get("HF_TOKEN", "")
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

STYLE_SUFFIX = (
    "dark moody technical illustration, deep dark background with subtle teal and cyan accent lighting, "
    "minimalist industrial aesthetic, clean vector-style elements, dark navy and black tones, "
    "glowing circuit traces and data streams, no text, no words, no labels, no watermarks, "
    "professional tech blog hero image, 8k quality"
)

# Map folders to specific scene prompts, keyed by section
PROMPTS = {}

PROMPTS["projects"] = {
    "condition-monitoring": "industrial vibration sensor attached to machine with real-time anomaly detection graphs and health scoring dashboard, predictive maintenance",
    "nats-suite": "abstract network of glowing nodes connected by light beams in a dark void, data routing mesh with multiple endpoints, futuristic interconnected server topology",
    "kafka-suite": "distributed event streaming pipeline with partitioned topic logs flowing as parallel data rivers, horizontally scaled broker cluster with producers and consumers exchanging high-throughput message streams",
    "cip-suite": "Allen-Bradley ControlLogix PLC rack with EtherNet/IP communication cables and protocol data packets flowing, industrial automation",
    "s7-suite": "Siemens S7-1500 PLC with communication interface, industrial controller exchanging data blocks via protocol connection",
    "opcua-suite": "OPC-UA server and client architecture with information model tree, secure encrypted industrial data exchange",
    "i3x": "unified industrial data interface connecting diverse factory machines through a standardized API gateway, abstract manufacturing network",
    "clab-interfaces": "compact embedded IoT gateway board with GPIO pins, serial ports, CAN bus and cellular antenna, industrial edge hardware",
}

PROMPTS["blog"] = {
    "nats-edge-to-cloud-pipeline": "industrial factory floor sensors connected to cloud servers via glowing data streams, NATS messaging nodes as relay points",
    "compulab-iot-gateway-node-red": "compact embedded IoT gateway device with glowing ports and cables, industrial edge computing hardware",
    "ml-inference-edge-onnx-node-red": "neural network brain on a small edge device, machine learning inference on embedded hardware, data flowing from sensors through ML model",
    "predictive-maintenance-node-red": "industrial machine with vibration sensors and health monitoring graphs, predictive maintenance dashboard with signal waves",
    "mqtt-vs-sparkplug-vs-nats-vs-opcua": "four different messaging protocol symbols interconnected, industrial communication network comparison, data packets flowing",
    "i3x-open-manufacturing-api": "manufacturing API endpoints connecting different industrial machines, standardized data interfaces",
    "node-red-vs-kepware-vs-ignition": "three industrial IoT platforms side by side as abstract architectural blocks, comparison visualization",
    "rest-vs-opcua-vs-graphql-manufacturing": "three API paradigms as abstract geometric shapes exchanging manufacturing data",
    "docker-vs-k3s-edge-deployment": "Docker containers and Kubernetes pods on an industrial edge server, container orchestration",
    "can-bus-reverse-engineering-node-red": "CAN bus data lines with signal analysis oscilloscope view, reverse engineering industrial protocol",
    "siemens-s7-opcua-node-red": "Siemens PLC controller connected via OPC-UA protocol to a monitoring dashboard",
    "cicd-node-red-flows": "CI/CD pipeline with automated testing and deployment stages for IoT flows, DevOps automation",
    "from-process-engineer-to-iiot-developer": "transformation journey from factory floor engineering to software development, industrial to digital",
    "lessons-learned-publishing-npm-packages": "npm package boxes being published and downloaded, open source software distribution",
    "data-engineering-zoomcamp-week-1": "Docker containers and PostgreSQL database with data ingestion pipeline, cloud infrastructure setup",
    "data-engineering-zoomcamp-week-2": "workflow orchestration DAG with connected pipeline stages, data automation",
    "data-engineering-zoomcamp-week-3": "BigQuery data warehouse with analytical queries and data transformations",
    "data-engineering-zoomcamp-week-4": "dbt data transformation models with analytics dashboards and visualizations",
    "data-engineering-zoomcamp-week-5": "Apache Spark cluster processing large datasets in parallel, distributed computing",
    "data-engineering-zoomcamp-week-6": "Apache Kafka streaming data pipeline with real-time event processing",
    "ML-ZoomCamp-week-1": "machine learning regression model with data points and prediction line, introductory ML concepts",
    "ML-ZoomCamp-week-2": "linear regression and feature engineering with mathematical formulas and data matrices",
    "ML-ZoomCamp-week-3": "classification model with decision boundaries separating data clusters",
    "ML-ZoomCamp-week-4": "model evaluation metrics with ROC curves and confusion matrices",
    "ML-ZoomCamp-week-5": "machine learning model deployment with Flask API server and prediction endpoint",
    "ML-ZoomCamp-week-6": "decision trees and random forest ensemble learning visualization",
    "ML-Ops-ZoomCamp-week-1": "MLOps pipeline overview with experiment tracking and model registry",
    "ML-Ops-ZoomCamp-week-2-mlflow": "MLflow experiment tracking dashboard with model metrics and artifacts",
    "ML-Ops-ZoomCamp-week-2-wandb": "Weights and Biases experiment dashboard with training curves and hyperparameters",
    "ML-Ops-ZoomCamp-week-3": "Prefect workflow orchestration with connected ML pipeline tasks",
    "ML-Ops-ZoomCamp-week-4": "ML model deployment infrastructure with serving endpoints and monitoring",
    "ML-Ops-ZoomCamp-week-5": "Grafana monitoring dashboard with ML model performance metrics and Evidently drift detection",
    "ML-Ops-ZoomCamp-week-6": "software engineering best practices with testing frameworks and code quality tools",
}



def generate_image(section, folder_name, prompt_text):
    """Generate image via Hugging Face Inference API."""
    full_prompt = f"{prompt_text}, {STYLE_SUFFIX}"
    content_dir = os.path.join(BASE_DIR, "content", section)
    output_path = os.path.join(content_dir, folder_name, "featured.png")

    print(f"  Generating: {folder_name}...")
    payload = json.dumps({
        "inputs": full_prompt,
        "parameters": {"width": WIDTH, "height": HEIGHT}
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=payload, headers={
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "image/png",
    })

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
                content_type = resp.headers.get("Content-Type", "")
                if "json" in content_type:
                    err = json.loads(data)
                    if "estimated_time" in err:
                        wait = int(err["estimated_time"]) + 5
                        print(f"  Model loading, waiting {wait}s...")
                        time.sleep(wait)
                        continue
                    print(f"  ERROR: {err}")
                    return False
                if len(data) < 5000:
                    print(f"  SKIP (response too small: {len(data)} bytes)")
                    return False
                with open(output_path, "wb") as f:
                    f.write(data)
                print(f"  OK ({len(data) // 1024} KB)")
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 503:
                try:
                    err = json.loads(body)
                    wait = int(err.get("estimated_time", 30)) + 5
                except Exception:
                    wait = 30
                print(f"  Model loading, waiting {wait}s... (attempt {attempt+1})")
                time.sleep(wait)
                continue
            elif e.code == 429:
                print(f"  Rate limited, waiting 60s... (attempt {attempt+1})")
                time.sleep(60)
                continue
            print(f"  ERROR {e.code}: {body[:200]}")
            return False
        except Exception as e:
            print(f"  ERROR: {e}")
            return False
    print(f"  FAILED after 3 attempts")
    return False


def main():
    # Usage: generate-thumbnails.py [section] [filter]
    # section: blog, projects, or all (default: all)
    # filter: substring to match folder names
    section = sys.argv[1] if len(sys.argv) > 1 else "all"
    only = sys.argv[2] if len(sys.argv) > 2 else None

    if section == "all":
        sections = list(PROMPTS.keys())
    elif section in PROMPTS:
        sections = [section]
    else:
        # Treat first arg as filter across all sections
        sections = list(PROMPTS.keys())
        only = section

    total_ok, total_fail = 0, 0
    for sec in sections:
        folders = sorted(PROMPTS[sec].keys())
        if only:
            folders = [f for f in folders if only in f]
        if not folders:
            continue

        print(f"\n=== {sec} ({len(folders)} images) ===\n")
        for i, folder in enumerate(folders, 1):
            print(f"[{i}/{len(folders)}]", end="")
            if generate_image(sec, folder, PROMPTS[sec][folder]):
                total_ok += 1
            else:
                total_fail += 1
            if i < len(folders):
                time.sleep(3)

    print(f"\nDone: {total_ok} generated, {total_fail} failed")


if __name__ == "__main__":
    main()
