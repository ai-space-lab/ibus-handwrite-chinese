# IBus 中文手寫輸入法

[![CI](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/ci.yml/badge.svg)](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/ci.yml)
[![Release](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/release.yml/badge.svg)](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/release.yml)

一款 Linux 平臺的中文手寫輸入法，採用 macOS 風格浮動面板、evdev 觸控板整合和 PP-OCRv6 ONNX 深度學習引擎。

![screenshot](docs/screenshot.png)

## 功能特點

- **macOS 風格彈出面板**：深色浮動視窗，候選詞嵌入面板頂部
- **evdev 觸控板輸入**：在筆記型電腦觸控板上書寫漢字 —— 支援所有支援 BTN_TOUCH + ABS_X/ABS_MT_POSITION_X 的現代觸控板（Synaptics、ELAN、ALPS、bcm5974）
- **點擊選擇**：輕觸觸控板即可選擇候選詞 —— 空間映射匹配候選詞位置
- **雙指滑動**：雙指左右滑動翻頁瀏覽候選詞
- **刪除筆畫**：⌫ 按鈕可撤銷上一筆畫
- **關閉按鈕**：左上角始終顯示 × 按鈕，點擊關閉並恢復上一輸入法
- **ESC 狀態機**：按一次 ESC 暫停（釋放觸控板，顯示「已暫停」遮罩），再按一次 ESC 關閉並恢復上一輸入法；點擊視窗恢復
- **智慧視窗定位**：彈出面板自動避開當前活動視窗，不遮擋應用程式畫面
- **拖曳手柄**：頂部欄自訂拖曳手柄可隨意移動視窗位置
- **滑鼠備用**：如無 evdev 觸控板，可使用滑鼠繪圖
- **PP-OCRv6 深度學習引擎**：基於 ONNX 的 CNN 辨識，覆蓋 18710 個漢字，使用 MAX 池化置信度評分
- **'--test' 測試模式**：獨立 GTK 視窗（無需 IBus），適合快速測試、資料收集和除錯

## 跨發行版支援

`bootstrap.sh` 自動檢測您的 Linux 發行版並安裝全部依賴：

