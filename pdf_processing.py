"""Ferramentas avançadas de leitura de editais em PDF.

Centraliza a detecção de páginas (texto x imagem), extração com OCR em
português e inglês, normalização de texto e extração de tabelas com
múltiplos backends.
"""
from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

import fitz

# Limiares heurísticos para classificar páginas
TEXT_DENSITY_THRESHOLD = 0.009
TEXT_CHAR_THRESHOLD = 10


@dataclass
class TextBox:
    bbox: List[float]
    text: str
    source: str = "text"


@dataclass
class PageAnalysis:
    page_number: int
    density: float
    char_count: int
    has_text: bool
    label: str
    boxes: List[TextBox] = field(default_factory=list)


@dataclass
class TableExtraction:
    page: int
    source: str
    rows: List[List[str]]
    columns: Optional[List[str]] = None
    bbox: Optional[List[float]] = None


@dataclass
class PDFContent:
    classification: str
    pages: List[PageAnalysis]
    tables: List[TableExtraction]

    @property
    def texto_completo(self) -> str:
        return "\n".join(
            box.text for page in self.pages for box in page.boxes if box.text.strip()
        )


def _import_camelot():
    try:
        import camelot

        return camelot
    except Exception:
        return None


def _import_tabula():
    try:
        import tabula

        return tabula
    except Exception:
        return None


def _import_pytesseract():
    try:
        import pytesseract

        return pytesseract
    except Exception:
        return None


def _import_paddleocr():
    try:
        from paddleocr import PaddleOCR

        return PaddleOCR
    except Exception:
        return None


def normalize_text(text: str) -> str:
    linhas = text.split("\n")
    normalizadas: List[str] = []
    buffer = ""
    for linha in linhas:
        linha_limpa = linha.strip()
        if not linha_limpa:
            if buffer:
                normalizadas.append(buffer)
                buffer = ""
            normalizadas.append("")
            continue

        if linha_limpa.endswith("-") and len(linha_limpa) > 1:
            buffer += linha_limpa[:-1]
            continue

        if buffer:
            linha_limpa = f"{buffer}{linha_limpa}"
            buffer = ""

        linha_limpa = " ".join(linha_limpa.split())
        normalizadas.append(linha_limpa)

    if buffer:
        normalizadas.append(buffer)

    return "\n".join(normalizadas).strip()


def detectar_tipo_paginas(caminho_pdf: str) -> List[PageAnalysis]:
    doc = fitz.open(caminho_pdf)
    analises: List[PageAnalysis] = []
    for indice, pagina in enumerate(doc):
        blocos = pagina.get_text("blocks")
        char_count = sum(len(bloco[4]) for bloco in blocos if len(bloco) >= 5)
        area_total = float(pagina.rect.width * pagina.rect.height) or 1.0
        density = char_count / area_total
        has_text = density >= TEXT_DENSITY_THRESHOLD or char_count >= TEXT_CHAR_THRESHOLD
        label = "text" if has_text else "image"

        boxes = [
            TextBox(bbox=list(bloco[:4]), text=normalize_text(bloco[4]), source="text")
            for bloco in blocos
            if len(bloco) >= 5 and bloco[4].strip()
        ]
        analises.append(
            PageAnalysis(
                page_number=indice + 1,
                density=density,
                char_count=char_count,
                has_text=has_text,
                label=label,
                boxes=boxes,
            )
        )
    doc.close()
    return analises


def classificar_documento(analises: List[PageAnalysis]) -> str:
    if not analises:
        return "desconhecido"
    textos = sum(1 for a in analises if a.has_text)
    imagens = len(analises) - textos
    if textos and imagens:
        return "misto"
    if textos:
        return "texto"
    return "imagem"


def _run_ocr_on_page(pagina: fitz.Page, idiomas: str = "por+eng") -> List[TextBox]:
    pytesseract = _import_pytesseract()
    PaddleOCR = _import_paddleocr()
    imagem = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
    image_bytes = imagem.tobytes("png")

    if pytesseract:
        from PIL import Image

        data = pytesseract.image_to_data(
            Image.open(io.BytesIO(image_bytes)), lang=idiomas, output_type=pytesseract.Output.DICT
        )
        boxes: List[TextBox] = []
        for i, texto in enumerate(data.get("text", [])):
            if not texto.strip():
                continue
            bbox = [
                data["left"][i],
                data["top"][i],
                data["left"][i] + data["width"][i],
                data["top"][i] + data["height"][i],
            ]
            boxes.append(TextBox(bbox=bbox, text=normalize_text(texto), source="ocr"))
        if boxes:
            return boxes

    if PaddleOCR:
        ocr = PaddleOCR(lang="pt", use_angle_cls=True, show_log=False)
        results = ocr.ocr(image_bytes, cls=True)
        boxes: List[TextBox] = []
        for linha in results[0]:
            bbox_coords = [coord for ponto in linha[0] for coord in ponto]
            texto = linha[1][0]
            boxes.append(TextBox(bbox=bbox_coords, text=normalize_text(texto), source="ocr"))
        return boxes

    return []


