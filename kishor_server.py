#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║          KISHOR AI DESKTOP AGENT — Python Backend        ║
║          Controls your computer via voice commands       ║
╚══════════════════════════════════════════════════════════╝

Usage:
    python kishor_server.py

Then open kishor-ai-assistant.html in your browser.
"""

import asyncio
import json
import os
import platform
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# ── Auto-install missing packages ─────────────────────────
def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

try:
    import websockets
except ImportError:
    print("📦 Installing websockets...")
    install("websockets")
    import websockets

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    PYAUTOGUI_OK = True
except ImportError:
    print("📦 Installing pyautogui...")
    install("pyautogui")
    try:
        import pyautogui
        pyautogui.FAILSAFE = True
        PYAUTOGUI_OK = True
    except Exception:
        PYAUTOGUI_OK = False
        print("⚠️  pyautogui not available on this system")

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    print("📦 Installing psutil...")
    install("psutil")
    try:
        import psutil
        PSUTIL_OK = True
    except Exception:
        PSUTIL_OK = False

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    print("📦 Installing requests...")
    install("requests")
    try:
        import requests
        REQUESTS_OK = True
    except Exception:
        REQUESTS_OK = False

# ── Platform detection ─────────────────────────────────────
OS = platform.system()  # "Windows", "Darwin", "Linux"
print(f"\n🖥️  Detected OS: {OS}")

# ──────────────────────────────────────────────────────────
# COMMAND EXECUTOR
# ──────────────────────────────────────────────────────────

class KishorCommands:

    # ── Applications ──────────────────────────────────────

    @staticmethod
    def open_browser(url="https://www.google.com"):
        webbrowser.open(url)
        return f"✅ Opened browser → {url}"

    @staticmethod
    def open_app(app_name: str):
        app = app_name.lower().strip()
        result = ""

        app_map_windows = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe",
            "explorer": "explorer.exe",
            "file manager": "explorer.exe",
            "cmd": "cmd.exe",
            "terminal": "cmd.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "settings": "ms-settings:",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "vlc": "vlc.exe",
            "spotify": "spotify.exe",
            "zoom": "zoom.exe",
            "teams": "teams.exe",
            "whatsapp": "whatsapp.exe",
        }
        app_map_mac = {
            "safari": "Safari",
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "terminal": "Terminal",
            "finder": "Finder",
            "calculator": "Calculator",
            "notes": "Notes",
            "mail": "Mail",
            "calendar": "Calendar",
            "spotify": "Spotify",
            "zoom": "zoom.us",
            "word": "Microsoft Word",
            "excel": "Microsoft Excel",
            "vscode": "Visual Studio Code",
            "textedit": "TextEdit",
        }
        app_map_linux = {
            "firefox": "firefox",
            "chrome": "google-chrome",
            "terminal": "gnome-terminal",
            "file manager": "nautilus",
            "calculator": "gnome-calculator",
            "text editor": "gedit",
            "vlc": "vlc",
            "spotify": "spotify",
        }

        try:
            if OS == "Windows":
                target = app_map_windows.get(app, app)
                if target.startswith("ms-"):
                    subprocess.Popen(["start", target], shell=True)
                else:
                    subprocess.Popen(target, shell=True)
                result = f"✅ Opened {app_name} on Windows"

            elif OS == "Darwin":
                target = app_map_mac.get(app, app_name)
                subprocess.Popen(["open", "-a", target])
                result = f"✅ Opened {target} on macOS"

            else:  # Linux
                target = app_map_linux.get(app, app)
                subprocess.Popen([target])
                result = f"✅ Launched {target} on Linux"

        except Exception as e:
            result = f"⚠️ Could not open {app_name}: {e}"

        return result

    # ── Web Search ────────────────────────────────────────

    @staticmethod
    def web_search(query: str):
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"✅ Searching Google for: '{query}'"

    @staticmethod
    def open_youtube(query: str = ""):
        if query:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        else:
            url = "https://www.youtube.com"
        webbrowser.open(url)
        return f"✅ Opened YouTube" + (f" → searching '{query}'" if query else "")

    @staticmethod
    def open_url(url: str):
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"✅ Opened: {url}"

    # ── File System ───────────────────────────────────────

    @staticmethod
    def open_file_manager(path: str = ""):
        target = path or str(Path.home())
        try:
            if OS == "Windows":
                subprocess.Popen(["explorer", target])
            elif OS == "Darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
            return f"✅ Opened file manager at: {target}"
        except Exception as e:
            return f"⚠️ Error: {e}"

    @staticmethod
    def list_files(path: str = ""):
        target = Path(path) if path else Path.home() / "Desktop"
        if not target.exists():
            target = Path.home()
        try:
            files = list(target.iterdir())
            names = [f.name for f in files[:20]]
            return f"📁 Files in {target}:\n" + "\n".join(f"  {'📁' if f.is_dir() else '📄'} {f.name}" for f in files[:20])
        except Exception as e:
            return f"⚠️ Error listing files: {e}"

    @staticmethod
    def create_file(filename: str, content: str = ""):
        try:
            desktop = Path.home() / "Desktop"
            desktop.mkdir(exist_ok=True)
            filepath = desktop / filename
            filepath.write_text(content or f"Created by Kishor AI on {datetime.now()}")
            return f"✅ Created file: {filepath}"
        except Exception as e:
            return f"⚠️ Error creating file: {e}"

    # ── Screenshot ────────────────────────────────────────

    @staticmethod
    def take_screenshot():
        if not PYAUTOGUI_OK:
            return "⚠️ Screenshot not available (pyautogui unavailable)"
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            desktop = Path.home() / "Desktop"
            desktop.mkdir(exist_ok=True)
            filepath = desktop / f"screenshot_{ts}.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(str(filepath))
            return f"✅ Screenshot saved to Desktop: screenshot_{ts}.png"
        except Exception as e:
            return f"⚠️ Screenshot error: {e}"

    # ── System Info ───────────────────────────────────────

    @staticmethod
    def system_info():
        info = {
            "OS": f"{OS} {platform.release()}",
            "Machine": platform.machine(),
            "Processor": platform.processor() or "Unknown",
            "Python": sys.version.split()[0],
            "Time": datetime.now().strftime("%I:%M:%S %p"),
            "Date": datetime.now().strftime("%A, %d %B %Y"),
        }
        if PSUTIL_OK:
            info["CPU Usage"] = f"{psutil.cpu_percent(interval=0.5)}%"
            mem = psutil.virtual_memory()
            info["RAM"] = f"{mem.percent}% used ({round(mem.used/1e9,1)}GB / {round(mem.total/1e9,1)}GB)"
            disk = psutil.disk_usage("/")
            info["Disk"] = f"{disk.percent}% used ({round(disk.free/1e9,1)}GB free)"
        lines = "\n".join(f"  {k}: {v}" for k, v in info.items())
        return f"💻 System Information:\n{lines}"

    @staticmethod
    def get_time():
        now = datetime.now()
        return f"🕐 Current time: {now.strftime('%I:%M:%S %p')}\n📅 Date: {now.strftime('%A, %d %B %Y')}"

    @staticmethod
    def get_battery():
        if not PSUTIL_OK:
            return "⚠️ psutil not available"
        try:
            battery = psutil.sensors_battery()
            if battery:
                status = "Charging" if battery.power_plugged else "Discharging"
                return f"🔋 Battery: {battery.percent:.0f}% ({status})"
            return "🔋 No battery detected (desktop PC)"
        except Exception as e:
            return f"⚠️ Battery info error: {e}"

    # ── Mouse & Keyboard (pyautogui) ──────────────────────

    @staticmethod
    def type_text(text: str):
        if not PYAUTOGUI_OK:
            return "⚠️ pyautogui not available"
        try:
            time.sleep(0.5)
            pyautogui.typewrite(text, interval=0.05)
            return f"✅ Typed: '{text}'"
        except Exception as e:
            return f"⚠️ Type error: {e}"

    @staticmethod
    def press_key(key: str):
        if not PYAUTOGUI_OK:
            return "⚠️ pyautogui not available"
        try:
            pyautogui.press(key)
            return f"✅ Pressed key: {key}"
        except Exception as e:
            return f"⚠️ Key press error: {e}"

    @staticmethod
    def hotkey(*keys):
        if not PYAUTOGUI_OK:
            return "⚠️ pyautogui not available"
        try:
            pyautogui.hotkey(*keys)
            return f"✅ Hotkey: {'+'.join(keys)}"
        except Exception as e:
            return f"⚠️ Hotkey error: {e}"

    @staticmethod
    def scroll(direction: str = "down", amount: int = 3):
        if not PYAUTOGUI_OK:
            return "⚠️ pyautogui not available"
        try:
            clicks = -amount if direction == "down" else amount
            pyautogui.scroll(clicks)
            return f"✅ Scrolled {direction}"
        except Exception as e:
            return f"⚠️ Scroll error: {e}"

    # ── Volume Control ────────────────────────────────────

    @staticmethod
    def volume_up():
        try:
            if OS == "Windows":
                for _ in range(5):
                    subprocess.call(["nircmd", "changesysvolume", "3000"])
            elif OS == "Darwin":
                subprocess.call(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) + 10)"])
            else:
                subprocess.call(["amixer", "-D", "pulse", "sset", "Master", "10%+"])
            return "🔊 Volume increased"
        except:
            if PYAUTOGUI_OK:
                pyautogui.press("volumeup")
                return "🔊 Volume up"
            return "⚠️ Volume control not available"

    @staticmethod
    def volume_down():
        try:
            if OS == "Darwin":
                subprocess.call(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) - 10)"])
            elif OS == "Linux":
                subprocess.call(["amixer", "-D", "pulse", "sset", "Master", "10%-"])
            else:
                if PYAUTOGUI_OK:
                    pyautogui.press("volumedown")
            return "🔉 Volume decreased"
        except:
            return "⚠️ Volume control not available"

    @staticmethod
    def mute():
        if PYAUTOGUI_OK:
            pyautogui.press("volumemute")
            return "🔇 Muted/Unmuted"
        return "⚠️ Mute not available"

    # ── Email ─────────────────────────────────────────────

    @staticmethod
    def open_email():
        webbrowser.open("https://mail.google.com")
        return "📧 Opened Gmail in browser"

    @staticmethod
    def compose_email(to: str = "", subject: str = "", body: str = ""):
        url = f"mailto:{to}?subject={subject}&body={body}"
        webbrowser.open(url)
        return f"📧 Opened email composer → To: {to}"

    # ── System Power ──────────────────────────────────────

    @staticmethod
    def lock_screen():
        try:
            if OS == "Windows":
                subprocess.call(["rundll32.exe", "user32.dll,LockWorkStation"])
            elif OS == "Darwin":
                subprocess.call(["pmset", "displaysleepnow"])
            else:
                subprocess.call(["gnome-screensaver-command", "-l"])
            return "🔒 Screen locked"
        except Exception as e:
            return f"⚠️ Lock error: {e}"

    @staticmethod
    def shutdown(confirm=False):
        if not confirm:
            return "⚠️ Shutdown requires confirmation. Send confirm=true to proceed."
        try:
            if OS == "Windows":
                subprocess.call(["shutdown", "/s", "/t", "10"])
            elif OS == "Darwin":
                subprocess.call(["sudo", "shutdown", "-h", "+1"])
            else:
                subprocess.call(["shutdown", "-h", "+1"])
            return "⚠️ System will shut down in 60 seconds. Run 'shutdown -a' to cancel."
        except Exception as e:
            return f"⚠️ Shutdown error: {e}"

    # ── Clipboard ─────────────────────────────────────────

    @staticmethod
    def copy_to_clipboard(text: str):
        try:
            if OS == "Windows":
                subprocess.run("clip", input=text.encode(), check=True)
            elif OS == "Darwin":
                subprocess.run("pbcopy", input=text.encode(), check=True)
            else:
                subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
            return f"✅ Copied to clipboard: '{text[:50]}...'" if len(text) > 50 else f"✅ Copied: '{text}'"
        except Exception as e:
            return f"⚠️ Clipboard error: {e}"

    # ── Weather ───────────────────────────────────────────

    @staticmethod
    def get_weather(city: str = ""):
        try:
            url = f"https://wttr.in/{city.replace(' ', '+')}?format=3"
            if REQUESTS_OK:
                r = requests.get(url, timeout=5)
                return f"🌤️ Weather: {r.text.strip()}"
            else:
                webbrowser.open(f"https://wttr.in/{city}")
                return f"🌤️ Opened weather for {city or 'your location'}"
        except Exception as e:
            return f"⚠️ Weather error: {e}"


# ──────────────────────────────────────────────────────────
# NATURAL LANGUAGE COMMAND PARSER
# ──────────────────────────────────────────────────────────

cmd = KishorCommands()

def parse_command(text: str) -> str:
    t = text.lower().strip()

    # Time / Date
    if any(w in t for w in ["time", "date", "day", "today"]):
        return cmd.get_time()

    # Screenshot
    if any(w in t for w in ["screenshot", "capture screen", "snap screen"]):
        return cmd.take_screenshot()

    # System info
    if any(w in t for w in ["system info", "cpu", "ram", "memory", "disk", "hardware"]):
        return cmd.system_info()

    # Battery
    if "battery" in t:
        return cmd.get_battery()

    # Weather
    if "weather" in t:
        city = t.replace("weather", "").replace("in", "").replace("for", "").replace("what is the", "").strip()
        return cmd.get_weather(city)

    # Volume
    if "volume up" in t or "increase volume" in t or "louder" in t:
        return cmd.volume_up()
    if "volume down" in t or "decrease volume" in t or "quieter" in t:
        return cmd.volume_down()
    if "mute" in t:
        return cmd.mute()

    # Web Search
    if any(w in t for w in ["search for", "google", "search the web", "look up", "find online"]):
        for phrase in ["search for", "search the web for", "google", "look up", "find online", "search"]:
            if phrase in t:
                query = t.replace(phrase, "").strip()
                if query:
                    return cmd.web_search(query)
        return cmd.open_browser("https://www.google.com")

    # YouTube
    if "youtube" in t:
        query = t.replace("youtube", "").replace("play", "").replace("open", "").strip()
        return cmd.open_youtube(query)

    # Open browser / URL
    if "open browser" in t or "open chrome" in t or "open firefox" in t or "open edge" in t:
        return cmd.open_browser()

    if "open" in t and ("http" in t or ".com" in t or ".in" in t or ".org" in t):
        parts = t.split()
        for part in parts:
            if "." in part and not part.startswith("."):
                return cmd.open_url(part)

    # Email
    if any(w in t for w in ["email", "gmail", "mail", "inbox"]):
        if "compose" in t or "write" in t or "send" in t:
            return cmd.compose_email()
        return cmd.open_email()

    # File manager
    if any(w in t for w in ["file manager", "file explorer", "my files", "open folder", "documents", "desktop folder"]):
        return cmd.open_file_manager()

    # List files
    if any(w in t for w in ["list files", "show files", "what files", "files on desktop"]):
        return cmd.list_files()

    # Lock
    if "lock" in t and "screen" in t:
        return cmd.lock_screen()

    # Shutdown
    if "shutdown" in t or "shut down" in t or "turn off computer" in t:
        return cmd.shutdown(confirm=False)

    # Scroll
    if "scroll down" in t:
        return cmd.scroll("down")
    if "scroll up" in t:
        return cmd.scroll("up")

    # Clipboard
    if "copy" in t:
        content = t.replace("copy", "").strip()
        if content:
            return cmd.copy_to_clipboard(content)

    # Type text
    if t.startswith("type "):
        return cmd.type_text(t[5:])

    # Press key
    if t.startswith("press "):
        key = t.replace("press ", "").strip()
        return cmd.press_key(key)

    # Common keyboard shortcuts
    if "copy all" in t or "select all" in t:
        return cmd.hotkey("ctrl", "a")
    if "undo" in t:
        return cmd.hotkey("ctrl", "z")
    if "save" in t and ("file" in t or "document" in t):
        return cmd.hotkey("ctrl", "s")

    # Open applications
    apps = ["notepad", "calculator", "paint", "word", "excel", "powerpoint",
            "outlook", "spotify", "zoom", "teams", "whatsapp", "vlc",
            "terminal", "cmd", "chrome", "firefox", "edge", "safari", "finder"]
    for app in apps:
        if app in t:
            return cmd.open_app(app)

    if "open" in t:
        app = t.replace("open", "").strip()
        if app:
            return cmd.open_app(app)

    # Help
    if any(w in t for w in ["help", "what can you do", "commands", "capabilities"]):
        return """🤖 Kishor can:
  🌐 open browser / search web / open YouTube
  📁 file manager / list files / create file
  📸 take screenshot
  🔊 volume up / down / mute
  📧 open email / compose email
  💻 system info / battery / time & date
  🔒 lock screen
  ⌨️  type text / press key / hotkeys
  🌤️  get weather [city]
  🎵 open spotify / vlc / media apps
  + open any app by name!"""

    return f"🤔 I understood: '{text}' — try 'help' to see all commands, or be more specific."


# ──────────────────────────────────────────────────────────
# WEBSOCKET SERVER
# ──────────────────────────────────────────────────────────

CLIENTS = set()

async def handler(websocket):
    CLIENTS.add(websocket)
    client_addr = websocket.remote_address
    print(f"🔗 Client connected: {client_addr}")

    # Send welcome
    await websocket.send(json.dumps({
        "type": "connected",
        "message": f"✅ Kishor Desktop Agent connected on {OS}",
        "os": OS,
        "time": datetime.now().strftime("%I:%M %p")
    }))

    try:
        async for raw in websocket:
            try:
                data = json.loads(raw)
                msg_type = data.get("type", "command")
                text = data.get("command", data.get("text", ""))

                print(f"📥 Command: {text}")

                if msg_type == "ping":
                    await websocket.send(json.dumps({"type": "pong", "time": datetime.now().isoformat()}))
                    continue

                if msg_type == "sysinfo":
                    result = cmd.system_info()
                    await websocket.send(json.dumps({"type": "sysinfo", "result": result}))
                    continue

                # Execute command
                result = parse_command(text)
                print(f"📤 Result: {result}")

                await websocket.send(json.dumps({
                    "type": "result",
                    "command": text,
                    "result": result,
                    "time": datetime.now().strftime("%I:%M:%S %p")
                }))

            except json.JSONDecodeError:
                result = parse_command(raw)
                await websocket.send(json.dumps({"type": "result", "result": result}))
            except Exception as e:
                await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    except websockets.exceptions.ConnectionClosedOK:
        pass
    except Exception as e:
        print(f"⚠️ Connection error: {e}")
    finally:
        CLIENTS.discard(websocket)
        print(f"🔌 Client disconnected: {client_addr}")


async def broadcast(message: dict):
    if CLIENTS:
        await asyncio.gather(*[c.send(json.dumps(message)) for c in CLIENTS], return_exceptions=True)


# ──────────────────────────────────────────────────────────
# HTTP SERVER (serves the HTML frontend)
# ──────────────────────────────────────────────────────────

class CORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # suppress HTTP logs


def start_http_server(port=8080):
    server = HTTPServer(("localhost", port), CORSHandler)
    print(f"🌐 HTTP Server: http://localhost:{port}")
    server.serve_forever()


# ──────────────────────────────────────────────────────────
# SYSTEM MONITOR (broadcasts stats every 5s)
# ──────────────────────────────────────────────────────────

async def system_monitor():
    while True:
        await asyncio.sleep(5)
        if CLIENTS and PSUTIL_OK:
            try:
                cpu = psutil.cpu_percent(interval=0.2)
                mem = psutil.virtual_memory()
                stats = {
                    "type": "stats",
                    "cpu": cpu,
                    "ram": mem.percent,
                    "time": datetime.now().strftime("%I:%M:%S %p")
                }
                await broadcast(stats)
            except Exception:
                pass


# ──────────────────────────────────────────────────────────
# MAIN ENTRY
# ──────────────────────────────────────────────────────────

async def main():
    WS_PORT = 8765
    HTTP_PORT = 8080

    print("""
