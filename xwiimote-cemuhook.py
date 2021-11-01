from __future__ import print_function
import errno
from time import sleep
from select import poll, POLLIN
from inspect import getmembers

from evdev.device import AbsInfo
import xwiimote
from evdev import UInput, InputDevice, categorize, ecodes
import json
import os
import sys
import evdev
import threading
import socket
import struct
from binascii import Error, crc32
import time
import asyncio
import signal
import dbus
import json
import argparse
import subprocess
import os.path
from termcolor import colored
import re

def print_verbose(str):
    global args
    if True: #args.verbose:
        print(colored("Debug: ", "red", attrs=["bold"])+str)

def clamp(my_value, min_value, max_value):
    return max(min(my_value, max_value), min_value)

def abs_to_button(value):
    if value > 0.75:
        value = 255
    else:
        value = 0
    return value

class BaseMessage(bytearray):
    Types = dict(version=bytes([0x00, 0x00, 0x10, 0x00]),
                 ports=bytes([0x01, 0x00, 0x10, 0x00]),
                 data=bytes([0x02, 0x00, 0x10, 0x00]))

    def __init__(self, message_type, data):
        self.extend([
            0x44, 0x53, 0x55, 0x53,  # DSUS,
            0xE9, 0x03,  # protocol version (1001),
            *struct.pack('<H', len(data) + 4),  # data length
            0x00, 0x00, 0x00, 0x00,  # place for CRC32
            0xff, 0xff, 0xff, 0xff,  # server ID
            *BaseMessage.Types[message_type],  # data type
            *data
        ])

        # CRC32
        crc = crc32(self) & 0xffffffff
        self[8:12] = struct.pack('<I', crc)

class Message(BaseMessage):
    def __init__(self, message_type, device, data=[0]):
        index = getattr(device, 'index', device) & 0xff

        # Shared response for ports and data messages
        data = [
            index,  # pad id
            0x02 if getattr(device, 'connected', False) else 0x00,  # state (disconnected/connected)
            0x02,  # model (full gyro)
            getattr(device, 'connection_type', 0x00),  # connection type (n.a./usb/bluetooth)
            *(getattr(device, 'mac', [0x00] * 6)),  # MAC
            getattr(device, 'battery_status', 0x00)  # battery status
        ] + data

        super(Message, self).__init__(message_type, data)

