"""
CogniLoad - Database Layer
SQLite database for users, sessions, and reports
"""
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'cogniload.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize all database tables"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    c = conn.cursor()

    # Account types: 'single' or 'supervisor'
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            account_type TEXT NOT NULL DEFAULT 'single',
            supervisor_id INTEGER,
            email TEXT,
            full_name TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            is_active INTEGER DEFAULT 1,
            can_change_password INTEGER DEFAULT 1,
            FOREIGN KEY (supervisor_id) REFERENCES accounts(id)
        )
    ''')

    # Keystroke sessions
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            total_keystrokes INTEGER DEFAULT 0,
            total_backspaces INTEGER DEFAULT 0,
            avg_wpm REAL DEFAULT 0,
            avg_iki_ms REAL DEFAULT 0,
            avg_load_level TEXT,
            active_app TEXT,
            FOREIGN KEY (user_id) REFERENCES accounts(id)
        )
    ''')

    # Individual analysis reports
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id INTEGER,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            load_level TEXT NOT NULL,
            confidence REAL,
            keystrokes INTEGER,
            backspaces INTEGER,
            wpm REAL,
            avg_iki_ms REAL,
            long_pauses INTEGER,
            active_app TEXT,
            predictions TEXT,
            advice TEXT,
            raw_metrics TEXT,
            FOREIGN KEY (user_id) REFERENCES accounts(id),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    ''')

    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash password with salt using SHA256"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash"""
    try:
        salt, hashed = stored_hash.split(':', 1)
        check = hashlib.sha256((password + salt).encode()).hexdigest()
        return check == hashed
    except Exception:
        return False

def create_user(username: str, password: str, account_type: str = 'single',
                supervisor_id: int = None, full_name: str = '', email: str = '',
                can_change_password: bool = True) -> dict:
    """Create a new user account"""
    conn = get_connection()
    c = conn.cursor()
    try:
        pw_hash = hash_password(password)
        c.execute('''
            INSERT INTO accounts (username, password_hash, account_type, supervisor_id,
                                  full_name, email, can_change_password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, pw_hash, account_type, supervisor_id, full_name, email,
              1 if can_change_password else 0))
        conn.commit()
        return {'success': True, 'user_id': c.lastrowid}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'Username already exists'}
    finally:
        conn.close()

def login_user(username: str, password: str) -> dict:
    """Authenticate user and return user data"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM accounts WHERE username = ? AND is_active = 1', (username,))
    user = c.fetchone()
    conn.close()
    if not user:
        return {'success': False, 'error': 'User not found'}
    if not verify_password(password, user['password_hash']):
        return {'success': False, 'error': 'Incorrect password'}
    return {
        'success': True,
        'user': dict(user)
    }

def get_supervisor_users(supervisor_id: int) -> list:
    """Get all users under a supervisor"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, username, full_name, email, created_at, is_active, can_change_password
        FROM accounts WHERE supervisor_id = ?
    ''', (supervisor_id,))
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return users

def update_user_password(user_id: int, new_password: str, changer_id: int = None) -> bool:
    """Update a user's password (supervisor only for sub-users)"""
    conn = get_connection()
    c = conn.cursor()
    # Check if changer has permission
    if changer_id:
        c.execute('SELECT supervisor_id, can_change_password FROM accounts WHERE id = ?', (user_id,))
        user = c.fetchone()
        if user and user['supervisor_id'] != changer_id:
            conn.close()
            return False
    pw_hash = hash_password(new_password)
    c.execute('UPDATE accounts SET password_hash = ? WHERE id = ?', (pw_hash, user_id))
    conn.commit()
    conn.close()
    return True

def toggle_user_active(user_id: int, supervisor_id: int) -> bool:
    """Activate/deactivate a sub-user"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT is_active FROM accounts WHERE id = ? AND supervisor_id = ?',
              (user_id, supervisor_id))
    user = c.fetchone()
    if not user:
        conn.close()
        return False
    new_state = 0 if user['is_active'] else 1
    c.execute('UPDATE accounts SET is_active = ? WHERE id = ?', (new_state, user_id))
    conn.commit()
    conn.close()
    return True

def delete_sub_user(user_id: int, supervisor_id: int) -> bool:
    """Delete a sub-user"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE accounts SET is_active = 0 WHERE id = ? AND supervisor_id = ?',
              (user_id, supervisor_id))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def save_report(user_id: int, session_id: int, load_level: str, confidence: float,
                keystrokes: int, backspaces: int, wpm: float, avg_iki: float,
                long_pauses: int, active_app: str, predictions: str, advice: str,
                raw_metrics: str) -> int:
    """Save an analysis report"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO reports (user_id, session_id, load_level, confidence, keystrokes,
                             backspaces, wpm, avg_iki_ms, long_pauses, active_app,
                             predictions, advice, raw_metrics)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, session_id, load_level, confidence, keystrokes, backspaces,
          wpm, avg_iki, long_pauses, active_app, predictions, advice, raw_metrics))
    report_id = c.lastrowid
    conn.commit()
    conn.close()
    return report_id

def get_user_reports(user_id: int, limit: int = 50) -> list:
    """Get reports for a user"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM reports WHERE user_id = ?
        ORDER BY timestamp DESC LIMIT ?
    ''', (user_id, limit))
    reports = [dict(row) for row in c.fetchall()]
    conn.close()
    return reports

def get_all_reports_for_supervisor(supervisor_id: int, limit: int = 200) -> list:
    """Get reports for all users under a supervisor"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT r.*, a.username, a.full_name
        FROM reports r
        JOIN accounts a ON r.user_id = a.id
        WHERE a.supervisor_id = ? OR r.user_id = ?
        ORDER BY r.timestamp DESC LIMIT ?
    ''', (supervisor_id, supervisor_id, limit))
    reports = [dict(row) for row in c.fetchall()]
    conn.close()
    return reports

def start_session(user_id: int) -> int:
    """Start a new monitoring session"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO sessions (user_id, started_at) VALUES (?, ?)
    ''', (user_id, datetime.now().isoformat()))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def end_session(session_id: int, total_keystrokes: int, total_backspaces: int,
                avg_wpm: float, avg_iki: float, avg_load: str, active_app: str):
    """End a monitoring session"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE sessions SET ended_at = ?, total_keystrokes = ?, total_backspaces = ?,
        avg_wpm = ?, avg_iki_ms = ?, avg_load_level = ?, active_app = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), total_keystrokes, total_backspaces,
          avg_wpm, avg_iki, avg_load, active_app, session_id))
    conn.commit()
    conn.close()
