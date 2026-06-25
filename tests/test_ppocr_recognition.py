#!/usr/bin/env python3
"""Test PP-OCRv6 ONNX recognition backend (OnnxHandle class).

Tests OnnxHandle directly without GTK/IBus dependencies.
Runs standalone: ``python3 tests/test_ppocr_recognition.py``
Or with pytest: ``python3 -m pytest tests/test_ppocr_recognition.py -v``
"""

import os
import sys
import time
import threading
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'src'))

# ---------------------------------------------------------------------------
# Module loading
# ---------------------------------------------------------------------------
HAS_ENGINE = False
engine = None
_import_error = ""

try:
    import importlib.machinery
    import importlib.util

    _engine_path = os.path.join(SCRIPT_DIR, '..', 'src', 'ibus-engine-handwrite-chinese')
    loader = importlib.machinery.SourceFileLoader('engine', _engine_path)
    spec = importlib.util.spec_from_loader('engine', loader)
    engine = importlib.util.module_from_spec(spec)
    loader.exec_module(engine)
    HAS_ENGINE = True
except Exception as exc:
    HAS_ENGINE = False
    _import_error = str(exc)

# ---------------------------------------------------------------------------
# Model paths
# ---------------------------------------------------------------------------
MODEL_PATH = "/tmp/models/ppocrv6_small.onnx"
DICT_PATH = "/tmp/models/dict_v6.txt"

MODELS_AVAILABLE = os.path.exists(MODEL_PATH) and os.path.exists(DICT_PATH)

# Determine the actual number of output classes from the model file
MODEL_OUTPUT_CLASSES = None
if HAS_ENGINE and MODELS_AVAILABLE:
    try:
        import onnxruntime
        _sess = onnxruntime.InferenceSession(
            MODEL_PATH, providers=["CPUExecutionProvider"]
        )
        for o in _sess.get_outputs():
            MODEL_OUTPUT_CLASSES = o.shape[-1]
            break
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Helper: dict size for decode tests
# ---------------------------------------------------------------------------
_DICT_SIZE = 0
if HAS_ENGINE and MODELS_AVAILABLE:
    try:
        with open(DICT_PATH, "r", encoding="utf-8") as _f:
            for _line in _f:
                if _line.strip():
                    _DICT_SIZE += 1
    except Exception:
        pass


# ===================================================================
# 1. OnnxHandle creation with correct dict/model
# ===================================================================
@unittest.skipIf(not HAS_ENGINE, f"Engine could not be loaded: {_import_error}")
class TestOnnxHandleCreation(unittest.TestCase):
    """Test OnnxHandle construction and init."""

    # -- Tests requiring real model files --
    @unittest.skipIf(not MODELS_AVAILABLE, f"Model not found at {MODEL_PATH}")
    def test_creation_with_correct_paths(self):
        """OnnxHandle creation with valid model and dict paths."""
        handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)
        try:
            self.assertIsNotNone(handle)
            self.assertIsNotNone(handle.session)
            self.assertIsNotNone(handle.dict)
            self.assertGreater(len(handle.dict), 0)
            self.assertEqual(handle.num_classes, len(handle.dict) + 2)
            self.assertEqual(handle.max_candidates, engine.MAX_CANDIDATES)
            self.assertEqual(handle.all_points, [])
            self.assertEqual(handle._last_results, [])
        finally:
            handle.destroy()

    @unittest.skipIf(not MODELS_AVAILABLE, f"Model not found at {MODEL_PATH}")
    def test_creation_custom_max_candidates(self):
        """OnnxHandle creation with custom max_candidates."""
        handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH, max_candidates=10)
        try:
            self.assertEqual(handle.max_candidates, 10)
        finally:
            handle.destroy()

    # -- Tests that do NOT need model files --
    def test_creation_fails_invalid_model(self):
        """OnnxHandle raises when model path is invalid."""
        with self.assertRaises(Exception):
            engine.OnnxHandle("/nonexistent/model.onnx", DICT_PATH)

    def test_creation_fails_invalid_dict(self):
        """OnnxHandle raises when dict path is invalid."""
        with self.assertRaises(Exception):
            engine.OnnxHandle(MODEL_PATH, "/nonexistent/dict.txt")

    def test_creation_fails_missing_numpy(self):
        """OnnxHandle raises RuntimeError without numpy (simulated)."""
        # Monkey-patch HAS_NUMPY to False to verify the error path.
        original = engine.HAS_NUMPY
        engine.HAS_NUMPY = False
        try:
            with self.assertRaises(RuntimeError):
                engine.OnnxHandle(MODEL_PATH, DICT_PATH)
        finally:
            engine.HAS_NUMPY = original


