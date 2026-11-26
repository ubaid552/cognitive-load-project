"""
CogniLoad - Main Dashboard Window (Redesigned)
Real-time monitoring, overlay, integration popups, system tray
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTabWidget, QScrollArea, QSizePolicy,
    QSystemTrayIcon, QMenu, QApplication, QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QAction, QColor
from app.ui.overlay import CogniLoadOverlay

from app.monitor.keystroke_hook import KeystrokeHook
from app.monitor.system_monitor import SystemMonitor
from app.ml.predictor import predictor
from app.ml.prediction_engine import generate_predictions, format_predictions_for_db, format_advice_for_db
from app.auth.db import save_report, start_session, end_session
from app.ui.integration_popup import AppWatcher, AppIntegrationPopup
import json, time

# ── Global Stylesheet ────────────────────────────────────────────────────────
STYLE = """
QMainWindow, QWidget { background:#070b12; color:#e0eeff; font-family:'Segoe UI',Arial; }

/* Tabs */
QTabWidget::pane { border:1px solid #152032; border-radius:10px; background:#0b1520; margin-top:-1px; }
QTabBar::tab {
    background:#0b1520; color:#6090b0; border:1px solid #152032;
    padding:10px 22px; margin-right:3px; border-radius:8px 8px 0 0;
    font-size:12px; font-weight:600;
}
QTabBar::tab:selected { background:#0b1520; color:#00e5ff; border-bottom:2.5px solid #00e5ff; font-weight:700; }
QTabBar::tab:hover { color:#a0d0e8; }

/* Scroll */
QScrollArea { border:none; background:transparent; }
QScrollBar:vertical { background:#0b1520; width:5px; border-radius:3px; }
QScrollBar::handle:vertical { background:#2a4060; border-radius:3px; min-height:20px; }

/* Buttons — all clearly visible */
QPushButton {
    border-radius:9px; font-size:12px; font-weight:700;
    padding:10px 18px; border:none; color:#e0eeff;
}

/* Analyze — gradient, black text on bright bg */
QPushButton#btnAnalyze {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00c8f0,stop:1 #6c3fff);
    color: #000000;
    font-weight: 800;
    font-size: 13px;
}
QPushButton#btnAnalyze:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33d6f5,stop:1 #8560ff);
    color: #000000;
}

/* Reset — visible blue-grey text */
QPushButton#btnReset {
    background: #0f1928;
    border: 1.5px solid #2a4060;
    color: #7ab0cc;
    font-weight: 600;
}
QPushButton#btnReset:hover { border-color:#00e5ff; color:#00e5ff; background:#101e30; }

/* Ghost — readable steel blue */
QPushButton#btnGhost {
    background: transparent;
    border: 1.5px solid #2a4060;
    color: #7ab0cc;
    font-weight: 600;
}
QPushButton#btnGhost:hover { border-color:#00e5ff; color:#00e5ff; background:rgba(0,229,255,0.05); }

/* Logout */
QPushButton#btnLogout {
    background: #0f1928;
    border: 1px solid #2a4060;
    color: #7ab0cc;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton#btnLogout:hover { border-color:#ff5252; color:#ff5252; background:#1a0f0f; }

/* Cards */
QFrame#card { background:#0b1520; border:1px solid #1a2840; border-radius:12px; }
QFrame#cardHigh { background:#0d0809; border:2px solid #ff5252; border-radius:12px; }
QFrame#cardLow  { background:#080d0a; border:2px solid #00e676; border-radius:12px; }
QFrame#metricCell { background:#0e1830; border:1px solid #1e3050; border-radius:10px; }

/* Labels */
QLabel#secTitle { font-size:10px; color:#5090b0; letter-spacing:2px; font-weight:700; }
QLabel#lvlHigh { font-family:'Consolas',monospace; font-size:32px; font-weight:700; color:#ff5252; }
QLabel#lvlLow  { font-family:'Consolas',monospace; font-size:32px; font-weight:700; color:#00e676; }
QLabel#lvlIdle { font-family:'Consolas',monospace; font-size:26px; font-weight:700; color:#4a7a9a; }
QLabel#metricNum { font-family:'Consolas',monospace; font-size:24px; font-weight:700; color:#00e5ff; }
QLabel#metricLbl { font-size:10px; color:#5090b0; letter-spacing:1px; font-weight:600; }
QLabel#topPredTitle { font-size:13px; font-weight:700; color:#e0eeff; }
QLabel#topPredAdv { font-size:11px; color:#7ab0cc; }
QLabel#appName { font-family:'Consolas',monospace; font-size:13px; color:#00e5ff; font-weight:600; }
QLabel#dotLive { font-size:11px; color:#00e676; font-family:'Consolas'; letter-spacing:1px; font-weight:700; }

/* Progress */
QProgressBar { background:#0f1928; border-radius:4px; border:none; }
QProgressBar::chunk { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00c8f0,stop:1 #6c3fff); border-radius:4px; }
"""



def card(parent=None, obj="card"):
    f = QFrame(parent); f.setObjectName(obj)
    return f


def sec_title(text):
    l = QLabel(text.upper()); l.setObjectName("secTitle")
    return l


class AnalyzeWorker(QThread):
    result_ready = pyqtSignal(dict, list)
    error_signal = pyqtSignal(str)

    def __init__(self, events, total_ms, stats):
        super().__init__()
        self.events = events; self.total_ms = total_ms; self.stats = stats

    def run(self):
        try:
            r = predictor.predict(self.events, self.total_ms)
            if 'error' in r:
                self.error_signal.emit(r['error']); return
            preds = generate_predictions(r, self.stats)
            self.result_ready.emit(r, preds)
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self, user: dict, auth_manager):
        super().__init__()
        self.user = user
        self.auth = auth_manager
        self.hook = KeystrokeHook()
        self.sys_monitor = SystemMonitor()
        self.session_id = start_session(user['id'])
        self.last_result = None
        self.last_predictions = []
        self._worker = None
        self._popups = []
        self._monitored_apps = set()
        self._overlay = None

        self.setWindowTitle(f"CogniLoad  —  {user.get('username','User')}")
        self.setMinimumSize(1120, 720)
        self.setStyleSheet(STYLE)

        self._build_ui()
        self._setup_tray()
        self._start_monitoring()
        self._setup_app_watcher()
        self._create_overlay()

        # Timers
        self._live_timer = QTimer(); self._live_timer.timeout.connect(self._refresh_live); self._live_timer.start(1000)
        self._auto_timer = QTimer(); self._auto_timer.timeout.connect(self._auto_analyze); self._auto_timer.start(60000)

    # ── Build UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        c = QWidget(); self.setCentralWidget(c)
        root = QVBoxLayout(c); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._build_header())

        self.tabs = QTabWidget(); self.tabs.setContentsMargins(0,0,0,0)
        self.tabs.addTab(self._build_dashboard(), "  📊  Dashboard  ")
        self.tabs.addTab(self._build_reports_tab(), "  📋  Reports  ")
        self.tabs.addTab(self._build_integrations_tab(), "  🔌  Integrations  ")
        if self.user.get('account_type') == 'supervisor':
            from app.ui.supervisor import SupervisorPanel
            self.tabs.addTab(SupervisorPanel(self.user, self.auth), "  👥  Team  ")
        root.addWidget(self.tabs)

    def _build_header(self):
        h = QFrame(); h.setFixedHeight(58)
        h.setStyleSheet("background:#080e18; border-bottom:1.5px solid #0f1f30;")
        hl = QHBoxLayout(h); hl.setContentsMargins(22,0,22,0); hl.setSpacing(0)

        logo = QLabel("🧠  COGNILOAD")
        logo.setStyleSheet("font-family:'Consolas'; font-size:15px; font-weight:700; color:#00e5ff; letter-spacing:2px;")

        self._dot = QLabel("● LIVE"); self._dot.setObjectName("dotLive")

        self._hdr_app = QLabel("—")
        self._hdr_app.setStyleSheet("color:#3d6080; font-size:11px; font-family:'Consolas';")

        acc_type = self.user.get('account_type','user').upper()
        color = "#a78bff" if acc_type == "SUPERVISOR" else "#5a7a9a"
        uname = self.user.get('full_name') or self.user.get('username')
        user_lbl = QLabel(f"{'👑' if acc_type=='SUPERVISOR' else '👤'}  {uname}  [{acc_type}]")
        user_lbl.setStyleSheet(f"color:{color}; font-size:11px;")

        logout = QPushButton("Logout"); logout.setObjectName("btnLogout"); logout.setFixedWidth(78)
        logout.clicked.connect(self._logout)

        hl.addWidget(logo)
        hl.addSpacing(18)
        hl.addWidget(self._dot)
        hl.addStretch()
        hl.addWidget(self._hdr_app)
        hl.addSpacing(24)
        hl.addWidget(user_lbl)
        hl.addSpacing(14)
        hl.addWidget(logout)
        return h

    # ── Dashboard Tab ─────────────────────────────────────────────────────────
    def _build_dashboard(self):
        w = QWidget()
        outer = QHBoxLayout(w); outer.setContentsMargins(18,18,18,18); outer.setSpacing(16)

        # ── LEFT COLUMN ────────────────────────────────────────────────────
        left = QVBoxLayout(); left.setSpacing(14)

        # Live Metrics Grid
        mc = card(); mc_l = QVBoxLayout(mc); mc_l.setContentsMargins(20,16,20,16); mc_l.setSpacing(12)
        mc_l.addWidget(sec_title("Live Session Metrics"))

        grid = QGridLayout(); grid.setSpacing(10)
        self._mw = {}
        defs = [
            ("keystrokes","⌨","Keystrokes","0"),
            ("wpm","✍","Words / Min","0"),
            ("backspaces","⌫","Backspaces","0"),
            ("avg_iki_ms","⏱","Avg IKI ms","0"),
            ("long_pauses","💤","Long Pauses","0"),
            ("session_minutes","🕐","Session min","0"),
        ]
        for i,(k,ico,lbl,def_) in enumerate(defs):
            cell = QFrame(); cell.setObjectName("metricCell")
            cl = QVBoxLayout(cell); cl.setContentsMargins(14,12,14,12); cl.setSpacing(3)
            num = QLabel(def_); num.setObjectName("metricNum")
            lbl_w = QLabel(f"{ico}  {lbl}"); lbl_w.setObjectName("metricLbl")
            cl.addWidget(num); cl.addWidget(lbl_w)
            self._mw[k] = num
            grid.addWidget(cell, i//3, i%3)
        mc_l.addLayout(grid)
        left.addWidget(mc)

        # Controls row
        ctrl = card(); cl2 = QHBoxLayout(ctrl); cl2.setContentsMargins(16,12,16,12); cl2.setSpacing(10)
        an_btn = QPushButton("⚡  Analyze Now"); an_btn.setObjectName("btnAnalyze"); an_btn.setFixedHeight(44)
        an_btn.clicked.connect(self._do_analyze)
        rs_btn = QPushButton("↺  Reset"); rs_btn.setObjectName("btnReset"); rs_btn.setFixedHeight(44); rs_btn.setFixedWidth(110)
        rs_btn.clicked.connect(self._reset_session)
        self._status_lbl = QLabel("Monitoring all apps — start typing to begin")
        self._status_lbl.setStyleSheet("color:#3d6080; font-size:11px;")
        cl2.addWidget(an_btn); cl2.addWidget(rs_btn); cl2.addStretch(); cl2.addWidget(self._status_lbl)
        left.addWidget(ctrl)

        # Active app
        ac = card(); al = QHBoxLayout(ac); al.setContentsMargins(16,12,16,12); al.setSpacing(12)
        al.addWidget(sec_title("Active App"))
        self._app_lbl = QLabel("—"); self._app_lbl.setObjectName("appName")
        al.addWidget(self._app_lbl); al.addStretch()
        left.addWidget(ac)
        left.addStretch()
        outer.addLayout(left, 3)

        # ── RIGHT COLUMN ───────────────────────────────────────────────────
        right = QVBoxLayout(); right.setSpacing(14)

        # Cognitive Load Result
        self._res_card = card(); self._res_card.setMinimumWidth(310)
        rl = QVBoxLayout(self._res_card); rl.setContentsMargins(24,22,24,22); rl.setSpacing(8)
        rl.setAlignment(Qt.AlignmentFlag.AlignTop)
        rl.addWidget(sec_title("Cognitive Load"))
        rl.addSpacing(10)

        self._load_icon = QLabel("🧠"); self._load_icon.setStyleSheet("font-size:42px;")
        self._load_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.addWidget(self._load_icon)

        self._load_lbl = QLabel("WAITING…"); self._load_lbl.setObjectName("lvlIdle")
        self._load_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.addWidget(self._load_lbl)

        self._load_sub = QLabel("Type anything to begin monitoring")
        self._load_sub.setStyleSheet("color:#3d6080; font-size:12px;")
        self._load_sub.setAlignment(Qt.AlignmentFlag.AlignCenter); self._load_sub.setWordWrap(True)
        rl.addWidget(self._load_sub)

        rl.addSpacing(12)
        rl.addWidget(sec_title("Confidence"))
        self._conf_bar = QProgressBar(); self._conf_bar.setRange(0,100); self._conf_bar.setValue(0)
        self._conf_bar.setFixedHeight(7); self._conf_bar.setTextVisible(False)
        self._conf_val = QLabel("—"); self._conf_val.setStyleSheet("color:#00e5ff; font-family:'Consolas'; font-size:13px;")
        rl.addWidget(self._conf_bar); rl.addWidget(self._conf_val)
        right.addWidget(self._res_card)

        # Top Prediction preview
        pc = card(); pl = QVBoxLayout(pc); pl.setContentsMargins(18,14,18,14); pl.setSpacing(8)
        pl.addWidget(sec_title("Top Prediction"))
        self._pred_title = QLabel("Run analysis to see predictions")
        self._pred_title.setObjectName("topPredTitle"); self._pred_title.setWordWrap(True)
        self._pred_adv = QLabel(""); self._pred_adv.setObjectName("topPredAdv"); self._pred_adv.setWordWrap(True)
        see_btn = QPushButton("View Full Report →"); see_btn.setObjectName("btnGhost")
        see_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        pl.addWidget(self._pred_title); pl.addWidget(self._pred_adv)
        pl.addSpacing(4); pl.addWidget(see_btn)
        right.addWidget(pc)
        right.addStretch()
        outer.addLayout(right, 2)
        return w

    def _build_reports_tab(self):
        from app.ui.reports import ReportsPanel
        self._reports_panel = ReportsPanel(self.user)
        return self._reports_panel

    # ── Integrations Tab ─────────────────────────────────────────────────────
    def _build_integrations_tab(self):
        from app.ui.integration_popup import SUPPORTED_APPS, CATEGORIES, integration_state
        w = QWidget()
        root = QVBoxLayout(w); root.setContentsMargins(20,18,20,18); root.setSpacing(14)

        # ── Header ───────────────────────────────────────────────────────────
        hdr_row = QHBoxLayout()
        t = QLabel("🔌  App Integrations")
        t.setStyleSheet("font-size:18px; font-weight:700; color:#ddeeff;")

        # Master toggle: Enable All / Disable All
        self._master_on  = QPushButton("⚡  Enable All")
        self._master_off = QPushButton("⏹  Disable All")
        for b, obj in [(self._master_on,"btnAnalyze"),(self._master_off,"btnReset")]:
            b.setObjectName(obj); b.setFixedHeight(36)
        self._master_on.clicked.connect(lambda: self._set_all_integrations(True))
        self._master_off.clicked.connect(lambda: self._set_all_integrations(False))

        hdr_row.addWidget(t); hdr_row.addStretch()
        hdr_row.addWidget(self._master_on); hdr_row.addSpacing(8); hdr_row.addWidget(self._master_off)
        root.addLayout(hdr_row)

        sub = QLabel(
            "Toggle monitoring ON/OFF per app.  "
            "CogniLoad auto-detects running apps and scans for new ones every 6 seconds."
        )
        sub.setStyleSheet("color:#3d6080; font-size:11px;"); sub.setWordWrap(True)
        root.addWidget(sub)

        # ── Scrollable card grid ──────────────────────────────────────────────
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_l = QVBoxLayout(inner); inner_l.setContentsMargins(0,0,0,0); inner_l.setSpacing(14)

        self._app_toggle_btns   = {}   # key → QPushButton (the ON/OFF toggle)
        self._app_status_labels = {}   # key → QLabel (status text)
        self._app_cards         = {}   # key → QFrame (card widget)

        for cat in CATEGORIES:
            apps_in_cat = [(k,v) for k,v in SUPPORTED_APPS.items() if v.get('cat') == cat]
            if not apps_in_cat:
                continue

            # Category heading
            cat_lbl = QLabel(cat.upper())
            cat_lbl.setStyleSheet(
                "font-size:10px; color:#3d6080; letter-spacing:2px; "
                "font-weight:700; font-family:'Consolas';"
            )
            inner_l.addWidget(cat_lbl)

            # Grid row for this category
            row_widget = QWidget()
            row_grid = QGridLayout(row_widget)
            row_grid.setSpacing(10); row_grid.setContentsMargins(0,0,0,0)

            for idx, (key, info) in enumerate(apps_in_cat):
                card_w = QFrame()
                card_w.setObjectName("card")
                card_w.setStyleSheet(
                    "QFrame#card { background:#0b1520; border:1px solid #152032; border-radius:12px; }"
                )
                cl = QVBoxLayout(card_w); cl.setContentsMargins(14,12,14,12); cl.setSpacing(8)

                # Top row: icon + name + toggle
                tr = QHBoxLayout(); tr.setSpacing(8)
                ico_lbl = QLabel(info['icon']); ico_lbl.setStyleSheet("font-size:22px;"); ico_lbl.setFixedWidth(30)
                nm_lbl  = QLabel(info['name'])
                nm_lbl.setStyleSheet(f"font-size:12px; font-weight:700; color:{info.get('color','#ddeeff')};")

                tog_btn = QPushButton("OFF")
                tog_btn.setFixedSize(60, 28)
                tog_btn.setCheckable(True)
                tog_btn.setChecked(integration_state.is_on(key))
                self._style_toggle(tog_btn, integration_state.is_on(key))
                tog_btn.clicked.connect(lambda checked, k=key, b=tog_btn: self._toggle_app(k, b))

                tr.addWidget(ico_lbl); tr.addWidget(nm_lbl, 1); tr.addWidget(tog_btn)
                cl.addLayout(tr)

                # Description
                ds_lbl = QLabel(info['desc'])
                ds_lbl.setStyleSheet("font-size:11px; color:#3d6080;"); ds_lbl.setWordWrap(True)
                cl.addWidget(ds_lbl)

                # Status label
                st_lbl = QLabel("⏳ Not detected yet")
                st_lbl.setStyleSheet("font-size:10px; color:#2a4060; font-family:'Consolas';")
                cl.addWidget(st_lbl)

                self._app_toggle_btns[key]   = tog_btn
                self._app_status_labels[key] = st_lbl
                self._app_cards[key]         = card_w

                row_grid.addWidget(card_w, idx//2, idx%2)

            inner_l.addWidget(row_widget)

        inner_l.addStretch()
        scroll.setWidget(inner); root.addWidget(scroll)
        return w

    def _style_toggle(self, btn: QPushButton, is_on: bool):
        """Style the ON/OFF toggle button"""
        if is_on:
            btn.setText("ON")
            btn.setStyleSheet(
                "QPushButton { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #00c851,stop:1 #00e676); color:#000; border-radius:8px;"
                " font-weight:700; font-size:11px; border:none; }"
                "QPushButton:hover { background:#33eb91; }"
            )
        else:
            btn.setText("OFF")
            btn.setStyleSheet(
                "QPushButton { background:#0f1928; border:1.5px solid #1e3050;"
                " color:#3d6080; border-radius:8px; font-weight:700; font-size:11px; }"
                "QPushButton:hover { border-color:#5a7a9a; color:#5a7a9a; }"
            )

    def _toggle_app(self, key: str, btn: QPushButton):
        """Toggle ON/OFF for a specific app"""
        from app.ui.integration_popup import integration_state, SUPPORTED_APPS
        new_state = integration_state.toggle(key)
        self._style_toggle(btn, new_state)
        btn.setChecked(new_state)

        st = self._app_status_labels.get(key)
        if st:
            if new_state:
                detected = integration_state.is_detected(key)
                if detected:
                    st.setText("✅ Monitoring active — overlay enabled")
                    st.setStyleSheet("font-size:10px; color:#00e676; font-family:'Consolas';")
                else:
                    st.setText("✅ ON — will activate when app is detected")
                    st.setStyleSheet("font-size:10px; color:#00e5ff; font-family:'Consolas';")
                # Show overlay if it's running
                if detected and self._overlay:
                    self._overlay.show()
            else:
                st.setText("⏸ Monitoring paused")
                st.setStyleSheet("font-size:10px; color:#5a7a9a; font-family:'Consolas';")

        info = SUPPORTED_APPS.get(key, {})
        name = info.get('name', key)
        if self._tray:
            msg = f"{'Now monitoring' if new_state else 'Stopped monitoring'} {name}"
            self._tray.showMessage("CogniLoad Integration", msg,
                QSystemTrayIcon.MessageIcon.Information, 2500)

    def _set_all_integrations(self, state: bool):
        """Enable or disable ALL integrations at once"""
        from app.ui.integration_popup import integration_state
        for key, btn in self._app_toggle_btns.items():
            integration_state.set(key, state)
            self._style_toggle(btn, state)
            btn.setChecked(state)
            st = self._app_status_labels.get(key)
            if st:
                if state and integration_state.is_detected(key):
                    st.setText("✅ Monitoring active")
                    st.setStyleSheet("font-size:10px; color:#00e676; font-family:'Consolas';")
                elif state:
                    st.setText("✅ ON — waiting for app")
                    st.setStyleSheet("font-size:10px; color:#00e5ff; font-family:'Consolas';")
                else:
                    st.setText("⏸ Paused")
                    st.setStyleSheet("font-size:10px; color:#5a7a9a; font-family:'Consolas';")

    # ── Monitoring + Watcher ─────────────────────────────────────────────────
    def _start_monitoring(self):
        self.hook.start()
        self.sys_monitor.start()

    def _create_overlay(self):
        """Create the floating overlay (hidden by default, shown when integration accepted)"""
        self._overlay = CogniLoadOverlay()
        self._overlay.analyze_requested.connect(self._do_analyze)
        self._overlay.closed.connect(self._on_overlay_closed)
        # Don't show yet — shown when user accepts an integration

    def _on_overlay_closed(self):
        """User closed overlay — update integrations tab"""
        pass

    def _setup_app_watcher(self):
        self._watcher = AppWatcher()
        self._watcher.new_app_detected.connect(self._show_integration_popup)
        self._watcher.app_changed.connect(self._on_app_change)
        self._watcher.running_updated.connect(self._on_running_updated)
        self._watcher.start_watching(self.sys_monitor)

    @pyqtSlot(object)
    def _on_running_updated(self, found: set):
        """Called every 6s with all currently running supported apps"""
        from app.ui.integration_popup import integration_state, SUPPORTED_APPS
        for key in SUPPORTED_APPS:
            st_lbl = self._app_status_labels.get(key)
            card   = self._app_cards.get(key)
            if not st_lbl:
                continue
            is_running = key in found
            is_on      = integration_state.is_on(key)

            if is_running and is_on:
                st_lbl.setText("✅ Running  ·  Monitoring ON")
                st_lbl.setStyleSheet("font-size:10px; color:#00e676; font-family:'Consolas';")
                if card:
                    card.setStyleSheet(
                        "QFrame#card { background:#060f09; border:1.5px solid #00e676; border-radius:12px; }"
                    )
            elif is_running and not is_on:
                st_lbl.setText("🟡 Running  ·  Monitoring OFF")
                st_lbl.setStyleSheet("font-size:10px; color:#f39c12; font-family:'Consolas';")
                if card:
                    card.setStyleSheet(
                        "QFrame#card { background:#0f0e06; border:1.5px solid #f39c12; border-radius:12px; }"
                    )
            else:
                if not is_on:
                    st_lbl.setText("⬛ Not running")
                    st_lbl.setStyleSheet("font-size:10px; color:#2a4060; font-family:'Consolas';")
                else:
                    st_lbl.setText("🔵 ON  ·  Waiting for app to launch")
                    st_lbl.setStyleSheet("font-size:10px; color:#00e5ff; font-family:'Consolas';")
                if card:
                    card.setStyleSheet(
                        "QFrame#card { background:#0b1520; border:1px solid #152032; border-radius:12px; }"
                    )

    @pyqtSlot(str)
    def _on_app_change(self, raw: str):
        self._hdr_app.setText(raw[:30] if raw else "—")
        self._app_lbl.setText(raw[:40] if raw else "—")

    @pyqtSlot(str, dict)
    def _show_integration_popup(self, key: str, info: dict):
        popup = AppIntegrationPopup(key, info)
        popup.overlay_requested.connect(self._on_overlay_requested)
        popup.dismissed.connect(lambda k: None)
        popup.show()
        self._popups.append(popup)

    @pyqtSlot(str)
    def _on_overlay_requested(self, key: str):
        """User said YES to overlay — show floating overlay on top of their app"""
        from app.ui.integration_popup import SUPPORTED_APPS
        info = SUPPORTED_APPS.get(key, {})
        name = info.get('name', key)
        self._watcher.mark_seen(key)

        # Update integrations tab status
        if key in self._app_status_labels:
            self._app_status_labels[key].setText("✅ Overlay Active")
            self._app_status_labels[key].setStyleSheet("color:#00e676; font-size:11px; font-weight:600;")

        # Show the floating overlay
        if self._overlay:
            self._overlay.show()

        if self._tray:
            self._tray.showMessage(
                f"CogniLoad  ·  {name}",
                f"Overlay is now active!\nReal-time cognitive load shown on top of {name}.\nDrag it anywhere on screen.",
                QSystemTrayIcon.MessageIcon.Information, 4000
            )

    @pyqtSlot()
    def _refresh_live(self):
        s = self.hook.get_live_stats()
        for k, w in self._mw.items():
            w.setText(str(s.get(k, 0)))
        app = self.sys_monitor.get_active_app()
        self._hdr_app.setText(app[:30] if app else "—")
        self._app_lbl.setText(app if app else "—")
        # Feed overlay
        if self._overlay and self._overlay.isVisible():
            self._overlay.update_stats(s, app)

    def _auto_analyze(self):
        if len(self.hook.get_events_snapshot()) >= 10:
            self._do_analyze(silent=True)

    def _do_analyze(self, silent=False):
        events = self.hook.get_events_snapshot()
        if len(events) < 5:
            self._status_lbl.setText("Need more keystrokes — keep typing!"); return
        self._status_lbl.setText("Analyzing…")
        stats = self.hook.get_live_stats()
        self._worker = AnalyzeWorker(events, self.hook.get_total_time_ms(), stats)
        self._worker.result_ready.connect(self._on_result)
        self._worker.error_signal.connect(lambda e: self._status_lbl.setText(f"Error: {e}"))
        self._worker.start()

    @pyqtSlot(dict, list)
    def _on_result(self, result, preds):
        self.last_result = result; self.last_predictions = preds
        level = result.get('level','Low'); conf = result.get('confidence', 0)
        metrics = result.get('metrics', {})
        app = self.sys_monitor.get_active_app()

        # Update load card
        if level == 'High':
            self._load_lbl.setText("HIGH LOAD"); self._load_lbl.setObjectName("lvlHigh")
            self._load_icon.setText("⚠️"); self._load_sub.setText("High cognitive strain detected")
            self._res_card.setObjectName("cardHigh")
        else:
            self._load_lbl.setText("LOW LOAD"); self._load_lbl.setObjectName("lvlLow")
            self._load_icon.setText("✅"); self._load_sub.setText("Comfortable cognitive state")
            self._res_card.setObjectName("cardLow")
        self._res_card.style().unpolish(self._res_card); self._res_card.style().polish(self._res_card)
        self._load_lbl.style().unpolish(self._load_lbl); self._load_lbl.style().polish(self._load_lbl)

        self._conf_bar.setValue(int(conf)); self._conf_val.setText(f"{conf}%")
        self._status_lbl.setText(f"Last analyzed: {time.strftime('%H:%M:%S')}")

        # Update overlay
        if self._overlay:
            self._overlay.update_result(level, conf)

        if preds:
            self._pred_title.setText(preds[0]['title'])
            self._pred_adv.setText(f"💡 {preds[0]['advice'][0]}")

        # Save
        save_report(
            user_id=self.user['id'], session_id=self.session_id,
            load_level=level, confidence=conf,
            keystrokes=metrics.get('total_keystrokes',0),
            backspaces=metrics.get('backspaces',0),
            wpm=metrics.get('words_per_min',0),
            avg_iki=metrics.get('avg_pause_ms',0),
            long_pauses=metrics.get('long_pauses',0),
            active_app=app,
            predictions=format_predictions_for_db(preds),
            advice=format_advice_for_db(preds),
            raw_metrics=json.dumps(metrics)
        )
        if hasattr(self, '_reports_panel'):
            self._reports_panel.refresh()
        if level == 'High' and self._tray:
            self._tray.showMessage("CogniLoad ⚠",
                f"High load! ({conf}%) — {preds[0]['title'] if preds else ''}",
                QSystemTrayIcon.MessageIcon.Warning, 5000)

    def _reset_session(self):
        self.hook.reset()
        self.last_result = None; self.last_predictions = []
        self._load_lbl.setText("WAITING…"); self._load_lbl.setObjectName("lvlIdle")
        self._load_icon.setText("🧠"); self._load_sub.setText("Session reset — start typing")
        self._res_card.setObjectName("card")
        self._res_card.style().unpolish(self._res_card); self._res_card.style().polish(self._res_card)
        self._load_lbl.style().unpolish(self._load_lbl); self._load_lbl.style().polish(self._load_lbl)
        self._conf_bar.setValue(0); self._conf_val.setText("—")
        self._pred_title.setText("Run analysis to see predictions"); self._pred_adv.setText("")
        self._status_lbl.setText("Session reset")
        self.session_id = start_session(self.user['id'])

    # ── Tray ─────────────────────────────────────────────────────────────────
    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("CogniLoad — Monitoring Active")
        m = QMenu()
        m.addAction(QAction("📊  Show Dashboard", self, triggered=self.show))
        m.addAction(QAction("⚡  Analyze Now", self, triggered=self._do_analyze))
        m.addAction(QAction("🔲  Show/Hide Overlay", self, triggered=self._toggle_overlay))
        m.addSeparator()
        m.addAction(QAction("✕  Quit CogniLoad", self, triggered=self._quit_app))
        self._tray.setContextMenu(m)
        # Connect double-click to restore window
        self._tray.activated.connect(
            lambda r: self.show() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self._tray.show()  # Show the tray icon immediately

    def _toggle_overlay(self):
        if self._overlay:
            if self._overlay.isVisible():
                self._overlay.hide()
            else:
                self._overlay.show()

    def closeEvent(self, event):
        event.ignore(); self.hide()
        self._tray.showMessage("CogniLoad",
            "Running in background — monitoring all apps.\nDouble-click tray icon to restore.",
            QSystemTrayIcon.MessageIcon.Information, 3000)

    def _quit_app(self):
        self.hook.stop(); self.sys_monitor.stop()
        s = self.hook.get_live_stats()
        end_session(self.session_id, s['keystrokes'], s['backspaces'],
                    s['wpm'], s['avg_iki_ms'],
                    self.last_result['level'] if self.last_result else 'N/A',
                    self.sys_monitor.get_active_app())
        QApplication.quit()

    def _logout(self):
        self.hook.stop(); self.sys_monitor.stop(); self.auth.logout()
        from app.ui.login_window import LoginWindow
        self._lw = LoginWindow(self.auth)
        self._lw.login_success.connect(self._reopen)
        self._lw.show(); self.close()

    def _reopen(self, user):
        self._lw.close()
        self._nw = MainWindow(user, self.auth); self._nw.show()
