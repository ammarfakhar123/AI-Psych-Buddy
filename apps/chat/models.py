from django.conf import settings
from django.db import models


class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=120, default="New conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["user", "-updated_at"])]

    def __str__(self):
        return f"{self.title} ({self.user})"


class Message(models.Model):
    SENDER_USER = "user"
    SENDER_ASSISTANT = "assistant"
    SENDER_CHOICES = [(SENDER_USER, "User"), (SENDER_ASSISTANT, "Assistant")]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    # Titles of the knowledge-base chunks that informed an assistant reply (RAG transparency).
    sources = models.JSONField(default=list, blank=True)
    # True when the safety layer flagged this exchange as high risk.
    is_crisis = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp", "id"]
        indexes = [models.Index(fields=["conversation", "timestamp"])]

    def __str__(self):
        return f"{self.sender}: {self.message[:40]}"
