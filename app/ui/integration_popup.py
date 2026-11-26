"""
CogniLoad - App Integration System
- Auto-detects ALL running apps that involve typing/work
- Per-app ON/OFF toggle
- Integration popup with overlay offer
- AppWatcher scans running processes every 5s (not just active window)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
import psutil

# ── Comprehensive App Catalogue ───────────────────────────────────────────────
# Key = process name (lowercase, no .exe), value = display info
SUPPORTED_APPS = {
    # ── Coding / IDEs & Editors ───────────────────────────────────────────────
    # Microsoft / VS Family
    "code":           {"name":"Visual Studio Code",  "icon":"💻","cat":"Coding","color":"#00e5ff","desc":"Popular code editor — track load while coding & debugging."},
    "devenv":         {"name":"Visual Studio",       "icon":"🖥","cat":"Coding","color":"#6c5ce7","desc":"Full-stack IDE — monitor enterprise dev sessions."},
    "codeoss":        {"name":"Code - OSS",          "icon":"💻","cat":"Coding","color":"#00e5ff","desc":"Open VS Code build — track coding sessions."},
    "vscodium":       {"name":"VSCodium",            "icon":"💻","cat":"Coding","color":"#29b6f6","desc":"FOSS VS Code build — monitor coding load."},
    "cursor":         {"name":"Cursor (AI Editor)",  "icon":"🤖","cat":"Coding","color":"#7c4dff","desc":"AI-powered editor — track AI-assisted coding load."},
    "windsurf":       {"name":"Windsurf",            "icon":"🏄","cat":"Coding","color":"#4dd0e1","desc":"AI code editor — monitor AI pair programming."},
    # JetBrains Family
    "pycharm64":      {"name":"PyCharm",             "icon":"🐍","cat":"Coding","color":"#00e676","desc":"Python IDE — debugging sessions spike cognitive load."},
    "idea64":         {"name":"IntelliJ IDEA",       "icon":"☕","cat":"Coding","color":"#ff6b6b","desc":"Java/Kotlin IDE — track complex refactoring sessions."},
    "webstorm64":     {"name":"WebStorm",            "icon":"🌐","cat":"Coding","color":"#00cec9","desc":"JS/TS IDE — monitor frontend development sessions."},
    "clion64":        {"name":"CLion",               "icon":"🔧","cat":"Coding","color":"#fdcb6e","desc":"C/C++ IDE — track low-level programming load."},
    "rider64":        {"name":"Rider",               "icon":"🎯","cat":"Coding","color":"#a29bfe","desc":".NET IDE — track C# development cognitive load."},
    "phpstorm64":     {"name":"PhpStorm",            "icon":"🐘","cat":"Coding","color":"#b39ddb","desc":"PHP IDE — monitor web backend development load."},
    "datagrip64":     {"name":"DataGrip",            "icon":"🗄","cat":"Coding","color":"#26c6da","desc":"Database IDE — track SQL & schema work load."},
    "goland64":       {"name":"GoLand",              "icon":"🐹","cat":"Coding","color":"#00acc1","desc":"Go IDE — monitor Golang development sessions."},
    "rubymine64":     {"name":"RubyMine",            "icon":"💎","cat":"Coding","color":"#ef5350","desc":"Ruby/Rails IDE — track web development load."},
    "dataspell64":    {"name":"DataSpell",           "icon":"📊","cat":"Coding","color":"#42a5f5","desc":"Data Science IDE — track ML & analysis load."},
    "aqua64":         {"name":"Aqua (JetBrains)",    "icon":"🧪","cat":"Coding","color":"#29b6f6","desc":"Test automation IDE — monitor testing sessions."},
    "fleet":          {"name":"JetBrains Fleet",     "icon":"🚀","cat":"Coding","color":"#7c4dff","desc":"Next-gen multi-language IDE — monitor projects."},
    # Eclipse Family
    "eclipse":        {"name":"Eclipse IDE",         "icon":"🌘","cat":"Coding","color":"#74b9ff","desc":"Java IDE — monitor enterprise development load."},
    "netbeans64":     {"name":"NetBeans",            "icon":"☕","cat":"Coding","color":"#ffb74d","desc":"Java/PHP IDE — track enterprise coding load."},
    # Lightweight Editors
    "sublime_text":   {"name":"Sublime Text",        "icon":"✏","cat":"Coding","color":"#e17055","desc":"Fast editor — monitor speed-coding sessions."},
    "atom":           {"name":"Atom Editor",         "icon":"⚛","cat":"Coding","color":"#fd79a8","desc":"GitHub editor — track coding and writing load."},
    "notepad++":      {"name":"Notepad++",           "icon":"📝","cat":"Coding","color":"#55efc4","desc":"Multi-language editor — track coding & text work."},
    "notepadplusplus":{"name":"Notepad++",           "icon":"📝","cat":"Coding","color":"#55efc4","desc":"Multi-language editor — track coding & text work."},
    "zed":            {"name":"Zed Editor",          "icon":"⚡","cat":"Coding","color":"#fff176","desc":"Ultra-fast editor — track collaborative coding load."},
    "brackets":       {"name":"Brackets",            "icon":"🎯","cat":"Coding","color":"#f48fb1","desc":"Web editor — track frontend development load."},
    "geany":          {"name":"Geany",               "icon":"🦎","cat":"Coding","color":"#a5d6a7","desc":"Lightweight IDE — monitor multi-language coding."},
    "kate":           {"name":"Kate Editor",         "icon":"🐱","cat":"Coding","color":"#90caf9","desc":"KDE editor — track multi-file coding load."},
    "ultraedit":      {"name":"UltraEdit",           "icon":"✍","cat":"Coding","color":"#b0bec5","desc":"Power editor — track heavy text & code editing."},
    "editplus":       {"name":"EditPlus",            "icon":"✏","cat":"Coding","color":"#80deea","desc":"Code/text editor — monitor mixed work sessions."},
    "textpad":        {"name":"TextPad",             "icon":"📄","cat":"Coding","color":"#b0bec5","desc":"Text/code editor — monitor editing sessions."},
    "bbedit":         {"name":"BBEdit",              "icon":"🖊","cat":"Coding","color":"#80deea","desc":"Mac text/code editor — track coding load."},
    "nova":           {"name":"Nova Editor",         "icon":"💫","cat":"Coding","color":"#ff8a65","desc":"Mac-native IDE — monitor web development."},
    "coderunner":     {"name":"CodeRunner",          "icon":"▶","cat":"Coding","color":"#aed6f1","desc":"Multi-lang runner — monitor quick script sessions."},
    # Terminal / Modal Editors
    "vim":            {"name":"Vim",                 "icon":"🔮","cat":"Coding","color":"#a5d6a7","desc":"Modal editor — track keyboard-intensive coding."},
    "gvim":           {"name":"GVim",                "icon":"🔮","cat":"Coding","color":"#a5d6a7","desc":"GUI Vim — monitor modal coding sessions."},
    "nvim":           {"name":"Neovim",              "icon":"🔮","cat":"Coding","color":"#57a143","desc":"Modern Vim — track plugin-heavy coding load."},
    "emacs":          {"name":"Emacs",               "icon":"🦬","cat":"Coding","color":"#b39ddb","desc":"Power editor — track Lisp & scripting load."},
    "runemacs":       {"name":"Emacs",               "icon":"🦬","cat":"Coding","color":"#b39ddb","desc":"Power editor — track Lisp & scripting load."},
    "helix":          {"name":"Helix Editor",        "icon":"🌀","cat":"Coding","color":"#80cbc4","desc":"Modal editor — monitor keyboard-heavy coding."},
    "nano":           {"name":"GNU Nano",            "icon":"📝","cat":"Coding","color":"#80cbc4","desc":"Terminal editor — monitor quick CLI edits."},
    # C/C++ / Systems
    "codeblocks":     {"name":"Code::Blocks",        "icon":"🧱","cat":"Coding","color":"#ffcc80","desc":"C/C++ IDE — track systems programming load."},
    "devcpp":         {"name":"Dev-C++",             "icon":"🔨","cat":"Coding","color":"#ef9a9a","desc":"C++ IDE — monitor low-level coding sessions."},
    # Android / Mobile
    "studio64":       {"name":"Android Studio",      "icon":"🤖","cat":"Coding","color":"#00b894","desc":"Android IDE — track mobile development load."},
    "androidstudio":  {"name":"Android Studio",      "icon":"🤖","cat":"Coding","color":"#00b894","desc":"Android IDE — monitor mobile dev sessions."},
    # Data Science / ML / Scientific
    "spyder":         {"name":"Spyder IDE",          "icon":"🕷","cat":"Coding","color":"#ef5350","desc":"Scientific Python IDE — track data science load."},
    "rstudio":        {"name":"RStudio",             "icon":"📈","cat":"Coding","color":"#42a5f5","desc":"R IDE — monitor statistical analysis sessions."},
    "matlab":         {"name":"MATLAB",              "icon":"〽","cat":"Coding","color":"#e67e22","desc":"Math/engineering — track numerical computing load."},
    "idle":           {"name":"Python IDLE",         "icon":"🐍","cat":"Coding","color":"#ffd54f","desc":"Python IDLE — monitor beginner coding sessions."},
    "thonny":         {"name":"Thonny",              "icon":"🐍","cat":"Coding","color":"#fff176","desc":"Python beginner IDE — monitor learning load."},
    "jupyter":        {"name":"JupyterLab",          "icon":"📓","cat":"Coding","color":"#f57c00","desc":"Notebooks — track data science & ML sessions."},
    "jupyterlab":     {"name":"JupyterLab",          "icon":"📓","cat":"Coding","color":"#f57c00","desc":"Notebooks — monitor interactive computing load."},
    "dataspell":      {"name":"DataSpell",           "icon":"📊","cat":"Coding","color":"#42a5f5","desc":"Data Science IDE — monitor analysis sessions."},
    # Go / Rust / Misc Language-specific
    "liteide":        {"name":"LiteIDE",             "icon":"🐹","cat":"Coding","color":"#80cbc4","desc":"Go IDE — track Golang project load."},
    # Embedded / Hardware
    "arduino":        {"name":"Arduino IDE",         "icon":"🔌","cat":"Coding","color":"#00acc1","desc":"Arduino — track embedded programming load."},
    "platformio":     {"name":"PlatformIO",          "icon":"🔋","cat":"Coding","color":"#f05033","desc":"Embedded IDE — monitor IoT project load."},
    # Online / Cloud IDEs (as desktop clients)
    "theia":          {"name":"Eclipse Theia",       "icon":"☁","cat":"Coding","color":"#4db6ac","desc":"Cloud IDE — monitor browser-based coding."},
    # Creative / Graphics Coding
    "processing":     {"name":"Processing",          "icon":"🎨","cat":"Coding","color":"#7986cb","desc":"Creative coding — monitor generative art load."},
    # Misc
    "komodo":         {"name":"Komodo IDE",          "icon":"🦎","cat":"Coding","color":"#ce93d8","desc":"Multi-language IDE — monitor polyglot projects."},
    "hex":            {"name":"HexEditor",           "icon":"🔢","cat":"Coding","color":"#b0bec5","desc":"Hex editor — monitor binary/low-level work."},
    "hexeditor":      {"name":"Hex Editor",          "icon":"🔢","cat":"Coding","color":"#b0bec5","desc":"Binary editor — track low-level analysis load."},
    "meld":           {"name":"Meld Diff",           "icon":"🔀","cat":"Coding","color":"#80cbc4","desc":"Diff tool — monitor code review sessions."},
    "winmerge":       {"name":"WinMerge",            "icon":"🔀","cat":"Coding","color":"#90caf9","desc":"File diff tool — track code comparison load."},
    "beyond compare": {"name":"Beyond Compare",      "icon":"🔍","cat":"Coding","color":"#ffcc80","desc":"Diff tool — monitor code comparison sessions."},
    "sourcetree":     {"name":"Sourcetree",          "icon":"🌲","cat":"Coding","color":"#00acc1","desc":"Git GUI — track version control workflow."},
    "typora":         {"name":"Typora",              "icon":"📝","cat":"Coding","color":"#00b4d8","desc":"Markdown editor — track docs & writing load."},
    "marktext":       {"name":"Mark Text",           "icon":"📝","cat":"Coding","color":"#a5d6a7","desc":"Markdown editor — monitor documentation load."},
    "devdocs":        {"name":"DevDocs",             "icon":"📚","cat":"Coding","color":"#90caf9","desc":"API docs viewer — monitor research sessions."},
    "virtualbox":     {"name":"VirtualBox",          "icon":"📦","cat":"Coding","color":"#0db7ed","desc":"VM — monitor cross-platform dev sessions."},
    "vmware":         {"name":"VMware",              "icon":"📦","cat":"Coding","color":"#607d8b","desc":"VM — track virtualized dev environment load."},

    # Office
    "winword":        {"name":"Microsoft Word",      "icon":"📄","cat":"Office",        "color":"#2980b9","desc":"Document editor — track writing & reviewing load."},
    "excel":          {"name":"Microsoft Excel",     "icon":"📊","cat":"Office",        "color":"#27ae60","desc":"Spreadsheets — monitor data analysis sessions."},
    "powerpnt":       {"name":"PowerPoint",          "icon":"📑","cat":"Office",        "color":"#e74c3c","desc":"Presentations — track slide design cognitive load."},
    "outlook":        {"name":"Microsoft Outlook",   "icon":"📧","cat":"Office",        "color":"#3498db","desc":"Email client — monitor email writing & reading."},
    "onenote":        {"name":"OneNote",             "icon":"🗒","cat":"Office",        "color":"#8e44ad","desc":"Notes — track note-taking cognitive patterns."},
    "soffice":        {"name":"LibreOffice",         "icon":"📋","cat":"Office",        "color":"#16a085","desc":"Open-source Office suite — track all document work."},
    "wps":            {"name":"WPS Office",          "icon":"📝","cat":"Office",        "color":"#c0392b","desc":"Office suite — monitor document creation load."},
    "acrobat":        {"name":"Adobe Acrobat",       "icon":"📕","cat":"Office",        "color":"#e74c3c","desc":"PDF editor — track document review sessions."},

    # Browsers
    "chrome":         {"name":"Google Chrome",       "icon":"🌐","cat":"Browser",       "color":"#f39c12","desc":"Browser — monitor research & reading sessions."},
    "msedge":         {"name":"Microsoft Edge",      "icon":"🌐","cat":"Browser",       "color":"#2980b9","desc":"Browser — track web-based work load."},
    "firefox":        {"name":"Firefox",             "icon":"🦊","cat":"Browser",       "color":"#e67e22","desc":"Browser — monitor browsing cognitive load."},
    "opera":          {"name":"Opera",               "icon":"🎭","cat":"Browser",       "color":"#c0392b","desc":"Browser — track web navigation load."},
    "brave":          {"name":"Brave Browser",       "icon":"🦁","cat":"Browser",       "color":"#e67e22","desc":"Browser — monitor browsing sessions."},

    # Communication
    "teams":          {"name":"Microsoft Teams",     "icon":"💬","cat":"Communication", "color":"#6264a7","desc":"Meetings & chat — monitor collaboration load."},
    "slack":          {"name":"Slack",               "icon":"💬","cat":"Communication", "color":"#e01e5a","desc":"Team chat — track communication cognitive load."},
    "zoom":           {"name":"Zoom",                "icon":"📹","cat":"Communication", "color":"#2d8cff","desc":"Video meetings — monitor meeting cognitive load."},
    "discord":        {"name":"Discord",             "icon":"🎮","cat":"Communication", "color":"#7289da","desc":"Chat & voice — track gaming & social load."},
    "skype":          {"name":"Skype",               "icon":"📞","cat":"Communication", "color":"#00aff0","desc":"Video calls — monitor call session load."},
    "telegram":       {"name":"Telegram",            "icon":"✈","cat":"Communication", "color":"#2ca5e0","desc":"Messaging — track rapid communication load."},
    "whatsapp":       {"name":"WhatsApp Desktop",    "icon":"💚","cat":"Communication", "color":"#25d366","desc":"Messaging — monitor chat session load."},

    # Database / Dev Tools
    "dbeaver":        {"name":"DBeaver",             "icon":"🗄","cat":"Dev Tools",     "color":"#5585c4","desc":"Database tool — track SQL query cognitive load."},
    "postman":        {"name":"Postman",             "icon":"🔧","cat":"Dev Tools",     "color":"#ff6c37","desc":"API testing — monitor API debugging load."},
    "insomnia":       {"name":"Insomnia",            "icon":"🌙","cat":"Dev Tools",     "color":"#5c6bc0","desc":"API client — track REST testing sessions."},
    "git-bash":       {"name":"Git Bash",            "icon":"📦","cat":"Dev Tools",     "color":"#f05033","desc":"Git terminal — monitor version control sessions."},
    "gitkraken":      {"name":"GitKraken",           "icon":"🐙","cat":"Dev Tools",     "color":"#179287","desc":"Git GUI — track branching & merging load."},
    "docker desktop": {"name":"Docker Desktop",      "icon":"🐳","cat":"Dev Tools",     "color":"#0db7ed","desc":"Containers — monitor DevOps workflow load."},

    # Terminals
    "cmd":            {"name":"Command Prompt",      "icon":"⬛","cat":"Terminal",      "color":"#aaaaaa","desc":"CMD — track command-line work load."},
    "powershell":     {"name":"PowerShell",          "icon":"🔷","cat":"Terminal",      "color":"#012456","desc":"PowerShell — monitor scripting sessions."},
    "windowsterminal":{"name":"Windows Terminal",    "icon":"⬛","cat":"Terminal",      "color":"#00e5ff","desc":"Terminal — track CLI cognitive load."},
    "wt":             {"name":"Windows Terminal",    "icon":"⬛","cat":"Terminal",      "color":"#00e5ff","desc":"Terminal — track CLI cognitive load."},
    "wsl":            {"name":"WSL / Linux Shell",   "icon":"🐧","cat":"Terminal",      "color":"#f7df1e","desc":"Linux shell — monitor bash session load."},
    "bash":           {"name":"Bash Terminal",       "icon":"🐧","cat":"Terminal",      "color":"#f7df1e","desc":"Bash — track shell scripting load."},

    # Design / Creative
    "figma":          {"name":"Figma",               "icon":"🎨","cat":"Design",        "color":"#ff7262","desc":"UI design — monitor design decision load."},
    "photoshop":      {"name":"Adobe Photoshop",     "icon":"🖼","cat":"Design",        "color":"#001d34","desc":"Photo editing — track creative work load."},
    "illustrator":    {"name":"Adobe Illustrator",   "icon":"✏","cat":"Design",        "color":"#ff7c00","desc":"Vector design — monitor illustration sessions."},
    "xd":             {"name":"Adobe XD",            "icon":"🎭","cat":"Design",        "color":"#ff61f6","desc":"UX design — track prototyping load."},
    "blender":        {"name":"Blender",             "icon":"🔵","cat":"Design",        "color":"#f5792a","desc":"3D modeling — monitor 3D work cognitive load."},

    # Note-taking / Writing
    "notepad":        {"name":"Notepad",             "icon":"📄","cat":"Writing",       "color":"#95a5a6","desc":"Text editor — monitor simple writing sessions."},
    "obsidian":       {"name":"Obsidian",            "icon":"🔮","cat":"Writing",       "color":"#7c3aed","desc":"Notes — track knowledge management load."},
    "notion":         {"name":"Notion",              "icon":"📓","cat":"Writing",       "color":"#000000","desc":"All-in-one — monitor Notion work sessions."},
    "typora":         {"name":"Typora",              "icon":"📝","cat":"Writing",       "color":"#00b4d8","desc":"Markdown editor — track writing cognitive load."},
}

# Categories in display order
CATEGORIES = ["Coding", "Office", "Browser", "Communication", "Dev Tools", "Terminal", "Design", "Writing"]

# ── Integration State Manager ─────────────────────────────────────────────────
class IntegrationState:
    """Tracks ON/OFF state for each app integration"""
    def __init__(self):
        self._states: dict[str, bool] = {}   # key → True (ON) / False (OFF)
        self._seen: set[str] = set()
        self._detected: set[str] = set()    # apps found running on system

    def is_on(self, key: str) -> bool:
        return self._states.get(key, False)

    def toggle(self, key: str) -> bool:
        new = not self._states.get(key, False)
        self._states[key] = new
        return new

    def set(self, key: str, val: bool):
        self._states[key] = val

    def add_seen(self, key: str):
        self._seen.add(key)

    def was_seen(self, key: str) -> bool:
        return key in self._seen

    def add_detected(self, key: str):
        self._detected.add(key)

    def is_detected(self, key: str) -> bool:
        return key in self._detected

    def all_on(self) -> list[str]:
        return [k for k, v in self._states.items() if v]


# Global state instance
integration_state = IntegrationState()


# ── App Watcher ───────────────────────────────────────────────────────────────
class AppWatcher(QObject):
    """Scans ALL running processes every 5s to auto-detect supported apps"""
    new_app_detected = pyqtSignal(str, dict)   # (key, info) — for popup
    app_changed      = pyqtSignal(str)          # current active app name
    running_updated  = pyqtSignal(set)          # all currently running detected keys

    def __init__(self):
        super().__init__()
        self._last_active = None

    def start_watching(self, sys_monitor):
        self._mon = sys_monitor

        # Active window poll (fast — every 2s)
        self._active_t = QTimer(self)
        self._active_t.timeout.connect(self._check_active)
        self._active_t.start(2000)

        # Full process scan (slower — every 6s)
        self._scan_t = QTimer(self)
        self._scan_t.timeout.connect(self._scan_processes)
        self._scan_t.start(6000)

        # Initial scan
        QTimer.singleShot(1500, self._scan_processes)

    def _check_active(self):
        try:
            raw = self._mon.get_active_app().lower()
        except Exception:
            return
        if raw == self._last_active:
            return
        self._last_active = raw
        self.app_changed.emit(raw)

        # Check if active app is supported and not yet seen
        for key in SUPPORTED_APPS:
            if key in raw and not integration_state.was_seen(key):
                integration_state.add_seen(key)
                self.new_app_detected.emit(key, SUPPORTED_APPS[key])
                break

    def _scan_processes(self):
        """Scan all running processes and find which ones are supported apps"""
        found = set()
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    pname = proc.info['name'].lower().replace('.exe', '')
                    for key in SUPPORTED_APPS:
                        if key in pname or pname in key:
                            found.add(key)
                            integration_state.add_detected(key)
                except Exception:
                    continue
        except Exception:
            pass
        self.running_updated.emit(found)

    def mark_seen(self, key: str):
        integration_state.add_seen(key)

    def pyqtSignal(self, *args):
        pass  # handled by QObject inheritance


# Fix: re-import pyqtSignal properly
from PyQt6.QtCore import pyqtSignal as _sig
AppWatcher.new_app_detected = _sig(str, dict)
AppWatcher.app_changed = _sig(str)
AppWatcher.running_updated = _sig(object)


# ── Integration Popup ─────────────────────────────────────────────────────────
POPUP_STYLE = """
QFrame#popCard {
    background: #07101c;
    border: 2px solid #1a3050;
    border-radius: 16px;
}
QPushButton#popEnable {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00c8f0,stop:1 #6c3fff);
    color:#000; border-radius:9px; font-weight:700;
    padding:10px 18px; border:none; font-size:12px;
}
QPushButton#popEnable:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33d6f5,stop:1 #8560ff);
}
QPushButton#popSkip {
    background:transparent; border:1.5px solid #1e3050;
    color:#3d6080; border-radius:9px; padding:10px 14px; font-size:12px;
}
QPushButton#popSkip:hover { border-color:#3d6080; color:#6090a0; }
QPushButton#popX {
    background:transparent; border:none; color:#2a4060;
    font-size:14px; padding:0; min-width:22px; max-width:22px;
    min-height:22px; max-height:22px; border-radius:11px;
}
QPushButton#popX:hover { color:#ff5252; background:rgba(255,82,82,0.12); }
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSignal


