"""
Modelos V3 - Módulo Nova Lei Universal
Sistema flexível para qualquer tipo de serviço
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

from models import db


class SvcScenario(db.Model):
    """
    Cenário de cálculo - Universal para todos os tipos de serviços
    """
    __tablename__ = 'svc_scenarios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)
    
    # Identificação
    nome_cenario = db.Column(db.String(200), nullable=False)
    tipo_servico = db.Column(db.String(100), nullable=False)
    
    # Dados da Empresa
    cnpj = db.Column(db.String(18))
    razao_social = db.Column(db.String(200))
    endereco = db.Column(db.Text)
    
    # Dados do Órgão/Processo
    numero_processo = db.Column(db.String(100))
    validade_proposta = db.Column(db.Integer)
    prazo_pagamento = db.Column(db.String(100))
    local_execucao = db.Column(db.String(200))
    prazo_execucao = db.Column(db.Integer)
    
    # Status
    status = db.Column(db.String(50), default='habilitação')
    valor_total = db.Column(db.Float, default=0.0)
    
    # Parâmetros de Encargos
    inss_patronal = db.Column(db.Float, default=20.0)
    salario_educacao = db.Column(db.Float, default=2.5)
    rat_sat = db.Column(db.Float, default=3.0)
    fap_multiplicador = db.Column(db.Float, default=1.0)
    sesc_senac = db.Column(db.Float, default=1.5)
    sebrae = db.Column(db.Float, default=0.6)
    incra = db.Column(db.Float, default=0.2)
    
    # Tributos
    regime_tributario = db.Column(db.String(50), default='simples')
    pis_cofins_cumulativo = db.Column(db.Boolean, default=False)
    aliquota_pis = db.Column(db.Float, default=0.65)
    aliquota_cofins = db.Column(db.Float, default=3.0)
    aliquota_iss = db.Column(db.Float, default=5.0)
    aliquota_simples = db.Column(db.Float, default=14.0)
    anexo_simples = db.Column(db.String(20), default='IV')
    
    # BDI/CITL
    custos_indiretos_percentual = db.Column(db.Float, default=5.0)
    lucro_percentual = db.Column(db.Float, default=8.0)
    
    # Metadata
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    jobs = db.relationship('SvcJob', backref='scenario', lazy=True, cascade='all, delete-orphan')
    benefits = db.relationship('SvcBenefit', backref='scenario', lazy=True, cascade='all, delete-orphan')
    insumos = db.relationship('SvcInsumo', backref='scenario', lazy=True, cascade='all, delete-orphan')
    despesas = db.relationship('SvcDespesa', backref='scenario', lazy=True, cascade='all, delete-orphan')
    outputs = db.relationship('SvcOutput', backref='scenario', lazy=True, cascade='all, delete-orphan')


class SvcJob(db.Model):
    """
    Postos de trabalho / Mão de obra
    """
    __tablename__ = 'svc_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('svc_scenarios.id'), nullable=False)
    
    # Agrupamento
    lote_numero = db.Column(db.Integer, default=1)
    lote_nome = db.Column(db.String(200), default='Lote 1')
    
    # Dados do posto
    cargo = db.Column(db.String(200), nullable=False)
    cbo = db.Column(db.String(20), nullable=True)
    quantidade_postos = db.Column(db.Integer, nullable=False, default=1)
    
    # Jornada
    jornada_tipo = db.Column(db.String(50), nullable=False)
    horas_semanais = db.Column(db.Float, nullable=True)
    
    # Remuneração
    salario_base = db.Column(db.Float, nullable=False)
    adicional_insalubridade = db.Column(db.Float, default=0.0)
    adicional_periculosidade = db.Column(db.Float, default=0.0)
    adicional_noturno_percentual = db.Column(db.Float, default=20.0)
    gratificacao = db.Column(db.Float, default=0.0)
    
    # CCT
    cct_referencia = db.Column(db.Text, nullable=True)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SvcBenefit(db.Model):
    """
    Benefícios (VT, VR, saúde, etc.)
    """
    __tablename__ = 'svc_benefits'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('svc_scenarios.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('svc_jobs.id'), nullable=True)
    
    tipo = db.Column(db.String(100), nullable=False)
    valor_unitario = db.Column(db.Float, default=0.0)
    quantidade_dias = db.Column(db.Integer, default=0)
    valor_mensal = db.Column(db.Float, default=0.0)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class SvcInsumo(db.Model):
    """
    Insumos (uniformes, EPIs, materiais)
    """
    __tablename__ = 'svc_insumos'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('svc_scenarios.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('svc_jobs.id'), nullable=True)
    
    lote_numero = db.Column(db.Integer, default=1)
    
    tipo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(300), nullable=False)
    
    custo_unitario = db.Column(db.Float, nullable=False)
    quantidade_por_posto = db.Column(db.Integer, default=1)
    periodicidade_meses = db.Column(db.Integer, default=12)
    
    cargo = db.Column(db.String(200), default='todos')
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class SvcDespesa(db.Model):
    """
    Despesas personalizáveis - NOVA TABELA V3
    Permite adicionar qualquer tipo de despesa
    """
    __tablename__ = 'svc_despesas'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('svc_scenarios.id'), nullable=False)
    
    # Agrupamento
    lote_numero = db.Column(db.Integer, default=1)
    
    # Categoria da despesa
    categoria = db.Column(db.String(100), nullable=False)  # 'mao_obra', 'material', 'equipamento', 'operacional', 'administrativa', 'bdi', 'outra'
    subcategoria = db.Column(db.String(100), nullable=True)
    
    # Descrição
    descricao = db.Column(db.String(300), nullable=False)
    unidade = db.Column(db.String(50), default='un')  # un, m², m³, kg, h, mês, etc.
    
    # Valores
    quantidade = db.Column(db.Float, default=1.0)
    valor_unitario = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    
    # Periodicidade (para despesas recorrentes)
    periodicidade = db.Column(db.String(50), default='unica')  # unica, mensal, trimestral, anual
    
    # Incidência de encargos/tributos
    incide_encargos = db.Column(db.Boolean, default=False)
    incide_tributos = db.Column(db.Boolean, default=True)
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class SvcOutput(db.Model):
    """
    Snapshots e relatórios gerados
    """
    __tablename__ = 'svc_outputs'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('svc_scenarios.id'), nullable=False)
    
    tipo = db.Column(db.String(50), nullable=False)
    resultado_json = db.Column(db.Text, nullable=True)
    arquivo_path = db.Column(db.String(500), nullable=True)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_resultado(self):
        if self.resultado_json:
            return json.loads(self.resultado_json)
        return {}
    
    def set_resultado(self, data):
        self.resultado_json = json.dumps(data, ensure_ascii=False)
