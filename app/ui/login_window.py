"""
CogniLoad - Login Window (v3)
Big premium input fields, 3-page flow, no dropdowns
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QStackedWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

S = """
QWidget {
    background: #07090f;
    color: #e0eeff;
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
}
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QScrollBar:vertical { background: #0b1120; width: 5px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #2a4060; border-radius: 3px; }

/* ── Input Fields — bright, clearly readable ── */
QLineEdit {
    background: #0e1c2e;
    border: 2px solid #1e3a5c;
    border-radius: 12px;
    padding: 16px 20px;
    color: #ffffff;
    font-size: 14px;
    font-family: 'Segoe UI', Arial;
    min-height: 26px;
    selection-background-color: #00e5ff;
    selection-color: #000000;
}
QLineEdit:focus {
    border: 2px solid #00e5ff;
    background: #102030;
    color: #ffffff;
}
QLineEdit:hover:!focus {
    border-color: #2a5080;
    background: #0f1e30;
}

/* ── Buttons — all text must be clearly readable ── */
QPushButton {
    border-radius: 12px;
    font-size: 14px;
    font-weight: 700;
    padding: 15px 24px;
    border: none;
    min-height: 24px;
    color: #ffffff;
}

/* Sign In — gradient, black text (bright bg so black is fine) */
QPushButton#btnLogin {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #00c8f0, stop:0.5 #3a70ff, stop:1 #6c3fff);
    color: #000000;
    font-size: 15px;
    font-weight: 800;
}
QPushButton#btnLogin:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #33d6f5, stop:0.5 #5080ff, stop:1 #8060ff);
    color: #000000;
}
QPushButton#btnLogin:pressed {
    padding-top: 17px;
    padding-bottom: 13px;
}

/* Single User — green border, bright green text */
QPushButton#btnSingle {
    background: #071e10;
    border: 2px solid #00d464;
    color: #00ff7a;
    font-size: 14px;
    font-weight: 700;
}
QPushButton#btnSingle:hover {
    background: #0d2c1a;
    border-color: #33eb91;
    color: #33ff8a;
}

/* Supervisor — purple border, bright purple text */
QPushButton#btnSuper {
    background: #0e0625;
    border: 2px solid #7c4dff;
    color: #c0a0ff;
    font-size: 14px;
    font-weight: 700;
}
QPushButton#btnSuper:hover {
    background: #16083a;
    border-color: #9d73ff;
    color: #d0bcff;
}

/* Ghost — visible grey text on transparent */
QPushButton#btnGhost {
    background: transparent;
    border: 2px solid #2a4060;
    color: #7aaccc;
    font-size: 13px;
    padding: 12px 22px;
    font-weight: 600;
}
QPushButton#btnGhost:hover {
    border-color: #00e5ff;
    color: #00e5ff;
    background: rgba(0, 229, 255, 0.05);
}

/* ── Cards ── */
QFrame#card   { background: #0b1522; border: 1px solid #1a3050; border-radius: 20px; }
QFrame#cGreen { background: #060f09; border: 2px solid #00d464; border-radius: 18px; }
QFrame#cPurp  { background: #080518; border: 2px solid #7c4dff; border-radius: 18px; }