class WiiDevice:
    def __init__(self, server, index, device):
        self.server = server
        self.index = index
        self.device = device

        self._resolve_device()

        self.serial = "00:00:00:00:00:00"

        try:
            with open(f"{self.device.get_syspath()}/uevent", 'r') as uevent_descriptor:
                serial = re.search(r'(?<=HID_UNIQ=)([^\n\r]*)', uevent_descriptor.read())
                if serial:
                    self.serial = serial.group()
        except Exception as e:
            print(e)

        self.mac = [int(part, 16) for part in self.serial.split(":")]

        # Connection type (1 = USB, 2 = Bluetooth)
        self.connection_type = 0x02

        #dev.rumble(True)
        #sleep(1/4.0)
        #dev.rumble(False)
        dev.set_led(1, True)
        dev.set_led(2, False)
        dev.set_led(3, False)
        dev.set_led(4, False)
        self.led_status = [1, 0, 0, 0]

        original_keymap = {
            "left_analog_x": "ABS_X",
            "left_analog_y": "ABS_Y",
            "right_analog_x": "ABS_RX",
            "right_analog_y": "-ABS_RY",
            "dpad_up": "BTN_DPAD_UP",
            "dpad_down": "BTN_DPAD_DOWN",
            "dpad_left": "BTN_DPAD_LEFT",
            "dpad_right": "BTN_DPAD_RIGHT",
            "button_cross": "BTN_SOUTH",
            "button_circle": "BTN_EAST",
            "button_square": "BTN_WEST",
            "button_triangle": "BTN_NORTH",
            "button_l1": "BTN_TL",
            "button_l2": "BTN_TL2",
            "button_l3": "BTN_THUMBL",
            "button_r1": "BTN_TR",
            "button_r2": "BTN_TR2",
            "button_r3": "BTN_THUMBR",
            "button_share": "BTN_SELECT",
            "button_options": "BTN_START",
            "button_ps": "BTN_MODE",
            "accel_x": None,
            "accel_y": None,
            "accel_z": None,
            "motion_x": None,
            "motion_y": None,
            "motion_z": None
        }

        cap = {
            #ecodes.EV_FF:  [ecodes.FF_RUMBLE],
            ecodes.EV_KEY: [ecodes.ecodes[code] for code in self.mapping.values()],
            ecodes.EV_ABS: [
                ecodes.ABS_X,
                ecodes.ABS_Y,
            ]
        }
        self.ui = UInput(cap, name="xwiimote controller 1", version=0x1, phys=self.serial)
        os.chmod(self.ui.device.path, 0o777)

        self.keymap = {evdev.ecodes.ecodes[ecode.lstrip('-')]:[] for ps_key,ecode in original_keymap.items() if ecode is not None}
        for ps_key,ecode in original_keymap.items():
            if ecode is not None:
                prefix = '-' if ecode.startswith('-') else ''
                self.keymap[evdev.ecodes.ecodes[ecode.lstrip('-')]].append(prefix+ps_key)

        self.state = {ps_key.lstrip('-'):0x00 for ps_key in original_keymap.keys()}

        self.state.update(accel_x=0.0, accel_y=0.0, accel_z=0.0,
                          motion_x=0.0, motion_y=0.0, motion_z=0.0)

        self.battery = None

        self.thread = threading.Thread(target=self._worker)
        self.thread.start()
    
    def _resolve_device(self):
        self.extension = self.device.get_extension()
        self.name = "wiimote" + (f" + {self.extension}" if self.extension != "none" else "")

        f = open(f'{self.extension}.json')
        self.mapping = json.load(f)

        self.fd = self.device.get_fd()
        print(self.device)
        print("fd:", self.fd)
        print("opened mask:", self.device.opened())
        self.device.open(self.device.available() | xwiimote.IFACE_WRITABLE)
        print("opened mask:", self.device.opened())

    def _worker(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # Event reading task
        tasks = {asyncio.ensure_future(self._handle_events())}

        # Battery level reading task
        tasks.add(asyncio.ensure_future(self._get_battery_level()))

        # Listen to termination request task
        tasks.add(asyncio.ensure_future(self._wait_for_termination()))

        # Start all tasks, stop at the first completed task
        done, pending = asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED))

        # Cancel all other tasks
        for task in pending:
            task.cancel()

        # Wait for all tasks to finish
        self._loop.run_until_complete(asyncio.wait(pending))
        self._loop.close()

        #self.device.close()
        #self.motion_device.close()
        print(F"Device disconnected: {self.name}")
        self.server.report_clean(self)

    async def _wait_for_termination(self):
        self._terminate_event = asyncio.Event()
        try:
            await self._terminate_event.wait()
        except asyncio.CancelledError:
            return

    def terminate(self):
        self._terminate_event.set()
        self.thread.join()

    async def _handle_events(self):
        print("Input events task started")
        try:
            p = poll()
            p.register(self.fd, POLLIN)
            evt = xwiimote.event()
            n = 0
            while True:
                try:
                    p.poll()
                    self.device.dispatch(evt)

                    #self.state['motion_x'] = 0
                    #self.state['motion_y'] = 0
                    #self.state['motion_z'] = 0

                    if evt.type in [xwiimote.EVENT_KEY, xwiimote.EVENT_NUNCHUK_KEY]:
                        code, state = evt.get_key()
                        evt.set_key(code, 0)
                        print("Key:", code, ", State:", state)
                        print(xwiimote_keymap.get(code))
                        print(ecodes.ecodes[self.mapping.get(xwiimote_keymap.get(code))])
                        print(self.keymap)
                        try:
                            ps_keys = self.keymap[ecodes.ecodes[self.mapping.get(xwiimote_keymap.get(code))]]
                        except Exception as e:
                            print(e)
                            continue

                        for ps_key in ps_keys:
                            self.state[ps_key] = 0xFF if state else 0x00
                        
                        #print(self.state)
                        self.ui.write(ecodes.EV_KEY, ecodes.ecodes[self.mapping.get(xwiimote_keymap.get(code))], state)
                    elif evt.type == xwiimote.EVENT_ACCEL:
                        x, y, z = evt.get_abs(0)
                        if self.extension == "none":
                            self.state['accel_x'] = -(y-13)/100
                            self.state['accel_y'] = (x-17)/100
                            self.state['accel_z'] = (z-10)/100
                        if self.extension == "nunchuk":
                            self.state['accel_x'] = (x-17)/100
                            self.state['accel_y'] = (y-13)/100
                            self.state['accel_z'] = (z-10)/100
                    elif evt.type == xwiimote.EVENT_GONE:
                        print("Gone")
                    elif evt.type == xwiimote.EVENT_WATCH:
                        print("Watch")
                        self._resolve_device()
                        self.server.print_slots()
                    elif evt.type == xwiimote.EVENT_CLASSIC_CONTROLLER_KEY:
                        code, state = evt.get_key()
                        print("Classical controller key:", code, state)
                        tv_sec, tv_usec = evt.get_time()
                        print(tv_sec, tv_usec)
                        evt.set_key(xwiimote.KEY_HOME, 1)
                        code, state = evt.get_key()
                        print("Classical controller key:", code, state)
                        evt.set_time(0, 0)
                        tv_sec, tv_usec = evt.get_time()
                        print(tv_sec, tv_usec)
                    elif evt.type == xwiimote.EVENT_CLASSIC_CONTROLLER_MOVE:
                        x, y, z = evt.get_abs(0)
                        print("Classical controller move 1:", x, y)
                        evt.set_abs(0, 1, 2, 3)
                        x, y, z = evt.get_abs(0)
                        print("Classical controller move 1:", x, y)
                        x, y, z = evt.get_abs(1)
                        print("Classical controller move 2:", x, y)
                    elif evt.type == xwiimote.EVENT_NUNCHUK_MOVE:
                        # Analog stick
                        x, y, z = evt.get_abs(0)
                        try:
                            ps_keys_x = self.keymap[ecodes.ecodes["ABS_X"]]
                            ps_keys_y = self.keymap[ecodes.ecodes["ABS_Y"]]
                        except Exception as e:
                            print(e)
                            continue

                        x-=10

                        if(abs(x) < 20): x = 0
                        if(abs(y) < 20): y = 0

                        for ps_key in ps_keys_x:
                            negate = ps_key.startswith('-')
                            self.ui.write(ecodes.EV_ABS, ecodes.ecodes["ABS_X"], int(clamp(x / 90, -1, 1) * 32767))
                            self.state[ps_key.lstrip('-')] = clamp(x / 90, -1, 1) * (-1 if negate else 1)
                        
                        for ps_key in ps_keys_y:
                            negate = ps_key.startswith('-')
                            self.ui.write(ecodes.EV_ABS, ecodes.ecodes["ABS_Y"], int(clamp(y / 90, -1, 1) * 32767 * -1))
                            self.state[ps_key.lstrip('-')] = clamp(y / 90, -1, 1) * (-1 if negate else 1)
                        
                        # Accelerometer
                        x, y, z = evt.get_abs(1)
                        #print((x+25)/200, y/200, z/200)
                    elif evt.type == xwiimote.EVENT_MOTION_PLUS:
                        x, y, z = evt.get_abs(0)
                        if self.extension == "none":
                            self.state['motion_x'] = (x+1000)/200
                            self.state['motion_y'] = (z+6900)/200
                            self.state['motion_z'] = -(y+10145)/200
                        if self.extension == "nunchuk":
                            self.state['motion_x'] = (x+1000)/200
                            self.state['motion_y'] = (y+10145)/200
                            self.state['motion_z'] = (z+6900)/200
                    elif evt.type == xwiimote.EVENT_IR:
                        for i in [0, 1, 2, 3]:
                            if evt.ir_is_valid(i):
                                x, y, z = evt.get_abs(i)
                                print("IR", i, x, y, z)
                    self.ui.syn()
                    self.server.report(self)
                    await asyncio.sleep(0)
                except IOError as e:
                    print(e)
                    if e.errno != errno.EAGAIN:
                        print("Bad")
        except Exception as e:
            print(e)
            print_verbose("Input events task ended")
    
    async def _get_battery_level(self):
        print("battery")
        print_verbose("Battery level reading thread started")
        try:
            while self.device != None:
                battery_percent = self.device.get_battery()
                print(battery_percent)
                if battery_percent != self.battery:
                    print_verbose("Battery level changed")
                    self.battery = battery_percent
                    self.server.print_slots()
                await asyncio.sleep(30)
        except (asyncio.CancelledError, Exception) as e:
            print(e)
            print_verbose("Battery level reading task ended")
            self.battery = None

    @property
    def connected(self):
        try:
            return self._loop.is_running()
        except AttributeError:
            return self.thread.is_alive()

    @property
    def battery_status(self):
        if self.battery is None:
            return 0x00
        elif self.battery < 10:
            return 0x01
        elif self.battery < 25:
            return 0x02
        elif self.battery < 75:
            return 0x03
        elif self.battery < 90:
            return 0x04
        else:
            return 0x05

    @property
    def report(self):
        state = self.state.copy()
        state["timestamp"] = time.time_ns() // 1000
        return state

