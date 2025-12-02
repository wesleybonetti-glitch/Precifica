"""
Leitor de Editais - Versão 2 (Pipeline Estruturado)
- Rotação automática de chaves (via gerenciador_chaves_api)
- Saída 100% em JSON estruturado para integração com calculadoras
- Opcional: HTML simples para compatibilidade legada
"""

import fitz  # PyMuPDF para leitura de PDF
import google.generativeai as genai
import time
import json
import textwrap
from typing import List, Dict, Any, Optional

from gerenciador_chaves_api import obter_gerenciador

# Cache simples para o modelo detectado
_modelo_detectado: Optional[str] = None


# =============================================================================
# 1. DETECÇÃO DE MODELO
# =============================================================================
def detectar_modelo_disponivel() -> str:
    """Detecta automaticamente qual modelo Gemini está disponível na conta.

    Usa a primeira chave disponível do gerenciador apenas para listar modelos.
    O resultado fica em cache em _modelo_detectado.
    """
    global _modelo_detectado

    if _modelo_detectado:
        return _modelo_detectado

    print("🔍 Detectando modelos disponíveis...")

    modelos_preferencia = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b-exp-0827",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-pro",
    ]

    try:
        gerenciador = obter_gerenciador()
        chave_temp = gerenciador.obter_chave_disponivel()
        genai.configure(api_key=chave_temp)

        modelos_compativeis = []
        for m in genai.list_models():
            try:
                if "generateContent" in m.supported_generation_methods:
                    nome = m.name.replace("models/", "")
                    modelos_compativeis.append(nome)
            except Exception:
                # Alguns modelos podem não ter esse atributo preenchido corretamente
                continue

        # Tenta casar preferência com disponíveis
        for preferido in modelos_preferencia:
            for disponivel in modelos_compativeis:
                if preferido in disponivel or disponivel in preferido:
                    _modelo_detectado = disponivel
                    print(f"✅ Modelo selecionado: {_modelo_detectado}")
                    return _modelo_detectado

        if modelos_compativeis:
            _modelo_detectado = modelos_compativeis[0]
        else:
            _modelo_detectado = "gemini-pro"

    except Exception as e:
        print(f"⚠️  Erro ao detectar modelos: {e}")
        _modelo_detectado = "gemini-pro"

    return _modelo_detectado


# =============================================================================
# 2. LEITURA DE PDF
# =============================================================================
def extrair_texto_de_pdf(caminho_pdf: str) -> Optional[str]:
    """Extrai todo o texto de um arquivo PDF usando PyMuPDF."""
    try:
        doc = fitz.open(caminho_pdf)
        texto_completo = ""
        for pagina in doc:
            texto_completo += pagina.get_text()
        doc.close()
        return texto_completo
    except Exception as e:
        print(f"Erro ao ler o PDF: {e}")
        return None


# =============================================================================
# 3. CHAMADA GENÉRICA COM ROTAÇÃO DE CHAVES
# =============================================================================
def _chamar_api_gemini(chave_api: str, prompt: str, nome_modelo: str, generation_config: dict) -> str:
    """Função que realmente chama a API Gemini. É usada pelo gerenciador em rotação."""
    genai.configure(api_key=chave_api)
    model = genai.GenerativeModel(nome_modelo)
    resp = model.generate_content(prompt, generation_config=generation_config)
    if hasattr(resp, "text") and resp.text:
        return resp.text
    raise Exception("Resposta vazia da API Gemini")


def _forcar_json(texto: str) -> dict:
    """Tenta converter a resposta da IA em JSON.

    - Primeiro tenta json.loads direto;
    - Se falhar, tenta extrair o trecho entre o primeiro '{' e o último '}'.
    - Em caso de falha, retorna {}.
    """
    if not texto:
        return {}

    texto = texto.strip()
    try:
        return json.loads(texto)
    except Exception:
        pass

    ini = texto.find("{")
    fim = texto.rfind("}")
    if ini != -1 and fim != -1 and fim > ini:
        trecho = texto[ini : fim + 1]
        try:
            return json.loads(trecho)
        except Exception:
            pass

    print("⚠️  Não foi possível converter a resposta em JSON. Retornando estrutura vazia.")
    return {}


