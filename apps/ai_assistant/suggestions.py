"""Rule-based wellness suggestions from the user's words and/or selected mood.

These are general wellness ideas only - never diagnoses or treatment advice.
"""
import re

# url_name values are resolved in templates/views with Django's `reverse`.
SUGGESTION_LIBRARY = {
    "grounding": {
        "title": "Try a grounding exercise",
        "description": "The 5-4-3-2-1 exercise can help you notice the present moment when things feel overwhelming.",
        "url_name": "exercises:grounding_list", "icon": "bi-tree",
    },
    "breathing": {
        "title": "Take a few slow breaths",
        "description": "A guided breathing rhythm may help you slow down and settle for a minute or two.",
        "url_name": "exercises:breathing", "icon": "bi-wind",
    },
    "cbt": {
        "title": "Reflect with a CBT-style exercise",
        "description": "Look at a difficult thought step by step and find a more balanced perspective.",
        "url_name": "exercises:cbt_new", "icon": "bi-lightbulb",
    },
    "journal": {
        "title": "Write it down",
        "description": "A few minutes of free writing about your day can help you sort through your feelings.",
        "url_name": "mood:tracker", "icon": "bi-journal-text",
    },
    "break": {
        "title": "Take a short break",
        "description": "Step away for 5-10 minutes: stretch, drink some water, or get a little fresh air.",
        "url_name": None, "icon": "bi-cup-hot",
    },
    "trusted_person": {
        "title": "Talk to someone you trust",
        "description": "Sharing how you feel with a friend or family member can make things feel lighter.",
        "url_name": None, "icon": "bi-people",
    },
    "professional": {
        "title": "Consider professional support",
        "description": "If these feelings keep affecting your daily life, a qualified mental-health professional can help.",
        "url_name": None, "icon": "bi-heart-pulse",
    },
}

THEMES = {
    "anxiety": (r"anxious|anxiety|panic|worry|worried|nervous|overwhelm|racing", ["breathing", "grounding", "cbt"]),
    "stress": (r"stress|pressure|deadline|burn(ed|t)? ?out|too much|exam|workload", ["break", "breathing", "journal"]),
    "low_mood": (r"sad|down|lonely|empty|cry|unmotivated|hopeless", ["trusted_person", "journal", "professional"]),
    "rumination": (r"overthink|can'?t stop thinking|negative thought|what if|ruminat|guilt|failure", ["cbt", "journal"]),
    "anger": (r"angry|furious|mad|irritat|frustrat|rage", ["breathing", "break", "journal"]),
    "tired": (r"tired|exhaust|can'?t sleep|insomnia|sleep|fatigue", ["break", "breathing"]),
}

MOOD_DEFAULTS = {
    "happy": ["journal"],
    "good": ["journal"],
    "neutral": ["journal", "breathing"],
    "tired": ["break", "breathing"],
    "sad": ["trusted_person", "journal", "cbt"],
    "anxious": ["breathing", "grounding", "cbt"],
    "stressed": ["breathing", "break", "journal"],
    "angry": ["breathing", "break", "journal"],
}


def suggest(text="", mood=None, limit=3):
    """Return up to `limit` suggestion dicts, best matches first."""
    keys = []
    for pattern, ideas in THEMES.values():
        if re.search(pattern, text or "", re.IGNORECASE):
            keys.extend(ideas)
    keys.extend(MOOD_DEFAULTS.get(mood, []))
    if not keys:
        keys = ["breathing", "journal", "trusted_person"]

    unique = list(dict.fromkeys(keys))[:limit]
    # Persistent low mood language -> always gently mention professional support.
    if re.search(r"hopeless|worthless|every day|for weeks|for months", text or "", re.IGNORECASE):
        if "professional" not in unique:
            unique = unique[: limit - 1] + ["professional"]
    return [dict(SUGGESTION_LIBRARY[key], key=key) for key in unique]
