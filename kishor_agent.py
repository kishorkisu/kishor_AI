#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          KISHOR AI ASSISTANT — Python Desktop Agent          ║
║          Version 2.0 | Bhanushali Systems                    ║
╚══════════════════════════════════════════════════════════════╝

This backend runs on your local machine and gives Kishor the
ability to control your computer: open apps, search the web,
manage files, take screenshots, type text, and much more.

Usage:
    python kishor_agent.py

Then open kishor-ai-assistant.html in your browser.
"""

import os
import sys
import json
import time
import platform
import subprocess
import threading
import webbrowser
import datetime
import shutil
import glob
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# PLATFORM DETECTION
# ─────────────────────────────────────────────────────────────
SYSTEM = platform.system()   # 'Windows', 'Darwin', 'Linux'
IS_WIN  = SYSTEM == 'Windows'
IS_MAC  = SYSTEM == 'Darwin'
IS_LIN  = SYSTEM == 'Linux'

print(f"""
╔══════════════════════════════════════════════════════════════╗
║          KISHOR AI ASSISTANT — Desktop Agent v2.0            ║
╚══════════════════════════════════════════════════════════════╝
  Platform : {SYSTEM}
  Python   : {sys.version.split()[0]}
  Time     : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  Status   : Starting server on http://localhost:5000