/* ── Labels ── */
QLabel#lTitle { font-size: 28px; font-weight: 700; color: #e8f4ff; }
QLabel#lSub   { font-size: 12px; color: #3a6080; letter-spacing: 2px; }
QLabel#lField { font-size: 11px; color: #6a9abf; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 2px; }
QLabel#lErr   { color: #ff5252; font-size: 12px; min-height: 16px; font-weight: 600; }
QLabel#lOk    { color: #00e676; font-size: 12px; min-height: 16px; font-weight: 600; }
QLabel#lNote  { color: #5a7a9a; font-size: 11px; }
"""



def _field(label, placeholder, pwd=False, icon=""):
    """Returns (wrapper QWidget, QLineEdit) — big, premium style"""
    w = QWidget()
    v = QVBoxLayout(w); v.setContentsMargins(0,0,0,0); v.setSpacing(6)
    lbl = QLabel(f"  {icon}  {label}" if icon else f"  {label}")
    lbl.setObjectName("lField")
    ed = QLineEdit()
    ed.setPlaceholderText(placeholder)
    ed.setMinimumHeight(54)
    if pwd:
        ed.setEchoMode(QLineEdit.EchoMode.Password)
    v.addWidget(lbl); v.addWidget(ed)
    return w, ed


def _hr(color="#142030"):
    f = QFrame(); f.setFixedHeight(1)
    f.setStyleSheet(f"background:{color}; border:none; margin:4px 0;")
    return f


class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self, auth):
        super().__init__()
        self.auth = auth
        self.setWindowTitle("CogniLoad — Cognitive Load Analyzer")
        self.setFixedSize(500, 680)
        self.setStyleSheet(S)

        self._stack = QStackedWidget(self)
        self._stack.setGeometry(0, 0, 500, 680)
        self._stack.addWidget(self._p_login())       # 0
        self._stack.addWidget(self._p_choose())      # 1
        self._stack.addWidget(self._p_single())      # 2
        self._stack.addWidget(self._p_supervisor())  # 3
        self._stack.setCurrentIndex(0)
        self._center()

    def _center(self):
        from PyQt6.QtWidgets import QApplication
        s = QApplication.primaryScreen().geometry()
        self.move((s.width()-500)//2, (s.height()-680)//2)

    def _logo(self, big=True):
        w = QWidget()
        v = QVBoxLayout(w); v.setSpacing(4); v.setContentsMargins(0,0,0,0)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brain = QLabel("🧠")
        brain.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brain.setStyleSheet(f"font-size:{'52' if big else '36'}px;")
        title = QLabel("COGNILOAD")
        fs = "26px" if big else "18px"
        title.setStyleSheet(
            f"font-size:{fs}; font-weight:800; font-family:'Consolas',monospace;"
            f" color:#00e5ff; letter-spacing:4px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(brain); v.addWidget(title)
        if big:
            sub = QLabel("COGNITIVE LOAD ANALYZER")
            sub.setObjectName("lSub"); sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(sub)
        return w

    # ── PAGE 0: LOGIN ────────────────────────────────────────────────────────
    def _p_login(self):
        page = QWidget()
        root = QVBoxLayout(page); root.setContentsMargins(40,30,40,30); root.setSpacing(0)

        root.addWidget(self._logo(True))
        root.addSpacing(28)

        card = QFrame(); card.setObjectName("card")
        cl = QVBoxLayout(card); cl.setContentsMargins(32,30,32,30); cl.setSpacing(0)

        hd = QLabel("Welcome Back"); hd.setObjectName("lTitle")
        st = QLabel("Sign in to continue monitoring")
        st.setStyleSheet("color:#2a4060; font-size:13px; margin-top:4px;")

        uw, self._lu = _field("USERNAME", "Enter your username", icon="👤")
        pw, self._lp = _field("PASSWORD", "Enter your password", pwd=True, icon="🔒")
        self._lp.returnPressed.connect(self._do_login)

        self._le = QLabel(""); self._le.setObjectName("lErr"); self._le.setWordWrap(True)

        sign_btn = QPushButton("Sign In  →")
        sign_btn.setObjectName("btnLogin")
        sign_btn.setMinimumHeight(56)
        sign_btn.clicked.connect(self._do_login)

        new_btn = QPushButton("Create a New Account")
        new_btn.setObjectName("btnGhost")
        new_btn.setMinimumHeight(50)
        new_btn.clicked.connect(lambda: self._stack.setCurrentIndex(1))

        cl.addWidget(hd); cl.addWidget(st)
        cl.addSpacing(26)
        cl.addWidget(uw); cl.addSpacing(14)
        cl.addWidget(pw); cl.addSpacing(8)
        cl.addWidget(self._le); cl.addSpacing(14)
        cl.addWidget(sign_btn); cl.addSpacing(14)
        cl.addWidget(_hr()); cl.addSpacing(14)
        cl.addWidget(new_btn)

        root.addWidget(card); root.addStretch()
        foot = QLabel("LGU · SE · AI Project  ·  Based on Lin et al. (2013)")
        foot.setStyleSheet("color:#0f2030; font-size:10px; letter-spacing:1px;")
        foot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(foot)
        return page

    # ── PAGE 1: CHOOSE ───────────────────────────────────────────────────────
    def _p_choose(self):
        page = QWidget()
        root = QVBoxLayout(page); root.setContentsMargins(40,30,40,30); root.setSpacing(0)
        root.addWidget(self._logo(False))
        root.addSpacing(10)

        hd = QLabel("Choose Account Type"); hd.setObjectName("lTitle")
        hd.setStyleSheet("font-size:22px; font-weight:700; color:#d4e6ff;")
        hd.setAlignment(Qt.AlignmentFlag.AlignCenter)
        st = QLabel("Pick the plan that suits your needs")
        st.setStyleSheet("color:#2a4060; font-size:12px; margin-top:3px;")
        st.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(hd); root.addWidget(st); root.addSpacing(24)

        # Single card
        sc = QFrame(); sc.setObjectName("cGreen")
        sl = QVBoxLayout(sc); sl.setContentsMargins(28,22,28,22); sl.setSpacing(10)
        ic1 = QLabel("👤"); ic1.setStyleSheet("font-size:30px;")
        h1 = QLabel("Personal  /  Single User")
        h1.setStyleSheet("font-size:17px; font-weight:700; color:#00e676;")
        d1 = QLabel("For individual use.\nMonitor your own cognitive load across all apps.\nFull access to your personal reports & history.")
        d1.setStyleSheet("color:#3a7a4a; font-size:12px; line-height:1.6;"); d1.setWordWrap(True)
        b1 = QPushButton("  Get Started as Single User  →"); b1.setObjectName("btnSingle")
        b1.setMinimumHeight(52); b1.clicked.connect(lambda: self._stack.setCurrentIndex(2))
        sl.addWidget(ic1); sl.addWidget(h1); sl.addWidget(d1); sl.addSpacing(6); sl.addWidget(b1)
        root.addWidget(sc); root.addSpacing(16)

        # Supervisor card
        vc = QFrame(); vc.setObjectName("cPurp")
        vl = QVBoxLayout(vc); vl.setContentsMargins(28,22,28,22); vl.setSpacing(10)
        ic2 = QLabel("👥"); ic2.setStyleSheet("font-size:30px;")
        h2 = QLabel("Supervisor  /  Team Manager")
        h2.setStyleSheet("font-size:17px; font-weight:700; color:#b090ff;")
        d2 = QLabel("For companies & teams.\nAdd employees, control all passwords,\nview entire team's cognitive load reports.")
        d2.setStyleSheet("color:#5a4a9a; font-size:12px; line-height:1.6;"); d2.setWordWrap(True)
        b2 = QPushButton("  Create Supervisor Account  →"); b2.setObjectName("btnSuper")
        b2.setMinimumHeight(52); b2.clicked.connect(lambda: self._stack.setCurrentIndex(3))
        vl.addWidget(ic2); vl.addWidget(h2); vl.addWidget(d2); vl.addSpacing(6); vl.addWidget(b2)
        root.addWidget(vc); root.addSpacing(20)

        bk = QPushButton("← Back to Login"); bk.setObjectName("btnGhost"); bk.setMinimumHeight(46)
        bk.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        root.addWidget(bk); root.addStretch()
        return page

    # ── PAGE 2: SINGLE USER ──────────────────────────────────────────────────
    def _p_single(self):
        page = QWidget()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer = QVBoxLayout(page); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

        inner = QWidget(); scroll.setWidget(inner)
        root = QVBoxLayout(inner); root.setContentsMargins(40,30,40,30); root.setSpacing(0)

        # Header
        hr_row = QHBoxLayout(); hr_row.setSpacing(14)
        ico = QLabel("👤"); ico.setStyleSheet("font-size:34px;")
        hv = QVBoxLayout(); hv.setSpacing(3)
        hv.addWidget(QLabel("Personal Account").__class__(
            "Personal Account",
            styleSheet="font-size:22px; font-weight:700; color:#d4e6ff;"
        ))
        hv.addWidget(QLabel("Single User Registration").__class__(
            "Single User Registration",
            styleSheet="font-size:11px; color:#00e676; letter-spacing:1.5px;"
        ))
        hr_row.addWidget(ico); hr_row.addLayout(hv); hr_row.addStretch()
        root.addLayout(hr_row); root.addSpacing(20)

        card = QFrame(); card.setObjectName("card")
        cl = QVBoxLayout(card); cl.setContentsMargins(32,28,32,28); cl.setSpacing(14)

        nw, self._sn = _field("FULL NAME", "Your full name", icon="✏")
        ew, self._se = _field("EMAIL  (optional)", "your@email.com", icon="✉")
        uw, self._su = _field("USERNAME", "Choose a unique username", icon="👤")
        pw, self._sp = _field("PASSWORD", "Minimum 6 characters", pwd=True, icon="🔒")
        p2w, self._sp2 = _field("CONFIRM PASSWORD", "Repeat your password", pwd=True, icon="🔒")
        self._sp2.returnPressed.connect(self._do_single)

        self._se_err = QLabel(""); self._se_err.setObjectName("lErr"); self._se_err.setWordWrap(True)
        self._se_ok  = QLabel(""); self._se_ok.setObjectName("lOk");  self._se_ok.setWordWrap(True)

        btn = QPushButton("  ✅  Create Personal Account")
        btn.setObjectName("btnSingle"); btn.setMinimumHeight(56)
        btn.clicked.connect(self._do_single)

        for w in [nw, ew, _hr("#0a2015"), uw, pw, p2w]:
            cl.addWidget(w)
        cl.addWidget(self._se_err); cl.addWidget(self._se_ok)
        cl.addSpacing(6); cl.addWidget(btn)

        root.addWidget(card); root.addSpacing(14)
        bk = QPushButton("← Choose Different Account Type"); bk.setObjectName("btnGhost"); bk.setMinimumHeight(46)
        bk.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        root.addWidget(bk); root.addStretch()
        return page

    # ── PAGE 3: SUPERVISOR ───────────────────────────────────────────────────
    def _p_supervisor(self):
        page = QWidget()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer = QVBoxLayout(page); outer.setContentsMargins(0,0,0,0); outer.addWidget(scroll)

        inner = QWidget(); scroll.setWidget(inner)
        root = QVBoxLayout(inner); root.setContentsMargins(40,30,40,30); root.setSpacing(0)

        hr_row = QHBoxLayout(); hr_row.setSpacing(14)
        ico = QLabel("👥"); ico.setStyleSheet("font-size:34px;")
        hv = QVBoxLayout(); hv.setSpacing(3)
        t1 = QLabel("Supervisor Account"); t1.setStyleSheet("font-size:22px; font-weight:700; color:#d4e6ff;")
        t2 = QLabel("Team / Company Registration"); t2.setStyleSheet("font-size:11px; color:#b090ff; letter-spacing:1.5px;")
        hv.addWidget(t1); hv.addWidget(t2)
        hr_row.addWidget(ico); hr_row.addLayout(hv); hr_row.addStretch()
        root.addLayout(hr_row); root.addSpacing(20)

        card = QFrame(); card.setObjectName("card")
        cl = QVBoxLayout(card); cl.setContentsMargins(32,28,32,28); cl.setSpacing(14)

        nw, self._vn  = _field("SUPERVISOR FULL NAME", "Your full name", icon="✏")
        ow, self._vo  = _field("ORGANIZATION  (optional)", "Company or team name", icon="🏢")
        ew, self._ve  = _field("EMAIL  (optional)", "supervisor@company.com", icon="✉")
        sep = QLabel("LOGIN CREDENTIALS"); sep.setObjectName("lField")
        sep.setStyleSheet("font-size:10px; color:#2a4060; letter-spacing:2px; font-weight:700; margin-top:6px;")
        uw, self._vu  = _field("SUPERVISOR USERNAME", "Choose your admin username", icon="👤")
        pw, self._vp  = _field("PASSWORD", "Minimum 6 characters", pwd=True, icon="🔒")
        p2w, self._vp2 = _field("CONFIRM PASSWORD", "Repeat your password", pwd=True, icon="🔒")
        self._vp2.returnPressed.connect(self._do_supervisor)

        note = QLabel(
            "ℹ  As supervisor you can:\n"
            "  • Add unlimited team members\n"
            "  • Set and reset their passwords\n"
            "  • Employees cannot change their own passwords\n"
            "  • They can log in from any PC with their credentials"
        )
        note.setStyleSheet(
            "background:#0d0820; border:1.5px solid #1e1040; border-radius:10px;"
            " padding:12px 14px; color:#5a4a9a; font-size:11px; line-height:1.6;"
        )
        note.setWordWrap(True)

        self._ve_err = QLabel(""); self._ve_err.setObjectName("lErr"); self._ve_err.setWordWrap(True)
        self._ve_ok  = QLabel(""); self._ve_ok.setObjectName("lOk");  self._ve_ok.setWordWrap(True)

        btn = QPushButton("  ✅  Create Supervisor Account")
        btn.setObjectName("btnSuper"); btn.setMinimumHeight(56)
        btn.clicked.connect(self._do_supervisor)

        for w in [nw, ow, ew, _hr("#0a0520"), sep, uw, pw, p2w, note]:
            cl.addWidget(w)
        cl.addWidget(self._ve_err); cl.addWidget(self._ve_ok)
        cl.addSpacing(6); cl.addWidget(btn)

        root.addWidget(card); root.addSpacing(14)
        bk = QPushButton("← Choose Different Account Type"); bk.setObjectName("btnGhost"); bk.setMinimumHeight(46)
        bk.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        root.addWidget(bk); root.addStretch()
        return page

    # ── ACTIONS ──────────────────────────────────────────────────────────────
    def _do_login(self):
        u = self._lu.text().strip(); p = self._lp.text()
        if not u or not p:
            self._le.setText("⚠  Please enter both username and password."); return
        self._le.setText("Signing in…")
        r = self.auth.login(u, p)
        if r['success']:
            self._le.setText(""); self.login_success.emit(r['user'])
        else:
            self._le.setText(f"⚠  {r['error']}")

    def _do_single(self):
        n=self._sn.text().strip(); e=self._se.text().strip()
        u=self._su.text().strip(); p=self._sp.text(); p2=self._sp2.text()
        if not u or not p:
            self._se_err.setText("⚠  Username and password are required."); return
        if p != p2:
            self._se_err.setText("⚠  Passwords do not match."); return
        if len(p) < 6:
            self._se_err.setText("⚠  Password must be at least 6 characters."); return
        r = self.auth.register_single_user(u, p, n, e)
        if r['success']:
            self._se_ok.setText("✅  Account created! Logging you in…")
            QTimer.singleShot(800, lambda: self._auto_login(u, p))
        else:
            self._se_err.setText(f"⚠  {r['error']}")

    def _do_supervisor(self):
        n=self._vn.text().strip(); o=self._vo.text().strip()
        e=self._ve.text().strip()
        u=self._vu.text().strip(); p=self._vp.text(); p2=self._vp2.text()
        if not n or not u or not p:
            self._ve_err.setText("⚠  Name, username and password are required."); return
        if p != p2:
            self._ve_err.setText("⚠  Passwords do not match."); return
        if len(p) < 6:
            self._ve_err.setText("⚠  Password must be at least 6 characters."); return
        full = f"{n} ({o})" if o else n
        r = self.auth.register_supervisor(u, p, full, e)
        if r['success']:
            self._ve_ok.setText("✅  Supervisor account created! Logging you in…")
            QTimer.singleShot(800, lambda: self._auto_login(u, p))
        else:
            self._ve_err.setText(f"⚠  {r['error']}")

    def _auto_login(self, u, p):
        r = self.auth.login(u, p)
        if r['success']:
            self.login_success.emit(r['user'])
