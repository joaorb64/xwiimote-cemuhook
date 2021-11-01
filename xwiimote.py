# This file was automatically generated by SWIG (http://www.swig.org).
# Version 4.0.2
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
if _swig_python_version_info < (2, 7, 0):
    raise RuntimeError("Python 2.7 or later required")

# Import the low-level C/C++ module
if __package__ or "." in __name__:
    from . import _xwiimote
else:
    import _xwiimote

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)


def _swig_setattr_nondynamic_instance_variable(set):
    def set_instance_attr(self, name, value):
        if name == "thisown":
            self.this.own(value)
        elif name == "this":
            set(self, name, value)
        elif hasattr(self, name) and isinstance(getattr(type(self), name), property):
            set(self, name, value)
        else:
            raise AttributeError("You cannot add instance attributes to %s" % self)
    return set_instance_attr


def _swig_setattr_nondynamic_class_variable(set):
    def set_class_attr(cls, name, value):
        if hasattr(cls, name) and not isinstance(getattr(cls, name), property):
            set(cls, name, value)
        else:
            raise AttributeError("You cannot add class attributes to %s" % cls)
    return set_class_attr


def _swig_add_metaclass(metaclass):
    """Class decorator for adding a metaclass to a SWIG wrapped class - a slimmed down version of six.add_metaclass"""
    def wrapper(cls):
        return metaclass(cls.__name__, cls.__bases__, cls.__dict__.copy())
    return wrapper


class _SwigNonDynamicMeta(type):
    """Meta class to enforce nondynamic attributes (no new attributes) for a class"""
    __setattr__ = _swig_setattr_nondynamic_class_variable(type.__setattr__)


class monitor(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, poll, direct):
        _xwiimote.monitor_swiginit(self, _xwiimote.new_monitor(poll, direct))
    __swig_destroy__ = _xwiimote.delete_monitor

    def get_fd(self, blocking):
        return _xwiimote.monitor_get_fd(self, blocking)

    def poll(self):
        return _xwiimote.monitor_poll(self)

# Register monitor in _xwiimote:
_xwiimote.monitor_swigregister(monitor)

