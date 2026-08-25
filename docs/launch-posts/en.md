# Launch Post Drafts — English

> DRAFTS for owner review. Do not post. Each post is under 400 words.
> Replace the demo GIF URL with the final asset once B1.1 is recorded, or link the install page as fallback.
>
> Shared assets:
> - Demo GIF: `https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif`
> - Install page: `https://ai-space-lab.github.io/ibus-handwrite-chinese/`
> - GitHub repo: `https://github.com/ai-space-lab/ibus-handwrite-chinese`
> - Releases: `https://github.com/ai-space-lab/ibus-handwrite-chinese/releases`
> - One-liner: `bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart`

---

## 1. r/linux — Show HN style

**Title:** Show HN: A macOS-style Chinese handwriting IME that draws on your Linux trackpad

**Body:**

I got tired of hunting for the right character on a pinyin keyboard when I only knew how to write it. So I built a Chinese handwriting input method for Linux that turns your trackpad into a writing surface, the way macOS does on a MacBook.

It's an IBus engine. Switch to "Chinese Handwriting", draw a character with one finger on the trackpad, and candidates pop up in a dark floating panel near your cursor. Tap the trackpad to pick one, or swipe two fingers to page through candidates.

Recognition runs locally via ONNX Runtime, covering 18,710 characters. On a set of 40 real handwritten samples it scored 100% top-1 accuracy (average confidence 94.97%). That's a small sample, so treat it as promising rather than definitive, but it's been solid in daily use.

Key features:
- macOS-style floating panel that appears next to your text cursor
- Draw directly on the trackpad via evdev (no tablet needed); mouse fallback if no trackpad
- Tap-to-select, two-finger swipe paging, and swipe momentum
- 6-tab GTK preference dialog (model, engine, window, user dictionary, shortcuts)
- On-demand model download (tiny / small / medium tiers) from the prefs
- Local user dictionary that learns characters you pick
- Fully configurable shortcuts

Install (auto-detects your distro):

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

Demo: https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif
Install guide: https://ai-space-lab.github.io/ibus-handwrite-chinese/
Source and releases: https://github.com/ai-space-lab/ibus-handwrite-chinese

Tested on an Acer Aspire (HTIX5288) and a MacBook Pro (bcm5974) trackpad. Other trackpads with touch detection should work but are untested. Feedback and bug reports welcome.

---

## 2. r/archlinux

**Title:** Chinese handwriting input for Linux trackpads (IBus engine, PKGBUILD + one-liner)

**Body:**

For Arch users who want to handwrite Chinese on their trackpad instead of fighting a pinyin layout: there's now an IBus engine that does macOS-style trackpad handwriting, with deep-learning recognition.

On Arch you have two easy paths. Build from the PKGBUILD in the repo:

```bash
git clone https://github.com/ai-space-lab/ibus-handwrite-chinese
cd ibus-handwrite-chinese/packaging
makepkg -si
ibus restart
```

Or just run the cross-distro one-liner, which handles `pacman` + `yay` (AUR) automatically:

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

What you get:
- A dark floating panel near your cursor; draw a character on the trackpad, tap to select, swipe to page
- Local ONNX Runtime recognition covering 18,710 characters; 100% top-1 on a 40-sample handwritten test (avg confidence 94.97%)
- 6-tab GTK settings, on-demand model download, local user dictionary, configurable shortcuts
- Mouse fallback if your trackpad isn't evdev-compatible

Demo: https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif
Install guide: https://ai-space-lab.github.io/ibus-handwrite-chinese/
Releases (PKGBUILD + packages): https://github.com/ai-space-lab/ibus-handwrite-chinese/releases

Note: Wayland popup positioning and SELinux evdev access are untested on Arch. Tested on an Acer Aspire and MacBook Pro trackpad. The AUR package is still "coming soon", so PKGBUILD or the one-liner are the current options.

---

## 3. r/Fedora

**Title:** Handwrite Chinese on your Fedora trackpad — IBus engine with .rpm install

**Body:**

If you run Fedora and sometimes need to input Chinese by writing rather than pinyin, there's an IBus engine that lets you draw characters on the trackpad, macOS-style.

Fedora install is a single `.rpm` from the releases page:

```bash
sudo rpm -i <file-from-releases>
ibus restart
```

Or use the one-liner, which detects Fedora and runs `dnf` + model download for you:

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

Why it's worth a look:
- Draw on the trackpad via evdev; a dark panel shows candidates by your cursor. Tap to pick, two-finger swipe to page.
- ONNX Runtime recognition over 18,710 characters. On 40 real handwritten samples: 100% top-1 accuracy, 94.97% average confidence.
- 6-tab GTK preferences, on-demand model download (tiny/small/medium), user dictionary, remappable shortcuts.
- Mouse fallback when no trackpad is available.

Demo: https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif
Install guide: https://ai-space-lab.github.io/ibus-handwrite-chinese/
Releases (.rpm): https://github.com/ai-space-lab/ibus-handwrite-chinese/releases

Heads-up: SELinux evdev access and Wayland popup positioning are untested on Fedora. Verified on an Acer Aspire and MacBook Pro trackpad. Requires Fedora 40+.

---

## 4. r/Ubuntu

**Title:** Write Chinese on your Ubuntu trackpad — IBus handwriting engine (.deb + one-liner)

**Body:**

Ubuntu users who'd rather draw a character than spell it out: there's an IBus engine for macOS-style trackpad handwriting with deep-learning recognition.

Two install options. The `.deb` from releases:

```bash
sudo dpkg -i <file-from-releases> && sudo apt install -f
ibus restart
```

Or the one-liner, which detects Ubuntu and runs `apt` + model download automatically:

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

What it does:
- A dark floating panel appears by your cursor. Draw with one finger on the trackpad, tap to select, swipe two fingers to page through candidates.
- Recognition uses ONNX Runtime locally, covering 18,710 characters. In a 40-sample handwritten test it hit 100% top-1 accuracy (94.97% average confidence).
- 6-tab GTK settings, on-demand model download, a local user dictionary that learns from your picks, and fully configurable shortcuts.
- Mouse fallback if your machine has no evdev trackpad.

Demo: https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif
Install guide: https://ai-space-lab.github.io/ibus-handwrite-chinese/
Releases (.deb): https://github.com/ai-space-lab/ibus-handwrite-chinese/releases

Requires Ubuntu 22.04+. Tested on an Acer Aspire and MacBook Pro trackpad; other touch-capable trackpads should work but are untested.
