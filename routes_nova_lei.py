"""
Rotas do Módulo: Calculadora de Serviços - Nova Lei
Blueprint isolado para manter modularidade
"""

from flask import Blueprint, render_template, request, jsonify, session, send_file, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import json
import io
import os
import requests

from models import db
from models_nova_lei import SvcScenario, SvcJob, SvcBenefit, SvcInsumo, SvcOutput
from motor_calculo_nova_lei import MotorCalculoNovaLei

# Criar blueprint
nova_lei_bp = Blueprint('nova_lei', __name__, url_prefix='/servicos/nova-lei')


# ========================================
# ROTAS DE UI
# ========================================

@nova_lei_bp.route('/', methods=['GET'])
@login_required
def index():
    """
    Redireciona para a página de simulação (lista de propostas)
    """
    return redirect(url_for('nova_lei.simulacao'))


@nova_lei_bp.route('/simulacao', methods=['GET'])
@login_required
def simulacao():
    """
    Página de simulação - lista todas as propostas salvas
    """
    user_id = current_user.id
    registros = SvcScenario.query.filter_by(user_id=user_id).order_by(SvcScenario.criado_em.desc()).all()
    
    return render_template('nova_lei/simulacao.html', registros=registros)


@nova_lei_bp.route('/calculadora', methods=['GET'])
@login_required
def calculadora():
    """
    Página da calculadora (wizard de 2 passos)
    """
    # Verificar se é edição
    editar_id = request.args.get('editar')
    cenario = None
    
    if editar_id:
        cenario = SvcScenario.query.filter_by(id=editar_id, user_id=current_user.id).first()
    
    return render_template('nova_lei/calculadora.html', cenario=cenario)


# ========================================
# ROTAS DE API
# ========================================

