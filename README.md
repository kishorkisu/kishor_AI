# 🤖 KISHOR AI DESKTOP AGENT

Your personal AI assistant that controls your computer by voice.

---

## 📁 FILES IN THIS PACKAGE

| File | Purpose |
|------|---------|
| `kishor_server.py` | Python backend — controls your computer |
| `kishor-ai-assistant.html` | Browser UI — voice input & chat |
| `requirements.txt` | Python dependencies |
| `START_KISHOR.bat` | **Windows** one-click launcher |
| `start_kishor.sh` | **Mac/Linux** one-click launcher |

---

## 🚀 HOW TO START

### Windows
1. Double-click **`START_KISHOR.bat`**
2. Browser opens automatically
3. Say **"Hi Kishor"** → it activates!

### Mac / Linux
```bash
chmod +x start_kishor.sh
./start_kishor.sh
```

### Manual Start
```bash
pip install -r requirements.txt
python kishor_server.py
```
Then open `kishor-ai-assistant.html` in Chrome/Edge.

---

## 🎙️ VOICE COMMANDS

| Say This | What Kishor Does |
|----------|-----------------|
| "Hi Kishor" | Wake word — activates the assistant |
| "Open browser" | Launches your default browser |
| "Search for [topic]" | Google search in browser |
| "Open YouTube [song]" | YouTube search |
| "Take screenshot" | Saves to Desktop |
| "Open file manager" | Opens Explorer/Finder |
| "Open calculator" | Launches calculator app |
| "Open notepad" | Opens Notepad |
| "Open Spotify" | Launches Spotify |
| "Check email" | Opens Gmail in browser |
| "Volume up / down" | Adjusts system volume |
| "Mute" | Toggles mute |
| "System info" | CPU, RAM, Disk stats |
| "Battery status" | Shows battery % |
| "What's the time?" | Current time & date |
| "Weather in [city]" | Current weather |
| "Type [text]" | Types text wherever cursor is |
| "Press [key]" | Presses keyboard key |
| "Scroll down / up" | Scrolls page |
| "Lock screen" | Locks your computer |

---

## ⚙️ REQUIREMENTS

- Python 3.8+
- Chrome / Edge / Firefox browser
- Internet connection (for AI responses)
- Microphone (for voice commands)

---

## 🔧 PORTS USED

- **WebSocket:** `ws://localhost:8765` (agent communication)
- **HTTP:** `http://localhost:8080` (serves the HTML file)

---

## 🛡️ KEYBOARD SHORTCUT

Press **Ctrl+K** in the browser to toggle the microphone on/off.

---

*Kishor AI Agent — Built with Python + WebSockets + Web Speech API*
