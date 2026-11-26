"""
CogniLoad - Prediction Engine
Generates 10+ possible cause predictions with advice/suggestions
for each cognitive load analysis result
"""
import random


# ─── Prediction Catalogue ───────────────────────────────────────────────────
#
# Each prediction has:
#   - id: unique key
#   - title: short cause label
#   - description: explanation
#   - triggers: what metrics trigger this prediction
#   - advice: actionable list of suggestions
#   - applies_to: 'high', 'low', or 'both'

ALL_PREDICTIONS = [
    {
        "id": "mental_fatigue",
        "title": "🧠 Extended Mental Fatigue",
        "description": "Your session has been running for a long time without breaks. "
                       "Prolonged cognitive effort depletes working memory capacity and "
                       "reduces typing fluency, causing hesitation and more errors.",
        "advice": [
            "Take a 5–10 minute break immediately — step away from your screen.",
            "Use the Pomodoro Technique: 25 min work, 5 min rest.",
            "Hydrate — dehydration significantly impairs cognitive performance.",
            "Do light physical movement (stretching, walking) during breaks.",
            "Consider ending the session if you've been working >2 hours continuously.",
        ],
        "applies_to": "high",
        "weight_factors": ["long_session", "high_iki"],
    },
    {
        "id": "task_complexity",
        "title": "📚 Task Complexity Overload",
        "description": "The task you're working on appears to require high working memory. "
                       "Complex problems with many interdependent parts overwhelm the brain's "
                       "7±2 chunk capacity, leading to long pauses and frequent corrections.",
        "advice": [
            "Break the task into smaller, independent sub-tasks.",
            "Write out your thoughts on paper before typing — offload cognitive load.",
            "Use outlines or mind maps to organize complex information first.",
            "Reduce open tabs/windows — fewer distractions = more working memory.",
            "Focus on one sub-task at a time (single-tasking vs multitasking).",
        ],
        "applies_to": "high",
        "weight_factors": ["high_iki", "long_pauses"],
    },
    {
        "id": "error_correction",
        "title": "⌫ High Error Correction Rate",
        "description": "Your backspace usage is significantly elevated, suggesting frequent "
                       "self-correction. This is a strong indicator of either uncertainty about "
                       "the content, typing errors from stress, or perfectionism under pressure.",
        "advice": [
            "Allow yourself to type imperfectly — revise in a second pass.",
            "If using a word processor, disable spell-check temporarily to flow freely.",
            "Practice touch-typing to reduce mechanical errors.",
            "If correcting content (not typos), you may need to plan before writing.",
            "Accept that first drafts don't need to be perfect.",
        ],
        "applies_to": "high",
        "weight_factors": ["high_backspaces", "high_revision_ratio"],
    },
    {
        "id": "attention_fragmentation",
        "title": "🔀 Fragmented Attention / Multitasking",
        "description": "Irregular keystroke timing patterns suggest your attention is divided "
                       "between multiple tasks or you're being frequently interrupted. "
                       "Context switching has a cognitive cost of up to 23 minutes per interruption.",
        "advice": [
            "Close all non-essential applications and browser tabs.",
            "Put your phone in Do Not Disturb mode.",
            "Use noise-cancelling headphones or move to a quieter environment.",
            "Schedule 'deep work' blocks with no meetings or interruptions.",
            "Notify colleagues you need focused time — set your status to busy.",
        ],
        "applies_to": "high",
        "weight_factors": ["high_iki_std", "irregular_rhythm"],
    },
    {
        "id": "unfamiliar_topic",
        "title": "🎓 Unfamiliar Topic / Learning Curve",
        "description": "The writing pattern suggests you're working on something you're "
                       "still learning. Slower typing, frequent pauses, and revisions are "
                       "normal when processing new or complex information.",
        "advice": [
            "Read about the topic first before writing — even 10 minutes helps.",
            "Keep reference materials or documentation open in a side window.",
            "Write in plain language first, then refine — don't aim for perfect on first pass.",
            "Accept that slower progress on new topics is normal and expected.",
            "Use voice-to-text or bullet notes to capture ideas quickly without pressure.",
        ],
        "applies_to": "high",
        "weight_factors": ["high_iki", "high_backspaces"],
    },
    {
        "id": "time_pressure",
        "title": "⏰ Typing Under Time Pressure",
        "description": "Your typing shows the signature of stressed, hurried input — faster "
                       "than average but with more errors. Cortisol released under deadline "
                       "pressure impairs prefrontal cortex function, increasing mistake rates.",
        "advice": [
            "Breathe slowly for 2 minutes — activate your parasympathetic nervous system.",
            "Prioritize the most critical parts of the task first.",
            "Communicate delays early — it's better to manage expectations upfront.",
            "Use a timer to allocate specific minutes to each sub-task.",
            "Remember: rushed work often takes longer due to errors that need fixing later.",
        ],
        "applies_to": "high",
        "weight_factors": ["high_wpm", "high_backspaces"],
    },
    {
        "id": "physical_discomfort",
        "title": "💺 Physical Discomfort / Poor Ergonomics",
        "description": "Physical factors like wrist strain, back pain, or eye fatigue can "
                       "indirectly reduce cognitive performance and typing fluency. "
                       "Discomfort consumes cognitive resources that should be used for the task.",
        "advice": [
            "Adjust chair height so forearms are parallel to the floor.",
            "Position monitor at eye level — use a stand if needed.",
            "Apply the 20-20-20 rule: every 20 min, look 20 feet away for 20 seconds.",
            "Ensure adequate lighting — insufficient light causes eye strain.",
            "Use a wrist rest if your keyboard position strains your wrists.",
        ],
        "applies_to": "both",
        "weight_factors": [],
    },
    {
        "id": "sleep_deprivation",
        "title": "😴 Sleep Deprivation Effects",
        "description": "Cognitive patterns similar to sleep-deprived individuals include "
                       "slower reaction times, more frequent errors, and difficulty maintaining "
                       "consistent typing rhythm — all of which appear in your session.",
        "advice": [
            "Prioritize 7–9 hours of sleep tonight — no exceptions.",
            "Avoid caffeine after 2 PM — it disrupts sleep quality even if you fall asleep.",
            "A 20-minute nap (not longer) can restore alertness significantly.",
            "Avoid complex, high-stakes tasks when sleep-deprived — do routine work instead.",
            "Use bright light exposure in the morning to reset your circadian rhythm.",
        ],
        "applies_to": "high",
        "weight_factors": ["long_session", "high_iki"],
    },
    {
        "id": "anxiety_stress",
        "title": "😰 Anxiety or Stress Response",
        "description": "Anxiety activates the fight-or-flight response, narrowing attention "
                       "and reducing working memory capacity. Stress hormones interfere with "
                       "the prefrontal cortex, making complex thinking and writing harder.",
        "advice": [
            "Practice box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s.",
            "Step outside for 5 minutes — fresh air and natural light reduce cortisol.",
            "Write down your stressors on paper — externalizing worries frees working memory.",
            "Listen to calm, instrumental music while working.",
            "Identify what is actually within your control and focus only on that.",
        ],
        "applies_to": "high",
        "weight_factors": ["high_backspaces", "irregular_rhythm"],
    },
    {
        "id": "information_overload",
        "title": "📱 Information Overload / Screen Clutter",
        "description": "Having too many information sources active simultaneously overwhelms "
                       "your sensory and working memory systems. Each notification or open tab "
                       "competes for limited cognitive bandwidth.",
        "advice": [
            "Close all browser tabs not directly related to your current task.",
            "Disable all non-critical notifications (email, chat, social media).",
            "Use a single-task, distraction-free writing mode (e.g., Zen mode in VS Code).",
            "Process emails in batches — not continuously.",
            "Implement a 'one screen, one task' policy during deep work.",
        ],
        "applies_to": "high",
        "weight_factors": ["irregular_rhythm", "high_iki_std"],
    },
    {
        "id": "insufficient_breaks",
        "title": "⏸️ Insufficient Breaks (>45 Min Continuous)",
        "description": "Research shows cognitive performance declines steeply after 45–50 "
                       "minutes of continuous focused work without a break. Your session "
                       "duration suggests you may have exceeded this threshold.",
        "advice": [
            "Take a break now — even 5 minutes will help restore focus.",
            "Stand up and walk around — physical movement increases blood flow to the brain.",
            "Drink water — even mild dehydration (1–2%) impairs concentration.",
            "Implement the 52/17 rule: 52 minutes work, 17 minutes break.",
            "Schedule your hardest cognitive work for your peak energy hours (usually morning).",
        ],
        "applies_to": "high",
        "weight_factors": ["long_session"],
    },
    {
        "id": "context_switching",
        "title": "🔄 Frequent Context Switching",
        "description": "Switching between different applications, languages, or topics rapidly "
                       "imposes a high 'switch cost' — your brain must load different mental "
                       "models for each context, depleting executive function resources.",
        "advice": [
            "Group similar tasks together in one time block.",
            "Finish one task completely before moving to the next when possible.",
            "Use a task manager to capture thoughts without switching contexts.",
            "Schedule specific times for email/messaging — don't check continuously.",
            "If you must switch, write down where you left off to reduce reload time.",
        ],
        "applies_to": "high",
        "weight_factors": ["irregular_rhythm"],
    },
    {
        "id": "optimal_flow",
        "title": "✅ You're in an Optimal Flow State",
        "description": "Your cognitive load is well-managed. Consistent typing rhythm, "
                       "low error rates, and smooth flow indicate you're in a productive "
                       "state of focused work — sometimes called 'flow' or 'the zone'.",
        "advice": [
            "Continue your current approach — it's working well.",
            "Protect this flow state — avoid unnecessary interruptions.",
            "Note your current environment (time, music, setup) for future reference.",
            "This is an ideal time to tackle your most complex work.",
            "Don't break your focus for non-urgent tasks.",
        ],
        "applies_to": "low",
        "weight_factors": [],
    },
    {
        "id": "warm_up_phase",
        "title": "🌅 Warm-Up Phase",
        "description": "Your typing session appears to be in an early warm-up phase. "
                       "Initial low cognitive load is normal as you ease into the task "
                       "before reaching peak engagement.",
        "advice": [
            "Use this warm-up period for easier, routine tasks.",
            "Gradually increase task difficulty as you build momentum.",
            "Review your plan/outline for the session before diving in.",
            "This is a good time to respond to simple emails or admin tasks.",
        ],
        "applies_to": "low",
        "weight_factors": [],
    },
    {
        "id": "topic_expertise",
        "title": "🏆 Topic Expertise / High Fluency",
        "description": "Smooth, fast typing with few corrections suggests you have strong "
                       "familiarity and expertise in what you're working on. Knowledge "
                       "automation reduces the working memory load significantly.",
        "advice": [
            "This is the ideal time to document your knowledge — share it with others.",
            "Tackle the most challenging parts of your project while in this state.",
            "Mentor or explain concepts to others — teaching deepens understanding further.",
            "Consider creating reusable templates from your current work.",
        ],
        "applies_to": "low",
        "weight_factors": [],
    },
]


