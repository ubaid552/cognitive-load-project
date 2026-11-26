# 🧠 CogniLoad — Cognitive Load Analyzer

**Repository:** `cognitive-load-project` · **Version:** 2.0.0 · **Platform:** Windows · **Language:** Python

**AI Project · Lahore Garrison University · Department of Software Engineering**
> Based on: Lin et al. (2013) — *Automatic cognitive load evaluation using writing features*

CogniLoad predicts, in real time, whether a user is under **High** or **Low** cognitive load — using only their typing patterns. It captures keystrokes system-wide, extracts 33 features from them, classifies the load with a trained Decision Tree model, explains the likely causes, and gives actionable advice — all from a PyQt6 desktop app that lives in the system tray.

---

## 📋 What Is CogniLoad?

**CogniLoad** is a Windows desktop application that monitors your **cognitive load in real-time** by analyzing your typing patterns across **any application** on your PC. It uses a pre-trained machine learning model to classify whether you are under **High** or **Low** cognitive load based on 33 keystroke-derived features, and gives you actionable advice to improve your mental performance.

The app runs as a **system tray application** and includes:
- 📊 Live dashboard with real-time keystroke metrics
- 🔮 Draggable floating overlay on top of any app
- 🔌 Auto-detection of 150+ apps (IDEs, browsers, office tools, terminals, etc.)
- 📋 Full analysis history with cause predictions and advice
- 👥 Supervisor/team management system
- 🧠 15 cognitive cause predictions with 5 actionable advice points each

---

## 📁 Project Structure

```
cogniload_app/
│
├── main.py                        ← App entry point (launch this)
├── run.bat                        ← Double-click launcher (installs deps + runs)
├── requirements.txt               ← Python package dependencies
│
├── cognitive_load_model.pkl       ← Trained ML model (Decision Tree Pipeline)
├── label_encoder.pkl              ← LabelEncoder — classes: ['GR', 'UG']
│
├── data/
│   └── .gitkeep                   ← SQLite database (cogniload.db) is auto-created
│                                    on first run and is NOT stored in this repo
│
└── app/
    ├── __init__.py                ← Package init (version 2.0.0)
    │
    ├── auth/
    │   ├── __init__.py
    │   ├── auth_manager.py        ← User session & auth management
    │   └── db.py                  ← SQLite DB layer (users, sessions, reports)
    │
    ├── ml/
    │   ├── __init__.py
    │   ├── predictor.py           ← ML model wrapper + 33-feature extraction
    │   └── prediction_engine.py   ← 15 cognitive cause predictions + advice
    │
    ├── monitor/
    │   ├── __init__.py
    │   ├── keystroke_hook.py      ← System-wide keystroke capture (pynput)
    │   └── system_monitor.py      ← Active app detection (psutil + Win32 API)
    │
    ├── ui/
    │   ├── __init__.py
    │   ├── login_window.py        ← Login / Register flow (4-page stacked widget)
    │   ├── main_window.py         ← Main dashboard (tabbed, system tray)
    │   ├── overlay.py             ← Draggable always-on-top floating widget
    │   ├── reports.py             ← Analysis history panel
    │   ├── supervisor.py          ← Supervisor/team management panel
    │   └── integration_popup.py   ← App watcher + per-app toggles + popup
    │
    └── utils/
        └── __init__.py            ← Shared helpers (format_timestamp, etc.)
```

---

## 🚀 How to Run

### Option A — Double-click (Easiest)
```
Double-click  run.bat
```
Automatically installs all dependencies on first run, then launches the app.

### Option B — Command Line
```bash
git clone https://github.com/ubaid552/cognitive-load-project.git
cd cognitive-load-project
pip install -r requirements.txt
python main.py
```

### Requirements
- **Python 3.10 or newer**
- **Windows** (uses Win32 API for active app detection)
- Internet connection on first run (to install packages)

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| PyQt6 | ≥6.6.0 | GUI framework (windows, widgets, system tray) |
| pynput | ≥1.7.6 | System-wide keystroke capture |
| psutil | ≥5.9.0 | Process monitoring, active app detection |
| scikit-learn | ≥1.3.0 | ML model (Decision Tree Pipeline) |
| joblib | ≥1.3.0 | Loading `.pkl` model files |
| numpy | ≥1.24.0 | Numerical feature computation |

---

## ⚙️ How It Works

### Step 1 — Keystroke Capture
`KeystrokeHook` (pynput) silently listens to **all keypresses system-wide** without blocking them. For every keypress it records:
- **IKI** — Inter-Keystroke Interval (milliseconds between keypresses)
- **Type** — insertion / deletion / backspace / other
- **Character counts** — `ins_chars`, `del_chars`

### Step 2 — Feature Extraction (33 features)
Based on **Lin et al. (2013)** methodology:

| Feature Group | Features |
|---|---|
| IKI Stats | mean, median, std, max, long_pauses (>2000 ms) |
| Revision | total_backspaces, del_chars, ins_chars, del_words, revision_events |
| Counts | n_insertions, n_deletions, n_substitutions, n_chars_process/product |
| Duration | total_duration, mean_duration, std_duration |
| Ratios | deletion_ratio, revision_ratio, backspace_rate, long_pause_ratio |
| Speed | words_per_min, chars_per_word, process_overhead, total_time |

### Step 3 — ML Prediction
The model is a **scikit-learn Pipeline**:
1. `SimpleImputer(strategy='median')` — fills missing values
2. `DecisionTreeClassifier(max_depth=5, random_state=42)` — classifies load level

**Output:**
- `GR` → **HIGH** Cognitive Load
- `UG` → **LOW** Cognitive Load

> If model files are missing, the predictor automatically falls back to a rule-based heuristic.

