---
name: Automatic conveyor belt
tools: [Linux, Raspberry Pi, Python, SPS, University Project, Machine Learning]
image: https://raw.githubusercontent.com/blanpa/blanpa.github.io/main/_projects/media/(1)%20University%20project%20conveyor%20belt/1.png

description: University Project
external_url: 
---
# Description
The conveyor belt is at the center of the system. The sensors and pneumatic cylinders are attached to the side of one of the aluminum profiles. In the direction of travel, the capacitive sensor is mounted first, followed by the inductive sensor. The color sensor is mounted next, followed by the Rasp-berry Pi camera. All sensors are to remain permanently mounted on the conveyor belt in order to keep the conversion work to a minimum. The pneumatic cylinders are equipped with a pusher that allows the sorted parts to fall off to the side while the conveyor belt is running.

**Control and electronics**

o control all the sensors and actuators we need a controller. We have decided to use the Pixtend.

[https://www.pixtend.de/pixtend-v2/](https://www.pixtend.de/pixtend-v2/)

The PiXtend is a programmable logic controller (PLC) based on the Raspberry Pi. Due to the wide range of digital and analog inputs & outputs, it allows the connection of a wide variety of sensors and actuators from the industry. It also has various standard serial interfaces (RS232, RS485, CAN, Ethernet, WiFi and Bluetooth).

So you can really do a lot with it.

## Test setup 1

In setup 1, we use the capacitive and the inductive sensor, as well as the two pneumatic cylinders. We always use the capacitive sensor as the starting point.

The inductive sensor distinguishes between metal and non-metal parts, for metal parts it sends a HIGH signal.

In the program we have defined it so that non-metal parts are ejected with the first pneumatic slider and metal parts are ejected with the 2nd pneumatic slider.

{% include elements/video.html id="zK1IAr4HmpM" %}

## Test setup 2

In setup 2, we use the capacitive as well as the color sensor, in which several different color classes can be trained. The color sensor has several outputs, one output per color class, i.e. a total of 4 outputs that can be easily read out.

We have then trained with the color sensor 4 color classes once the conveyor belt (black), green 1, blue 2, red 3.

In the program we have defined it in such a way that green at the 1., blue at the 2. pneumatic cylinder, red drive completely through.

In the next experiment it will be a bit tricky. In order to distinguish between different objects using the webcam, we need a neural network that can classify different objects.

{% include elements/video.html id="LOC4O2OxLF8" %}


## Test setup 3

The object is detected by the capacitive sensor and stops at the camera. Then a picture is taken and thrown into the trained model and a prediction for one of the defined classes is obtained.

We have defined this in the program so that:

- Class 0 -> conveyor belt: as reference
- Class1 ->Horseshoe: Sorted on the 1st pneumatic cylinder
- Class 2 -> Cross: Sorted on 2nd pneumatic cylinder
- Class 3: ->Cylinder: Moves through

As you can see very well now that the ejection with the ejector does not work so well here, which can be improved in the next semester.

{% include elements/video.html id="LAhTtD7sYsg" %}
