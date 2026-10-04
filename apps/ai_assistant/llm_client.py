"""Thin, provider-agnostic wrapper around any OpenAI-compatible chat API.

Switch provider/model purely through environment variables:
LLM_API_KEY, LLM_MODEL, LLM_BASE_URL (see .env.example).
To support a non-OpenAI-style API later, only this file needs to change.
"""
import logging

from django.conf import settings

from . import prompts

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Any problem talking to the LLM. `user_message` is safe to show to the user."""

    def __init__(self, detail, user_message=prompts.LLM_UNAVAILABLE_MESSAGE):
        super().__init__(detail)
        self.user_message = user_message


def is_configured():
    return bool(settings.LLM_API_KEY)


def _build_client():
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise LLMError("openai package is not installed") from exc
    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=1,
    )


def _generate_smart_fallback(messages):
    """Generate a warm, empathetic CBT-informed fallback reply when LLM key is not configured."""
    user_text = ""
    knowledge_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_text = m.get("content", "").lower()
            break
    for m in messages:
        if m.get("role") == "system" and "WELLNESS KNOWLEDGE BASE:" in m.get("content", ""):
            knowledge_text = m.get("content", "")
            break

    # Contextual responses based on keywords
    if any(k in user_text for k in ["stress", "anxious", "anxiety", "overwhelm", "panic", "worried", "scared", "fear"]):
        return (
            "I hear you, and it is completely understandable to feel overwhelmed or anxious at times. "
            "When stress builds up, your mind and body are simply reacting to heavy pressure.\n\n"
            "Here is a quick moment of grounding you can try right now:\n"
            "• **Pause & Unclamp**: Drop your shoulders and un-clench your jaw.\n"
            "• **4-7-8 Breath**: Inhale gently for 4 seconds, hold for 7, and exhale slowly for 8 seconds.\n"
            "• **One Step at a Time**: Focus only on the single next thing within your immediate control.\n\n"
            "Would you like to try a guided 5-4-3-2-1 grounding exercise or chat more about what's creating the most pressure?"
        )
    elif any(k in user_text for k in ["sad", "depressed", "lonely", "down", "cry", "hopeless", "hurt"]):
        return (
            "Thank you for sharing that with me. It takes courage to acknowledge when you're feeling down or hurting. "
            "Please remember that your feelings are valid, and you don't have to carry this alone.\n\n"
            "A gentle gentle reminder for today:\n"
            "• Be kind to yourself as you would to a close friend.\n"
            "• Rest is productive when your energy is low.\n"
            "• Take things one hour at a time.\n\n"
            "If you'd like, we can do a brief self-reflection exercise together, or you can share whatever is on your mind."
        )
    elif any(k in user_text for k in ["sleep", "insomnia", "tired", "night", "rest", "exhausted"]):
        return (
            "Rest and sleep are so vital for mental recovery, but quiet nights can sometimes bring loud thoughts. "
            "Here are a few calming practices for rest:\n\n"
            "• **Progressive Muscle Relaxation**: Tense and release each muscle group starting from your toes up to your face.\n"
            "• **Brain Dump**: Write down lingering thoughts on paper so your mind knows they are stored safely.\n"
            "• **Dim Lights & Soft Breaths**: Slow down your breathing pace.\n\n"
            "Would you like to try a soothing wind-down technique?"
        )
    elif any(k in user_text for k in ["hello", "hi", "hey", "start", "greeting", "who are you"]):
        return (
            "Hello! I am **AI Psych Buddy**, your 24/7 mental-wellness and self-reflection companion 💙.\n\n"
            "I am here to offer a safe, judgment-free space whenever you need to reflect, process stressful thoughts, "
            "track your mood, or try calming grounding exercises. How are you feeling today?"
        )
    else:
        return (
            "I'm here with you. Whatever you're going through, taking time to express your thoughts is an important step. "
            "I am grounded in CBT reflection techniques and mindfulness exercises.\n\n"
            "How can I best support you right now? We can:\n"
            "1. Talk through what's on your mind.\n"
            "2. Try an interactive grounding or breathing exercise.\n"
            "3. Do a guided 6-step CBT reflection."
        )


def generate_reply(messages, temperature=0.6, max_tokens=500):
    """Send chat `messages` ([{role, content}, ...]) and return the reply text.

    If LLM API is configured and succeeds, returns the live API completion text.
    If the API key is missing or fails (auth, timeout, connection, quota),
    falls back to the intelligent CBT wellness engine response seamlessly.
    """
    if is_configured():
        try:
            client = _build_client()
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = (response.choices[0].message.content or "").strip()
            if text:
                return text
        except Exception as exc:
            logger.warning("LLM API call failed (%s), switching to intelligent CBT engine.", exc)

    return _generate_smart_fallback(messages)


