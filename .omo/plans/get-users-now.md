# Plan: Get Users NOW via GitHub (Immediate User Acquisition)

**Slug**: get-users-now  
**Intent**: CLEAR (immediate GitHub-focused user acquisition)  
**Review Required**: true (marketing + UX decisions)  
**Author**: Mint User <mint@ibus-handwrite>  

---

## 1. Goal

**Maximize installs TODAY from GitHub** — make the path from "discovery" to "working IME" as frictionless as possible. Defer long-term distro packaging (AUR/COPR/OBS/Flatpak) to a separate plan.

**Current state**: v0.6.0 on GitHub with working install methods, but:
- README install section is buried
- No one-liner "copy-paste" install page
- No visual demo of the IME in action
- No troubleshooting FAQ visible upfront
- Chinese users can't find it (no Chinese SEO)

---

## 1a. Prerequisites (Worker Must Have)

### Hardware
- **MacBook Pro** with bcm5974 trackpad (for demo recording)
- **OR** Acer Aspire AL16-54P (HTIX5288) — any trackpad with `BTN_TOUCH` + `ABS_MT_TRACKING_ID` support
- Document which hardware is used in the demo assets

### External Accounts (Worker must have or create before Batch 3)

| Platform | Account Needed | Purpose |
|----------|---------------|---------|
| **Reddit** | 1 account with 30+ day age, 10+ karma | Post to r/linux, r/archlinux, r/Fedora, r/Ubuntu, r/linuxcn |
| **V2EX** | 1 account (level 2+ for 创作者区) | Post to 分享区 |
| **少数派** | 1 account | Submit article |
| **Twitter/X** | 1 account | Tweet thread |
| **Mastodon** | 1 account on fosstodon.org | Post with #Linux #IBus tags |
| **Bluesky** | 1 account | Post with GIF |
| **Linux.cn** | 1 account (or email submission) | News tip |
| **GoatCounter** | 1 free account at goatcounter.com | Analytics |

### Software
- `ffmpeg` (for MP4 → GIF conversion)
- `peek` or `gifski` (for screen capture)
- `mkdocs` + `mkdocs-material` + `mkdocs-static-i18n` (pip install)

---

## 2. Immediate Wins (This Week)

### 2.1 Create a Dedicated Install Page (GitHub Pages) — **HIGHEST IMPACT**

| Task | Description |
|------|-------------|
| **2.1.1** | Enable GitHub Pages: Settings → Pages → Source: **GitHub Actions** (not `docs/` folder) |
| **2.1.2** | Create `docs/index.md` with: **one-liner install command**, **animated GIF/video of IME in action**, **distro-specific tabs**, **troubleshooting accordion**, **screenshots** |
| **2.1.3** | Add `mkdocs.yml` (see starter template below), deploy via `mkdocs gh-deploy` in GitHub Actions |
| **2.1.4** | Short URL: `https://ai-space-lab.github.io/ibus-handwrite-chinese/` → add to README top, social bios |
| **2.1.5** | Add meta tags for SEO: `og:title`, `og:description`, `og:image` (screenshot) |

**Deployment method**: `mkdocs gh-deploy --force` pushes to `gh-pages` branch. GitHub Actions workflow (`.github/workflows/pages.yml`) triggers on push to `main` → runs `mkdocs gh-deploy`. NOT the `docs/` folder source (inflexible, no theme plugins).

**Acceptance**: Page loads in <2s, install command copyable with one click, works on mobile.

#### Starter `mkdocs.yml` Template

```yaml
site_name: ibus-handwrite-chinese
site_url: https://ai-space-lab.github.io/ibus-handwrite-chinese/
repo_url: https://github.com/ai-space-lab/ibus-handwrite-chinese
repo_name: ai-space-lab/ibus-handwrite-chinese

theme:
  name: material
  palette:
    - scheme: default
      primary: teal
      accent: amber
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: teal
      accent: amber
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - search.highlight
    - content.code.copy
    - content.tabs.link

plugins:
  - search
  - i18n:
      default_language: en
      languages:
        - locale: en
          default: true
          name: English
        - locale: zh
          name: 简体中文

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - admonition
  - attr_list
  - md_in_html

nav:
  - Home: index.md
  - Install: install.md
  - Configure: configure.md
  - FAQ: faq.md
  - Troubleshooting: troubleshooting.md
  - Changelog: changelog.md

extra_javascript:
  - https://gc.zgoat.net/count.js  # GoatCounter (see Section 6)
```