class UDPServer:
    MAX_PADS = 4
    TIMEOUT = 5

    def __init__(self, host='', port=26760):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        print_verbose("Started UDP server with ip "+str(host)+", port "+str(port))
        self.counter = 0
        self.clients = dict()
        self.slots = [None] * UDPServer.MAX_PADS
        self.stop_event = threading.Event()

    def _res_ports(self, index):
        device = self.slots[index]
        if device is None:
            device = index

        return Message('ports', device)

    def _req_ports(self, message, address):
        requests_count = struct.unpack("<I", message[20:24])[0]

        for slot_id in message[24 : 24 + requests_count]:
            try:
                self.sock.sendto(self._res_ports(slot_id), address)
            except IndexError:
                print('[udp] Received malformed ports request')
                return

    def _req_data(self, message, address):
        reg_id = message[20]
        slot_id = message[21]
        # reg_mac = message[22:28]

        if address not in self.clients:
            print(F'[udp] Client connected: {address[0]}:{address[1]}')
            self.clients[address] = dict(controllers=[False] * 4)

        self.clients[address]["timestamp"] = time.time()

        # Register all slots
        if reg_id == 0:
            self.clients[address]["controllers"] = [True] * 4

        # Register a single slot
        elif reg_id == 1:
            self.clients[address]["controllers"][slot_id] = True

        # MAC-based registration (TODO)
        elif reg_id == 2:
            print("[udp] Ignored request for MAC-based registration (unimplemented)")
        else:
            print(F"[udp] Unknown data request type: {reg_id}")
    
    def _res_data(self, controller_index, message):
        now = time.time()
        for address, data in self.clients.copy().items():
            if now - data["timestamp"] > UDPServer.TIMEOUT:
                print(F'[udp] Client disconnected: {address[0]}:{address[1]}')
                del self.clients[address]

            elif data["controllers"][controller_index]:
                self.sock.sendto(message, address)
    
    def _handle_request(self, request):
        message, address = request

        # Ignore empty messages (sent by sock_stop)
        if not message:
            return

        # client_id = message[12:16]
        msg_type = message[16:20]

        if msg_type == Message.Types['version']:
            return
        elif msg_type == Message.Types['ports']:
            self._req_ports(message, address)
        elif msg_type == Message.Types['data']:
            self._req_data(message, address)
        else:
            print('[udp] Unknown message type: ' + str(msg_type))

    def report(self, device):
        device_state = device.report

        # Acceleration in g's
        sensors = [
            device_state.get('accel_x'),
            -device_state.get('accel_z'),
            -device_state.get('accel_y'),
        ]

        # Gyro rotation in deg/s
        sensors.extend([
            -device_state.get('motion_z'),
            -device_state.get('motion_x'),
            -device_state.get('motion_y')
        ])

        buttons1 = 0x00
        buttons1 |= int(abs_to_button(device_state.get("button_share", 0x00))/255)
        buttons1 |= int(abs_to_button(device_state.get("button_l3", 0x00))/255) << 1
        buttons1 |= int(abs_to_button(device_state.get("button_r3", 0x00))/255) << 2
        buttons1 |= int(abs_to_button(device_state.get("button_options", 0x00))/255) << 3
        buttons1 |= int(abs_to_button(device_state.get("dpad_up", 0x00))/255) << 4
        buttons1 |= int(abs_to_button(device_state.get("dpad_right", 0x00))/255) << 5
        buttons1 |= int(abs_to_button(device_state.get("dpad_down", 0x00))/255) << 6
        buttons1 |= int(abs_to_button(device_state.get("dpad_left", 0x00))/255) << 7

        buttons2 = 0x00
        buttons2 |= int(abs_to_button(device_state.get("button_l2", 0x00))/255)
        buttons2 |= int(abs_to_button(device_state.get("button_r2", 0x00))/255) << 1
        buttons2 |= int(abs_to_button(device_state.get("button_l1", 0x00))/255) << 2
        buttons2 |= int(abs_to_button(device_state.get("button_r1", 0x00))/255) << 3
        buttons2 |= int(abs_to_button(device_state.get("button_triangle", 0x00))/255) << 4
        buttons2 |= int(abs_to_button(device_state.get("button_circle", 0x00))/255) << 5
        buttons2 |= int(abs_to_button(device_state.get("button_cross", 0x00))/255) << 6
        buttons2 |= int(abs_to_button(device_state.get("button_square", 0x00))/255) << 7

        data = [
            0x01,  # is active (true)
            *struct.pack('<I', self.counter),
            buttons1,
            buttons2,
            abs_to_button(device_state.get("button_ps", 0x00)),  # PS
            0x00,  # Touch

            int(device_state.get("left_analog_x", 0x00) * 127) + 128,  # position left x
            int(device_state.get("left_analog_y", 0x00) * 127) + 128,  # position left y
            int(device_state.get("right_analog_x", 0x00) * 127) + 128,  # position right x
            int(device_state.get("right_analog_y", 0x00) * 127) + 128,  # position right y

            abs_to_button(device_state.get("dpad_left", 0x00)),  # dpad left
            abs_to_button(device_state.get("dpad_down", 0x00)),  # dpad down
            abs_to_button(device_state.get("dpad_right", 0x00)),  # dpad right
            abs_to_button(device_state.get("dpad_up", 0x00)),  # dpad up

            abs_to_button(device_state.get("button_square", 0x00)),  # square
            abs_to_button(device_state.get("button_cross", 0x00)),  # cross
            abs_to_button(device_state.get("button_circle", 0x00)),  # circle
            abs_to_button(device_state.get("button_triangle", 0x00)),  # triange

            abs_to_button(device_state.get("button_r1", 0x00)),  # r1
            abs_to_button(device_state.get("button_l1", 0x00)),  # l1

            abs_to_button(device_state.get("button_r2", 0x00)),  # r2
            abs_to_button(device_state.get("button_l2", 0x00)),  # l2

            0x00,  # track pad first is active (false)
            0x00,  # track pad first id

            0x00, 0x00,  # trackpad first x
            0x00, 0x00,  # trackpad first y

            0x00,  # track pad second is active (false)
            0x00,  # track pad second id

            0x00, 0x00,  # trackpad second x
            0x00, 0x00,  # trackpad second y

            *struct.pack('<Q', device_state.get("timestamp")),  # Motion data timestamp
            *struct.pack('<ffffff', *sensors)  # Accelerometer and Gyroscope data
        ]

        self.counter += 1

        self._res_data(device.index, Message('data', device, data))
    
    def report_clean(self, device):
        self._res_data(device.index, Message('data', device))
    
    def add_device(self, device):
        # Find an empty slot for the new device
        for i, slot in enumerate(self.slots):
            if not slot:
                self.slots[i] = WiiDevice(self, i, device)
                return i

        # All four slots have been allocated
        return UDPServer.MAX_PADS

    def add_devices(self, device, motion_devices, motion_only=False):
        i = -1

        # Any motion device except the first one should have only motion reading task to avoid 'device busy' errors
        for i, motion_device in enumerate(motion_devices):
            if self.add_device(device, motion_device, motion_only if i == 0 else True) == UDPServer.MAX_PADS:
                return i

        return i + 1

    def print_slots(self):
        print(colored(F" {self.sock.getsockname()} ".center(55, "="), attrs=["bold"]))

        print (colored("{:<26} {:<12} {:<12} {:<12}", attrs=["bold"])
            .format("Device", "LED status", "Battery Lv", "MAC Addr"))

        for i, slot in enumerate(self.slots):
            if not slot:
                print(str(i+1)+" ❎ ")
            else:
                device = str(i+1)+" "
                device += slot.name

                leds = ""
                for led in slot.led_status:
                    leds += "■ " if led else "□ "

                if not leds:
                    leds = "?"

                if slot.battery:
                    battery = F"{str(slot.battery)} {chr(ord('▁') + int(slot.battery * 7 / 100))}"
                else:
                    battery = "❌"
                
                mac = slot.serial

                # print device after calculating alignment because the gamepad symbols cause alignment errors
                print(F'{"":<26} {colored(F"{leds:<12}", "green")} {colored(F"{battery:<12}", "green")} {mac:<12}\r{device}')

        print(colored("".center(55, "="), attrs=["bold"]))

    def connected_devices(self):
        return sum(d is not None for d in self.slots)

    def _worker(self):
        while not self.stop_event.is_set():
            self._handle_request(self.sock.recvfrom(1024))
        self.sock.close()

    def start(self):
        self.thread = threading.Thread(target=self._worker)
        self.thread.start()

    def stop(self):
        for slot in self.slots:
            if slot:
                slot.terminate()

        self.stop_event.set()

        # Send message to sock to trigger sock.recvfrom
        sock_stop = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_stop.sendto(b'', self.sock.getsockname())
        sock_stop.close()

        self.thread.join()


