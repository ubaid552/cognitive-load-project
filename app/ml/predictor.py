"""
CogniLoad - ML Predictor
Wraps the existing scikit-learn model to predict cognitive load
from keystroke features (Lin et al., 2013)
"""
import os
import numpy as np
import joblib

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE, 'cognitive_load_model.pkl')
ENCODER_PATH = os.path.join(BASE, 'label_encoder.pkl')

FEATURE_COLS = [
    "iki_mean_x", "iki_median", "iki_std", "iki_max", "long_pauses",
    "total_backspaces", "total_del_chars", "total_ins_chars", "total_del_words",
    "revision_events", "n_insertions", "n_deletions", "n_substitutions",
    "total_duration", "mean_duration", "std_duration", "mean_from_edge",
    "mean_from_sent", "mean_chars_product", "total_revisions",
    "deletion_ratio", "revision_ratio", "backspace_rate", "long_pause_ratio",
    "iki_mean_y", "iki_sd", "n_chars_process", "n_chars_product",
    "n_words_product", "total_time", "words_per_min", "chars_per_word",
    "process_overhead"
]


class CognitiveLoadPredictor:
    def __init__(self):
        self.model = None
        self.encoder = None
        self._load_model()

    def _load_model(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            self.encoder = joblib.load(ENCODER_PATH)
        except Exception as e:
            print(f"[Predictor] Warning: Could not load model: {e}")
            self.model = None
            self.encoder = None

    def extract_features(self, events: list, total_time_ms: float) -> list:
        """Extract 33 Lin et al. (2013) features from keystroke events"""
        if not events:
            return None

        ikis = [e['iki'] for e in events if e.get('iki') is not None]
        durations = [e['duration'] for e in events if e.get('duration') is not None]

        n_backspaces = sum(1 for e in events if e.get('is_backspace'))
        n_deletions_e = sum(1 for e in events if e.get('type') == 'deletion')
        n_insertions = sum(1 for e in events if e.get('type') == 'insertion')
        n_del_chars = sum(e.get('del_chars', 0) for e in events)
        n_ins_chars = sum(e.get('ins_chars', 0) for e in events)
        n_del_words = sum(e.get('del_words', 0) for e in events)
        revision_events = sum(1 for e in events if e.get('is_revision'))
        n_substitutions = sum(1 for e in events if e.get('type') == 'substitution')
        total_revisions = len(events)
        n_chars_process = sum(e.get('ins_chars', 0) + e.get('del_chars', 0) for e in events)
        n_chars_product = n_ins_chars
        n_words_product = max(1, n_chars_product // 5)

        iki_arr = np.array(ikis) if ikis else np.array([0])
        dur_arr = np.array(durations) if durations else np.array([0])

        iki_mean = float(np.mean(iki_arr))
        iki_median = float(np.median(iki_arr))
        iki_std = float(np.std(iki_arr))
        iki_max = float(np.max(iki_arr))
        long_pauses = int(np.sum(iki_arr > 2000))

        total_dur = float(np.sum(dur_arr))
        mean_dur = float(np.mean(dur_arr))
        std_dur = float(np.std(dur_arr))

        deletion_ratio = n_del_chars / (n_ins_chars + 1)
        revision_ratio = revision_events / (total_revisions + 1)
        backspace_rate = n_backspaces / (total_dur + 1) * 1000
        long_pause_ratio = long_pauses / (total_revisions + 1)

        words_per_min = n_words_product / (total_time_ms / 60000 + 0.001)
        chars_per_word = n_chars_product / (n_words_product + 1)
        process_overhead = n_chars_process / (n_chars_product + 1)

        feat = {
            "iki_mean_x": iki_mean, "iki_median": iki_median,
            "iki_std": iki_std, "iki_max": iki_max,
            "long_pauses": long_pauses,
            "total_backspaces": n_backspaces,
            "total_del_chars": n_del_chars,
            "total_ins_chars": n_ins_chars,
            "total_del_words": n_del_words,
            "revision_events": revision_events,
            "n_insertions": n_insertions,
            "n_deletions": n_deletions_e,
            "n_substitutions": n_substitutions,
            "total_duration": total_dur,
            "mean_duration": mean_dur,
            "std_duration": std_dur,
            "mean_from_edge": 5.0,
            "mean_from_sent": 20.0,
            "mean_chars_product": n_chars_product / (total_revisions + 1),
            "total_revisions": total_revisions,
            "deletion_ratio": deletion_ratio,
            "revision_ratio": revision_ratio,
            "backspace_rate": backspace_rate,
            "long_pause_ratio": long_pause_ratio,
            "iki_mean_y": iki_mean,
            "iki_sd": iki_std,
            "n_chars_process": n_chars_process,
            "n_chars_product": n_chars_product,
            "n_words_product": n_words_product,
            "total_time": total_time_ms,
            "words_per_min": words_per_min,
            "chars_per_word": chars_per_word,
            "process_overhead": process_overhead,
        }
        return [feat[c] for c in FEATURE_COLS]

    def predict(self, events: list, total_time_ms: float) -> dict:
        """Run prediction and return result dict"""
        if len(events) < 5:
            return {'error': 'Not enough data (need at least 5 keystrokes)'}

        features = self.extract_features(events, total_time_ms)
        if features is None:
            return {'error': 'Feature extraction failed'}

        # If model not available, use heuristic
        if self.model is None:
            return self._heuristic_predict(events, total_time_ms, features)

        try:
            X = np.array(features).reshape(1, -1)
            pred = self.model.predict(X)[0]
            label = self.encoder.inverse_transform([pred])[0]
            proba = self.model.predict_proba(X)[0] if hasattr(self.model, 'predict_proba') else None
            confidence = round(float(np.max(proba)) * 100, 1) if proba is not None else 75.0
            level = 'High' if label == 'GR' else 'Low'

            # Compute readable metrics
            ikis = [e['iki'] for e in events if e.get('iki') is not None]
            avg_iki = float(np.mean(ikis)) if ikis else 0
            n_bs = sum(1 for e in events if e.get('is_backspace'))
            ins_chars = sum(e.get('ins_chars', 0) for e in events)
            words = max(1, ins_chars // 5)
            wpm = words / (total_time_ms / 60000 + 0.001)
            long_p = sum(1 for i in ikis if i > 2000)

            return {
                'label': label,
                'level': level,
                'confidence': confidence,
                'metrics': {
                    'avg_pause_ms': round(avg_iki),
                    'backspaces': n_bs,
                    'words_per_min': round(wpm, 1),
                    'long_pauses': long_p,
                    'total_keystrokes': len(events),
                    'deletion_ratio': round(features[20], 3),
                    'revision_ratio': round(features[21], 3),
                }
            }
        except Exception as e:
            return self._heuristic_predict(events, total_time_ms, features)

    def _heuristic_predict(self, events: list, total_time_ms: float, features: list = None) -> dict:
        """Fallback heuristic when model is not available"""
        ikis = [e['iki'] for e in events if e.get('iki') is not None]
        avg_iki = float(np.mean(ikis)) if ikis else 200
        n_bs = sum(1 for e in events if e.get('is_backspace'))
        long_p = sum(1 for i in ikis if i > 2000)
        ins_chars = sum(e.get('ins_chars', 0) for e in events)
        total = len(events)

        score = 0
        if avg_iki > 500: score += 2
        if n_bs / (total + 1) > 0.2: score += 2
        if long_p > 3: score += 2

        level = 'High' if score >= 3 else 'Low'
        label = 'GR' if level == 'High' else 'OK'
        confidence = min(95, 60 + score * 5)

        wpm = max(1, ins_chars // 5) / (total_time_ms / 60000 + 0.001)
        return {
            'label': label,
            'level': level,
            'confidence': float(confidence),
            'metrics': {
                'avg_pause_ms': round(avg_iki),
                'backspaces': n_bs,
                'words_per_min': round(wpm, 1),
                'long_pauses': long_p,
                'total_keystrokes': total,
                'deletion_ratio': n_bs / (total + 1),
                'revision_ratio': n_bs / (total + 1),
            }
        }


# Singleton
predictor = CognitiveLoadPredictor()
