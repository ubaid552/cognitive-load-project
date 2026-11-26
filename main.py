"""
CogniLoad — Cognitive Load Analyzer
Main Entry Point

LGU · Department of Software Engineering · AI Project
Based on: Lin et al. (2013) - Automatic cognitive load evaluation using writing features
"""
import sys
import os

# ── Ensure cogniload_app/ root is on the path ──────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _check_model_files():
    """Warn if ML model files are missing (app still works with heuristic fallback)"""
    missing = []
    for fname in ("cognitive_load_model.pkl", "label_encoder.pkl"):
        if not os.path.exists(os.path.join(ROOT, fname)):
            missing.append(fname)
    if missing:
        print(f"[CogniLoad] Warning: missing model files: {missing}")
        print("[CogniLoad] The app will run using the built-in heuristic predictor.")


def main():
    _check_model_files()

    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt

    app = QApplication(sys.argv)
    app.setApplicationName("CogniLoad")
    app.setApplicationDisplayName("CogniLoad — Cognitive Load Analyzer")
    app.setOrganizationName("Lahore Garrison University")
    app.setOrganizationDomain("lgu.edu.pk")
    # Keep alive in system tray when all windows are closed
    app.setQuitOnLastWindowClosed(False)

    # ── Import after QApplication is created ─────────────────────────────────
    try:
        from app.auth.auth_manager import auth
        from app.ui.login_window import LoginWindow
        from app.ui.main_window import MainWindow
    except Exception as e:
        QMessageBox.critical(None, "CogniLoad — Startup Error",
            f"Failed to load application modules:\n\n{e}\n\n"
            "Please ensure all dependencies are installed:\n"
            "  pip install -r requirements.txt")
        sys.exit(1)

    # Keep strong references to prevent garbage collection
    _windows = []

    def on_login(user: dict):
        """Called when user successfully logs in."""
        login_win.hide()
        try:
            main_win = MainWindow(user, auth)
            main_win.show()
            _windows.append(main_win)
        except Exception as e:
            QMessageBox.critical(None, "CogniLoad — Error",
                f"Failed to open dashboard:\n\n{e}")
            login_win.show()

    login_win = LoginWindow(auth)
    login_win.login_success.connect(on_login)
    _windows.append(login_win)
    login_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
