import unittest

from prompt_library.evaluation import AnnotatedEdital, evaluate_parser, load_annotated_editais


class ParserEvaluationTest(unittest.TestCase):
    def setUp(self):
        self.examples = load_annotated_editais()

    def test_dataset_has_diverse_examples(self):
        orgaos = {example.orgao for example in self.examples}
        formatos = {example.formato for example in self.examples}

        self.assertGreaterEqual(len(self.examples), 3)
        self.assertGreaterEqual(len(orgaos), 3)
        self.assertGreaterEqual(len(formatos), 3)

    def test_perfect_parser_reaches_one_scores(self):
        metrics = evaluate_parser(self.examples, lambda example: example.anotacoes)

        for field, values in metrics.items():
            if field == "macro_avg":
                continue
            self.assertAlmostEqual(1.0, values["precision"])
            self.assertAlmostEqual(1.0, values["recall"])
            self.assertAlmostEqual(1.0, values["f1"])

    def test_missing_predictions_penalized(self):
        metrics = evaluate_parser(self.examples, lambda example: {})

        for field, values in metrics.items():
            if field == "macro_avg":
                continue
            self.assertEqual(0.0, values["precision"])
            self.assertEqual(0.0, values["recall"])
            self.assertEqual(0.0, values["f1"])

        self.assertLess(metrics["macro_avg"]["f1"], 0.1)


if __name__ == "__main__":
    unittest.main()