@nova_lei_bp.route('/api/preview', methods=['POST'])
@login_required
def api_preview():
    """
    Recebe JSON dos passos e retorna preview do cálculo
    
    Payload esperado:
    {
        "postos": [...],
        "insumos": [...],
        "parametros": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'sucesso': False, 'erro': 'Dados não fornecidos'}), 400
        
        # Extrair dados
        parametros = data.get('parametros', {})
        postos = data.get('postos', [])
        insumos = data.get('insumos', [])
        
        # Validações básicas
        if not postos:
            return jsonify({'sucesso': False, 'erro': 'Nenhum posto informado'}), 400
        
        # Criar motor de cálculo
        motor = MotorCalculoNovaLei(parametros)
        
        # Executar cálculo
        resultado = motor.calcular(postos, insumos)
        
        # Retornar resultado
        return jsonify({
            'sucesso': True,
            'resultado': resultado
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@nova_lei_bp.route('/api/salvar', methods=['POST'])
@login_required
def api_salvar():
    """
    Salva um cenário completo no banco de dados
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'sucesso': False, 'erro': 'Dados não fornecidos'}), 400
        
        # Extrair dados
        passo1 = data.get('passo1', {})
        postos = data.get('postos', [])
        insumos = data.get('insumos', [])
        parametros = data.get('parametros', {})
        
        # Calcular resultado para obter valor total
        motor = MotorCalculoNovaLei(parametros)
        resultado = motor.calcular(postos, insumos)
        valor_total = resultado.get('total_contrato', {}).get('total_contrato', 0.0)
        
        # Criar ou atualizar cenário
        cenario_id = data.get('cenario_id')
        
        if cenario_id:
            # Atualizar cenário existente
            cenario = SvcScenario.query.filter_by(id=cenario_id, user_id=current_user.id).first()
            if not cenario:
                return jsonify({'sucesso': False, 'erro': 'Cenário não encontrado'}), 404
        else:
            # Criar novo cenário
            cenario = SvcScenario(user_id=current_user.id)
            db.session.add(cenario)
        
        # Atualizar dados do cenário
        cenario.nome_cenario = passo1.get('tipo_servico', 'Sem nome')
        cenario.tipo_servico = passo1.get('tipo_servico', '')
        cenario.cnpj = passo1.get('cnpj', '')
        cenario.razao_social = passo1.get('razao_social', '')
        cenario.endereco = passo1.get('endereco', '')
        cenario.numero_processo = passo1.get('numero_processo', '')
        cenario.validade_proposta = passo1.get('validade_proposta', 60)
        cenario.prazo_pagamento = passo1.get('prazo_pagamento', '')
        cenario.local_execucao = passo1.get('local_execucao', '')
        cenario.prazo_execucao = passo1.get('prazo_execucao', 12)
        cenario.valor_total = valor_total
        
        # Parâmetros
        cenario.inss_patronal = parametros.get('inss_patronal', 20.0)
        cenario.salario_educacao = parametros.get('salario_educacao', 2.5)
        cenario.rat_sat = parametros.get('rat_sat', 3.0)
        cenario.fap_multiplicador = parametros.get('fap_multiplicador', 1.0)
        cenario.sesc_senac = parametros.get('sesc_senac', 1.5)
        cenario.sebrae = parametros.get('sebrae', 0.6)
        cenario.incra = parametros.get('incra', 0.2)
        cenario.regime_tributario = parametros.get('regime_tributario', 'simples')
        cenario.aliquota_simples = parametros.get('aliquota_simples', 14.0)
        cenario.aliquota_pis = parametros.get('aliquota_pis', 0.65)
        cenario.aliquota_cofins = parametros.get('aliquota_cofins', 3.0)
        cenario.aliquota_iss = parametros.get('aliquota_iss', 5.0)
        cenario.custos_indiretos_percentual = parametros.get('custos_indiretos_percentual', 5.0)
        cenario.lucro_percentual = parametros.get('lucro_percentual', 8.0)
        
        db.session.flush()  # Para obter o ID do cenário
        
        # Remover postos e insumos antigos se for edição
        if cenario_id:
            SvcJob.query.filter_by(scenario_id=cenario.id).delete()
            SvcInsumo.query.filter_by(scenario_id=cenario.id).delete()
        
        # Salvar postos
        for posto_data in postos:
            posto = SvcJob(
                scenario_id=cenario.id,
                lote_numero=posto_data.get('lote_numero', 1),
                lote_nome=posto_data.get('lote_nome', 'Lote 1'),
                cargo=posto_data.get('cargo', ''),
                quantidade_postos=posto_data.get('quantidade_postos', 1),
                jornada_tipo=posto_data.get('jornada_tipo', '44h'),
                salario_base=posto_data.get('salario_base', 0.0),
                adicional_insalubridade=posto_data.get('adicional_insalubridade', 0.0),
                adicional_periculosidade=posto_data.get('adicional_periculosidade', 0.0),
                adicional_noturno_percentual=posto_data.get('adicional_noturno_percentual', 20.0),
                gratificacao=posto_data.get('gratificacao', 0.0)
            )
            db.session.add(posto)
        
        # Salvar insumos
        for insumo_data in insumos:
            insumo = SvcInsumo(
                scenario_id=cenario.id,
                lote_numero=insumo_data.get('lote_numero', 1),
                tipo=insumo_data.get('tipo', 'material'),
                descricao=insumo_data.get('descricao', ''),
                custo_unitario=insumo_data.get('custo_unitario', 0.0),
                quantidade_por_posto=insumo_data.get('quantidade_por_posto', 1),
                periodicidade_meses=insumo_data.get('periodicidade_meses', 12),
                cargo=insumo_data.get('cargo', 'todos')
            )
            db.session.add(insumo)
        
        # Salvar output (resultado do cálculo)
        output = SvcOutput(
            scenario_id=cenario.id,
            tipo='json'
        )
        output.set_resultado(resultado)
        db.session.add(output)
        
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'cenario_id': cenario.id,
            'mensagem': 'Cenário salvo com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@nova_lei_bp.route('/api/carregar/<int:cenario_id>', methods=['GET'])
