# Linux 也能用觸控板手寫中文了？macOS 風格 IBus 引擎，18,710 字離線辨識

**作者：Mint User**  
**發布日期：2026年8月**  
**標籤：#Linux #IBus #中文輸入法 #開源軟體 #手寫輸入 #觸控板**

---

## 前言

很多人問我：為什麼要用手寫輸入法？明明有拼音/注音啊？

我是這樣想的：當我只記得這個字的筆畫，卻忘記拼音怎麼打時，我就很煩。也許你也有同感。

於是我寫了一個 IBus 引擎，把筆記型電腦的觸控板變成手寫板。像 macOS 一樣，用一根手指在觸控板上畫字，候選框就會出現在游標旁。單指點選、雙指左右滑頁、滑動動量翻頁都支援。

---

## 什麼是 ibus-handwrite-chinese？

**ibus-handwrite-chinese** 是一個 Linux 的 IBus 引擎，提供 macOS 風格的手寫輸入體驗：

- **觸控板直讀**：直接用 evdev 讉觸控板，無需手寫板
- **深度學習辨識**：PP-OCRv6 ONNX Runtime，覆蓋 18,710 字
- **本地運算**：模型和辨識全在本機進行，隱私安全
- **6 分頁 GTK 設定介面**：模型、引擎、視窗、用戶字典、快捷鍵全自訂
- **跨發行版一鍵安裝**：支援 Debian/Ubuntu/Fedora/Arch/openSUSE

---

## 亮點功能

| 功能 | 說明 |
|------|------|
| macOS 風格浮動候選框 | 貼著游標出現，看起來很順手 |
| 直接用觸控板寫字 | 只要有觸控偵測即可，不需手寫板 |
| 點選、雙指滑頁、滑動動量 | 手勢操作極其自然 |
| 6 分頁 GTK 設定介面 | 模型、引擎、視窗、用戶字典、快捷鍵全自訂 |
| 本地用戶字典 | 會學你常用的字，辨識越來越準 |
| 快捷鍵全可自訂 | ESC、Enter、Backspace、頁上頁下等盡可重新綁定 |
| 跨發行版一鍵安裝 | `bootstrap.sh` 自動偵測發行版並安裝 |

---

## 安裝方式

### 一鍵安裝（推薦）

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

### 手動安裝

**Debian/Ubuntu/Mint**：
```bash
sudo apt install python3-evdev python3-venv
git clone https://github.com/ai-space-lab/ibus-handwrite-chinese
cd ibus-handwrite-chinese
./tools/install.sh
ibus restart
```

**Fedora**：
```bash
sudo dnf install ibus-devel python3-devel
git clone https://github.com/ai-space-lab/ibus-handwrite-chinese
cd ibus-handwrite-chinese
./tools/install.sh
ibus restart
```

**Arch/Manjaro**：
```bash
# 使用 PKGBUILD
git clone https://github.com/ai-space-lab/ibus-handwrite-chinese
cd ibus-handwrite-chinese/packaging
makepkg -si
# 或使用一鍵安裝
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

---

## 實測結果

| 測試項目 | 結果 |
|----------|------|
| 40 筆真人手寫樣本 top-1 準確率 | 100% |
| 平均信心度 | 94.97% |
| 測試字符 | 一 七 三 上 下 不 中 九 二 五 人 入 八 六 十 口 四 土 士 大 天 太 女 好 小 山 己 已 心 文 日 曰 月 木 未 末 水 火 王 田 |
| 測試平台 | Acer Aspire (HTIX5288) 與 MacBook Pro (bcm5974) 觸控板 |

---

## 專案資源

- **GitHub 專案**：https://github.com/ai-space-lab/ibus-handwrite-chinese
- **GitHub 發行版**：https://github.com/ai-space-lab/ibus-handwrite-chinese/releases
- **安裝頁面**：https://ai-space-lab.github.io/ibus-handwrite-chinese/
- **Demo GIF**：https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif
- **說明文件**：https://github.com/ai-space-lab/ibus-handwrite-chinese/wiki

---

## 使用心得

安裝後切換到「中文手寫」輸入法，就可以在觸控板上畫字了。畫出來的字會出現在游標旁的深色浮動候選框裡。單指點選想要的字，雙指左右滑頁翻頁。速度其實不慢，因為候選框會根據手勢位置顯示對應的字。

用了幾天後，本地用戶字典開始學習我常用的字，辨識度越來越高。特別是一些生僻字，有了用戶字典後基本都能認出來。

唯一的缺點是，Wayland 環境下的彈出視窗定位和 SELinux 的 evdev 存取在某些發行版上可能需要額外設定。但總體來說，這是一個非常實用的工具，特別是對於那些忘記拼音但會寫字的人來說。

---

## 支持項目

如果你覺得這個項目對你有幫助，歡迎：

- **Star** the GitHub 專案
- **分享** 給需要的朋友
- **回報問題** 或 **建議新功能**
- **翻譯** 文檔到其他語言

---

## 結語

`ibus-handwrite-chinese` v0.6.0 已經準備好，歡迎大家嘗試使用。無論是開發者、Linux 愛好者，還是只是想嘗試不同輸入方式的用戶，都歡迎加入這個項目。

**版本**：v0.6.0  
**授權**：GPLv3  
**作者**：Mint User <mint@ibus-handwrite>

---
*本文同步發布於：GitHub、知乎、Reddit*  
*如有誤記或建議，歡迎在評論區指正。*