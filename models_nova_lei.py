"""
Modelos do Módulo: Calculadora de Serviços - Nova Lei
Arquivo isolado para manter modularidade
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# Usar a mesma instância db do models.py principal
from models import db


class SvcScenario(db.Model):
    """
    Tabela para cenários de cálculo (versões, parâmetros de tributos/CITL)
    """
    __tablename__ = 'svc_scenarios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)
    
    # Identificação
    nome_cenario = db.Column(db.String(200), nullable=False)  # 'Base', 'Agressivo', 'Conservador'
    tipo_servico = db.Column(db.String(100), nullable=False)  # 'Portaria', 'Limpeza', 'Copeiragem', etc.
    
    # Dados da Empresa
    cnpj = db.Column(db.String(18))
    razao_social = db.Column(db.String(200))
    endereco = db.Column(db.Text)
    
    # Dados do Órgão/Processo
    numero_processo = db.Column(db.String(100))
    validade_proposta = db.Column(db.Integer)  # em dias
    prazo_pagamento = db.Column(db.String(100))
    local_execucao = db.Column(db.String(200))
    prazo_execucao = db.Column(db.Integer)  # em meses
    
    # Status da proposta
    status = db.Column(db.String(50), default='habilitação')  # habilitação, adjudica, perdida, anulada, prazo vencido
    valor_total = db.Column(db.Float, default=0.0)
    
    # Parâmetros de Encargos (editáveis)
    inss_patronal = db.Column(db.Float, default=20.0)
    salario_educacao = db.Column(db.Float, default=2.5)
    rat_sat = db.Column(db.Float, default=3.0)
    fap_multiplicador = db.Column(db.Float, default=1.0)
    sesc_senac = db.Column(db.Float, default=1.5)
    sebrae = db.Column(db.Float, default=0.6)
    incra = db.Column(db.Float, default=0.2)
    
    # Tributos
    regime_tributario = db.Column(db.String(50), default='simples')  # 'simples', 'presumido', 'real'
    pis_cofins_cumulativo = db.Column(db.Boolean, default=False)
    aliquota_pis = db.Column(db.Float, default=0.65)
    aliquota_cofins = db.Column(db.Float, default=3.0)
    aliquota_iss = db.Column(db.Float, default=5.0)
    aliquota_simples = db.Column(db.Float, default=14.0)
    anexo_simples = db.Column(db.String(20), default='IV')
    
    # CITL (Custos Indiretos, Tributos e Lucro)
    custos_indiretos_percentual = db.Column(db.Float, default=5.0)
    lucro_percentual = db.Column(db.Float, default=8.0)
    
    # Metadata
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)  # Alias para compatibilidade
    
    # Relacionamentos
    jobs = db.relationship('SvcJob', backref='scenario', lazy=True, cascade='all, delete-orphan')
    benefits = db.relationship('SvcBenefit', backref='scenario', lazy=True, cascade='all, delete-orphan')
    insumos = db.relationship('SvcInsumo', backref='scenario', lazy=True, cascade='all, delete-orphan')
    outputs = db.relationship('SvcOutput', backref='scenario', lazy=True, cascade='all, delete-orphan')


class SvcJob(db.Model):
    """
    Tabela para armazenar perfis/postos de trabalho
    (CBO, jornada, salário-base, adicionais)
    """
    __tablename__ = 'svc_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('svc_scenarios.id'), nullable=False)
    
    # Lote (para agrupar postos)
    lote_numero = db.Column(db.Integer, default=1)
    lote_nome = db.Column(db.String(200), default='Lote 1')
    
    # Dados do posto
    cargo = db.Column(db.String(200), nullable=False)
    cbo = db.Column(db.String(20), nullable=True)
    quantidade_postos = db.Column(db.Integer, nullable=False, default=1)
    
    # Jornada
    jornada_tipo = db.Column(db.String(50), nullable=False)  # '44h', '40h', '12x36_diurno', '12x36_noturno'
    horas_semanais = db.Column(db.Float, nullable=True)
    
    # Remuneração
    salario_base = db.Column(db.Float, nullable=False)
    adicional_insalubridade = db.Column(db.Float, default=0.0)
    adicional_periculosidade = db.Column(db.Float, default=0.0)
    adicional_noturno_percentual = db.Column(db.Float, default=20.0)  # 20% padrão CLT
    gratificacao = db.Column(db.Float, default=0.0)
    
    # CCT/Dissídio
    cct_referencia = db.Column(db.Text, nullable=True)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SvcBenefit(db.Model):
    """
    Tabela para benefícios (VT, VR/VA, saúde, cesta, etc.)
    """
    __tablename__ = 'svc_benefits'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('svc_scenarios.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('svc_jobs.id'), nullable=True)  # Pode ser por posto ou geral
    
    # Tipo de benefício
    tipo = db.Column(db.String(100), nullable=False)  # 'VT', 'VR', 'VA', 'saude', 'cesta', 'outro'
    
    # Valores
    valor_unitario = db.Column(db.Float, default=0.0)
    quantidade_dias = db.Column(db.Integer, default=0)  # Para VT, VR
    valor_mensal = db.Column(db.Float, default=0.0)  # Para saúde, cesta
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class SvcInsumo(db.Model):
    """
    Tabela para insumos (uniformes, EPIs, materiais)
    SEM natureza salarial
    """
    __tablename__ = 'svc_insumos'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('svc_scenarios.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('svc_jobs.id'), nullable=True)  # Pode ser por posto ou geral
    
    # Lote (para agrupar insumos)
    lote_numero = db.Column(db.Integer, default=1)
    
    # Tipo de insumo
    tipo = db.Column(db.String(100), nullable=False)  # 'uniforme', 'epi', 'material'
    descricao = db.Column(db.String(300), nullable=False)
    
    # Custo e periodicidade
    custo_unitario = db.Column(db.Float, nullable=False)
    quantidade_por_posto = db.Column(db.Integer, default=1)
    periodicidade_meses = db.Column(db.Integer, default=12)  # Vida útil em meses
    
    # Aplicação
    cargo = db.Column(db.String(200), default='todos')  # 'todos' ou cargo específico
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class SvcOutput(db.Model):
    """
    Tabela para snapshots e PDFs/planilhas geradas
    """
    __tablename__ = 'svc_outputs'
    
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('svc_scenarios.id'), nullable=False)
    
    # Tipo de saída
    tipo = db.Column(db.String(50), nullable=False)  # 'pdf', 'excel', 'json'
    
    # Resultado do cálculo (JSON)
    resultado_json = db.Column(db.Text, nullable=True)
    
    # Arquivo gerado
    arquivo_path = db.Column(db.String(500), nullable=True)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_resultado(self):
        """Retorna o resultado como dicionário Python"""
        if self.resultado_json:
            return json.loads(self.resultado_json)
        return {}
    
    def set_resultado(self, data):
        """Salva o resultado como JSON"""
        self.resultado_json = json.dumps(data, ensure_ascii=False)
