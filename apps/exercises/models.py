from django.conf import settings
from django.db import models


class WellnessExercise(models.Model):
    """A guided exercise (grounding, breathing, ...). Steps are stored as JSON list."""

    CATEGORY_CHOICES = [
        ("grounding", "Grounding"),
        ("breathing", "Breathing"),
        ("relaxation", "Relaxation"),
    ]
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    steps = models.JSONField(default=list, help_text="List of {'title': ..., 'prompt': ...} dicts")
    duration_minutes = models.PositiveSmallIntegerField(default=3)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self):
        return self.title


class CBTReflection(models.Model):
    """A completed CBT-style self-reflection exercise (a wellness exercise, not therapy)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cbt_reflections")
    situation = models.TextField(max_length=1500)
    automatic_thought = models.TextField(max_length=1000)
    evidence_for = models.TextField(max_length=1500)
    evidence_against = models.TextField(max_length=1500)
    balanced_thought = models.TextField(max_length=1000)
    reflection = models.TextField(max_length=1500, blank=True)
    ai_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"Reflection by {self.user} on {self.created_at:%Y-%m-%d}"
