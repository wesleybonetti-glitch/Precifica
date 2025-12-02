"""
Leitor de Editais - Versão com Integração Completa
- Rotação automática de chaves
- Dupla saída: HTML + JSON
- Integração com calculadoras
"""

import fitz
import google.generativeai as genai
import time
import os
import re
import json
from google.api_core import exceptions as google_exceptions
from gerenciador_chaves_api import obter_gerenciador


# Variável global para armazenar o modelo detectado
_modelo_detectado = None


def configurar_ia(api_key=None):
    """
    Configura a API do Google GenAI.
    Agora usa sistema de rotação automática (ignora api_key fornecida).

    Args:
        api_key: Mantido para compatibilidade, mas não é usado
    """
    print("--- DEBUG: Sistema de rotação de chaves ativado. ---")


def detectar_modelo_disponivel():
    """Detecta automaticamente qual modelo Gemini está disponível."""
    global _modelo_detectado

    if _modelo_detectado:
        return _modelo_detectado

    print("🔍 Detectando modelos disponíveis...")

    gerenciador = obter_gerenciador()
    chave_temp = gerenciador.obter_chave_disponivel()
    genai.configure(api_key=chave_temp)

    modelos_preferencia = [
        'gemini-1.5-flash-latest',
        'gemini-1.5-flash',
        'gemini-2.0-flash-exp',
        'gemini-1.5-pro-latest',
        'gemini-1.5-pro',
        'gemini-pro',
    ]

    try:
        modelos_disponiveis = list(genai.list_models())
        modelos_compativeis = []

        for modelo in modelos_disponiveis:
            if 'generateContent' in modelo.supported_generation_methods:
                nome_modelo = modelo.name.replace('models/', '')
                modelos_compativeis.append(nome_modelo)

        for modelo_preferido in modelos_preferencia:
            for modelo_disponivel in modelos_compativeis:
                if modelo_preferido in modelo_disponivel or modelo_disponivel in modelo_preferido:
                    _modelo_detectado = modelo_disponivel
                    print(f"✅ Modelo selecionado: {_modelo_detectado}")
                    return _modelo_detectado

        if modelos_compativeis:
            _modelo_detectado = modelos_compativeis[0]
            return _modelo_detectado

        _modelo_detectado = 'gemini-pro'
        return _modelo_detectado

    except Exception as e:
        print(f"⚠️  Erro ao detectar modelos: {e}")
        _modelo_detectado = 'gemini-pro'
        return _modelo_detectado


def extrair_texto_de_pdf(caminho_pdf):
    """Extrai texto de PDF com detecção automática e OCR.

    A função utiliza heurísticas de densidade de texto para classificar
    o arquivo (texto, imagem ou misto) e aciona OCR (por padrão
    `por+eng`) quando encontra páginas sem conteúdo textual. Também
    preserva bounding boxes dos trechos lidos e captura tabelas via
    múltiplos backends.
    """
    try:
        from pdf_processing import extrair_texto_avancado

        resultado = extrair_texto_avancado(caminho_pdf)
        return resultado.texto_completo
    except Exception as e:
        print(f"Erro ao ler o PDF: {e}")
        try:
            doc = fitz.open(caminho_pdf)
            texto_completo = "".join(pagina.get_text() for pagina in doc)
            doc.close()
            return texto_completo
        except Exception:
            return None


def chamar_api_com_rotacao(chave_api, prompt, nome_modelo, generation_config):
    """
    Função interna que faz a chamada à API.
    Esta função é chamada pelo gerenciador com rotação automática.
    """
    genai.configure(api_key=chave_api)
    model = genai.GenerativeModel(nome_modelo)
    response = model.generate_content(prompt, generation_config=generation_config)

    if response and response.text:
        return response.text
    else:
        raise Exception("Resposta vazia da API")


