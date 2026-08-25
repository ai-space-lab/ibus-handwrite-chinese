# Learnings — get-users-now

Conventions, patterns, and successful approaches discovered during work on this plan.

_Auto-scaffolded by /start-work. Append new entries below - never overwrite._

---

## B1.2 — docs/index.md (GitHub Pages install page)

Created `docs/index.md`, the primary install landing page.

- One-line installer at top with an HTML copy button (clipboard JS) plus a
  fenced code block. Exact command reused from README:
  `bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh)` then `ibus restart`.
- Demo GIF embedded as `![demo](assets/demo.gif)` (user-supplied, B1.1).
- Distro tabs (Material `===`): Debian/Ubuntu/Mint (`.deb` + `dpkg -i`),
  Fedora (`.rpm` + `rpm -i`), Arch (AUR "coming soon" + PKGBUILD note),
  openSUSE (`.rpm` from GitHub Release). Commands match README Packages table.
- Troubleshooting accordion (Material `???` details): trackpad/input group/udev,
  engine not found / IBus restart, IBus restart / switch key, model download /
  onnxruntime. Self-contained, no version numbers hardcoded.
- Screenshots gallery references `assets/*.png` (user-supplied, B2.1).

Assumptions:
- mkdocs.yml (B1.3) will enable `pymdownx.tabbed` + `pymdownx.details`
  (both default in MkDocs Material) and reference this file as `index.md` in nav.
- `assets/` directory will be created alongside the user's GIF/screenshots.

GIF and screenshots are NOT created here — they are recorded by the user on
MacBook Pro (B1.1 / B2.1) and dropped into `docs/assets/`. The page is complete
without them; the image links resolve once those files exist.

No other files modified (README, bootstrap.sh untouched).

---

## B1.3 — mkdocs.yml + pages.yml (GitHub Pages deploy)

Created `mkdocs.yml` (repo root) and `.github/workflows/pages.yml` for
auto-deploy to GitHub Pages at
`https://ai-space-lab.github.io/ibus-handwrite-chinese/`.

**mkdocs.yml:**
- `site_name: ibus-handwrite-chinese`, `site_url`, `repo_url`, `repo_name` set.
- Material theme: dark/light toggle (teal/amber), `navigation.tabs`,
  `content.code.copy`. (Dropped `navigation.sections`, `search.highlight`,
  `content.tabs.link` from the plan template to stay minimal — only the
  required features kept.)
- `plugins`: `search` + `i18n`. **Used v1.x i18n syntax** (`languages:` list
  with `locale:` + `default: true`), NOT the plan template's `default_language:`
  key — that key is deprecated/removed in mkdocs-static-i18n >=1.0 and breaks
  the build. `docs_structure: suffix` so `index.md` = English, `index.zh.md` =
  Chinese (zh falls back to en via `fallback_to_default`, default true).
- `nav`: Home (`index.md`), Configure, FAQ, Troubleshooting, Changelog.
- `extra_javascript`: GoatCounter `https://gc.zgoat.net/count.js` (account
  created by user later at goatcounter.com).