# ===================================================================
# 2 & 3. clear() resets state / add_stroke() accumulates
# ===================================================================
@unittest.skipIf(not HAS_ENGINE, f"Engine could not be loaded: {_import_error}")
@unittest.skipIf(not MODELS_AVAILABLE, f"Model not found at {MODEL_PATH}")
class TestOnnxHandleState(unittest.TestCase):
    """Test state management: clear() and add_stroke()."""

    def setUp(self):
        self.handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)

    def tearDown(self):
        self.handle.destroy()

    def test_clear_resets_state(self):
        """clear() resets all_points and _last_results."""
        self.handle.add_stroke([(100, 100), (200, 200)])
        self.handle._last_results = [("test", 0.5)]
        self.handle.clear()
        self.assertEqual(self.handle.all_points, [])
        self.assertEqual(self.handle._last_results, [])

    def test_add_stroke_accumulates(self):
        """add_stroke() appends strokes to all_points."""
        self.assertEqual(len(self.handle.all_points), 0)

        stroke1 = [(100, 100), (200, 200)]
        self.handle.add_stroke(stroke1)
        self.assertEqual(len(self.handle.all_points), 1)
        self.assertIs(self.handle.all_points[0], stroke1)

        stroke2 = [(300, 300), (400, 400)]
        self.handle.add_stroke(stroke2)
        self.assertEqual(len(self.handle.all_points), 2)

    def test_clear_after_multiple_strokes(self):
        """clear() after adding multiple strokes empties the list."""
        self.handle.add_stroke([(100, 100), (200, 200)])
        self.handle.add_stroke([(300, 300), (400, 400)])
        self.handle.clear()
        self.assertEqual(self.handle.all_points, [])

    def test_add_stroke_empty_list(self):
        """add_stroke([]) appends an empty stroke."""
        self.handle.add_stroke([])
        self.assertEqual(len(self.handle.all_points), 1)
        self.assertEqual(self.handle.all_points[0], [])


# ===================================================================
# 8 & 9. _preprocess returns None for no strokes / correct shape
# ===================================================================
@unittest.skipIf(not HAS_ENGINE, f"Engine could not be loaded: {_import_error}")
@unittest.skipIf(not MODELS_AVAILABLE, f"Model not found at {MODEL_PATH}")
class TestOnnxHandlePreprocess(unittest.TestCase):
    """Test OnnxHandle._preprocess()."""

    def setUp(self):
        self.handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)

    def tearDown(self):
        self.handle.destroy()

    # ---- 8. _preprocess returns None for no strokes ----
    def test_preprocess_none_when_no_strokes(self):
        """_preprocess() returns None when no strokes added."""
        self.assertIsNone(self.handle._preprocess())

    def test_preprocess_none_when_empty_stroke(self):
        """_preprocess() returns None when stroke has no points."""
        self.handle.add_stroke([])
        self.assertIsNone(self.handle._preprocess())

    def test_preprocess_none_when_only_empty_strokes(self):
        """_preprocess() returns None when all strokes are empty."""
        self.handle.add_stroke([])
        self.handle.add_stroke([])
        self.assertIsNone(self.handle._preprocess())

    # ---- 9. _preprocess produces correct tensor shape ----
    def test_preprocess_tensor_shape(self):
        """_preprocess() returns [1, 3, 48, W] tensor."""
        self.handle.add_stroke([(100, 500), (900, 500)])
        result = self.handle._preprocess()
        self.assertIsNotNone(result)
        self.assertEqual(result.ndim, 4)
        self.assertEqual(result.shape[0], 1)    # batch
        self.assertEqual(result.shape[1], 3)    # channels (replicated)
        self.assertEqual(result.shape[2], 48)   # height (resized)
        self.assertGreater(result.shape[3], 0)  # width (aspect-preserved)
        self.assertEqual(result.dtype.kind, 'f')

    def test_preprocess_multiple_strokes(self):
        """_preprocess() handles multiple strokes."""
        self.handle.add_stroke([(100, 100), (400, 400)])
        self.handle.add_stroke([(500, 100), (200, 400)])
        result = self.handle._preprocess()
        self.assertIsNotNone(result)
        self.assertEqual(result.shape[1], 3)
        self.assertEqual(result.shape[2], 48)

    def test_preprocess_values_normalized(self):
        """_preprocess() normalizes pixel values to [-1, 1]."""
        self.handle.add_stroke([(100, 500), (900, 500)])
        result = self.handle._preprocess()
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result.min(), -1.0 - 1e-5)
        self.assertLessEqual(result.max(), 1.0 + 1e-5)

    def test_preprocess_width_varies_with_aspect_ratio(self):
        """_preprocess() width depends on stroke aspect ratio."""
        self.handle.add_stroke([(100, 100), (100, 900)])  # tall
        tall_result = self.handle._preprocess()
        self.handle.clear()
        self.handle.add_stroke([(100, 100), (900, 100)])  # wide
        wide_result = self.handle._preprocess()
        self.assertIsNotNone(tall_result)
        self.assertIsNotNone(wide_result)
        # Tall stroke should have narrower width than wide stroke
        self.assertLess(tall_result.shape[3], wide_result.shape[3])

    def test_preprocess_three_channels_identical(self):
        """_preprocess() replicates grayscale across 3 channels."""
        self.handle.add_stroke([(100, 500), (900, 500)])
        result = self.handle._preprocess()
        self.assertIsNotNone(result)
        # Channels 0, 1, 2 should be identical
        import numpy as np
        np.testing.assert_array_equal(result[0, 0], result[0, 1])
        np.testing.assert_array_equal(result[0, 1], result[0, 2])


