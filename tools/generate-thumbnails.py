#!/usr/bin/env python3
"""Generate AI cover images for posts and projects (FLUX.1-schnell via Hugging Face)."""

import os
import time
import sys

from PIL import Image  # pip install Pillow — used to encode hero images as webp
from huggingface_hub import InferenceClient  # pip install huggingface_hub

# The repository root, not tools/: this script lives one level down but
# writes into content/. Getting this wrong makes every save land in a
# tools/content/ tree that does not exist.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDTH = 1200
HEIGHT = 640  # FLUX prefers multiples of 64

HF_TOKEN = os.environ.get("HF_TOKEN", "")
MODEL = "black-forest-labs/FLUX.1-schnell"

# hf-inference used to serve this model directly and now answers 410
# "deprecated and no longer supported by provider". It lives on at fal-ai,
# nscale and wavespeed, which bill against Hugging Face credits — so the
# calls go through the router's provider selection rather than a hardcoded
# URL, and a provider going away is a config change and not a rewrite.
# Check who still has it:
#   curl -s "https://huggingface.co/api/models/black-forest-labs/FLUX.1-schnell\
#   ?expand[]=inferenceProviderMapping"
PROVIDER = os.environ.get("HF_PROVIDER", "fal-ai")

# The wording is the CSS tokens in prose: canvas against fg, one accent blue,
# hairlines and no glow. Hex codes are in there because they cost nothing, but
# the model works off the colour words, so those carry the description.
#
# "paper" matches the light theme, "ink" the dark one — and defaultAppearance
# is dark, so whichever is picked is a bright or heavy block in the other.
# There is no third option that suits both: a mid-grey suits neither. The
# committed covers are drawn by tools/draw-covers.py, which needs no model and
# no token; this is the alternative, and it has to speak the same palette.
STYLES = {
    "paper": (
        "fine ink drawing on a warm light grey ground (#f7f6f4), "
        "near-black graphite linework with a single burnt-amber accent (#a35b00), "
        "technical etching with engraved crosshatch shading, hairline rules, "
        "restrained editorial illustration for a printed journal, matte and flat, "
        "generous empty ground around the subject, "
        "no glow, no neon, no gradients, no dark background, "
        "no text, no words, no labels, no watermarks"
    ),
    "ink": (
        "fine chalk drawing on a near-black graphite ground (#17191d), "
        "pale grey linework with a single signal-amber accent (#f0b429), "
        "technical etching with engraved crosshatch shading, hairline rules, "
        "restrained editorial illustration, matte and flat, "
        "generous empty ground around the subject, "
        "no glow, no neon, no gradients, no teal, no cyan, "
        "no text, no words, no labels, no watermarks"
    ),
}
STYLE_SUFFIX = STYLES["paper"]  # reassigned from --style in main()

# Map folders to specific scene prompts, keyed by section
PROMPTS = {}

PROMPTS["projects"] = {
    "condition-monitoring": "industrial vibration sensor attached to machine with real-time anomaly detection graphs and health scoring dashboard, predictive maintenance",
    "nats-suite": "abstract network of small nodes joined by fine ruled lines, data routing mesh with multiple endpoints, interconnected server topology drawn as a diagram",
    "kafka-suite": "distributed event streaming pipeline with partitioned topic logs flowing as parallel data rivers, horizontally scaled broker cluster with producers and consumers exchanging high-throughput message streams",
    "cip-suite": "Allen-Bradley ControlLogix PLC rack with EtherNet/IP communication cables and protocol data packets flowing, industrial automation",
    "s7-suite": "Siemens S7-1500 PLC with communication interface, industrial controller exchanging data blocks via protocol connection",
    "opcua-suite": "OPC-UA server and client architecture with information model tree, secure encrypted industrial data exchange",
    "i3x": "unified industrial data interface connecting diverse factory machines through a standardized API gateway, abstract manufacturing network",
}