# display a constant
print("=== " + xwiimote.NAME_CORE + " ===")

# list wiimotes and remember the first one
try:
    mon = xwiimote.monitor(True, True)
    print("mon fd", mon.get_fd(False))
    ent = mon.poll()
    firstwiimote = ent
    while ent is not None:
        print("Found device: " + ent)
        ent = mon.poll()
except SystemError as e:
    print("ooops, cannot create monitor (", e, ")")

# create a new iface
try:
    dev = xwiimote.iface(firstwiimote)
except IOError as e:
    print("ooops,", e)
    exit(1)

# display some information and open the iface
# try:
#     print("syspath:" + dev.get_syspath())
#     fd = dev.get_fd()
#     print("fd:", fd)
#     print("opened mask:", dev.opened())
#     dev.open(dev.available() | xwiimote.IFACE_WRITABLE)
#     print("opened mask:", dev.opened())

#     #dev.rumble(True)
#     #sleep(1/4.0)
#     #dev.rumble(False)
#     dev.set_led(1, dev.get_led(2))
#     dev.set_led(2, dev.get_led(3))
#     dev.set_led(3, dev.get_led(4))
#     dev.set_led(4, dev.get_led(4) == False)

# except SystemError as e:
#     print("ooops", e)
#     exit(1)

# dev.set_mp_normalization(10, 20, 30, 40)
x, y, z, factor = dev.get_mp_normalization()
print("mp", x, y, z, factor)

xwiimote_keymap = {
    0: "KEY_LEFT",
    1: "KEY_RIGHT",
    2: "KEY_UP",
    3: "KEY_DOWN",
    4: "KEY_A",
    5: "KEY_B",
    6: "KEY_PLUS",
    7: "KEY_MINUS",
    8: "KEY_HOME",
    9: "KEY_ONE",
    10: "KEY_TWO",
    11: "KEY_X",
    12: "KEY_Y",
    13: "KEY_TL",
    14: "KEY_TR",
    15: "KEY_ZL",
    16: "KEY_ZR",
    17: "KEY_THUMBL",
    18: "KEY_THUMBR",
    19: "KEY_C",
    20: "KEY_Z",
}

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

for device in devices:
    print(device.path, device.name, device.phys, device.uniq)
    if "Nintendo Wii" in device.name:
        os.chmod(device.path, 0o700)

server = UDPServer("127.0.0.1", 26760)
server.start()
#dev = WiiDevice(server, 0, ent)
server.add_device(dev)
sleep(5)
server.print_slots()

while True:
    sleep(5)