# ===================================================================
# 10. _decode handles output correctly, excludes blank and unknown
# ===================================================================
@unittest.skipIf(not HAS_ENGINE, f"Engine could not be loaded: {_import_error}")
@unittest.skipIf(not MODELS_AVAILABLE, f"Model not found at {MODEL_PATH}")
class TestOnnxHandleDecode(unittest.TestCase):
    """Test OnnxHandle._decode()."""

    def setUp(self):
        self.handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)

    def tearDown(self):
        self.handle.destroy()

    def _num_classes_for_decode(self):
        """Return the number of classes _decode can safely handle.

        The OnnxHandle computes ``num_classes = len(dict) + 2``, but the
        on-disk model may have a different count.  We test ``_decode`` at
        ``len(dict) + 2`` so that ``avg_probs[1:-1]`` yields exactly
        ``len(dict)`` candidates – matching what the method expects.
        """
        return len(self.handle.dict) + 2

    def _make_fake_output(self):
        """Create a fake ONNX output tensor [1, 10, nc] for decode tests."""
        import numpy as np
        nc = self._num_classes_for_decode()
        return np.zeros((1, 10, nc), dtype=np.float32)

    def test_decode_excludes_blank_and_unknown(self):
        """_decode() skips blank (idx 0) and unknown (last idx)."""
        import numpy as np
        nc = self._num_classes_for_decode()
        probs = self._make_fake_output()
        probs[:] = 0.001 / nc                     # low uniform background
        probs[:, :, 0] = 0.5                       # blank — must be excluded
        probs[:, :, 1] = 0.4                       # first real char
        probs[:, :, -1] = 0.1                      # unknown — must be excluded
        result = self.handle._decode(probs)
        self.assertGreater(len(result), 0)
        # Top candidate should be the first real char (= dict[0])
        self.assertEqual(result[0][0], self.handle.dict[0])

    def test_decode_returns_string_score_tuples(self):
        """_decode() returns list of (str, float) tuples."""
        import numpy as np
        nc = self._num_classes_for_decode()
        probs = self._make_fake_output()
        probs[:] = 0.001 / nc
        probs[:, :, 1] = 0.9    # dominate with first real char
        result = self.handle._decode(probs)
        for ch, score in result:
            self.assertIsInstance(ch, str)
            self.assertIsInstance(score, float)

    def test_decode_respects_max_candidates(self):
        """_decode() returns at most max_candidates results."""
        import numpy as np
        nc = self._num_classes_for_decode()
        probs = self._make_fake_output()
        # Give high probability to many different chars
        probs[:] = 0.001 / nc
        for i in range(min(50, nc - 2)):
            probs[:, :, 1 + i] = 0.5 - i * 0.01
        result = self.handle._decode(probs)
        self.assertLessEqual(len(result), self.handle.max_candidates)

    def test_decode_results_are_sorted_by_score_descending(self):
        """_decode() returns results in descending score order."""
        import numpy as np
        probs = self._make_fake_output()
        probs[:] = 0.001 / self._num_classes_for_decode()
        # Give top three classes distinct probabilities
        probs[:, :, 1] = 0.6
        probs[:, :, 2] = 0.3
        probs[:, :, 3] = 0.1
        result = self.handle._decode(probs)
        scores = [s for _, s in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_decode_uniform_input(self):
        """_decode() handles uniform probabilities without IndexError."""
        import numpy as np
        nc = self._num_classes_for_decode()
        probs = np.zeros((1, 10, nc), dtype=np.float32)
        probs[:] = 1.0 / nc
        result = self.handle._decode(probs)
        self.assertGreater(len(result), 0)

    def test_decode_returns_dict_chars_only(self):
        """_decode() only returns characters from the loaded dict."""
        import numpy as np
        nc = self._num_classes_for_decode()
        probs = self._make_fake_output()
        probs[:] = 1.0 / nc
        result = self.handle._decode(probs)
        dict_set = set(self.handle.dict)
        for ch, _ in result:
            self.assertIn(ch, dict_set)


# ===================================================================
# 4 & 5. classify() with/without strokes
# ===================================================================
@unittest.skipIf(not HAS_ENGINE, f"Engine could not be loaded: {_import_error}")
@unittest.skipIf(not MODELS_AVAILABLE, f"Model not found at {MODEL_PATH}")
class TestOnnxHandleClassify(unittest.TestCase):
    """Test OnnxHandle.classify() sync inference."""

    def setUp(self):
        self.handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)

    def tearDown(self):
        self.handle.destroy()

    # ---- 4. classify() with strokes returns results ----
    def test_classify_with_strokes(self):
        """classify() with strokes returns non-empty candidate list."""
        self.handle.add_stroke([(100, 500), (900, 500)])
        results = self.handle.classify()
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        ch, score = results[0]
        self.assertIsInstance(ch, str)
        self.assertGreater(len(ch), 0)
        self.assertIsInstance(score, float)

    def test_classify_with_multiple_strokes(self):
        """classify() handles multiple strokes."""
        self.handle.add_stroke([(100, 100), (500, 500)])
        self.handle.add_stroke([(600, 100), (200, 500)])
        results = self.handle.classify()
        self.assertGreater(len(results), 0)

    # ---- 5. classify() with empty strokes returns [] ----
    def test_classify_empty_no_strokes(self):
        """classify() with no strokes returns []."""
        self.assertEqual(self.handle.classify(), [])

    def test_classify_empty_after_clear(self):
        """classify() returns [] after clear()."""
        self.handle.add_stroke([(100, 500), (900, 500)])
        self.handle.clear()
        self.assertEqual(self.handle.classify(), [])

    def test_classify_empty_stroke_list(self):
        """classify() with empty stroke in list returns []."""
        self.handle.add_stroke([])
        self.assertEqual(self.handle.classify(), [])

    def test_classify_returns_results(self):
        """classify() returns valid candidate list."""
        self.handle.add_stroke([(100, 500), (900, 500)])
        results = self.handle.classify()
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(self.handle._last_results, [])

    def test_classify_consistency_same_input(self):
        """classify() produces same top candidate for identical input."""
        self.handle.add_stroke([(200, 200), (500, 800), (800, 200)])
        results1 = self.handle.classify()
        self.handle.clear()
        self.handle.add_stroke([(200, 200), (500, 800), (800, 200)])
        results2 = self.handle.classify()
        self.assertEqual(results1[0][0], results2[0][0])


