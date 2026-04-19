---
title: "About"
description: "IIoT Software Developer with an Industrial Engineering background — building connectivity solutions from edge to cloud."
layout: "simple"
---

<div class="about-hero">
  <h2 class="about-hero__title">Building the bridge between <span class="accent">shop floor</span> and <span class="accent">cloud</span></h2>
  <p class="about-hero__text">I am an IIoT Software Developer with an Industrial Engineering background. I build industrial connectivity solutions — from edge gateways and fieldbus protocols to real-time messaging and predictive maintenance. My focus is on open-source Node-RED modules for condition monitoring, OPC-UA, NATS, S7, CIP/EtherNet-IP, and IoT gateway integration.</p>
</div>

## Skills

<div class="skills-section">
  <div class="skill-group">
    <h3 class="skill-group__title">Languages</h3>
    <div class="skill-chips">
      <span class="skill-chip">Python</span>
      <span class="skill-chip">JavaScript</span>
      <span class="skill-chip">TypeScript</span>
      <span class="skill-chip">SQL</span>
      <span class="skill-chip">Go</span>
      <span class="skill-chip">Java</span>
    </div>
  </div>
  <div class="skill-group">
    <h3 class="skill-group__title">Platforms & Tools</h3>
    <div class="skill-chips">
      <span class="skill-chip">Node-RED</span>
      <span class="skill-chip">Docker</span>
      <span class="skill-chip">Kubernetes / K3s</span>
      <span class="skill-chip">Linux / Embedded Linux</span>
      <span class="skill-chip">Terraform</span>
      <span class="skill-chip">Ansible</span>
      <span class="skill-chip">Git</span>
      <span class="skill-chip">GitHub Actions</span>
      <span class="skill-chip">Jenkins</span>
      <span class="skill-chip">Azure</span>
      <span class="skill-chip">GitLab</span>
    </div>
  </div>
  <div class="skill-group">
    <h3 class="skill-group__title">Industrial Protocols</h3>
    <div class="skill-chips">
      <span class="skill-chip chip--proto">OPC-UA</span>
      <span class="skill-chip chip--proto">NATS / JetStream</span>
      <span class="skill-chip chip--proto">MQTT</span>
      <span class="skill-chip chip--proto">Siemens S7</span>
      <span class="skill-chip chip--proto">EtherNet/IP (CIP)</span>
      <span class="skill-chip chip--proto">CAN Bus</span>
      <span class="skill-chip chip--proto">RS485 / Modbus</span>
      <span class="skill-chip chip--proto">Sparkplug B</span>
      <span class="skill-chip chip--proto">REST / gRPC / WebSocket</span>
    </div>
  </div>
  <div class="skill-group">
    <h3 class="skill-group__title">Databases</h3>
    <div class="skill-chips">
      <span class="skill-chip">PostgreSQL</span>
      <span class="skill-chip">InfluxDB</span>
      <span class="skill-chip">TimescaleDB</span>
    </div>
  </div>
  <div class="skill-group">
    <h3 class="skill-group__title">Visualization & Monitoring</h3>
    <div class="skill-chips">
      <span class="skill-chip">Grafana</span>
      <span class="skill-chip">Apache Superset</span>
    </div>
  </div>
</div>

## Architecture

<div class="tech-arch">
  <div class="tech-arch__layer">
    <span class="tech-arch__label">Shop Floor</span>
    <div class="tech-arch__nodes">
      <span class="tech-arch__node node--edge">CAN Bus</span>
      <span class="tech-arch__node node--edge">RS485</span>
      <span class="tech-arch__node node--edge">Siemens S7</span>
      <span class="tech-arch__node node--edge">Allen-Bradley</span>
      <span class="tech-arch__node node--edge">Modbus</span>
      <span class="tech-arch__node node--edge">CompuLab</span>
    </div>
  </div>
  <div class="tech-arch__connector">
    <svg width="40" height="32" viewBox="0 0 40 32"><path d="M20 0v32" stroke="#00c8a5" stroke-width="2" stroke-dasharray="4 4" opacity="0.5"/><path d="M10 22l10 10 10-10" stroke="#00c8a5" stroke-width="2" fill="none" opacity="0.5"/></svg>
  </div>
  <div class="tech-arch__layer">
    <span class="tech-arch__label">Edge Gateway</span>
    <div class="tech-arch__nodes">
      <span class="tech-arch__node node--mid">Node-RED</span>
      <span class="tech-arch__node node--mid">Docker</span>
      <span class="tech-arch__node node--mid">Embedded Linux</span>
      <span class="tech-arch__node node--mid">OPC-UA</span>
      <span class="tech-arch__node node--mid">K3s</span>
    </div>
  </div>
  <div class="tech-arch__connector">
    <svg width="40" height="32" viewBox="0 0 40 32"><path d="M20 0v32" stroke="#00a8dd" stroke-width="2" stroke-dasharray="4 4" opacity="0.5"/><path d="M10 22l10 10 10-10" stroke="#00a8dd" stroke-width="2" fill="none" opacity="0.5"/></svg>
  </div>
  <div class="tech-arch__layer">
    <span class="tech-arch__label">Messaging</span>
    <div class="tech-arch__nodes">
      <span class="tech-arch__node node--msg">NATS</span>
      <span class="tech-arch__node node--msg">JetStream</span>
      <span class="tech-arch__node node--msg">MQTT</span>
    </div>
  </div>
  <div class="tech-arch__connector">
    <svg width="40" height="32" viewBox="0 0 40 32"><path d="M20 0v32" stroke="#0088cc" stroke-width="2" stroke-dasharray="4 4" opacity="0.5"/><path d="M10 22l10 10 10-10" stroke="#0088cc" stroke-width="2" fill="none" opacity="0.5"/></svg>
  </div>
  <div class="tech-arch__layer">
    <span class="tech-arch__label">Cloud & Analytics</span>
    <div class="tech-arch__nodes">
      <span class="tech-arch__node node--cloud">Python</span>
      <span class="tech-arch__node node--cloud">Terraform</span>
      <span class="tech-arch__node node--cloud">Grafana</span>
      <span class="tech-arch__node node--cloud">Superset</span>
      <span class="tech-arch__node node--cloud">CI/CD</span>
      <span class="tech-arch__node node--cloud">i3x</span>
    </div>
  </div>
