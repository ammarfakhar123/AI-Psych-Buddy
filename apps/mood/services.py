"""Mood helper functions (kept out of views so they can be reused by the AI pipeline)."""
from datetime import timedelta

from django.utils import timezone

from .models import MoodEntry

LOW_MOODS = {"sad", "anxious", "stressed", "angry", "tired"}


def entries_since(user, days):
    start = timezone.localdate() - timedelta(days=days - 1)
    return MoodEntry.objects.filter(user=user, date__gte=start).order_by("date")


def todays_entry(user):
    return MoodEntry.objects.filter(user=user, date=timezone.localdate()).first()


def chart_data(user, days):
    """Labels + scores for Chart.js."""
    entries = list(entries_since(user, days))
    return {
        "labels": [e.date.strftime("%b %d") for e in entries],
        "scores": [e.score for e in entries],
        "moods": [e.get_mood_display() for e in entries],
    }


def describe_trend(entries):
    """Neutral, non-clinical wording about recent entries (never a diagnosis)."""
    entries = list(entries)
    if len(entries) < 3:
        return "Log a few more days to see how your mood is trending."
    low_days = sum(1 for e in entries if e.mood in LOW_MOODS or e.score <= 2)
    high_days = sum(1 for e in entries if e.score >= 4)
    if low_days >= len(entries) * 0.6:
        return ("Your recent entries show more low-mood days. You may want to reflect on what has been "
                "affecting your wellbeing, and consider talking with someone you trust.")
    if high_days >= len(entries) * 0.6:
        return "Your recent entries show mostly positive days. It may help to notice what has been supporting you."
    return "Your recent entries show a mix of moods, which is a normal part of everyday life."


def summary_for_prompt(user, days=7):
    """One short line about recent moods, injected into the LLM prompt for personalisation."""
    entries = list(entries_since(user, days))
    if not entries:
        return "No recent mood check-ins."
    recent = ", ".join(f"{e.date:%a}: {e.mood}" for e in entries[-5:])
    return f"{recent}. {describe_trend(entries)}"