╔══════════════════════════════════════════════════════════╗
║   🤖  KISHOR AI DESKTOP AGENT — Starting Up...          ║
╚══════════════════════════════════════════════════════════╝""")

    # Start HTTP server in background thread
    http_thread = threading.Thread(target=start_http_server, args=(HTTP_PORT,), daemon=True)
    http_thread.start()

    # Start WebSocket server
    print(f"🔌 WebSocket: ws://localhost:{WS_PORT}")
    print(f"📂 Serving files from: {os.getcwd()}")
    print("\n✅ Kishor Agent is READY!")
    print("━" * 58)
    print("  1. Open kishor-ai-assistant.html in your browser")
    print("  2. The page will auto-connect to this agent")
    print("  3. Say 'Hi Kishor' or type a command!")
    print("━" * 58)
    print("  Press Ctrl+C to stop the agent\n")

    # Auto-open the HTML file
    html_path = Path("kishor-ai-assistant.html")
    if html_path.exists():
        time.sleep(1)
        webbrowser.open(f"http://localhost:{HTTP_PORT}/kishor-ai-assistant.html")
        print("🚀 Auto-opened Kishor in your browser!")

    async with websockets.serve(handler, "localhost", WS_PORT):
        await asyncio.gather(
            system_monitor(),
            asyncio.Future()  # run forever
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Kishor Agent stopped. Goodbye!")