class AppIntegrationPopup(QWidget):
    overlay_requested = pyqtSignal(str)
    dismissed         = pyqtSignal(str)

    def __init__(self, app_key: str, info: dict, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.app_key = app_key
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._build(info)
        self._auto = QTimer(self); self._auto.timeout.connect(self._skip); self._auto.start(14000)
        self._cnt = 100
        self._bt  = QTimer(self); self._bt.timeout.connect(self._tick); self._bt.start(140)
        self.adjustSize(); self._pos()

    def _build(self, info: dict):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0)
        card = QFrame(); card.setObjectName("popCard"); card.setFixedWidth(360)
        card.setStyleSheet(POPUP_STYLE)
        root.addWidget(card)

        lay = QVBoxLayout(card); lay.setContentsMargins(20,16,20,18); lay.setSpacing(12)

        # Header
        tr = QHBoxLayout(); tr.setSpacing(6)
        dot = QLabel("●"); dot.setStyleSheet("color:#00e5ff; font-size:9px;")
        hd  = QLabel("🧠 CogniLoad  ·  App Detected")
        hd.setStyleSheet("font-size:10px; color:#3d6080; font-family:'Consolas'; letter-spacing:1px;")
        xb  = QPushButton("✕"); xb.setObjectName("popX"); xb.clicked.connect(self._skip)
        tr.addWidget(dot); tr.addWidget(hd); tr.addStretch(); tr.addWidget(xb)
        lay.addLayout(tr)

        d = QFrame(); d.setFixedHeight(1); d.setStyleSheet("background:#152030; border:none;")
        lay.addWidget(d)

        # App info
        ar = QHBoxLayout(); ar.setSpacing(14)
        ic = QLabel(info['icon']); ic.setStyleSheet("font-size:36px;"); ic.setFixedWidth(46)
        iv = QVBoxLayout(); iv.setSpacing(4)
        nm = QLabel(info['name'])
        nm.setStyleSheet(f"font-size:15px; font-weight:700; color:{info.get('color','#00e5ff')};")
        ds = QLabel(info['desc']); ds.setStyleSheet("font-size:12px; color:#5a7a9a;"); ds.setWordWrap(True)
        ft = QLabel(f"📂 Category: {info.get('cat','General')}  ·  ✔ Overlay  ·  ✔ Live alerts")
        ft.setStyleSheet("font-size:10px; color:#2a4060;"); ft.setWordWrap(True)
        iv.addWidget(nm); iv.addWidget(ds); iv.addWidget(ft)
        ar.addWidget(ic); ar.addLayout(iv, 1)
        lay.addLayout(ar)

        # Buttons
        br = QHBoxLayout(); br.setSpacing(10)
        en = QPushButton(f"  Enable Overlay  ✓")
        en.setObjectName("popEnable"); en.clicked.connect(self._enable)
        sk = QPushButton("Skip Now"); sk.setObjectName("popSkip"); sk.clicked.connect(self._skip)
        br.addWidget(en, 1); br.addWidget(sk)
        lay.addLayout(br)

        # Countdown bar
        self._bar = QFrame(); self._bar.setFixedHeight(3)
        self._bar.setStyleSheet("background:#00e5ff; border-radius:2px;")
        lay.addWidget(self._bar)

    def _tick(self):
        self._cnt = max(0, self._cnt - 1)
        w = int(360 * self._cnt / 100)
        self._bar.setFixedWidth(w)

    def _pos(self):
        sc = QApplication.primaryScreen().geometry()
        self.move(sc.width()-390, sc.height()-self.height()-70)

    def _enable(self):
        self._auto.stop(); self._bt.stop()
        self.overlay_requested.emit(self.app_key); self.close()

    def _skip(self):
        self._auto.stop(); self._bt.stop()
        self.dismissed.emit(self.app_key); self.close()

    def showEvent(self, e):
        super().showEvent(e); self.adjustSize(); self._pos()