PROMPTS["blog"] = {
    "nats-edge-to-cloud-pipeline": "industrial factory floor sensors connected to cloud servers by traced data lines, NATS messaging nodes as relay points",
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
    "kafka-shop-floor-event-streaming": "Apache Kafka distributed event log streaming manufacturing sensor data as parallel partitioned rivers, factory floor feeding a high-throughput broker cluster with many independent consumers",
    "allen-bradley-ethernet-ip-node-red": "Allen-Bradley ControlLogix PLC rack with EtherNet/IP communication cables and CIP protocol data packets flowing to an edge device, industrial automation",
    "modbus-node-red": "Modbus RTU serial RS-485 bus connecting industrial meters VFDs and sensors with 16-bit register data words flowing, classic industrial protocol",
    "securing-ot-networks-opcua-purdue": "layered industrial network security with segmented zones and firewalls, Purdue model pyramid of factory levels with an isolated DMZ protecting PLCs, OT cybersecurity",
}



def generate_image(client, section, folder_name, prompt_text):
    """Generate one cover and write it as webp. Returns True on success."""
    full_prompt = f"{prompt_text}, {STYLE_SUFFIX}"
    output_path = os.path.join(REPO_ROOT, "content", section, folder_name, "featured.webp")

    print(f"  Generating: {folder_name}...")
    for attempt in range(3):
        try:
            img = client.text_to_image(
                full_prompt, model=MODEL, width=WIDTH, height=HEIGHT
            )
        except Exception as e:
            msg = str(e)
            # 402 is the free tier's monthly inference credit running out.
            # Retrying cannot fix it, and the remaining folders would each
            # burn a request to learn the same thing.
            if "402" in msg or "payment" in msg.lower() or "credits" in msg.lower():
                print(f"  OUT OF CREDIT: {msg[:200]}")
                raise SystemExit(
                    "\nHugging Face inference credit is exhausted. Covers already "
                    "written are kept; the rest are unchanged."
                )
            if "429" in msg or "rate" in msg.lower():
                print(f"  Rate limited, waiting 60s... (attempt {attempt + 1})")
                time.sleep(60)
                continue
            print(f"  ERROR: {type(e).__name__}: {msg[:200]}")
            return False

        # Re-encode as webp (~95% smaller than the PNG the providers return)
        img.convert("RGB").save(output_path, "WEBP", quality=82, method=6)
        print(f"  OK ({os.path.getsize(output_path) // 1024} KB webp)")
        return True

    print("  FAILED after 3 attempts")
    return False

def main():
    # Usage: tools/generate-thumbnails.py [--style=paper|ink] [section] [filter]
    # section: blog, projects, or all (default: all)
    # filter: substring to match folder names
    #
    # Covers are committed, so a run that comes out wrong is undone with
    # `git checkout -- content/`. Generate one first and look at it before
    # spending the other twenty-three.
    global STYLE_SUFFIX
    argv = sys.argv[1:]
    style = "paper"
    for arg in list(argv):
        if arg.startswith("--style="):
            style = arg.split("=", 1)[1]
            argv.remove(arg)
    if style not in STYLES:
        print(f"unknown style {style!r}: pick one of {', '.join(sorted(STYLES))}", file=sys.stderr)
        return 2
    STYLE_SUFFIX = STYLES[style]

    if not HF_TOKEN:
        print("HF_TOKEN is not set — the API rejects unauthenticated calls.", file=sys.stderr)
        return 2

    client = InferenceClient(provider=PROVIDER, api_key=HF_TOKEN)
    print(f"style: {style}  provider: {PROVIDER}")
    section = argv[0] if len(argv) > 0 else "all"
    only = argv[1] if len(argv) > 1 else None

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
            if generate_image(client, sec, folder, PROMPTS[sec][folder]):
                total_ok += 1
            else:
                total_fail += 1
            if i < len(folders):
                time.sleep(3)

    print(f"\nDone: {total_ok} generated, {total_fail} failed")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
