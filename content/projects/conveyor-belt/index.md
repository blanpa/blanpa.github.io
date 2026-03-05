---
title: "Conveyor Belt Sorting System"
description: "PLC-controlled sorting system with inductive, capacitive, and color sensors — plus ML-based object classification via camera"
tags: ["Raspberry Pi", "PLC", "Python", "Machine Learning"]
weight: 6
---

## Overview

A university project demonstrating industrial sorting automation using a **PiXtend PLC** (Raspberry Pi-based programmable logic controller). The system sorts objects on a conveyor belt using three increasingly sophisticated approaches: inductive sensing, color classification, and machine learning-based image recognition.

## Hardware Setup

The conveyor belt system integrates multiple industrial sensors and actuators:

- **Capacitive sensor** — Detects the presence of any object (metal, plastic, wood)
- **Inductive sensor** — Distinguishes metal from non-metal parts
- **Color sensor** — Classifies objects by color (4 trainable classes)
- **Raspberry Pi Camera** — Captures images for ML-based classification
- **Pneumatic cylinders** — Eject sorted objects at defined positions

### The Controller: PiXtend

The [PiXtend](https://www.pixtend.de/pixtend-v2/) is a PLC based on the Raspberry Pi with industrial-grade digital and analog I/O. It supports RS232, RS485, CAN, Ethernet, WiFi, and Bluetooth — making it a versatile controller for automation projects.

## Test Setup 1 — Material Sorting

The simplest approach: distinguish metal from non-metal using the inductive sensor.

- Capacitive sensor detects object presence
- Inductive sensor checks for metal (HIGH = metal)
- Non-metal → ejected at cylinder 1
- Metal → ejected at cylinder 2

{{< youtube zK1IAr4HmpM >}}

## Test Setup 2 — Color Sorting

Using the color sensor with 4 trained color classes:

- Green → ejected at cylinder 1
- Blue → ejected at cylinder 2
- Red → passes through to the end

{{< youtube LOC4O2OxLF8 >}}

## Test Setup 3 — ML-Based Object Classification

The most advanced approach: a trained neural network classifies objects from camera images.

| Class | Object | Action |
|-------|--------|--------|
| 0 | Conveyor belt | Reference (no action) |
| 1 | Horseshoe | Ejected at cylinder 1 |
| 2 | Cross | Ejected at cylinder 2 |
| 3 | Cylinder | Passes through |

The flow: capacitive sensor detects object → belt stops → camera captures image → ML model predicts class → pneumatic actuator sorts accordingly.

{{< youtube LAhTtD7sYsg >}}

## Key Learnings

- Industrial sensor integration with PLCs
- PLC programming on Raspberry Pi-based controllers
- Training and deploying ML models for real-time classification on embedded hardware
- Pneumatic actuator control and timing