──────────────────────────────────────────────────────────────
""")

# ─────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS (graceful degradation)
# ─────────────────────────────────────────────────────────────
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    HAS_PYAUTOGUI = True
    print("  ✅ pyautogui   — Mouse/keyboard control enabled")
except ImportError:
    HAS_PYAUTOGUI = False
    print("  ⚠️  pyautogui   — Not installed (pip install pyautogui)")

try:
    import psutil
    HAS_PSUTIL = True
    print("  ✅ psutil      — System monitoring enabled")
except ImportError:
    HAS_PSUTIL = False
    print("  ⚠️  psutil      — Not installed (pip install psutil)")

try:
    from PIL import ImageGrab
    HAS_PIL = True
    print("  ✅ Pillow      — Screenshot support enabled")
except ImportError:
    HAS_PIL = False
    print("  ⚠️  Pillow      — Not installed (pip install Pillow)")

try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 165)
    tts_engine.setProperty('volume', 0.9)
    HAS_TTS = True
    print("  ✅ pyttsx3     — Local TTS enabled")
except Exception:
    HAS_TTS = False
    print("  ⚠️  pyttsx3     — Not installed (pip install pyttsx3)")

print("")

# ─────────────────────────────────────────────────────────────
# COMMAND HISTORY
# ─────────────────────────────────────────────────────────────
command_history = []


def log_command(cmd, result, success=True):
    command_history.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "command": cmd,
        "result": result,
        "success": success
    })
    if len(command_history) > 100:
        command_history.pop(0)
    status = "✅" if success else "❌"
    print(f"  {status} [{command_history[-1]['time']}] {cmd[:60]}")


# ─────────────────────────────────────────────────────────────
# SYSTEM INFO
# ─────────────────────────────────────────────────────────────
def get_system_info():
    info = {
        "platform": SYSTEM,
        "hostname": platform.node(),
        "user": os.environ.get("USERNAME") or os.environ.get("USER", "User"),
        "python": sys.version.split()[0],
        "time": datetime.datetime.now().strftime("%I:%M:%S %p"),
        "date": datetime.datetime.now().strftime("%A, %d %B %Y"),
    }
    if HAS_PSUTIL:
        info["cpu"] = psutil.cpu_percent(interval=0.1)
        info["ram_used"] = round(psutil.virtual_memory().used / (1024**3), 1)
        info["ram_total"] = round(psutil.virtual_memory().total / (1024**3), 1)
        info["ram_percent"] = psutil.virtual_memory().percent
        info["disk_free"] = round(psutil.disk_usage('/').free / (1024**3), 1)
        info["disk_total"] = round(psutil.disk_usage('/').total / (1024**3), 1)
        info["battery"] = None
        try:
            bat = psutil.sensors_battery()
            if bat:
                info["battery"] = round(bat.percent)
        except Exception:
            pass
    return info


# ─────────────────────────────────────────────────────────────
# OPEN APPLICATION
# ─────────────────────────────────────────────────────────────
APP_MAP_WIN = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
    "explorer": "explorer.exe",
    "file manager": "explorer.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "cmd": "cmd.exe",
    "terminal": "cmd.exe",
    "powershell": "powershell.exe",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "vlc": "vlc.exe",
    "spotify": "spotify.exe",
    "zoom": "zoom.exe",
    "teams": "teams.exe",
    "vs code": "code",
    "vscode": "code",
    "whatsapp": "whatsapp.exe",
}

APP_MAP_MAC = {
    "safari": "Safari",
    "chrome": "Google Chrome",
    "firefox": "Firefox",
    "finder": "Finder",
    "terminal": "Terminal",
    "calculator": "Calculator",
    "notes": "Notes",
    "mail": "Mail",
    "calendar": "Calendar",
    "spotify": "Spotify",
    "zoom": "zoom.us",
    "vs code": "Visual Studio Code",
    "vscode": "Visual Studio Code",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "whatsapp": "WhatsApp",
    "vlc": "VLC",
}

APP_MAP_LIN = {
    "terminal": ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"],
    "file manager": ["nautilus", "dolphin", "thunar", "nemo"],
    "calculator": ["gnome-calculator", "kcalc", "galculator"],
    "text editor": ["gedit", "kate", "mousepad", "nano"],
    "chrome": ["google-chrome", "chromium-browser", "chromium"],
    "firefox": ["firefox"],
    "vlc": ["vlc"],
    "spotify": ["spotify"],
    "vs code": ["code"],
    "vscode": ["code"],
}


def open_application(app_name):
    app_lower = app_name.lower().strip()

    if IS_WIN:
        exe = APP_MAP_WIN.get(app_lower, app_lower)
        try:
            subprocess.Popen(exe, shell=True)
            return True, f"Opening {app_name} on Windows."
        except Exception as e:
            return False, f"Could not open {app_name}: {e}"

    elif IS_MAC:
        app = APP_MAP_MAC.get(app_lower, app_name)
        try:
            subprocess.Popen(["open", "-a", app])
            return True, f"Opening {app} on macOS."
        except Exception as e:
            # Try direct command
            try:
                subprocess.Popen([app_lower])
                return True, f"Opening {app_name}."
            except Exception:
                return False, f"Could not open {app_name}: {e}"

    else:  # Linux
        candidates = APP_MAP_LIN.get(app_lower, [app_lower])
        if isinstance(candidates, str):
            candidates = [candidates]
        for cmd in candidates:
            if shutil.which(cmd):
                subprocess.Popen([cmd])
                return True, f"Opening {cmd} on Linux."
        return False, f"Could not find {app_name}. Is it installed?"


# ─────────────────────────────────────────────────────────────
# WEB BROWSER & SEARCH
# ─────────────────────────────────────────────────────────────
def open_url(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return True, f"Opening {url} in your browser."


def web_search(query, engine="google"):
    engines = {
        "google": f"https://www.google.com/search?q={query.replace(' ', '+')}",
        "bing": f"https://www.bing.com/search?q={query.replace(' ', '+')}",
        "youtube": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
        "maps": f"https://www.google.com/maps/search/{query.replace(' ', '+')}",
    }
    url = engines.get(engine, engines["google"])
    webbrowser.open(url)
    return True, f"Searching for '{query}' on {engine.capitalize()}."


def open_website(name):
    sites = {
        "gmail": "https://mail.google.com",
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "facebook": "https://facebook.com",
        "twitter": "https://twitter.com",
        "linkedin": "https://linkedin.com",
        "whatsapp web": "https://web.whatsapp.com",
        "github": "https://github.com",
        "stackoverflow": "https://stackoverflow.com",
        "amazon": "https://amazon.in",
        "flipkart": "https://flipkart.com",
        "netflix": "https://netflix.com",
        "news": "https://news.google.com",
        "weather": "https://weather.com",
        "maps": "https://maps.google.com",
        "drive": "https://drive.google.com",
        "docs": "https://docs.google.com",
        "sheets": "https://sheets.google.com",
        "translate": "https://translate.google.com",
    }
    url = sites.get(name.lower(), f"https://{name}.com")
    webbrowser.open(url)
    return True, f"Opening {name} in your browser."


# ─────────────────────────────────────────────────────────────
# FILE SYSTEM OPERATIONS
# ─────────────────────────────────────────────────────────────
def list_files(path=None):
    path = path or str(Path.home() / "Desktop")
    try:
        items = os.listdir(path)
        files = [f for f in items if os.path.isfile(os.path.join(path, f))]
        folders = [f for f in items if os.path.isdir(os.path.join(path, f))]
        result = {"path": path, "files": files[:20], "folders": folders[:20]}
        return True, result
    except Exception as e:
        return False, str(e)


def open_file(filepath):
    try:
        if IS_WIN:
            os.startfile(filepath)
        elif IS_MAC:
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
        return True, f"Opening file: {filepath}"
    except Exception as e:
        return False, f"Could not open file: {e}"


def open_folder(path=None):
    path = path or str(Path.home())
    try:
        if IS_WIN:
            subprocess.Popen(["explorer", path])
        elif IS_MAC:
            subprocess.Popen(["open", path])
        else:
            for fm in ["nautilus", "dolphin", "thunar", "xdg-open"]:
                if shutil.which(fm):
                    subprocess.Popen([fm, path])
                    break
        return True, f"Opening folder: {path}"
    except Exception as e:
        return False, str(e)


def create_folder(name, where=None):
    where = where or str(Path.home() / "Desktop")
    path = os.path.join(where, name)
    try:
        os.makedirs(path, exist_ok=True)
        return True, f"Folder '{name}' created at {path}"
    except Exception as e:
        return False, str(e)


def find_files(pattern, search_in=None):
    search_in = search_in or str(Path.home())
    results = glob.glob(os.path.join(search_in, "**", f"*{pattern}*"), recursive=True)
    return True, {"matches": results[:15], "count": len(results)}


# ─────────────────────────────────────────────────────────────
# SCREENSHOT
# ─────────────────────────────────────────────────────────────
def take_screenshot(save_dir=None):
    save_dir = save_dir or str(Path.home() / "Pictures")
    os.makedirs(save_dir, exist_ok=True)
    fname = f"kishor_screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    fpath = os.path.join(save_dir, fname)

    if HAS_PIL:
        img = ImageGrab.grab()
        img.save(fpath)
        return True, f"Screenshot saved: {fpath}"
    elif IS_WIN:
        # PowerShell fallback
        ps_cmd = f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen | Out-Null; $b = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); $g = [System.Drawing.Graphics]::FromImage($b); $g.CopyFromScreen(0,0,0,0,$b.Size); $b.Save("{fpath}")'
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
        return True, f"Screenshot saved: {fpath}"
    elif IS_MAC:
        subprocess.run(["screencapture", fpath])
        return True, f"Screenshot saved: {fpath}"
    elif IS_LIN:
        for tool in ["scrot", "gnome-screenshot", "import"]:
            if shutil.which(tool):
                if tool == "scrot":
                    subprocess.run([tool, fpath])
                elif tool == "gnome-screenshot":
                    subprocess.run([tool, "-f", fpath])
                elif tool == "import":
                    subprocess.run([tool, "-window", "root", fpath])
                return True, f"Screenshot saved: {fpath}"
        return False, "No screenshot tool found. Install scrot: sudo apt install scrot"
    else:
        return False, "Screenshot not supported on this platform."


# ─────────────────────────────────────────────────────────────
# MOUSE & KEYBOARD CONTROL
# ─────────────────────────────────────────────────────────────
def type_text(text):
    if not HAS_PYAUTOGUI:
        return False, "pyautogui not installed. Run: pip install pyautogui"
    time.sleep(0.5)
    pyautogui.write(text, interval=0.03)
    return True, f"Typed: {text[:40]}..."


def press_key(key):
    if not HAS_PYAUTOGUI:
        return False, "pyautogui not installed."
    pyautogui.press(key)
    return True, f"Pressed key: {key}"


def hotkey(*keys):
    if not HAS_PYAUTOGUI:
        return False, "pyautogui not installed."
    pyautogui.hotkey(*keys)
    return True, f"Hotkey: {' + '.join(keys)}"


def move_mouse(x, y):
    if not HAS_PYAUTOGUI:
        return False, "pyautogui not installed."
    pyautogui.moveTo(x, y, duration=0.3)
    return True, f"Mouse moved to ({x}, {y})"


def click_mouse(x=None, y=None, button="left"):
    if not HAS_PYAUTOGUI:
        return False, "pyautogui not installed."
    if x and y:
        pyautogui.click(x, y, button=button)
    else:
        pyautogui.click(button=button)
    return True, f"Clicked at ({x}, {y}) with {button} button"


def scroll_mouse(clicks=3, direction="down"):
    if not HAS_PYAUTOGUI:
        return False, "pyautogui not installed."
    amount = -clicks if direction == "down" else clicks
    pyautogui.scroll(amount)
    return True, f"Scrolled {direction} {clicks} clicks"


# ─────────────────────────────────────────────────────────────
# SYSTEM COMMANDS
# ─────────────────────────────────────────────────────────────
def get_time_date():
    now = datetime.datetime.now()
    return True, {
        "time": now.strftime("%I:%M:%S %p"),
        "time_24": now.strftime("%H:%M:%S"),
        "date": now.strftime("%A, %d %B %Y"),
        "day": now.strftime("%A"),
        "timestamp": now.isoformat()
    }


def set_volume(level):
    """Set system volume 0-100"""
    try:
        if IS_WIN:
            # Uses nircmd if available, else PowerShell
            if shutil.which("nircmd"):
                subprocess.run(["nircmd", "setsysvolume", str(int(level * 655.35))])
            else:
                ps = f"$obj = New-Object -com wscript.shell; $obj.SendKeys([char]174)"
                subprocess.run(["powershell", ps], capture_output=True)
        elif IS_MAC:
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"])
        elif IS_LIN:
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{level}%"])
        return True, f"Volume set to {level}%"
    except Exception as e:
        return False, str(e)


def run_shell_command(cmd):
    """Run a safe shell command and return output"""
    # Safety whitelist
    safe_prefixes = ["echo", "dir", "ls", "pwd", "whoami", "date", "ipconfig", "ifconfig", "ping"]
    first_word = cmd.strip().split()[0].lower()
    if not any(cmd.strip().lower().startswith(p) for p in safe_prefixes):
        return False, f"Command '{first_word}' not in safe list for security reasons."
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return True, result.stdout or result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out."
    except Exception as e:
        return False, str(e)


def speak_text(text):
    if HAS_TTS:
        def _speak():
            tts_engine.say(text)
            tts_engine.runAndWait()
        threading.Thread(target=_speak, daemon=True).start()
        return True, "Speaking..."
    return False, "TTS not available."


def shutdown_system(action="shutdown"):
    """Shutdown, restart or sleep the computer"""
    if IS_WIN:
        cmds = {"shutdown": "shutdown /s /t 30", "restart": "shutdown /r /t 30", "sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"}
    elif IS_MAC:
        cmds = {"shutdown": "sudo shutdown -h +1", "restart": "sudo shutdown -r +1", "sleep": "pmset sleepnow"}
    else:
        cmds = {"shutdown": "shutdown -h +1", "restart": "shutdown -r +1", "sleep": "systemctl suspend"}
    cmd = cmds.get(action)
    if cmd:
        subprocess.Popen(cmd, shell=True)
        return True, f"System {action} initiated. You have 1 minute to cancel (run shutdown /a on Windows)."
    return False, f"Unknown action: {action}"


# ─────────────────────────────────────────────────────────────
# COMMAND ROUTER
# ─────────────────────────────────────────────────────────────
def route_command(data):
    """
    Main dispatcher — receives JSON from browser, routes to handler.
    Expected: { "action": "...", "params": {...} }
    """
    action = data.get("action", "").lower().strip()
    params = data.get("params", {})
    text   = data.get("text", "").lower().strip()  # raw voice text

    # ── TIME / DATE ──────────────────────────────────────────
    if action == "get_time" or any(w in text for w in ["what time", "current time", "what's the time"]):
        ok, result = get_time_date()
        msg = f"The time is {result['time']} on {result['date']}." if ok else result
        log_command(text or action, msg, ok)
        return {"success": ok, "message": msg, "data": result if ok else {}}

    # ── OPEN APPLICATION ─────────────────────────────────────
    elif action == "open_app" or "open " in text:
        app = params.get("app") or re.sub(r"open\s+", "", text, flags=re.I).strip()
        ok, msg = open_application(app)
        log_command(text or action, msg, ok)
        return {"success": ok, "message": msg}

    # ── WEB SEARCH ───────────────────────────────────────────
    elif action == "web_search" or any(w in text for w in ["search for", "google", "search the web", "look up"]):
        query = params.get("query") or re.sub(r"(search for|google|search the web for|look up)\s*", "", text, flags=re.I).strip()
        engine = params.get("engine", "google")
        ok, msg = web_search(query, engine)
        log_command(text or action, msg, ok)
        return {"success": ok, "message": msg}

    # ── OPEN URL ─────────────────────────────────────────────
    elif action == "open_url":
        url = params.get("url", "")
        ok, msg = open_url(url)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── OPEN WEBSITE ─────────────────────────────────────────
    elif action == "open_website" or any(w in text for w in ["open gmail", "open youtube", "open facebook", "open whatsapp"]):
        site = params.get("site") or re.sub(r"open\s+", "", text, flags=re.I).strip()
        ok, msg = open_website(site)
        log_command(text or action, msg, ok)
        return {"success": ok, "message": msg}

    # ── SCREENSHOT ───────────────────────────────────────────
    elif action == "screenshot" or any(w in text for w in ["screenshot", "take a screenshot", "capture screen"]):
        ok, msg = take_screenshot()
        log_command(text or action, msg, ok)
        return {"success": ok, "message": msg}

    # ── FILE LISTING ─────────────────────────────────────────
    elif action == "list_files":
        path = params.get("path")
        ok, result = list_files(path)
        msg = f"Found {len(result.get('files',[]))} files and {len(result.get('folders',[]))} folders." if ok else result
        log_command(action, msg, ok)
        return {"success": ok, "message": msg, "data": result if ok else {}}

    # ── OPEN FOLDER ──────────────────────────────────────────
    elif action == "open_folder" or any(w in text for w in ["open folder", "open file manager", "file explorer"]):
        path = params.get("path")
        ok, msg = open_folder(path)
        log_command(text or action, msg, ok)
        return {"success": ok, "message": msg}

    # ── CREATE FOLDER ────────────────────────────────────────
    elif action == "create_folder":
        name = params.get("name", "New Folder")
        where = params.get("where")
        ok, msg = create_folder(name, where)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── TYPE TEXT ────────────────────────────────────────────
    elif action == "type_text":
        t = params.get("text", "")
        ok, msg = type_text(t)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── PRESS KEY ────────────────────────────────────────────
    elif action == "press_key":
        key = params.get("key", "enter")
        ok, msg = press_key(key)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── HOTKEY ───────────────────────────────────────────────
    elif action == "hotkey":
        keys = params.get("keys", [])
        ok, msg = hotkey(*keys)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── MOUSE CLICK ──────────────────────────────────────────
    elif action == "click":
        x = params.get("x")
        y = params.get("y")
        btn = params.get("button", "left")
        ok, msg = click_mouse(x, y, btn)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── SCROLL ───────────────────────────────────────────────
    elif action == "scroll":
        direction = params.get("direction", "down")
        clicks = params.get("clicks", 3)
        ok, msg = scroll_mouse(clicks, direction)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── SYSTEM INFO ──────────────────────────────────────────
    elif action == "system_info" or any(w in text for w in ["system info", "cpu usage", "ram usage", "battery"]):
        info = get_system_info()
        parts = [f"Running on {info['platform']}"]
        if "cpu" in info:
            parts.append(f"CPU {info['cpu']}%")
            parts.append(f"RAM {info['ram_used']}GB / {info['ram_total']}GB ({info['ram_percent']}%)")
        if info.get("battery"):
            parts.append(f"Battery {info['battery']}%")
        msg = ", ".join(parts) + "."
        log_command(text or action, msg, True)
        return {"success": True, "message": msg, "data": info}

    # ── SPEAK ────────────────────────────────────────────────
    elif action == "speak":
        t = params.get("text", "")
        ok, msg = speak_text(t)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── VOLUME ───────────────────────────────────────────────
    elif action == "set_volume":
        level = params.get("level", 50)
        ok, msg = set_volume(level)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── SHUTDOWN ─────────────────────────────────────────────
    elif action in ["shutdown", "restart", "sleep"]:
        ok, msg = shutdown_system(action)
        log_command(action, msg, ok)
        return {"success": ok, "message": msg}

    # ── SHELL COMMAND ────────────────────────────────────────
    elif action == "shell":
        cmd = params.get("command", "")
        ok, msg = run_shell_command(cmd)
        log_command(action, msg, ok)
        return {"success": ok, "message": str(msg)[:500]}

    # ── HISTORY ──────────────────────────────────────────────
    elif action == "history":
        return {"success": True, "message": "Command history", "data": command_history[-20:]}

    # ── PING / HEALTH ────────────────────────────────────────
    elif action == "ping":
        return {"success": True, "message": "Kishor Agent is online and ready!", "data": get_system_info()}

    # ── UNKNOWN ──────────────────────────────────────────────
    else:
        msg = f"Command '{action}' not recognized. Try: open_app, web_search, screenshot, list_files, open_url, system_info."
        log_command(action, msg, False)
        return {"success": False, "message": msg}


# ─────────────────────────────────────────────────────────────
# HTTP SERVER
# ─────────────────────────────────────────────────────────────
class KishorHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Suppress default HTTP logs

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/ping":
            self._json_response({"success": True, "message": "Kishor Agent online!", "data": get_system_info()})
        elif path == "/history":
            self._json_response({"success": True, "data": command_history[-20:]})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/command":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                data = json.loads(body.decode("utf-8"))
                result = route_command(data)
                self._json_response(result)
            except json.JSONDecodeError:
                self._json_response({"success": False, "message": "Invalid JSON payload"}, 400)
            except Exception as e:
                self._json_response({"success": False, "message": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def _json_response(self, data, code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)


# ─────────────────────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────────────────────
def main():
    HOST = "localhost"
    PORT = 5000

    server = HTTPServer((HOST, PORT), KishorHandler)

    print(f"  🟢 Kishor Agent running at http://{HOST}:{PORT}")
    print(f"  📋 Endpoints:")
    print(f"     GET  /ping       — Health check")
    print(f"     POST /command    — Execute command")
    print(f"     GET  /history    — Command history")
    print(f"\n  💡 Now open kishor-ai-assistant.html in your browser.")
    print(f"  ⏹️  Press Ctrl+C to stop.\n")
    print("─" * 62)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  👋 Kishor Agent stopped. Goodbye!\n")
        server.shutdown()


if __name__ == "__main__":
    main()