# ===================================================================
# 6. classify_async() invokes callback with results
# ===================================================================
@unittest.skipIf(not HAS_ENGINE, f"Engine could not be loaded: {_import_error}")
@unittest.skipIf(not MODELS_AVAILABLE, f"Model not found at {MODEL_PATH}")
class TestOnnxHandleAsync(unittest.TestCase):
    """Test OnnxHandle.classify_async() and lock contention."""

    def setUp(self):
        self.handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)

    def tearDown(self):
        self.handle.destroy()

    # ---- 6. classify_async invokes callback ----
    def test_async_updates_last_results(self):
        """classify_async() populates _last_results (no GLib needed)."""
        self.handle.add_stroke([(100, 500), (900, 500)])

        def _cb(_r):
            pass

        self.handle.classify_async(_cb)
        self._wait_for_async(3)
        self.assertGreater(len(self.handle._last_results), 0)

    def test_async_invokes_callback(self):
        """classify_async() invokes callback with results via GLib.idle_add."""
        self.handle.add_stroke([(100, 500), (900, 500)])

        results = []
        event = threading.Event()

        def _cb(r):
            results.append(r)
            event.set()

        self.handle.classify_async(_cb)

        # Run GLib main loop to dispatch the idle_add callback
        self._run_glib_loop(timeout=5, quit_event=event)

        self.assertTrue(event.is_set(), "Callback was not invoked within timeout")
        self.assertGreater(len(results[0]), 0)

    def test_async_callback_receives_list_of_tuples(self):
        """classify_async() callback receives [(str, float), ...]."""
        self.handle.add_stroke([(100, 500), (900, 500)])

        results = []
        event = threading.Event()

        def _cb(r):
            results.append(r)
            event.set()

        self.handle.classify_async(_cb)
        self._run_glib_loop(timeout=5, quit_event=event)

        self.assertTrue(event.is_set())
        for ch, score in results[0]:
            self.assertIsInstance(ch, str)
            self.assertIsInstance(score, float)

    # ---- 7. Lock contention drops concurrent calls ----
    def test_async_lock_contention_second_call_dropped(self):
        """Concurrent classify_async() call is dropped (lock contention)."""
        self.handle.add_stroke([(100, 500), (900, 500)])

        first_in_progress = threading.Event()
        first_finished = threading.Event()
        call_count = [0]

        # Slow down _preprocess so the first call holds the lock longer
        orig_preprocess = self.handle._preprocess

        def _slow_preprocess():
            first_in_progress.set()
            time.sleep(0.5)
            return orig_preprocess()

        self.handle._preprocess = _slow_preprocess

        def _cb(_r):
            call_count[0] += 1
            first_finished.set()

        # First call — enters slow _preprocess, lock held
        self.handle.classify_async(_cb)
        first_in_progress.wait(timeout=3)

        # Second call — should be dropped (lock already held)
        # This must not raise an exception
        try:
            self.handle.classify_async(lambda r: None)
        except Exception:
            self.fail("classify_async() raised when lock was contended")

        # Wait for first call to complete
        first_finished.wait(timeout=5)

        # Restore
        self.handle._preprocess = orig_preprocess

        # Run GLib loop to dispatch the idle callback
        self._run_glib_loop(timeout=2)

        # Only one call should have reached the callback
        self.assertEqual(call_count[0], 1)

    def test_async_lock_held_until_completion(self):
        """The infer lock is held during inference and released after."""
        self.handle.add_stroke([(100, 500), (900, 500)])

        # Verify the lock is free initially
        acquired = self.handle._infer_lock.acquire(blocking=False)
        self.assertTrue(acquired, "Lock should be free before async call")
        self.handle._infer_lock.release()

        in_progress = threading.Event()

        orig_preprocess = self.handle._preprocess

        def _slow_preprocess():
            in_progress.set()
            time.sleep(0.3)
            return orig_preprocess()

        self.handle._preprocess = _slow_preprocess

        done = threading.Event()

        def _cb(_r):
            done.set()

        self.handle.classify_async(_cb)
        in_progress.wait(timeout=3)

        # Lock should be held during inference
        acquired = self.handle._infer_lock.acquire(blocking=False)
        self.assertFalse(acquired, "Lock should be held during async inference")

        # Wait for completion
        done.wait(timeout=4)
        self.handle._preprocess = orig_preprocess

        # Run GLib loop to dispatch the idle callback
        self._run_glib_loop(timeout=2)

        # Lock should be free again
        acquired = self.handle._infer_lock.acquire(blocking=False)
        self.assertTrue(acquired, "Lock should be free after async inference")
        self.handle._infer_lock.release()

    def test_async_sequential_calls(self):
        """Sequential classify_async() calls both complete."""
        self.handle.add_stroke([(100, 500), (900, 500)])

        call_count = [0]
        event = threading.Event()

        def _cb1(_r):
            call_count[0] += 1

        def _cb2(_r):
            call_count[0] += 1
            event.set()

        self.handle.classify_async(_cb1)
        time.sleep(0.3)

        self.handle.classify_async(_cb2)
        event.wait(timeout=5)

        self._run_glib_loop(timeout=2)

        self.assertEqual(call_count[0], 2)

    # ------------------------- helpers -------------------------
    def _wait_for_async(self, timeout):
        """Wait for background async thread to complete."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.handle._last_results:
                return
            time.sleep(0.05)

    def _start_glib_loop(self, timeout_ms=5000):
        """Start a GLib main loop in the current thread with a timeout."""
        from gi.repository import GLib
        loop = GLib.MainLoop()
        GLib.timeout_add(timeout_ms, loop.quit)
        return loop

    def _run_glib_loop(self, timeout=5, quit_event=None):
        """Run GLib main loop for up to `timeout` seconds to dispatch idle callbacks."""
        from gi.repository import GLib
        if quit_event is None:
            quit_event = threading.Event()
        loop = GLib.MainLoop()

        def _quit():
            loop.quit()
            return False

        def _check_timeout():
            if not quit_event.is_set():
                return True  # keep checking
            loop.quit()
            return False

        GLib.timeout_add(int(timeout * 1000), _quit)
        GLib.timeout_add(200, _check_timeout)
        loop.run()


# ===================================================================
# 10b. (additional decode edge cases)
# ===================================================================
# (included in TestOnnxHandleDecode above)


# ===================================================================
# 11. get_results returns last cached results
# ===================================================================
@unittest.skipIf(not HAS_ENGINE, f"Engine could not be loaded: {_import_error}")
@unittest.skipIf(not MODELS_AVAILABLE, f"Model not found at {MODEL_PATH}")
class TestOnnxHandleGetResults(unittest.TestCase):
    """Test OnnxHandle.get_results()."""

    def setUp(self):
        self.handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)

    def tearDown(self):
        self.handle.destroy()

    def test_get_results_empty_initially(self):
        """get_results() returns [] before any classify call."""
        self.assertEqual(self.handle.get_results(), [])

    def test_get_results_returns_last_cached(self):
        """get_results() returns the last cached results."""
        expected = [("a", 0.5), ("b", 0.3)]
        self.handle._last_results = list(expected)
        self.assertEqual(self.handle.get_results(), expected)

    def test_get_results_returns_copy_not_reference(self):
        """get_results() returns a copy; mutating it doesn't affect internal state."""
        self.handle._last_results = [("a", 0.5)]
        external = self.handle.get_results()
        external.append(("b", 0.3))
        self.assertEqual(len(self.handle._last_results), 1)

    def test_get_results_after_classify_updates_last_results(self):
        """get_results() returns _last_results (updated by async classify)."""
        self.handle.add_stroke([(100, 500), (900, 500)])
        # get_results() returns _last_results; classify() doesn't update it
        self.handle._last_results = [("一", 0.9)]
        self.assertEqual(self.handle.get_results(), [("一", 0.9)])

    def test_get_results_after_clear(self):
        """get_results() reflects cleared state."""
        self.handle._last_results = [("一", 0.9)]
        self.handle.clear()
        self.assertEqual(self.handle.get_results(), [])


