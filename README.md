# PAA5100JE 2-Dimensional Optical Flow Sensor

A quick and dirty Circuitpython port of the [Pimoroni](https://github.com/pimoroni/pmw3901-python) PMW3901/PAA5100EJ sensor library. Its the very first thing Ive done in either Python/CircuitPython so aint to pretty :) In addition to the aforementioned Pimoroni library; this library was also greatly inspired/aided by the Arduino port by [Bitcraze](https://github.com/bitcraze/Bitcraze_PMW3901)

NB: Since completing the library I discoved an official Pico one for Micropython by Pimoroni so that may be a better option for you? This can be found [here](https://github.com/pimoroni/pimoroni-pico) Although it looks like there may be a few more hoops that will need to be jumped through to get things up and going etc (see their readme for more details)

## Prerequisites

Assuming you already have an already complete CircuitPython installation; in order to use this library you will need to install the [Adafruit_Circuit_BusDevice library](https://github.com/adafruit/Adafruit_CircuitPython_BusDevice). This library can be locatated via the previous link or installed via the following pip command:

```
pip3 install adafruit-circuitpython-busdevice
```

## Installing

One you have installed the rquired prerequisites all you need to do is place the file paa5100ej.py in your designated library location and the file code.py in its equivalent. 

### Notes
1. This code has only been tested via Adafruit CircuitPython 7.1.1 on an Adafruit Feather RP2040 with rp2040 via Thonny
2. The code has been targeted for the PAA5100JE only; modification to the init/secret registers may be needed to make it work with the pmw3901
3. The product page for the used PAA5100JE can be found [here](https://shop.pimoroni.com/products/paa5100je-optical-tracking-spi-breakout).
4. Enjoy ;)