def formatar_resultado_json(texto_analise):
    """
    NOVA FUNÇÃO: Converte o resultado da análise em JSON estruturado.
    Este JSON será usado pelas calculadoras para preenchimento automático.

    Returns:
        dict: Dicionário com estrutura:
        {
            'informacoes_gerais': {
                'razao_social': str,
                'cnpj': str,
                'endereco': str,
                'numero_processo': str,
                'validade_proposta': int,
                'prazo_pagamento': int,
                'prazo_entrega': int,
                'objeto': str,
                'modalidade': str,
                'tipo': str,
                'valor_total': str,
                'data_abertura': str
            },
            'itens': [
                {
                    'item': str,
                    'descricao': str,
                    'quantidade': str,
                    'unidade': str,
                    'valor_unitario': str,
                    'valor_total': str
                }
            ]
        }
    """
    if not texto_analise:
        return {'informacoes_gerais': {}, 'itens': []}

    resultado = {
        'informacoes_gerais': {},
        'itens': []
    }

    linhas = texto_analise.split('\n')

    # Extrai informações gerais
    for linha in linhas:
        linha = linha.strip()
        if not linha or '|' in linha:
            continue

        # Remove formatação markdown
        linha = linha.replace('**', '').replace('*', '')

        if ':' in linha:
            partes = linha.split(':', 1)
            if len(partes) == 2:
                campo = partes[0].strip().lower()
                valor = partes[1].strip()

                # Mapeia campos para chaves do JSON
                if 'razão social' in campo or 'razao social' in campo:
                    resultado['informacoes_gerais']['razao_social'] = valor

                elif 'cnpj' in campo:
                    # Remove formatação do CNPJ
                    cnpj_limpo = re.sub(r'[^\d]', '', valor)
                    resultado['informacoes_gerais']['cnpj'] = cnpj_limpo

                elif 'endereço' in campo or 'endereco' in campo:
                    resultado['informacoes_gerais']['endereco'] = valor

                elif 'número do processo' in campo or 'numero do processo' in campo or 'processo' in campo:
                    resultado['informacoes_gerais']['numero_processo'] = valor

                elif 'validade da proposta' in campo or 'validade' in campo:
                    # Extrai apenas números
                    dias = re.findall(r'\d+', valor)
                    if dias:
                        resultado['informacoes_gerais']['validade_proposta'] = int(dias[0])

                elif 'prazo de pagamento' in campo or 'pagamento' in campo:
                    dias = re.findall(r'\d+', valor)
                    if dias:
                        resultado['informacoes_gerais']['prazo_pagamento'] = int(dias[0])

                elif 'prazo de entrega' in campo or 'entrega' in campo:
                    dias = re.findall(r'\d+', valor)
                    if dias:
                        resultado['informacoes_gerais']['prazo_entrega'] = int(dias[0])

                elif 'objeto' in campo and 'licitação' in campo:
                    resultado['informacoes_gerais']['objeto'] = valor

                elif 'modalidade' in campo:
                    resultado['informacoes_gerais']['modalidade'] = valor

                elif 'tipo' in campo:
                    resultado['informacoes_gerais']['tipo'] = valor

                elif 'valor total' in campo or 'valor estimado' in campo:
                    resultado['informacoes_gerais']['valor_total'] = valor

                elif 'data de abertura' in campo or 'abertura' in campo:
                    resultado['informacoes_gerais']['data_abertura'] = valor

    # Extrai itens da tabela
    em_tabela_itens = False
    for linha in linhas:
        linha = linha.strip()

        # Detecta início da seção de itens
        if 'PARTE 3' in linha.upper() or 'TABELA' in linha.upper() and 'ITENS' in linha.upper():
            em_tabela_itens = True
            continue

        # Detecta fim da seção de itens
        if em_tabela_itens and 'PARTE 4' in linha.upper():
            break

        # Processa linhas da tabela
        if em_tabela_itens and '|' in linha:
            # Pula cabeçalhos e separadores
            if 'Item' in linha or '---' in linha or '===' in linha:
                continue

            # Divide por pipe e limpa
            colunas = [col.strip() for col in linha.split('|')]
            colunas = [col for col in colunas if col]

            # Precisa ter pelo menos 3 colunas (item, descrição, quantidade)
            if len(colunas) >= 3:
                item = {
                    'item': colunas[0] if len(colunas) > 0 else '',
                    'descricao': colunas[1] if len(colunas) > 1 else '',
                    'quantidade': colunas[2] if len(colunas) > 2 else '',
                    'unidade': colunas[3] if len(colunas) > 3 else '',
                    'valor_unitario': colunas[4] if len(colunas) > 4 else '',
                    'valor_total': colunas[5] if len(colunas) > 5 else ''
                }

                # Só adiciona se tiver descrição
                if item['descricao'] and item['descricao'] != '-':
                    resultado['itens'].append(item)

    return resultado