### Step 4 — Cause Predictions
`prediction_engine.py` scores 15 possible cognitive causes and returns the top 12 ranked by relevance to your current metrics:

**For HIGH Load:** Extended Mental Fatigue · Task Complexity Overload · High Error Correction Rate · Fragmented Attention · Unfamiliar Topic · Time Pressure · Physical Discomfort · Sleep Deprivation · Anxiety/Stress · Information Overload · Insufficient Breaks · Context Switching

**For LOW Load:** Optimal Flow State · Warm-Up Phase · Topic Expertise

### Step 5 — Auto-Analysis
- Runs automatically every **60 seconds** if ≥10 keystrokes are detected
- Manual trigger via "⚡ Analyze Now" button or the floating overlay

### Step 6 — App Integration
Scans all running processes every **6 seconds** via psutil. Supports **150+ apps** across 8 categories. When a new supported app is detected, a popup notification appears.

---

## 🖥️ UI Overview

### Login Screen
A 4-page stacked flow:
- **Page 0** — Sign In (username + password)
- **Page 1** — Choose Account Type (Single User or Supervisor)
- **Page 2** — Register as Single User
- **Page 3** — Register as Supervisor (with org name + team notes)

### Main Dashboard (Tabs)

| Tab | Description |
|---|---|
| 📊 Dashboard | Live 6-metric grid, Analyze/Reset buttons, cognitive load result card, confidence bar, top prediction |
| 📋 Reports | Full analysis history list + clickable detail view with ranked predictions and advice |
| 🔌 Integrations | 150+ app cards with ON/OFF toggles, running status, Enable All / Disable All |
| 👥 Team | *(Supervisor only)* Add/manage team members, change passwords, activate/deactivate |

### Floating Overlay
- Always on top of every app
- Draggable anywhere on screen
- Shows: load level, confidence %, WPM, keystrokes, backspaces, active app
- Collapse/expand toggle, close button
- Pulsing live dot indicator

### Integration Popup
- Appears bottom-right when a new supported app is detected
- 14-second countdown bar
- "Enable Overlay" or "Skip" options

---

## 🗄️ Database Schema (`data/cogniload.db`)

### `accounts`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| username | TEXT UNIQUE | Login name |
| password_hash | TEXT | `salt:sha256(pass+salt)` |
| account_type | TEXT | `single` / `supervisor` / `employee` |
| supervisor_id | INTEGER FK | Parent supervisor (employees only) |
| full_name | TEXT | Display name |
| email | TEXT | Optional |
| created_at | TEXT | ISO 8601 datetime |
| is_active | INTEGER | 1=active, 0=disabled |
| can_change_password | INTEGER | 0=supervisor sets password |

### `sessions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK | |
| started_at / ended_at | TEXT | ISO 8601 |
| total_keystrokes / total_backspaces | INTEGER | |
| avg_wpm / avg_iki_ms | REAL | |
| avg_load_level | TEXT | Final classification |
| active_app | TEXT | Last active app |

### `reports`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id / session_id | INTEGER FK | |
| timestamp | TEXT | ISO 8601 |
| load_level | TEXT | `High` or `Low` |
| confidence | REAL | Model confidence % |
| keystrokes / backspaces / wpm / avg_iki_ms / long_pauses | Metrics | |
| active_app | TEXT | App at time of analysis |
| predictions | TEXT | Ranked cause list |
| advice | TEXT | Advice from top 5 predictions |
| raw_metrics | TEXT | JSON blob of all metrics |

---

## 👥 User Roles

| Role | Capabilities |
|---|---|
| **Single User** | Self-register · Monitor own load · View own reports · Change own password |
| **Supervisor** | All above + Team tab · Add unlimited employees · Reset any employee password · Activate/deactivate accounts |
| **Employee** | Login (created by supervisor) · Monitor load · View reports · **Cannot** change own password |

---

## 🤖 Model Performance

| Model | Cross-Val Accuracy | Test Accuracy |
|---|---|---|
| **Decision Tree** | **96.9%** | **100%** |
| Random Forest | 93.8% | 88.2% |
| SVM (RBF) | 89.2% | 94.1% |

**Chosen model:** `DecisionTreeClassifier(max_depth=5, random_state=42)` in a `SimpleImputer(median)` Pipeline.

---

## 🐛 Known Fixes Applied (v2.0.0)

- ✅ Fixed: System tray icon not appearing until overlay was toggled (bug in `_setup_tray` / `_toggle_overlay`)
- ✅ Fixed: `main.py` was missing — now created with robust error handling
- ✅ Added: Proper `__init__.py` for all packages with exports
- ✅ Added: `app/utils` module with shared helpers
- ✅ Added: ML model fallback heuristic when `.pkl` files are absent

---

## 🔐 Privacy & Security Notes

- **No passwords, API keys or secrets are stored in this repository.** A full scan was done before publishing.
- User passwords are never stored in plain text — the app stores only a salted SHA-256 hash (`salt:sha256(password + salt)` in `app/auth/db.py`).
- The local database `data/cogniload.db` can contain user accounts and reports from a real run, so it is excluded via `.gitignore` and is re-created automatically on first launch.
- Keystroke monitoring is local only: features and metrics are computed and stored on the user's own PC; nothing is sent to an external API or server.

---

## 📚 Reference

Lin, T., Xie, T., Chen, Y., & Tang, N. (2013). *Automatic cognitive load evaluation using writing features: An exploratory study.* International Journal of Industrial Ergonomics, **43**(6), 503–513.

---

## 🏫 Academic Info

| | |
|---|---|
| **University** | Lahore Garrison University (LGU) |
| **Department** | Software Engineering |
| **Project Type** | AI Final Year Project |
| **Version** | 2.0.0 |
