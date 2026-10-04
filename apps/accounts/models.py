from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra information about a user. Created automatically with the user."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=60, blank=True, help_text="What the assistant should call you.")
    support_focus = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional: what you'd like to work on (e.g. 'stress at work, sleep'). Used to personalise replies.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def friendly_name(self):
        return self.display_name or self.user.first_name or self.user.username