# =============================================================================
# 4. EXTRAÇÃO DE BLOCO DE ITENS / LOTES
# =============================================================================
def extrair_bloco_itens(texto: str) -> str:
    """Tenta localizar o bloco de itens/lotes no texto do edital.

    Procura marcadores típicos como:
    - 'ANEXO I', 'ANEXO II'
    - 'TERMO DE REFERÊNCIA'
    - 'PLANILHA DE ITENS'
    - 'ESPECIFICAÇÃO DOS ITENS'

    Se não encontrar nada, devolve o texto completo (melhor isso do que nada).
    """
    marcadores_inicio = [
        "ANEXO I",
        "ANEXO II",
        "TERMO DE REFERÊNCIA",
        "TERMO DE REFERENCIA",
        "PLANILHA DE ITENS",
        "PLANILHA DE PREÇOS",
        "ESPECIFICAÇÃO DOS ITENS",
        "ESPECIFICACAO DOS ITENS",
        "ESPECIFICAÇÕES DOS SERVIÇOS",
        "ESPECIFICACOES DOS SERVICOS",
    ]

    upper = texto.upper()
    idx_inicio = None

    for m in marcadores_inicio:
        pos = upper.find(m)
        if pos != -1:
            if idx_inicio is None or pos < idx_inicio:
                idx_inicio = pos

    if idx_inicio is None:
        # Não encontrou marcador claro de itens: devolve tudo
        return texto

    return texto[idx_inicio:]


def _chunk_text(texto: str, max_chars: int = 15000) -> List[str]:
    """Divide o texto em pedaços menores para evitar estouro de contexto da IA."""
    return [texto[i : i + max_chars] for i in range(0, len(texto), max_chars)]


# =============================================================================
# 5. ANÁLISE GERAL DO EDITAL (OBJETO, PRAZOS, HABILITAÇÃO, RISCOS)
# =============================================================================
def analisar_edital_geral_json(texto_edital: str) -> dict:
    """Analisa o edital inteiro e devolve um JSON com as seções gerais (sem itens)."""
    if not texto_edital:
        return {}

    gerenciador = obter_gerenciador()
    nome_modelo = detectar_modelo_disponivel()
    print(f"🤖 Usando modelo para análise geral: {nome_modelo}")
    print(f"--- DEBUG: Edital com {len(texto_edital)} caracteres. Processamento em modo JSON (seções gerais). ---")

    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 32,
        "max_output_tokens": 4096,
    }

    template = """
Você é um analista de licitações especialista na Lei 14.133/2021.

Leia com atenção o edital abaixo (texto integral) e devolva EXCLUSIVAMENTE um JSON
no formato a seguir (sem texto explicativo, sem comentários, sem markdown):

{{
  "informacoes_gerais": {{
    "razao_social": string ou null,
    "cnpj": string ou null,
    "endereco": string ou null,
    "numero_processo": string ou null,
    "objeto": string ou null,
    "modalidade": string ou null,
    "tipo": string ou null,
    "data_abertura": string ou null,
    "validade_proposta": integer ou null,
    "prazo_entrega": integer ou null,
    "prazo_pagamento": integer ou null,
    "valor_total": string ou null
  }},
  "prazos": {{
    "data_abertura": string ou null,
    "hora_abertura": string ou null,
    "local_sessao": string ou null,
    "validade_proposta_dias": integer ou null,
    "prazo_entrega_dias": integer ou null,
    "prazo_pagamento_dias": integer ou null,
    "endereco_entrega": string ou null
  }},
  "habilitacao": {{
    "juridica": string ou null,
    "regularidade_fiscal_trabalhista": string ou null,
    "qualificacao_economico_financeira": string ou null,
    "qualificacao_tecnica": string ou null,
    "outros": string ou null
  }},
  "exigencias_tecnicas": string ou null,
  "riscos_observacoes": string ou null
}}

REGRAS IMPORTANTES:
- Preencha tudo diretamente a partir do texto do edital.
- Se não encontrar a informação, use null (não invente).
- "exigencias_tecnicas" deve resumir as exigências técnicas do objeto/licitação.
- "riscos_observacoes" deve destacar penalidades, multas, garantias, riscos e pegadinhas.
- NÃO use markdown, NÃO use texto fora do JSON.

EDITAL (TEXTO COMPLETO):
<<<INICIO_DO_EDITAL>>>
{conteudo}
<<<FIM_DO_EDITAL>>>
    """

    prompt = template.format(conteudo=texto_edital)

    inicio = time.time()
    resultado_bruto = gerenciador.executar_com_rotacao(
        _chamar_api_gemini,
        prompt,
        nome_modelo,
        generation_config,
    )
    tempo = time.time() - inicio
    print(f"✅ Análise geral concluída em {tempo:.1f} segundos!")

    dados = _forcar_json(resultado_bruto)
    dados_normalizados = _normalizar_estrutura_geral(dados)
    return dados_normalizados


