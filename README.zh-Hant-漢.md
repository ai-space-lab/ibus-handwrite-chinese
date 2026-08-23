# IBus 中文手寫輸入法

[![CI](https://github.com/ai-space-lab/ibus-handwrite-chinese/actions/workflows/ci.yml/badge.svg)](https://github.com/ai-space-lab/ibus-handwrite-chinese/actions/workflows/ci.yml)
[![Release](https://github.com/ai-space-lab/ibus-handwrite-chinese/actions/workflows/release.yml/badge.svg)](https://github.com/ai-space-lab/ibus-handwrite-chinese/actions/workflows/release.yml)

一款 Linux 平臺的中文手寫輸入法，採用 macOS 風格浮動面板、evdev 觸控板整合和 PP-OCRv6 ONNX 深度學習引擎。

![screenshot](docs/screenshot.png)

## 功能特點

- **macOS 風格彈出面板**：深色浮動視窗，候選詞嵌入面板頂部
- **evdev 觸控板輸入**：在筆記型電腦觸控板上書寫漢字 —— 支援所有支援 BTN_TOUCH + ABS_X/ABS_MT_POSITION_X 的觸控板（已在 MacBook Pro bcm5974 上測試通過——其他支援 BTN_TOUCH + ABS_X/ABS_MT_POSITION_X 的觸控板可能可用，但未經測試）
- **點擊選擇**：輕觸觸控板即可選擇候選詞 —— 空間映射匹配候選詞位置
- **雙指滑動**：雙指左右滑動翻頁瀏覽候選詞
- **滑動慣性**：快速雙指滑動會慣性減速穿越多頁 —— 滑得越快，翻頁越多
- **單指候選拖動**：在觸控板頂部 5% 區域內單指拖動，按位置高亮候選詞，抬指選擇
- **非破壞性多點觸控**：書寫時意外觸碰到第二根手指不會破壞當前筆畫 —— 引擎會自動儲存和恢復筆畫狀態
- **刪除筆畫**：⌫ 按鈕可撤銷上一筆畫
- **關閉按鈕**：左上角始終顯示 × 按鈕，點擊關閉並恢復上一輸入法
- **ESC 狀態機**：按一次 ESC 暫停（釋放觸控板，顯示「已暫停」遮罩），再按一次 ESC 關閉並恢復上一輸入法；點擊視窗恢復。**Enter 有候選字時**提交首個候選字；**Enter 無候選字時**傳遞到下層應用程式。
- **智慧視窗定位**：彈出面板自動出現在文字游標附近，不遮擋應用程式畫面
- **拖曳手柄**：頂部欄自訂拖曳手柄可隨意移動視窗位置
- **滑鼠備用**：如無 evdev 觸控板，可使用滑鼠繪圖
- **偏好設定對話框**：6 標籤 GTK3 設定介面（一般、模型、引擎、視窗、使用者辭典、快捷鍵）—— 可從 IBus 選單或透過 `ibus-setup handwrite-chinese` 開啟
- **隨需模型下載**：直接從偏好設定對話框下載 PP-OCRv6 模型（tiny/small/medium），自動使用 pkexec 提權進行系統級安裝
- **自動下載提示**：選取未下載的模型等級時自動詢問是否立即下載
- **可設定鍵盤快捷鍵**：透過快捷鍵標籤頁自訂所有按鍵綁定（ESC、Enter、Backspace、翻頁、主題切換、設定）
- **使用者辭典**：透過本機 SQLite 資料庫學習使用者選取的漢字，在後續辨識中提升其優先級
- **TOML 設定檔**：所有設定儲存在 `~/.config/ibus-handwrite-chinese/config.toml`，可透過 `IBUS_HANDWRITE_*` 環境變數覆蓋
- **PP-OCRv6 深度學習引擎**：基於 ONNX 的 CNN 辨識，覆蓋 18710 個漢字，使用 MAX 池化置信度評分
- **'--test' 測試模式**：獨立 GTK 視窗（無需 IBus），適合快速測試、資料收集和除錯

## 跨發行版支援

`bootstrap.sh` 自動檢測您的 Linux 發行版並安裝全部依賴：

| 發行版 | 安裝方式 | 模型來源 |
|--------|----------|----------|
| Debian 12+, Ubuntu 22.04+, Mint 21+ | `apt` + 下載 | 系統套件 + PP-OCRv6 ONNX 模型 |
| Fedora 40+ | `dnf` + 下載 | PP-OCRv6 ONNX 模型 |
| Arch Linux, Manjaro | `pacman` + `yay` (AUR) + 下載 | PP-OCRv6 ONNX 模型 |
| openSUSE Tumbleweed | `zypper` + 下載 | PP-OCRv6 ONNX 模型 |

安裝程式自動下載 PP-OCRv6 ONNX 模型（覆蓋 18710 個漢字）用於深度學習辨識。

## 系統需求

- Linux 系統，帶觸控板（或觸控螢幕）
- IBus 輸入法框架（大多數桌面環境預設安裝）
- **Debian 系列**：Debian 11+、Ubuntu 22.04+、Linux Mint 21+
- **Fedora**：Fedora 40+
- **Arch**：Arch Linux、Manjaro
- **openSUSE**：Tumbleweed

## 快速安裝

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh)
ibus restart
```

**Debian/Ubuntu/Mint** 使用者也可使用傳統方式：

```bash
sudo apt install python3-evdev python3-venv
git clone https://github.com/ai-space-lab/ibus-handwrite-chinese
cd ibus-handwrite-chinese
./tools/install.sh    # sudo 在內部自動使用
ibus restart
```

`install.sh` 自動下載 PP-OCRv6 ONNX 模型（覆蓋 18710 個漢字）用於深度學習辨識。

切換輸入法：

```bash
ibus engine handwrite-chinese
```

或者從桌面環境的 IBus 選單中選擇 **Chinese Handwriting**。

## 使用方法

1. 從 IBus 選單切換到 **Chinese Handwriting**
2. 深色浮動面板將出現在您的文字游標附近
3. 用單指在觸控板上書寫漢字
4. 候選字顯示在面板頂部
5. 輕觸觸控板選擇候選詞（空間映射）
6. 雙指左右滑動翻頁
7. 按 **⌫** 撤銷上一筆畫
8. 按 **ESC** 暫停（視窗顯示「已暫停」遮罩）
9. 再按 **ESC** 關閉並恢復上一輸入法
10. 點擊視窗恢復（暫停狀態下）
11. 當無候選字時（未繪製筆畫），**Enter** 鍵傳遞到應用程式 — 可在終端正常打字
12. 如需不切換 IME 進行測試，使用 venv Python：
    ```bash
    /usr/local/share/ibus-handwrite-chinese/venv/bin/python3 \
      /usr/local/share/ibus-handwrite-chinese/ibus-engine-handwrite-chinese --test
    ```
    辨識結果記錄到 `/tmp/ppocr-recognition.log`。

## 疑難排解

- **觸控板無法使用**：執行 `sudo udevadm trigger` 套用 udev 規則，或將使用者加入 `input` 群組：`sudo usermod -a -G input $USER && reboot`
- **IBus 未辨識輸入法**：安裝後執行 `ibus restart`
- **輸入法無法啟動**：切換到輸入法時查看 `journalctl -f` 取得錯誤訊息
- **權限被拒絕**：用 `getfacl /dev/input/event*` 驗證 —— 您的使用者應對觸控板裝置有 `rw` 權限
- **ESC 不工作 / Enter 被引擎攔截**：如果按 ESC 暫停後 Enter 無法傳遞到終端，請用最新版 `install.sh` 重新安裝。修復確保：(1) 無候選字時 Enter 可通過，(2) 暫停狀態下按 ESC 關閉並恢復上一輸入法，(3) ESC 現在可在 Firefox 和其他設定 IBUS_RELEASE_MASK 的應用程式中正常運作。

## 測試

兩個工作流分別覆蓋開發和發佈：

### 主 CI

[主 CI](.github/workflows/ci.yml) 在每次推送/PR 到 `main` 時執行，覆蓋 5 個 Docker 容器：
- **lint**：shellcheck、xmllint、Python 語法檢查
- **test-install**：按發行版安裝依賴，驗證 ONNX 執行階段載入，檢查 Python 語法
- **test-bootstrap**：完整執行 bootstrap.sh，驗證安裝檔案和模型，執行辨識冒煙測試
- **test-gtk-write**：在 10 個發行版版本上執行 GTK 書寫模擬，並上傳截圖產物

測試容器：`debian:bookworm`、`ubuntu:24.04`、`fedora:latest`、`archlinux:latest`、`opensuse/tumbleweed`。

### 發佈

[Release](.github/workflows/release.yml) 在 `v*` 標籤推送或手動觸發時執行：
- 解析發佈標籤和版本號
- 建置 `.deb`、`.rpm` 和原始碼 tarball
- 驗證發佈產物
- 上傳發佈資產到 GitHub Release

### 辨識冒煙測試

辨識冒煙測試（`tests/test_recognition.py`）建立合成筆畫：
- 水平線 → 辨識為 **一**（得分 > 0.9）
- 十字形 → 辨識為 **十**（得分 > 0.95）

CI 會在 Xvfb 下測試 GTK，但不會在容器中測試真實 IBus、evdev 或觸控板硬體。

### 手動測試環境

最近的 ESC/Enter 修復在此環境下驗證通過：

| 元件 | 詳情 |
|------|------|
| 作業系統 | Linux Mint 22.3 (Zena) XFCE |
| 核心 | 6.14.0-37-generic (x86_64) |
| 桌面環境 | XFCE on X11 |
| IBus | 1.5.29-rc2 |
| Python | 3.12.3 |
| 觸控板 | bcm5974（MacBook Pro，USB） |
| 安裝方式 | `sudo ./tools/install.sh` 或 `.deb` 套件 |

### PP-OCRv6 精度驗證

用於驗證 PP-OCRv6 辨識精度的分析指令碼：
- `scripts/collect_ppocr_data.py` — 透過 `--test` 模式（或 `--prompt` / `--free` 模式）互動式收集資料
- `scripts/analyze_ppocr_data.py` — 精度、置信度直方圖、校準、筆畫複雜度及字典索引分析
- `scripts/capture_one.py` — 單筆畫收集與辨識測試
- `scripts/gtk_collect_loop.py` — 透過日誌輪詢配合 `--test` 模式的批次收集

執行完整分析流程：
```bash
python3 scripts/analyze_ppocr_data.py --input .omo/evidence/ppocr-handwriting-dataset/dataset-chat-v1.json --verbose
```

## 已知限制

- **實機測試**：在 MacBook Pro（bcm5974）上測試通過 —— 應適用於任何支援 `BTN_TOUCH + ABS_X` 的觸控板，但 Fedora/Arch 上的 Wayland 彈出面板定位和 SELinux evdev 存取尚未測試
- **辨識精度**：使用 PP-OCRv6（18710 字，ONNX）深度學習引擎。經 40 個真實手寫字元驗證（36 個不同字，含 7 組相似字：土/士、未/末、日/曰、人/入、大/太、已/己、上/下），首選辨識率 100%，平均置信度 94.97%
- **單字輸入**：暫不支援多字組合（一次輸入一個字）。V2 版本可能加入空間分割實現連續輸入
- **ONNX 模型下載**：PP-OCRv6 模型託管在 GitHub Releases。如果下載失敗，安裝程式將發出警告並繼續。CI 容器優雅跳過下載

## 致謝

- **PP-OCRv6** — 文字辨識模型，由 [PaddlePaddle](https://github.com/PaddlePaddle/PaddleOCR) / 百度開發，採用 [Apache 2.0](https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE) 授權條款。
- **ONNX Runtime** — 跨平台推論引擎，由微軟開發，採用 [MIT](https://github.com/microsoft/onnxruntime/blob/main/LICENSE) 授權條款。

## 授權條款

GPLv3 — 由相依函式庫要求（python3-evdev、ibus）。

## 軟體套件

預先建置的軟體套件可在 [GitHub Release](https://github.com/ai-space-lab/ibus-handwrite-chinese/releases) 頁面下載：

| 格式 | 安裝命令 | 發行版 |
|------|----------|--------|
| `.deb` | `sudo dpkg -i <file> && sudo apt install -f` | Debian 11+, Ubuntu 22.04+, Mint 21+ |
| `.rpm` | `sudo rpm -i <file>` | Fedora 40+, openSUSE Tumbleweed |
| `PKGBUILD` | 參考 `packaging/PKGBUILD` | Arch Linux（需手動提交到 AUR）|

軟體套件在推送標籤時由 CI 自動建置。安裝後自動下載 PP-OCRv6 ONNX 模型（非致命失敗）。

## 設定

### 偏好設定對話框

從 IBus 選單開啟 6 標籤偏好設定對話框：
- 右鍵點擊 IBus 托盤圖示 → 偏好設定 → Chinese Handwriting
- 或執行：`ibus-setup handwrite-chinese`
- 或在桌面設定中搜尋"Chinese Handwriting"

對話框包含以下標籤：

| 標籤頁 | 設定內容 |
|--------|----------|
| **一般** | 主題（深色/淺色/自動）、日誌層級、日誌路徑 |
| **模型** | 模型等級（tiny/small/medium）、自訂模型/字典路徑、自動下載開關、帶進度指示的下載按鈕 |
| **引擎** | 筆畫寬度（px）、頁面大小、最大候選數、慣性設定、防抖定時器 |
| **視窗** | 視窗寬/高、繪製區域高度、拖曳手柄高度、候選按鈕寬度 |
| **使用者辭典** | 啟用/停用使用者辭典、提升強度、最大條目數 |
| **快捷鍵** | 自訂所有按鍵綁定（ESC、Enter、Backspace、翻頁、主題切換、開啟設定） |

變更在點選**套用**並重新啟動 IBus（`ibus restart`）後生效。

### 環境變數

所有設定均可透過 `IBUS_HANDWRITE_*` 環境變數覆蓋，優先級高於 TOML 設定檔：

| 變數 | 設定鍵 | 範例 |
|------|--------|------|
| `IBUS_HANDWRITE_THEME` | general.theme | `dark` |
| `IBUS_HANDWRITE_LOG_LEVEL` | general.log_level | `DEBUG` |
| `IBUS_HANDWRITE_PPOCR_MODEL` | model.tier | `small` |
| `IBUS_HANDWRITE_PPOCR_MODEL_PATH` | model.path | `/path/to/model.onnx` |
| `IBUS_HANDWRITE_PPOCR_DICT_PATH` | model.dict_path | `/path/to/dict.txt` |
| `IBUS_HANDWRITE_DOWNLOAD_PATH` | model.download_path | `/usr/local/share/ibus-handwrite-chinese/models` |
| `IBUS_HANDWRITE_AUTO_DOWNLOAD` | model.auto_download | `true` |
| `IBUS_HANDWRITE_STROKE_WIDTH` | engine.stroke_width | `12` |

### 模型管理

透過偏好設定對話框的**模型**標籤頁下載模型：

1. 從下拉選單中選擇等級（tiny / small / medium）
2. 如果模型尚未下載，系統會詢問是否立即下載
3. 點選**下載模型**開始下載 — 脈衝進度條顯示活動狀態
4. 模型下載到系統暫存目錄，然後複製到目標位置（必要時使用 `pkexec` 提權）
5. 字典檔（`dict_v6.txt`）在所有等級間共享
6. 下載後重新啟動 IBus 以使引擎載入新模型

您也可以透過**模型路徑**/**字典路徑**欄位設定自訂路徑，使用儲存在別處的模型。

### 模型等級

| 等級 | 參數量 | 適用場景 |
|------|--------|----------|
| tiny | 1.5M | 快速，低資源環境 |
| small | ~8M | 速度與精度均衡（預設） |
| medium | 34.5M | 最高精度 |

### 已修復的 Bug

共發現並修復了十三個 Bug，涵蓋 PP-OCRv6 管線、ESC 狀態機、Firefox 相容性、桌面/非文字區域自動暫停、模型下載、設定及偏好設定對話框：

1. **字典索引損壞**（第 290 行）：`line.strip()` 從字典條目中剝離了 U+3000（表意空格），導致後續所有字元索引偏移 1。修復為 `line.rstrip('\n')`。
2. **置信度池化**（第 405 行）：`np.mean(probs, axis=0)` 對所有 CTC 時間步（包括空白幀）取平均，使真實置信度稀釋約 10 倍。修復為 `np.max(probs, axis=0)`（MAX 池化），符合單字元辨識的 CTC argmax 行為。
3. **筆畫線寬**（第 364 行）：`cr.set_line_width(6)` 渲染的筆畫比訓練資料分佈更細。增加到 `set_line_width(8)`。

### 4. ESC 鍵可靠性 & Enter 傳遞（PR #1）
改進了 ESC 狀態機，使其在所有狀態下正確處理 Enter 鍵：

| 按鍵 | 活躍（狀態 0） | 暫停（狀態 1） |
|---|---|---|
| ESC | 暫停面板，顯示遮罩 | 關閉 + 恢復上一 IME |
| Enter + 有候選字 | 提交首個候選字 | ✅ 傳遞到應用程式 |
| Enter + 無候選字 | ✅ 傳遞到應用程式 | ✅ 傳遞到應用程式 |
| Backspace | 清除筆畫（傳遞通過） | ✅ 傳遞到應用程式 |

**根本原因**：`do_process_key_event` 在視窗可見時攔截 Enter/Backspace/ESC，無論暫停狀態或是否存在候選字。修復方法：
- 將 ESC（始終處理）與 Enter/Backspace（僅在活躍狀態 0 攔截）分離
- 添加 `self.last_results` 保護：僅在有候選字時消費 Enter
- 對 `--test` 模式使用的 GTK `on_key` 處理程序應用相同保護

### 5. `--test` 模式鍵盤焦點修復
獨立 `--test` 模式視窗無法接收 GTK 鍵盤事件，因為 `__init__` 中設定了 `set_accept_focus(False)`。透過在 `main()` 中的 `win.present()` 前呼叫 `win.set_accept_focus(True)` 修復。

### 6. Firefox ESC 相容性修復
Firefox 透過 IBus 發送 ESC 按鍵事件時會設定 `IBUS_RELEASE_MASK`（1 << 30），導致原始 ESC 處理程序在檢查 `RELEASE_MASK` 時被繞過。修復方法：
- 將 ESC 檢查移到 `do_process_key_event` 中的 `RELEASE_MASK` 過濾之前 —— 無論按下/釋放狀態，ESC 都能被處理
- 在 `on_key_esc()` 中添加 150ms 去抖，防止按下+釋放事件對的雙重觸發
- 透過 `/tmp/hw.log` 日誌分析驗證，ESC → 暫停 → 關閉狀態轉換在 Firefox 中正常運作

### 7. 無文字焦點時 ESC 暫停修復
當無文字欄位獲得焦點時（例如 Firefox 標題列、桌面），按下 ESC 暫停面板無效。存在兩種按鍵事件路徑：IBus 路徑（`do_process_key_event`）需要活躍的 IBus 輸入上下文（僅由文字輸入控制項建立），GTK 路徑（`on_key` 處理程序）需要面板擁有鍵盤焦點 —— 被 `set_accept_focus(False)` 阻止。

**根本原因**：之前的修復嘗試了 50ms 延遲焦點獲取（`_grab_focus_if_needed`），但在視窗管理器處理焦點授予前立即還原了 `set_accept_focus(False)`。日誌顯示獲取運行了但 ESC 從未到達。

**修復方法**：完全移除定時器。在 `do_enable()` 中，在 `present()` 前呼叫 `set_accept_focus(True)` 並在會話期間保持 True —— 與 `--test` 模式的做法一致。在 `do_disable()` 中重設為 `False`。透過 xdotool 驗證：當桌面聚焦時按下 ESC，記錄到 `on_key_esc: _state=0`。

### 8. 非文字區域焦點丟失時自動暫停（Firefox 標題列、桌面背景）
當使用者點擊 Firefox 標題列或桌面背景時，手寫視窗仍處於開啟狀態，但沒有任何 ESC 或鍵盤事件能到達視窗 —— IBus 上下文已不活躍（無文字欄位），視窗也沒有鍵盤焦點。

**根本原因**：存在兩條事件路徑 —— IBus 的 `do_process_key_event`（需要活躍的 IBus 輸入上下文，僅由文字輸入控制項建立）和 GTK 的 `on_key` 處理程序（需要視窗擁有鍵盤焦點）。點擊非文字區域後，兩條路徑均不可用。

**修復方法**：新增了 GTK `focus-out-event` 處理程序（`on_focus_out_event`），安排 50ms 去抖定時器。到期時，`_handle_focus_lost` 呼叫 `on_key_esc()` 自動暫停視窗。50ms 去抖可吸收 XFCE 在桌面點擊後約 20ms 觸發的虛假 `do_focus_in` 訊號。自動暫停受 `_has_drawn` 保護 —— 如果使用者尚未繪製任何筆畫，則不會自動暫停（避免啟動時的混淆行為）。

### 9. 由於 `_focused_since_enable` 競態，第二次啟動時 `present()` 被跳過
在關閉手寫視窗（透過雙擊 ESC 或切換 IME）並第二次重新啟動後，ESC 和自動暫停無聲地停止運作。視窗出現了但沒有鍵盤焦點。

**根本原因**：`_grab_focus_if_needed` 在 `do_enable()` 期間透過 `GLib.idle_add` 排程。在第二次啟動時，一個虛假的 XFCE `do_focus_in` 訊號在閒置處理程序執行前觸發，將 `_focused_since_enable` 設為 True。舊程式碼隨後完全跳過了 `self.win.present()` —— 視窗可見但沒有鍵盤焦點，因此 GTK `focus-out-event` 永遠不會觸發，ESC 鍵事件也永遠不會到達。

**修復方法**：在 `_grab_focus_if_needed` 中始終呼叫 `self.win.present()`，無論 `_focused_since_enable` 如何。這是安全的，因為在手寫模式下使用者透過觸控板/滑鼠互動，而非鍵盤 —— 視窗只需要焦點來路由 ESC 和 GTK 焦點事件。

### 10. X11 屬性刷新時序阻止 `present()` 授予焦點
即使在修復 #9 之後，某些第二次啟動嘗試仍然無法獲得鍵盤焦點。調查顯示 `on_focus_in_event` 在啟動序列中缺失，儘管呼叫了 `present()`。

**根本原因**：`set_accept_focus(True)` 和 `present()` 都在 `_grab_focus_if_needed`（GLib 閒置處理程序）內部呼叫。GTK 批次處理 X11 `WM_HINTS` 屬性變更 —— 當閒置處理程序執行時，`accept_focus=True` 尚未刷新到 X 伺服器。視窗管理器仍然看到 `accept_focus(False)`（仍然來自之前的 `do_disable()`）並拒絕了焦點請求。

**修復方法**：在 `do_enable()` 中的 `show_all()` 和 `GLib.idle_add` 之前呼叫 `self.win.set_accept_focus(True)`。當閒置處理程序觸發並呼叫 `present()` 時，X11 屬性變更已刷新到伺服器。視窗管理器看到 `accept_focus(True)` 並授予焦點，從而在每個啟動週期產生 `on_focus_in_event`，並使 ESC 和 `on_focus_out_event` 正常運作。

### 驗證結果

透過 `--test` 模式和觸控板收集的 40 個真實手寫字元：

| 指標 | 結果 |
|------|------|
| 首選準確率 | 40/40（100%） |
| 前五準確率 | 40/40（100%） |
| 平均置信度 | 94.97% |
| 最低置信度 | 34.47%（小） |
| 最高置信度 | 100.00%（月、女等） |
| 相似字組測試 | 7 組，14/14 正確 |

測試字元：一 七 三 上 下 不 中 九 二 五 人 入 八 六 十 口 四 土 士 大 天 太 女 好 小 山 己 已 心 文 日 曰 月 木 未 末 水 火 王 田

完整分析報告：`.omo/evidence/ppocr-handwriting-dataset/analysis-report.json`
瓶頸報告：`.omo/evidence/ppocr-handwriting-dataset/bottleneck-report.txt`

### 11. 模型下載權限錯誤
從偏好設定對話框下載模型時出現 `PermissionError`，原因是 `tempfile.mkdtemp()`
在 root 擁有的 `/usr/local/share/.../models/` 目錄內建立了暫存目錄。修復方法：
改為下載到系統暫存目錄（`/tmp`），並使用 `shutil.move()` 配合 `pkexec cp` 回退
方案將檔案最終複製到目標目錄。

### 12. 顯示筆畫寬度忽略偏好設定
在引擎標籤頁中變更筆畫寬度沒有可見效果 — 顯示繪製硬編碼了 `3 * scale`
而非讀取 `CONFIG["engine"]["stroke_width"]`。在 Cairo 繪製程式碼的兩處位置修復：
`rebuild_pix()`（已完成筆畫）和 `on_draw()`（即時筆畫）。辨識渲染（第 183 行）
已使用設定值。

### 13. 設定清理
移除了兩個無效設定鍵：`model.variant`（PP-OCRv6 舊命名的遺留項）和
`engine.max_strokes`（在設定和偏好設定 UI 中定義但引擎從未讀取）。

## 目錄結構

```
├── scripts/
│   ├── analyze_ppocr_data.py          PP-OCRv6 精度分析管線
│   ├── collect_ppocr_data.py          互動式手寫資料收集
│   ├── capture_one.py                 單筆畫收集輔助工具
│   ├── gtk_collect_loop.py            基於日誌的 GTK 收集指令碼
│   └── read_last_log.py               辨識日誌讀取器
├── src/
│   ├── ibus-engine-handwrite-chinese    主引擎（Python、GTK 彈出面板、evdev 整合）
│   ├── handwrite_config.py              TOML/環境變數設定載入器
│   ├── handwrite_model_download.py      PP-OCRv6 模型下載器（含 SHA256 驗證）
│   ├── handwrite_prefs.py               6 標籤 GTK3 偏好設定對話框
│   ├── handwrite_shortcuts.py           可設定的按鍵綁定系統
│   ├── handwrite_userdict.py            基於 SQLite 的使用者字元學習模組
│   └── handwrite_evdev.py               Evdev 多點觸控讀取模組
├── xml/
│   └── handwrite-chinese.xml            IBus 元件
├── icons/
│   └── handwrite-chinese.svg            引擎圖示
├── tools/
│   ├── install.sh                       安裝指令碼（Debian 原生，支援 `--skip-deps`）
│   ├── restore.sh                       回滾/恢復指令碼
│   ├── 99-trackpad-handwrite.rules      觸控板存取的 udev 規則
│   └── diagnose_trackpad.sh            ESC + input 組 + IBus 診斷
├── tests/
│   ├── test_recognition.py             合成筆畫辨識冒煙測試
│   ├── test_esc_key_routing.py         ESC 按鍵路由自動化測試
│   └── test_data/                      測試筆畫資料
├── docs/
│   └── screenshot.png                   應用截圖
│   ├── plan-handwriting-accuracy-test.md 辨識精度測試方案（歷史文件）
│   └── multi-char-composition-with-phrase-boost-plan.md  V2 功能規劃
├── models/                              本地模型快取（gitignore）
├── packaging/                            Debian 打包、RPM spec、PKGBUILD
├── .github/workflows/
│   ├── ci.yml                          主 CI — 5 個發行版
│   └── release.yml                     發佈建置、驗證、上傳
├── .omo/
│   └── evidence/ppocr-handwriting-dataset/  精度驗證證據
│       ├── dataset-chat-v1.json              40 個手寫樣本，100% 準確率
│       ├── analysis-report.json              完整分析報告及指標
│       └── bottleneck-report.txt             Bug 修復與驗證報告
├── bootstrap.sh                        跨發行版安裝入口
├── README.md
├── README.zh-Hans-汉.md
└── README.zh-Hant-漢.md
```
