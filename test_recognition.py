#!/usr/bin/env python3
"""Test handwriting recognition with synthetic strokes across all models."""

import ctypes
import os
import sys

MODEL_DIR = "/usr/share/tegaki/models/zinnia"


def load_zinnia():
    for libname in ["libzinnia.so.0", "libzinnia.so"]:
        try:
            libz = ctypes.CDLL(libname)
            return libz
        except OSError:
            continue
    print("FAIL: Could not load libzinnia")
    sys.exit(1)


def setup_signatures(libz):
    libz.zinnia_recognizer_new.restype = ctypes.c_void_p
    libz.zinnia_recognizer_destroy.restype = None
    libz.zinnia_recognizer_destroy.argtypes = [ctypes.c_void_p]
    libz.zinnia_recognizer_open.restype = ctypes.c_int
    libz.zinnia_recognizer_open.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    libz.zinnia_recognizer_strerror.restype = ctypes.c_char_p
    libz.zinnia_recognizer_strerror.argtypes = [ctypes.c_void_p]

    libz.zinnia_character_new.restype = ctypes.c_void_p
    libz.zinnia_character_destroy.restype = None
    libz.zinnia_character_destroy.argtypes = [ctypes.c_void_p]
    libz.zinnia_character_set_width.restype = None
    libz.zinnia_character_set_width.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    libz.zinnia_character_set_height.restype = None
    libz.zinnia_character_set_height.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    libz.zinnia_character_add.restype = ctypes.c_int
    libz.zinnia_character_add.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int]

    libz.zinnia_recognizer_classify.restype = ctypes.c_void_p
    libz.zinnia_recognizer_classify.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]

    libz.zinnia_result_value.restype = ctypes.c_char_p
    libz.zinnia_result_value.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    libz.zinnia_result_score.restype = ctypes.c_float
    libz.zinnia_result_score.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    libz.zinnia_result_size.restype = ctypes.c_size_t
    libz.zinnia_result_size.argtypes = [ctypes.c_void_p]
    libz.zinnia_result_destroy.restype = None
    libz.zinnia_result_destroy.argtypes = [ctypes.c_void_p]


def test_model(libz, model_path, strokes, label):
    if not os.path.exists(model_path):
        print(f"  SKIP: model not found: {model_path}")
        return True

    recognizer = libz.zinnia_recognizer_new()
    if not recognizer:
        print(f"  FAIL: Could not create recognizer for {label}")
        return False

    if not libz.zinnia_recognizer_open(recognizer, model_path.encode()):
        err = libz.zinnia_recognizer_strerror(recognizer)
        err_msg = err.decode() if err else "unknown"
        print(f"  FAIL: Could not open model {label}: {err_msg}")
        libz.zinnia_recognizer_destroy(recognizer)
        return False

    char = libz.zinnia_character_new()
    libz.zinnia_character_set_width(char, 1000)
    libz.zinnia_character_set_height(char, 1000)

    for stroke_id, points in enumerate(strokes):
        for x, y in points:
            libz.zinnia_character_add(char, stroke_id, x, y)

    result = libz.zinnia_recognizer_classify(recognizer, char, 96)
    if not result:
        print(f"  FAIL: Classification returned null for {label}")
        libz.zinnia_character_destroy(char)
        libz.zinnia_recognizer_destroy(recognizer)
        return False

    size = libz.zinnia_result_size(result)
    print(f"  {label}: {size} candidates")

    candidates = []
    for i in range(min(size, 5)):
        char_str = libz.zinnia_result_value(result, i)
        score = libz.zinnia_result_score(result, i)
        if char_str:
            char_str = char_str.decode("utf-8", errors="replace")
        else:
            char_str = "<null>"
        candidates.append((char_str, score))
        print(f"    #{i}: '{char_str}' score={score:.2f}")

    libz.zinnia_result_destroy(result)
    libz.zinnia_character_destroy(char)
    libz.zinnia_recognizer_destroy(recognizer)

    if not candidates:
        print(f"  FAIL: No candidates for {label}")
        return False

    if not candidates[0][0] or candidates[0][0] == "<null>":
        print(f"  FAIL: Empty top candidate for {label}")
        return False

    if candidates[0][1] <= 0:
        print(f"  FAIL: Non-positive score ({candidates[0][1]}) for {label}")
        return False

    print(f"  PASS: '{candidates[0][0]}' score={candidates[0][1]:.2f}")
    return True


def main():
    libz = load_zinnia()
    setup_signatures(libz)

    passed = 0
    failed = 0

    tests = [
        ("Simplified zh_CN", os.path.join(MODEL_DIR, "handwriting-zh_CN.model"),
         [[(100, 500), (900, 500)]]),
        ("Traditional zh_TW", os.path.join(MODEL_DIR, "handwriting-zh_TW.model"),
         [[(100, 500), (900, 500)], [(500, 100), (500, 900)]]),
    ]

    for label, model_path, strokes in tests:
        print(f"\n--- {label} ---")
        if test_model(libz, model_path, strokes, label):
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*30}")
    print(f"Results: {passed} passed, {failed} failed")

    if failed:
        sys.exit(1)
    if passed == 0:
        print("FAIL: No tests were run (no models found?)")
        sys.exit(1)
    print("All tests passed!")


if __name__ == "__main__":
    main()
