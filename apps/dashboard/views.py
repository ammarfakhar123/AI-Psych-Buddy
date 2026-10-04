from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.ai_assistant import suggestions
from apps.chat.models import Conversation, Message
from apps.mood import services as mood_services
from apps.mood.models import MoodEntry


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return render(request, "landing.html")


@login_required
def home(request):
    today_entry = mood_services.todays_entry(request.user)

    # "AI Wellness Suggestions": based on today's mood and the user's latest chat message.
    last_message = (
        Message.objects.filter(conversation__user=request.user, sender=Message.SENDER_USER)
        .order_by("-timestamp").values_list("message", flat=True).first() or ""
    )
    return render(request, "dashboard/home.html", {
        "today_entry": today_entry,
        "week_trend": mood_services.describe_trend(mood_services.entries_since(request.user, 7)),
        "recent_conversations": Conversation.objects.filter(user=request.user)[:5],
        "recent_moods": MoodEntry.objects.filter(user=request.user)[:5],
        "suggestions": suggestions.suggest(last_message, today_entry.mood if today_entry else None),
        "mood_options": MoodEntry.mood_options(),
        "today": timezone.localdate(),
    })