def formatar_resultado_html(texto_analise):
    """
    Converte o resultado da análise em HTML formatado e profissional.
    """
    if not texto_analise:
        return "<p>Nenhum resultado disponível.</p>"

    html = ""

    # Divide o texto em seções
    secoes = {
        'informacoes_gerais': [],
        'habilitacao': [],
        'itens': []
    }

    linhas = texto_analise.split('\n')
    secao_atual = None

    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue

        # Identifica seções
        linha_upper = linha.upper()
        if 'INFORMAÇÕES GERAIS' in linha_upper or 'INFORMACOES GERAIS' in linha_upper or 'PARTE 1' in linha_upper:
            secao_atual = 'informacoes_gerais'
            continue
        elif 'HABILITAÇÃO' in linha_upper or 'HABILITACAO' in linha_upper or 'REQUISITOS' in linha_upper or 'PARTE 2' in linha_upper:
            secao_atual = 'habilitacao'
            continue
        elif 'ITENS' in linha_upper or 'SERVIÇOS' in linha_upper or 'SERVICOS' in linha_upper or 'TABELA' in linha_upper or 'PARTE 3' in linha_upper:
            secao_atual = 'itens'
            continue

        # Adiciona linha à seção atual
        if secao_atual:
            secoes[secao_atual].append(linha)

    # SEÇÃO 1: INFORMAÇÕES GERAIS
    if secoes['informacoes_gerais']:
        html += '''
        <div class="secao-espacamento resultado-container">
            <h4 class="secao-titulo">
                <i class="fas fa-info-circle"></i>
                Informações Gerais do Edital
            </h4>
            <div class="secao-conteudo">
                <table class="info-table table table-hover">
                    <tbody>
        '''

        for linha in secoes['informacoes_gerais']:
            if ':' in linha or '|' in linha:
                linha = linha.replace('**', '').replace('*', '')

                if ':' in linha:
                    partes = linha.split(':', 1)
                elif '|' in linha:
                    partes = linha.split('|', 1)
                else:
                    continue

                if len(partes) == 2:
                    campo = partes[0].strip().replace('-', '').strip()
                    valor = partes[1].strip()

                    if not valor or valor == '-':
                        continue

                    if 'Razão Social' in campo and 'CNPJ' in campo:
                        continue

                    if 'R$' in valor or 'Valor' in campo or 'valor' in campo:
                        valor = f'<span class="valor-destaque">{valor}</span>'

                    html += f'''
                        <tr>
                            <th>{campo}</th>
                            <td>{valor}</td>
                        </tr>
                    '''

        html += '''
                    </tbody>
                </table>
            </div>
        </div>
        '''

    # SEÇÃO 2: REQUISITOS DE HABILITAÇÃO
    if secoes['habilitacao']:
        html += '''
        <div class="secao-espacamento resultado-container">
            <h4 class="secao-titulo">
                <i class="fas fa-clipboard-check"></i>
                Requisitos de Habilitação
            </h4>
            <div class="secao-conteudo">
                <ul class="lista-requisitos">
        '''

        requisito_atual = None
        descricao_atual = []

        for linha in secoes['habilitacao']:
            linha = linha.replace('**', '').replace('*', '').strip()

            if ':' in linha and not linha.startswith('-'):
                if requisito_atual:
                    desc = ' '.join(descricao_atual)
                    if desc:
                        html += f'''
                        <li>
                            <strong>{requisito_atual}</strong>
                            {desc}
                        </li>
                        '''

                partes = linha.split(':', 1)
                requisito_atual = partes[0].strip()
                descricao_atual = [partes[1].strip()] if len(partes) > 1 and partes[1].strip() else []
            else:
                if requisito_atual and linha and linha != '-':
                    descricao_atual.append(linha)

        if requisito_atual:
            desc = ' '.join(descricao_atual)
            if desc:
                html += f'''
                <li>
                    <strong>{requisito_atual}</strong>
                    {desc}
                </li>
                '''

        html += '''
                </ul>
            </div>
        </div>
        '''

    # SEÇÃO 3: TABELA DE ITENS/SERVIÇOS
    if secoes['itens']:
        html += '''
        <div class="secao-espacamento resultado-container">
            <h4 class="secao-titulo">
                <i class="fas fa-list-alt"></i>
                Itens / Serviços Licitados
            </h4>
            <div class="secao-conteudo">
                <div class="table-responsive">
                    <table class="tabela-itens">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th>Descrição</th>
                                <th>Qtd.</th>
                                <th>Unidade</th>
                                <th>Vlr. Unit.</th>
                                <th>Vlr. Total</th>
                            </tr>
                        </thead>
                        <tbody>
        '''

        for linha in secoes['itens']:
            if '|' in linha:
                if 'Item' in linha or '---' in linha or '===' in linha:
                    continue

                colunas = [col.strip() for col in linha.split('|')]
                colunas = [col for col in colunas if col]

                if len(colunas) >= 3:
                    html += '<tr>'
                    for i, col in enumerate(colunas):
                        if i < 6:
                            html += f'<td>{col}</td>'
                    while len(colunas) < 6:
                        html += '<td>-</td>'
                        colunas.append('-')
                    html += '</tr>'

        html += '''
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        '''

    if not any(secoes.values()):
        html = f'''
        <div class="resultado-container">
            <div class="secao-conteudo">
                <pre style="white-space: pre-wrap; font-family: inherit; font-size: 0.95rem; line-height: 1.6;">{texto_analise}</pre>
            </div>
        </div>
        '''

    return html


