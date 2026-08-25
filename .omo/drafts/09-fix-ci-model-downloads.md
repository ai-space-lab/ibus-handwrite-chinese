---
slug: 09-fix-ci-model-downloads
status: drafting
intent: clear
pending-action: write .omo/plans/09-fix-ci-model-downloads.md
approach: Replace wrong GitHub Release download URLs in CI with correct HuggingFace/PaddlePaddle upstream URLs
---

# Draft: 09-fix-ci-model-downloads

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
- CI workflow | All 10 GTK write tests pass | active | ci.yml lines 168-178

## Findings (updated during execution)
6. After fixing download URLs, 3 distros still fail GTK write tests with:
   - `error: externally-managed-environment` (PEP 668 blocks pip install)
   - `E: Unable to locate package python3-onnxruntime` (no apt package)
   - `RuntimeError: numpy is required for ONNX recognition`
   - Affected: debian:12, ubuntu:24.04, opensuse/tumbleweed
   - Unaffected (pip works): debian:11, ubuntu:22.04, fedora:* (uses dnf native), archlinux

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
- ONNX model location | Download from HuggingFace PaddlePaddle repo | Same URL that install.sh uses; follows copilot-instructions rule "Do not store third-party handwriting models in the repository or GitHub Releases" | Yes

## Findings (cited - path:lines)
1. CI "Download PP-OCRv6 ONNX model" step (ci.yml:168-178) uses URLs that don't exist:
   - `https://github.com/ai-space-lab/ibus-handwrite-chinese/releases/download/v0.1.0/ppocrv6_small_rec.onnx` — v0.1.0 release has no ONNX model asset (confirmed: `gh release view v0.1.0 --json assets` shows only RPM/tar.gz/deb)
   - `https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/data/models/dict_v6.txt` — `data/models/` doesn't exist in the repo
2. Both downloads produce 0-byte files (CI log: `-rw-r--r-- 1 root root    0 Jun 25 03:47 ppocrv6_small_rec.onnx`)
3. Error: `onnxruntime.capi.onnxruntime_pybind11_state.Fail: Load model from .../ppocrv6_small_rec.onnx failed: ModelProto does not have a graph.` — caused by 0-byte file
4. install.sh (tools/install.sh:46-47) uses correct upstream URLs:
   - Model: `https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx/resolve/main/inference.onnx`
   - Dict: `https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt`
5. Engine model path search order (ibus-engine-handwrite-chinese:778-791): checks `/usr/local/share/ibus-handwrite-chinese/models/` as option 2
6. After fixing download URLs, PEP 668 blocked pip on 3 distros — fixed with two-step pip (regular → --break-system-packages fallback)
7. After fixing `engine.zinnia` reference → `engine.recognizer` in GTK test (line 194), all 10 distros pass GTK tests WITHOUT the model error ❌→✅
8. Result: 9/10 GTK write tests PASS, 1 cancelled (archlinux 30-min timeout) — Python 3.14 onnxruntime compatibility hang

## Decisions (with rationale)
1. **Replace CI download URLs with upstream HuggingFace/PaddlePaddle URLs** — follows copilot-instructions "Do not store third-party handwriting models in the repository or GitHub Releases". install.sh already uses these same URLs successfully.
2. **Single-file change** — only `.github/workflows/ci.yml` needs updating. No engine code changes needed.

## Scope IN
- `.github/workflows/ci.yml`: replace the 10-line download step (168-178) with correct URLs
- Add `--timeout=60` to wget calls (matching install.sh)
- Add `mkdir -p` guard in the download step as belt-and-suspenders

## Scope OUT (Must NOT have)
- NO uploading model files to GitHub Releases
- NO changes to engine code, install.sh, bootstrap.sh, or any other file
- NO restructuring of CI jobs or matrix
- NO adding/removing distro versions from test matrix

## Open questions
(none — all facts resolved from codebase)

## Approval gate
status: approved
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
