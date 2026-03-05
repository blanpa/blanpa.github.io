---
title: "Automated Table Soccer"
description: "Industrial PLC-controlled table soccer with linear motors, CAN bus communication, and automated ball return"
tags: ["Revolution Pi", "Python", "CAN Bus", "3D Printing"]
weight: 7
date: 2022-03-01
---

## Overview

A university project built for [Dunkermotoren](https://www.dunkermotoren.com/) — an automated table soccer table controlled by an industrial PLC, using linear motors with CAN bus communication and a fully automated ball return mechanism.

## The Challenge

Build a functional, exhibition-ready table soccer system that:
- Uses industrial linear motors (Dunkermotoren BGA 22 dGo) for player movement
- Can be controlled via Sony PlayStation controllers
- Tracks the score automatically via light barriers
- Returns the ball to play after each goal
- Is robust enough for public exhibition at Dunkermotoren

## Architecture

### From Arduino to Revolution Pi

The initial implementation used multiple Arduino microcontrollers communicating with each other. This setup proved unreliable — the limited processing power and lack of real multitasking made coordinated motor control difficult.

The solution: migrate to [Revolution Pi](https://revolutionpi.com/) — an open, modular industrial PC based on the Raspberry Pi. Housed in a DIN-rail enclosure with 24V power, it provides:

- Industrial-grade I/O modules
- Fieldbus gateways (CAN, RS485)
- Real multitasking with full Linux OS
- Graphical configuration tool

### CAN Bus Communication

Each linear motor is controlled via **CAN bus** — the same protocol used in automotive and industrial automation. The Revolution Pi sends position and speed commands to the motor controllers, enabling precise player movement with low latency.

## Ball Return Mechanism

A custom-designed mechanism using 3D-printed components:

1. Ball enters the goal
2. Rolls through a U-shaped tube to a collection point
3. **Light barrier** detects the ball and increments the score
4. Ball is automatically returned to the playing field

The score is displayed on screens visible to both players.

## Result

{{< youtube wgXZfWWLlIM >}}

## Key Learnings

- CAN bus protocol for real-time motor control
- Migration from hobby (Arduino) to industrial (Revolution Pi) controllers
- 3D printing for custom mechanical components
- Real-time system design with multiple actuators and sensors
- Building exhibition-ready industrial demonstrators