def analisar_edital_com_ia(texto_edital):
    """
    VERSÃO COM INTEGRAÇÃO COMPLETA:
    - Rotação automática de chaves
    - Dupla saída: HTML + JSON
    - Integração com calculadoras

    Returns:
        tuple: (resultado_html, resultado_json)
    """
    if not texto_edital:
        return None, None

    try:
        gerenciador = obter_gerenciador()
        nome_modelo = detectar_modelo_disponivel()
        print(f"🤖 Usando modelo: {nome_modelo}")

        MAX_CARACTERES = 600000
        if len(texto_edital) > MAX_CARACTERES:
            print(f"⚠️  Edital muito grande ({len(texto_edital)} caracteres). Usando primeiros {MAX_CARACTERES} caracteres.")
            texto_edital = texto_edital[:MAX_CARACTERES]

        print(f"--- DEBUG: Edital com {len(texto_edital)} caracteres. Processamento com dupla saída (HTML + JSON). ---")

        # Prompt otimizado para extrair dados estruturados
        prompt_completo = f"""
Analise este edital de licitação e extraia TODAS as informações relevantes de forma COMPLETA e DETALHADA.

**PARTE 1: INFORMAÇÕES GERAIS DO EDITAL**
Extraia TODAS as informações abaixo (se disponíveis no edital):

**Órgão Licitante:**
- Razão Social: [nome completo do órgão]
- CNPJ: [número completo]
- Endereço Completo: [rua, número, bairro, cidade, estado, CEP]
- Telefone: [se disponível]
- Email: [se disponível]
- Site: [se disponível]

**Dados da Licitação:**
- Número do Processo/Edital: [número completo]
- Modalidade: [Pregão Eletrônico, Concorrência, etc.]
- Tipo: [Menor Preço, Técnica e Preço, etc.]
- Regime de Execução: [Empreitada por preço global, unitário, etc.]
- Objeto da Licitação: [descrição COMPLETA do objeto]
- Justificativa: [se disponível]

**Datas e Prazos:**
- Data de Abertura: [data e hora completas]
- Data Limite para Impugnação: [se disponível]
- Data Limite para Esclarecimentos: [se disponível]
- Validade da Proposta: [número de dias]
- Prazo de Entrega: [número de dias e condições]
- Prazo de Execução: [se aplicável]
- Vigência do Contrato: [período]

**Valores:**
- Valor Total Estimado: [valor completo com R$]
- Valor Mínimo: [se houver]
- Valor Máximo: [se houver]
- Dotação Orçamentária: [se disponível]

**Condições de Pagamento:**
- Forma de Pagamento: [descrição completa]
- Prazo de Pagamento: [número de dias e condições]
- Reajuste: [se previsto e condições]

**Garantias:**
- Garantia de Proposta: [se exigida, percentual e forma]
- Garantia de Execução: [se exigida, percentual e forma]

**Critérios de Julgamento:**
- Critério Principal: [menor preço, técnica e preço, etc.]
- Critérios de Desempate: [se houver]
- Preferências: [ME/EPP, produtos nacionais, etc.]

**PARTE 2: REQUISITOS DE HABILITAÇÃO**
Liste TODOS os documentos e requisitos exigidos, organizados por categoria:

**Habilitação Jurídica:**
[Liste TODOS os documentos exigidos com detalhes]

**Regularidade Fiscal e Trabalhista:**
[Liste TODAS as certidões e documentos exigidos]

**Qualificação Econômico-Financeira:**
[Liste TODOS os requisitos e documentos]

**Qualificação Técnica:**
[Liste TODOS os atestados, certidões e comprovações exigidas]

**Declarações Obrigatórias:**
[Liste TODAS as declarações que devem ser apresentadas]

**Outros Documentos:**
[Qualquer outro documento exigido]

**PARTE 3: TABELA COMPLETA DE ITENS/SERVIÇOS**
Crie uma tabela COMPLETA com TODOS os itens do edital:

| Item | Descrição Completa | Qtd | Unidade | Vlr Unit Estimado | Vlr Total Estimado |
|------|-------------------|-----|---------|-------------------|-------------------|
| 1    | [descrição detalhada] | [qtd] | [un] | [R$ valor] | [R$ valor] |
| 2    | [descrição detalhada] | [qtd] | [un] | [R$ valor] | [R$ valor] |
[Continue para TODOS os itens]

**PARTE 4: INFORMAÇÕES COMPLEMENTARES**
- Anexos do Edital: [liste todos os anexos]
- Legislação Aplicável: [leis e normas citadas]
- Sanções Previstas: [penalidades por inadimplência]
- Observações Importantes: [qualquer informação relevante adicional]

EDITAL:
{texto_edital}

IMPORTANTE: 
- Seja COMPLETO e DETALHADO
- Não omita informações importantes
- Se alguma informação não estiver disponível, indique "[Não especificado no edital]"
- Mantenha a formatação clara e organizada
- Use SEMPRE o formato de tabela com pipes (|) para os itens
"""

        generation_config = {
            'temperature': 0.2,
            'top_p': 0.8,
            'top_k': 20,
            'max_output_tokens': 8192,
        }

        print("⚡ Processando com rotação automática de chaves...")
        print("📋 Extraindo informações COMPLETAS do edital...")
        inicio = time.time()

        # Executa com rotação automática de chaves
        resultado = gerenciador.executar_com_rotacao(
            chamar_api_com_rotacao,
            prompt_completo,
            nome_modelo,
            generation_config
        )

        tempo_decorrido = time.time() - inicio
        print(f"✅ Processamento concluído em {tempo_decorrido:.1f} segundos!")

        # Imprime estatísticas de uso
        print("\n📊 Estatísticas de uso das chaves:")
        stats = gerenciador.obter_estatisticas()
        print(f"   Chaves disponíveis: {stats['chaves_disponiveis']}/{stats['total_chaves']}")
        print(f"   Total de requisições: {stats['total_requisicoes']}")

        if resultado:
            # Formata em HTML para visualização
            resultado_html = formatar_resultado_html(resultado)

            # Formata em JSON para integração com calculadoras
            resultado_json = formatar_resultado_json(resultado)

            print("✅ Dupla saída gerada: HTML + JSON")
            print(f"   JSON contém {len(resultado_json.get('itens', []))} itens")

            return resultado_html, resultado_json
        else:
            return "<p class='text-danger'>Erro: Resposta vazia da API. Tente novamente.</p>", None

    except Exception as e:
        print(f"❌ Erro ao chamar a API de IA: {e}")
        return f"<p class='text-danger'>Ocorreu um erro ao analisar o documento: {e}</p>", None

