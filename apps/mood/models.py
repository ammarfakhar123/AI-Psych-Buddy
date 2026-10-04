from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class MoodEntry(models.Model):
    """One mood check-in per user per day (re-submitting the same day updates it)."""

    MOOD_CHOICES = [
        ("happy", "Happy"),
        ("good", "Good"),
        ("neutral", "Neutral"),
        ("tired", "Tired"),
        ("sad", "Sad"),
        ("anxious", "Anxious"),
        ("stressed", "Stressed"),
        ("angry", "Angry"),
    ]
    # Default 1-5 score for each mood (5 = most positive). Users can adjust it.
    DEFAULT_SCORES = {
        "happy": 5, "good": 4, "neutral": 3, "tired": 2,
        "sad": 2, "anxious": 2, "stressed": 2, "angry": 1,
    }
    EMOJI = {
        "happy": "😄", "good": "🙂", "neutral": "😐", "tired": "😴",
        "sad": "😢", "anxious": "😟", "stressed": "😣", "angry": "😠",
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mood_entries")
    date = models.DateField(default=timezone.localdate)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 = very low, 5 = very good",
    )
    note = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "mood entries"
        constraints = [models.UniqueConstraint(fields=["user", "date"], name="one_mood_entry_per_day")]
        indexes = [models.Index(fields=["user", "-date"])]

    def __str__(self):
        return f"{self.user} - {self.date} - {self.mood}"

    @property
    def emoji(self):
        return self.EMOJI.get(self.mood, "")

    @classmethod
    def mood_options(cls):
        """List of dicts for templates: value, label, emoji, default score."""
        return [
            {"value": v, "label": label, "emoji": cls.EMOJI[v], "score": cls.DEFAULT_SCORES[v]}
            for v, label in cls.MOOD_CHOICES
        ]