</div>

## Open Source

I maintain several open-source Node-RED packages for industrial IoT on [npm](https://www.npmjs.com/~blanpa):

{{< npm-stats >}}

### GitHub

{{< github repo="blanpa/node-red-contrib-condition-monitoring" >}}
{{< github repo="blanpa/node-red-contrib-nats-suite" >}}
{{< github repo="blanpa/node-red-contrib-kafka-suite" >}}
{{< github repo="blanpa/node-red-contrib-cip-suite" >}}
{{< github repo="blanpa/node-red-contrib-s7-suite" >}}
{{< github repo="blanpa/node-red-contrib-opcua-suite" >}}
{{< github repo="blanpa/node-red-contrib-clab-interfaces" >}}
{{< github repo="blanpa/node-red-contrib-i3x" >}}

## Experience

<div class="timeline">
  <div class="timeline-item">
    <div class="timeline-marker"></div>
    <div class="timeline-content glass">
      <span class="timeline-date">2024 — present</span>
      <h3>IIoT Software Developer</h3>
      <p>Designing and implementing software solutions for industrial applications — IoT, cloud computing, and data analytics. Building real-time data collection, processing, and analysis systems for industrial devices and systems.</p>
    </div>
  </div>
  <div class="timeline-item">
    <div class="timeline-marker"></div>
    <div class="timeline-content glass">
      <span class="timeline-date">2022 — 2023</span>
      <h3>Process Engineer — Industrial Engineering</h3>
      <p>Analyzed manufacturing processes, optimized efficiency and quality. Led process validation, implemented Lean Manufacturing and Six Sigma methodologies. Collaborated with R&D to transfer new products from development to production.</p>
    </div>
  </div>
  <div class="timeline-item">
    <div class="timeline-marker"></div>
    <div class="timeline-content glass">
      <span class="timeline-date">2017 — 2021</span>
      <h3>B.Eng. Industrial Engineering — Product Engineering</h3>
      <p>Interdisciplinary studies combining engineering, economics, and product development. Focused on manufacturing processes, quality management, and industrial systems.</p>
    </div>
  </div>
  <div class="timeline-item">
    <div class="timeline-marker"></div>
    <div class="timeline-content glass">
      <span class="timeline-date">2012 — 2016</span>
      <h3>Apprenticeship — Electronics Technician for Devices and Systems</h3>
      <p>Vocational training in electronics for devices and systems. Hands-on experience with circuit design, embedded systems, and industrial electronics.</p>
    </div>
  </div>
</div>

## Get in Touch

Interested in working together or have a question? Feel free to reach out.

{{< contact-form id="mjgaaoww" >}}

## Support My Work

<div class="support-cards">
  <a href="https://ko-fi.com/blanpa" target="_blank" class="support-card">
    <span class="support-card__icon">&#9749;</span>
    <span class="support-card__label">Ko-fi</span>
  </a>
  <a href="https://github.com/sponsors/blanpa" target="_blank" class="support-card">
    <span class="support-card__icon">&#10084;</span>
    <span class="support-card__label">GitHub Sponsors</span>
  </a>
  <a href="https://buymeacoffee.com/blanpa" target="_blank" class="support-card">
    <span class="support-card__icon">&#127861;</span>
    <span class="support-card__label">Buy Me a Coffee</span>
  </a>
</div>
