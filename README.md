# AHK Debugger 技能说明

## 概述

`ahk-debugger` 是一个用于自动调试 AutoHotkey (AHK) v1/v2 脚本错误的技能。它通过自动化运行脚本、捕获错误弹窗截图、分析错误信息并指导代码修复，实现完整的调试闭环，适用于opencode cloudcode等工具。

---

## 核心组件

### capture_ahk_error.py

**路径：** `skills/ahk-debugger/capture_ahk_error.py`

**功能：**
- 自动检测 AHK 脚本版本（v1 或 v2）
- 启动 AHK 解释器并运行目标脚本
- 捕获前置窗口的客户区精确截图（不含标题栏和边框）
- 识别弹窗是否来自 AHK（通过进程名或窗口类名判断）
- 自动关闭错误弹窗和 AHK 进程
- 使用 CLIP/LLaVA 模型生成图像描述（供无视觉能力的模型使用）
- 返回 JSON 格式结果

**调用方式：**
```bash
python capture_ahk_error.py "path/to/script.ahk"
```

**返回格式：**
```json
{
  "screenshot_file": "skills/ahk-debugger/ahk_error_capture.png",
  "is_ahk": true,
  "ahk_version": "v2",
  "image_description": ""
}
```

---

## 工作流程

```
┌─────────────────────────────────────────────────────────┐
│                      调试循环                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 检测 AHK 版本                                       │
│     └─ 检查 #Requires AutoHotkey v2 / #NoEnv 等特征    │
│                                                         │
│  2. 终止旧 AHK 进程                                     │
│                                                         │
│  3. 运行 capture_ahk_error.py                           │
│     └─ 获取截图路径                                     │
│                                                         │
│  4. 检查返回值:                                         │
│     ├─ error → 检查脚本路径是否正确                     │
│     ├─ is_ahk: false → 脚本正常运行，输出成功报告       │
│     └─ is_ahk: true  → 主代理读取截图分析错误           │
│                                                         │
│  5. 主代理分析错误内容并修复代码                         │
│                                                         │
│  6. 删除截图文件                                        │
│                                                         │
│  7. 重复步骤 3-6（最多 5 轮）                           │
│                                                         │
│  8. 输出最终结果                                        │
│     └─ 调试结论 + 修复后的完整代码                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 触发条件

当用户请求以下操作时自动触发：
- "调试 AHK 脚本"
- "修复 AHK 错误"
- "AHK 报错了"
- "运行 AHK 并检查错误"
- "AHK 弹窗错误"
- 任何涉及 AHK 脚本调试的任务

---

## 技术细节

### AHK 版本判断逻辑

```python
def detect_ahk_version(self, script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read(500)
        if '#Requires AutoHotkey v2' in content:
            return 'v2'
        elif '#NoEnv' in content or 'SendMode Input' in content:
            return 'v1'
        else:
            return 'v1'  # 默认 v1
```

### AHK 解释器路径

| 版本 | 路径 |
|------|------|
| v1 | `C:\Program Files\AutoHotkey\AutoHotkeyU64.exe` |
| v2 | `C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe` |

### 截图机制

1. 使用 `win32gui.GetForegroundWindow()` 获取前置窗口句柄
2. 通过 `win32process` 获取进程 PID，验证是否为 AHK 进程
3. 使用 `win32gui.GetClientRect()` 获取客户区矩形
4. 使用 `pyautogui.screenshot(region=...)` 截取客户区（无标题栏/边框）
5. 保存为技能目录下的 `ahk_error_capture.png`

### AHK v1 vs v2 语法差异参考

| 特性 | AHK v1 | AHK v2 |
|------|--------|--------|
| MsgBox | `MsgBox, text` | `MsgBox("text")` |
| Send | `Send, {Enter}` | `Send("{Enter}")` |
| 循环 | `Loop, 10 {` | `Loop 10 {` |
| 表达式 | `%var%` | `var` |
| Hotkey | `F1::` + 缩进 | `F1:: { ... }` |

---

## 常见错误类型及修复

| 错误类型 | 示例 | 修复方式 |
|----------|------|----------|
| 函数不存在 | `NonExistentFunction()` | 使用正确的内置函数 |
| 语法错误 | `x := 5 + * 3` | `x := 5 + 3` |
| 变量未定义 | `y := x + z` | 先定义变量 `z` |
| 引号不匹配 | `MsgBox, "test` | `MsgBox, "test"` |
| 参数错误 | `Func("a")` (需 2 参数) | `Func("a", "b")` |
| Hotkey 缺少大括号 | `F1::` | `F1:: { ... }` |
| catch 语法错误 | `catch e {` | `catch {` |

---

## 职责分工

| 任务 | 执行者 |
|------|--------|
| 运行 capture_ahk_error.py | 主代理 (Bash) |
| 读取截图文件 | 主代理 (read) |
| Vision 分析错误 | 主代理 (自动) |
| 修复代码 | 主代理 (edit/write) |
| 删除截图文件 | 主代理 (Bash) |
| 验证修复结果 | 主代理 (Bash) |

---

## 数据流

```
AHK 脚本
    ↓
capture_ahk_error.py
    ↓
JSON: { screenshot_file, is_ahk, ahk_version }
    ↓
主代理读取截图 → Vision 分析错误信息
    ↓
修复代码
    ↓
删除截图
    ↓
重新运行验证（循环）
    ↓
最终报告
```

---

## 截图管理规则

1. **保存位置：** 技能文件夹内 (`skills/ahk-debugger/ahk_error_capture.png`)
2. **命名规则：** 固定文件名，每次覆盖
3. **清理时机：** 主代理完成 vision 分析后立即删除
4. **清理命令：** `Remove-Item "路径/ahk_error_capture.png" -Force`

---

## 调试规则

1. **必须用 capture_ahk_error.py** — 不使用 MCP Screenshot
2. **最多修复 5 次** — 超过后查阅官方文档
3. **自动关闭弹窗** — `capture_ahk_error.py` 会自动处理
4. **截图精确** — 截取客户区像素（无标题栏/边框）

---

## 注意事项

- 不调用外部 API，截图由主代理读取，vision 自动分析
- 截图分析成功后立即删除，避免残留
- 根据 `ahk_version` 字段使用对应的 v1/v2 语法进行修复
- 主代理直接使用工具执行所有操作，无需子代理

---

## 官方文档

- **AHK v1:** https://www.autohotkey.com/docs/v1/
- **AHK v2:** https://www.autohotkey.com/docs/v2/

---

## 依赖

| 依赖 | 用途 |
|------|------|
| Python 3.x | 运行 capture_ahk_error.py |
| pyautogui | 屏幕截图 |
| pywin32 | Windows GUI 操作（窗口枚举、截图、进程终止） |
| Pillow (PIL) | 图像处理 |
| llama-llava-cli（可选） | 图像描述生成，用于无视觉能力的模型 |

---

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 截图不存在 | capture_ahk_error.py 执行失败 | 检查 Python 环境和依赖 |
| is_ahk: false | 脚本正常运行无错误 | 输出成功报告，无需修复 |
| 版本判断错误 | 脚本无版本声明 | 默认使用 v1，根据语法特征调整 |
| 弹窗未关闭 | close_popup 失败 | 手动终止 AHK 进程 |
| 修复后仍报错 | 多个错误需逐轮修复 | 继续下一轮调试循环 |
