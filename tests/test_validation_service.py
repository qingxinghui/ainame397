import unittest

from core.validation_service import build_domain_stems


class ValidationServiceTests(unittest.TestCase):
    def test_english_name_and_custom_stems_are_normalized(self):
        result = build_domain_stems("Nova Lab", ["Nova-AI", "Nova-AI"])
        self.assertIn(("novalab", "custom"), result)
        self.assertEqual(result.count(("nova-ai", "custom")), 1)

    def test_unsafe_domain_characters_are_removed(self):
        result = build_domain_stems("A&B 品牌", [" My Brand! "])
        self.assertIn(("ab", "custom"), result)
        self.assertIn(("mybrand", "custom"), result)


if __name__ == "__main__":
    unittest.main()