class event(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr
    type = property(_xwiimote.event_type_get, _xwiimote.event_type_set)

    def get_abs(self, n):
        return _xwiimote.event_get_abs(self, n)

    def set_abs(self, n, x, y, z):
        return _xwiimote.event_set_abs(self, n, x, y, z)

    def get_key(self):
        return _xwiimote.event_get_key(self)

    def set_key(self, code, state):
        return _xwiimote.event_set_key(self, code, state)

    def get_time(self):
        return _xwiimote.event_get_time(self)

    def set_time(self, tv_sec, tv_usec):
        return _xwiimote.event_set_time(self, tv_sec, tv_usec)

    def ir_is_valid(self, n):
        return _xwiimote.event_ir_is_valid(self, n)

    def __init__(self):
        _xwiimote.event_swiginit(self, _xwiimote.new_event())
    __swig_destroy__ = _xwiimote.delete_event

# Register event in _xwiimote:
_xwiimote.event_swigregister(event)

class iface(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, syspath):
        _xwiimote.iface_swiginit(self, _xwiimote.new_iface(syspath))
    __swig_destroy__ = _xwiimote.delete_iface

    def open(self, ifaces):
        return _xwiimote.iface_open(self, ifaces)

    def close(self, ifaces):
        return _xwiimote.iface_close(self, ifaces)

    def opened(self):
        return _xwiimote.iface_opened(self)

    def get_syspath(self):
        return _xwiimote.iface_get_syspath(self)

    def get_fd(self):
        return _xwiimote.iface_get_fd(self)

    def available(self):
        return _xwiimote.iface_available(self)

    def dispatch(self, ev):
        return _xwiimote.iface_dispatch(self, ev)

    def rumble(self, on):
        return _xwiimote.iface_rumble(self, on)

    def get_led(self, led):
        return _xwiimote.iface_get_led(self, led)

    def set_led(self, led, state):
        return _xwiimote.iface_set_led(self, led, state)

    def get_battery(self):
        return _xwiimote.iface_get_battery(self)

    def get_devtype(self):
        return _xwiimote.iface_get_devtype(self)

    def get_extension(self):
        return _xwiimote.iface_get_extension(self)

    def set_mp_normalization(self, x, y, z, factor):
        return _xwiimote.iface_set_mp_normalization(self, x, y, z, factor)

    def get_mp_normalization(self):
        return _xwiimote.iface_get_mp_normalization(self)

    @staticmethod
    def get_name(iface):
        return _xwiimote.iface_get_name(iface)

# Register iface in _xwiimote:
_xwiimote.iface_swigregister(iface)

def iface_get_name(iface):
    return _xwiimote.iface_get_name(iface)

NAME_CORE = _xwiimote.NAME_CORE
NAME_ACCEL = _xwiimote.NAME_ACCEL
NAME_IR = _xwiimote.NAME_IR
NAME_MOTION_PLUS = _xwiimote.NAME_MOTION_PLUS
NAME_NUNCHUK = _xwiimote.NAME_NUNCHUK
NAME_CLASSIC_CONTROLLER = _xwiimote.NAME_CLASSIC_CONTROLLER
NAME_BALANCE_BOARD = _xwiimote.NAME_BALANCE_BOARD
NAME_PRO_CONTROLLER = _xwiimote.NAME_PRO_CONTROLLER
NAME_DRUMS = _xwiimote.NAME_DRUMS
NAME_GUITAR = _xwiimote.NAME_GUITAR
EVENT_KEY = _xwiimote.EVENT_KEY
EVENT_ACCEL = _xwiimote.EVENT_ACCEL
EVENT_IR = _xwiimote.EVENT_IR
EVENT_BALANCE_BOARD = _xwiimote.EVENT_BALANCE_BOARD
EVENT_MOTION_PLUS = _xwiimote.EVENT_MOTION_PLUS
EVENT_PRO_CONTROLLER_KEY = _xwiimote.EVENT_PRO_CONTROLLER_KEY
EVENT_PRO_CONTROLLER_MOVE = _xwiimote.EVENT_PRO_CONTROLLER_MOVE
EVENT_WATCH = _xwiimote.EVENT_WATCH
EVENT_CLASSIC_CONTROLLER_KEY = _xwiimote.EVENT_CLASSIC_CONTROLLER_KEY
EVENT_CLASSIC_CONTROLLER_MOVE = _xwiimote.EVENT_CLASSIC_CONTROLLER_MOVE
EVENT_NUNCHUK_KEY = _xwiimote.EVENT_NUNCHUK_KEY
EVENT_NUNCHUK_MOVE = _xwiimote.EVENT_NUNCHUK_MOVE
EVENT_DRUMS_KEY = _xwiimote.EVENT_DRUMS_KEY
EVENT_DRUMS_MOVE = _xwiimote.EVENT_DRUMS_MOVE
EVENT_GUITAR_KEY = _xwiimote.EVENT_GUITAR_KEY
EVENT_GUITAR_MOVE = _xwiimote.EVENT_GUITAR_MOVE
EVENT_GONE = _xwiimote.EVENT_GONE
EVENT_NUM = _xwiimote.EVENT_NUM
KEY_LEFT = _xwiimote.KEY_LEFT
KEY_RIGHT = _xwiimote.KEY_RIGHT
KEY_UP = _xwiimote.KEY_UP
KEY_DOWN = _xwiimote.KEY_DOWN
KEY_A = _xwiimote.KEY_A
KEY_B = _xwiimote.KEY_B
KEY_PLUS = _xwiimote.KEY_PLUS
KEY_MINUS = _xwiimote.KEY_MINUS
KEY_HOME = _xwiimote.KEY_HOME
KEY_ONE = _xwiimote.KEY_ONE
KEY_TWO = _xwiimote.KEY_TWO
KEY_X = _xwiimote.KEY_X
KEY_Y = _xwiimote.KEY_Y
KEY_TL = _xwiimote.KEY_TL
KEY_TR = _xwiimote.KEY_TR
KEY_ZL = _xwiimote.KEY_ZL
KEY_ZR = _xwiimote.KEY_ZR
KEY_THUMBL = _xwiimote.KEY_THUMBL
KEY_THUMBR = _xwiimote.KEY_THUMBR
KEY_C = _xwiimote.KEY_C
KEY_Z = _xwiimote.KEY_Z
KEY_STRUM_BAR_UP = _xwiimote.KEY_STRUM_BAR_UP
KEY_STRUM_BAR_DOWN = _xwiimote.KEY_STRUM_BAR_DOWN
KEY_FRET_FAR_UP = _xwiimote.KEY_FRET_FAR_UP
KEY_FRET_UP = _xwiimote.KEY_FRET_UP
KEY_FRET_MID = _xwiimote.KEY_FRET_MID
KEY_FRET_LOW = _xwiimote.KEY_FRET_LOW
KEY_FRET_FAR_LOW = _xwiimote.KEY_FRET_FAR_LOW
KEY_NUM = _xwiimote.KEY_NUM
DRUMS_ABS_PAD = _xwiimote.DRUMS_ABS_PAD
DRUMS_ABS_CYMBAL_LEFT = _xwiimote.DRUMS_ABS_CYMBAL_LEFT
DRUMS_ABS_CYMBAL_RIGHT = _xwiimote.DRUMS_ABS_CYMBAL_RIGHT
DRUMS_ABS_TOM_LEFT = _xwiimote.DRUMS_ABS_TOM_LEFT
DRUMS_ABS_TOM_RIGHT = _xwiimote.DRUMS_ABS_TOM_RIGHT
DRUMS_ABS_TOM_FAR_RIGHT = _xwiimote.DRUMS_ABS_TOM_FAR_RIGHT
DRUMS_ABS_BASS = _xwiimote.DRUMS_ABS_BASS
DRUMS_ABS_HI_HAT = _xwiimote.DRUMS_ABS_HI_HAT
DRUMS_ABS_NUM = _xwiimote.DRUMS_ABS_NUM
IFACE_CORE = _xwiimote.IFACE_CORE
IFACE_ACCEL = _xwiimote.IFACE_ACCEL
IFACE_IR = _xwiimote.IFACE_IR
IFACE_MOTION_PLUS = _xwiimote.IFACE_MOTION_PLUS
IFACE_NUNCHUK = _xwiimote.IFACE_NUNCHUK
IFACE_CLASSIC_CONTROLLER = _xwiimote.IFACE_CLASSIC_CONTROLLER
IFACE_BALANCE_BOARD = _xwiimote.IFACE_BALANCE_BOARD
IFACE_PRO_CONTROLLER = _xwiimote.IFACE_PRO_CONTROLLER
IFACE_DRUMS = _xwiimote.IFACE_DRUMS
IFACE_GUITAR = _xwiimote.IFACE_GUITAR
IFACE_ALL = _xwiimote.IFACE_ALL
IFACE_WRITABLE = _xwiimote.IFACE_WRITABLE
LED1 = _xwiimote.LED1
LED2 = _xwiimote.LED2
LED3 = _xwiimote.LED3
LED4 = _xwiimote.LED4

