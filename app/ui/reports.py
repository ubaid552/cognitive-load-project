"""
CogniLoad - Reports Panel
Full analysis history with predictions and advice
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt
from app.auth.db import get_user_reports
import json


PRED_COLORS = {
    'High': '#ff5252',
    'Low': '#00e676',
}

CARD_STYLE = """
QFrame#reportCard {
    background: #0d1424;
    border: 1px solid #1e3050;
    border-radius: 10px;
    margin: 4px 0;
}
QFrame#reportCard:hover { border-color: #2a4a70; }
QLabel#reportLevel { font-family:'Consolas'; font-size:13px; font-weight:bold; }
QLabel#reportTime { color:#5a7a9a; font-size:11px; font-family:'Consolas'; }
QLabel#predTitle { color:#00e5ff; font-size:12px; font-weight:bold; }
QLabel#predDesc { color:#8090a0; font-size:11px; }
QLabel#adviceItem { color:#a0b4c8; font-size:11px; }
QLabel#sectionHdr { color:#5a7a9a; font-size:10px; letter-spacing:2px; }
"""


class PredictionCard(QFrame):
    def __init__(self, pred: dict, rank: int, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:#111c2e; border:1px solid #1a2840; border-radius:8px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        # Header row
        hdr = QHBoxLayout()
        rank_lbl = QLabel(f"#{rank}")
        rank_lbl.setStyleSheet("color:#00e5ff; font-family:'Consolas'; font-size:12px; font-weight:bold;")
        title_lbl = QLabel(pred['title'])
        title_lbl.setObjectName("predTitle")
        title_lbl.setWordWrap(True)
        score_lbl = QLabel(f"{pred['score']:.0f}%")
        score_lbl.setStyleSheet("color:#7c4dff; font-family:'Consolas'; font-size:11px;")
        hdr.addWidget(rank_lbl)
        hdr.addSpacing(8)
        hdr.addWidget(title_lbl, 1)
        hdr.addWidget(score_lbl)
        layout.addLayout(hdr)

        # Description
        desc = QLabel(pred['description'])
        desc.setObjectName("predDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Advice
        advice_hdr = QLabel("ADVICE:")
        advice_hdr.setStyleSheet("color:#5a7a9a; font-size:10px; letter-spacing:1px; margin-top:4px;")
        layout.addWidget(advice_hdr)
        for adv in pred['advice'][:3]:
            adv_lbl = QLabel(f"  💡 {adv}")
            adv_lbl.setObjectName("adviceItem")
            adv_lbl.setWordWrap(True)
            layout.addWidget(adv_lbl)


class ReportDetailView(QWidget):
    """Full detail view for a single report"""
    def __init__(self, report: dict, predictions_live: list = None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(CARD_STYLE + "QWidget{background:#080c14;color:#e8f0fe;font-family:'Segoe UI';}")

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        level = report.get('load_level', 'Unknown')
        color = PRED_COLORS.get(level, '#e8f0fe')

        # Title
        t = QLabel(f"{'⚠️  HIGH COGNITIVE LOAD' if level=='High' else '✅  LOW COGNITIVE LOAD'}")
        t.setStyleSheet(f"font-family:'Consolas'; font-size:22px; font-weight:bold; color:{color};")
        layout.addWidget(t)

        ts = QLabel(report.get('timestamp', '')[:19].replace('T', '  '))
        ts.setStyleSheet("color:#5a7a9a; font-size:12px; font-family:'Consolas';")
        layout.addWidget(ts)

        # Metrics row
        m_frame = QFrame()
        m_frame.setObjectName("reportCard")
        m_layout = QHBoxLayout(m_frame)
        m_layout.setContentsMargins(16, 12, 16, 12)
        raw = {}
        try:
            raw = json.loads(report.get('raw_metrics', '{}'))
        except Exception:
            pass

        def metric_cell(icon, label, val):
            c = QWidget()
            cl = QVBoxLayout(c)
            cl.setContentsMargins(10, 0, 10, 0)
            cl.setSpacing(2)
            v = QLabel(str(val))
            v.setStyleSheet("font-family:'Consolas'; font-size:20px; font-weight:bold; color:#00e5ff;")
            l = QLabel(f"{icon} {label}")
            l.setStyleSheet("color:#5a7a9a; font-size:10px;")
            cl.addWidget(v)
            cl.addWidget(l)
            return c

        m_layout.addWidget(metric_cell("⌨", "Keystrokes", report.get('keystrokes', '—')))
        m_layout.addWidget(metric_cell("⌫", "Backspaces", report.get('backspaces', '—')))
        m_layout.addWidget(metric_cell("✍", "WPM", f"{report.get('wpm', 0):.1f}"))
        m_layout.addWidget(metric_cell("⏱", "Avg IKI ms", round(report.get('avg_iki_ms', 0))))
        m_layout.addWidget(metric_cell("💤", "Long Pauses", report.get('long_pauses', '—')))
        m_layout.addWidget(metric_cell("🎯", "Confidence", f"{report.get('confidence', 0):.1f}%"))
        layout.addWidget(m_frame)

        # Active app
        if report.get('active_app'):
            app_lbl = QLabel(f"🖥  Active Application: {report['active_app']}")
            app_lbl.setStyleSheet("color:#7c4dff; font-size:12px; font-family:'Consolas';")
            layout.addWidget(app_lbl)

        # Predictions
        preds_hdr = QLabel("POSSIBLE CAUSES — PREDICTIONS")
        preds_hdr.setObjectName("sectionHdr")
        preds_hdr.setStyleSheet("color:#5a7a9a; font-size:11px; letter-spacing:2px; margin-top:8px;")
        layout.addWidget(preds_hdr)

        if predictions_live:
            for i, pred in enumerate(predictions_live, 1):
                layout.addWidget(PredictionCard(pred, i))
        else:
            # Parse from DB text
            preds_text = report.get('predictions', 'No predictions available.')
            advice_text = report.get('advice', '')
            preds_box = QTextEdit()
            preds_box.setReadOnly(True)
            preds_box.setPlainText(preds_text)
            preds_box.setStyleSheet("background:#0d1424; border:1px solid #1e3050; border-radius:8px; color:#a0b4c8; font-size:12px; padding:10px;")
            preds_box.setFixedHeight(180)
            layout.addWidget(preds_box)

            if advice_text:
                adv_hdr = QLabel("ADVICE & SUGGESTIONS")
                adv_hdr.setStyleSheet("color:#5a7a9a; font-size:11px; letter-spacing:2px; margin-top:8px;")
                layout.addWidget(adv_hdr)
                advice_box = QTextEdit()
                advice_box.setReadOnly(True)
                advice_box.setPlainText(advice_text)
                advice_box.setStyleSheet("background:#0d1424; border:1px solid #1e3050; border-radius:8px; color:#a0b4c8; font-size:12px; padding:10px;")
                advice_box.setFixedHeight(200)
                layout.addWidget(advice_box)

        layout.addStretch()


class ReportsPanel(QWidget):
    def __init__(self, user: dict, parent=None):
        super().__init__(parent)
        self.user = user
        self.setStyleSheet(CARD_STYLE + "QWidget{background:#080c14; color:#e8f0fe; font-family:'Segoe UI';}")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(16)

        # Left: report list
        left = QWidget()
        left.setMaximumWidth(360)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        hdr_row = QHBoxLayout()
        hdr_lbl = QLabel("ANALYSIS HISTORY")
        hdr_lbl.setStyleSheet("color:#5a7a9a; font-size:11px; letter-spacing:2px;")
        refresh_btn = QPushButton("↺ Refresh")
        refresh_btn.setObjectName("ghostBtn")
        refresh_btn.setFixedWidth(90)
        refresh_btn.clicked.connect(self.refresh)
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()
        hdr_row.addWidget(refresh_btn)
        left_layout.addLayout(hdr_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_widget)
        left_layout.addWidget(scroll)
        self._layout.addWidget(left)

        # Right: detail view placeholder
        self._detail_container = QWidget()
        self._detail_container.setStyleSheet("background:#0d1424; border:1px solid #1e3050; border-radius:12px;")
        detail_ph_layout = QVBoxLayout(self._detail_container)
        ph = QLabel("Select a report from the list to view details")
        ph.setStyleSheet("color:#5a7a9a; font-size:13px;")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail_ph_layout.addWidget(ph)
        self._layout.addWidget(self._detail_container, 1)

        self.refresh()

    def refresh(self):
        reports = get_user_reports(self.user['id'], limit=50)
        # Clear list
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for r in reports:
            self._list_layout.insertWidget(self._list_layout.count() - 1, self._make_report_row(r))

    def _make_report_row(self, r: dict) -> QFrame:
        f = QFrame()
        f.setObjectName("reportCard")
        f.setStyleSheet("QFrame#reportCard{background:#0d1424;border:1px solid #1e3050;border-radius:8px;} QFrame#reportCard:hover{border-color:#2a4a70;}")
        f.setCursor(Qt.CursorShape.PointingHandCursor)
        hl = QHBoxLayout(f)
        hl.setContentsMargins(14, 10, 14, 10)
        level = r.get('load_level', '—')
        color = PRED_COLORS.get(level, '#e8f0fe')

        level_lbl = QLabel(f"{'⚠' if level=='High' else '✓'}  {level.upper()}")
        level_lbl.setStyleSheet(f"color:{color}; font-family:'Consolas'; font-size:12px; font-weight:bold;")

        ts = r.get('timestamp', '')[:16].replace('T', ' ')
        ts_lbl = QLabel(ts)
        ts_lbl.setStyleSheet("color:#5a7a9a; font-size:11px; font-family:'Consolas';")

        conf_lbl = QLabel(f"{r.get('confidence', 0):.0f}%")
        conf_lbl.setStyleSheet("color:#7c4dff; font-family:'Consolas'; font-size:12px;")

        hl.addWidget(level_lbl)
        hl.addStretch()
        hl.addWidget(ts_lbl)
        hl.addSpacing(10)
        hl.addWidget(conf_lbl)

        def on_click(event, report=r):
            self._show_detail(report)
        f.mousePressEvent = on_click
        return f

    def _show_detail(self, report: dict):
        # Remove old detail
        old = self._layout.takeAt(1)
        if old and old.widget():
            old.widget().deleteLater()

        detail = ReportDetailView(report)
        detail.setStyleSheet("background:#0d1424; border:1px solid #1e3050; border-radius:12px;")
        self._layout.addWidget(detail, 1)

    def show_live_result(self, report: dict, predictions: list):
        """Called with live result to show full detail immediately"""
        old = self._layout.takeAt(1)
        if old and old.widget():
            old.widget().deleteLater()
        detail = ReportDetailView(report, predictions_live=predictions)
        detail.setStyleSheet("background:#0d1424; border:1px solid #1e3050; border-radius:12px;")
        self._layout.addWidget(detail, 1)
        self.refresh()