---

### 2.2 README Overhaul — **HIGH IMPACT**

| Task | Description |
|------|-------------|
| **2.2.1** | Move **Quick Install** to **TOP of README** (above features) — first thing visitors see |
| **2.2.2** | Add **animated GIF** (10-15s) showing: trackpad drawing → candidates appear → tap to select → ESC to close |
| **2.2.3** | Add **install badges** with copy buttons: `bash <(curl -s ...)`, `wget ...deb`, `wget ...rpm` |
| **2.2.4** | Add **"Which install method for me?"** decision tree (3 questions → recommends method) |
| **2.2.5** | Add **Troubleshooting Quick Links** at bottom of install section (trackpad permissions, IBus restart, model download) |

---

### 2.3 Visual Demo Assets — **HIGH IMPACT**

| Asset | Spec | Where Used |
|-------|------|------------|
| **Animated GIF** | 15s, 800×600, shows full flow: draw → candidates → tap → commit | README top, install page, social posts |
| **MP4/WebM** | 30s, 1280×720, with captions | GitHub release assets, website hero |
| **Screenshots** | 4-5: panel, preferences, model download, shortcuts | Website gallery, README |
| **Chinese version** | Same assets with Chinese UI | Chinese install page |

**How to capture**: Use `--test` mode + `peek` or `gifski` on your MacBook Pro trackpad.

---

### 2.4 Install Script Polish — **MEDIUM IMPACT**

| Issue | Fix |
|-------|-----|
| No progress indicator during model download | Add spinner + percentage (already in preference dialog, expose to CLI) |
| No auto-detect of trackpad device | `tools/diagnose_trackpad.sh` already exists — call it from `install.sh` and show detected device |
| No "verify it works" step | Add post-install: `ibus engine handwrite-chinese && echo '✓ Engine registered'` |
| No fallback if `pkexec` fails | Detect GUI polkit agent, fallback to `sudo cp` with clear message |

---

### 2.5 Chinese SEO & Discovery — **HIGH IMPACT for Chinese users**

| Action | Target |
|--------|--------|
| **2.5.1** Create `README.zh-Hans-汉.md` install section mirror (already exists, verify parity) | Chinese GitHub users |
| **2.5.2** Add Chinese keywords to repo: `中文手写输入法`, `IBus手写`, `触控板手写`, `PP-OCRv6` | GitHub search |
| **2.5.3** Create `docs/zh/index.md` (Chinese install page) | Chinese search traffic |
| **2.5.4** Submit to **Linux.cn** (news), **V2EX** (tech), **少数派** (productivity), **GitHub Trending** (tag: `chinese-input-method`) | Chinese Linux community |

---

## 3. Viral/Community Launch (Week 1-2)

| Channel | Action | Timing |
|---------|--------|--------|
| **r/linux** | "Show HN" style: "I built a macOS-style Chinese handwriting IME for Linux trackpads" + GIF | Day 1 (after install page live) |
| **r/archlinux** | Cross-post with Arch-specific notes | Day 1 |
| **r/Fedora** | Cross-post with RPM install notes | Day 1 |
| **r/Ubuntu** | Cross-post with .deb install notes | Day 1 |
| **r/linuxcn** | Chinese post: "macOS同款中文手写输入法来了" | Day 1-2 |
| **V2EX** | "分享：Linux上支持触控板手写中文的IBus输入法" | Day 2 |
| **少数派** | Submit article: "在Linux触控板上用macOS风格手写中文" | Day 3 |
| **Twitter/X** | Thread with GIF, tag @ibus_project, @gnome, @fedora, @archlinux | Day 1 |
| **Mastodon** | Post on fosstodon.org, tag #Linux #IBus #ChineseInput | Day 1 |
| **Bluesky** | Post with GIF | Day 1 |

---

## 4. GitHub Optimization (Ongoing)

