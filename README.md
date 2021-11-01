# xwiimote-cemuhook
Support for cemuhook's UDP protocol for xwiimote devices

Provisional instructions for running:
- Install xwiimote from the official repo; Be sure to copy over the udev X11 rules as per its README to avoid having the wiimote working as a keyboard and messing up everything. You can also `xinput -list` then `xinput disable <ID>` for a temporary fix if you don't want to restart to test it.
- Requirements should have all used libraries
- I included xwiimote python bindings, but I do not know of how portable it is like this. Maybe you'll have to generate it on your own... please help me confirm how this works!
- Run with sudo. It uses root permissions to:
 
  - remove user read permissions from the original `Nintendo Wii*` evdev devices;
  - create a new UDEV device to output the inputs;
  - set LED status, get battery status.

- At the moment, works with only 1 Wiimote without nunchuk (sideways) or 1 Wiimote+Nunchuk. Tested with Dolphin, Citra and Yuzu.
