from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.ai_assistant import suggestions

from . import services
from .forms import MoodEntryForm
from .models import MoodEntry


@login_required
def tracker(request):
    today = timezone.localdate()
    existing = services.todays_entry(request.user)

    if request.method == "POST":
        form = MoodEntryForm(request.POST, instance=existing)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.date = today
            entry.save()
            messages.success(request, "Mood saved. Thanks for checking in.")
            return redirect("mood:tracker")
    else:
        form = MoodEntryForm(instance=existing)

    week = list(services.entries_since(request.user, 7))
    month = list(services.entries_since(request.user, 30))
    history_page = Paginator(MoodEntry.objects.filter(user=request.user), 10).get_page(request.GET.get("page"))

    return render(request, "mood/tracker.html", {
        "form": form,
        "today_entry": existing,
        "week_trend": services.describe_trend(week),
        "month_trend": services.describe_trend(month),
        "history_page": history_page,
        "mood_options": MoodEntry.mood_options(),
        "suggestions": suggestions.suggest(mood=existing.mood if existing else None),
    })


@login_required
def chart_json(request):
    """Data for the Chart.js graph. ?range=7|30"""
    days = 30 if request.GET.get("range") == "30" else 7
    return JsonResponse(services.chart_data(request.user, days))


@login_required
@require_POST
def delete_entry(request, pk):
    entry = get_object_or_404(MoodEntry, pk=pk, user=request.user)  # owner-only
    entry.delete()
    messages.success(request, "Mood entry deleted.")
    return redirect("mood:tracker")
