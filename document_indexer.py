"""Segmentação de PDFs, geração de embeddings e recuperação contextual.

Divide editais em seções estruturadas (capítulos, itens, anexos), detecta
tabelas de forma heurística, gera embeddings por seção com referências de
página/parágrafo e expõe uma função de consulta para recuperar as seções mais
relevantes para um campo específico antes de acionar um LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import sqrt
from typing import Dict, Iterable, List, Optional, Sequence
import os
import re
import uuid

import fitz
from openai import OpenAI

# Regex patterns used to find structural markers in the text
HEADING_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(r"^(CAP[ÍI]TULO|Cap[íi]tulo)\s+\w+"),
    re.compile(r"^(ANEXO|Anexo)\s+[A-Z0-9]+"),
    re.compile(r"^(Item|ITEM)\s+\d+[\.\d]*"),
    re.compile(r"^\d+(\.\d+)*\s*[-–]?\s+\S+"),
)


@dataclass
class Section:
    """Represents a logical section of the document."""

    id: str
    title: str
    content: str
    page_start: int
    page_end: int
    paragraph_indices: List[int]
    section_type: str = "text"  # "text" or "table"

    def to_record(self) -> Dict[str, object]:
        return asdict(self)


def _is_heading(line: str) -> bool:
    candidate = line.strip()
    if not candidate:
        return False
    return any(pattern.search(candidate) for pattern in HEADING_PATTERNS)


def _is_table_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if "|" in stripped and stripped.count("|") >= 2:
        return True
    # Detect multiple spaced columns (at least two large gaps)
    return len(re.findall(r"\s{2,}", stripped)) >= 2 and len(stripped.split()) >= 3


def _join_lines(lines: Iterable[str]) -> str:
    return "\n".join(l.strip() for l in lines if l.strip())


def segment_pdf_by_structure(pdf_path: str) -> List[Section]:
    """
    Split a PDF into logical sections using headings, numbering and table markers.

    Args:
        pdf_path: Absolute or relative path to a PDF file.

    Returns:
        List of :class:`Section` objects with page/paragraph references.
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    sections: List[Section] = []
    current_section: Optional[Section] = None
    paragraph_index = 0

    with fitz.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text")
            lines = text.splitlines()
            cursor = 0

            while cursor < len(lines):
                line = lines[cursor]
                if _is_heading(line):
                    if current_section:
                        current_section.page_end = page_number
                        sections.append(current_section)
                    current_section = Section(
                        id=str(uuid.uuid4()),
                        title=line.strip(),
                        content="",
                        page_start=page_number,
                        page_end=page_number,
                        paragraph_indices=[],
                        section_type="text",
                    )
                    cursor += 1
                    continue

                if _is_table_line(line):
                    table_lines = [line]
                    cursor += 1
                    while cursor < len(lines) and _is_table_line(lines[cursor]):
                        table_lines.append(lines[cursor])
                        cursor += 1
                    sections.append(
                        Section(
                            id=str(uuid.uuid4()),
                            title=current_section.title if current_section else "Tabela",
                            content=_join_lines(table_lines),
                            page_start=page_number,
                            page_end=page_number,
                            paragraph_indices=list(range(paragraph_index, paragraph_index + len(table_lines))),
                            section_type="table",
                        )
                    )
                    paragraph_index += len(table_lines)
                    continue

                if current_section is None:
                    current_section = Section(
                        id=str(uuid.uuid4()),
                        title="Corpo do Documento",
                        content="",
                        page_start=page_number,
                        page_end=page_number,
                        paragraph_indices=[],
                        section_type="text",
                    )

                current_section.content += ("\n" if current_section.content else "") + line.strip()
                current_section.paragraph_indices.append(paragraph_index)
                paragraph_index += 1
                current_section.page_end = page_number
                cursor += 1

    if current_section:
        sections.append(current_section)

    return sections


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Embeddings com tamanhos diferentes")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def generate_section_embeddings(
    sections: Sequence[Section],
    model: str = "text-embedding-3-small",
    client: Optional[OpenAI] = None,
) -> List[Dict[str, object]]:
    """Build embeddings for each section and attach references (page, index)."""

    openai_client = client or OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    records: List[Dict[str, object]] = []

    for section in sections:
        content = section.content.strip()
        if not content:
            continue
        response = openai_client.embeddings.create(model=model, input=content)
        embedding = response.data[0].embedding
        record = section.to_record()
        record["embedding"] = embedding
        records.append(record)

    return records


def query_top_k_sections(
    query: str,
    embedded_sections: Sequence[Dict[str, object]],
    field: Optional[str] = None,
    field_keywords: Optional[Dict[str, Sequence[str]]] = None,
    top_k: int = 3,
    model: str = "text-embedding-3-small",
    client: Optional[OpenAI] = None,
) -> List[Dict[str, object]]:
    """
    Retrieve the top-k most relevant sections for a given field before LLM usage.

    Args:
        query: Natural language query that will be embedded.
        embedded_sections: Iterable of section records containing an ``embedding`` key.
        field: Optional field name (e.g., "objeto", "vigencia"). Used to pre-filter
            sections whose title matches configured keywords.
        field_keywords: Optional mapping from field name to keywords that must appear
            in the section title. If omitted, a conservative default is used.
        top_k: Number of sections to return.
        model: Embedding model to use for the query.
        client: Optional OpenAI client (allows dependency injection for tests).
    """

    if not embedded_sections:
        return []

    openai_client = client or OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    keywords_map = field_keywords or {
        "objeto": ("objeto", "capítulo", "capitulo"),
        "vigencia": ("vigência", "vigencia", "prazo"),
        "itens": ("item", "itens", "tabela"),
        "anexos": ("anexo", "anexos"),
    }

    query_embedding = (
        openai_client.embeddings.create(model=model, input=query).data[0].embedding
    )

    candidates = list(embedded_sections)
    if field:
        allowed_keywords = keywords_map.get(field.lower())
        if allowed_keywords:
            candidates = [
                record
                for record in candidates
                if any(
                    kw.lower() in str(record.get("title", "")).lower()
                    for kw in allowed_keywords
                )
            ]

    scored = [
        (
            _cosine_similarity(query_embedding, record["embedding"]),
            record,
        )
        for record in candidates
        if "embedding" in record
    ]

    scored.sort(key=lambda item: item[0], reverse=True)
    return [record for _, record in scored[:top_k]]
