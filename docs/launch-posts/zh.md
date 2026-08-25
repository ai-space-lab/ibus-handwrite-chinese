# 发布文案草稿 — 中文

> 供所有者审阅的草稿，请勿直接发布。每篇均在 400 字以内。
> 待 B1.1 录制完成后，把演示 GIF 链接替换为最终地址；若尚未就绪，可改用安装页链接。
>
> 共用素材：
> - 演示 GIF：`https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif`
> - 安装页：`https://ai-space-lab.github.io/ibus-handwrite-chinese/`
> - GitHub 仓库：`https://github.com/ai-space-lab/ibus-handwrite-chinese`
> - 发布页：`https://github.com/ai-space-lab/ibus-handwrite-chinese/releases`
> - 一行安装命令：`bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart`

---

## 1. r/linuxcn

**标题：** macOS 同款的中文手写输入法，现在能在 Linux 触控板上用了

**正文：**

有时候你明明会写这个字，却怎么也想不起它的拼音。macOS 上可以用触控板手写中文，Linux 这边一直缺一个好用的方案。最近我做了一个 IBus 输入法引擎，把触控板变成书写区，思路跟 macOS 基本一致。

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

已在 Acer Aspire（HTIX5288）和 MacBook Pro（bcm5974）触控板上验证。其他支持触摸的触控板应该也能用，但尚未逐一测试。欢迎提意见和报 bug。

---

## 2. V2EX（分享区）

**标题：** 分享：一个支持触控板手写中文的 Linux IBus 输入法

**正文：**

最近在用的一个小工具，觉得值得分享给同样在 Linux 上写中文的朋友。

痛点很直接：有些字你会写，但拼音一时想不起来，或者生僻字根本打不出。这个 IBus 引擎让你像在 macOS 上那样，直接在触控板上手写中文。

切换输入法后，单指在触控板写字，深色面板浮在光标旁出候选，轻点选字、双指滑动翻页。识别基于 ONNX Runtime（本地运行），覆盖 18,710 个汉字；我手头 40 个手写样本测下来 top-1 准确率 100%，平均置信度 94.97%。样本少，仅供参考，但日常够用。

亮点：
- 浮动面板贴着光标，书写体验接近 macOS
- evdev 直读触控板，无需手写板；没有触控板可用鼠标
- 6 页 GTK 设置、按需下载模型、本地用户词典、快捷键可自定义

一行装好（自动识别发行版）：

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

演示：https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif
安装页：https://ai-space-lab.github.io/ibus-handwrite-chinese/
发布页：https://github.com/ai-space-lab/ibus-handwrite-chinese/releases

已在 Acer 和 MacBook Pro 触控板验证，其他触控板未逐一测。Wayland 下的弹窗定位和 SELinux 的 evdev 权限还没测过。有问题的欢迎回帖。

---

## 3. 少数派（投稿）

**标题：** 在 Linux 触控板上，用 macOS 风格手写中文

**正文：**

在 Linux 上输入中文，大多数人习惯拼音或五笔。但总有些时候，你清楚这个字怎么写，拼音却卡在嘴边。macOS 用户可以用触控板手写，Linux 这边一直少一个顺手的方案。最近我做了一个 IBus 输入法引擎，把这套体验搬了过来。

启用后，用一根手指在触控板上写出汉字，一个深色浮动面板会浮现在光标旁边，实时给出候选字。轻点触控板选字，双指左右滑动翻页，滑得越快翻得越多。

识别在本地用 ONNX Runtime 完成，覆盖 18,710 个汉字。在 40 个真实手写样本里，top-1 准确率 100%，平均置信度 94.97%。样本量有限，结论仅供参考，但日常书写已经很可靠。

它还有一些实用的地方：
- 面板紧贴光标，书写手感接近 macOS
- 直接读取触控板（evdev），不需要额外手写板；没有触控板也能用鼠标书写
- 6 个标签页的 GTK 设置，可切换模型档位、调整引擎和窗口
- 设置里按需下载模型，带本地用户词典，快捷键全部可改

安装只需一行，会自动识别你的发行版：

```bash
bash <(curl -s https://raw.githubusercontent.com/ai-space-lab/ibus-handwrite-chinese/main/bootstrap.sh) && ibus restart
```

演示：https://ai-space-lab.github.io/ibus-handwrite-chinese/assets/demo.gif
安装指引：https://ai-space-lab.github.io/ibus-handwrite-chinese/
源码：https://github.com/ai-space-lab/ibus-handwrite-chinese

已在 Acer Aspire 和 MacBook Pro 的触控板上验证。如果你也在 Linux 上写中文，不妨试试，也欢迎告诉我你的触控板型号和体验。