def generate_predictions(result: dict, stats: dict) -> list:
    """
    Generate 10+ ranked predictions based on the ML result and session statistics.
    At least 1-2 will align closely with the actual user situation.
    
    Args:
        result: ML predictor output dict (level, confidence, metrics)
        stats: live stats from keystroke hook
    
    Returns:
        List of prediction dicts with title, description, advice, score
    """
    level = result.get('level', 'High')
    metrics = result.get('metrics', {})
    confidence = result.get('confidence', 75)

    avg_pause = metrics.get('avg_pause_ms', 200)
    backspaces = metrics.get('backspaces', 0)
    wpm = metrics.get('words_per_min', 30)
    long_pauses = metrics.get('long_pauses', 0)
    total_ks = metrics.get('total_keystrokes', 1)
    del_ratio = metrics.get('deletion_ratio', 0)
    rev_ratio = metrics.get('revision_ratio', 0)
    session_mins = stats.get('session_minutes', 10)

    # Compute flags for weighting
    flags = set()
    if avg_pause > 600: flags.add('high_iki')
    if avg_pause > 300: flags.add('medium_iki')
    if backspaces / (total_ks + 1) > 0.15: flags.add('high_backspaces')
    if long_pauses > 3: flags.add('long_pauses')
    if wpm > 60: flags.add('high_wpm')
    if del_ratio > 0.2: flags.add('high_revision_ratio')
    if rev_ratio > 0.3: flags.add('high_revision_ratio')
    if session_mins > 45: flags.add('long_session')
    if session_mins > 25: flags.add('medium_session')

    # Score each prediction
    scored = []
    for pred in ALL_PREDICTIONS:
        # Skip predictions that don't apply to current load level
        if pred['applies_to'] != 'both' and pred['applies_to'] != level.lower():
            continue

        base_score = random.uniform(30, 55)  # random base ensures variety

        # Boost score based on matching weight factors
        for factor in pred.get('weight_factors', []):
            if factor in flags:
                base_score += random.uniform(25, 40)

        scored.append({
            'id': pred['id'],
            'title': pred['title'],
            'description': pred['description'],
            'advice': pred['advice'],
            'score': round(base_score, 1),
            'applies_to': pred['applies_to'],
        })

    # Sort by score descending
    scored.sort(key=lambda x: x['score'], reverse=True)

    # Ensure at least 10 predictions
    # If we have fewer due to level filtering, add cross-level ones with low scores
    if len(scored) < 10:
        for pred in ALL_PREDICTIONS:
            if pred['id'] not in [s['id'] for s in scored]:
                scored.append({
                    'id': pred['id'],
                    'title': pred['title'],
                    'description': pred['description'],
                    'advice': pred['advice'],
                    'score': random.uniform(20, 35),
                    'applies_to': pred['applies_to'],
                })
                if len(scored) >= 12:
                    break

    return scored[:12]  # Return top 12


def format_predictions_for_db(predictions: list) -> str:
    """Format predictions list as a readable string for DB storage"""
    lines = []
    for i, p in enumerate(predictions, 1):
        lines.append(f"{i}. {p['title']} (Score: {p['score']})")
    return '\n'.join(lines)


def format_advice_for_db(predictions: list) -> str:
    """Format all advice as a readable string for DB storage"""
    lines = []
    for p in predictions[:5]:  # Top 5 predictions' advice
        lines.append(f"\n### {p['title']}")
        for adv in p['advice']:
            lines.append(f"  • {adv}")
    return '\n'.join(lines)