@login_required
def api_carregar(cenario_id):
    """
    Carrega um cenário existente
    """
    try:
        cenario = SvcScenario.query.filter_by(id=cenario_id, user_id=current_user.id).first()
        
        if not cenario:
            return jsonify({'sucesso': False, 'erro': 'Cenário não encontrado'}), 404
        
        # Montar dados do cenário
        cenario_data = {
            'id': cenario.id,
            'nome_cenario': cenario.nome_cenario,
            'tipo_servico': cenario.tipo_servico,
            'cnpj': cenario.cnpj,
            'razao_social': cenario.razao_social,
            'endereco': cenario.endereco,
            'numero_processo': cenario.numero_processo,
            'validade_proposta': cenario.validade_proposta,
            'prazo_pagamento': cenario.prazo_pagamento,
            'local_execucao': cenario.local_execucao,
            'prazo_execucao': cenario.prazo_execucao,
            'status': cenario.status,
            'valor_total': cenario.valor_total,
            'parametros': {
                'inss_patronal': cenario.inss_patronal,
                'salario_educacao': cenario.salario_educacao,
                'rat_sat': cenario.rat_sat,
                'fap_multiplicador': cenario.fap_multiplicador,
                'sesc_senac': cenario.sesc_senac,
                'sebrae': cenario.sebrae,
                'incra': cenario.incra,
                'regime_tributario': cenario.regime_tributario,
                'aliquota_simples': cenario.aliquota_simples,
                'aliquota_pis': cenario.aliquota_pis,
                'aliquota_cofins': cenario.aliquota_cofins,
                'aliquota_iss': cenario.aliquota_iss,
                'custos_indiretos_percentual': cenario.custos_indiretos_percentual,
                'lucro_percentual': cenario.lucro_percentual
            },
            'postos': [],
            'insumos': []
        }
        
        # Adicionar postos
        for posto in cenario.jobs:
            cenario_data['postos'].append({
                'id': posto.id,
                'lote_numero': posto.lote_numero,
                'lote_nome': posto.lote_nome,
                'cargo': posto.cargo,
                'quantidade_postos': posto.quantidade_postos,
                'jornada_tipo': posto.jornada_tipo,
                'salario_base': posto.salario_base,
                'adicional_insalubridade': posto.adicional_insalubridade,
                'adicional_periculosidade': posto.adicional_periculosidade,
                'adicional_noturno_percentual': posto.adicional_noturno_percentual,
                'gratificacao': posto.gratificacao
            })
        
        # Adicionar insumos
        for insumo in cenario.insumos:
            cenario_data['insumos'].append({
                'id': insumo.id,
                'lote_numero': insumo.lote_numero,
                'tipo': insumo.tipo,
                'descricao': insumo.descricao,
                'custo_unitario': insumo.custo_unitario,
                'quantidade_por_posto': insumo.quantidade_por_posto,
                'periodicidade_meses': insumo.periodicidade_meses,
                'cargo': insumo.cargo
            })
        
        return jsonify({
            'sucesso': True,
            'cenario': cenario_data
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@nova_lei_bp.route('/api/excluir/<int:cenario_id>', methods=['DELETE'])
@login_required
def api_excluir(cenario_id):
    """
    Exclui um cenário
    """
    try:
        cenario = SvcScenario.query.filter_by(id=cenario_id, user_id=current_user.id).first()
        
        if not cenario:
            return jsonify({'sucesso': False, 'erro': 'Cenário não encontrado'}), 404
        
        db.session.delete(cenario)
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Cenário excluído com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@nova_lei_bp.route('/api/presets', methods=['GET'])
@login_required
def api_presets():
    """
    Retorna presets por categoria de serviço
    """
    presets = {
        'Portaria': {
            'postos': [
                {
                    'cargo': 'Porteiro',
                    'quantidade_postos': 1,
                    'jornada_tipo': '12x36_noturno',
                    'salario_base': 1500.0,
                    'adicional_noturno_percentual': 20.0
                }
            ],
            'insumos': [
                {
                    'tipo': 'uniforme',
                    'descricao': 'Uniforme completo (calça, camisa, sapato)',
                    'custo_unitario': 150.0,
                    'quantidade_por_posto': 2,
                    'periodicidade_meses': 6
                }
            ]
        },
        'Limpeza': {
            'postos': [
                {
                    'cargo': 'Auxiliar de Limpeza',
                    'quantidade_postos': 1,
                    'jornada_tipo': '44h',
                    'salario_base': 1400.0,
                    'adicional_insalubridade': 200.0
                }
            ],
            'insumos': [
                {
                    'tipo': 'uniforme',
                    'descricao': 'Uniforme de limpeza',
                    'custo_unitario': 120.0,
                    'quantidade_por_posto': 2,
                    'periodicidade_meses': 6
                },
                {
                    'tipo': 'epi',
                    'descricao': 'Luvas e botas',
                    'custo_unitario': 60.0,
                    'quantidade_por_posto': 1,
                    'periodicidade_meses': 3
                }
            ]
        },
        'Copeiragem': {
            'postos': [
                {
                    'cargo': 'Copeira',
                    'quantidade_postos': 1,
                    'jornada_tipo': '40h',
                    'salario_base': 1450.0,
                    'gratificacao': 100.0
                }
            ],
            'insumos': [
                {
                    'tipo': 'uniforme',
                    'descricao': 'Uniforme de copeira',
                    'custo_unitario': 130.0,
                    'quantidade_por_posto': 2,
                    'periodicidade_meses': 6
                }
            ]
        },
        'Zeladoria': {
            'postos': [
                {
                    'cargo': 'Zelador',
                    'quantidade_postos': 1,
                    'jornada_tipo': '44h',
                    'salario_base': 1600.0
                }
            ],
            'insumos': [
                {
                    'tipo': 'uniforme',
                    'descricao': 'Uniforme de zelador',
                    'custo_unitario': 140.0,
                    'quantidade_por_posto': 2,
                    'periodicidade_meses': 6
                },
                {
                    'tipo': 'epi',
                    'descricao': 'Equipamentos de proteção',
                    'custo_unitario': 80.0,
                    'quantidade_por_posto': 1,
                    'periodicidade_meses': 6
                }
            ]
        }
    }
    
    return jsonify({'sucesso': True, 'presets': presets})


@nova_lei_bp.route('/api/export/pdf/<int:cenario_id>', methods=['GET'])
@login_required
def api_export_pdf(cenario_id):
    """
    Gera PDF timbrado da planilha
    """
    try:
        # Buscar cenário
        user_id = current_user.id
        cenario = SvcScenario.query.filter_by(id=cenario_id, user_id=user_id).first_or_404()
        
        # Buscar empresa
        from models import Empresa
        empresa = Empresa.query.filter_by(user_id=user_id).first()
        
        # Buscar dados relacionados
        postos = SvcJob.query.filter_by(scenario_id=cenario_id).all()
        insumos = SvcInsumo.query.filter_by(scenario_id=cenario_id).all()
        
        # Preparar dados para cálculo
        postos_data = []
        for posto in postos:
            postos_data.append({
                'cargo': posto.cargo,
                'quantidade_postos': posto.quantidade_postos,
                'jornada_tipo': posto.jornada_tipo,
                'salario_base': posto.salario_base,
                'adicional_insalubridade': posto.adicional_insalubridade,
                'adicional_periculosidade': posto.adicional_periculosidade,
                'adicional_noturno_percentual': posto.adicional_noturno_percentual,
                'gratificacao': posto.gratificacao
            })
        
        insumos_data = []
        for insumo in insumos:
            insumos_data.append({
                'tipo': insumo.tipo,
                'descricao': insumo.descricao,
                'custo_unitario': insumo.custo_unitario,
                'quantidade_por_posto': insumo.quantidade_por_posto,
                'periodicidade_meses': insumo.periodicidade_meses,
                'cargo': insumo.cargo
            })
        
        # Parâmetros
        parametros = {
            'inss_patronal': cenario.inss_patronal,
            'salario_educacao': cenario.salario_educacao,
            'rat_sat': cenario.rat_sat,
            'fap_multiplicador': cenario.fap_multiplicador,
            'sesc_senac': cenario.sesc_senac,
            'sebrae': cenario.sebrae,
            'incra': cenario.incra,
            'regime_tributario': cenario.regime_tributario,
            'aliquota_simples': cenario.aliquota_simples,
            'aliquota_pis': cenario.aliquota_pis,
            'aliquota_cofins': cenario.aliquota_cofins,
            'aliquota_iss': cenario.aliquota_iss,
            'custos_indiretos_percentual': cenario.custos_indiretos_percentual,
            'lucro_percentual': cenario.lucro_percentual
        }
        
        # Calcular
        motor = MotorCalculoNovaLei(parametros)
        resultado = motor.calcular(postos_data, insumos_data)
        
        # Gerar PDF
        from gerador_pdf_nova_lei import GeradorPDFNovaLei
        gerador = GeradorPDFNovaLei(empresa, cenario, resultado)
        pdf_buffer = gerador.gerar()
        
        # Retornar PDF
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'proposta_servicos_{cenario_id}.pdf'
        )
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@nova_lei_bp.route('/api/export/excel/<int:cenario_id>', methods=['GET'])
@login_required
def api_export_excel(cenario_id):
    """
    Gera Excel com planilha de custos completa
    """
    try:
        # Buscar cenário
        user_id = current_user.id
        cenario = SvcScenario.query.filter_by(id=cenario_id, user_id=user_id).first_or_404()
        
        # Buscar empresa
        from models import Empresa
        empresa = Empresa.query.filter_by(user_id=user_id).first()
        
        # Buscar dados relacionados
        postos = SvcJob.query.filter_by(scenario_id=cenario_id).all()
        insumos = SvcInsumo.query.filter_by(scenario_id=cenario_id).all()
        
        # Preparar dados para cálculo
        postos_data = []
        for posto in postos:
            postos_data.append({
                'cargo': posto.cargo,
                'quantidade_postos': posto.quantidade_postos,
                'jornada_tipo': posto.jornada_tipo,
                'salario_base': posto.salario_base,
                'adicional_insalubridade': posto.adicional_insalubridade,
                'adicional_periculosidade': posto.adicional_periculosidade,
                'adicional_noturno_percentual': posto.adicional_noturno_percentual,
                'gratificacao': posto.gratificacao
            })
        
        insumos_data = []
        for insumo in insumos:
            insumos_data.append({
                'tipo': insumo.tipo,
                'descricao': insumo.descricao,
                'custo_unitario': insumo.custo_unitario,
                'quantidade_por_posto': insumo.quantidade_por_posto,
                'periodicidade_meses': insumo.periodicidade_meses,
                'cargo': insumo.cargo
            })
        
        # Parâmetros
        parametros = {
            'inss_patronal': cenario.inss_patronal,
            'salario_educacao': cenario.salario_educacao,
            'rat_sat': cenario.rat_sat,
            'fap_multiplicador': cenario.fap_multiplicador,
            'sesc_senac': cenario.sesc_senac,
            'sebrae': cenario.sebrae,
            'incra': cenario.incra,
            'regime_tributario': cenario.regime_tributario,
            'aliquota_simples': cenario.aliquota_simples,
            'aliquota_pis': cenario.aliquota_pis,
            'aliquota_cofins': cenario.aliquota_cofins,
            'aliquota_iss': cenario.aliquota_iss,
            'custos_indiretos_percentual': cenario.custos_indiretos_percentual,
            'lucro_percentual': cenario.lucro_percentual
        }
        
        # Calcular
        motor = MotorCalculoNovaLei(parametros)
        resultado = motor.calcular(postos_data, insumos_data)
        
        # Gerar Excel
        from gerador_excel_nova_lei import GeradorExcelNovaLei
        gerador = GeradorExcelNovaLei(empresa, cenario, resultado)
        excel_buffer = gerador.gerar()
        
        # Retornar Excel
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'planilha_custos_{cenario_id}.xlsx'
        )
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@nova_lei_bp.route('/api/consultar-cnpj/<cnpj>', methods=['GET'])
@login_required
def api_consultar_cnpj(cnpj):
    """
    Consulta CNPJ via ReceitaWS (proxy para evitar CORS)
    """
    try:
        # Remover caracteres não numéricos
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
        
        if len(cnpj_limpo) != 14:
            return jsonify({
                'sucesso': False,
                'erro': 'CNPJ inválido. Digite 14 dígitos.'
            }), 400
        
        # Consultar ReceitaWS
        url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({
                'sucesso': False,
                'erro': 'Erro ao consultar CNPJ. Tente novamente.'
            }), 500
        
        data = response.json()
        
        if data.get('status') == 'ERROR':
            return jsonify({
                'sucesso': False,
                'erro': data.get('message', 'CNPJ não encontrado.')
            }), 404
        
        # Formatar endereço
        endereco = f"{data.get('logradouro', '')}, {data.get('numero', '')} - {data.get('bairro', '')}, {data.get('municipio', '')} - {data.get('uf', '')}, CEP: {data.get('cep', '')}"
        
        return jsonify({
            'sucesso': True,
            'dados': {
                'cnpj': data.get('cnpj', ''),
                'razao_social': data.get('nome', ''),
                'nome_fantasia': data.get('fantasia', ''),
                'endereco': endereco,
                'logradouro': data.get('logradouro', ''),
                'numero': data.get('numero', ''),
                'complemento': data.get('complemento', ''),
                'bairro': data.get('bairro', ''),
                'municipio': data.get('municipio', ''),
                'uf': data.get('uf', ''),
                'cep': data.get('cep', ''),
                'telefone': data.get('telefone', ''),
                'email': data.get('email', ''),
                'situacao': data.get('situacao', ''),
                'abertura': data.get('abertura', '')
            }
        })
        
    except requests.Timeout:
        return jsonify({
            'sucesso': False,
            'erro': 'Timeout ao consultar CNPJ. Tente novamente.'
        }), 504
    except requests.RequestException as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro na requisição: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro interno: {str(e)}'
        }), 500


# ========================================
# FUNÇÃO DE REGISTRO
# ========================================

def registrar_blueprint(app):
    """
    Registra o blueprint no app Flask
    """
    app.register_blueprint(nova_lei_bp)
