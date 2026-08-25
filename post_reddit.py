#!/usr/bin/env python3
"""
Post Reddit launch posts using copied Firefox profile.
"""
import time
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager


# ==================== POST DATA ====================
POSTS = [
    {
        "subreddit": "linux",
        "title": "Show HN: A macOS-style Chinese handwriting IME that draws on your Linux trackpad",
        "body": """I got tired of hunting for the right character on a pinyin keyboard when I only knew how to write it. So I built a Chinese handwriting input method for Linux that turns your trackpad into a writing surface, the way macOS does on a MacBook.

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

Tested on an Acer Aspire (HTIX5288) and a MacBook Pro (bcm5974) trackpad. Other trackpads with touch detection should work but are untested. Feedback and bug reports welcome.""",
    },
    {
        "subreddit": "archlinux",
        "title": "Chinese handwriting input for Linux trackpads (IBus engine, PKGBUILD + one-liner)",
        "body": """For Arch users who want to handwrite Chinese on their trackpad instead of fighting a pinyin layout: there's now an IBus engine that does macOS-style trackpad handwriting, with deep-learning recognition.

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

Note: Wayland popup positioning and SELinux evdev access are untested on Arch. Tested on an Acer Aspire and MacBook Pro trackpad. The AUR package is still "coming soon", so PKGBUILD or the one-liner are the current options.""",
    },
    {
        "subreddit": "Fedora",
        "title": "Handwrite Chinese on your Fedora trackpad — IBus engine with .rpm install",
        "body": """If you run Fedora and sometimes need to input Chinese by writing rather than pinyin, there's an IBus engine that lets you draw characters on the trackpad, macOS-style.

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

Heads-up: SELinux evdev access and Wayland popup positioning are untested on Fedora. Verified on an Acer Aspire and MacBook Pro trackpad. Requires Fedora 40+.""",
    },
    {
        "subreddit": "Ubuntu",
        "title": "Write Chinese on your Ubuntu trackpad — IBus handwriting engine (.deb + one-liner)",
        "body": """Ubuntu users who'd rather draw a character than spell it out: there's an IBus engine for macOS-style trackpad handwriting with deep-learning recognition.

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

Requires Ubuntu 22.04+. Tested on an Acer Aspire and MacBook Pro trackpad; other touch-capable trackpads should work but are untested.""",
    },
    {
        "subreddit": "linuxcn",
        "title": "macOS 同款的中文手写输入法，现在能在 Linux 触控板上用了",
        "body": """有时候你明明会写这个字，却怎么也想不起它的拼音。macOS 上可以用触控板手写中文，Linux 这边一直缺一个好用的方案。最近我做了一个 IBus 输入法引擎，把触控板变成书写区，思路跟 macOS 基本一致。

切到「中文手写」后，用一根手指在触控板上写出汉字，深色浮动面板就会出现在光标旁边，列出候选字。轻点触控板选字，双指左右滑动翻页，滑得越快翻得越多。

识别在本地用 ONNX Runtime 完成，覆盖 18,710 个汉字。在 40 个真实手写样本上，top-1 准确率是 100%，平均置信度 94.97%。样本量不大，只能说表现不错，不能当成绝对结论，但日常用下来很稳。

主要功能：
- macOS 风格浮动面板，紧贴光标位置
- 直接通过 evdev 在触控板上书写，不需要手写板；没有触控板也能用鼠标写
- 轻点选字、双指滑动翻页、滑动惯性
- 6 个标签页的 GTK 设置（模型、引擎、窗口、用户词典、快捷键等）
- 设置里按需下载模型（tiny / small / medium 三档）
- 本地用户词典，会记住你常选的字
- 快捷键全部可改

安装（自动识别发行版）：

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

演示：https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif
安装指引：https://ai-space-lab.github.io/ibus-handwrite-chinese/
源码与发布：https://github.com/ai-space-lab/ibus-handwrite-chinese

已在 Acer Aspire（HTIX5288）和 MacBook Pro（bcm5974）触控板上验证。其他支持触摸的触控板应该也能用，但尚未逐一测试。欢迎提意见和报 bug.""",
    },
]


def setup_driver():
    """Set up Firefox with copied profile."""
    profile_path = Path("/tmp/ff-reddit-profile")
    if not profile_path.exists():
        print("ERROR: Copied profile not found at /tmp/ff-reddit-profile")
        sys.exit(1)

    options = Options()
    options.profile = str(profile_path)
    options.add_argument("--no-remote")
    # options.add_argument("--headless")  # Keep visible for debugging

    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    driver.set_window_size(1280, 900)
    return driver


