#!/usr/bin/env python3
"""Compare handwriting recognition accuracy: tegaki vs 幽兰百合 30k model."""

import ctypes
import os
import sys
import time

TEGAKI_CN = "/usr/share/tegaki/models/zinnia/handwriting-zh_CN.model"
TEGAKI_TW = "/usr/share/tegaki/models/zinnia/handwriting-zh_TW.model"
COMMUNITY = "/tmp/handwriting-model-community/ZJHandWriting-zh_CN.model"

W, H = 300, 300


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
    libz.zinnia_recognizer_size.restype = ctypes.c_uint
    libz.zinnia_recognizer_size.argtypes = [ctypes.c_void_p]
    libz.zinnia_recognizer_value.restype = ctypes.c_char_p
    libz.zinnia_recognizer_value.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

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
    r = libz.zinnia_recognizer_new()
    if not r:
        return None
    if not libz.zinnia_recognizer_open(r, path.encode()):
        libz.zinnia_recognizer_destroy(r)
        return None
    return r


def get_chars(libz, recognizer):
    n = libz.zinnia_recognizer_size(recognizer)
    chars = set()
    for i in range(n):
        cv = libz.zinnia_recognizer_value(recognizer, i)
        if cv:
            chars.add(cv.decode("utf-8"))
    return chars


def classify(libz, recognizer, strokes, nbest=96):
    char = libz.zinnia_character_new()
    libz.zinnia_character_set_width(char, W)
    libz.zinnia_character_set_height(char, H)
    for sid, points in enumerate(strokes):
        for x, y in points:
            libz.zinnia_character_add(char, sid, x, y)
    result = libz.zinnia_recognizer_classify(recognizer, char, nbest)
    candidates = []
    if result:
        n = libz.zinnia_result_size(result)
        for i in range(n):
            cv = libz.zinnia_result_value(result, i)
            s = libz.zinnia_result_score(result, i)
            c = cv.decode("utf-8", errors="replace") if cv else "<null>"
            candidates.append((c, s))
        libz.zinnia_result_destroy(result)
    libz.zinnia_character_destroy(char)
    return candidates


def make_stroke(x1, y1, x2, y2, steps=10):
    xs = [int(x1 + (x2 - x1) * t / steps) for t in range(steps + 1)]
    ys = [int(y1 + (y2 - y1) * t / steps) for t in range(steps + 1)]
    return list(zip(xs, ys))


def make_horizontal(y, x1=50, x2=250, steps=10):
    return make_stroke(x1, y, x2, y, steps)


def make_vertical(x, y1=50, y2=250, steps=10):
    return make_stroke(x, y1, x, y2, steps)


def make_diag(x1, y1, x2, y2, steps=10):
    return make_stroke(x1, y1, x2, y2, steps)


STROKE_DEFS = {
    "一": [make_horizontal(150)],
    "丨": [make_vertical(150)],
    "十": [make_horizontal(150), make_vertical(150)],
    "人": [make_diag(150, 50, 80, 250), make_diag(150, 60, 220, 250)],
    "八": [make_diag(100, 50, 70, 250), make_diag(200, 50, 230, 250)],
    "大": [make_horizontal(150), make_diag(150, 150, 80, 250), make_diag(150, 160, 220, 250)],
    "小": [make_stroke(150, 50, 150, 200), make_stroke(80, 80, 130, 150), make_stroke(170, 80, 220, 150)],
    "下": [make_horizontal(80), make_vertical(150, 80, 250), make_stroke(180, 200, 200, 220)],
    "上": [make_horizontal(80), make_vertical(150, 80, 250), make_horizontal(250)],
    "中": [make_vertical(150), make_stroke(80, 80, 220, 80, 5), make_stroke(220, 80, 220, 220, 5),
           make_horizontal(220)],
    "口": [make_vertical(80, 80, 220), make_stroke(80, 80, 220, 80, 5), make_stroke(220, 80, 220, 220, 5),
           make_horizontal(220, 80, 220)],
    "山": [make_vertical(80, 80, 220), make_stroke(80, 220, 220, 220), make_vertical(220, 80, 220)],
    "木": [make_horizontal(150), make_vertical(150), make_diag(150, 150, 80, 250), make_diag(150, 160, 220, 250)],
    "火": [make_stroke(150, 50, 150, 80), make_stroke(150, 80, 80, 220), make_stroke(150, 100, 220, 220)],
    "王": [make_horizontal(80), make_horizontal(150), make_vertical(150, 80, 220), make_horizontal(220)],
    "田": [make_vertical(80, 80, 220), make_stroke(80, 80, 220, 80, 5), make_stroke(220, 80, 220, 220, 5),
           make_horizontal(220, 80, 220), make_horizontal(150, 80, 220), make_vertical(150, 80, 220)],
    "力": [make_stroke(180, 50, 220, 50, 5), make_stroke(220, 50, 220, 200, 5), make_stroke(220, 200, 80, 200),
           make_diag(220, 200, 170, 250)],
    "文": [make_stroke(150, 50, 150, 80), make_horizontal(80), make_diag(150, 80, 80, 250), make_diag(150, 90, 220, 250)],
    "天": [make_horizontal(80), make_horizontal(130), make_diag(150, 130, 80, 250), make_diag(150, 140, 220, 250)],
    "不": [make_horizontal(80), make_diag(150, 80, 80, 200), make_vertical(150, 100, 250), make_stroke(180, 200, 220, 220)],
    "生": [make_diag(150, 50, 130, 80), make_horizontal(80), make_horizontal(150),
           make_vertical(150, 80, 220), make_horizontal(220)],
    "水": [make_stroke(150, 50, 150, 200), make_stroke(120, 100, 80, 180), make_stroke(120, 100, 180, 80),
           make_stroke(160, 120, 220, 220)],
    "月": [make_diag(200, 50, 80, 50), make_stroke(80, 50, 80, 250, 5), make_stroke(80, 250, 220, 250, 5),
           make_horizontal(120, 80, 200), make_horizontal(180, 80, 200)],
    "日": [make_vertical(80, 80, 220), make_stroke(80, 80, 220, 80, 5), make_stroke(220, 80, 220, 220, 5),
           make_horizontal(220, 80, 220), make_horizontal(150, 80, 220)],
}


