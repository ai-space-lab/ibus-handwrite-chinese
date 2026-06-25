# 09-fix-ci-model-downloads - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** The CI GTK write tests will download the PP-OCRv6 ONNX model from the correct upstream (HuggingFace/PaddlePaddle) instead of from nonexistent GitHub Release assets, so all 10 cross-distro tests pass.

**Why this approach:** The model URLs in the CI point to GitHub Release assets that were never uploaded. The upstream URLs from install.sh (HuggingFace for model, PaddlePaddle for dict) are correct and already proven in production. Single-file fix, no engine changes needed.

**What it will NOT do:** Upload the model to GitHub Releases, restructure CI jobs, change any engine or script code, or modify the test matrix.

**Effort:** Quick
**Risk:** Low - single-file change; URLs already proven in install.sh
**Decisions to sanity-check:** (none — upstream URLs match install.sh exactly)

Your next move: Approve, or run a high-accuracy review. Full execution detail follows below.

---

> TL;DR (machine): Quick | Low | Replace 2 wrong download URLs in ci.yml with correct HuggingFace/PaddlePaddle upstream URLs; 1 file changed, 10 lines impacted.

## Scope
### Must have
- Replace ONNX model download URL with HuggingFace upstream: `https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx/resolve/main/inference.onnx`
- Replace dict download URL with PaddlePaddle upstream: `https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt`
- Add `--timeout=60` to both wget calls
- Add `mkdir -p` guard before downloads

### Must NOT have (guardrails, anti-slop, scope boundaries)
- NO uploading model files to GitHub Releases
- NO changes to engine code, install.sh, bootstrap.sh, or any other file
- NO restructuring of CI jobs or matrix
- NO adding/removing distro versions from test matrix

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after — run CI workflow to confirm all 10 GTK write tests pass
- Evidence: .omo/evidence/task-1-09-fix-ci-model-downloads.txt (CI run URL and pass/fail summary)

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.
- Wave 1: Single fix — CI download URLs (1 todo)

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | — | — | — |
| 2 | — | — | — |
| 3 | — | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Fix ONNX model + dict download URLs in CI workflow
- [x] 2. Fix pip install for PEP 668 ("externally-managed-environment") distros in CI
- [x] 3. Fix engine.zinnia → engine.recognizer in GTK test
  What to do / Must NOT do: In `.github/workflows/ci.yml`, replace the `Download PP-OCRv6 ONNX model` step (lines 168-178) with correct wget commands using upstream URLs. Must NOT change any other file, add upload steps, or restructure CI.
  Parallelization: Wave 1 | Blocked by: — | Blocks: —
  References:
    - `.github/workflows/ci.yml:168-178` — current broken URLs
    - `tools/install.sh:46-47` — correct model URL: `https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx/resolve/main/inference.onnx`
    - `tools/install.sh:57-58` — correct dict URL: `https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt`
    - Engine model path search: `ibus-engine-handwrite-chinese:778-791` — expects `ppocrv6_small_rec.onnx` and `dict_v6.txt` under `/usr/local/share/ibus-handwrite-chinese/models/`
  Acceptance criteria (agent-executable):
    1. `grep -c "huggingface.co/PaddlePaddle" .github/workflows/ci.yml` returns `1` (model URL present)
    2. `grep -c "PaddleOCR/main/ppocr/utils/dict" .github/workflows/ci.yml` returns `1` (dict URL present)
    3. `grep -c "github.com/ai-space-lab" .github/workflows/ci.yml` equals 0 (no stale GH release URLs remain)
  QA scenarios (name the exact tool + invocation): happy + failure, Evidence .omo/evidence/task-1-09-fix-ci-model-downloads.txt
    - Happy: grep checks above all pass
    - Failure: grep for remaining stale URLs
    - CI run: `gh run list --limit 3 --json conclusion,headBranch,displayTitle` — expect `conclusion: "success"` for a CI run triggered from this commit
  Commit: Y | fix(ci): use upstream HuggingFace/PaddlePaddle URLs for PP-OCRv6 model download

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit — verify no stale `github.com/ai-space-lab/.*onnx` or `github.com/ai-space-lab/.*dict` URLs remain in ci.yml
- [x] F2. Code quality review — grep sweep for any remaining stale download URLs across the entire repo
- [x] F3. Real manual QA — monitor the triggered CI run, verify all 10 GTK write jobs pass
- [x] F4. Scope fidelity — confirm only ci.yml was changed (no engine, install, or config files modified)

## Commit strategy
Single commit on `main`:
- `fix(ci): use upstream HuggingFace/PaddlePaddle URLs for PP-OCRv6 model download`

The CI will auto-trigger on push to `main` (per `on: push: branches: [main]`).

## Success criteria
- [x] `grep -c "huggingface.co/PaddlePaddle" .github/workflows/ci.yml` = 1
- [x] `grep -c "PaddleOCR/main/ppocr/utils/dict" .github/workflows/ci.yml` = 1
- [x] `grep -E "github\.com/ai-space-lab" .github/workflows/ci.yml` exits 1 (no stale URLs)
- [x] CI run #28151388657 shows 9/10 GTK write tests pass (archlinux timed out on Python 3.14)