def _normalizar_estrutura_geral(dados: dict) -> dict:
    """Garante que todas as chaves esperadas existam, com None como default."""
    base = {
        "informacoes_gerais": {
            "razao_social": None,
            "cnpj": None,
            "endereco": None,
            "numero_processo": None,
            "objeto": None,
            "modalidade": None,
            "tipo": None,
            "data_abertura": None,
            "validade_proposta": None,
            "prazo_entrega": None,
            "prazo_pagamento": None,
            "valor_total": None,
        },
        "prazos": {
            "data_abertura": None,
            "hora_abertura": None,
            "local_sessao": None,
            "validade_proposta_dias": None,
            "prazo_entrega_dias": None,
            "prazo_pagamento_dias": None,
            "endereco_entrega": None,
        },
        "habilitacao": {
            "juridica": None,
            "regularidade_fiscal_trabalhista": None,
            "qualificacao_economico_financeira": None,
            "qualificacao_tecnica": None,
            "outros": None,
        },
        "exigencias_tecnicas": None,
        "riscos_observacoes": None,
        "itens": [],
    }

    if not isinstance(dados, dict):
        return base

    for chave in ["informacoes_gerais", "prazos", "habilitacao"]:
        if chave not in dados or not isinstance(dados[chave], dict):
            dados[chave] = {}

    # Atualiza campos conhecidos, mantendo None como fallback
    for campo in base["informacoes_gerais"]:
        base["informacoes_gerais"][campo] = dados.get("informacoes_gerais", {}).get(campo)

    for campo in base["prazos"]:
        base["prazos"][campo] = dados.get("prazos", {}).get(campo)

    for campo in base["habilitacao"]:
        base["habilitacao"][campo] = dados.get("habilitacao", {}).get(campo)

    base["exigencias_tecnicas"] = dados.get("exigencias_tecnicas")
    base["riscos_observacoes"] = dados.get("riscos_observacoes")

    # Se já vierem itens (em alguma versão anterior), preserva
    if isinstance(dados.get("itens"), list):
        base["itens"] = dados["itens"]

    return base


# =============================================================================
# 6. EXTRAÇÃO DE ITENS / LOTES EM CHUNKS
# =============================================================================
def analisar_itens_em_chunks(texto_itens: str) -> List[Dict[str, Any]]:
    """Analisa o bloco de itens em pedaços e retorna lista consolidada de itens."""
    if not texto_itens:
        return []

    gerenciador = obter_gerenciador()
    nome_modelo = detectar_modelo_disponivel()
    print(f"🤖 Usando modelo para itens: {nome_modelo}")

    generation_config = {
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 32,
        "max_output_tokens": 4096,
    }

    template = """
Você está lendo um trecho de um edital que contém especificações de itens e/ou lotes.

Sua tarefa é extrair TODOS os itens que aparecerem neste trecho e devolver
EXCLUSIVAMENTE um JSON no formato:

{{
  "itens": [
    {{
      "item": "número do item ou lote, como está no edital (ex: '1', '2', '1.1', 'Lote 01')",
      "descricao": "descrição COMPLETA do item exatamente como está no edital, sem resumir para 'MATERIAL/SERVIÇO'",
      "quantidade": "quantidade, como string (ex: '10', '5.000', '1,5') ou null se não constar",
      "unidade": "unidade de medida (UN, M², CX, PCT, etc.) ou null se não constar claramente",
      "valor_unitario": "valor unitário estimado como string (ex: 'R$ 10,50') ou null se não constar",
      "valor_total": "valor total estimado como string (ex: 'R$ 1.050,00') ou null se não constar"
    }}
  ]
}}

REGRAS IMPORTANTES:
- NÃO resuma a descrição para algo genérico como 'ITEM MATERIAL/SERVIÇO'.
  Use sempre o texto mais completo disponível no trecho.
- Se um item não tiver quantidade ou valores, use null nesses campos.
- Não invente valores que não estejam no trecho.
- Devolva apenas o JSON, sem comentários, sem markdown.

TRECHO DO EDITAL:
<<<INICIO_DO_TRECHO>>>
{trecho}
<<<FIM_DO_TRECHO>>>
    """

    todos_itens: List[Dict[str, Any]] = []

    for pedaco in _chunk_text(texto_itens, max_chars=15000):
        if not pedaco.strip():
            continue

        prompt = template.format(trecho=pedaco)

        inicio = time.time()
        resultado_bruto = gerenciador.executar_com_rotacao(
            _chamar_api_gemini,
            prompt,
            nome_modelo,
            generation_config,
        )
        tempo = time.time() - inicio
        print(f"✅ Chunk de itens processado em {tempo:.1f} segundos!")

        dados = _forcar_json(resultado_bruto)
        itens_parciais = []

        if isinstance(dados, dict):
            itens_parciais = dados.get("itens") or []
        elif isinstance(dados, list):
            itens_parciais = dados

        for it in itens_parciais:
            if not isinstance(it, dict):
                continue
            item_norm = {
                "item": (str(it.get("item")).strip() or None) if it.get("item") is not None else None,
                "descricao": (str(it.get("descricao") or "")).strip(),
                "quantidade": (str(it.get("quantidade")).strip() or None) if it.get("quantidade") is not None else None,
                "unidade": (str(it.get("unidade")).strip() or None) if it.get("unidade") is not None else None,
                "valor_unitario": (str(it.get("valor_unitario")).strip() or None) if it.get("valor_unitario") is not None else None,
                "valor_total": (str(it.get("valor_total")).strip() or None) if it.get("valor_total") is not None else None,
            }
            # ignora itens sem descrição
            if item_norm["descricao"]:
                todos_itens.append(item_norm)

    print(f"📦 Total de itens extraídos pela IA: {len(todos_itens)}")
    return todos_itens


