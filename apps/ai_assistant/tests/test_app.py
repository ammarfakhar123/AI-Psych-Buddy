"""Integration tests: auth protection, data isolation, pipeline fallbacks (LLM mocked)."""
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.ai_assistant import llm_client, pipeline, safety
from apps.chat.models import Conversation, Message
from apps.exercises.models import CBTReflection
from apps.mood.models import MoodEntry

User = get_user_model()


class AuthAndIsolationTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-Alice-123")
        self.bob = User.objects.create_user("bob", password="pw-Bob-12345")
        self.convo = Conversation.objects.create(user=self.alice, title="Alice private")
        self.reflection = CBTReflection.objects.create(
            user=self.alice, situation="s", automatic_thought="t", evidence_for="f",
            evidence_against="a", balanced_thought="b")

    def test_pages_require_login(self):
        for name in ["dashboard:home", "chat:home", "chat:history", "mood:tracker", "exercises:index",
                     "exercises:breathing", "accounts:profile"]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn("/accounts/login/", response["Location"])

    def test_register_creates_user_and_profile(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "newbie", "email": "n@example.com",
            "password1": "Str0ng-pass-word!", "password2": "Str0ng-pass-word!"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.get(username="newbie").profile)

    def test_user_cannot_read_or_delete_other_users_conversation(self):
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse("chat:detail", args=[self.convo.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("chat:delete", args=[self.convo.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("chat:send", args=[self.convo.pk]),
                                          {"message": "hi"}, content_type="application/json").status_code, 404)
        self.assertTrue(Conversation.objects.filter(pk=self.convo.pk).exists())

    def test_user_cannot_see_other_users_reflection(self):
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse("exercises:cbt_detail", args=[self.reflection.pk])).status_code, 404)

    def test_owner_can_view_and_delete_conversation(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("chat:detail", args=[self.convo.pk])).status_code, 200)
        self.client.post(reverse("chat:delete", args=[self.convo.pk]))
        self.assertFalse(Conversation.objects.filter(pk=self.convo.pk).exists())

    def test_logout_requires_post_and_works(self):
        self.client.force_login(self.alice)
        self.client.post(reverse("accounts:logout"))
        self.assertEqual(self.client.get(reverse("dashboard:home")).status_code, 302)


class MoodTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("m", password="pw-Mood-12345")
        self.client.force_login(self.user)

    def test_one_entry_per_day_is_updated(self):
        url = reverse("mood:tracker")
        self.client.post(url, {"mood": "happy", "score": 5, "note": ""})
        self.client.post(url, {"mood": "sad", "score": 2, "note": "rough"})
        self.assertEqual(MoodEntry.objects.filter(user=self.user).count(), 1)
        self.assertEqual(MoodEntry.objects.get(user=self.user).mood, "sad")

    def test_invalid_score_rejected(self):
        self.client.post(reverse("mood:tracker"), {"mood": "happy", "score": 9})
        self.assertEqual(MoodEntry.objects.count(), 0)

    def test_chart_data_endpoint(self):
        self.client.post(reverse("mood:tracker"), {"mood": "good", "score": 4})
        data = self.client.get(reverse("mood:chart_data") + "?range=7").json()
        self.assertEqual(data["scores"], [4])


class PipelineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("p", password="pw-Pipe-12345")

    @override_settings(LLM_API_KEY="")
    def test_no_api_key_gives_friendly_message(self):
        result = pipeline.generate_response(self.user, "I feel stressed about work")
        self.assertFalse(result.ok)
        self.assertIn("trouble connecting", result.reply)

    def test_empty_input(self):
        self.assertFalse(pipeline.generate_response(self.user, "   ").ok)

    def test_high_risk_skips_llm(self):
        with mock.patch.object(llm_client, "generate_reply") as fake_llm:
            result = pipeline.generate_response(self.user, "I want to kill myself")
        fake_llm.assert_not_called()
        self.assertTrue(result.is_crisis)
        self.assertEqual(result.risk_level, safety.HIGH)

    def test_normal_flow_uses_llm_and_retrieval(self):
        with mock.patch.object(llm_client, "generate_reply", return_value="That sounds tough. Try a slow breath?") as fake_llm, \
                mock.patch("apps.ai_assistant.rag.retriever.retrieve", return_value=[]):
            result = pipeline.generate_response(self.user, "I feel anxious")
        self.assertTrue(result.ok)
        self.assertIn("slow breath", result.reply)
        system_prompt = fake_llm.call_args[0][0][0]["content"]
        self.assertIn("Buddy", system_prompt)

    def test_unsafe_llm_output_is_replaced(self):
        with mock.patch.object(llm_client, "generate_reply", return_value="You have depression. Take 50 mg."), \
                mock.patch("apps.ai_assistant.rag.retriever.retrieve", return_value=[]):
            result = pipeline.generate_response(self.user, "I feel low")
        self.assertNotIn("50 mg", result.reply)

    def test_llm_error_handled(self):
        with mock.patch.object(llm_client, "generate_reply", side_effect=llm_client.LLMError("timeout")), \
                mock.patch("apps.ai_assistant.rag.retriever.retrieve", return_value=[]):
            result = pipeline.generate_response(self.user, "hello there")
        self.assertFalse(result.ok)

    def test_chat_api_saves_messages(self):
        self.client.force_login(self.user)
        convo = Conversation.objects.create(user=self.user)
        with mock.patch.object(llm_client, "generate_reply", return_value="Hello! How are you?"), \
                mock.patch("apps.ai_assistant.rag.retriever.retrieve", return_value=[]):
            response = self.client.post(reverse("chat:send", args=[convo.pk]),
                                        {"message": "hi buddy"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.filter(conversation=convo).count(), 2)
        convo.refresh_from_db()
        self.assertEqual(convo.title, "hi buddy")

    def test_chat_api_rejects_empty_message(self):
        self.client.force_login(self.user)
        convo = Conversation.objects.create(user=self.user)
        response = self.client.post(reverse("chat:send", args=[convo.pk]),
                                    {"message": "  "}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
