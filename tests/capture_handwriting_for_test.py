#!/usr/bin/env python3
"""Capture actual handwriting from touchpad, compare Tegaki vs 幽兰百合 accuracy."""

import ctypes
import sys
import time
import json
import os

TEGAKI_CN = "/usr/share/tegaki/models/zinnia/handwriting-zh_CN.model"
COMMUNITY = "/tmp/handwriting-model-community/ZJHandWriting-zh_CN.model"
W, H = 1000, 1000
SAVE_FILE = "/tmp/ibus-handwrite-chinese/captured_strokes.json"

TEST_CHARS = {
    "A: Common":   ["一", "十", "人", "大", "中", "国", "我", "的", "是", "不"],
    "B: Medium":   ["家", "爱", "学", "书", "长", "用", "为", "会", "没", "进"],
    "C: OOV only": ["堃", "彧", "犇", "甪", "劖", "勔", "厾", "叕", "彟", "玊"],
}

# ── Zinnia setup ──

def load_zinnia():
    for libname in ["libzinnia.so.0", "libzinnia.so"]:
        try:
            return ctypes.CDLL(libname)
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

def open_model(libz, path):
    if not os.path.exists(path):
        print(f"  SKIP: model not found at {path}")
        return None
    r = libz.zinnia_recognizer_new()
    if not r:
        print(f"  FAIL: could not create recognizer")
        return None
    if not libz.zinnia_recognizer_open(r, path.encode()):
        err = libz.zinnia_recognizer_strerror(r)
        print(f"  FAIL: {err.decode() if err else 'unknown'}")
        libz.zinnia_recognizer_destroy(r)
        return None
    return r

def classify_strokes(libz, rec, strokes_frac):
    """Classify strokes given as fractional coords (0.0-1.0)."""
    # Map fractional to 0-1000 box, then apply same bbox normalization as engine
    all_pts = [(int(x * W), int(y * H)) for stroke in strokes_frac for (x, y) in stroke]
    if not all_pts:
        return []
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    cw = max(xmax - xmin, 1)
    ch = max(ymax - ymin, 1)
    scale = min((W - 100) / cw, (H - 100) / ch)
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2

    char = libz.zinnia_character_new()
    libz.zinnia_character_set_width(char, W)
    libz.zinnia_character_set_height(char, H)
    for sid, stroke in enumerate(strokes_frac):
        for fx, fy in stroke:
            nx = int(500 + (int(fx * W) - cx) * scale)
            ny = int(500 + (int(fy * H) - cy) * scale)
            nx = max(0, min(W, nx))
            ny = max(0, min(H, ny))
            libz.zinnia_character_add(char, sid, nx, ny)

    result_ptr = libz.zinnia_recognizer_classify(rec, char, 10)
    candidates = []
    if result_ptr:
        n = libz.zinnia_result_size(result_ptr)
        for i in range(n):
            cv = libz.zinnia_result_value(result_ptr, i)
            sc = libz.zinnia_result_score(result_ptr, i)
            c = cv.decode("utf-8", errors="replace") if cv else "<null>"
            candidates.append((c, sc))
        libz.zinnia_result_destroy(result_ptr)
    libz.zinnia_character_destroy(char)
    return candidates

from handwrite_evdev import TouchpadCapture

# ── Main ──

