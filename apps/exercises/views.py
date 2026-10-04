import logging

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.ai_assistant import llm_client, prompts, safety

from .models import CBTReflection, WellnessExercise

logger = logging.getLogger(__name__)


class CBTReflectionForm(forms.ModelForm):
    class Meta:
        model = CBTReflection
        fields = ("situation", "automatic_thought", "evidence_for", "evidence_against",
                  "balanced_thought", "reflection")
        widgets = {name: forms.Textarea(attrs={"rows": 4, "class": "form-control"}) for name in fields}

    def clean(self):
        cleaned = super().clean()
        for name, value in cleaned.items():
            if isinstance(value, str):
                cleaned[name] = value.strip()
        return cleaned


# CBT wizard steps shown in the template: (field name, title, helper text)
CBT_STEPS = [
    ("situation", "Situation", "What happened? Where were you, and who was there? Stick to the facts."),
    ("automatic_thought", "Automatic thought", "What went through your mind? Write the exact thought."),
    ("evidence_for", "Evidence for the thought", "What facts support this thought?"),
    ("evidence_against", "Evidence against the thought", "What facts don't fit it? What would you tell a friend?"),
    ("balanced_thought", "Balanced thought", "Write a fairer, more balanced way of seeing it."),
    ("reflection", "Reflection (optional)", "How do you feel now? Did anything shift, even a little?"),
]


# ------------------------------------------------------------------ hub
@login_required
def index(request):
    return render(request, "exercises/index.html", {
        "grounding": WellnessExercise.objects.filter(category="grounding"),
        "recent_reflections": CBTReflection.objects.filter(user=request.user)[:3],
    })


# ------------------------------------------------------------------ grounding
@login_required
def grounding_list(request):
    exercises = WellnessExercise.objects.filter(category="grounding")
    return render(request, "exercises/grounding_list.html", {"exercises": exercises})


@login_required
def grounding_detail(request, slug):
    exercise = get_object_or_404(WellnessExercise, slug=slug, category="grounding")
    return render(request, "exercises/grounding_detail.html", {"exercise": exercise})


# ------------------------------------------------------------------ breathing & instant relief
@login_required
def breathing(request):
    return render(request, "exercises/breathing.html")


@login_required
def relief(request):
    return render(request, "exercises/relief.html")


# ------------------------------------------------------------------ CBT
@login_required
def cbt_list(request):
    return render(request, "exercises/cbt_list.html", {
        "reflections": CBTReflection.objects.filter(user=request.user),
    })


def _ai_feedback(reflection):
    """Short supportive AI comment on a finished exercise. Never raises."""
    combined = " ".join([reflection.situation, reflection.automatic_thought, reflection.evidence_for,
                         reflection.evidence_against, reflection.balanced_thought, reflection.reflection])
    if safety.assess_message(combined).is_high_risk:
        return safety.build_crisis_response()
    if not llm_client.is_configured():
        return ""
    messages_ = [
        {"role": "system", "content": prompts.SYSTEM_PROMPT + "\n" + prompts.CBT_FEEDBACK_PROMPT},
        {"role": "user", "content": (
            f"Situation: {reflection.situation}\nAutomatic thought: {reflection.automatic_thought}\n"
            f"Evidence for: {reflection.evidence_for}\nEvidence against: {reflection.evidence_against}\n"
            f"Balanced thought: {reflection.balanced_thought}\nReflection: {reflection.reflection}")},
    ]
    try:
        feedback = llm_client.generate_reply(messages_, max_tokens=250)
    except llm_client.LLMError:
        return ""
    return feedback if safety.is_output_safe(feedback) else ""


@login_required
def cbt_new(request):
    form = CBTReflectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        reflection = form.save(commit=False)
        reflection.user = request.user
        reflection.ai_feedback = _ai_feedback(reflection)
        reflection.save()
        messages.success(request, "Your reflection was saved.")
        return redirect("exercises:cbt_detail", pk=reflection.pk)
    wizard_steps = [{"field": form[name], "title": title, "help": help_text} for name, title, help_text in CBT_STEPS]
    return render(request, "exercises/cbt_form.html", {"form": form, "steps": wizard_steps})


@login_required
def cbt_detail(request, pk):
    reflection = get_object_or_404(CBTReflection, pk=pk, user=request.user)  # owner-only
    sections = [{"title": title, "text": getattr(reflection, name)} for name, title, _ in CBT_STEPS]
    return render(request, "exercises/cbt_detail.html", {"reflection": reflection, "sections": sections})


@login_required
@require_POST
def cbt_delete(request, pk):
    reflection = get_object_or_404(CBTReflection, pk=pk, user=request.user)
    reflection.delete()
    messages.success(request, "Reflection deleted.")
    return redirect("exercises:cbt_list")
