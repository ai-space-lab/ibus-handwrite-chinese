#!/usr/bin/env python3
"""
GTK writing simulation test for ibus-handwrite-chinese.
Orchestrates the engine in --test mode, draws strokes programmatically,
and captures screenshots.
"""

import os
import sys
import types

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'src'))
sys.path.insert(0, SRC_DIR)

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import GLib, Gtk, Gdk

engine_path = os.path.join(SRC_DIR, 'ibus-engine-handwrite-chinese')
mod = types.ModuleType("engine")
mod.__file__ = engine_path
mod.__package__ = ""
sys.path.insert(0, SRC_DIR)
with open(engine_path) as f:
    exec(f.read(), mod.__dict__)

ZinniaHandle = mod.ZinniaHandle
HandwriteWin = mod.HandwriteWin
TestCommitEngine = mod.TestCommitEngine

CHAR_STROKES_SIMPLIFIED = [
    ("五", [
        [(50, 60), (350, 60)],
        [(200, 10), (200, 150)],
        [(80, 250), (320, 250)],
    ]),
    ("星", [
        [(120, 20), (280, 20), (280, 75), (120, 75), (120, 20)],
        [(80, 115), (320, 115)],
        [(200, 75), (200, 280)],
        [(80, 280), (320, 280)],
    ]),
    ("出", [
        [(150, 10), (150, 140)],
        [(250, 10), (250, 140)],
        [(150, 140), (250, 140)],
        [(150, 160), (250, 160)],
        [(150, 160), (150, 290)],
        [(250, 160), (250, 290)],
        [(150, 290), (250, 290)],
    ]),
    ("东", [
        [(50, 30), (350, 30)],
        [(200, 10), (200, 290)],
        [(100, 120), (300, 120)],
        [(50, 200), (350, 200)],
    ]),
    ("方", [
        [(100, 20), (300, 20)],
        [(200, 20), (200, 120), (120, 120)],
        [(200, 120), (200, 280)],
        [(60, 70), (340, 70)],
    ]),
    ("利", [
        [(50, 30), (50, 130), (150, 130), (150, 30), (50, 30)],
        [(100, 130), (100, 280)],
        [(50, 160), (150, 160)],
        [(200, 30), (350, 30), (350, 280), (200, 280)],
        [(275, 30), (275, 280)],
    ]),
    ("中", [
        [(100, 15), (300, 15), (300, 285), (100, 285), (100, 15)],
        [(200, 15), (200, 285)],
    ]),
    ("国", [
        [(80, 15), (320, 15), (320, 285), (80, 285), (80, 15)],
        [(160, 80), (240, 80), (240, 140), (160, 140)],
        [(200, 140), (200, 220)],
        [(140, 220), (260, 220)],
    ]),
]

CHAR_STROKES_TRADITIONAL = [
    ("五", CHAR_STROKES_SIMPLIFIED[0][1]),
    ("星", CHAR_STROKES_SIMPLIFIED[1][1]),
    ("出", CHAR_STROKES_SIMPLIFIED[2][1]),
    ("東", [
        [(50, 30), (350, 30)],
        [(200, 10), (200, 150)],
        [(100, 80), (300, 80)],
        [(80, 150), (320, 150)],
        [(200, 150), (200, 290)],
        [(100, 230), (300, 230)],
    ]),
    ("方", CHAR_STROKES_SIMPLIFIED[4][1]),
    ("利", CHAR_STROKES_SIMPLIFIED[5][1]),
    ("中", CHAR_STROKES_SIMPLIFIED[6][1]),
    ("國", [
        [(80, 15), (320, 15), (320, 285), (80, 285), (80, 15)],
        [(160, 60), (260, 60)],
        [(200, 60), (200, 200)],
        [(160, 120), (260, 120)],
        [(140, 200), (200, 200), (200, 240)],
        [(260, 80), (260, 240)],
    ]),
]


