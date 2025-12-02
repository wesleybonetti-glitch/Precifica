import json
import unittest

from prompt_library.campos import PromptLibrary, PROMPT_VERSION


class PromptLibraryGoldenTest(unittest.TestCase):
    def test_prompts_match_golden_set(self):
        library = PromptLibrary()
        generated = library.render_all()

        with open("tests/data/golden_prompts_v1.json", "r", encoding="utf-8") as handler:
            golden = json.load(handler)

        self.assertEqual(generated, golden)

    def test_prompt_contains_version_and_reinforcement(self):
        library = PromptLibrary()
        prompt = library.render_prompt(
            "objeto",
            "Trecho de teste",
            attempt=2,
            retry_reason="JSON inválido",
        )

        self.assertIn(f"[PROMPT_VERSION={PROMPT_VERSION}]", prompt)
        self.assertIn("JSON inválido", prompt)
        self.assertIn("Agora responda apenas com o JSON solicitado", prompt)


if __name__ == "__main__":
    unittest.main()
