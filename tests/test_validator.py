import json
import unittest

from prompt_library.campos import PromptLibrary
from prompt_library.validator import CampoValidator, extract_with_validation


class ValidatorTest(unittest.TestCase):
    def setUp(self):
        self.validator = CampoValidator()
        self.library = PromptLibrary()

    def test_valid_payload_passes_schema(self):
        payload = {
            "field": "prazos",
            "value": {
                "data_abertura": "2024-07-15T10:00:00-03:00",
                "validade_proposta_dias": 60,
            },
            "confidence": 0.9,
            "evidence": "Abertura em 15/07/2024 às 10h, validade das propostas: 60 dias.",
        }

        self.assertEqual([], self.validator.validate("prazos", payload))

    def test_retry_flow_recovers_after_schema_failure(self):
        responses = [
            json.dumps(
                {
                    "field": "modalidade",
                    "value": "Pregao Eletronico",
                    "confidence": 0.4,
                    "evidence": "Modalidade: Pregão Eletrônico",
                }
            ),
            json.dumps(
                {
                    "field": "modalidade",
                    "value": "pregao_eletronico",
                    "confidence": 0.9,
                    "evidence": "Modalidade: Pregão Eletrônico",
                }
            ),
        ]

        def generator(_: str) -> str:
            return responses.pop(0)

        prompt_builder = lambda attempt, reason=None: self.library.render_prompt(
            "modalidade", "Modalidade: Pregão Eletrônico", attempt=attempt, retry_reason=reason
        )

        result = extract_with_validation(
            "modalidade",
            "Modalidade: Pregão Eletrônico",
            prompt_builder,
            generator,
        )

        self.assertTrue(result.ok)
        self.assertEqual("pregao_eletronico", result.value["value"])
        self.assertEqual(2, result.attempts)
        self.assertGreaterEqual(len(result.errors), 1)

    def test_heuristic_coercion_salvages_enum(self):
        responses = [
            json.dumps(
                {
                    "field": "modalidade",
                    "value": "Pregao Eletronico",
                    "confidence": 0.5,
                    "evidence": "Modalidade: Pregão Eletrônico",
                }
            )
        ]

        def generator(_: str) -> str:
            return responses.pop(0)

        prompt_builder = lambda attempt, reason=None: self.library.render_prompt(
            "modalidade", "Modalidade: Pregão Eletrônico", attempt=attempt, retry_reason=reason
        )

        result = extract_with_validation(
            "modalidade",
            "Modalidade: Pregão Eletrônico",
            prompt_builder,
            generator,
            max_attempts=1,
        )

        self.assertTrue(result.ok)
        self.assertEqual("pregao_eletronico", result.value["value"])


if __name__ == "__main__":
    unittest.main()
