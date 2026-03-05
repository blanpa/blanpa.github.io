---
title: "From Process Engineer to IIoT Developer — My Career Switch"
tags: [career, iiot]
description: "How my Industrial Engineering background became my biggest advantage in IIoT software development."
date: 2026-05-16
series: ["IIoT"]
---

Two years ago, I was a process engineer in a manufacturing plant. I wore steel-toed boots, carried a clipboard, and spent my days optimizing cycle times and reducing scrap rates. Today, I build Node-RED modules for industrial IoT, maintain open-source packages, and write code that connects factory machines to dashboards and analytics systems.

This is the story of how I switched — what pushed me to leave, what I had to learn, what transferred surprisingly well, and what I'd tell someone considering the same move.

---

## Why I Left Process Engineering

It wasn't dissatisfaction with the work. Manufacturing is fascinating — every day brings a different problem, and improvements have tangible, measurable impact. What frustrated me was the tooling.

### The Spreadsheet Problem

Every process improvement project I ran followed the same pattern:

1. **Data collection** — walk to the machine, write down values, enter them into Excel
2. **Analysis** — pivot tables, maybe a histogram
3. **Presentation** — copy charts into PowerPoint
4. **Implementation** — hope the operator follows the new SOP
5. **Monitoring** — walk back to the machine in two weeks, check if things improved

The data was there — machines had PLCs, sensors were measuring everything — but getting that data out of the machine and into something useful was either impossible or required a six-figure SCADA investment.

```
My frustration loop:

    ┌──────────────────────┐
    │ See a problem on the │
    │ production line       │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │ Realize the data     │
    │ exists in the PLC    │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │ Ask IT for access    │
    │ to the data          │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │ Get told it requires │
    │ a vendor project     │
    │ ($50k, 6 months)     │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │ Go back to clipboard │
    │ and Excel            │
    └──────────────────────┘
```

### The Turning Point

One Friday evening, I stumbled on a YouTube video about Node-RED. Someone had connected an OPC-UA server to an MQTT broker and was visualizing PLC data on a web dashboard — all with drag-and-drop visual programming. No six-figure vendor project. No six-month timeline. A Raspberry Pi and a weekend.

I installed Node-RED that night. By Monday morning, I had a prototype that read temperature values from our test lab's Modbus sensor and displayed them on my phone. It was ugly, it was fragile, but it *worked* — and it took me 8 hours instead of 8 months.

That was the moment I realized: the bottleneck in manufacturing isn't hardware or data. It's the software layer between the machine and the human. And I wanted to be the one who builds that layer.

---

## What Transferred from Industrial Engineering

When I started learning software development, I expected my engineering background to be irrelevant. I was wrong. It turned out to be my biggest advantage.

### 1. Understanding the Domain

Most software developers have never set foot on a factory floor. They don't know what OEE is. They've never seen a PLC. They don't understand why an operator won't use a tool that requires more than three clicks.

I knew all of this. When I started building IIoT solutions, I didn't have to *guess* what users needed — I had *been* the user.

```
What a typical developer builds:
  ┌───────────────────────────────────────┐
  │  Beautiful dashboard with 47 charts,  │
  │  3 dropdown menus, a sidebar,         │
  │  and a settings page                  │
  │                                       │
  │  Operator: "I can't find the          │
  │  machine status"                      │
  └───────────────────────────────────────┘

What the operator actually needs:
  ┌───────────────────────────────────────┐
  │                                       │
  │         🟢  RUNNING  —  2,450 RPM     │
  │                                       │
  │       Shift total: 847 / 1,000        │
  │                                       │
  └───────────────────────────────────────┘
```

### 2. Lean / Six Sigma Thinking

Process engineering taught me to think in terms of value streams, waste elimination, and root cause analysis. This transfers directly to software:

| Manufacturing Concept | Software Equivalent |
|----------------------|---------------------|
| Value Stream Mapping | Data flow architecture |
| 5 Whys | Debugging methodology |
| Poka-yoke (mistake-proofing) | Input validation, type safety |
| Kaizen (continuous improvement) | Iterative development, CI/CD |
| Cycle time reduction | Performance optimization |
| Standard Work | Documentation, coding standards |
| PDCA (Plan-Do-Check-Act) | Agile sprints |
| Gemba (go to the source) | User research, talking to operators |

### 3. Knowing What Matters

