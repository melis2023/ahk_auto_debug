# ahk_auto_debug
ahk_auto_debug for opencode 、cloud code、openclaw

这个工具是使用在opencode等编程工具中，实现自动化修复的一个工具
在ahkv1，v2版本在自动化修复中，会出现msgbox等弹窗导致进程阻塞，利用该技能可以自动识别弹窗信息，并返回给大模型进行分析并修复。

ahk-debugger/
├── SKILL.md              # 技能定义文件 (6.6KB)
└── capture_ahk_error.py  # 核心工具脚本 (5.5KB)

1，打开.ahk文件

2，如果出现报错，则会弹窗
<img width="658" height="310" alt="image" src="https://github.com/user-attachments/assets/c7e0c82a-2154-4e88-9862-c3bdf2e77769" />

3，如果出现弹窗，则调用capture_ahk_error.py进行截图，并将截图数据传递回模型

4，执行后续修复代码的loop
