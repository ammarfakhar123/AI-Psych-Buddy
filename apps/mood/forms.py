from django import forms
from django.utils import timezone

from .models import MoodEntry


class MoodEntryForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ("mood", "score", "note")
        widgets = {
            "mood": forms.HiddenInput(),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control",
                                           "placeholder": "Optional: anything you'd like to remember about today?"}),
            "score": forms.NumberInput(attrs={"type": "range", "min": 1, "max": 5, "class": "form-range"}),
        }

    def clean_note(self):
        return self.cleaned_data["note"].strip()

    def clean_score(self):
        score = self.cleaned_data["score"]
        if not 1 <= score <= 5:
            raise forms.ValidationError("Score must be between 1 and 5.")
        return score
