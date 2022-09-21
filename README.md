# FoosScore

FoosScore is a program used for a foosball auto scoring system.  The system works in conjunction with FoosOBSPlus and requires a Raspberry Pico W.  The hardware consists of 3 lasers and corresponding receivers, two LEDs and 5 resistors (3x10M ohm, 2x330 ohm).

A config.py file is used to designate which pins the LEDs and Laser Receivers are connected to, as well as the Port number to connect for communication and the delay time to wait after a laser gets triggered before it is active again.

A secretsHP.py and secretsHome.py are used to store the wifi connection SSID and PASSWORD.  The connection in secretsHP.py is tried first followed by secretsHome.
