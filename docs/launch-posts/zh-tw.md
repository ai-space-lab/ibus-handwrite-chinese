# 發布貼文草稿 — 繁體中文 (台灣/香港)

> 供作者審核用，請勿直接發布。每篇皆在 400 字內。
> 請在 B1.1 錄製完成後替換 Demo GIF 網址，或改連結安裝頁面。
>
> 共用素材：
> - Demo GIF: `https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif`
> - 安裝頁面: `https://ai-space-lab.github.io/ibus-handwrite-chinese/`
> - GitHub Repo: `https://github.com/ai-space-lab/ibus-handwrite-chinese`
> - Releases: `https://github.com/ai-space-lab/ibus-handwrite-chinese/releases`
> - 一鍵安裝: `bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart`

---

## 1. HKLUG / Taiwan Linux User Group (FB 群組通用版)

**標題：**  Linux 也能用觸控板手寫中文了 — macOS 風格 IBus 引擎，支援 18,710 字

**內文：**

一直很煩：明明會寫這個字，卻只能靠注音/拼音慢慢打。乾脆自己寫一個把觸控板變成手寫板的 IBus 引擎，體驗像 macOS 一樣順手。

切到「中文手寫」，用一根手指在觸控板寫字，深色浮動候選框就會出現在游標旁。單指點選、雙指左右滑頁、滑動動量翻頁都支援。辨識用 ONNX Runtime 本地跑 PP-OCRv6，覆蓋 18,710 字。實測 40 筆真人手寫樣本 top-1 準確率 100%（平均信心度 94.97%），樣本數不大，姑且視為 promising，日常用起來很穩。

亮點：
- macOS 風格浮動候選框，貼著游標出現
- 直接用 evdev 讀觸控板（不需手寫板），無觸控板可用滑鼠備援
- 點選、雙指滑頁、滑動動量
- 6 分頁 GTK 設定介面（模型、引擎、視窗、用戶字典、快捷鍵）
- 設定介面可按需下載模型（tiny / small / medium）
- 本地用戶字典，會學你常用的字
- 快捷鍵全可自訂

安裝（自動偵測發行版）：

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

Demo: https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif  
安裝教學: https://ai-space-lab.github.io/ibus-handwrite-chinese/  
原始碼 & Releases: https://github.com/ai-space-lab/ibus-handwrite-chinese

實測平台：Acer Aspire (HTIX5288) 與 MacBook Pro (bcm5974) 觸控板。其他有觸控偵測的觸控板理論上也能用，但未測試。歡迎回報問題與建議！

#Linux #IBus #中文輸入法 #手寫輸入 #觸控板 #開源軟體 #HKLUG #TaiwanLinux

---

## 2. 針對 Arch Linux 使用者 (Arch Linux 中文社群 / Arch Linux Taiwan)

**標題：**  Arch 也能用觸控板手寫中文了 — IBus 引擎 + PKGBUILD + 一鍵安裝

**內文：**

不想每次都要跟注音/拼音鬥智慧？現在有個 IBus 引擎能在觸控板上 macOS 風格手寫中文，深度學習辨識、本地跑。

Arch 有兩條路徑：
1. 從 repo 的 PKGBUILD 自己打包：
```bash
git clone https://github.com/ai-space-lab/ibus-handwrite-chinese
cd ibus-handwrite-chinese/packaging
makepkg -si
ibus restart
```
2. 直接跑跨發行版一鍵安裝（自動處理 `pacman` + `yay` AUR）：
```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

功能：
- 深色浮動候選框貼游標，觸控板寫字、點選、滑頁
- ONNX Runtime 本地辨識 18,710 字，40 筆手寫測試 100% top-1（平均信心度 94.97%）
- 6 分頁 GTK 設定、按需下載模型、本地用戶字典、可改快捷鍵
- 無 evdev 觸控板時自動 fallback 滑鼠

Demo / 安裝教學 / Releases（含 PKGBUILD）：見上方連結

⚠️ Wayland 彈出視窗定位、SELinux evdev 存取在 Arch 未測試。AUR 套件尚未上架，目前用 PKGBUILD 或一鍵安裝。

#ArchLinux #ArchLinuxTW #IBus #中文輸入法 #手寫 #AUR

---

## 3. 針對 Fedora 使用者 (Fedora 中文社群 / Fedora Taiwan)

**標題：**  Fedora 觸控板手寫中文 — IBus 引擎，.rpm 一鍵裝

**內文：**

用 Fedora 又想手寫中文？這個 IBus 引擎讓你在觸控板寫字、macOS 風格候選框，深度學習本地辨識。

Fedora 裝法：從 Releases 抓 `.rpm`：
```bash
sudo rpm -i <releases-裡的-filename>
ibus restart
```
或用一鍵安裝（自動偵測 Fedora 跑 `dnf` + 下載模型）：
```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