def run_accuracy_test(libz, recognizers, strokes_def, label):
    results = {}
    for name, rec in recognizers.items():
        hits = misses = 0
        details = []
        for char, strokes in strokes_def.items():
            candidates = classify(libz, rec, strokes, nbest=10)
            top1 = candidates[0][0] if candidates else "?"
            top5 = [c[0] for c in candidates[:5]]
            hit = "TOP1" if top1 == char else ("TOP5" if char in top5 else "MISS")
            if hit == "TOP1":
                hits += 1
            elif hit == "TOP5":
                hits += 0.5
            score = candidates[0][1] if candidates else 0
            details.append((char, top1, score, hit, top5))
        acc = hits / len(strokes_def) * 100
        results[name] = {"accuracy": acc, "details": details}
    return results


def run_speed_test(libz, recognizers, n_iterations=500):
    strokes = STROKE_DEFS["十"]
    results = {}
    for name, rec in recognizers.items():
        times = []
        for _ in range(n_iterations):
            t0 = time.time()
            classify(libz, rec, strokes)
            t1 = time.time()
            times.append((t1 - t0) * 1000)
        avg = sum(times) / len(times)
        median = sorted(times)[len(times) // 2]
        results[name] = {"avg_ms": avg, "median_ms": median, "min_ms": min(times), "max_ms": max(times)}
    return results


def find_oov_chars(community_chars, tegaki_chars):
    return community_chars - tegaki_chars


def main():
    libz = load_zinnia()
    setup_signatures(libz)

    models = {
        "Tegaki zh_CN": TEGAKI_CN,
        "Tegaki zh_TW": TEGAKI_TW,
        "幽兰百合 Community": COMMUNITY,
    }

    recognizers = {}
    chars = {}
    for name, path in models.items():
        if not os.path.exists(path):
            print(f"SKIP {name}: model not found at {path}")
            continue
        rec = open_model(libz, path)
        if not rec:
            print(f"FAIL {name}: could not open model")
            continue
        recognizers[name] = rec
        chars[name] = get_chars(libz, rec)
        print(f"  {name}: {len(chars[name])} chars ({os.path.getsize(path) / 1024 / 1024:.0f} MB)")

    if len(recognizers) < 2:
        print("Need at least 2 models for comparison")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("COVERAGE COMPARISON")
    print("=" * 60)

    cn_chars = chars.get("Tegaki zh_CN", set())
    tw_chars = chars.get("Tegaki zh_TW", set())
    cm_chars = chars.get("幽兰百合 Community", set())

    print(f"\nTegaki zh_CN:         {len(cn_chars):>6} unique chars")
    print(f"Tegaki zh_TW:         {len(tw_chars):>6} unique chars")
    print(f"幽兰百合 Community:    {len(cm_chars):>6} unique chars")

    cn_tw_union = cn_chars | tw_chars
    print(f"Tegaki CN + TW union: {len(cn_tw_union):>6} unique chars")

    common_cn_cm = cn_chars & cm_chars
    cm_only = cm_chars - cn_chars
    cm_only_vs_all = cm_chars - cn_tw_union

    print(f"\nCommon (Tegaki CN ∩ 幽兰百合): {len(common_cn_cm)} chars ({len(common_cn_cm)/len(cm_chars)*100:.0f}% of 幽兰百合)")
    print(f"Chars in 幽兰百合 but NOT in Tegaki CN: {len(cm_only)}")
    print(f"Chars in 幽兰百合 but NOT in Tegaki CN+TW: {len(cm_only_vs_all)}")

    cn_not_cm = cn_chars - cm_chars
    print(f"Chars in Tegaki CN but NOT in 幽兰百合: {len(cn_not_cm)}")

    if cn_not_cm:
        sample = sorted(cn_not_cm)[:10]
        print(f"  Sample (Tegaki only): {', '.join(sample)}")
    if cm_only:
        sample = sorted(cm_only)[:15]
        print(f"  Sample (幽兰百合 only): {', '.join(sample)}")

    print("\n" + "=" * 60)
    print("ACCURACY TEST — Synthetic Strokes")
    print("=" * 60)

    results = run_accuracy_test(libz, recognizers, STROKE_DEFS, "strokes")

    headers = ["Char", "Expected"] + list(recognizers.keys())
    acc_row = ["ACCURACY", ""]
    for name in recognizers:
        r = results[name]
        acc_row.append(f"{r['accuracy']:.0f}%")
    print(f"\n{' | '.join(headers)}")
    print(f"{' | '.join(acc_row)}")

    details_rows = []
    for char in STROKE_DEFS:
        row = [char, char]
        for name in recognizers:
            r = results[name]
            d = next((d for d in r["details"] if d[0] == char), None)
            if d:
                row.append(f"{d[1]} ({d[2]:.2f})")
            else:
                row.append("?")
        details_rows.append(row)

    print("\nPer-character top-1:")
    for row in details_rows:
        print(f"  {row[0]:4s} → {' | '.join(row[2:])}")

    print("\nTop-1 hit details:")
    for name in recognizers:
        hits = [d[0] for d in results[name]["details"] if d[3] == "TOP1"]
        misses = [d[0] for d in results[name]["details"] if d[3] != "TOP1"]
        print(f"  {name}:")
        print(f"    TOP1: {', '.join(hits) if hits else 'none'}")
        print(f"    MISS: {', '.join(misses) if misses else 'none'}")

    print("\n" + "=" * 60)
    print("OOV VERIFICATION")
    print("=" * 60)

    oov_list = sorted(cm_only_vs_all)[:20]
    if oov_list:
        print(f"\nTesting {len(oov_list)} chars that 幽兰百合 has but Tegaki CN+TW lacks:")
        cm_rec = recognizers.get("幽兰百合 Community")
        cn_rec = recognizers.get("Tegaki zh_CN")
        tw_rec = recognizers.get("Tegaki zh_TW")

        for ch in oov_list:
            print(f"\n  '{ch}':")
            for label, rec in [("Tegaki CN", cn_rec), ("Tegaki TW", tw_rec), ("幽兰百合", cm_rec)]:
                if not rec:
                    continue
                strokes = [make_horizontal(150), make_vertical(150)]
                candidates = classify(libz, rec, strokes, nbest=5)
                top_str = ", ".join([f"'{c[0]}'({c[1]:.2f})" for c in candidates[:3]]) if candidates else "none"
                ch_in_top5 = any(c[0] == ch for c in candidates[:5])
                marker = " ✓" if ch_in_top5 else ""
                print(f"    {label:14s}: {top_str}{marker}")
    else:
        print("  (no OOV chars found)")

    print("\n" + "=" * 60)
    print("SPEED BENCHMARK")
    print("=" * 60)

    speed_results = run_speed_test(libz, recognizers, n_iterations=300)
    for name, sr in speed_results.items():
        print(f"  {name:25s}: avg={sr['avg_ms']:.3f}ms  median={sr['median_ms']:.3f}ms  "
              f"min={sr['min_ms']:.3f}ms  max={sr['max_ms']:.3f}ms")

    for name, rec in recognizers.items():
        libz.zinnia_recognizer_destroy(rec)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if cm_chars:
        print(f"  幽兰百合 covers {len(cm_chars)} chars vs {len(cn_chars)} for Tegaki CN "
              f"(+{len(cm_chars) - len(cn_chars)} chars, {((len(cm_chars)/len(cn_chars))-1)*100:.0f}% more)")
        print(f"  OOV chars vs Tegaki CN:     {len(cm_only)}")
        print(f"  OOV chars vs Tegaki CN+TW:  {len(cm_only_vs_all)}")

    if "幽兰百合 Community" in results and "Tegaki zh_CN" in results:
        cm_acc = results["幽兰百合 Community"]["accuracy"]
        cn_acc = results["Tegaki zh_CN"]["accuracy"]
        diff = cm_acc - cn_acc
        print(f"  Synthetic stroke accuracy: 幽兰百合={cm_acc:.0f}% vs Tegaki CN={cn_acc:.0f}% ({diff:+.0f}%)")

    if "幽兰百合 Community" in speed_results and "Tegaki zh_CN" in speed_results:
        cm_sp = speed_results["幽兰百合 Community"]["avg_ms"]
        cn_sp = speed_results["Tegaki zh_CN"]["avg_ms"]
        ratio = cm_sp / cn_sp if cn_sp else 0
        print(f"  Recognition speed: 幽兰百合={cm_sp:.2f}ms vs Tegaki CN={cn_sp:.2f}ms ({ratio:.1f}x)")


if __name__ == "__main__":
    main()
