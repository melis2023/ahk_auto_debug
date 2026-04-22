---
name: ahk-debugger
description: AHK 调试技能：自动运行 AHK 脚本、捕获错误弹窗截图、主代理 vision 分析、修复代码并验证。用于调试 AutoHotkey v1/v2 脚本错误，包括语法错误、函数错误、变量错误等。
allowed-tools: Bash(python:*), Bash(ahk:*), write, edit, read, glob, grep, Bash(rm:*)
hidden: false
---

# AHK 调试技能

## 触发条件

当用户请求以下操作时自动触发：
- "调试 AHK 脚本"
- "修复 AHK 错误"
- "AHK 报错了"
- "运行 AHK 并检查错误"
- "AHK 弹窗错误"
- 任何涉及 AHK 脚本调试的任务

## 核心工具

### capture_ahk_error.py

**位置:** `skills/ahk-debugger/capture_ahk_error.py`

**功能:**
- 自动判断 AHK 版本 (v1/v2)
- 运行脚本并捕获错误弹窗
- 截取客户区精确截图 (无标题栏/边框)
- 自动关闭弹窗和进程
- 返回极简 JSON（仅文件路径 + is_ahk 标志）

**调用:**
```bash
python skills/ahk-debugger/capture_ahk_error.py "script.ahk"
```

**返回:**
```json
{"screenshot_file": "path/to/screenshot.png", "is_ahk": true, "ahk_version": "v2"}
```

## 工作流程

```
1. 检测 AHK 版本 (检查 #Requires AutoHotkey v2)
2. 终止旧 AHK 进程
3. 运行 capture_ahk_error.py → 获取截图路径
4. 检查返回值:
   - error → 检查脚本路径
   - is_ahk: false → 脚本正常运行，输出成功报告
   - is_ahk: true → 主代理读取截图分析错误
5. 主代理分析错误内容并修复代码
6. 主代理删除截图文件
7. 重复步骤 2-6（最多 5 次）
8. 输出最终结果
```

## 版本判断

```powershell
$firstLines = Get-Content "script.ahk" -First 5 -Raw
if ($firstLines -match '#Requires\s+AutoHotkey\s+2') {
    # AHK v2
} else {
    # AHK v1
}
```

## AHK 路径

- **v1:** `C:\Program Files\AutoHotkey\AutoHotkeyU64.exe`
- **v2:** `C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe`

## 常见错误类型

| 错误类型 | 示例 | 修复 |
|----------|------|------|
| 函数不存在 | `NonExistentFunction()` | 使用内置函数或定义函数 |
| 语法错误 | `x := 5 + * 3` | `x := 5 + 3` |
| 变量未定义 | `y := x + z` | 定义变量 `z` |
| 引号不匹配 | `MsgBox, "test` | `MsgBox, "test"` |
| 参数错误 | `Func("a")` (需要 2 参数) | `Func("a", "b")` |

## 调试规则

1. **必须用 capture_ahk_error.py** - 不要用 MCP Screenshot
2. **最多修复 5 次** - 超过后查阅官方文档
3. **自动关闭弹窗** - capture_ahk_error.py 会自动处理
4. **截图精确** - 客户区像素（无标题栏/边框）

## 官方文档

- **AHK v1:** https://www.autohotkey.com/docs/v1/
- **AHK v2:** https://www.autohotkey.com/docs/v2/

## 输出要求

每轮输出：
1. 错误分析（截图中的错误信息）
2. AHK 版本（v1 或 v2）
3. 修复内容（修改的代码）
4. 验证结果（capture_ahk_error.py 返回）
5. 删除截图文件（分析成功后立即删除）

最终输出：
- 调试结果（是否通过）
- 最终代码（修复后）

## 注意事项

- **不要调用外部 API** - 截图由主代理 read 工具读取，vision 自动分析
- **截图自动清理** - 主代理分析成功后立即删除截图文件
- **版本感知修复** - 根据 ahk_version 字段使用对应的 v1/v2 语法
- **执行模式** - 主代理直接使用工具执行所有操作，无需子代理

