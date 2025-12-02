import io
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from unittest.mock import MagicMock, patch

import fitz
import pytest

from pdf_processing import (
    PDFContent,
    TableExtraction,
    classificar_documento,
    detectar_tipo_paginas,
    extrair_tabelas,
    extrair_texto_avancado,
    normalize_text,
)


@pytest.fixture
def text_pdf(tmp_path: Path) -> Path:
    caminho = tmp_path / "texto.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Edital de Licitação\nLote 1 - Equipamentos")
    doc.save(caminho)
    doc.close()
    return caminho


@pytest.fixture
def image_pdf(tmp_path: Path) -> Path:
    caminho = tmp_path / "imagem.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(page.rect, color=(0.5, 0.5, 0.5), fill=(0.9, 0.9, 0.9))
    doc.save(caminho)
    doc.close()
    return caminho


def test_classifica_pdf_textual(text_pdf: Path):
    analises = detectar_tipo_paginas(str(text_pdf))
    assert classificar_documento(analises) == "texto"
    assert analises[0].has_text is True
    assert analises[0].boxes


def test_classifica_pdf_imagem(image_pdf: Path):
    analises = detectar_tipo_paginas(str(image_pdf))
    assert classificar_documento(analises) == "imagem"
    assert analises[0].has_text is False


def test_ocr_injetado_em_paginas_sem_texto(image_pdf: Path):
    caixa_ocr = TableExtraction(page=1, source="ocr", rows=[["linha"]])

    fake_box = MagicMock()
    fake_box.text = "Contrato"
    fake_box.bbox = [0, 0, 10, 10]

    with patch("pdf_processing._run_ocr_on_page", return_value=[fake_box]):
        conteudo: PDFContent = extrair_texto_avancado(str(image_pdf))
    assert conteudo.classification == "imagem"
    assert any(box.text == "Contrato" for box in conteudo.pages[0].boxes)


def test_normalize_text_remove_hifenizacao():
    original = "Gestão-\nContratual"
    assert normalize_text(original) == "GestãoContratual"


def test_extrair_tabelas_usa_fallbacks(text_pdf: Path):
    fake_table = MagicMock()
    fake_table.page = 1
    fake_table.df = MagicMock()
    fake_table.df.values.tolist.return_value = [["a", "b"], ["c", "d"]]
    fake_table.df.columns = ["col1", "col2"]

    with patch("pdf_processing._import_camelot", return_value=None), patch(
        "pdf_processing._import_tabula", return_value=None
    ), patch("pdf_processing._extrair_tabelas_por_ocr", return_value=[
        TableExtraction(page=1, source="ocr-cells", rows=[["1", "2"]])
    ]):
        tabelas = extrair_tabelas(str(text_pdf))
    assert tabelas
    assert tabelas[0].source == "ocr-cells"
