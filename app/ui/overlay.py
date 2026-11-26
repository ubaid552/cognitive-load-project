"""
CogniLoad - Floating Overlay Widget
A small always-on-top window that shows real-time cognitive load
ON TOP of whatever app the user is currently using.
Draggable, semi-transparent, updates live.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QFont

OVERLAY_STYLE = """
QWidget#overlayRoot {
    background: transparent;
}
QFrame#overlayCard {
    background: rgba(7, 11, 18, 220);
    border: 1.5px solid #1e3a5c;
    border-radius: 14px;
}
QLabel#ovTitle {
    font-size: 9px;
    color: #3d6080;
    letter-spacing: 2px;
    font-family: 'Consolas', monospace;
    font-weight: 600;
}
QLabel#ovLoad {
    font-family: 'Consolas', monospace;
    font-size: 18px;
    font-weight: 700;
}
QLabel#ovMeta {
    font-size: 10px;
    color: #5a7a9a;
    font-family: 'Consolas', monospace;
}
QLabel#ovApp {
    font-size: 10px;
    color: #00e5ff;
    font-family: 'Consolas', monospace;
}
QPushButton#ovClose {
    background: transparent;
    border: none;
    color: #2a4060;
    font-size: 12px;
    padding: 0;
    min-width: 18px;
    max-width: 18px;
    min-height: 18px;
    max-height: 18px;
    border-radius: 9px;
}
QPushButton#ovClose:hover {
    color: #ff5252;
    background: rgba(255,82,82,0.1);
}
QPushButton#ovMinimize {
    background: transparent;
    border: none;
    color: #2a4060;
    font-size: 12px;
    padding: 0;
    min-width: 18px;
    max-width: 18px;
    min-height: 18px;
    max-height: 18px;
    border-radius: 9px;
}
QPushButton#ovMinimize:hover {
    color: #00e5ff;
    background: rgba(0,229,255,0.08);
}
QPushButton#ovAnalyze {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00c8f0,stop:1 #6c3fff);
    border: none;
    border-radius: 6px;
    color: #000;
    font-size: 10px;
    font-weight: 700;
    padding: 5px 10px;
}
QPushButton#ovAnalyze:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33d6f5,stop:1 #8560ff);
}
"""


class CogniLoadOverlay(QWidget):
    """
    A draggable, always-on-top floating overlay showing real-time
    cognitive load. Appears on top of any app the user is working in.
    """
    analyze_requested = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)  # don't steal focus!
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._drag_pos = None
        self._collapsed = False
        self._current_level = "IDLE"
        self._current_app = "—"

        self._build()
        self._position_top_right()

        # Pulse animation timer
        self._pulse = True
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._pulse_timer.start(1000)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("overlayCard")
        self._card.setFixedWidth(230)
        self._card.setStyleSheet(OVERLAY_STYLE)
        root.addWidget(self._card)

        layout = QVBoxLayout(self._card)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(6)

        # ── Top bar: title + buttons ────────────────────────────────────────
        top = QHBoxLayout(); top.setSpacing(4)
        self._title_lbl = QLabel("🧠 COGNILOAD")
        self._title_lbl.setObjectName("ovTitle")
        self._title_lbl.setStyleSheet("font-size:9px; color:#3d6080; letter-spacing:2px; font-family:'Consolas'; font-weight:600;")

        self._dot_lbl = QLabel("●")
        self._dot_lbl.setStyleSheet("color:#00e676; font-size:9px;")

        self._min_btn = QPushButton("−"); self._min_btn.setObjectName("ovMinimize")
        self._min_btn.clicked.connect(self._toggle_collapse)
        self._close_btn = QPushButton("✕"); self._close_btn.setObjectName("ovClose")
        self._close_btn.clicked.connect(self._on_close)

        top.addWidget(self._dot_lbl)
        top.addWidget(self._title_lbl)
        top.addStretch()
        top.addWidget(self._min_btn)
        top.addWidget(self._close_btn)
        layout.addLayout(top)

        # ── Divider ──────────────────────────────────────────────────────────
        self._divider = QFrame(); self._divider.setFixedHeight(1)
        self._divider.setStyleSheet("background:#1a2840; border:none;")
        layout.addWidget(self._divider)

        # ── Body (collapsible) ────────────────────────────────────────────
        self._body = QWidget()
        body_l = QVBoxLayout(self._body)
        body_l.setContentsMargins(0, 4, 0, 0)
        body_l.setSpacing(6)

        # Load level display
        self._load_row = QHBoxLayout(); self._load_row.setSpacing(8)
        self._load_icon = QLabel("🧠"); self._load_icon.setStyleSheet("font-size:20px;")
        self._load_lbl = QLabel("IDLE")
        self._load_lbl.setObjectName("ovLoad")
        self._load_lbl.setStyleSheet("font-family:'Consolas'; font-size:18px; font-weight:700; color:#3d6080;")
        self._conf_lbl = QLabel(""); self._conf_lbl.setStyleSheet("color:#5a7a9a; font-size:10px; font-family:'Consolas';")
        lv = QVBoxLayout(); lv.setSpacing(1)
        lv.addWidget(self._load_lbl); lv.addWidget(self._conf_lbl)
        self._load_row.addWidget(self._load_icon)
        self._load_row.addLayout(lv)
        self._load_row.addStretch()
        body_l.addLayout(self._load_row)

        # Stats row
        self._stats_row = QHBoxLayout(); self._stats_row.setSpacing(0)

        def stat_cell(label):
            w = QWidget()
            v = QVBoxLayout(w); v.setContentsMargins(0, 0, 8, 0); v.setSpacing(1)
            val = QLabel("0"); val.setStyleSheet("font-family:'Consolas'; font-size:13px; font-weight:700; color:#00e5ff;")
            lbl = QLabel(label); lbl.setStyleSheet("font-size:9px; color:#3d6080; letter-spacing:0.5px;")
            v.addWidget(val); v.addWidget(lbl)
            return w, val

        self._wpm_cell, self._wpm_val = stat_cell("WPM")
        self._ks_cell, self._ks_val = stat_cell("KEYS")
        self._bs_cell, self._bs_val = stat_cell("BKSPC")

        self._stats_row.addWidget(self._wpm_cell)
        self._stats_row.addWidget(self._ks_cell)
        self._stats_row.addWidget(self._bs_cell)
        self._stats_row.addStretch()
        body_l.addLayout(self._stats_row)

        # Active app
        self._app_lbl = QLabel("App: —")
        self._app_lbl.setObjectName("ovApp")
        self._app_lbl.setStyleSheet("font-size:10px; color:#00e5ff; font-family:'Consolas';")
        body_l.addWidget(self._app_lbl)

        # Analyze button
        self._an_btn = QPushButton("⚡ Analyze Now")
        self._an_btn.setObjectName("ovAnalyze")
        self._an_btn.clicked.connect(self.analyze_requested.emit)
        body_l.addWidget(self._an_btn)

        layout.addWidget(self._body)

    def _position_top_right(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 260, 60)

    def update_stats(self, stats: dict, active_app: str = "—"):
        """Called every second with live stats"""
        self._wpm_val.setText(str(stats.get('wpm', 0)))
        self._ks_val.setText(str(stats.get('keystrokes', 0)))
        self._bs_val.setText(str(stats.get('backspaces', 0)))
        name = active_app[:22] + "…" if len(active_app) > 22 else active_app
        self._app_lbl.setText(f"App: {name}")
        self._current_app = active_app

    def update_result(self, level: str, confidence: float):
        """Called when analysis result arrives"""
        self._current_level = level
        if level == 'High':
            self._load_lbl.setText("HIGH LOAD")
            self._load_lbl.setStyleSheet("font-family:'Consolas'; font-size:16px; font-weight:700; color:#ff5252;")
            self._load_icon.setText("⚠️")
            self._card.setStyleSheet(OVERLAY_STYLE + "QFrame#overlayCard { border-color: #ff5252; }")
        elif level == 'Low':
            self._load_lbl.setText("LOW LOAD")
            self._load_lbl.setStyleSheet("font-family:'Consolas'; font-size:16px; font-weight:700; color:#00e676;")
            self._load_icon.setText("✅")
            self._card.setStyleSheet(OVERLAY_STYLE + "QFrame#overlayCard { border-color: #00e676; }")
        self._conf_lbl.setText(f"{confidence:.0f}% confident")

    def _tick_pulse(self):
        """Pulse the live dot"""
        self._pulse = not self._pulse
        color = "#00e676" if self._pulse else "#1a3a1a"
        self._dot_lbl.setStyleSheet(f"color:{color}; font-size:9px;")

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)
        self._divider.setVisible(not self._collapsed)
        self._min_btn.setText("+" if self._collapsed else "−")
        self._card.adjustSize()
        self.adjustSize()

    def _on_close(self):
        self.hide()
        self.closed.emit()

    # ── Drag support ─────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
