import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_assistant import pipeline

from .models import Conversation, Message

logger = logging.getLogger(__name__)


def _owned_conversation_or_404(request, pk):
    """Security: only ever fetch conversations that belong to the logged-in user."""
    return get_object_or_404(Conversation, pk=pk, user=request.user)


@login_required
def chat_home(request):
    """Open the most recent conversation, or show an empty-state page."""
    latest = Conversation.objects.filter(user=request.user).first()
    if latest:
        return redirect("chat:detail", pk=latest.pk)
    return render(request, "chat/empty.html")


@login_required
def history(request):
    conversations = Conversation.objects.filter(user=request.user)
    return render(request, "chat/history.html", {"conversations": conversations})


@login_required
@require_POST
def new_conversation(request):
    conversation = Conversation.objects.create(user=request.user)
    return redirect("chat:detail", pk=conversation.pk)


@login_required
def conversation_detail(request, pk):
    conversation = _owned_conversation_or_404(request, pk)
    return render(
        request,
        "chat/conversation.html",
        {
            "conversation": conversation,
            "chat_messages": conversation.messages.all(),
            "sidebar_conversations": Conversation.objects.filter(user=request.user)[:15],
        },
    )


@login_required
@require_POST
def delete_conversation(request, pk):
    conversation = _owned_conversation_or_404(request, pk)
    conversation.delete()
    messages.success(request, "Conversation deleted.")
    return redirect("chat:history")


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)


class SendMessageView(APIView):
    """POST {"message": "..."} -> runs the safety + RAG + LLM pipeline and stores both messages."""

    def post(self, request, pk):
        conversation = _owned_conversation_or_404(request, pk)
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Please type a message before sending."}, status=status.HTTP_400_BAD_REQUEST
            )
        text = serializer.validated_data["message"]

        history_items = [
            {"sender": m.sender, "message": m.message}
            for m in conversation.messages.order_by("-timestamp", "-id")[:10]
        ][::-1]

        result = pipeline.generate_response(request.user, text, history_items)

        try:
            Message.objects.create(conversation=conversation, sender=Message.SENDER_USER, message=text)
            Message.objects.create(
                conversation=conversation, sender=Message.SENDER_ASSISTANT, message=result.reply,
                sources=result.sources, is_crisis=result.is_crisis,
            )
            if conversation.title == "New conversation":
                conversation.title = text[:60] + ("..." if len(text) > 60 else "")
            conversation.save()  # bumps updated_at
        except Exception:
            logger.exception("Could not save chat messages")
            return Response(
                {"error": "Something went wrong saving your message. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        suggestion_payload = []
        for item in result.suggestions:
            suggestion_payload.append({
                "title": item["title"], "description": item["description"], "icon": item["icon"],
                "url": reverse(item["url_name"]) if item["url_name"] else None,
            })
        return Response({
            "reply": result.reply,
            "sources": result.sources,
            "is_crisis": result.is_crisis,
            "ok": result.ok,
            "title": conversation.title,
            "suggestions": [] if result.is_crisis else suggestion_payload,
        })