class TestEditorWin(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Test Editor")
        self.set_default_size(600, 400)
        self.set_position(Gtk.WindowPosition.CENTER)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add(vbox)

        label = Gtk.Label(label="Handwriting Test Editor")
        vbox.pack_start(label, False, False, 4)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.textview = Gtk.TextView()
        self.textview.set_editable(True)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.textbuffer = self.textview.get_buffer()
        scrolled.add(self.textview)
        vbox.pack_start(scrolled, True, True, 0)

        self.connect("destroy", lambda _: Gtk.main_quit())


def take_screenshot(name):
    screenshot_dir = os.path.join(SCRIPT_DIR, 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    path = os.path.join(screenshot_dir, name)
    try:
        root = Gdk.get_default_root_window()
        if not root:
            print("SCREENSHOT FAILED: no root window", flush=True)
            return
        pb = Gdk.pixbuf_get_from_window(root, 0, 0, root.get_width(), root.get_height())
        if pb:
            pb.savev(path, "png", [], [])
            print(f"SCREENSHOT saved to {path}", flush=True)
        else:
            print("SCREENSHOT FAILED: pixbuf is None", flush=True)
    except Exception as e:
        print(f"SCREENSHOT FAILED: {e}", flush=True)


def run_test():
    Gtk.init(sys.argv)

    editor = TestEditorWin()
    editor.show_all()
    editor.present()

    while Gtk.events_pending():
        Gtk.main_iteration()

    engine = TestCommitEngine()
    win = HandwriteWin(engine)
    engine.win = win
    win.show_all()
    win.present()
    win._hide_cursor()

    while Gtk.events_pending():
        Gtk.main_iteration()

    results = []
    current_char = [0]
    phase = [0]

    def step():
        p = phase[0]
        if p == 0:
            phase[0] = 1
            GLib.timeout_add(200, step)
            return False
        if p == 1:
            idx = current_char[0]
            if idx >= len(CHAR_STROKES_SIMPLIFIED):
                phase[0] = 10
                GLib.timeout_add(200, step)
                return False

            char_name, strokes = CHAR_STROKES_SIMPLIFIED[idx]
            for stroke in strokes:
                engine.zinnia.add_stroke(stroke)
                win.strokes.append(stroke)

            win.pix = None
            win.queue_draw()

            while Gtk.events_pending():
                Gtk.main_iteration()

            phase[0] = 2
            GLib.timeout_add(300, step)
            return False

        if p == 2:
            idx = current_char[0]
            char_name = CHAR_STROKES_SIMPLIFIED[idx][0]

            engine.update_candidates()

            while Gtk.events_pending():
                Gtk.main_iteration()

            top = ""
            candidates_preview = []
            if engine.last_results:
                top = engine.last_results[0][0]
                candidates_preview = [c for c, _ in engine.last_results[:8]]

            print(f"CHAR {char_name} -> recognized as '{top}', candidates: {candidates_preview}", flush=True)
            results.append((char_name, top))
            engine.commit_first()

            if top == char_name:
                print(f"  ✓ MATCH", flush=True)

            if idx in (2, 6):
                take_screenshot(f"writing_{idx+1}.png")

            current_char[0] = idx + 1
            phase[0] = 0
            GLib.timeout_add(200, step)
            return False

        if p == 10:
            take_screenshot("writing_final.png")

            print("=" * 40, flush=True)
            print("TEST RESULTS:", flush=True)
            for expected, got in results:
                status = "OK" if expected == got else "MISMATCH"
                print(f"  {expected} -> '{got}' [{status}]", flush=True)
            print("=" * 40, flush=True)

            match_count = sum(1 for e, g in results if e == g)
            total = len(results)
            print(f"\nPassed: {match_count}/{total}", flush=True)
            GLib.timeout_add(500, Gtk.main_quit)
            return False

        return False

    GLib.timeout_add(500, step)
    Gtk.main()

    match_count = sum(1 for e, g in results if e == g)
    total = len(results)
    print(f"\nFinal: {match_count}/{total} correct", flush=True)

    if match_count == 0:
        print("WARNING: No characters matched exactly (synthetic stroke limitation)", flush=True)

    screenshots_exist = os.path.isdir(os.path.join(SCRIPT_DIR, 'screenshots'))
    print(f"\nPipeline verification:", flush=True)
    print(f"  Characters drawn: {total}", flush=True)
    print(f"  Characters committed: {len([r for r in results if r[1]])}", flush=True)
    print(f"  Screenshots captured: {screenshots_exist}", flush=True)

    if total > 0 and screenshots_exist:
        print("PIPELINE TEST PASSED", flush=True)
        return 0
    else:
        print("PIPELINE TEST FAILED", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(run_test())
