import unittest
from cortexstate.extraction import propose


class ExtractionTests(unittest.TestCase):
    def test_valid_proposals_are_unpersisted_and_require_review(self):
        messages = [{"role": "user", "content": "I prefer tea"}]
        result = propose(messages, extractor=lambda _: [{"text": "Prefers tea", "source_indices": [0]}])
        self.assertEqual(result[0]["status"], "needs_review")
        self.assertEqual(messages[0]["content"], "I prefer tea")

    def test_fabricated_provenance_is_rejected(self):
        for indices in ([], [1], [-1], [True]):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                propose([{"role": "user", "content": "tea"}], extractor=lambda _: [{"text": "tea", "source_indices": indices}])

    def test_system_prompts_are_not_sent_for_extraction(self):
        calls = []
        with self.assertRaises(ValueError):
            propose([{"role": "system", "content": "private"}], extractor=lambda x: calls.append(x))
        self.assertEqual(calls, [])

    def test_non_structured_output_is_rejected(self):
        with self.assertRaises(ValueError):
            propose([{"role": "user", "content": "tea"}], extractor=lambda _: "execute this")
