"""Validação de saídas de LLM contra JSON Schema com heurísticas de correção."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Any
import json

from dateutil import parser as date_parser
from jsonschema import Draft202012Validator, FormatChecker

from schemas.campos_canonicos import LicitacaoCanonica, campo_json_schemas


@dataclass
class ExtractionAttemptResult:
    """Representa o resultado de uma tentativa de extração."""

    ok: bool
    value: dict | None
    errors: List[str]
    attempts: int


class CampoValidator:
    """Valida saídas de extração utilizando o JSON Schema canônico."""

    def __init__(self) -> None:
        self.schemas = campo_json_schemas()
        self.root_schema = LicitacaoCanonica.model_json_schema()
        self.definitions = self.root_schema.get("$defs", {}) or self.root_schema.get(
            "definitions", {}
        )
        self._format_checker = FormatChecker()

    def build_output_schema(self, field: str) -> dict:
        if field not in self.schemas:
            raise KeyError(f"Campo não suportado: {field}")

        return {
            "type": "object",
            "required": ["field", "value"],
            "properties": {
                "field": {"const": field},
                "value": self.schemas[field],
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "evidence": {"type": "string"},
            },
            "$defs": self.definitions,
            "additionalProperties": False,
        }

    def validate(self, field: str, payload: dict) -> List[str]:
        """Retorna lista de erros de validação (vazia quando ok)."""

        schema = self.build_output_schema(field)
        validator = Draft202012Validator(schema, format_checker=self._format_checker)
        errors: List[str] = []
        for error in validator.iter_errors(payload):
            errors.append(error.message)
        return errors

    def heuristic_repair(self, field: str, raw_value: Any) -> dict | None:
        """Aplica heurísticas determinísticas para salvar respostas parcialmente válidas."""

        if field not in self.schemas:
            return None

        base = {"field": field, "value": None, "confidence": 0.0}
        schema = self.schemas[field]

        if isinstance(raw_value, dict):
            candidate_value = raw_value.get("value", raw_value)
        else:
            candidate_value = raw_value

        # Enum
        if "enum" in schema:
            coerced = self._coerce_enum(candidate_value, schema["enum"])
            if coerced:
                base["value"] = coerced
                return base

        # Strings simples
        if schema.get("type") == "string":
            base["value"] = self._coerce_string(candidate_value)
            return base

        # Objetos com propriedades conhecidas
        if schema.get("type") == "object":
            repaired = self._coerce_object(schema, candidate_value)
            if repaired:
                base["value"] = repaired
                return base

        # Listas de objetos
        if schema.get("type") == "array" and "items" in schema:
            repaired = self._coerce_array(schema, candidate_value)
            if repaired is not None:
                base["value"] = repaired
                return base

        return None

    @staticmethod
    def _coerce_string(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _coerce_enum(value: Any, allowed: List[str]) -> str | None:
        if value is None:
            return None
        candidate = str(value).lower().strip().replace(" ", "_")
        candidate = candidate.replace("á", "a").replace("ã", "a")
        candidate = candidate.replace("é", "e").replace("ê", "e")
        candidate = candidate.replace("í", "i")
        candidate = candidate.replace("ó", "o").replace("ô", "o")
        candidate = candidate.replace("ú", "u")
        for option in allowed:
            if candidate == option:
                return option
        return None

    def _coerce_object(self, schema: dict, value: Any) -> dict | None:
        if not isinstance(value, dict):
            return None

        repaired: Dict[str, Any] = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for prop, definition in properties.items():
            if prop in value:
                repaired[prop] = self._coerce_property(definition, value[prop])
        for prop in required:
            if prop not in repaired:
                # tentativas específicas para datas ou inteiros
                repaired[prop] = self._default_for_schema(properties.get(prop, {}))

        # Se ainda faltar algo obrigatório e não conseguimos default, falha
        missing_required = [prop for prop in required if repaired.get(prop) is None]
        if missing_required:
            return None
        return repaired

    def _coerce_array(self, schema: dict, value: Any) -> list | None:
        if isinstance(value, list):
            coerced_items = []
            for item in value:
                coerced = self._coerce_property(schema.get("items", {}), item)
                if coerced is None:
                    return None
                coerced_items.append(coerced)
            return coerced_items
        return None

    def _coerce_property(self, definition: dict, value: Any) -> Any:
        if definition.get("type") == "string":
            return self._coerce_string(value)
        if definition.get("type") == "integer":
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        if definition.get("format") == "date-time":
            try:
                parsed = date_parser.parse(str(value))
                return parsed.isoformat()
            except (ValueError, TypeError):
                return None
        if definition.get("type") == "boolean":
            if isinstance(value, bool):
                return value
            if str(value).lower().strip() in {"true", "sim", "yes", "1"}:
                return True
            if str(value).lower().strip() in {"false", "nao", "não", "0"}:
                return False
            return None
        if definition.get("type") == "array":
            return self._coerce_array(definition, value)
        if definition.get("type") == "object":
            return self._coerce_object(definition, value)
        if "enum" in definition:
            return self._coerce_enum(value, definition["enum"])
        return value

    @staticmethod
    def _default_for_schema(definition: dict) -> Any:
        if definition.get("type") == "integer":
            return 0
        if definition.get("type") == "string":
            return ""
        if definition.get("type") == "boolean":
            return False
        return None


def extract_with_validation(
    field: str,
    context: str,
    prompt_builder: Callable[[int, str | None], str],
    generator: Callable[[str], str],
    max_attempts: int = 2,
) -> ExtractionAttemptResult:
    """Executa fluxo de geração + validação, com retry e heurística determinística."""

    validator = CampoValidator()
    errors: List[str] = []
    parsed_payload: dict | None = None

    for attempt in range(1, max_attempts + 1):
        prompt = prompt_builder(attempt, errors[-1] if errors else None)
        raw_response = generator(prompt)
        try:
            parsed_payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            errors.append(f"JSON inválido: {exc.msg}")
            continue

        validation_errors = validator.validate(field, parsed_payload)
        if not validation_errors:
            return ExtractionAttemptResult(True, parsed_payload, errors, attempt)

        errors.extend(validation_errors)

    if parsed_payload is None:
        # última tentativa: heurística sobre a última resposta textual
        repaired = validator.heuristic_repair(field, raw_response if errors else None)
    else:
        repaired = validator.heuristic_repair(field, parsed_payload)

    if repaired and not validator.validate(field, repaired):
        return ExtractionAttemptResult(True, repaired, errors, max_attempts)

    return ExtractionAttemptResult(False, parsed_payload, errors, max_attempts)


__all__ = [
    "CampoValidator",
    "ExtractionAttemptResult",
    "extract_with_validation",
]
