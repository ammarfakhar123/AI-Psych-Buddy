"""Unit tests for the safety layer (no database or network needed)."""
from django.test import SimpleTestCase, override_settings

from apps.ai_assistant import safety


class AssessMessageTests(SimpleTestCase):
    def test_normal_message_is_not_flagged(self):
        for text in ["I had a stressful day at work", "I'm feeling a bit anxious about exams", "", "   "]:
            self.assertEqual(safety.assess_message(text).level, safety.NONE, text)

    def test_high_risk_phrases(self):
        for text in [
            "I want to kill myself",
            "I've been thinking about suicide",
            "I don't want to live anymore",
            "I want to end my life",
            "i keep wanting to hurt myself",
            "everyone would be better off dead",
            "I'm going to overdose tonight",
        ]:
            self.assertTrue(safety.assess_message(text).is_high_risk, text)

    def test_negated_phrases_are_not_high_risk(self):
        for text in ["I would never kill myself", "I'm not suicidal, just tired", "I don't want to die"]:
            self.assertFalse(safety.assess_message(text).is_high_risk, text)

    def test_elevated_risk(self):
        result = safety.assess_message("Everything feels hopeless lately")
        self.assertTrue(result.is_elevated)
        self.assertFalse(result.is_high_risk)

    def test_idioms_not_flagged(self):
        self.assertEqual(safety.assess_message("This homework is killing me").level, safety.NONE)


class CrisisResponseTests(SimpleTestCase):
    @override_settings(CRISIS_RESOURCES=[{"name": "Test Line", "contact": "Dial 123"}])
    def test_resources_are_configurable(self):
        text = safety.build_crisis_response()
        self.assertIn("Test Line", text)
        self.assertIn("Dial 123", text)
        self.assertIn("emergency", text.lower())


class OutputScreenTests(SimpleTestCase):
    def test_blocks_diagnosis_and_medication(self):
        for text in ["You have depression.", "You are clinically depressed.", "Take 50 mg of sertraline.",
                     "I am your therapist."]:
            self.assertFalse(safety.is_output_safe(text), text)

    def test_allows_supportive_text(self):
        self.assertTrue(safety.is_output_safe("That sounds really hard. Would a breathing exercise help?"))