## AHK v1 vs v2 语法差异

| 特性 | AHK v1 | AHK v2 |
|------|--------|--------|
| MsgBox | `MsgBox, text` | `MsgBox("text")` |
| 变量赋值 | `var := value` | `var := value` |
| 表达式 | `% var` | `var` |
| 函数定义 | `Func(param) {` | `Func(param) {` |
| Send | `Send, {Enter}` | `Send("{Enter}")` |
| 注释 | `; comment` | `; comment` |
| If 语句 | `if (x > 5) {` | `if (x > 5) {` |
| 循环 | `Loop, 10 {` | `Loop 10 {` |
| 数组 | `arr := [1,2,3]` | `arr := [1,2,3]` |
| 对象 | `obj := {key: "value"}` | `obj := {key: "value"}` |

## 主代理执行流程

### 职责分工

| 任务 | 执行者 |
|------|--------|
| 运行 capture_ahk_error.py | 主代理 (Bash 工具) |
| 读取截图文件 | 主代理 (read 工具) |
| Vision 分析错误 | 主代理 (自动) |
| 修复代码 | 主代理 (edit/write 工具) |
| 删除截图文件 | 主代理 (Bash 工具) |
| 验证修复结果 | 主代理 (Bash 工具) |

### 数据传递

capture_ahk_error.py 返回：
```json
{
  "screenshot_file": "技能目录/ahk_error_capture.png",
  "is_ahk": true,
  "ahk_version": "v2"
}
```

主代理处理流程：
1. 检查 `is_ahk` - 判断是否有错误弹窗
2. 读取 `screenshot_file` - 获取错误详情 (vision 自动分析)
3. 根据错误内容修复代码
4. 删除截图文件
5. 重新运行验证

### 调用示例

```
用户：调试这个 AHK 脚本
↓
主代理：运行 capture_ahk_error.py → 获取截图路径
↓
主代理：读取截图 → vision 自动分析错误
↓
主代理：修复代码 → 重新运行验证
↓
主代理：删除截图文件
↓
输出：调试完成报告
```

## 完整调试示例

### 示例 1: AHK v2 函数错误

**原始代码:**
```autohotkey
#Requires AutoHotkey v2.0
result := NonExistentFunc(123)
ExitApp
```

**错误弹窗:**
```
Warning: This global variable appears to never be assigned a value.
Specifically: NonExistentFunc
```

**修复后:**
```autohotkey
#Requires AutoHotkey v2.0
result := StrLen("test")
ExitApp
```

### 示例 2: AHK v1 MsgBox 语法错误

**原始代码:**
```autohotkey
MsgBox % "测试消息"
```

**错误弹窗:**
```
Error: Missing ending "%"
```

**修复后:**
```autohotkey
MsgBox, % "测试消息"
```

### 示例 3: AHK v2 MsgBox 语法错误

**原始代码:**
```autohotkey
MsgBox "测试消息"
```

**错误弹窗:**
```
Error: This expression failed to produce a value.
```

**修复后:**
```autohotkey
MsgBox("测试消息")
```

## 截图管理规则

1. **保存位置:** 技能文件夹内 (`skills/ahk-debugger/ahk_error_capture.png`)
2. **命名规则:** 固定文件名，每次覆盖
3. **清理时机:** 主代理完成 vision 分析后立即删除
4. **清理命令:** `Remove-Item "路径/ahk_error_capture.png" -Force`

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 截图不存在 | capture_ahk_error.py 执行失败 | 检查 Python 环境和依赖 |
| is_ahk: false | 脚本正常运行无错误 | 输出成功报告，无需修复 |
| 版本判断错误 | 脚本无版本声明 | 默认使用 v1，根据语法特征调整 |
| 弹窗未关闭 | close_popup 失败 | 手动终止 AHK 进程 |
| 修复后仍报错 | 多个错误 | 继续下一轮调试循环 |