In manufacturing, you learn very quickly that not all data is equally important. Machine vibration trending upward over weeks? Critical. Ambient humidity in a climate-controlled room? Noise.

This helped me build better IIoT systems. I never built a "collect everything" platform. I always started with: *What decision does this data support? What action will someone take based on this number?*

### 4. Communication with Plant People

I speak both languages. I can explain a REST API to a controls engineer, and I can explain OPC-UA to a web developer. In IIoT, this bridging skill is rare and incredibly valuable.

---

## What I Had to Learn from Scratch

Let's be honest — the learning curve was steep. Here's what was new territory for me:

### JavaScript

My first programming language beyond Excel VBA. I started with basic Node.js tutorials, then moved to Node-RED's function nodes as a stepping stone.

My learning path:

```
Month 1-2: JavaScript basics (freeCodeCamp)
  - Variables, functions, loops, arrays
  - Callbacks, promises, async/await
  - JSON (this is everywhere in IIoT)

Month 3-4: Node.js
  - File system, HTTP, streams
  - npm, package.json, modules
  - Express.js (simple REST APIs)

Month 5-6: Node-RED development
  - Writing custom nodes
  - Understanding the Node-RED runtime
  - Publishing to npm
```

### Python

For data engineering and machine learning. I learned it through DataTalks.Club's ZoomCamps — free, project-based courses that taught me more than any Udemy course.

```
DataTalks.Club ZoomCamps I completed:

┌────────────────────────────────┬──────────────────────────────────────┐
│ Data Engineering ZoomCamp      │ Docker, SQL, dbt, Spark, Kafka,      │
│                                │ Terraform, GCP                       │
├────────────────────────────────┼──────────────────────────────────────┤
│ ML ZoomCamp                    │ scikit-learn, XGBoost, deep learning,│
│                                │ model deployment                     │
├────────────────────────────────┼──────────────────────────────────────┤
│ MLOps ZoomCamp                 │ MLflow, Prefect, model monitoring,   │
│                                │ experiment tracking                  │
└────────────────────────────────┴──────────────────────────────────────┘

All free. All project-based. All excellent.
```

### Git & Version Control

Coming from "Final_Report_v3_FINAL_REVISED_v2.docx" culture, Git was a revelation. Understanding branches, commits, and merge requests took a few weeks, but it changed how I think about all work, not just code.

### Docker & Containers

This was the biggest force multiplier. Instead of "works on my machine," I could package an entire Node-RED setup — with all dependencies, custom nodes, and configuration — into a Docker image that runs anywhere.

```bash
# Before Docker:
# "To run my tool, install Node.js 18, then npm install these 15 packages,
#  then configure settings.js, then..."

# After Docker:
docker compose up -d
# Done.
```

### Cloud Infrastructure

AWS, Azure, and GCP basics. Not deep expertise — enough to deploy a container, set up an IoT hub, and manage credentials. For manufacturing, most infrastructure is still on-premise, but the cloud skills helped me understand modern deployment patterns.

---

## The Learning Strategy That Worked

I tried a lot of things. Udemy courses, YouTube tutorials, books, bootcamp-style programs. Here's what actually moved the needle:

### 1. Solve a Real Problem First

Don't learn Docker in the abstract. Have a problem — "I need to deploy Node-RED with my custom nodes to three different machines" — and then learn Docker to solve it.

Every meaningful skill I acquired was driven by a concrete need. I learned OPC-UA because I needed to read data from a Siemens PLC. I learned MQTT because I needed pub/sub for sensor data. I learned GitHub Actions because I was tired of deploying manually.

### 2. Build Open Source

Publishing npm packages forced me to write proper code. When strangers on the internet use your module, you learn very quickly about:

