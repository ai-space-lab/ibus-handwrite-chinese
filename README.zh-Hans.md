# IBus 中文手写输入法

[![CI](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/ci.yml/badge.svg)](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/ci.yml)
[![Release](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/release.yml/badge.svg)](https://github.com/vinceyap88/ibus-handwrite-chinese/actions/workflows/release.yml)

一款 Linux 平台的中文手写输入法，采用 macOS 风格浮动面板、evdev 触摸板集成和双识别引擎：幽兰百合 Zinnia 和 PP-OCRv6 ONNX 深度学习引擎。

![screenshot](docs/screenshot.png)

## 功能特点

- **macOS 风格弹出面板**：深色浮动窗口，候选词嵌入面板顶部
- **evdev 触摸板输入**：在笔记本电脑触摸板上书写汉字 —— 支持所有支持 BTN_TOUCH + ABS_X/ABS_MT_POSITION_X 的现代触摸板（Synaptics、ELAN、ALPS、bcm5974）
- **点击选择**：轻触触摸板即可选择候选词 —— 空间映射匹配候选词位置
- **双指滑动**：双指左右滑动翻页浏览候选词
- **删除笔画**：⌫ 按钮可撤销上一笔画
- **关闭按钮**：左上角始终显示 × 按钮，点击关闭并恢复上一输入法
- **ESC 状态机**：按一次 ESC 暂停（释放触摸板，显示"已暂停"遮罩），再按一次 ESC 关闭并恢复上一输入法；点击窗口恢复
- **智能窗口定位**：弹出面板自动避开当前活动窗口，不遮挡应用程序视图
- **拖拽手柄**：顶部栏自定义拖拽手柄可随意移动窗口位置
- **鼠标后备**：如无 evdev 触摸板，可使用鼠标绘图
- **PP-OCRv6 深度学习引擎**：基于 ONNX 的 CNN 识别，覆盖 18710 个汉字，使用 MAX 池化置信度评分
- **'--test' 测试模式**：独立 GTK 窗口（无需 IBus），适合快速测试、数据采集和调试

## 跨发行版支持

`bootstrap.sh` 自动检测您的 Linux 发行版并安装全部依赖：

| 发行版 | 安装方式 | 模型来源 |
|--------|----------|----------|
| Debian 12+, Ubuntu 22.04+, Mint 21+ | `apt` + 镜像下载 | 系统包 + 幽兰百合（首选 Gitee，备用 GitHub） |
| Fedora 39+ | `dnf` + 下载 | tegaki + 幽兰百合模型 |
| Arch Linux, Manjaro | `pacman` + `yay` (AUR) + 下载 | tegaki + 幽兰百合模型 |
| openSUSE Tumbleweed | `zypper` + 下载 | tegaki + 幽兰百合模型 |

安装程序从 [tegaki GitHub releases](https://github.com/tegaki/tegaki-models/releases) 下载 tegaki v0.3 模型（`zh_CN.model` — 6763 字，`zh_TW.model` — 11853 字），并从 [Gitee](https://gitee.com/LZQingXi/handwriting-zh_CN_Community) 下载 **幽兰百合 Community v1.1.0** 模型（`ZJHandWriting-zh_CN.model` — 9374 字）。简体中文以幽兰百合为主识别器，tegaki zh_CN 为后备。

## 系统要求

- Linux 系统，带触摸板（或触摸屏）
- IBus 输入法框架（大多数桌面环境默认安装）
- **Debian 系列**：Debian 11+，Ubuntu 22.04+，Linux Mint 21+
- **Fedora**：Fedora 40+
- **Arch**：Arch Linux，Manjaro（zinnia 来自 AUR）
- **openSUSE**：Tumbleweed（Leap 不提供 zinnia）

## 快速安装

```bash
bash <(curl -s https://raw.githubusercontent.com/vinceyap88/ibus-handwrite-chinese/main/bootstrap.sh)
ibus restart
```

**Debian/Ubuntu/Mint** 用户也可使用传统方式：

```bash
sudo apt install python3-evdev tegaki-zinnia-simplified-chinese tegaki-zinnia-traditional-chinese
git clone https://github.com/vinceyap88/ibus-handwrite-chinese
cd ibus-handwrite-chinese
sudo ./install.sh          # 已安装依赖可加 --skip-deps
ibus restart
```

`install.sh` 自动下载缺失的模型：tegaki 繁体模型从 GitHub 获取，幽兰百合 Community v1.1.0 模型（9374 字）从 Gitee 获取，用于提升简体中文识别精度。

切换输入法：

```bash
ibus engine handwrite-chinese-simplified   # 简体中文
ibus engine handwrite-chinese-traditional  # 繁体中文
```

或者从桌面环境的 IBus 菜单中选择 **Chinese Handwriting (Simplified)** 或 **Chinese Handwriting (Traditional)**。

## 软件包

预构建的软件包可在 [GitHub Release](https://github.com/vinceyap88/ibus-handwrite-chinese/releases) 页面下载：

| 格式 | 安装命令 | 发行版 |
|------|----------|--------|
| `.deb` | `sudo dpkg -i <file> && sudo apt install -f` | Debian 11+, Ubuntu 22.04+, Mint 21+ |
| `.rpm` | `sudo rpm -i <file>` | Fedora 40+, openSUSE Tumbleweed |
| `PKGBUILD` | 参考 `packaging/PKGBUILD` | Arch Linux（需手动提交到 AUR）|

软件包在推送标签时由 CI 自动构建。安装后自动下载 tegaki 模型（GitHub）和幽兰百合模型（Gitee，非致命失败）。

## 使用方法

1. 从 IBus 菜单切换到 **Chinese Handwriting (Simplified)** 或 **Chinese Handwriting (Traditional)**
2. 深色浮动面板将在屏幕右下角出现
3. 用单指在触摸板上书写汉字
4. 候选字显示在面板顶部
5. 轻触触摸板选择候选词（空间映射）
6. 双指左右滑动翻页
7. 按 **⌫** 撤销上一笔画
8. 点击面板左上角 **×** 关闭并恢复上一输入法，或按 **ESC** 暂停（释放触摸板）
9. 再按 **ESC** 关闭并恢复上一输入法
10. 点击面板恢复（暂停状态下）
11. 如需不切换 IME 进行测试，在终端运行 `python3 src/ibus-engine-handwrite-chinese --test` — 独立 GTK 窗口将出现，识别结果记录到 `/tmp/ppocr-recognition.log`

## 故障排除

- **触摸板无法使用**：运行 `sudo udevadm trigger` 应用 udev 规则，或将用户加入 `input` 组：`sudo usermod -a -G input $USER && reboot`
- **IBus 未识别输入法**：安装后运行 `ibus restart`
- **输入法无法启动**：切换到输入法时查看 `journalctl -f` 获取错误信息
- **权限被拒绝**：用 `getfacl /dev/input/event*` 验证 —— 您的用户应对触摸板设备有 `rw` 权限

## 测试

两个工作流分别覆盖开发和发布：

### 主 CI

[主 CI](.github/workflows/ci.yml) 在每次推送/PR 到 `main` 时运行，覆盖 5 个 Docker 容器：
- **lint**：shellcheck、xmllint、Python 语法检查
- **test-install**：按发行版安装依赖，验证 `libzinnia.so` 加载，检查 Python 语法
- **test-bootstrap**：完整运行 bootstrap.sh，验证安装文件和模型，运行识别冒烟测试
- **test-gtk-write**：在 10 个发行版版本上运行 GTK 书写模拟，并上传截图产物

测试容器：`debian:bookworm`、`ubuntu:24.04`、`fedora:latest`、`archlinux:latest`、`opensuse/tumbleweed`。

### 发布

[Release](.github/workflows/release.yml) 在 `v*` 标签推送或手动触发时运行：
- 解析发布标签和版本号
- 构建 `.deb`、`.rpm` 和源码 tarball
- 验证发布产物
- 上传发布资产到 GitHub Release

### 识别冒烟测试

识别冒烟测试（`tests/test_recognition.py`）创建合成笔画：
- 水平线 → 识别为 **一**（得分 > 0.9）
- 十字形 → 识别为 **十**（得分 > 0.95）

CI 会在 Xvfb 下测试 GTK，但不会在容器中测试真实 IBus、evdev 或触摸板硬件。

### PP-OCRv6 精度验证

用于验证 PP-OCRv6 识别精度的分析脚本：
- `scripts/collect_ppocr_data.py` — 通过 `--test` 模式（或 `--prompt` / `--free` 模式）交互式采集数据
- `scripts/analyze_ppocr_data.py` — 精度、置信度直方图、校准、笔画复杂度及字典索引分析
- `scripts/capture_one.py` — 单笔画采集与识别测试
- `scripts/gtk_collect_loop.py` — 通过日志轮询配合 `--test` 模式的批量采集

运行完整分析流程：
```bash
python3 scripts/analyze_ppocr_data.py --input .omo/evidence/ppocr-handwriting-dataset/dataset-chat-v1.json --verbose
```

## 已知限制

- **实机测试**：在 MacBook Pro（bcm5974）上测试通过 —— 应适用于任何支持 `BTN_TOUCH + ABS_X` 的触摸板，但 Fedora/Arch 上的 Wayland 弹出面板定位和 SELinux evdev 访问尚未测试
- **识别精度**：简体中文以 PP-OCRv6（18710 字，ONNX）深度学习引擎为主，幽兰百合 Zinnia（9374 字）为后备。经 40 个真实手写字符验证（36 个不同字，含 7 组相似字：土/士、未/末、日/曰、人/入、大/太、已/己、上/下），首选识别率 100%，平均置信度 94.97%。繁体中文使用 tegaki zh_TW（11853 字）
- **单字输入**：暂不支持多字组合（一次输入一个字）。V2 版本可能加入空间分割实现连续输入
- **openSUSE Leap**：zinnia 库在 Leap 16.0 默认源中不可用。请使用 openSUSE Tumbleweed，或从 OBS 手动安装 zinnia
- **第三方模型**：幽兰百合模型托管在 Gitee（中国）。如果 Gitee 无法访问，安装程序将回退到本地 `models/` 缓存，或发出警告并继续。CI 容器优雅跳过下载

## 许可协议

GPLv3 — 由依赖库要求（libzinnia、python3-evdev、ibus）。

## PP-OCRv6 集成

简体中文使用 PP-OCRv6 ONNX 模型（MobileNetV3 small，训练于 18710 个汉字）作为主要识别引擎。

### 架构

引擎支持两种识别后端，由 `_USE_ONNX` 标志控制：
- **PP-OCRv6**（`_USE_ONNX = True`）：简体中文默认。ONNX 运行时，CTC 解码和 MAX 池化置信度评分。
- **幽兰百合 Zinnia**（`_USE_ONNX = False`）：繁体中文默认。基于格子的 Zinnia 识别引擎。

### 设置

1. 通过 `bootstrap.sh` 或 `install.sh` 下载模型（PP-OCRv6 ONNX + 字典，或 Zinnia 模型）
2. 通过环境变量设置 ONNX 模型路径：
   ```bash
   export IBUS_HANDWRITE_PPOCR_MODEL=small  # 或 large、server（默认：small）
   export IBUS_HANDWRITE_PPOCR_MODEL_PATH=/tmp/models/ppocrv6_small.onnx
   export IBUS_HANDWRITE_PPOCR_DICT_PATH=/tmp/models/dict_v6.txt
   ```
3. 照常切换引擎：
   ```bash
   ibus engine handwrite-chinese-simplified
   ```

### 无需 IBus 测试

以独立 `--test` 模式运行引擎，测试识别功能无需切换 IME：
```bash
python3 src/ibus-engine-handwrite-chinese --test
```
这将打开一个 GTK 浮动窗口，您可以在其中绘制字符。识别结果显示在 `/tmp/ppocr-recognition.log`。

### 已修复的 Bug

验证过程中发现并修复了 PP-OCRv6 管线的三个 Bug：

1. **字典索引损坏**（第 290 行）：`line.strip()` 从字典条目中剥离了 U+3000（表意空格），导致后续所有字符索引偏移 1。修复为 `line.rstrip('\n')`。
2. **置信度池化**（第 405 行）：`np.mean(probs, axis=0)` 对所有 CTC 时间步（包括空白帧）取平均，使真实置信度稀释约 10 倍。修复为 `np.max(probs, axis=0)`（MAX 池化），符合单字符识别的 CTC argmax 行为。
3. **笔画线宽**（第 364 行）：`cr.set_line_width(6)` 渲染的笔画比训练数据分布更细。增加到 `set_line_width(8)`。

### 验证结果

通过 `--test` 模式和触摸板采集的 40 个真实手写字符：

| 指标 | 结果 |
|------|------|
| 首选准确率 | 40/40（100%） |
| 前五准确率 | 40/40（100%） |
| 平均置信度 | 94.97% |
| 最低置信度 | 34.47%（小） |
| 最高置信度 | 100.00%（月、女等） |
| 相似字组测试 | 7 组，14/14 正确 |

测试字符：一 七 三 上 下 不 中 九 二 五 人 入 八 六 十 口 四 土 士 大 天 太 女 好 小 山 己 已 心 文 日 曰 月 木 未 末 水 火 王 田

完整分析报告：`.omo/evidence/ppocr-handwriting-dataset/analysis-report.json`
瓶颈报告：`.omo/evidence/ppocr-handwriting-dataset/bottleneck-report.txt`

## 目录结构

```
├── scripts/
│   ├── analyze_ppocr_data.py          PP-OCRv6 精度分析管线
│   ├── collect_ppocr_data.py          交互式手写数据采集
│   ├── capture_one.py                 单笔画采集辅助工具
│   ├── gtk_collect_loop.py            基于日志的 GTK 采集脚本
│   └── read_last_log.py               识别日志读取器
├── src/
│   ├── ibus-engine-handwrite-chinese    主引擎（Python、Zinnia ctypes、GTK 弹出面板、evdev 集成）
│   └── handwrite_evdev.py               Evdev 多点触控读取模块
├── xml/
│   ├── handwrite-chinese-simplified.xml IBus 组件：简体中文
│   └── handwrite-chinese-traditional.xml IBus 组件：繁体中文
├── icons/
│   ├── handwrite-chinese-simplified.svg 引擎图标：简体
│   └── handwrite-chinese-traditional.svg 引擎图标：繁体
├── tools/
│   ├── install.sh                       安装脚本（Debian 原生，支持 `--skip-deps`）
│   ├── restore.sh                       回滚/恢复脚本
│   └── 99-trackpad-handwrite.rules      触摸板访问的 udev 规则
├── tests/
│   ├── test_recognition.py             合成笔画识别冒烟测试
│   └── test_data/                      测试笔画数据
├── docs/
│   └── screenshot.png                   应用截图
│   ├── plan-handwriting-accuracy-test.md tegaki 与幽兰百合精度对比测试方案
│   └── multi-char-composition-with-phrase-boost-plan.md  V2 功能规划
├── models/                              本地模型缓存（gitignore）
├── packaging/                            Debian 打包、RPM spec、PKGBUILD
├── .github/workflows/
│   ├── ci.yml                          主 CI — 5 个发行版
│   └── release.yml                     发布构建、验证、上传
├── .omo/
│   └── evidence/ppocr-handwriting-dataset/  精度验证证据
│       ├── dataset-chat-v1.json              40 个手写样本，100% 准确率
│       ├── analysis-report.json              完整分析报告及指标
│       └── bottleneck-report.txt             Bug 修复与验证报告
├── bootstrap.sh                        跨发行版安装入口
├── README.md
├── README.zh-Hans.md
└── README.zh-Hant.md
```
