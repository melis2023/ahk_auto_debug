"""
AHK 弹窗捕获工具
捕获前置 AHK 弹窗客户区截图，返回文件路径 + 图像描述
"""

import subprocess
import time
import pyautogui
import win32gui
import win32process
import win32api
import win32con
import json
import sys
import os
import base64
from io import BytesIO
from PIL import Image


# 截图保存到技能文件夹内
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
AHK_V1_PATH = r"C:\Program Files\AutoHotkey\AutoHotkeyU64.exe"
AHK_V2_PATH = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"
POPUP_MAX_WIDTH = 600
POPUP_MAX_HEIGHT = 500
CLIP_MODEL_PATH = r"I:\model\lmstudio-community\Qwen3.6-35B-A3B-APEX-I-Compact\mmproj.gguf"


class AhkPopupCapture:
    def __init__(self):
        self.ahk_process = None
    
    def detect_ahk_version(self, script_path):
        """检测 AHK 脚本版本"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read(500)
                if '#Requires' in content and ('v2' in content or '2.0' in content):
                    return 'v2'
                elif '#NoEnv' in content or 'SendMode Input' in content:
                    return 'v1'
                else:
                    return 'v1'  # 默认 v1
        except:
            return 'v1'
    
    def run_ahk_script(self, script_path):
        """运行 AHK 脚本 (自动判断 v1/v2)"""
        version = self.detect_ahk_version(script_path)
        ahk_path = AHK_V2_PATH if version == 'v2' else AHK_V1_PATH
        
        self.ahk_process = subprocess.Popen([ahk_path, script_path])
        time.sleep(1.5)
        return self.ahk_process, version
    
    def capture_foreground_client(self):
        """截取前置窗口的客户区"""
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None, False
        
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
                exe_path = win32process.GetModuleFileNameEx(handle, 0)
                win32api.CloseHandle(handle)
                exe_name = exe_path.split('\\')[-1].lower()
            except:
                exe_name = ""
            
            is_ahk = 'autohotkey' in exe_name or 'autohotkey64' in exe_name or win32gui.GetClassName(hwnd) == 'AutoHotkey'
            
            client_rect = win32gui.GetClientRect(hwnd)
            client_left, client_top = win32gui.ClientToScreen(hwnd, (0, 0))
            client_width = client_rect[2]
            client_height = client_rect[3]
            
            region = (client_left, client_top, client_width, client_height)
            screenshot = pyautogui.screenshot(region=region)
            
            return screenshot, region, is_ahk
        except Exception as e:
            print(f"截图失败：{e}", file=sys.stderr)
            return None, None, False
    
    def close_popup(self, hwnd):
        """关闭弹窗和进程"""
        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        except:
            pass
        
        time.sleep(0.3)
        
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
            if handle:
                win32api.TerminateProcess(handle, 0)
                win32api.CloseHandle(handle)
        except:
            pass
    
    def describe_image_with_clip(self, image_path):
        """使用 CLIP 模型生成图像描述（供不支持视觉的模型使用）"""
        if not os.path.exists(CLIP_MODEL_PATH):
            return ""
        
        try:
            cmd = [
                "llama-llava-cli.exe",
                "-m", r"I:\llama\llama.dll",
                "--mmproj", CLIP_MODEL_PATH,
                "-ngl", "99",
                "-p", "",
                "-c", "2048",
                "--temp", "0.1",
                "-n", "0",
                "-t", "4",
                "--image", image_path,
                "--verbose"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 提取描述文字（llava-cli 输出在 stderr）
            output = result.stderr
            for line in output.split('\n'):
                if 'assistant' in line.lower() or 'response' in line.lower():
                    return line
            
            return ""
        except:
            return ""
    

    
    def capture_and_analyze(self, script_path):
        """
        完整流程：运行脚本 → 捕获弹窗 → 返回文件路径 + 版本信息
        
        Returns:
            dict: 包含截图文件路径、是否 AHK、AHK 版本
        """
        if not os.path.exists(script_path):
            return {"error": f"脚本不存在：{script_path}"}
        
        # 检测版本并运行 AHK 脚本
        process, version = self.run_ahk_script(script_path)
        
        # 捕获前置窗口
        screenshot, region, is_ahk = self.capture_foreground_client()
        
        if not screenshot:
            # 无截图返回，可能是脚本正常运行结束了
            # 终止 AHK 进程
            if self.ahk_process:
                try:
                    self.ahk_process.terminate()
                except:
                    pass
            return {"error": "未能捕获窗口", "is_ahk": False}
        
        # 保存图片到技能文件夹
        filename = "ahk_error_capture.png"
        filepath = os.path.join(SKILL_DIR, filename)
        screenshot.save(filepath)
        
        # 生成图像描述（供不支持视觉的模型使用）
        image_description = self.describe_image_with_clip(filepath)
        
        result = {
            "screenshot_file": filepath,
            "is_ahk": is_ahk,
            "ahk_version": version,
            "image_description": image_description
        }
        
        # 如果是 AHK 弹窗，关闭它；否则终止 AHK 进程
        if is_ahk:
            hwnd = win32gui.GetForegroundWindow()
            self.close_popup(hwnd)
        else:
            # 脚本正常运行，终止进程
            if self.ahk_process:
                try:
                    self.ahk_process.terminate()
                except:
                    pass
        
        return result


def main():
    if len(sys.argv) < 2:
        print("用法：python capture_ahk_error.py <script.ahk>")
        sys.exit(1)
    
    script_path = sys.argv[1]
    capture = AhkPopupCapture()
    result = capture.capture_and_analyze(script_path)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
