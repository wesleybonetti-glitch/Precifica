"""Avaliação de parsers de editais com base em anotações canônicas."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Set
import json

from schemas.campos_canonicos import LicitacaoCanonica


@dataclass(frozen=True)
class AnnotatedEdital:
    """Representa um edital anotado manualmente."""

    id: str
    orgao: str
    formato: str
    texto: str
    anotacoes: dict

    @classmethod
    def from_dict(cls, payload: dict) -> "AnnotatedEdital":
        return cls(
            id=payload["id"],
            orgao=payload["orgao"],
            formato=payload["formato"],
            texto=payload["texto"],
            anotacoes=payload["anotacoes"],
        )


def load_annotated_editais(base_path: Path | str = Path("tests/data/annotated_editais")) -> List[AnnotatedEdital]:
    """Carrega o conjunto de editais anotados do disco."""

    directory = Path(base_path)
    examples: List[AnnotatedEdital] = []
    for path in sorted(directory.glob("*.json")):
        with open(path, "r", encoding="utf-8") as handler:
            payload = json.load(handler)
        examples.append(AnnotatedEdital.from_dict(payload))
    return examples


def _normalize_scalar(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return " ".join(value.split()).strip()
    return str(value)


def _normalize_structure(value: object) -> object:
    if isinstance(value, dict):
        return {key: _normalize_structure(val) for key, val in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize_structure(item) for item in value]
    return _normalize_scalar(value)


def _facts_from_value(prefix: str, value: object) -> Set[str]:
    """Transforma o valor em um conjunto de "fatos" atômicos para scoring."""

    facts: Set[str] = set()
    if value is None:
        return facts

    if isinstance(value, dict):
        for key, val in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            facts |= _facts_from_value(next_prefix, val)
        return facts

    if isinstance(value, list):
        for item in value:
            normalized = _normalize_structure(item)
            serialized = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
            facts.add(f"{prefix}[]={serialized}")
        return facts

    facts.add(f"{prefix}={_normalize_scalar(value)}")
    return facts


def _score_field(field: str, expected: object, predicted: object) -> Dict[str, int]:
    expected_facts = _facts_from_value(field, expected)
    predicted_facts = _facts_from_value(field, predicted)

    tp = len(expected_facts & predicted_facts)
    fp = len(predicted_facts - expected_facts)
    fn = len(expected_facts - predicted_facts)

    return {"tp": tp, "fp": fp, "fn": fn, "support": len(expected_facts)}


def _precision(tp: int, fp: int) -> float:
    return tp / (tp + fp) if (tp + fp) else 0.0


def _recall(tp: int, fn: int) -> float:
    return tp / (tp + fn) if (tp + fn) else 0.0


def _f1(tp: int, fp: int, fn: int) -> float:
    precision = _precision(tp, fp)
    recall = _recall(tp, fn)
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def evaluate_parser(
    examples: Iterable[AnnotatedEdital],
    parser_fn: Callable[[AnnotatedEdital], dict],
) -> Dict[str, Dict[str, float]]:
    """Calcula precisão/recall/F1 por campo usando anotações de referência."""

    field_names = list(LicitacaoCanonica.model_fields.keys())
    aggregates: Dict[str, Dict[str, int]] = {
        field: {"tp": 0, "fp": 0, "fn": 0, "support": 0} for field in field_names
    }

    for example in examples:
        predicted = parser_fn(example) or {}
        for field in field_names:
            scores = _score_field(field, example.anotacoes.get(field), predicted.get(field))
            for key, value in scores.items():
                aggregates[field][key] += value

    metrics: Dict[str, Dict[str, float]] = {}
    precisions: List[float] = []
    recalls: List[float] = []
    f1s: List[float] = []

    for field, values in aggregates.items():
        tp, fp, fn, support = (
            values["tp"],
            values["fp"],
            values["fn"],
            values["support"],
        )
        precision = _precision(tp, fp)
        recall = _recall(tp, fn)
        f1 = _f1(tp, fp, fn)

        metrics[field] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "support": support,
        }

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    metrics["macro_avg"] = {
        "precision": sum(precisions) / len(precisions) if precisions else 0.0,
        "recall": sum(recalls) / len(recalls) if recalls else 0.0,
        "f1": sum(f1s) / len(f1s) if f1s else 0.0,
    }

    return metrics


__all__ = [
    "AnnotatedEdital",
    "evaluate_parser",
    "load_annotated_editais",
]
