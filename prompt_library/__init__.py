"""Biblioteca versionada de prompts e utilitários de validação."""

from .campos import PromptLibrary, PromptSpec, PromptExample, PROMPT_VERSION
from .evaluation import AnnotatedEdital, evaluate_parser, load_annotated_editais
from .validator import CampoValidator, ExtractionAttemptResult, extract_with_validation

__all__ = [
    "PromptLibrary",
    "PromptSpec",
    "PromptExample",
    "PROMPT_VERSION",
    "AnnotatedEdital",
    "evaluate_parser",
    "load_annotated_editais",
    "CampoValidator",
    "ExtractionAttemptResult",
    "extract_with_validation",
]
