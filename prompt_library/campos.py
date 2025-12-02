"""Prompts canônicos para extração de campos de licitação.

Cada campo possui um prompt especializado com:
- versão explícita (para rastreabilidade e regressão);
- formato de saída JSON estrito e validável via JSON Schema;
- exemplos positivos com confiança simulada e evidências.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import json

from schemas.campos_canonicos import campo_json_schemas

PROMPT_VERSION = "v1.0.0"


@dataclass(frozen=True)
class PromptExample:
    """Exemplo concreto de saída esperada para o campo."""

    context: str
    payload: dict


@dataclass(frozen=True)
class PromptSpec:
    """Metadados e templates de um prompt por campo."""

    name: str
    resumo: str
    schema: dict
    examples: List[PromptExample]


class PromptLibrary:
    """Renderiza prompts estruturados por campo com JSON estrito."""

    def __init__(self) -> None:
        self.schemas = campo_json_schemas()
        self.specs = self._build_specs()

    def _build_specs(self) -> Dict[str, PromptSpec]:
        schemas = self.schemas
        return {
            "objeto": PromptSpec(
                name="objeto",
                resumo="Descrever de forma objetiva o objeto da contratação, evitando verborragia.",
                schema=schemas["objeto"],
                examples=[
                    PromptExample(
                        context="Objeto: aquisição de 50 computadores para laboratórios.",
                        payload={
                            "field": "objeto",
                            "value": "Aquisição de 50 computadores para laboratórios",
                            "evidence": "Objeto: aquisição de 50 computadores para laboratórios.",
                            "confidence": 0.94,
                        },
                    )
                ],
            ),
            "orgao": PromptSpec(
                name="orgao",
                resumo="Identificar o órgão ou entidade pública responsável pelo edital.",
                schema=schemas["orgao"],
                examples=[
                    PromptExample(
                        context="Município de Curitiba - Secretaria Municipal de Educação",
                        payload={
                            "field": "orgao",
                            "value": "Secretaria Municipal de Educação de Curitiba",
                            "evidence": "Município de Curitiba - Secretaria Municipal de Educação",
                            "confidence": 0.9,
                        },
                    )
                ],
            ),
            "modalidade": PromptSpec(
                name="modalidade",
                resumo="Identificar a modalidade da licitação (enum fechado).",
                schema=schemas["modalidade"],
                examples=[
                    PromptExample(
                        context="Modalidade: Pregão Eletrônico",
                        payload={
                            "field": "modalidade",
                            "value": "pregao_eletronico",
                            "evidence": "Modalidade: Pregão Eletrônico",
                            "confidence": 0.93,
                        },
                    )
                ],
            ),
            "tipo_julgamento": PromptSpec(
                name="tipo_julgamento",
                resumo="Apontar o critério de julgamento das propostas (enum fechado).",
                schema=schemas["tipo_julgamento"],
                examples=[
                    PromptExample(
                        context="Tipo de julgamento: menor preço global",
                        payload={
                            "field": "tipo_julgamento",
                            "value": "menor_preco",
                            "evidence": "Tipo de julgamento: menor preço global",
                            "confidence": 0.91,
                        },
                    )
                ],
            ),
            "prazos": PromptSpec(
                name="prazos",
                resumo="Extrair marcos temporais (datas ISO 8601 e prazos em dias/horas).",
                schema=schemas["prazos"],
                examples=[
                    PromptExample(
                        context="Abertura em 15/07/2024 às 10h, validade das propostas: 60 dias.",
                        payload={
                            "field": "prazos",
                            "value": {
                                "data_abertura": "2024-07-15T10:00:00-03:00",
                                "validade_proposta_dias": 60,
                            },
                            "evidence": "Abertura em 15/07/2024 às 10h, validade das propostas: 60 dias.",
                            "confidence": 0.86,
                        },
                    )
                ],
            ),
            "habilitacao": PromptSpec(
                name="habilitacao",
                resumo="Mapear requisitos de habilitação, preenchendo booleans e lista de outros exigências.",
                schema=schemas["habilitacao"],
                examples=[
                    PromptExample(
                        context="Exige regularidade fiscal e declaração ME/EPP; não há visita técnica.",
                        payload={
                            "field": "habilitacao",
                            "value": {
                                "regularidade_fiscal": True,
                                "capacidade_tecnica": True,
                                "qualif_economica": True,
                                "declaracao_me_epp": True,
                                "visitas_tecnicas": False,
                                "outros": None,
                            },
                            "evidence": "Exige regularidade fiscal e declaração ME/EPP; não há visita técnica.",
                            "confidence": 0.84,
                        },
                    )
                ],
            ),
            "anexos": PromptSpec(
                name="anexos",
                resumo="Listar anexos com nome, URL HTTP/HTTPS e se são obrigatórios.",
                schema=schemas["anexos"],
                examples=[
                    PromptExample(
                        context="Anexo I - Termo de Referência disponível em https://compras.gov/anexo1.pdf",
                        payload={
                            "field": "anexos",
                            "value": [
                                {
                                    "nome": "Anexo I - Termo de Referência",
                                    "url": "https://compras.gov/anexo1.pdf",
                                    "obrigatorio": True,
                                }
                            ],
                            "evidence": "Anexo I - Termo de Referência disponível em https://compras.gov/anexo1.pdf",
                            "confidence": 0.82,
                        },
                    )
                ],
            ),
            "penalidades": PromptSpec(
                name="penalidades",
                resumo="Relacionar penalidades previstas com tipo e fundamento legal.",
                schema=schemas["penalidades"],
                examples=[
                    PromptExample(
                        context="Multa de 2% por atraso superior a 5 dias (art. 86 da Lei 8.666/93)",
                        payload={
                            "field": "penalidades",
                            "value": [
                                {
                                    "tipo": "multa_atraso",
                                    "fundamento_legal": "Art. 86 da Lei 8.666/93",
                                    "descricao": "Multa de 2% por atraso superior a 5 dias",
                                }
                            ],
                            "evidence": "Multa de 2% por atraso superior a 5 dias (art. 86 da Lei 8.666/93)",
                            "confidence": 0.8,
                        },
                    )
                ],
            ),
        }

    def render_prompt(
        self,
        field_name: str,
        context: str,
        attempt: int = 1,
        retry_reason: str | None = None,
    ) -> str:
        """Renderiza o prompt para um campo específico.

        Args:
            field_name: nome canônico do campo (ex.: ``objeto``).
            context: trecho ou seção do edital.
            attempt: contador de tentativa para reforçar instruções.
            retry_reason: motivo textual da re-tentativa.
        """

        if field_name not in self.specs:
            raise KeyError(f"Campo não suportado: {field_name}")

        spec = self.specs[field_name]
        reinforcement = ""
        if attempt > 1:
            reinforcement = (
                "\nATENÇÃO: a tentativa anterior falhou pela razão a seguir. Refaça "
                "a extração obedecendo estritamente ao JSON pedido. \n"
                f"Motivo: {retry_reason or 'violação de schema ou JSON inválido.'}\n"
            )

        examples_block = "\n".join(
            self._format_example(example) for example in spec.examples
        )

        output_shape = {
            "field": spec.name,
            "value": "<valor conforme JSON Schema do campo>",
            "confidence": 0.0,
            "evidence": "trecho literal usado como prova",
        }

        prompt = (
            f"[PROMPT_VERSION={PROMPT_VERSION}] Campo: {spec.name}\n"
            f"Objetivo: {spec.resumo}\n"
            "Responda exclusivamente com JSON válido (sem markdown, títulos ou comentários).\n"
            "Formato de saída obrigatório:\n"
            f"{json.dumps(output_shape, ensure_ascii=False, indent=2)}\n"
            "JSON Schema do campo (propriedade `value`):\n"
            f"{json.dumps(spec.schema, ensure_ascii=False, indent=2)}\n"
            "Regras adicionais: \n"
            "- Normalize strings removendo espaços duplos e mantendo acentuação.\n"
            "- Use datas e datetimes em ISO 8601.\n"
            "- Preencha sempre o campo `evidence` com o trecho original.\n"
            "- Use `confidence` entre 0 e 1.\n"
            "Exemplos de resposta correta:\n"
            f"{examples_block}\n"
            f"Contexto do edital:\n{context.strip()}\n"
            "Agora responda apenas com o JSON solicitado."
            f"{reinforcement}"
        )
        return prompt

    def render_all(self, context_placeholder: str = "[TRECHO_DO_EDITAL]") -> Dict[str, str]:
        """Gera todos os prompts com um contexto padrão (usado em testes dourados)."""

        return {
            name: self.render_prompt(name, context_placeholder) for name in sorted(self.specs)
        }

    @staticmethod
    def _format_example(example: PromptExample) -> str:
        serialized = json.dumps(example.payload, ensure_ascii=False, indent=2)
        return (
            "Contexto de exemplo:\n"
            f"{example.context}\n"
            "Saída esperada:\n"
            f"{serialized}\n"
        )


__all__ = ["PromptLibrary", "PromptSpec", "PromptExample", "PROMPT_VERSION"]
