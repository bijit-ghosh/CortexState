import unittest
from collections import Counter

from cortexstate.memory import _bm25_score, _rust_rank


class RankerParityTests(unittest.TestCase):
    def test_rust_and_python_scorers_match_reference(self):
        if _rust_rank is None:
            self.skipTest("native Rust extension is optional outside compiled installs")
        query = ["coffee", "morning"]
        document = ["coffee", "coffee", "in", "the", "morning"]
        frequencies = Counter({"coffee": 2, "morning": 1})
        python_score = _bm25_score(query, document, 5, frequencies, 4.2)
        rust_score = _rust_rank.bm25_batch(query, [document], 5, frequencies, 4.2)[0]
        self.assertAlmostEqual(rust_score, python_score, places=14)

    def test_reference_scorer_returns_zero_for_no_match(self):
        self.assertEqual(_bm25_score({"unmatched"}, ["other"], 1, {"unmatched": 0}, 1), 0)


if __name__ == "__main__":
    unittest.main()