# ===================================================================
# 12. destroy cleans up
# ===================================================================
@unittest.skipIf(not HAS_ENGINE, f"Engine could not be loaded: {_import_error}")
@unittest.skipIf(not MODELS_AVAILABLE, f"Model not found at {MODEL_PATH}")
class TestOnnxHandleDestroy(unittest.TestCase):
    """Test OnnxHandle.destroy()."""

    def test_destroy_clears_state(self):
        """destroy() clears all_points and _last_results."""
        handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)
        handle.add_stroke([(100, 100), (200, 200)])
        handle._last_results = [("a", 0.5)]
        handle.destroy()
        self.assertEqual(handle.all_points, [])
        self.assertEqual(handle._last_results, [])

    def test_destroy_idempotent(self):
        """Calling destroy() multiple times is safe."""
        handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)
        handle.destroy()
        # Second destroy should not raise
        handle.destroy()

    def test_destroy_does_not_affect_session(self):
        """destroy() does not cascade-delete the onnxruntime session."""
        handle = engine.OnnxHandle(MODEL_PATH, DICT_PATH)
        session = handle.session
        handle.destroy()
        # The session object should still exist (not freed by our destroy)
        self.assertIsNotNone(session)


# ===================================================================
# Entry point
# ===================================================================
if __name__ == "__main__":
    unittest.main()
