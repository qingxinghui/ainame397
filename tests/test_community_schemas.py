import unittest

from pydantic import ValidationError

from schemas.community_schemas import PollCreateIn


class CommunitySchemaTests(unittest.TestCase):
    def test_poll_requires_at_least_two_options(self):
        with self.assertRaises(ValidationError):
            PollCreateIn(title="帮我选名字", options=[{"name": "清和"}])

    def test_poll_accepts_generated_name_options(self):
        poll = PollCreateIn(
            title="帮宝宝选名字",
            description="偏好清雅风格",
            options=[{"name": "清和", "moral": "清朗和美"}, {"name": "云舒", "moral": "从容自在"}],
        )
        self.assertEqual(len(poll.options), 2)


if __name__ == "__main__":
    unittest.main()