# =============================================================================
# 7. PIPELINE COMPLETO PARA O EDITAL
# =============================================================================
def processar_edital(texto_edital: str) -> dict:
    """Pipeline completo:

    1. Analisa o edital inteiro para informações gerais, prazos, habilitação e riscos.
    2. Extrai o bloco de itens / termo de referência.
    3. Analisa esse bloco em chunks para extrair itens/lotes.
    4. Devolve um ÚNICO dicionário JSON consolidado, pronto para uso no template
       leitor_edital.html e para integração com as calculadoras.
    """
    if not texto_edital:
        return _normalizar_estrutura_geral({})

    # 1) Análise geral
    geral = analisar_edital_geral_json(texto_edital)

    # 2) Bloco de itens
    bloco_itens = extrair_bloco_itens(texto_edital)

    # 3) Itens em chunks
    itens = analisar_itens_em_chunks(bloco_itens)

    geral["itens"] = itens
    return geral


# =============================================================================
# 8. FUNÇÃO COMPATÍVEL COM A VERSÃO ANTIGA (HTML + JSON)
# =============================================================================
def analisar_edital_com_ia(texto_edital: str):
    """Função de compatibilidade com a versão antiga.

    Agora ela usa o novo pipeline (processar_edital) e gera:
    - resultado_html: um HTML simples com um resumo básico;
    - resultado_json: o JSON completo usado pelas calculadoras e pelo novo template.

    Isso mantém compatibilidade com qualquer código que ainda espere (html, json).
    """
    if not texto_edital:
        return "<p class='text-danger'>Nenhum texto de edital recebido.</p>", None

    try:
        resumo = processar_edital(texto_edital)

        # HTML bem simples apenas para fallback/depuração
        info = resumo.get("informacoes_gerais", {}) or {}
        orgao = info.get("razao_social") or "Não identificado"
        objeto = info.get("objeto") or "Não identificado"
        modalidade = info.get("modalidade") or "Não identificado"
        tipo = info.get("tipo") or "Não identificado"
        data_abertura = info.get("data_abertura") or "Não identificado"

        html = f"""
        <div class="resultado-container">
            <h4>Resumo automático do edital (gerado por IA)</h4>
            <p><strong>Órgão / Razão social:</strong> {orgao}</p>
            <p><strong>Objeto:</strong> {objeto}</p>
            <p><strong>Modalidade:</strong> {modalidade}</p>
            <p><strong>Tipo de julgamento:</strong> {tipo}</p>
            <p><strong>Data de abertura:</strong> {data_abertura}</p>
            <p><em>Para ver a análise completa, utilize a nova página do Leitor de Editais.</em></p>
        </div>
        """

        print(f"✅ JSON contém {len(resumo.get('itens', []))} itens")
        return html, resumo

    except Exception as e:
        print(f"❌ Erro no pipeline de análise do edital: {e}")
        return f"<p class='text-danger'>Ocorreu um erro ao analisar o documento: {e}</p>", None