def check_logged_in(driver):
    """Verify we're logged in as hgentic001."""
    driver.get("https://www.reddit.com")
    time.sleep(3)

    try:
        # Look for username in the UI
        page_source = driver.page_source
        if "hgentic001" in page_source:
            print("✓ Confirmed logged in as hgentic001")
            return True
        else:
            print("✗ Not logged in as hgentic001 (username not found in page)")
            print("Page title:", driver.title)
            # Print some debug info
            if "Log In" in page_source or "Sign Up" in page_source:
                print("  Page shows login/signup - not logged in")
            return False
    except Exception as e:
        print(f"✗ Check failed: {e}")
        return False


def submit_post(driver, post):
    """Submit a text post to a subreddit."""
    sub = post["subreddit"]
    title = post["title"]
    body = post["body"]

    print(f"\n{'='*60}")
    print(f"Posting to r/{sub}")
    print(f"Title: {title[:80]}...")
    print(f"{'='*60}")

    # Go to submit page
    submit_url = f"https://www.reddit.com/r/{sub}/submit"
    driver.get(submit_url)
    time.sleep(3)

    try:
        # Wait for page load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
        print(f"  Current URL: {driver.current_url}")
        print(f"  Page title: {driver.title}")

        # Check if we need to select "Post" tab (text post) - new Reddit UI
        try:
            # Try multiple selectors for the Post tab
            post_tab_selectors = [
                "//button[@role='tab' and contains(., 'Post')]",
                "//button[contains(@data-testid, 'post-tab')]",
                "//button[contains(., 'Post') and @role='tab']",
                "//a[contains(@href, 'submit') and contains(., 'Post')]",
            ]
            for xpath in post_tab_selectors:
                try:
                    post_tab = driver.find_element(By.XPATH, xpath)
                    if post_tab.is_displayed():
                        aria_selected = post_tab.get_attribute("aria-selected")
                        if aria_selected == "false":
                            post_tab.click()
                            time.sleep(1)
                            print("  ✓ Clicked Post tab")
                        break
                except NoSuchElementException:
                    continue
        except Exception:
            pass

        # Fill title - try multiple selectors
        title_selectors = [
            "[data-testid='post-title-input']",
            "input[id='post-title']",
            "textarea[id='post-title']",
            "input[placeholder*='Title' i]",
            "textarea[placeholder*='Title' i]",
            "#post-title",
            "input[name='title']",
            "textarea[name='title']",
            "[data-test-id='post-title-input']",
        ]
        title_input = None
        for selector in title_selectors:
            try:
                title_input = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if title_input:
                    print(f"  ✓ Found title input with: {selector}")
                    break
            except TimeoutException:
                continue
        
        if not title_input:
            # Debug: print all input/textarea elements
            print("  DEBUG: Searching for all input/textarea elements...")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            for idx, inp in enumerate(inputs):
                try:
                    print(f"    input[{idx}]: id={inp.get_attribute('id')}, name={inp.get_attribute('name')}, placeholder={inp.get_attribute('placeholder')}, type={inp.get_attribute('type')}, class={inp.get_attribute('class')}")
                except:
                    pass
            for idx, ta in enumerate(textareas):
                try:
                    print(f"    textarea[{idx}]: id={ta.get_attribute('id')}, name={ta.get_attribute('name')}, placeholder={ta.get_attribute('placeholder')}, class={ta.get_attribute('class')}")
                except:
                    pass
            
            # Last resort: find any visible input/textarea near "title" label
            try:
                title_input = driver.find_element(By.XPATH, "//label[contains(., 'Title')]/following::input[1] | //label[contains(., 'Title')]/following::textarea[1]")
                print("  ✓ Found title input via label")
            except NoSuchElementException:
                pass
        
        if not title_input:
            return {"status": "FAILED", "reason": "Could not find title input"}
        
        title_input.clear()
        title_input.send_keys(title)
        print("  ✓ Title filled")
        time.sleep(0.5)
        title_input.clear()
        title_input.send_keys(title)
        print("✓ Title filled")
        time.sleep(0.5)

        # Fill body - Reddit uses a contenteditable div or textarea
        body_selectors = [
            "[data-testid='post-content-editor']",
            "[role='textbox']",
            ".public-DraftEditor-content",
            "textarea[placeholder*='Text']",
            "div[contenteditable='true']"
        ]

        body_filled = False
        for selector in body_selectors:
            try:
                body_elem = driver.find_element(By.CSS_SELECTOR, selector)
                if body_elem.is_displayed():
                    body_elem.click()
                    time.sleep(0.5)
                    body_elem.clear()
                    body_elem.send_keys(body)
                    print("  ✓ Body filled")
                    body_filled = True
                    break
            except NoSuchElementException:
                continue

        if not body_filled:
            # Try JavaScript injection as fallback
            try:
                driver.execute_script("""
                    var editors = document.querySelectorAll('[contenteditable="true"], [role="textbox"], textarea');
                    for (var i = 0; i < editors.length; i++) {
                        if (editors[i].offsetParent !== null) {
                            editors[i].focus();
                            editors[i].innerText = arguments[0];
                            editors[i].dispatchEvent(new Event('input', {bubbles: true}));
                            return true;
                        }
                    }
                    return false;
                """, body)
                print("  ✓ Body filled via JS")
                body_filled = True
            except Exception as e:
                print(f"  ✗ Failed to fill body: {e}")

        if not body_filled:
            return {"status": "FAILED", "reason": "Could not fill body"}

        time.sleep(1)

        # Click Post button
        post_button_selectors = [
            "[data-testid='submit-button']",
            "button[type='submit']",
            "button[data-click-id='submit']"
        ]

        posted = False
        for selector in post_button_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed() and btn.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.5)
                    btn.click()
                    print("  ✓ Post button clicked")
                    posted = True
                    break
            except NoSuchElementException:
                continue

        if not posted:
            # Try XPath for button containing "Post"
            try:
                btn = driver.find_element(By.XPATH, "//button[contains(., 'Post')]")
                if btn.is_displayed() and btn.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.5)
                    btn.click()
                    print("  ✓ Post button clicked (XPath)")
                    posted = True
            except NoSuchElementException:
                pass

        if not posted:
            return {"status": "FAILED", "reason": "Could not find/click Post button"}

        # Wait for result
        time.sleep(5)

        # Check result
        current_url = driver.current_url
        page_source = driver.page_source

        if "/comments/" in current_url:
            print(f"✓ POSTED successfully: {current_url}")
            return {"status": "POSTED", "url": current_url}
        elif "submitted" in page_source.lower() or "posted" in page_source.lower():
            print("✓ POSTED (detected success message)")
            return {"status": "POSTED", "url": current_url}
        elif "removed" in page_source.lower() or "auto-removed" in page_source.lower() or "moderator" in page_source.lower():
            print("⚠ AUTO-REMOVED (likely karma/age filter)")
            return {"status": "AUTO-REMOVED", "url": current_url}
        elif "error" in page_source.lower() or "something went wrong" in page_source.lower():
            print("✗ FAILED (error detected)")
            return {"status": "FAILED", "reason": "Reddit error page", "url": current_url}
        else:
            print(f"? UNKNOWN - check manually: {current_url}")
            return {"status": "UNKNOWN", "url": current_url}

    except TimeoutException as e:
        return {"status": "FAILED", "reason": f"Timeout: {e}"}
    except Exception as e:
        return {"status": "FAILED", "reason": f"Exception: {e}"}


def main():
    print("Setting up Firefox with copied profile...")
    driver = setup_driver()

    try:
        print("Checking login status...")
        if not check_logged_in(driver):
            print("\n✗ STOPPING: Not logged in as hgentic001")
            print("Please log in to Reddit in your main Firefox first.")
            return

        results = []
        for i, post in enumerate(POSTS):
            result = submit_post(driver, post)
            result["subreddit"] = post["subreddit"]
            results.append(result)

            # Space posts apart
            if i < len(POSTS) - 1:
                print("Waiting 10 seconds before next post...")
                time.sleep(10)

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        for r in results:
            status = r["status"]
            sub = r["subreddit"]
            extra = ""
            if "url" in r:
                extra = f" -> {r['url']}"
            elif "reason" in r:
                extra = f" ({r['reason']})"
            print(f"  r/{sub:<12} {status}{extra}")

    finally:
        print("\nClosing browser...")
        driver.quit()


if __name__ == "__main__":
    main()