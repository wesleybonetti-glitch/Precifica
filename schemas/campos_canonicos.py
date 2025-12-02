"""Modelos canônicos para campos de licitação.

Este módulo define uma lista de campos padronizados para editais e pregões,
com estruturas Pydantic e JSON Schema para validação automatizada.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, NonNegativeInt, PositiveInt, constr


class Modalidade(str, Enum):
    """Enumeração de modalidades de licitação previstas em lei."""

    CONCORRENCIA = "concorrencia"
    PREGAO_ELETRONICO = "pregao_eletronico"
    PREGAO_PRESENCIAL = "pregao_presencial"
    TOMADA_PRECOS = "tomada_precos"
    CONCURSO = "concurso"
    REGISTRO_PRECO = "registro_preco"
    DISPENSA = "dispensa"
    INEXIGIBILIDADE = "inexigibilidade"


class TipoJulgamento(str, Enum):
    """Formas de julgamento admitidas."""

    MENOR_PRECO = "menor_preco"
    MAIOR_DESCONTO = "maior_desconto"
    MAIOR_LANCE = "maior_lance"
    MELHOR_TECNICA = "melhor_tecnica"
    TECNICA_E_PRECO = "tecnica_e_preco"
    MAIOR_OFERTA = "maior_oferta"


class Anexo(BaseModel):
    """Arquivos de referência do processo."""

    nome: constr(min_length=3, strip_whitespace=True) = Field(
        ..., description="Nome do arquivo ou documento referenciado."
    )
    url: HttpUrl = Field(
        ..., description="URL oficial ou hash de acesso ao anexo."
    )
    obrigatorio: bool = Field(
        False, description="Indica se o envio ou ciência do anexo é obrigatório."
    )


class Penalidade(BaseModel):
    """Penalidades aplicáveis ao descumprimento contratual ou editalício."""

    tipo: constr(min_length=3, strip_whitespace=True) = Field(
        ..., description="Tipo de penalidade, e.g., multa_atraso, impedimento_licitar."
    )
    fundamento_legal: constr(min_length=3, strip_whitespace=True) = Field(
        ..., description="Citação do artigo ou dispositivo legal."
    )
    descricao: Optional[constr(min_length=5, strip_whitespace=True)] = Field(
        None, description="Descrição complementar do gatilho da penalidade."
    )


class Habilitacao(BaseModel):
    """Requisitos de habilitação exigidos."""

    regularidade_fiscal: bool = Field(
        True, description="Exige comprovação de regularidade fiscal e trabalhista."
    )
    capacidade_tecnica: bool = Field(
        True, description="Exige atestados de capacidade técnica compatíveis."
    )
    qualif_economica: bool = Field(
        True, description="Exige demonstrações econômicas/financeiras."
    )
    declaracao_me_epp: bool = Field(
        False, description="Permite tratamento favorecido a ME/EPP (LC 123/06)."
    )
    visitas_tecnicas: bool = Field(
        False, description="Prevê visita técnica prévia como requisito."
    )
    outros: Optional[List[constr(min_length=3, strip_whitespace=True)]] = Field(
        default=None, description="Lista de exigências adicionais específicas."
    )


class Prazos(BaseModel):
    """Marcos temporais relevantes."""

    data_abertura: datetime = Field(
        ..., description="Data/hora de abertura da sessão ou recebimento de propostas."
    )
    data_limite_esclarecimentos: Optional[datetime] = Field(
        None, description="Data limite para pedidos de esclarecimento."
    )
    data_limite_impugnacao: Optional[datetime] = Field(
        None, description="Data limite para impugnação do edital."
    )
    validade_proposta_dias: PositiveInt = Field(
        ..., description="Número de dias de validade mínima das propostas."
    )
    prazo_execucao_dias: Optional[PositiveInt] = Field(
        None, description="Prazo máximo para execução/entrega do objeto."
    )
    prazo_entrega_documentos_horas: Optional[NonNegativeInt] = Field(
        None, description="Prazo (em horas) para envio de documentos de habilitação."
    )


class LicitacaoCanonica(BaseModel):
    """Agregador de campos canônicos para licitações."""

    objeto: constr(min_length=10, strip_whitespace=True) = Field(
        ..., description="Descrição sucinta e objetiva do objeto da contratação."
    )
    orgao: constr(min_length=3, strip_whitespace=True) = Field(
        ..., description="Órgão ou entidade responsável pela licitação."
    )
    modalidade: Modalidade = Field(..., description="Modalidade de licitação adotada.")
    tipo_julgamento: TipoJulgamento = Field(
        ..., description="Critério de julgamento das propostas."
    )
    prazos: Prazos = Field(..., description="Conjunto de marcos temporais relevantes.")
    habilitacao: Habilitacao = Field(..., description="Requisitos de habilitação exigidos.")
    anexos: List[Anexo] = Field(
        default_factory=list,
        description="Relação de anexos ou arquivos complementares ao edital."
    )
    penalidades: List[Penalidade] = Field(
        default_factory=list,
        description="Penalidades previstas em caso de descumprimento."
    )


def campo_json_schemas() -> dict:
    """Retorna o JSON Schema individualizado para cada campo da licitação.

    As definições reutilizam o schema raiz do modelo ``LicitacaoCanonica``
    para manter consistência entre validações de campo e de payload completo.
    """

    schema = LicitacaoCanonica.model_json_schema(ref_template="#/definitions/{model}")
    definitions = schema.get("definitions", {})
    properties = schema.get("properties", {})

    resolved = {}
    for name, definition in properties.items():
        if "$ref" in definition:
            ref = definition["$ref"].split("/")[-1]
            resolved[name] = definitions.get(ref, definition)
        else:
            resolved[name] = definition
    return resolved


__all__ = [
    "Anexo",
    "Habilitacao",
    "LicitacaoCanonica",
    "Modalidade",
    "Penalidade",
    "Prazos",
    "TipoJulgamento",
    "campo_json_schemas",
]