- `docs_dir` left default (`docs/`) so `docs/index.md` (B1.2) is picked up.
- `markdown_extensions`: pymdownx.highlight/superfences/tabbed, admonition,
  attr_list, md_in_html (supports B1.2's `===` tabs + `???` details).

**pages.yml:** separate workflow (does not touch ci.yml/release.yml). Triggers
on push to `main` + manual dispatch. Uses `actions/checkout@v4`,
`actions/setup-python@v5`, `pip install mkdocs-material mkdocs-static-i18n`,
then `mkdocs gh-deploy --force`. `permissions: contents: write` for gh-deploy.

**Stub pages created:** `docs/configure.md`, `docs/faq.md`,
`docs/troubleshooting.md`, `docs/changelog.md` (H1 + one TODO line each) so the
build passes. `docs/index.md` already existed (B1.2 real content) — left
untouched.

**Verification:** `mkdocs build` exits 0 (verified in a venv with
mkdocs-material + mkdocs-static-i18n installed). Both `en` and `zh` built.
`--strict` mode aborts only on warnings (not errors): missing `docs/assets/*.png`
+ `demo.gif` (B1.1/B2.1, user-supplied later) and pre-existing docs not in nav
(ARCHITECTURE.md, DEPENDENCIES.md, plan-*.md). None caused by this config.

**mkdocs version used:** mkdocs-material + mkdocs-static-i18n latest from PyPI
(unpinned, matching the workflow's `pip install`).

---

## B1.4 — README Quick Install moved to top

Reordered `README.md` so install is the first thing visitors see.

- **Moved**: the entire `## Quick Install` block (bootstrap one-liner + `ibus
  restart`, Debian traditional method, `install.sh` notes, switch-back command)
  from its old spot (after Requirements) to immediately after the title/CI
  badges/screenshot, before `## Features`.
- **Embedded demo GIF**: `![demo](docs/assets/demo.gif)` at the top of Quick
  Install (user-recorded in B1.1, referenced only — file not created here).
- **Decision tree added** ("Which install method for me?") as a 3-question
  nested list:
  1. Which distro? → Debian/Ubuntu/Mint, Fedora, Arch/Manjaro, openSUSE (each
     points to bootstrap.sh auto or a package)
  2. One command or package? → bootstrap.sh (recommended) vs `.deb`/`.rpm`
  3. From source? → clone + `install.sh` vs stick with bootstrap/package
  Plus a blockquote linking to the [Full install guide](docs/index.md) (B1.2).
- **Troubleshooting Quick Links** added at the bottom of Quick Install:
  trackpad permissions (input group / udevadm trigger), IBus won't start
  (`ibus restart` + `ibus engine handwrite-chinese`), model download
  (preference dialog / `#troubleshooting` anchor).
- **Preserved**: every original section kept intact and only reordered —
  Features, Cross-Distro Support, Requirements, Packages, Usage,
  Troubleshooting, Testing, Known Limitations, Acknowledgments, License,
  Configuration, Repository Structure. No commands changed, no src/ or
  tools/ files touched.

Verification: `grep "^## "` shows Quick Install at line 12, Features at 70,
all other headings follow in original order.

---

## B2.3 — OG social preview image (docs/assets/og-image.png) — BLOCKED

Attempted to create the 1280×640 Open Graph preview image from
`docs/screenshot.png` via ImageMagick.

- **ImageMagick available?** NO. Both `command -v magick` and
  `command -v convert` returned exit code 1 (not installed on this host).
- **Command intended:** `magick docs/screenshot.png -resize 1280x640^
  -gravity center -extent 1280x640 docs/assets/og-image.png`
  (or `convert` if only that existed).
- **Output dimensions:** N/A — file NOT created.
- **Fallback:** None applied. Per task rules, did NOT substitute another
  tool (sips/ffmpeg/Python PIL/sharp) without confirmation.
- **Source confirmed:** `docs/screenshot.png` exists (94.9K, 664 perms).
- **Action needed:** Install ImageMagick (`apt install imagemagick` /
  `brew install imagemagick`) or approve a substitute tool, then re-run the
  resize command and verify with `identify -format "%wx%h"`.

---

## B1.5 — tools/install.sh: trackpad auto-detection + post-install engine verify

Surgical additions to `tools/install.sh` (no rewrite, no deps changed, no
model-download/venv logic touched, `--skip-deps` behavior preserved).

**Added 1 — trackpad auto-detection (after dep check, before model download):**
- New block `=== Detecting trackpad (auto-detection) ===` inserted right after
  the `SKIP_DEPS` block (before `[PP-OCR]` download).
- Guards on `python3` + `import evdev` so it no-ops gracefully on distros where
  python3-evdev isn't installed yet (non-Debian) instead of failing.
- Runs `bash "$SCRIPT_DIR/diagnose_trackpad.sh"` (captured, `2>/dev/null || true`
  so the script's `set -e` can't abort install), then extracts the device name
  from the "Trackpad(s) matching CURRENT filter" section via grep/sed.
- Prints `Detected trackpad: <device>` or a clear "no trackpad / mouse fallback"
  or "python3-evdev not available" message.

**Added 2 — post-install engine registration verify (after install complete):**
- New block `=== Verifying IBus engine registration ===` appended at end of
  script (after the existing "LOG OUT and BACK IN" warning).
- Mirrors the same display/D-Bus guards used by the SET_ENGINE block
  (`DISPLAY`/`WAYLAND_DISPLAY` and `DBUS_SESSION_BUS_ADDRESS`); if absent, prints
  a skip note + the hint instead of running `ibus`.
- Adds `sleep 2` before checking (per requirement — runs after the script's own
  `ibus restart`).
- Runs `ibus list-engine | grep -q handwrite-chinese` as the real user (uses
  `su -c` when running as root for a non-root REAL_USER, matching existing style).
- On success: `✓ Engine registered (handwrite-chinese)`. On failure:
  `✗ Engine NOT registered` + hint `Run: ibus restart, then ibus engine handwrite-chinese`.

**Verification:**
- `shellcheck -e SC1091 tools/install.sh` → passes, no errors (shellcheck-py
  0.11.0.1 used locally; CI uses the same `-e SC1091` flag).
- `bash -n tools/install.sh` → syntax OK.
- `diagnose_trackpad.sh` was NOT modified (requirement).

**Edge cases found / handled:**
- `diagnose_trackpad.sh` has `set -e` and may exit non-zero (e.g. missing
  getfacl, no event devices) — wrapped in `|| true` so install continues.
- evdev may be absent pre-install on non-Debian distros — guarded, skips cleanly.
- No display / no D-Bus (CI, headless) — verify block skips and prints hint
  rather than erroring, so cross-distro CI (Debian/Fedora/Arch/openSUSE) stays
  green.
- The `grep -A2` + `head -1` extraction only captures CURRENT-filter devices,
  not the FIXED-filter "would match" lines (which appear later, beyond the 2-line
  window), avoiding false positives.

---

## B2.4 — README.zh-Hans-汉.md install parity with English README

Brought the Simplified-Chinese README in line with the English README (B1.4).

**Was it already matching?** NO. The Chinese README predated B1.4: its `## 快速安装`
(Quick Install) sat *after* `## 功能特点` (Features) at roughly line 56, and it
lacked the demo GIF, the decision tree, and the troubleshooting quick links.

**What was changed (surgical — install section only):**
- **Moved** Quick Install to the top, immediately after the screenshot and before
  `## 功能特点`, mirroring the English structure.
- **Added** `![demo](docs/assets/demo.gif)` at the top of Quick Install.
- **Added** the 3-question decision tree `### 我该用哪种安装方式？` (distro →
  one-command-vs-package → source-or-not), translated to natural Simplified Chinese.
- **Added** `### 故障排除快速链接` (Troubleshooting Quick Links): 触控板权限
  (input group / udevadm trigger), IBus 无法启动 (`ibus restart` + `ibus engine
  handwrite-chinese`), 模型下载 (preference dialog / `#故障排除` anchor).
- **Removed** the old, now-duplicate Quick Install block that was buried lower in
  the file (it had a simpler one-liner + Debian traditional method + a stray
  `ibus engine handwrite-chinese` switch command). The Debian traditional method
  and switch-back command were preserved inside the new top Quick Install block.
- **Preserved** all other Chinese content untouched: 功能特点, 跨发行版支持,
  系统要求, 软件包, 使用方法, 故障排除, 测试, 已知限制, 致谢, 许可协议, 配置,
  目录结构.

**Parity confirmed:**
- One-liner install command is **identical** in both languages:
  `bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh)` + `ibus restart`.
- Both READMEs now share: Quick Install at top, demo GIF, 3-question decision
  tree, 3 troubleshooting quick links.
- English README.md was NOT modified.

**Translation notes:**
- "Which install method for me?" → "我该用哪种安装方式？" (natural, not literal).
- "One command (recommended)" → "一条命令（推荐）"; "Manual package" → "手动装包".
- Kept code/identifiers verbatim (`bootstrap.sh`, `.deb`, `PKGBUILD`, `input`
  group, `udevadm trigger`, `ibus engine handwrite-chinese`).
- Anchor link uses the Chinese heading slug `#故障排除` (the Chinese Troubleshooting
   section is `## 故障排除`), so the in-page link resolves correctly.

---

## B2.2 — docs/launch-posts/en.md + zh.md (bilingual launch post drafts)

Created two draft files for owner review (NOT posted). These are the B2.2 deliverable
feeding the B3.2 (EN) / B3.3 (ZH) posting gate.

**Files:**
- `docs/launch-posts/en.md` — 4 English drafts: r/linux (Show HN style), r/archlinux
  (PKGBUILD + one-liner), r/Fedora (.rpm), r/Ubuntu (.deb + one-liner).
- `docs/launch-posts/zh.md` — 3 Chinese drafts: r/linuxcn, V2EX (分享区), 少数派.
  Written natively in Chinese (not machine-translated), lead angle "在 Linux 触控板上
  用手写输入中文 / macOS 风格".

**Shared structure per post:** hook → problem statement → demo GIF reference (or
install-page fallback) → one-liner install → 3-5 key features → links. All under 400
words. One-liner used verbatim:
`bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart`

**Links embedded:** demo GIF URL, install page, GitHub repo, releases page.

**Claims used (all sourced from README, no invention):**
- macOS-style floating panel, evdev trackpad input
- PP-OCRv6 ONNX recognition, 18,710 chars
- 100% top-1 accuracy on 40 real handwriting samples, avg confidence 94.97%
- 6-tab GTK prefs, on-demand model download, user dictionary, configurable shortcuts
- tap-to-select, two-finger swipe paging, swipe momentum, mouse fallback
- Tested on Acer Aspire (HTIX5288) + MacBook Pro (bcm5974)

**Claims FLAGGED for owner verification before posting:**
1. "100% top-1 on 40 samples" — small sample (README itself calls it "validated",
   plan says "40 samples"). Drafts already hedge with "small sample / 仅供参考" language,
   but owner should confirm the framing is acceptable for public posting.
2. Wayland popup positioning + SELinux evdev access "untested" — drafts state this
   honestly per README Known Limitations; confirm before posting to Fedora/Arch.
3. AUR package "coming soon" — EN r/archlinux + install page say AUR is not yet live;
   owner should confirm AUR status at post time (B3.2) so the post isn't stale.
4. Demo GIF URL (`.../assets/demo.gif`) depends on B1.1 (user-recorded, blocked on
   hardware). Drafts reference it but note install-page fallback; verify GIF exists
   before B3.2/B3.3, else swap to install page link.

**No files modified** other than the two new draft files. README.md and docs/index.md
untouched (per MUST NOT DO).

**Post titles (for owner review):**
- EN r/linux: "Show HN: A macOS-style Chinese handwriting IME that draws on your Linux trackpad"
- EN r/archlinux: "Chinese handwriting input for Linux trackpads (IBus engine, PKGBUILD + one-liner)"
- EN r/Fedora: "Handwrite Chinese on your Fedora trackpad — IBus engine with .rpm install"
- EN r/Ubuntu: "Write Chinese on your Ubuntu trackpad — IBus handwriting engine (.deb + one-liner)"
- ZH r/linuxcn: "macOS 同款的中文手写输入法，现在能在 Linux 触控板上用了"
- ZH V2EX: "分享：一个支持触控板手写中文的 Linux IBus 输入法"
- ZH 少数派: "在 Linux 触控板上，用 macOS 风格手写中文"

**Platforms targeted:** 4 EN (r/linux, r/archlinux, r/Fedora, r/Ubuntu) + 3 ZH
(r/linuxcn, V2EX, 少数派) = 7 drafts, matching plan Section 3.


---

## B2.3 — OG social preview image (docs/assets/og-image.png) — DONE (Pillow)

Created the 1280×640 Open Graph preview image from `docs/screenshot.png`
using Python Pillow (ImageMagick was not installed; Pillow 10.2.0 approved
as substitute).

- **Tool used:** Python Pillow 10.2.0 (`PIL.Image`).
- **Logic:** cover-resize (scale to fill, `ratio = max(target_w/w, target_h/h)`,
  `Image.LANCZOS`) + center crop to 1280×640. No distortion/stretch.
- **Command:**
  `python3 -c "from PIL import Image; im=Image.open('docs/assets/og-image.png'); print(im.size)"`
- **Output dimensions:** `(1280, 640)` — verified exactly.
- **Source `docs/screenshot.png` NOT modified.**
- **Supersedes** the earlier BLOCKED ImageMagick attempt (B2.3 — BLOCKED entry above).

---

## B1.1/B2.1 — tools/record-demo.sh (interactive demo recorder guide)

Created `tools/record-demo.sh` — an interactive launcher/guide (NOT an auto-recorder)
to unblock the user's MacBook Pro demo capture for B1.1 (demo.gif/MP4) and B2.1 (PNGs).

- `#!/usr/bin/env bash` + `set -euo pipefail`; repo root resolved from `BASH_SOURCE`
  (matches `tools/install.sh` style). Creates `docs/assets/` if missing.
- Checks `ffmpeg` (required, warns if absent), `peek` + ImageMagick `import` (warns if
  absent). Detects macOS vs Linux via `uname` for platform-specific ffmpeg hints.
- 4 steps, each gated by `read -r -p` so the user controls recording timing:
  1. launch `ibus-engine-handwrite-chinese --test` (standalone GTK, no IBus needed)
  2. 15s GIF 800x600 → `docs/assets/demo.gif` (peek, or ffmpeg MP4→GIF)
  3. 30s MP4 1280x720 → `docs/assets/demo.mp4` (macOS `avfoundation -i "1"`,
     Linux `x11grab -i :0.0`; both show `-list_devices true`)
  4. screenshots via `screencapture -i` (macOS) / `import` (Linux) into the 6 exact
     filenames: main-panel, trackpad-drawing, preference-dialog, model-download,
     shortcuts-tab, user-dict (all under `docs/assets/`).
- Ends by listing saved files and telling the user to tell Atlas "assets are in".
- **Verification:** `bash -n` syntax OK; `shellcheck -e SC1091` clean. No other files
  modified (per MUST NOT DO). Does NOT invoke ffmpeg/peek/import itself.