為什麼值得試：
- evdev 讀觸控板，深色候選框貼游標，點選、雙指滑頁
- ONNX Runtime 18,710 字，40 筆測試 100% top-1（94.97% 平均信心度）
- 6 分頁 GTK 設定、按需下載模型、用戶字典、快捷鍵可改
- 無觸控板可用滑鼠

Demo / 安裝教學 / .rpm Releases：見上方連結

⚠️ SELinux evdev 存取、Wayland 彈出視窗定位在 Fedora 未測試。需 Fedora 40+。實測 Acer Aspire 與 MacBook Pro 觸控板。

#Fedora #FedoraTaiwan #IBus #中文輸入法 #手寫 #rpm

---

## 4. 針對 Ubuntu / Mint 使用者 (Ubuntu Taiwan / Linux Mint 台灣社群 / Ubuntu HK)

**標題：**  Ubuntu / Mint 觸控板手寫中文 — IBus 引擎，.deb + 一鍵安裝

**內文：**

不想拼注音/拼音？這個 IBus 引擎支援觸控板 macOS 風格手寫中文，深度學習本地辨識。

Ubuntu / Mint 兩種裝法。從 Releases 抓 `.deb`：
```bash
sudo dpkg -i <releases-裡的-filename> && sudo apt install -f
ibus restart
```
或一鍵安裝（自動偵測 Ubuntu/Mint 跑 `apt` + 下載模型）：
```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

功能：
- 浮動候選框貼游標，觸控板單指寫字、點選、雙指滑頁
- ONNX Runtime 本地辨識 18,710 字，40 筆測試 100% top-1（94.97% 平均信心度）
- 6 分頁 GTK 設定、按需下載模型、本地用戶字典、快捷鍵全可改
- 無 evdev 觸控板 fallback 滑鼠

Demo / 安裝教學 / .deb Releases：見上方連結

需 Ubuntu 22.04+ / Mint 21+。實測 Acer Aspire 與 MacBook Pro 觸控板；其他支援觸控的觸控板應可用但未測試。

#Ubuntu #UbuntuTaiwan #LinuxMint #IBus #中文輸入法 #手寫 #deb

---

## 5. 通用精簡版（適合快速分享、轉發、貼文字數受限處）

**標題：**  Linux 觸控板手寫中文 IBus 引擎 — macOS 風格、本地 AI 辨識、一鍵安裝

**內文：**

把筆記本觸控板變成中文手寫板，像 macOS 一樣順手。切到「中文手寫」，一指寫字、點選、雙指滑頁。ONNX Runtime 本地跑 PP-OCRv6，18,710 字，40 筆實測 100% top-1。

✅ macOS 風格浮動候選框  
✅ evdev 觸控板直讀、滑鼠備援  
✅ 6 分頁 GTK 設定、按需下載模型、用戶字典、快捷鍵全可改  
✅ 跨發行版一鍵安裝（Arch/Ubuntu/Fedora/Mint/openSUSE 自動偵測）

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

🎬 Demo: https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif  
📦 安裝教學 & 下載: https://ai-space-lab.github.io/ibus-handwrite-chinese/  
💻 原始碼: https://github.com/ai-space-lab/ibus-handwrite-chinese

實測 Acer Aspire + MacBook Pro 觸控板。Wayland/SELinux 相關未測試，歡迎回報。

#Linux #IBus #中文輸入法 #手寫輸入 #觸控板 #開源 #HKLUG #TaiwanLinux #ArchLinux #Fedora #Ubuntu