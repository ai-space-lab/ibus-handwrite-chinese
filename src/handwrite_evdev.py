"""Trackpad event reader for Chinese handwriting input.

Reads from any touchpad/trackpad via evdev, provides stroke/tap/swipe events
to the IBus engine GTK window via GLib idle callbacks.
"""

import sys
import evdev
from evdev import ecodes
import threading
import time
from gi.repository import GLib

_STATE_IDLE = 0
_STATE_TOUCH = 1
_STATE_STROKE = 2
_STATE_SWIPE = 3



class TrackpadReader:
    """Reads multitouch events from a touchpad in a background thread.

    Callbacks (all dispatched on GTK main thread via GLib.idle_add):
      on_stroke_begin(x, y): stroke started at calibrated coords
      on_stroke_point(x, y): finger moved to calibrated coords
      on_stroke_end(points): finger lifted; points = list of (x,y) tuples
      on_tap(x_frac): quick finger tap; x_frac = 0..1 proportional position
      on_swipe_left(): two-finger swipe left (candidate prev page)
      on_swipe_right(): two-finger swipe right (candidate next page)
    """

    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.device = None
        self.thread = None
        self.running = False

        self._cal_x_min = 0
        self._cal_x_max = 1
        self._cal_y_min = 0
        self._cal_y_max = 1
        self._cal_x_range = 1
        self._cal_y_range = 1
        self._move_threshold = 10
        self._swipe_threshold = 40

        self._state = _STATE_IDLE
        self._x = 0
        self._y = 0
        self._stroke = []
        self._finger_down_t = 0.0
        self._touch_x = None
        self._touch_y = None

        self._mt_slots = {}
        self._current_slot = 0
        self._swipe_acc = 0
        self._swipe_centroid = 0
        self._pending = False

    def _map_x(self, raw):
        return (raw - self._cal_x_min) / self._cal_x_range

    def _map_y(self, raw):
        return (raw - self._cal_y_min) / self._cal_y_range

    def _count_active_slots(self):
        return sum(1 for s in self._mt_slots.values() if s['id'] >= 0)

    def _avg_x(self):
        active = [s for s in self._mt_slots.values() if s['id'] >= 0]
        if not active:
            return 0
        return sum(s['x'] for s in active) / len(active)

    def _grab(self):
        if not self.device:
            return
        try:
            self.device.grab()
        except Exception:
            pass

    def _ungrab(self):
        if not self.device:
            return
        try:
            self.device.ungrab()
        except Exception:
            pass

    def start(self):
        devices = [evdev.InputDevice(p) for p in evdev.list_devices()]
        for d in devices:
            caps = d.capabilities(absinfo=False)
            has_touch = ecodes.BTN_TOUCH in caps.get(ecodes.EV_KEY, [])
            abs_codes = caps.get(ecodes.EV_ABS, [])
            has_pos = ecodes.ABS_X in abs_codes or ecodes.ABS_MT_POSITION_X in abs_codes
            if has_touch and has_pos:
                self.device = d
                break
        if not self.device:
            return False

        abs_codes = self.device.capabilities(absinfo=False).get(ecodes.EV_ABS, [])
        if ecodes.ABS_X in abs_codes:
            xi = self.device.absinfo(ecodes.ABS_X)
            yi = self.device.absinfo(ecodes.ABS_Y)
        else:
            xi = self.device.absinfo(ecodes.ABS_MT_POSITION_X)
            yi = self.device.absinfo(ecodes.ABS_MT_POSITION_Y)
        self._cal_x_min = xi.min
        self._cal_x_max = xi.max
        self._cal_y_min = yi.min
        self._cal_y_max = yi.max
        self._cal_x_range = self._cal_x_max - self._cal_x_min
        self._cal_y_range = self._cal_y_max - self._cal_y_min
        self._move_threshold = int(self._cal_x_range * 0.02)
        self._swipe_threshold = int(self._cal_x_range * 0.08)
        self._uses_mt_pos = ecodes.ABS_X not in abs_codes

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self.running = False
        if self.device:
            self.device.close()
            self.device = None

    def _idle(self, fn, *args):
        if self.running:
            GLib.idle_add(fn, *args)

    def _run(self):
        for event in self.device.read_loop():
            if not self.running:
                break

            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    self._x = event.value
                elif event.code == ecodes.ABS_Y:
                    self._y = event.value
                elif event.code == ecodes.ABS_MT_SLOT:
                    self._current_slot = event.value
                elif event.code == ecodes.ABS_MT_TRACKING_ID:
                    if self._current_slot not in self._mt_slots:
                        self._mt_slots[self._current_slot] = {'id': event.value, 'x': 0, 'y': 0}
                    else:
                        self._mt_slots[self._current_slot]['id'] = event.value
                elif event.code == ecodes.ABS_MT_POSITION_X:
                    if self._current_slot in self._mt_slots:
                        self._mt_slots[self._current_slot]['x'] = event.value
                elif event.code == ecodes.ABS_MT_POSITION_Y:
                    if self._current_slot in self._mt_slots:
                        self._mt_slots[self._current_slot]['y'] = event.value

            elif event.type == ecodes.EV_KEY:
                if event.code == ecodes.BTN_TOUCH:
                    if event.value == 1 and self._state == _STATE_IDLE:
                        self._pending = True
                        self._grab()
                    elif event.value == 0:
                        self._ungrab()
                        if self._state == _STATE_STROKE:
                            self._idle(self.callbacks["on_stroke_end"],
                                       list(self._stroke))
                        elif self._state == _STATE_TOUCH:
                            if self._touch_x is not None:
                                elapsed = time.time() - self._finger_down_t
                                if elapsed < 0.25:
                                    x_frac = self._map_x(self._touch_x)
                                    self._idle(self.callbacks["on_tap"], x_frac)
                        self._state = _STATE_IDLE
                        self._stroke = []
                        self._pending = False

            elif event.type == ecodes.EV_SYN and event.code == ecodes.SYN_REPORT:
                active = self._count_active_slots()

                if active >= 2:
                    cx = self._avg_x()
                    if self._state == _STATE_SWIPE:
                        dx = cx - self._swipe_centroid
                        self._swipe_acc += dx
                        if abs(self._swipe_acc) > self._swipe_threshold:
                            if self._swipe_acc > 0:
                                self._idle(self.callbacks.get("on_swipe_right", lambda: None))
                            else:
                                self._idle(self.callbacks.get("on_swipe_left", lambda: None))
                            self._swipe_acc = 0
                    else:
                        self._state = _STATE_SWIPE
                        self._stroke = []
                        self._swipe_acc = 0
                    self._swipe_centroid = cx
                    self._pending = False

                elif active == 0:
                    self._ungrab()
                    if self._state != _STATE_IDLE:
                        self._state = _STATE_IDLE
                        self._stroke = []
                        self._pending = False
                        self._mt_slots = {}

                elif active == 1:
                    if self._uses_mt_pos:
                        rx = ry = 0
                        for s in self._mt_slots.values():
                            if s['id'] >= 0:
                                rx, ry = s['x'], s['y']
                                break
                    else:
                        rx, ry = self._x, self._y
                    fx = self._map_x(rx)
                    fy = self._map_y(ry)

                    if self._state == _STATE_SWIPE:
                        self._state = _STATE_IDLE
                        self._stroke = []
                        self._pending = False
                        self._mt_slots = {}
                        self._ungrab()

                    elif self._state == _STATE_IDLE and self._pending:
                        self._state = _STATE_TOUCH
                        self._stroke = []
                        self._finger_down_t = time.time()
                        self._touch_x = None
                        self._touch_y = None
                        self._pending = False

                    elif self._state == _STATE_TOUCH:
                        if self._touch_x is None:
                            self._touch_x = self._x
                            self._touch_y = self._y
                        else:
                            dx = abs(self._x - self._touch_x)
                            dy = abs(self._y - self._touch_y)
                            if dx > self._move_threshold or dy > self._move_threshold:
                                self._state = _STATE_STROKE
                                self._stroke = [(fx, fy)]
                                self._idle(self.callbacks["on_stroke_begin"], fx, fy)

                    elif self._state == _STATE_STROKE:
                        if self._stroke:
                            lx, ly = self._stroke[-1]
                            if abs(fx - lx) > 0.001 or abs(fy - ly) > 0.001:
                                self._stroke.append((fx, fy))
                                self._idle(self.callbacks["on_stroke_point"], fx, fy)

                else:
                    if self._state != _STATE_IDLE:
                        self._state = _STATE_IDLE
                        self._stroke = []
                    self._pending = False
                    self._mt_slots = {}
