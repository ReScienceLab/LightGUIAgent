# LightGUIAgent

> 基于网格坐标的轻量级 GUI 自动化智能体

**基于网格坐标系统和 Claude Opus 4.5 的轻量级 GUI 自动化智能体**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-managed-green.svg)](https://github.com/astral-sh/uv)
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-5865F2?logo=discord&logoColor=white)](https://discord.gg/3BmDnDPcM6)
[![WeChat](https://img.shields.io/badge/WeChat-Community-07C160?logo=wechat&logoColor=white)](#微信社区)

**核心创新**：将屏幕划分为 10×20 的网格（类似国际象棋坐标），允许模型输出 "E5" 而不是复杂的像素坐标。

## 主要特性

- **网格坐标系统**：10×20 网格 (A-J × 1-20) 代替像素坐标
- **Claude Opus 4.5**：最先进的视觉模型，用于 UI 理解
- **视觉上下文记忆**：包含上一步的标记截图，便于更好地决策
- **多语言支持**：完美支持中文、英文和其他语言输入
- **快速**：每步 5-8 秒（本地模型需 24-30 秒）
- **轻量级**：200MB 内存（本地模型需 10GB）
- **易于部署**：无需 GPU，只需 Python + API 密钥

## 前置要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) 包管理器
- 启用 USB 调试的 Android 设备
- [ADB](https://developer.android.com/studio/command-line/adb)（Android Debug Bridge）
- 来自 [Anthropic](https://console.anthropic.com/) 的 Claude API 密钥

## 快速开始

### 1. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/ReScienceLab/LightGUIAgent.git
cd LightGUIAgent

# 安装依赖（自动创建 .venv）
uv sync

# 或使用便捷命令
make dev
```

### 2. 设置 API 密钥

```bash
# 设置 Anthropic API 密钥
export ANTHROPIC_API_KEY='your-key-here'

# 或创建 .env 文件（推荐）
cp .env.example .env
# 然后编辑 .env 并添加你的 API 密钥

# 要在 shell 中持久化，添加到 ~/.bashrc 或 ~/.zshrc
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.bashrc
```

### 3. 连接 Android 设备

```bash
# 在 Android 设备上启用 USB 调试
# 通过 USB 连接并授权计算机

# 验证 ADB 连接
adb devices
```

### 4. （可选）自定义配置

**LightGUIAgent 自动检测你的设备和屏幕设置** - 无需配置！

如需自定义配置：

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml 以自定义网格密度、行为等
```

**自动检测：**
- 设备名称（通过 ADB）
- 屏幕尺寸（通过 ADB）
- 网格密度（计算得到约 108×120px 的单元格）

**可配置：**
- 网格列数/行数（覆盖自动计算）
- 最大步数、延迟时间
- 网格视觉样式（颜色、线宽、标签大小）
- 内部坐标标签（在网格单元内显示标签）
- Claude API 参数

## 使用示例

### 示例 1：小红书（中文）

在小红书社交媒体应用中发布内容：

```bash
make run TASK="打开小红书，发布一个post，内容是 '大家好,我是LightGUIAgent'"
```

**执行步骤：**
1. 打开小红书应用
2. 导航到创建帖子
3. 输入消息 "大家好,我是LightGUIAgent"
4. 发布帖子

**演示视频：**

https://github.com/ReScienceLab/LightGUIAgent/releases/download/untagged-838af5b8d906ee80fc4d/LightGUIAgent-Demo-1.mp4

**分步截图：**

<table>
  <tr>
    <td width="33%">
      <b>步骤 1：打开小红书应用</b><br/>
      <img src="examples/demo1_screenshots/xiaohongshu_step01_action_marked.jpg" width="100%"/>
    </td>
    <td width="33%">
      <b>步骤 2：点击创建帖子按钮</b><br/>
      <img src="examples/demo1_screenshots/xiaohongshu_step02_action_marked.jpg" width="100%"/>
    </td>
    <td width="33%">
      <b>步骤 3：发布帖子</b><br/>
      <img src="examples/demo1_screenshots/xiaohongshu_step03_action_marked.jpg" width="100%"/>
    </td>
  </tr>
</table>

### 示例 2：X/Twitter（英文）

在 X (Twitter) 上发布消息：

```bash
make run TASK="Open X，post 'Hi, this post is from LightGUIAgent'"
```

**执行步骤：**
1. 打开 X 应用
2. 点击撰写按钮
3. 输入 "Hi, this post is from LightGUIAgent"
4. 发布推文

**演示视频：**

https://github.com/ReScienceLab/LightGUIAgent/releases/download/untagged-838af5b8d906ee80fc4d/LightGUIAgent-Demo-2.mp4

**分步截图：**

<table>
  <tr>
    <td width="33%">
      <b>步骤 1：打开 X 应用</b><br/>
      <img src="examples/demo2_screenshots/twitter_step01_action_marked.jpg" width="100%"/>
    </td>
    <td width="33%">
      <b>步骤 2：导航到撰写</b><br/>
      <img src="examples/demo2_screenshots/twitter_step02_action_marked.jpg" width="100%"/>
    </td>
    <td width="33%">
      <b>步骤 3：点击撰写按钮</b><br/>
      <img src="examples/demo2_screenshots/twitter_step03_action_marked.jpg" width="100%"/>
    </td>
  </tr>
  <tr>
    <td width="33%">
      <b>步骤 4：聚焦文本输入</b><br/>
      <img src="examples/demo2_screenshots/twitter_step04_action_marked.jpg" width="100%"/>
    </td>
    <td width="33%">
      <b>步骤 5：输入消息</b><br/>
      <img src="examples/demo2_screenshots/twitter_step05_action_marked.jpg" width="100%"/>
    </td>
    <td width="33%">
      <b>步骤 6：检查内容</b><br/>
      <img src="examples/demo2_screenshots/twitter_step06_action_marked.jpg" width="100%"/>
    </td>
  </tr>
  <tr>
    <td width="33%">
      <b>步骤 8：确认发布</b><br/>
      <img src="examples/demo2_screenshots/twitter_step07_action_marked.jpg" width="100%"/>
    </td>
    <td width="33%">
      <b>步骤 9：帖子已发布</b><br/>
      <img src="examples/demo2_screenshots/twitter_step08_action_marked.jpg" width="100%"/>
    </td>
    <td width="33%">
      <b>步骤 10：验证成功</b><br/>
      <img src="examples/demo2_screenshots/twitter_step09_action_marked.jpg" width="100%"/>
    </td>
  </tr>
</table>

### 其他使用方法

```bash
# 方法 1：使用 Makefile（推荐）
make run TASK="你的任务描述"

# 方法 2：直接使用 main.py
uv run python main.py "你的任务描述"

# 方法 3：运行测试
make test              # 测试网格系统
make test-verbose      # 详细输出测试
```

## 示例输出

```
======================================================================
LightGUIAgent - 智能 GUI 自动化
======================================================================
任务：打开 X，发布 'Hi, this post is from LightGUIAgent'
模型：Claude Opus 4.5
网格：10×20 坐标系统 (A-J, 1-20)
日志：logs/task_20260202_145623/session.jsonl
======================================================================

LLM Claude Opus 4.5 推理时间：6.18 秒
执行命令：adb shell input tap 486 540
步骤 1 耗时：6.92 秒
步骤 1/50 完成。操作：点击 E5 → (486, 540)
  ➤ 点击 X 应用图标打开
  📝 摘要：目标是打开 X 并发布消息。第一步：从主屏幕打开 X 应用。

LLM Claude Opus 4.5 推理时间：5.87 秒
执行命令：adb shell input tap 972 2340
步骤 2 耗时：6.41 秒
步骤 2/50 完成。操作：点击 J22 → (972, 2340)
  ➤ 点击蓝色 '+' 按钮创建新帖子
  📝 摘要：X 应用已在趋势页面打开。现在点击撰写按钮创建新帖子。

LLM Claude Opus 4.5 推理时间：7.19 秒
执行命令 (yadb)：adb shell app_process ... -keyboard 'Hi, this post is from LightGUIAgent'
步骤 3 耗时：7.45 秒
步骤 3/50 完成。操作：输入 "Hi, this post is from LightGUIAgent"
  ➤ 在文本输入框中输入帖子内容
  📝 摘要：打开 X 并开始创建新帖子，现在输入消息内容。

...

任务成功完成！

============================================================
执行摘要
============================================================
完成步骤：6
耗时：      45.3秒
平均每步：  7.6秒
最快步骤：  5.9秒
最慢步骤：  8.2秒

日志摘要：
   总事件数：28
   日志文件：logs/task_20260202_145623/9a3b7c21-4d5e-4a2b-8f3d-2c1e5b6a9d7f.jsonl

成本摘要
==================================================
输入 tokens：  8,420
输出 tokens：  624
总计 tokens：  9,044
--------------------------------------------------
输入成本：     $0.0421
输出成本：     $0.0156
总成本：       $0.0577
==================================================
```

## 性能对比

| 指标 | 本地模型 (4B) | LightGUIAgent | 提升 |
|--------|------------------|---------------|-------------|
| **速度** | 24-30秒/步 | **5-8秒/步** | **快 3-4 倍** |
| **部署** | 2 小时 | **5 分钟** | **快 24 倍** |
| **内存** | 10GB | **200MB** | **减少 50 倍** |
| **准确率** | ~73% | **~80-85%*** | **+10%** |
| **成本** | $0 (需要 GPU) | **$0.05-0.15/任务** | **按使用付费** |

\* 基于 Claude Opus 4.5 能力的估计

## 网格系统

### 概述

屏幕被划分为 **10×20 网格** 以便于坐标参考：

- **列**：A-J（10 列，从左到右）
- **行**：1-20（20 行，从上到下）
- **单元格大小**：约 108×120 像素（根据屏幕分辨率自动计算）

### 示例

```
"E5" → 点击单元格 E5 的中心位置 (486, 540)
```

### 网格可视化

```
   A    B    C    D    E    F    G    H    I    J
 ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
1│    │    │    │ [S]│    │    │    │    │    │    │ ← 搜索
 ├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
2│    │    │    │    │    │    │    │    │    │    │
 ├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
3│    │  [按钮]   │    │    │    │    │    │    │   ← UI 元素
 ├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
4│[应用]  │    │    │[邮件]  │    │    │    │    │ ← 应用
 ├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
...
```

### 内部坐标标签

LightGUIAgent 支持在网格单元内显示半透明坐标标签，便于识别：

**配置 (config.yaml)：**
```yaml
grid:
  show_inner_labels: true     # 启用内部标签
  inner_label_interval: 3     # 每 3 个单元格显示一个标签
  inner_label_opacity: 128    # 半透明 (0-255)
```

**选项：**
- `inner_label_interval: 1` - 在每个单元格中显示标签（密集）
- `inner_label_interval: 2` - 每 2 个单元格显示一个标签
- `inner_label_interval: 3` - 每 3 个单元格显示一个标签（默认，平衡）

这有助于 Claude 识别屏幕中心的坐标，而无需从边缘标签推断。

## 架构

### 组件

- **config.py** - 带自动检测的配置管理
- **settings.py** - 带验证的设置模型
- **grid_converter.py** - 网格 ↔ 像素坐标转换
- **grid_overlay.py** - 带网格覆盖的截图标注
- **claude_client.py** - 带视觉支持的 Claude API 集成
- **agent.py** - 主编排循环
- **logger.py** - 带详细指标的 JSONL 日志系统

### 工作流程

1. **捕获** - 通过 ADB 截图
2. **标注** - 添加带坐标标签的网格覆盖
3. **压缩** - 调整到 Claude API 的最佳大小
4. **分析** - Claude 根据视觉上下文决定下一步操作
5. **执行** - 通过 ADB 执行操作（点击、输入、滚动等）
6. **日志** - 记录步骤详情到 JSONL 格式并保存截图
7. **重复** - 直到任务完成或达到最大步数

### 可用操作

1. **CLICK** - 点击网格位置（例如 "E5"）
2. **TYPE** - 在聚焦的输入框中输入文本
   - 通过 yadb 支持中文、表情符号和特殊字符
   - 可选 `clear_first` 清除现有文本
3. **SCROLL** - 在屏幕上向上或向下滚动
4. **AWAKE** - 通过包名启动应用
5. **COMPLETE** - 标记任务成功完成

## 故障排除

### API 密钥问题

```bash
# 验证 API 密钥已设置
echo $ANTHROPIC_API_KEY

# 或检查 .env 文件
cat .env | grep ANTHROPIC_API_KEY
```

### ADB 问题

```bash
# 重启 ADB 服务器
adb kill-server && adb start-server

# 检查设备授权
adb devices  # 应显示 "device" 而不是 "unauthorized"

# 如果设备显示离线
adb reconnect
```

### 网格不可见

- 检查 `artifacts/logs/task_*/images/*_annotated.jpg` 文件
- 验证屏幕分辨率是否正确检测
- 如需要，在 `config.yaml` 中调整网格颜色：
  ```yaml
  grid:
    line_color: [0, 255, 0]  # 改为绿色
    label_color: [255, 0, 0]  # 改为红色
  ```

### 重复点击检测

如果智能体重复点击同一位置：
- 系统现在会检测重复点击并警告 Claude
- 检查配置中的 `delay_after_action`（如果 UI 转换较慢，增加此值）
- 查看标记的截图以确认 UI 是否实际发生了变化

## 项目结构

```
LightGUIAgent/
├── main.py                  # 入口点
├── lightguiagent/           # 主包
│   ├── agent.py            # 主编排器
│   ├── claude_client.py    # Claude API 客户端
│   ├── grid_overlay.py     # 网格可视化
│   ├── grid_converter.py   # 坐标转换
│   ├── config.py           # 配置管理
│   ├── settings.py         # 设置模型
│   └── logger.py           # JSONL 日志
├── tests/                   # 测试套件
│   └── test_grid_system.py
├── examples/                # 演示视频
│   ├── LightGUIAgent-Demo-1.mp4
│   └── LightGUIAgent-Demo-2.mp4
├── artifacts/               # 生成的输出
│   ├── logs/               # 任务执行日志
│   └── debug/              # 调试截图
├── bin/                     # 辅助二进制文件 (yadb)
├── config.yaml              # 用户配置
├── config.example.yaml      # 配置模板
├── pyproject.toml           # 依赖项
├── Makefile                 # 便捷命令
└── README.md
```

## 参考资料

- [Claude API 文档](https://docs.anthropic.com/)
- [ADB 文档](https://developer.android.com/studio/command-line/adb)
- [uv 包管理器](https://github.com/astral-sh/uv)

## 许可证

本项目采用 Apache License 2.0 许可 - 详见 [LICENSE](LICENSE) 文件。
