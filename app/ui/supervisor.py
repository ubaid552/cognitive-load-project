"""
CogniLoad - Supervisor Panel
Manage team members, view all reports
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QLineEdit, QDialog, QDialogButtonBox,
    QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from app.auth.db import (
    get_supervisor_users, update_user_password,
    toggle_user_active, delete_sub_user, get_all_reports_for_supervisor
)


STYLE = """
QWidget { background:#080c14; color:#e8f0fe; font-family:'Segoe UI'; }
QFrame#userCard { background:#0d1424; border:1px solid #1e3050; border-radius:10px; }
QLabel#nameLabel { font-size:14px; font-weight:bold; color:#e8f0fe; }
QLabel#usernameLabel { font-family:'Consolas'; font-size:12px; color:#00e5ff; }
QLabel#statusActive { color:#00e676; font-size:11px; }
QLabel#statusInactive { color:#ff5252; font-size:11px; }
QPushButton#primaryBtn { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00e5ff,stop:1 #7c4dff);
    color:#000; border-radius:6px; font-weight:bold; padding:7px 14px; border:none; font-size:11px; }
QPushButton#ghostBtn { background:transparent; border:1px solid #1e3050; color:#5a7a9a;
    border-radius:6px; padding:7px 12px; font-size:11px; }
QPushButton#ghostBtn:hover { border-color:#00e5ff; color:#00e5ff; }
QPushButton#dangerBtn { background:#2a0a0a; border:1px solid #ff5252; color:#ff5252;
    border-radius:6px; padding:7px 12px; font-size:11px; }