| 發行版 | 安裝方式 | 模型來源 |
|--------|----------|----------|
| Debian 12+, Ubuntu 22.04+, Mint 21+ | `apt` + 下載 | 系統套件 + PP-OCRv6 ONNX 模型 |
| Fedora 39+ | `dnf` + 下載 | PP-OCRv6 ONNX 模型 |
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
bash <(curl -s https://raw.githubusercontent.com/vinceyap88/ibus-handwrite-chinese/main/bootstrap.sh)
ibus restart
```

**Debian/Ubuntu/Mint** 使用者也可使用傳統方式：

```bash
sudo apt install python3-evdev
git clone https://github.com/vinceyap88/ibus-handwrite-chinese
cd ibus-handwrite-chinese
sudo ./install.sh          # 已安裝依賴可加 --skip-deps
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
2. 深色浮動面板將在螢幕右下角出現
3. 用單指在觸控板上書寫漢字
4. 候選字顯示在面板頂部
5. 輕觸觸控板選擇候選詞（空間映射）
6. 雙指左右滑動翻頁
7. 按 **⌫** 撤銷上一筆畫
8. 點擊面板左上角 **×** 關閉並恢復上一輸入法，或按 **ESC** 暫停（釋放觸控板）
9. 再按 **ESC** 關閉並恢復上一輸入法
10. 點擊面板恢復（暫停狀態下）
11. 如需不切換 IME 進行測試，在終端執行 `python3 src/ibus-engine-handwrite-chinese --test` — 獨立 GTK 視窗將出現，辨識結果記錄到 `/tmp/ppocr-recognition.log`

## 疑難排解

- **觸控板無法使用**：執行 `sudo udevadm trigger` 套用 udev 規則，或將使用者加入 `input` 群組：`sudo usermod -a -G input $USER && reboot`
- **IBus 未辨識輸入法**：安裝後執行 `ibus restart`
- **輸入法無法啟動**：切換到輸入法時查看 `journalctl -f` 取得錯誤訊息
- **權限被拒絕**：用 `getfacl /dev/input/event*` 驗證 —— 您的使用者應對觸控板裝置有 `rw` 權限

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

## 授權條款

GPLv3 — 由相依函式庫要求（python3-evdev、ibus）。

## 軟體套件

預先建置的軟體套件可在 [GitHub Release](https://github.com/vinceyap88/ibus-handwrite-chinese/releases) 頁面下載：

| 格式 | 安裝命令 | 發行版 |
|------|----------|--------|
| `.deb` | `sudo dpkg -i <file> && sudo apt install -f` | Debian 11+, Ubuntu 22.04+, Mint 21+ |
| `.rpm` | `sudo rpm -i <file>` | Fedora 40+, openSUSE Tumbleweed |
| `PKGBUILD` | 參考 `packaging/PKGBUILD` | Arch Linux（需手動提交到 AUR）|

軟體套件在推送標籤時由 CI 自動建置。安裝後自動下載 PP-OCRv6 ONNX 模型（非致命失敗）。

## PP-OCRv6 整合

PP-OCRv6 ONNX 模型（MobileNetV3 small，訓練於 18710 個漢字）是唯一辨識引擎。

### 架構

引擎使用 PP-OCRv6 ONNX 執行階段，採用 CTC 解碼和 MAX 池化置信度評分。

### 設定

1. 透過 `bootstrap.sh` 或 `install.sh` 下載 PP-OCRv6 ONNX 模型及字典
2. 透過環境變數設定 ONNX 模型路徑：
   ```bash
   export IBUS_HANDWRITE_PPOCR_MODEL=small  # 或 large、server（預設：small）
   export IBUS_HANDWRITE_PPOCR_MODEL_PATH=/tmp/models/ppocrv6_small.onnx
   export IBUS_HANDWRITE_PPOCR_DICT_PATH=/tmp/models/dict_v6.txt
   ```
3. 照常切換引擎：
   ```bash
   ibus engine handwrite-chinese
   ```

### 無需 IBus 測試

以獨立 `--test` 模式執行引擎，測試辨識功能無需切換 IME：
```bash
python3 src/ibus-engine-handwrite-chinese --test
```
這將開啟一個 GTK 浮動視窗，您可以在其中繪製字元。辨識結果顯示在 `/tmp/ppocr-recognition.log`。

### 已修復的 Bug

驗證過程中發現並修復了 PP-OCRv6 管線的三個 Bug：

1. **字典索引損壞**（第 290 行）：`line.strip()` 從字典條目中剝離了 U+3000（表意空格），導致後續所有字元索引偏移 1。修復為 `line.rstrip('\n')`。
2. **置信度池化**（第 405 行）：`np.mean(probs, axis=0)` 對所有 CTC 時間步（包括空白幀）取平均，使真實置信度稀釋約 10 倍。修復為 `np.max(probs, axis=0)`（MAX 池化），符合單字元辨識的 CTC argmax 行為。
3. **筆畫線寬**（第 364 行）：`cr.set_line_width(6)` 渲染的筆畫比訓練資料分佈更細。增加到 `set_line_width(8)`。

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

## 目錄結構

```
├── scripts/
│   ├── analyze_ppocr_data.py          PP-OCRv6 精度分析管線
│   ├── collect_ppocr_data.py          互動式手寫資料收集
│   ├── capture_one.py                 單筆畫收集輔助工具
│   ├── gtk_collect_loop.py            基於日誌的 GTK 收集指令碼
│   └── read_last_log.py               辨識日誌讀取器
├── src/
│   ├── ibus-engine-handwrite-chinese    主引擎（Python、PP-OCRv6 ONNX、GTK 彈出面板、evdev 整合）
│   └── handwrite_evdev.py               Evdev 多點觸控讀取模組
├── xml/
│   └── handwrite-chinese.xml            IBus 元件
├── icons/
│   └── handwrite-chinese.svg            引擎圖示
├── tools/
│   ├── install.sh                       安裝指令碼（Debian 原生，支援 `--skip-deps`）
│   ├── restore.sh                       回滾/恢復指令碼
│   └── 99-trackpad-handwrite.rules      觸控板存取的 udev 規則
├── tests/
│   ├── test_recognition.py             合成筆畫辨識冒煙測試
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
├── README.zh-Hans.md
└── README.zh-Hant.md
```