def main():
    print("=" * 60)
    print("  HANDWRITING ACCURACY TEST: Tegaki zh_CN vs 幽兰百合 Community")
    print("=" * 60)

    libz = load_zinnia()
    setup_signatures(libz)

    tegaki_rec = open_model(libz, TEGAKI_CN)
    community_rec = open_model(libz, COMMUNITY)
    if not tegaki_rec or not community_rec:
        print("FAIL: One or more models could not be loaded")
        sys.exit(1)
    print(f"\n  Models loaded:" )
    print(f"    Tegaki zh_CN:    {TEGAKI_CN}")
    print(f"    幽兰百合:         {COMMUNITY}")

    print("\n  Initializing touchpad capture...")
    cap = TouchpadCapture()
    if not cap.start():
        print("FAIL: No touchpad found or could not grab")
        sys.exit(1)
    print(f"  Touchpad: {cap.device.name} ({cap.device.path})")

    results = []
    total = sum(len(chars) for chars in TEST_CHARS.values())
    done = 0

    print(f"\n  Ready! You will write {total} characters.")
    print("  For each character: write it on the touchpad, then press ENTER.")
    print("  (Make sure the touchpad is not being used by another app.)")

    # Quick self-test: prompt user to touch the pad once
    print("\n  --- SELF TEST ---")
    print("  Tap the touchpad once, then press ENTER...", end=" ", flush=True)
    cap._debug = True
    cap.read_and_clear()
    sys.stdin.readline()
    time.sleep(0.3)
    test_strokes = cap.read_and_clear()
    cap._debug = False
    if test_strokes:
        n_strokes = len(test_strokes)
        n_pts = sum(len(s) for s in test_strokes)
        print(f"  ✓ Touchpad detected! ({n_strokes} strokes, {n_pts} points)")
    else:
        print(f"  ⚠ No strokes detected. The touchpad may be grabbed by another app.")
        print(f"  Please close any app using the touchpad and try again.")
        print(f"  (Try: pkill -f ibus-engine-handwrite-chinese)")
        print(f"  Continuing anyway...")

    for category, chars in TEST_CHARS.items():
        print(f"\n{'─' * 60}")
        print(f"  {category}")
        print(f"{'─' * 60}")

        for ch in chars:
            cap.read_and_clear()
            done += 1
            print(f"\n  [{done}/{total}] Write '{ch}' on touchpad → ", end="", flush=True)
            sys.stdin.readline()
            time.sleep(0.15)
            strokes_frac = cap.read_and_clear()
            if not strokes_frac:
                print("  (no strokes detected, skipping)")
                continue

            t0 = time.time()
            tegaki_cands = classify_strokes(libz, tegaki_rec, strokes_frac)
            t1 = time.time()
            community_cands = classify_strokes(libz, community_rec, strokes_frac)
            t2 = time.time()

            t_top1 = tegaki_cands[0] if tegaki_cands else ("?", 0)
            c_top1 = community_cands[0] if community_cands else ("?", 0)
            t_hit = " ✓" if t_top1[0] == ch else ""
            c_hit = " ✓" if c_top1[0] == ch else ""
            t_top5 = any(c[0] == ch for c in tegaki_cands[:5])
            c_top5 = any(c[0] == ch for c in community_cands[:5])
            t_flag = "✓" if t_hit else ("T5" if t_top5 else " ")
            c_flag = "✓" if c_hit else ("T5" if c_top5 else " ")

            print(f"Tegaki:     '{t_top1[0]}' ({t_top1[1]:.2f}) [{t_flag}]  "
                  f"幽兰百合: '{c_top1[0]}' ({c_top1[1]:.2f}) [{c_flag}]  "
                  f"({(t2-t0)*1000:.0f}ms)")

            # Show top-5 for misses
            if not t_hit:
                t5 = ", ".join(f"'{c[0]}'({c[1]:.2f})" for c in tegaki_cands[:5])
                print(f"         Tegaki top-5: {t5}")
            if not c_hit:
                c5 = ", ".join(f"'{c[0]}'({c[1]:.2f})" for c in community_cands[:5])
                print(f"         幽兰百合 top-5: {c5}")

            results.append({
                "char": ch,
                "category": category,
                "strokes": strokes_frac,
                "tegaki": [(c, round(s, 4)) for c, s in tegaki_cands[:5]],
                "community": [(c, round(s, 4)) for c, s in community_cands[:5]],
                "tegaki_top1_hit": bool(t_hit),
                "community_top1_hit": bool(c_hit),
                "tegaki_top5_hit": t_top5,
                "community_top5_hit": c_top5,
                "latency_ms": round((t2 - t0) * 1000, 1),
            })

    cap.stop()

    # ── Save ──
    with open(SAVE_FILE, "w") as f:
        json.dump({"models": {"tegaki": TEGAKI_CN, "community": COMMUNITY}, "results": results}, f, ensure_ascii=False, indent=1)
    print(f"\n  Saved: {SAVE_FILE}")

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print("  RESULTS SUMMARY")
    print(f"{'=' * 60}")

    for category, chars in TEST_CHARS.items():
        cat_results = [r for r in results if r["category"] == category]
        n = len(cat_results)
        t1 = sum(1 for r in cat_results if r["tegaki_top1_hit"])
        t5 = sum(1 for r in cat_results if r["tegaki_top5_hit"])
        c1 = sum(1 for r in cat_results if r["community_top1_hit"])
        c5 = sum(1 for r in cat_results if r["community_top5_hit"])
        print(f"\n  {category}:")
        print(f"    {'':22s} {'Tegaki CN':>12s} {'幽兰百合':>12s}")
        print(f"    {'Top-1 hit':22s} {t1:3d}/{n:2d} ({t1/n*100:3.0f}%){c1:3d}/{n:2d} ({c1/n*100:3.0f}%)")
        print(f"    {'Top-5 hit':22s} {t5:3d}/{n:2d} ({t5/n*100:3.0f}%){c5:3d}/{n:2d} ({c5/n*100:3.0f}%)")

    t1_all = sum(1 for r in results if r["tegaki_top1_hit"])
    t5_all = sum(1 for r in results if r["tegaki_top5_hit"])
    c1_all = sum(1 for r in results if r["community_top1_hit"])
    c5_all = sum(1 for r in results if r["community_top5_hit"])
    n_all = len(results)
    print(f"\n  {'─' * 46}")
    print(f"  {'TOTAL':22s} {'Tegaki CN':>12s} {'幽兰百合':>12s}")
    print(f"    {'Top-1 hit':22s} {t1_all:3d}/{n_all:2d} ({t1_all/n_all*100:3.0f}%){c1_all:3d}/{n_all:2d} ({c1_all/n_all*100:3.0f}%)")
    print(f"    {'Top-5 hit':22s} {t5_all:3d}/{n_all:2d} ({t5_all/n_all*100:3.0f}%){c5_all:3d}/{n_all:2d} ({c5_all/n_all*100:3.0f}%)")

    # Per-char detail
    print(f"\n  Detail:")
    print(f"    {'Char':6s} {'Tegaki CN top-1':>20s}  {'幽兰百合 top-1':>20s}")
    print(f"    {'─' * 48}")
    for r in results:
        tc = r["tegaki"][0] if r["tegaki"] else ("?", 0)
        cc = r["community"][0] if r["community"] else ("?", 0)
        tm = "✓" if r["tegaki_top1_hit"] else " "
        cm = "✓" if r["community_top1_hit"] else " "
        print(f"    {r['char']:6s} {tm} {tc[0]:6s} ({tc[1]:.2f}){'':8s} {cm} {cc[0]:6s} ({cc[1]:.2f})")

    # Cleanup
    libz.zinnia_recognizer_destroy(tegaki_rec)
    libz.zinnia_recognizer_destroy(community_rec)

    print(f"\n  Done! Results saved to {SAVE_FILE}")

if __name__ == "__main__":
    main()
