"""The whole GenAI flow in one place (easy to explain in a demo):

User message -> Safety check -> Query processing -> Retriever -> Knowledge context
            -> Prompt (system + personal context + knowledge + history) -> LLM
            -> Output safety screen -> Reply
"""
import logging
from dataclasses import dataclass, field

from django.conf import settings

from . import llm_client, prompts, safety, suggestions
from .rag import retriever

logger = logging.getLogger(__name__)

MAX_USER_MESSAGE_CHARS = 2000
HISTORY_MESSAGES = 10


@dataclass
class PipelineResult:
    reply: str
    sources: list = field(default_factory=list)
    is_crisis: bool = False
    risk_level: str = safety.NONE
    ok: bool = True                       # False when the LLM could not be used
    suggestions: list = field(default_factory=list)


def _personal_context(user):
    """Personalisation block: preferred name, focus areas, recent mood summary."""
    from apps.mood.services import summary_for_prompt

    profile = getattr(user, "profile", None)
    name = profile.friendly_name if profile else user.get_username()
    focus = (profile.support_focus if profile and profile.support_focus else "not specified")
    try:
        mood_summary = summary_for_prompt(user)
    except Exception:  # never let personalisation break the chat
        logger.exception("Could not build mood summary")
        mood_summary = "unavailable"
    return prompts.PERSONAL_CONTEXT_TEMPLATE.format(name=name, focus=focus, mood_summary=mood_summary)


def _knowledge_block(chunks):
    if not chunks:
        return prompts.NO_CONTEXT_NOTE
    joined = "\n\n---\n\n".join(c.text for c in chunks)
    return prompts.CONTEXT_TEMPLATE.format(knowledge=joined)


def build_messages(user, user_text, history, chunks, elevated=False):
    """Assemble the chat messages sent to the LLM."""
    system = prompts.SYSTEM_PROMPT
    if elevated:
        system += prompts.ELEVATED_RISK_ADDENDUM
    system += "\n\n" + _personal_context(user) + "\n\n" + _knowledge_block(chunks)

    messages = [{"role": "system", "content": system}]
    for item in history[-HISTORY_MESSAGES:]:
        role = "assistant" if item["sender"] == "assistant" else "user"
        messages.append({"role": role, "content": item["message"]})
    messages.append({"role": "user", "content": user_text})
    return messages


def generate_response(user, user_text, history=None):
    """Run the full pipeline.

    `history` is a list of {"sender": "user"|"assistant", "message": str} (oldest first)
    that does NOT include the current user_text.
    """
    history = history or []
    user_text = (user_text or "").strip()
    if not user_text:
        return PipelineResult(reply=prompts.EMPTY_INPUT_MESSAGE, ok=False)
    user_text = user_text[:MAX_USER_MESSAGE_CHARS]

    # 1) Safety check - high risk never reaches the LLM.
    assessment = safety.assess_message(user_text)
    if assessment.is_high_risk:
        return PipelineResult(
            reply=safety.build_crisis_response(), is_crisis=True, risk_level=safety.HIGH,
        )

    # 2) Query processing + 3) retrieval (failures simply mean "no context").
    previous_user_texts = [h["message"] for h in history if h["sender"] == "user"]
    query = retriever.process_query(user_text, previous_user_texts)
    chunks = retriever.retrieve(query, top_k=settings.RAG_TOP_K)
    logger.info("RAG: %d relevant chunk(s) retrieved.", len(chunks))

    # 4) Prompt + LLM
    messages = build_messages(user, user_text, history, chunks, elevated=assessment.is_elevated)
    sources = list(dict.fromkeys(f"{c.title} ({c.category})" for c in chunks))
    try:
        reply = llm_client.generate_reply(messages)
    except llm_client.LLMError as exc:
        logger.warning("LLM unavailable: %s", exc)
        return PipelineResult(
            reply=exc.user_message, risk_level=assessment.level, ok=False,
            suggestions=suggestions.suggest(user_text),
        )

    # 5) Output screening
    if not safety.is_output_safe(reply):
        reply = prompts.UNSAFE_OUTPUT_FALLBACK
        sources = []

    return PipelineResult(
        reply=reply, sources=sources, risk_level=assessment.level,
        suggestions=suggestions.suggest(user_text),
    )
