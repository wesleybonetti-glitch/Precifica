# Orquestração da extração de documentos

## Visão geral por etapas
1. **Ingestão (PDF/HTML)**: recebe arquivos ou URLs, normaliza (ex.: download e salvamento), identifica tipo de fonte e extrai metadados básicos (nome do arquivo, hash, número de páginas).
2. **OCR (condicional)**: aplicado quando o documento não é pesquisável ou contém imagens/scan. Deve preservar coordenadas de página e, se possível, bounding boxes para mapear parágrafos e tabelas.
3. **Segmentação por seções**: divide o documento em blocos semânticos (título, sumário, capítulos, anexos, tabelas). A saída referencia páginas e índices de parágrafos para permitir rastreabilidade.
4. **Extração por campo (prompts específicos)**: para cada campo alvo (ex.: órgão, objeto, vigência), usa prompts especializados considerando contexto local (seção) e global (metadados do documento).
5. **Validação**: aplica regras de consistência (tipos, regex, datas, intervalos, obrigatoriedade) e checagem cruzada entre campos (ex.: datas de início ≤ datas de fim).
6. **Fallback heurístico**: quando a extração modelada falha ou retorna baixa confiança, aplica heurísticas/regex e recuperação de trechos próximos para tentar preencher campos.
7. **Agregação final**: consolida valores por campo, resolve conflitos (prioridade por confiança e proximidade contextual), produz payload final e registra trilha de evidências.

## Interfaces entre etapas (JSON)
### Entrada padrão de documento
```json
{
  "document_id": "uuid",
  "source": {"type": "pdf" | "html", "uri": "..."},
  "metadata": {"filename": "...", "hash": "...", "pages": 12},
  "raw_content": null,
  "pages": []
}
```
- `raw_content`: opcional (HTML puro). `pages`: preenchido após OCR/conversão.

### Saída da ingestão
```json
{
  "document_id": "uuid",
  "metadata": {"filename": "...", "hash": "...", "pages": 12},
  "pages": [
    {"page": 1, "text": "...", "blocks": [{"bbox": [x1,y1,x2,y2], "text": "..."}]}
  ],
  "ingestion_log": {"source_type": "pdf", "download_ms": 120}
}
```

### Saída do OCR (quando aplicado)
```json
{
  "document_id": "uuid",
  "pages": [
    {"page": 1, "text": "...", "blocks": [{"bbox": [x1,y1,x2,y2], "text": "..."}], "ocr_engine": "tesseract-4.1"}
  ],
  "ocr_log": {"applied": true, "confidence_avg": 0.91}
}
```

### Saída da segmentação por seções
```json
{
  "document_id": "uuid",
  "sections": [
    {"id": "sec-1", "title": "Objeto", "page_start": 2, "page_end": 3, "paragraphs": [{"index": 10, "text": "..."}]}
  ],
  "segmentation_log": {"model": "model-x", "tokens_used": 1024}
}
```

### Saída da extração por campo
```json
{
  "document_id": "uuid",
  "fields": {
    "orgao": {"value": "Prefeitura X", "confidence": 0.92, "section_ref": "sec-1", "page_ref": 2, "paragraph_ref": 10, "evidence": "trecho original"},
    "objeto": {"value": "Contratação de serviços...", "confidence": 0.88, "section_ref": "sec-1", "page_ref": 2, "paragraph_ref": 11, "prompt_used": "prompt_objeto_v1"}
  },
  "extraction_log": {"model": "gpt-4.1", "tokens_prompt": 800, "tokens_completion": 120}
}
```

### Saída da validação
```json
{
  "document_id": "uuid",
  "validated_fields": {
    "orgao": {"value": "Prefeitura X", "status": "ok"},
    "data_inicio": {"value": "2024-02-01", "status": "warning", "issues": ["format normalized"]},
    "data_fim": {"value": null, "status": "error", "issues": ["missing"]}
  },
  "validation_log": {"rules_fired": ["date_format", "required_fields"], "errors": 1, "warnings": 1}
}
```

### Saída do fallback heurístico
```json
{
  "document_id": "uuid",
  "fallback_fields": {
    "data_fim": {"value": "2024-12-31", "method": "regex_nearby", "page_ref": 5, "paragraph_ref": 42, "evidence": "trecho próximo"}
  },
  "fallback_log": {"methods_tried": ["regex_nearby", "table_scan"], "success": true}
}
```

### Saída da agregação final
```json
{
  "document_id": "uuid",
  "result": {
    "orgao": {"value": "Prefeitura X", "source": "extraction", "confidence": 0.92},
    "objeto": {"value": "Contratação de serviços...", "source": "extraction", "confidence": 0.88},
    "data_inicio": {"value": "2024-02-01", "source": "extraction", "confidence": 0.7},
    "data_fim": {"value": "2024-12-31", "source": "fallback", "confidence": 0.5}
  },
  "evidence_trail": [
    {"field": "data_fim", "page_ref": 5, "paragraph_ref": 42, "section_ref": null, "text_excerpt": "trecho próximo"}
  ],
  "aggregation_log": {"conflict_policy": "highest_confidence", "fields_missing": []}
}
```

## Pontos de observabilidade
- **Logs estruturados**: eventos por etapa (`ingestion`, `ocr`, `segmentation`, `extraction`, `validation`, `fallback`, `aggregation`) com `document_id`, timestamps, duração, tamanhos de payload, e indicadores de sucesso/falha.
- **Métricas**: 
  - Contadores: documentos processados, documentos com OCR, extrações bem-sucedidas por campo, falhas por etapa.
  - Latências: tempo médio/p95 por etapa, tempo total do pipeline.
  - Qualidade: distribuição de `confidence` por campo, percentual de campos preenchidos, taxa de fallback acionado.
- **Tracing**: 
  - ID de trace por documento e spans por etapa, incluindo tokens usados em chamadas de modelo, referência ao prompt, e IDs de seções/páginas utilizados.
  - Anexar snippets/evidências no trace para depuração (respeitando segurança de dados).
- **Auditoria de contexto**: armazenar quais páginas/parágrafos foram enviados ao modelo e qual `prompt` foi utilizado para cada campo, permitindo reprodutibilidade.
- **Alertas**: thresholds para taxa de erro por etapa, confiança média por campo abaixo do esperado, ou tempo de processamento acima do p95 definido.
