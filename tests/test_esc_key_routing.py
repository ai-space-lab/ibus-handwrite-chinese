#!/usr/bin/env python3
"""
Test: ESC key routing in ibus-engine-handwrite-chinese.

Verifies that ESC key events are correctly handled by the engine's
on_key_esc method and the two-state state machine (pause then close).

The engine logs state transitions to /tmp/hw.log (PID-prefixed).
We verify by:
  1. Starting the engine in --test mode
  2. Sending ESC via xdotool to the "Chinese Handwriting" window
  3. Reading /tmp/hw.log for the expected state transitions

Requires: xdotool, X server (Xvfb :99 works in CI)
"""

import os
import shutil
import signal
import subprocess
import sys
import time
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ENGINE_PATH = os.path.join(PROJECT_ROOT, 'src', 'ibus-engine-handwrite-chinese')
HW_LOG = '/tmp/hw.log'
DISPLAY_ENV = os.environ.get('DISPLAY', ':99')

# ---------------------------------------------------------------------------
# Prerequisite detection
# ---------------------------------------------------------------------------
_has_xdotool = shutil.which('xdotool') is not None


def _check_x_server():
    """Check if an X server is available via xdpyinfo."""
    try:
        result = subprocess.run(
            ['xdpyinfo', '-display', DISPLAY_ENV],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


_has_x_server = _check_x_server()


@unittest.skipIf(not _has_xdotool, "xdotool is not installed")
@unittest.skipIf(not _has_x_server, f"No X server available at DISPLAY={DISPLAY_ENV}")
class TestEscKeyRouting(unittest.TestCase):
    """Test ESC key routing in --test mode."""

    def setUp(self):
        """Clear HW log before each test."""
        if os.path.exists(HW_LOG):
            os.unlink(HW_LOG)
        self.proc = None

    def tearDown(self):
        """Ensure engine subprocess is stopped."""
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _start_engine(self):
        """Start the engine in --test mode as a subprocess."""
        self.proc = subprocess.Popen(
            [sys.executable, ENGINE_PATH, '--test'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, 'DISPLAY': DISPLAY_ENV},
        )
        # Give GTK time to settle — window creation + event loop start
        time.sleep(2)

    def _find_window(self, timeout=12):
        """Wait for the 'Chinese Handwriting' window to appear.

        Returns the first matching X window ID, or None on timeout.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'Chinese Handwriting'],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split()[0]
            time.sleep(0.3)
        return None

    def _focus_window(self, window_id):
        """Focus the given X window ('xdotool windowactivate --sync')."""
        subprocess.run(
            ['xdotool', 'windowactivate', '--sync', window_id],
            capture_output=True, timeout=5,
        )
        time.sleep(0.3)  # let GTK process the focus event

    def _send_esc(self):
        """Send a single ESC key via xdotool."""
        subprocess.run(['xdotool', 'key', 'Escape'], timeout=5)
        time.sleep(0.5)  # let the engine process the event

    def _read_log(self):
        """Return /tmp/hw.log lines that begin with our PID."""
        if not os.path.exists(HW_LOG):
            return []
        with open(HW_LOG) as f:
            lines = f.readlines()
        prefix = f"{self.proc.pid} "
        return [l.strip() for l in lines if l.startswith(prefix)]

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------
    def test_esc_pause_then_close(self):
        """Verify ESC transitions: _state 0->1 (pause) then 1->0 (close)."""
        self._start_engine()
        try:
            # Find the HandwriteWin window
            window_id = self._find_window(timeout=12)
            self.assertIsNotNone(
                window_id,
                "HandwriteWin window did not appear within 12 seconds",
            )

            # Focus so the window receives key events
            self._focus_window(window_id)

            # ---- First ESC: _state 0 -> 1 (pause) ----
            self._send_esc()

            log_entries = self._read_log()
            self.assertIn(
                f"{self.proc.pid} on_key_esc: _state=0",
                log_entries,
                f"First ESC should log _state=0. Got: {log_entries}",
            )

            # ---- Second ESC: _state 1 -> close (_do_disable) ----
            self._send_esc()

            log_entries = self._read_log()
            self.assertIn(
                f"{self.proc.pid} on_key_esc: _state=1",
                log_entries,
                f"Second ESC should log _state=1. Got: {log_entries}",
            )

        finally:
            if self.proc is not None and self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=2)


if __name__ == '__main__':
    unittest.main()