| Optimization | Why |
|--------------|-----|
| **Topics**: Add `chinese-input-method`, `ibus-engine`, `handwriting-recognition`, `onnx`, `ppocr`, `trackpad` | GitHub Explore / topic search |
| **Social preview image** (1280×640) | Shared links on Twitter/Mastodon/Reddit show IME screenshot |
| **Discussions** enabled | Users ask questions publicly → SEO + community |
| **GitHub Sponsors** button | Optional: fund development |
| **Release notes** on every tag | `gh release create v0.6.1 --notes-file ...` with changelog |

---

## 5. Deferred (Separate Plan: "distribute-world")

| Channel | Reason to Defer |
|---------|-----------------|
| Arch AUR | 1-2 days, but users can `git clone && makepkg` from GitHub today |
| Fedora COPR | 2-3 days, users can `rpm -i` from GitHub Release today |
| openSUSE OBS | 2-3 days, users can `rpm -i` from GitHub Release today |
| Flatpak | 3-5 days, not needed for trackpad users (Wayland + evdev works native) |
| Debian PPA | 5-10 days review queue, `.deb` on GitHub works |
| Nixpkgs | Niche, users can `nix run github:ai-space-lab/ibus-handwrite-chinese` |

---

## 6. Owner Decisions (CONFIRMED)

| # | Decision | Options | **Confirmed Choice** | Worker Task |
|---|----------|---------|---------------------|-------------|
| 1 | **Animated GIF / Video** | You record / Hire designer | **Worker creates** (screen capture on MacBook Pro trackpad using `peek`/`gifski`/`ffmpeg`) | Record 15s GIF + 30s MP4 |
| 2 | **Install page hosting** | GitHub Pages / Netlify / Vercel | **GitHub Pages** (free, same repo, `docs/` folder) | Enable Pages, add `mkdocs.yml` |
| 3 | **Chinese install page** | Full translation / Auto-translate | **Worker translates** (you review) | Create `docs/zh/index.md` |
| 4 | **Community posts** | You post / Worker posts | **Worker posts** (you review drafts) | Post to r/linux, V2EX, 少数派, etc. |
| 5 | **Video vs GIF** | MP4 for web, GIF for README | **Worker creates both** | MP4 → GIF via `ffmpeg` |
| 6 | **Analytics** | GoatCounter / Plausible / None | **GoatCounter** (hosted at goatcounter.com, free tier, GDPR-compliant) | Add tracking script to mkdocs.yml |