- Documentation (because people read it)
- Error handling (because people hit edge cases you never imagined)
- Testing (because you can't manually test every PR)
- API design (because breaking changes make people angry)
- Semantic versioning (because people depend on your version numbers)

My open-source packages became my portfolio, my teacher, and my proof of competence — all in one.

### 3. DataTalks.Club ZoomCamps

I cannot overstate how valuable these were. Each ZoomCamp is a 2-4 month program with weekly lessons, homework projects, and a capstone project. They're free, entirely online, and taught by practitioners.

For someone coming from engineering into data/software, this is the best learning path I've found. The projects give you real portfolio pieces, and the community is incredibly supportive.

### 4. Read Other People's Code

I spent hours reading the source code of popular Node-RED contrib packages. How does `node-red-contrib-opcua` handle connections? How does `node-red-dashboard` manage state? Reading code teaches you patterns that tutorials never cover.

---

## Key Lessons

### Domain Knowledge is Underrated

In tech, there's a bias toward pure engineering skill. But in IIoT, knowing the difference between a VFD and a servo matters more than knowing the difference between `map` and `reduce`. Manufacturing domain knowledge takes years to build. JavaScript takes months.

```
The IIoT developer skill stack:

                    ┌────────────────┐
                    │ Domain Expertise│  ← hardest to learn,
                    │ Manufacturing, │     takes years
                    │ processes, OT  │
                    ├────────────────┤
                    │ Industrial     │  ← moderate learning
                    │ Protocols      │     curve
                    │ OPC-UA, MQTT,  │
                    │ Modbus, CAN    │
                    ├────────────────┤
                    │ Software Dev   │  ← learnable in months
                    │ JS, Python,    │     with dedication
                    │ Docker, Git    │
                    └────────────────┘

Most developers have the bottom layer.
Few have the top.
Having all three is rare.
```

### Start with Solving Real Problems

Don't build a "platform." Build a solution to one specific problem. "I need to see the temperature of oven 3 on my phone" is a better starting point than "I'm going to build an IIoT middleware layer." The platform emerges from the solutions.

### Open Source as Portfolio

When I applied for my first IIoT developer role, I didn't have a CS degree. I didn't have three years of professional development experience. But I had five npm packages with real users, real tests, and real documentation. That mattered more than any certificate.

### Imposter Syndrome is Normal

For the first six months, I felt like a fraud. I was a process engineer pretending to be a developer. The code I wrote was ugly. My Git history was embarrassing. I had to Google basic syntax constantly.

Here's what I wish I'd known: every developer Googles basic syntax. Every developer writes ugly code at first. The difference between a beginner and an experienced developer isn't that they know everything — it's that they know how to find answers faster.

### The Factory Floor is Your Superpower

Every time I visit a customer's plant, I understand things that pure software developers miss. I notice that the operator can't use a touchscreen with gloves on. I know that the WiFi drops out near the welding robots. I understand that a 30-second data delay isn't acceptable when you're running a batch process.

This isn't soft skill trivia. It's the difference between building software that gets used and software that gets uninstalled.

---

## Advice for Engineers Considering the Switch

### Do You Even Need to Fully Switch?

Maybe you don't need to become a full-time developer. A process engineer who can build Node-RED dashboards and connect PLCs is incredibly valuable — maybe more valuable than a pure developer. Consider hybrid roles: "automation engineer with software skills" or "IIoT specialist."

### Practical Steps

1. **Install Node-RED today.** Spend one weekend building something — anything. Read a sensor, visualize data, send an alert. Prove to yourself that you can.

2. **Learn JavaScript fundamentals.** Not React, not Angular — plain JavaScript. You'll need it for Node-RED function nodes and custom node development. freeCodeCamp's curriculum is excellent and free.

3. **Learn Git.** Version control is non-negotiable. It takes two weeks to get comfortable with the basics (`add`, `commit`, `push`, `pull`, `branch`, `merge`).

4. **Join DataTalks.Club.** Enroll in their next ZoomCamp. The Data Engineering ZoomCamp is the best starting point — it covers Docker, SQL, Python, and cloud basics in a structured, project-based format.

5. **Build something open-source.** Write a Node-RED node for a protocol you understand. Publish it on npm. It doesn't have to be perfect — it has to exist.

6. **Talk to developers.** Find the software team at your company. Buy them coffee. Ask what they're working on. Offer your domain expertise in exchange for code reviews.

7. **Don't quit your day job (yet).** Build your skills on the side. When your side projects are more interesting than your day job and you have a portfolio to prove it, then consider the switch.

---

## Two Years Later

I still wear steel-toed boots sometimes — when I visit customer plants to understand their processes before writing code. The clipboard has been replaced by a laptop, but the mindset is the same: observe, measure, improve.

The best part? The problems are the same problems I cared about as a process engineer — reducing waste, improving uptime, giving operators the information they need. I'm just solving them with different tools now.

If you're an engineer sitting in a plant, frustrated by spreadsheets and manual data collection, staring at a PLC that you know holds valuable data — you're closer to becoming an IIoT developer than you think. The domain knowledge is the hard part. The code is just a tool. And tools can be learned.