def extrair_texto_avancado(caminho_pdf: str, idiomas_ocr: str = "por+eng") -> PDFContent:
    analises = detectar_tipo_paginas(caminho_pdf)
    classificacao = classificar_documento(analises)

    doc = fitz.open(caminho_pdf)
    for indice, pagina in enumerate(doc):
        analise_pagina = analises[indice]
        if not analise_pagina.has_text:
            caixas_ocr = _run_ocr_on_page(pagina, idiomas=idiomas_ocr)
            if caixas_ocr:
                analise_pagina.boxes.extend(caixas_ocr)
                analise_pagina.label = "ocr"
    doc.close()

    tabelas = extrair_tabelas(caminho_pdf)
    return PDFContent(classification=classificacao, pages=analises, tables=tabelas)


def extrair_tabelas(caminho_pdf: str) -> List[TableExtraction]:
    tabelas: List[TableExtraction] = []
    camelot = _import_camelot()
    tabula = _import_tabula()

    if camelot:
        try:
            for flavor in ("lattice", "stream"):
                try:
                    tables = camelot.read_pdf(caminho_pdf, flavor=flavor, pages="1-end")
                except Exception:
                    continue
                for tabela in tables:
                    tabelas.append(
                        TableExtraction(
                            page=tabela.page,
                            source=f"camelot-{flavor}",
                            rows=tabela.df.values.tolist(),
                            columns=list(tabela.df.columns),
                        )
                    )
        except Exception:
            pass

    if not tabelas and tabula:
        try:
            dfs = tabula.read_pdf(caminho_pdf, pages="all", multiple_tables=True)
            for idx, df in enumerate(dfs):
                tabelas.append(
                    TableExtraction(
                        page=idx + 1, source="tabula", rows=df.values.tolist(), columns=list(df.columns)
                    )
                )
        except Exception:
            pass

    if not tabelas:
        tabelas.extend(_extrair_tabelas_por_ocr(caminho_pdf))

    return tabelas


def _extrair_tabelas_por_ocr(caminho_pdf: str) -> List[TableExtraction]:
    doc = fitz.open(caminho_pdf)
    tabelas: List[TableExtraction] = []
    pytesseract = _import_pytesseract()
    if not pytesseract:
        doc.close()
        return tabelas

    for idx, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        from PIL import Image

        data = pytesseract.image_to_data(
            Image.open(io.BytesIO(pix.tobytes("png"))), lang="por+eng", output_type=pytesseract.Output.DICT
        )
        linhas = data.get("text", [])
        if not any(t.strip() for t in linhas):
            continue
        linhas_com_bbox: List[List[str]] = []
        atual: List[str] = []
        for texto in linhas:
            if not texto.strip():
                if atual:
                    linhas_com_bbox.append(atual)
                    atual = []
                continue
            atual.append(normalize_text(texto))
        if atual:
            linhas_com_bbox.append(atual)
        if linhas_com_bbox:
            tabelas.append(
                TableExtraction(page=idx + 1, source="ocr-cells", rows=linhas_com_bbox, columns=None, bbox=None)
            )
    doc.close()
    return tabelas


def salvar_tabelas_json(tabelas: Iterable[TableExtraction], caminho_saida: str) -> None:
    serializado = [
        {
            "page": tabela.page,
            "source": tabela.source,
            "rows": tabela.rows,
            "columns": tabela.columns,
            "bbox": tabela.bbox,
        }
        for tabela in tabelas
    ]
    with open(caminho_saida, "w", encoding="utf-8") as fp:
        json.dump(serializado, fp, ensure_ascii=False, indent=2)


__all__ = [
    "PDFContent",
    "PageAnalysis",
    "TableExtraction",
    "classificar_documento",
    "detectar_tipo_paginas",
    "extrair_tabelas",
    "extrair_texto_avancado",
    "normalize_text",
    "salvar_tabelas_json",
]