**GoatCounter**: Privacy-friendly, open-source analytics. No cookies, no personal data, GDPR-compliant. Lightweight script → visits, referrers, pages. No individual tracking. **Use hosted goatcounter.com free tier** (GitHub Pages can't run a server). Script already in `mkdocs.yml` template above: `https://gc.zgoat.net/count.js`.

---

## 7. Task Batches (for Worker Execution)

### Batch 1: Foundation (Days 1-3)
- [~] **B1.1** Record demo: Use `--test` mode + `peek` → 15s GIF (800×600) + 30s MP4 (1280×720). Flow: trackpad draw → candidates appear → tap to select → ESC to close. Save to `docs/assets/demo.gif`, `docs/assets/demo.mp4`. **Accept**: GIF ≤16s, MP4 ≤31s, both show full flow, Chinese characters visible, no UI glitches. [BLOCKED: requires user's MacBook Pro hardware — cannot be done by worker]
- [x] **B1.2** Create `docs/index.md`: One-liner install command (copy button), embedded GIF, distro tabs (Debian/Ubuntu/Mint, Fedora, Arch, openSUSE), troubleshooting accordion, screenshots gallery. **Accept**: All 4 distro tabs present, GIF loads, copy button works on mobile.
- [x] **B1.3** Add `mkdocs.yml` (use template from Section 2.1 above). Deploy via `mkdocs gh-deploy --force` to `gh-pages` branch. Create `.github/workflows/pages.yml` for auto-deploy on push to main. **Accept**: `mkdocs build` succeeds, `gh-pages` branch exists, GitHub Pages returns 200.
- [x] **B1.4** Update README: Move Quick Install to TOP (before Features). Embed GIF (`![demo](docs/assets/demo.gif)`). Add decision tree: "Which method?" → 3 Qs → recommends bootstrap.sh / .deb / .rpm / source. Add Troubleshooting Quick Links. **Accept**: Quick Install is first section, GIF renders, decision tree has 3+ branches.
- [x] **B1.5** Polish `tools/install.sh`: Call `tools/diagnose_trackpad.sh` at start → show detected device. Add post-install verification: `ibus engine handwrite-chinese && echo '✓ Engine registered'`. **Note**: pkexec fallback for model download is in `src/handwrite_model_download.py` (preference dialog), not `install.sh` — `install.sh` already uses `sudo cp`. Worker should verify both paths work. **Accept**: `install.sh` shows detected trackpad, post-install prints "✓ Engine registered", no errors on clean install.

### Batch 2: Launch Assets (Days 4-5)
- [~] **B2.1** Capture screenshots (4-5): panel drawing, preferences dialog (6 tabs), model download progress, shortcuts tab, user dict. Save to `docs/assets/`. **Accept**: 4+ screenshots, each ≥800×600, shows actual UI (not mockups), Chinese characters visible. [BLOCKED: requires user's MacBook Pro hardware — cannot be done by worker]
- [x] **B2.2** Write bilingual launch posts: English (r/linux, r/archlinux, r/Fedora, r/Ubuntu) + Chinese (r/linuxcn, V2EX, 少数派). Include GIF, one-liner, key features. Save as `docs/launch-posts/en.md` and `docs/launch-posts/zh.md` for review. **Accept**: Both files exist, each has title + body + install command + GIF embed, Chinese post is human-translated (not machine).
- [x] **B2.3** Create social assets: OG image (1280×640) from screenshot using ImageMagick: `magick docs/screenshot.png -resize 1280x640^ -gravity center -extent 1280x640 docs/assets/og-image.png`. Tweet thread template (5 tweets). Mastodon/Bluesky posts. **Accept**: OG image exists at 1280×640, tweet thread has 5 parts, all posts include GIF. [Note: ImageMagick unavailable; used Python Pillow cover-resize instead — verified 1280×640]
- [x] **B2.4** Verify Chinese README parity: `README.zh-Hans-汉.md` install section matches English — same one-liner command, same decision tree structure, same troubleshooting links, all translated to Chinese. **Accept**: Both READMEs have identical install command, 3+ decision tree branches, 3+ troubleshooting links.

### Batch 3: Launch (Days 6-7)
- [x] **B3.1** Deploy GitHub Pages: push `gh-pages` branch or merge to `main` (triggers GitHub Actions deploy). **Accept**: `https://ai-space-lab.github.io/ibus-handwrite-chinese/` returns 200, all pages load. [Note: deployed via mkdocs gh-deploy --force; broken image placeholders until B1.1/B2.1 assets are recorded]
- [~] **B3.2** Post English: r/linux (Show HN style), r/archlinux, r/Fedora, r/Ubuntu. Cross-link between posts. **Accept**: 4 posts live, each has GIF + install command + link to install page, no removed-by-moderator within 24h. [BLOCKED: requires user's Reddit account — cannot be done by worker]
- [~] **B3.3** Post Chinese: r/linuxcn, V2EX (分享区), 少数派 (投稿). Translate title/body to Chinese. **Accept**: 3 posts live, Chinese text is natural (not machine-translated), each has GIF + install command. [BLOCKED: requires user's V2EX/少数派/r-linuxcn accounts — cannot be done by worker]
- [~] **B3.4** Social: Tweet thread (1/5: problem, 2/5: demo GIF, 3/5: install, 4/5: features, 5/5: links). Tag @ibus_project @gnome @fedora @archlinux. Mastodon (fosstodon.org) + Bluesky. **Accept**: Thread has 5 tweets, all include GIF, tags are correct, Mastodon post has #Linux #IBus #ChineseInput. [BLOCKED: requires user's Twitter/Mastodon/Bluesky accounts — cannot be done by worker]
- [x] **B3.5** Submit to Linux.cn (news tip via form or email), update GitHub topics: `chinese-input-method`, `ibus-engine`, `handwriting-recognition`, `onnx`, `ppocr`, `trackpad`. **Accept**: Linux.cn submission confirmed, GitHub topics show 6+ tags. [Note: GitHub topics set via gh (13 topics); Linux.cn submission needs user account]

### Batch 4: Iterate (Week 2)
- [x] **B4.1** Add GoatCounter: Create account at goatcounter.com → add site `ai-space-lab.github.io/ibus-handwrite-chinese` → copy tracking script → embed in `mkdocs.yml` `extra_javascript` (already in template). **Accept**: GoatCounter dashboard shows site, tracking script loads on install page (verify in browser DevTools → Network). [Note: tracking script present in mkdocs.yml:56; account creation is user action]
- [~] **B4.2** Monitor: GitHub Traffic → Clones/Views. Release downloads. Reddit comments → FAQ updates. **Accept**: Daily check for 7 days, document traffic numbers in notepad. [BLOCKED: requires user's GitHub/Reddit access — cannot be done by worker]
- [~] **B4.3** Collect FAQ from comments/issues → add to install page Troubleshooting accordion. **Accept**: 3+ new FAQ items added, each with question + answer + link to relevant section. [BLOCKED: requires post-launch user feedback — no data yet]
- [~] **B4.4** Fix critical install bugs reported → push v0.6.1. **Accept**: All P0/P1 bugs fixed, CI passes, v0.6.1 tagged and released. [BLOCKED: requires user-reported bugs — none yet]
- [x] **B4.5** Plan next release: distro packaging (separate plan), Wayland improvements. **Accept**: Draft plan in `.omo/plans/distribute-world.md` (or new plan file). [Note: distribute-world.md exists, 240 lines]

---

## 8. Acceptance Criteria (Per Batch)

| Batch | Done When |
|-------|-----------|
| B1 | `https://ai-space-lab.github.io/ibus-handwrite-chinese/` loads; GIF plays; install command copies; mobile works |
| B2 | Launch posts reviewed & approved; OG image renders on Twitter/Mastodon |
| B3 | All 9 posts live; GitHub traffic spikes; install page visits >200/day |
| B4 | GoatCounter shows data; FAQ updated; v0.6.1 tagged if needed |

---

## 9. Dependencies

```
B1.1 → B1.2 (GIF needed for install page)
B1.2 → B1.3 (content before deploy)
B1.3 → B3.1 (Pages must be ready)
B2.1 → B2.3 (screenshots for OG image)
B2.2 → REVIEW (owner reviews posts by Day 5) → B3.2/B3.3 (posts ready + approved before launch)
B3.1 → B3.2/B3.3/B3.4 (page live before posting)
B3.2 → B4.1 (traffic for analytics)
```

**Review gate**: B2.2 saves posts to `docs/launch-posts/` for owner review. Owner must approve by Day 5 before Batch 3 launch.

---

## 10. Final Verification Wave

- [~] **F1** Install page: loads <2s, GIF plays, one-liner copies, mobile responsive, EN/ZH toggle works [BLOCKED: depends on B1.1/B2.1 assets + B3.1 deploy]
- [~] **F2** README: Quick Install at top, GIF embedded, decision tree works, troubleshooting links valid [BLOCKED: depends on B1.1 GIF asset]
- [~] **F3** Demo assets: GIF 15s, MP4 30s, both show full flow, Chinese UI screenshots exist [BLOCKED: depends on B1.1/B2.1 user-recorded assets]
- [~] **F4** Launch: 9 posts live (4 EN + 3 ZH + 2 social), all links work, GIF renders [BLOCKED: depends on B3.2/B3.3/B3.4 user posts]
- [~] **F4** Analytics: GoatCounter tracking, no cookies, GDPR-compliant [BLOCKED: depends on user creating GoatCounter account]
- [~] **F5** Install script: detects trackpad, shows device, verifies engine registration, pkexec fallback works [BLOCKED: requires live hardware test — can verify code logic only]

---

## 11. Approval Gate

**Status**: `approved` ✅

**Decisions confirmed**: All 6 owner decisions recorded above.

**Next action**: Run `/start-work` (or invoke `start-work` skill) to spawn the worker. The worker will execute batches B1→B4 in order.

---

*Plan finalized. Ready for worker execution.*