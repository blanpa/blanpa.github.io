---
name: Table soccer
tools: [Linux, Python, University Project, Raspberry Pi, Revolution Pi]
image: https://raw.githubusercontent.com/blanpa/blanpa.github.io/main/_projects/media/(2)%20University%20Project%20table%20soccer/1.png

description: University Project
external_url: 
---

# Description

**Requirements**

- Investigation Raspberry PI alternative to Arduino
- Control Raspberry PI with CAN interface
- Realization of display and implementation of electronic scoreboard
- Implementation of a ball return mechanism
- Implementation of stadium construction
- Documentation sufficient for operation and duplication of the exhibition model
- Finished assembly and handover to Dunkermotoren

Using linear motors and the BGA 22 dGo from Dunkermotoren,  controlled by Sony PlayStation controllers.

The initial implementation of the controller was implemented using multiple Arduino microcontrollers communicating with each other. However, this control did not work properly for a long time. Due to the limited functionality of the Arduino, the control was ported to a Raspberry Pi based system. This allows a more reliable control and implementation of other important requirements.

[Revolution Pi](https://revolutionpi.com/) is an open, modular and inexpensive industrial PC based on the well-known Raspberry Pi. Housed in a slim DIN-rail housing, the three available base modules can be seamlessly expanded by a variety of suitable I/O modules and fieldbus gateways. The 24V powered modules are connected via an overhead connector in seconds and can be easily configured via a graphical configuration tool.

**Ball Return Mechanism**

A U-shaped tube construction was designed to create a ball return. If a goal is scored, the ball rolls to a fixed point. When the ball reaches this point, a light barrier triggers a signal and the ball is brought back into play via the ball boy. Many of the components were manufactured via 3D printing.

The score of the game is counted via respective light barriers. The display of the score is provided via a display for both players.


{% include elements/video.html id="wgXZfWWLlIM" %}
