# FoosScore

FoosScore is a program used for a foosball auto scoring system.  The system works in conjunction with FoosOBSPlus and requires a Raspberry Pico W.  The hardware consists of 3 lasers (DAOKI model DR-US-583) and corresponding receivers, two LEDs, two push buttons and 7 resistors (5x10M ohm, 2x330 ohm).

A config.py file is used to designate which pins the LEDs, Push Buttons and Laser Receivers are connected to, as well as the Port number to connect for communication and separate delay times for laser and push button debounce.

A secretsHP.py and secretsHome.py are used to store the wifi connection SSID and PASSWORD.  The connection in secretsHP.py is tried first followed by secretsHome.