QPushButton#dangerBtn:hover { background:#3a1010; }
QLineEdit { background:#111c2e; border:1.5px solid #1e3050; border-radius:6px;
    padding:8px 12px; color:#e8f0fe; font-size:12px; }
QLineEdit:focus { border-color:#00e5ff; }
QScrollArea { border:none; background:transparent; }
QScrollBar:vertical { background:#111c2e; width:5px; border-radius:3px; }
QScrollBar::handle:vertical { background:#1e3050; border-radius:3px; }
"""


class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Team Member")
        self.setFixedSize(380, 340)
        self.setStyleSheet(STYLE + "QDialog{background:#080c14;}")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Add New Team Member")
        title.setStyleSheet("font-size:16px; font-weight:bold; color:#e8f0fe; margin-bottom:8px;")
        layout.addWidget(title)

        def field(lbl_text, placeholder, pwd=False):
            w = QWidget()
            vl = QVBoxLayout(w); vl.setContentsMargins(0,0,0,0); vl.setSpacing(3)
            l = QLabel(lbl_text); l.setStyleSheet("color:#5a7a9a; font-size:10px; letter-spacing:1px;")
            e = QLineEdit(); e.setPlaceholderText(placeholder)
            if pwd: e.setEchoMode(QLineEdit.EchoMode.Password)
            vl.addWidget(l); vl.addWidget(e)
            return w, e

        self._name_w, self.name_edit = field("FULL NAME", "Employee full name")
        self._user_w, self.user_edit = field("USERNAME", "Choose a username")
        self._pass_w, self.pass_edit = field("PASSWORD", "Set their password", pwd=True)
        self._pass2_w, self.pass2_edit = field("CONFIRM PASSWORD", "Repeat password", pwd=True)

        self._error = QLabel("")
        self._error.setStyleSheet("color:#ff5252; font-size:11px;")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Add Member")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primaryBtn")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00e5ff,stop:1 #7c4dff); color:#000; border-radius:6px; font-weight:bold; padding:7px 14px; border:none;")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)

        layout.addWidget(self._name_w)
        layout.addWidget(self._user_w)
        layout.addWidget(self._pass_w)
        layout.addWidget(self._pass2_w)
        layout.addWidget(self._error)
        layout.addWidget(buttons)

    def _validate(self):
        if not self.user_edit.text().strip():
            self._error.setText("Username is required."); return
        if self.pass_edit.text() != self.pass2_edit.text():
            self._error.setText("Passwords don't match."); return
        if len(self.pass_edit.text()) < 6:
            self._error.setText("Password must be at least 6 characters."); return
        self.accept()

    def get_data(self) -> dict:
        return {
            'username': self.user_edit.text().strip(),
            'password': self.pass_edit.text(),
            'full_name': self.name_edit.text().strip(),
        }


class ChangePasswordDialog(QDialog):
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Change Password — {username}")
        self.setFixedSize(360, 240)
        self.setStyleSheet(STYLE + "QDialog{background:#080c14;}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel(f"Set New Password for @{username}")
        title.setStyleSheet("font-size:14px; font-weight:bold; color:#e8f0fe;")
        title.setWordWrap(True)
        layout.addWidget(title)

        def field(lbl, ph, pwd=True):
            w = QWidget(); vl = QVBoxLayout(w); vl.setContentsMargins(0,0,0,0); vl.setSpacing(3)
            l = QLabel(lbl); l.setStyleSheet("color:#5a7a9a; font-size:10px; letter-spacing:1px;")
            e = QLineEdit(); e.setPlaceholderText(ph)
            if pwd: e.setEchoMode(QLineEdit.EchoMode.Password)
            vl.addWidget(l); vl.addWidget(e); return w, e

        self._pw_w, self.pw_edit = field("NEW PASSWORD", "Enter new password")
        self._pw2_w, self.pw2_edit = field("CONFIRM", "Repeat new password")
        self._error = QLabel(""); self._error.setStyleSheet("color:#ff5252; font-size:11px;")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Update Password")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)

        layout.addWidget(self._pw_w); layout.addWidget(self._pw2_w)
        layout.addWidget(self._error); layout.addWidget(buttons)

    def _validate(self):
        if self.pw_edit.text() != self.pw2_edit.text():
            self._error.setText("Passwords don't match."); return
        if len(self.pw_edit.text()) < 6:
            self._error.setText("Password must be at least 6 characters."); return
        self.accept()

    def get_password(self) -> str:
        return self.pw_edit.text()


class UserCard(QFrame):
    def __init__(self, user: dict, supervisor_id: int, on_refresh, parent=None):
        super().__init__(parent)
        self.user = user
        self.supervisor_id = supervisor_id
        self.on_refresh = on_refresh
        self.setObjectName("userCard")
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Info
        info = QVBoxLayout()
        name_lbl = QLabel(self.user.get('full_name') or self.user['username'])
        name_lbl.setObjectName("nameLabel")
        user_lbl = QLabel(f"@{self.user['username']}")
        user_lbl.setObjectName("usernameLabel")
        is_active = bool(self.user.get('is_active', 1))
        status_lbl = QLabel("● Active" if is_active else "● Inactive")
        status_lbl.setObjectName("statusActive" if is_active else "statusInactive")
        created = self.user.get('created_at', '')[:10]
        date_lbl = QLabel(f"Added: {created}")
        date_lbl.setStyleSheet("color:#3a5070; font-size:10px;")
        info.addWidget(name_lbl); info.addWidget(user_lbl)
        info.addWidget(status_lbl); info.addWidget(date_lbl)
        layout.addLayout(info, 1)

        # Actions
        actions = QVBoxLayout()
        actions.setSpacing(6)

        pw_btn = QPushButton("🔑 Change Password")
        pw_btn.setObjectName("ghostBtn")
        pw_btn.clicked.connect(self._change_password)

        toggle_btn = QPushButton("🔴 Deactivate" if self.user.get('is_active') else "🟢 Activate")
        toggle_btn.setObjectName("ghostBtn")
        toggle_btn.clicked.connect(self._toggle_active)

        del_btn = QPushButton("🗑 Remove")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete_user)

        actions.addWidget(pw_btn); actions.addWidget(toggle_btn); actions.addWidget(del_btn)
        layout.addLayout(actions)

    def _change_password(self):
        dlg = ChangePasswordDialog(self.user['username'], self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_pw = dlg.get_password()
            ok = update_user_password(self.user['id'], new_pw, self.supervisor_id)
            if ok:
                QMessageBox.information(self, "Success", "Password updated successfully.")
            else:
                QMessageBox.warning(self, "Error", "Could not update password.")

    def _toggle_active(self):
        toggle_user_active(self.user['id'], self.supervisor_id)
        self.on_refresh()

    def _delete_user(self):
        reply = QMessageBox.question(self, "Remove User",
            f"Remove @{self.user['username']} from your team?\nThis will deactivate their account.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            delete_sub_user(self.user['id'], self.supervisor_id)
            self.on_refresh()


class SupervisorPanel(QWidget):
    def __init__(self, user: dict, auth_manager, parent=None):
        super().__init__(parent)
        self.user = user
        self.auth = auth_manager
        self.setStyleSheet(STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("👥  Team Management")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#e8f0fe;")
        add_btn = QPushButton("+ Add Team Member")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._add_user)
        hdr.addWidget(title); hdr.addStretch(); hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        # Summary bar
        self._summary_lbl = QLabel("")
        self._summary_lbl.setStyleSheet("color:#5a7a9a; font-size:12px;")
        layout.addWidget(self._summary_lbl)

        # Scroll area for user cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._users_widget = QWidget()
        self._users_layout = QVBoxLayout(self._users_widget)
        self._users_layout.setSpacing(8)
        self._users_layout.setContentsMargins(0, 0, 0, 0)
        self._users_layout.addStretch()
        scroll.setWidget(self._users_widget)
        layout.addWidget(scroll)

        self._refresh_users()

    def _refresh_users(self):
        users = get_supervisor_users(self.user['id'])
        # Clear
        while self._users_layout.count() > 1:
            item = self._users_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active = sum(1 for u in users if u.get('is_active', 1))
        self._summary_lbl.setText(f"Total: {len(users)} members  |  Active: {active}  |  Inactive: {len(users)-active}")

        if not users:
            ph = QLabel("No team members yet. Click '+ Add Team Member' to get started.")
            ph.setStyleSheet("color:#5a7a9a; font-size:13px;")
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._users_layout.insertWidget(0, ph)
        else:
            for u in users:
                card = UserCard(u, self.user['id'], self._refresh_users)
                self._users_layout.insertWidget(self._users_layout.count() - 1, card)

    def _add_user(self):
        dlg = AddUserDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            result = self.auth.add_sub_user(
                username=data['username'],
                password=data['password'],
                full_name=data['full_name']
            )
            if result['success']:
                QMessageBox.information(self, "Success",
                    f"✅ Team member @{data['username']} added successfully!\n\n"
                    f"They can now log in from any PC using:\n"
                    f"Username: {data['username']}\n"
                    f"Password: (the one you set)")
                self._refresh_users()
            else:
                QMessageBox.warning(self, "Error", result['error'])
