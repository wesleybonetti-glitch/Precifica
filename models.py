from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import json  # ✅ ADICIONAR ESTA LINHA
from flask_login import current_user
from flask import current_app as app
db = SQLAlchemy()
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="ativo")
    data_ativacao = db.Column(db.DateTime, nullable=True)
    registros = db.relationship('Registro', backref='usuario', lazy=True)
    subusuarios = db.relationship('Subusuario', backref='user_principal', lazy=True)

    @property
    def is_active(self):
        return self.status == "ativo"

class Subusuario(UserMixin, db.Model):
    __tablename__ = 'subusuario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="ativo")
    user_principal_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @property
    def is_active(self):
        return self.status == "ativo"
class Registro(db.Model):
    __tablename__ = 'registro'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)  # Certifique-se deste atributo
    descricao = db.Column(db.Text, nullable=True)

class LogAcesso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_principal_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    acao = db.Column(db.String(255), nullable=False)  # Ex: "Login realizado", "Proposta alterada"
    ip = db.Column(db.String(50), nullable=False)  # Endereço IP do usuário
    data = db.Column(db.DateTime, default=datetime.utcnow)  # Data da ação

    def __repr__(self):
        return f"<Log {self.id} - {self.acao} - {self.data}>"
# Em models.py

class CalculadoraPasso1(db.Model):
    __tablename__ = 'calculadora_passo1'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)
    cnpj = db.Column(db.String(20), nullable=False)
    razao_social = db.Column(db.String(255), nullable=False)
    endereco = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Disputa")
    numero_processo = db.Column(db.String(100), nullable=False)
    validade_proposta = db.Column(db.Integer, nullable=False)
    prazo_pagamento = db.Column(db.String(50), nullable=False)
    local_entrega = db.Column(db.String(255), nullable=False)
    prazo_entrega = db.Column(db.Integer, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    produtos = db.relationship('Produto', backref='proposta', lazy=True)
    # Correção: Alterado de Float para Numeric
    frete = db.Column(db.Numeric(15, 4), nullable=True)

# Em models.py

class Produto(db.Model):
    __tablename__ = 'produto'
    id = db.Column(db.Integer, primary_key=True)
    numero_item = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.Text, nullable=False)
    marca_modelo = db.Column(db.String(200), nullable=False)
    # Correção: Alterado de Float para Numeric para garantir precisão decimal de até 4 casas
    custo = db.Column(db.Numeric(15, 4), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    unidade_medida = db.Column(db.String(50), nullable=False)
    # Correção: Alterado de Float para Numeric
    referencia = db.Column(db.Numeric(15, 4), nullable=True)
    # Correção: Alterado de Float para Numeric
    venda = db.Column(db.Numeric(15, 4), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)
    calculadora_passo1_id = db.Column(db.Integer, db.ForeignKey('calculadora_passo1.id'), nullable=False)
    # Correção: Alterado de Float para Numeric
    frete = db.Column(db.Numeric(15, 4), nullable=True)
    custo_total = db.Column(db.Numeric(15, 4), nullable=True)
    referencia_total = db.Column(db.Numeric(15, 4), nullable=True)
    imposto_total = db.Column(db.Numeric(15, 4), nullable=True)
    valor_total_venda = db.Column(db.Numeric(15, 4), nullable=True)
    lucro_total = db.Column(db.Numeric(15, 4), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    url_produto = db.Column(db.String(500), nullable=True)
    status_item = db.Column(db.String(50), nullable=True, default='Aguardando')
    # ➜ ADICIONE ESTES DOIS CAMPOS:
    produto_fornecedor_id = db.Column(
        db.Integer,
        db.ForeignKey('produtos_fornecedores.id'),
        nullable=True
    )
    produto_fornecedor = db.relationship(
        'ProdutosFornecedores',
        lazy='joined',
        backref=db.backref('itens_simulacao', lazy='dynamic')
    )

class Empresa(db.Model):
    __tablename__ = 'empresa'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    razao_social = db.Column(db.String(200), nullable=True)
    endereco = db.Column(db.String(300), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    capital_social = db.Column(db.String(50), nullable=True)
    atividade_principal = db.Column(db.String(300), nullable=True)
    atividades_secundarias = db.Column(db.Text, nullable=True)
    nome_socio = db.Column(db.String(150), nullable=True)
    cpf_socio = db.Column(db.String(14), nullable=True)
    logo = db.Column(db.String(300), nullable=True)
    regime_tributacao = db.Column(db.String(50), nullable=True)
    imposto_venda = db.Column(db.Numeric(10, 4), nullable=True)
    banco = db.Column(db.String(100), nullable=True)
    agencia = db.Column(db.String(10), nullable=True)
    conta = db.Column(db.String(20), nullable=True)
    pix = db.Column(db.String(200), nullable=True)
    nome_conta = db.Column(db.String(150), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    validade = db.Column(db.Date, nullable=True)
    arquivo = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='pendente')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)
    data_atualizacao = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref=db.backref('documentos', lazy=True))
    subusuario = db.relationship('Subusuario', backref=db.backref('documentos', lazy=True))
class Fornecedor(db.Model):
    __tablename__ = 'fornecedor'
    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    nome_empresa = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(255))
    atividade_principal = db.Column(db.String(255))  # Linha em questão
    contato = db.Column(db.String(100))
    nome_vendedor = db.Column(db.String(100))
    contato_vendedor = db.Column(db.String(100))
    comentario = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

class AvaliacaoFornecedor(db.Model):
    __tablename__ = 'avaliacao_fornecedor'
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedor.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nota_prazo = db.Column(db.Integer, nullable=False)
    nota_qualidade = db.Column(db.Integer, nullable=False)
    nota_preco = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text, nullable=True)
    data_avaliacao = db.Column(db.DateTime, default=datetime.utcnow)

class Banner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(512), nullable=False)

class ChamadoSuporte(db.Model):
        __tablename__ = 'chamados_suporte'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        titulo = db.Column(db.String(100), nullable=False)
        descricao = db.Column(db.Text, nullable=False)
        anexo = db.Column(db.String(255), nullable=True)
        status = db.Column(db.String(20), default='Aberto')
        resposta = db.Column(db.Text, nullable=True)
        anexo_resposta = db.Column(db.String(255), nullable=True)
        data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
        data_resposta = db.Column(db.DateTime, nullable=True)

        usuario = db.relationship('User', backref='chamados')

class RespostaChamado(db.Model):
    __tablename__ = 'resposta_chamado'

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados_suporte.id'), nullable=False)
    autor = db.Column(db.String(50), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    anexo = db.Column(db.String(255), nullable=True)  # Se não existir, adicione!
    data = db.Column(db.DateTime, default=datetime.utcnow)

    chamado = db.relationship('ChamadoSuporte', backref=db.backref('respostas', lazy=True))


class FornecedorProdutos(db.Model):
    __tablename__ = 'fornecedor_produtos'
    id = db.Column(db.Integer, primary_key=True)

    # CORREÇÃO: Remover unique=True para permitir CNPJ duplicado entre usuários
    cnpj = db.Column(db.String(20), nullable=False)  # Removido unique=True

    nome_empresa = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(255), nullable=True)
    atividade_principal = db.Column(db.String(255), nullable=True)
    contato = db.Column(db.String(100), nullable=True)
    nome_vendedor = db.Column(db.String(100), nullable=True)
    contato_vendedor = db.Column(db.String(100), nullable=True)
    comentario = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com produtos
    produtos = db.relationship('ProdutosFornecedores', backref='fornecedor', lazy=True)

    # NOVA CONSTRAINT: CNPJ único apenas por usuário
    __table_args__ = (
        db.UniqueConstraint('cnpj', 'user_id', name='unique_cnpj_per_user'),
    )
class ProdutosFornecedores(db.Model):
    __tablename__ = 'produtos_fornecedores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    marca = db.Column(db.String(100), nullable=True)
    modelo = db.Column(db.String(100), nullable=True)
    unidade_medida = db.Column(db.String(50), nullable=True)
    custo = db.Column(db.Float, nullable=False)
    # CORREÇÃO PRINCIPAL: Permitir NULL no fornecedor_id
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedor_produtos.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    detalhes_rel = db.relationship('ProdutoDetalhes', backref='produto', uselist=False, cascade='all, delete-orphan')

    @property
    def tem_foto(self):
        """Verifica se o produto tem foto"""
        detalhes = ProdutoDetalhes.query.filter_by(produto_id=self.id).first()
        return bool(detalhes and detalhes.foto_url)

    @property
    def tem_descricao(self):
        """Verifica se o produto tem descrição"""
        detalhes = ProdutoDetalhes.query.filter_by(produto_id=self.id).first()
        return bool(detalhes and detalhes.descricao_detalhada)

    @property
    def foto_url_prop(self):
        """Retorna URL da foto"""
        detalhes = ProdutoDetalhes.query.filter_by(produto_id=self.id).first()
        return detalhes.foto_url if detalhes else None

    @property
    def descricao_preview(self):
        """Retorna preview da descrição"""
        detalhes = ProdutoDetalhes.query.filter_by(produto_id=self.id).first()
        if detalhes and detalhes.descricao_detalhada:
            if len(detalhes.descricao_detalhada) > 100:
                return detalhes.descricao_detalhada[:100] + '...'
            return detalhes.descricao_detalhada
        return None

    def get_detalhes(self):
        """Retorna detalhes do produto"""
        return ProdutoDetalhes.query.filter_by(produto_id=self.id).first()


class Lote(db.Model):
    __tablename__ = 'lote'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)

    # Referenciar corretamente tanto produtos quanto serviços
    proposta_id = db.Column(db.Integer, db.ForeignKey('calculadora_passo1.id'), nullable=True)
    proposta_servico_id = db.Column(db.Integer, db.ForeignKey('calculadora_passo1_servicos.id'), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Adicionando a coluna para diferenciar os tipos
    proposta_tipo = db.Column(db.String(20), nullable=False, default="produto")  # "produto" ou "servico"

    servicos = db.relationship('Servico', backref='lote', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('nome', 'proposta_id', name='unique_lote_proposta'),
        db.CheckConstraint(
            "(proposta_id IS NOT NULL AND proposta_servico_id IS NULL) OR "
            "(proposta_id IS NULL AND proposta_servico_id IS NOT NULL)",
            name="check_lote_proposta"
        )
    )


class Servico(db.Model):
    __tablename__ = 'servico'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)  # Permite textos muito longos sem limite fixo
    unidade_medida = db.Column(db.String(50), nullable=False)
    custo_unitario = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    valor_venda = db.Column(db.Float, nullable=False)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    #__table_args__ = (
    #    db.UniqueConstraint('nome', 'lote_id', name='unique_servico_lote'),
  #  )


class Despesa(db.Model):
    __tablename__ = 'despesa'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Float, nullable=False)

    # Relacionamento correto com as duas tabelas de proposta
    proposta_id = db.Column(db.Integer, db.ForeignKey('calculadora_passo1.id'), nullable=True)
    proposta_servico_id = db.Column(db.Integer, db.ForeignKey('calculadora_passo1_servicos.id'), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)
    tipo = db.Column(db.String(50), nullable=False, default="variavel")  # Tipo de despesa
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


class CalculadoraPasso1Servicos(db.Model):
    __tablename__ = 'calculadora_passo1_servicos'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)
    cnpj = db.Column(db.String(20), nullable=False)
    razao_social = db.Column(db.String(255), nullable=False)
    endereco = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Disputa")
    numero_processo = db.Column(db.String(100), nullable=False)
    validade_proposta = db.Column(db.Integer, nullable=False)
    prazo_pagamento = db.Column(db.String(50), nullable=False)
    local_execucao = db.Column(db.String(255), nullable=False)
    prazo_execucao = db.Column(db.Integer, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com os lotes de serviços
    lotes = db.relationship('Lote', backref='proposta_servico', lazy=True)
    # Adicionar esta classe ao seu arquivo models.py existente


class CalculadoraSessao(db.Model):
    """
    Modelo para armazenar sessões de recuperação da calculadora
    """
    __tablename__ = 'calculadora_sessoes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)

    # Dados da sessão em JSON
    dados_sessao = db.Column(db.Text, nullable=False)  # JSON string
    passo_atual = db.Column(db.Integer, default=1)  # 1 ou 2

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))

    # Relacionamentos
    user = db.relationship('User', backref='calculadora_sessoes')
    subusuario = db.relationship('Subusuario', backref='calculadora_sessoes')

    def __repr__(self):
        return f'<CalculadoraSessao {self.id} - User {self.user_id} - Passo {self.passo_atual}>'

    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subusuario_id': self.subusuario_id,
            'dados_sessao': json.loads(self.dados_sessao) if self.dados_sessao else {},
            'passo_atual': self.passo_atual,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    def is_expired(self):
        """Verifica se a sessão expirou"""
        return datetime.utcnow() > self.expires_at

    def set_dados_sessao(self, dados):
        """Define os dados da sessão (converte para JSON)"""
        self.dados_sessao = json.dumps(dados)

    def get_dados_sessao(self):
        """Retorna os dados da sessão (converte de JSON)"""
        return json.loads(self.dados_sessao) if self.dados_sessao else {}


# ===== FUNÇÃO AUXILIAR PARA LIMPAR SESSÃO =====

def limpar_sessao_calculadora_atual():
    """
    Limpa a sessão de recuperação do usuário atual
    Deve ser chamada após finalizar uma licitação com sucesso
    """
    try:
        if not current_user.is_authenticated:
            return False

        # Determinar o usuário principal e o subusuário
        if isinstance(current_user, Subusuario):
            user_principal_id = current_user.user_principal_id
            subusuario_id = current_user.id
        else:
            user_principal_id = current_user.id
            subusuario_id = None

        # Buscar sessão ativa
        sessao = CalculadoraSessao.query.filter_by(
            user_id=user_principal_id,
            subusuario_id=subusuario_id
        ).first()

        if sessao:
            db.session.delete(sessao)
            db.session.commit()
            app.logger.info(f"✅ Sessão {sessao.id} removida automaticamente - Licitação finalizada")
            return True
        else:
            app.logger.info("ℹ️ Nenhuma sessão encontrada para limpar")
            return False

    except Exception as e:
        app.logger.error(f"❌ Erro ao limpar sessão automaticamente: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass
        return False

class CalculadoraSessaoServicos(db.Model):
        """
        Modelo para armazenar sessões de recuperação da calculadora de serviços
        """
        __tablename__ = 'calculadora_sessoes_servicos'

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        subusuario_id = db.Column(db.Integer, db.ForeignKey('subusuario.id'), nullable=True)

        # Dados da sessão em JSON
        dados_sessao = db.Column(db.Text, nullable=False)  # JSON string
        passo_atual = db.Column(db.Integer, default=1)  # 1 ou 2

        # Timestamps
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))

        # Relacionamentos
        user = db.relationship('User', backref='calculadora_sessoes_servicos')
        subusuario = db.relationship('Subusuario', backref='calculadora_sessoes_servicos')

        def __repr__(self):
            return f'<CalculadoraSessaoServicos {self.id} - User {self.user_id} - Passo {self.passo_atual}>'

        def to_dict(self):
            """Converte para dicionário"""
            return {
                'id': self.id,
                'user_id': self.user_id,
                'subusuario_id': self.subusuario_id,
                'dados_sessao': json.loads(self.dados_sessao) if self.dados_sessao else {},
                'passo_atual': self.passo_atual,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None
            }

        def is_expired(self):
            """Verifica se a sessão expirou"""
            return datetime.utcnow() > self.expires_at

        def set_dados_sessao(self, dados):
            """Define os dados da sessão (converte para JSON)"""
            self.dados_sessao = json.dumps(dados)

        def get_dados_sessao(self):
            """Retorna os dados da sessão (converte de JSON)"""
            return json.loads(self.dados_sessao) if self.dados_sessao else {}

    # ===== FUNÇÃO AUXILIAR PARA LIMPAR SESSÃO DE SERVIÇOS =====

def limpar_sessao_servicos_atual():
    """
    Limpa a sessão de recuperação de serviços do usuário atual
    Deve ser chamada após finalizar uma precificação de serviços com sucesso
    """
    try:
        if not current_user.is_authenticated:
            return False

        # Determinar o usuário principal e o subusuário
        if isinstance(current_user, Subusuario):
            user_principal_id = current_user.user_principal_id
            subusuario_id = current_user.id
        else:
            user_principal_id = current_user.id
            subusuario_id = None

        # Buscar sessão ativa
        sessao = CalculadoraSessaoServicos.query.filter_by(
            user_id=user_principal_id,
            subusuario_id=subusuario_id
        ).first()

        if sessao:
            db.session.delete(sessao)
            db.session.commit()
            app.logger.info(f"✅ Sessão de serviços {sessao.id} removida automaticamente - Precificação finalizada")
            return True
        else:
            app.logger.info("ℹ️ Nenhuma sessão de serviços encontrada para limpar")
            return False

    except Exception as e:
        app.logger.error(f"❌ Erro ao limpar sessão de serviços automaticamente: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass
        return False


# Usar a instância db existente
# db = SQLAlchemy()  # Esta linha já existe no seu models.py

# ============================================================================
# NOVAS TABELAS PARA CONFORMIDADE COM LEGISLAÇÃO
# ============================================================================

class ParametrosLegislacao(db.Model):
    """
    Tabela para armazenar parâmetros da legislação que podem mudar
    Permite atualizar percentuais sem alterar código
    """
    __tablename__ = 'parametros_legislacao'

    id = db.Column(db.Integer, primary_key=True)
    nome_parametro = db.Column(db.String(100), nullable=False, unique=True)
    valor_percentual = db.Column(db.Numeric(5, 2), nullable=False)  # Ex: 20.00 para 20%
    descricao = db.Column(db.Text, nullable=True)
    data_vigencia = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ParametroLegislacao {self.nome_parametro}: {self.valor_percentual}%>'


class SegmentoServico(db.Model):
    """
    Tabela para definir segmentos de serviços com parâmetros específicos
    Ex: Vigilância, Limpeza, TI, Saúde, etc.
    """
    __tablename__ = 'segmento_servico'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)

    # Percentuais específicos do segmento
    citl_minimo = db.Column(db.Numeric(5, 2), nullable=False, default=16.00)
    citl_maximo = db.Column(db.Numeric(5, 2), nullable=False, default=30.00)
    custo_indireto_min = db.Column(db.Numeric(5, 2), nullable=False, default=2.00)
    custo_indireto_max = db.Column(db.Numeric(5, 2), nullable=False, default=6.00)

    # Características do segmento
    tem_periculosidade = db.Column(db.Boolean, default=False)
    tem_insalubridade = db.Column(db.Boolean, default=False)
    grau_risco_padrao = db.Column(db.Integer, default=2)  # 1=baixo, 2=médio, 3=alto

    # Tributos específicos
    pis_cofins_cumulativo = db.Column(db.Boolean, default=True)

    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SegmentoServico {self.nome}>'


class ConvencaoColetiva(db.Model):
    """
    Tabela para armazenar dados de convenções coletivas por categoria
    """
    __tablename__ = 'convencao_coletiva'

    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False)
    sindicato = db.Column(db.String(200), nullable=True)
    uf = db.Column(db.String(2), nullable=False)

    # Valores da convenção
    salario_base = db.Column(db.Numeric(10, 2), nullable=False)
    vale_transporte = db.Column(db.Numeric(8, 2), nullable=True)
    vale_refeicao = db.Column(db.Numeric(8, 2), nullable=True)
    auxilio_saude = db.Column(db.Numeric(8, 2), nullable=True)
    outros_beneficios = db.Column(db.Text, nullable=True)  # JSON com outros benefícios

    # Adicionais específicos
    adicional_noturno = db.Column(db.Numeric(5, 2), default=20.00)  # 20%
    adicional_periculosidade = db.Column(db.Numeric(5, 2), default=30.00)  # 30%

    # Vigência
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    ativo = db.Column(db.Boolean, default=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ConvencaoColetiva {self.categoria} - {self.uf}>'


# ============================================================================
# EXTENSÕES DAS TABELAS EXISTENTES
# ============================================================================

# IMPORTANTE: Adicione estes campos às tabelas existentes via migration
# NÃO recrie as tabelas, apenas adicione os campos

"""
-- SQL para adicionar campos à tabela 'servico' existente:

ALTER TABLE servico ADD COLUMN segmento_id INTEGER;
ALTER TABLE servico ADD COLUMN convencao_coletiva_id INTEGER;
ALTER TABLE servico ADD COLUMN dados_legislacao TEXT; -- JSON com dados específicos
ALTER TABLE servico ADD COLUMN custo_direto DECIMAL(12,2);
ALTER TABLE servico ADD COLUMN custo_indireto DECIMAL(12,2);
ALTER TABLE servico ADD COLUMN tributos DECIMAL(12,2);
ALTER TABLE servico ADD COLUMN lucro DECIMAL(12,2);
ALTER TABLE servico ADD COLUMN percentual_citl DECIMAL(5,2);
ALTER TABLE servico ADD COLUMN preco_final_legislacao DECIMAL(12,2);

-- Adicionar foreign keys
ALTER TABLE servico ADD CONSTRAINT fk_servico_segmento 
    FOREIGN KEY (segmento_id) REFERENCES segmento_servico(id);
ALTER TABLE servico ADD CONSTRAINT fk_servico_convencao 
    FOREIGN KEY (convencao_coletiva_id) REFERENCES convencao_coletiva(id);

-- SQL para adicionar campos à tabela 'calculadora_passo1_servicos':

ALTER TABLE calculadora_passo1_servicos ADD COLUMN segmento_id INTEGER;
ALTER TABLE calculadora_passo1_servicos ADD COLUMN regime_tributario VARCHAR(50) DEFAULT 'lucro_presumido';
ALTER TABLE calculadora_passo1_servicos ADD COLUMN aliquota_iss DECIMAL(5,2) DEFAULT 5.00;
ALTER TABLE calculadora_passo1_servicos ADD COLUMN percentual_lucro DECIMAL(5,2) DEFAULT 6.79;
ALTER TABLE calculadora_passo1_servicos ADD COLUMN dados_calculo_legislacao TEXT; -- JSON com todos os cálculos

ALTER TABLE calculadora_passo1_servicos ADD CONSTRAINT fk_proposta_servico_segmento 
    FOREIGN KEY (segmento_id) REFERENCES segmento_servico(id);
"""


class ServicoLegislacao(db.Model):
    """
    Extensão da tabela Servico para dados específicos da legislação
    Mantém compatibilidade com dados existentes
    """
    __tablename__ = 'servico_legislacao'

    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False, unique=True)
    segmento_id = db.Column(db.Integer, db.ForeignKey('segmento_servico.id'), nullable=True)
    convencao_coletiva_id = db.Column(db.Integer, db.ForeignKey('convencao_coletiva.id'), nullable=True)

    # Dados específicos do trabalhador
    salario_base = db.Column(db.Numeric(10, 2), nullable=False)
    gratificacao_funcao = db.Column(db.Numeric(10, 2), default=0)
    adicional_periculosidade = db.Column(db.Boolean, default=False)
    adicional_insalubridade = db.Column(db.String(20), nullable=True)  # minimo, medio, maximo
    adicional_noturno = db.Column(db.Boolean, default=False)
    horas_noturnas_mes = db.Column(db.Integer, default=0)

    # Benefícios
    vale_transporte = db.Column(db.Numeric(8, 2), default=0)
    vale_refeicao = db.Column(db.Numeric(8, 2), default=0)
    auxilio_saude = db.Column(db.Numeric(8, 2), default=0)
    outros_beneficios = db.Column(db.Numeric(8, 2), default=0)

    # Insumos
    custo_uniformes = db.Column(db.Numeric(8, 2), default=0)
    custo_epis = db.Column(db.Numeric(8, 2), default=0)
    custo_materiais = db.Column(db.Numeric(8, 2), default=0)
    outros_insumos = db.Column(db.Numeric(8, 2), default=0)

    # Parâmetros de cálculo
    grau_risco = db.Column(db.Integer, default=2)  # 1, 2 ou 3
    fap = db.Column(db.Numeric(4, 2), default=1.00)  # Fator Acidentário
    turnover_estimado = db.Column(db.Numeric(4, 2), default=0.25)  # 25%

    # Regime tributário
    regime_tributario = db.Column(db.String(50), default='lucro_presumido')
    aliquota_iss = db.Column(db.Numeric(5, 2), default=5.00)
    aliquota_simples = db.Column(db.Numeric(5, 2), nullable=True)
    pis_cofins_cumulativo = db.Column(db.Boolean, default=True)

    # Percentuais CITL
    percentual_custo_indireto = db.Column(db.Numeric(5, 2), default=6.00)
    percentual_lucro = db.Column(db.Numeric(5, 2), default=6.79)

    # Resultados dos cálculos (armazenados para auditoria)
    custo_remuneracao = db.Column(db.Numeric(12, 2), nullable=True)
    custo_encargos = db.Column(db.Numeric(12, 2), nullable=True)
    custo_rescisao = db.Column(db.Numeric(12, 2), nullable=True)
    custo_reposicao = db.Column(db.Numeric(12, 2), nullable=True)
    custo_insumos_total = db.Column(db.Numeric(12, 2), nullable=True)
    custo_direto_total = db.Column(db.Numeric(12, 2), nullable=True)

    custos_indiretos = db.Column(db.Numeric(12, 2), nullable=True)
    tributos_total = db.Column(db.Numeric(12, 2), nullable=True)
    lucro_total = db.Column(db.Numeric(12, 2), nullable=True)
    citl_total = db.Column(db.Numeric(12, 2), nullable=True)
    percentual_citl = db.Column(db.Numeric(5, 2), nullable=True)

    preco_final_legislacao = db.Column(db.Numeric(12, 2), nullable=True)

    # Dados completos do cálculo em JSON para auditoria
    dados_calculo_completo = db.Column(db.Text, nullable=True)

    # Controle
    calculado_em = db.Column(db.DateTime, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    servico = db.relationship('Servico', backref=db.backref('legislacao', uselist=False))
    segmento = db.relationship('SegmentoServico', backref='servicos_legislacao')
    convencao = db.relationship('ConvencaoColetiva', backref='servicos_legislacao')

    def set_dados_calculo(self, dados_dict):
        """Armazena dados completos do cálculo em JSON"""
        self.dados_calculo_completo = json.dumps(dados_dict, default=str)

    def get_dados_calculo(self):
        """Recupera dados completos do cálculo"""
        if self.dados_calculo_completo:
            return json.loads(self.dados_calculo_completo)
        return {}

    def __repr__(self):
        return f'<ServicoLegislacao {self.servico_id}>'

# Em ProdutoDetalhes:
class ProdutoDetalhes(db.Model):
    __tablename__ = 'produto_detalhes'

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_fornecedores.id', ondelete='CASCADE'), nullable=False)
    foto_url = db.Column(db.String(500), nullable=True)
    descricao_detalhada = db.Column(db.Text, nullable=True)

class HistoricoCalculoLegislacao(db.Model):
    """
    Histórico de cálculos para auditoria e comparação
    """
    __tablename__ = 'historico_calculo_legislacao'

    id = db.Column(db.Integer, primary_key=True)
    servico_legislacao_id = db.Column(db.Integer, db.ForeignKey('servico_legislacao.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Snapshot dos dados no momento do cálculo
    dados_entrada = db.Column(db.Text, nullable=False)  # JSON
    dados_calculo = db.Column(db.Text, nullable=False)  # JSON
    preco_final = db.Column(db.Numeric(12, 2), nullable=False)

    # Metadados
    versao_calculo = db.Column(db.String(20), default='1.0')
    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    servico_legislacao = db.relationship('ServicoLegislacao', backref='historico_calculos')
    user = db.relationship('User', backref='historico_calculos_legislacao')

    def set_dados_entrada(self, dados_dict):
        self.dados_entrada = json.dumps(dados_dict, default=str)

    def get_dados_entrada(self):
        if self.dados_entrada:
            return json.loads(self.dados_entrada)
        return {}

    def set_dados_calculo(self, dados_dict):
        self.dados_calculo = json.dumps(dados_dict, default=str)

    def get_dados_calculo(self):
        if self.dados_calculo:
            return json.loads(self.dados_calculo)
        return {}

    def __repr__(self):
        return f'<HistoricoCalculo {self.id} - {self.criado_em}>'


# ============================================================================
# FUNÇÕES AUXILIARES PARA MIGRAÇÃO
# ============================================================================

def criar_parametros_padrao():
    """
    Cria parâmetros padrão da legislação na base de dados
    Execute esta função após criar as tabelas
    """
    parametros_padrao = [
        # Encargos Previdenciários
        ('inss_patronal', 20.00, 'INSS Patronal sobre folha de pagamento'),
        ('fgts', 8.00, 'FGTS sobre remuneração'),
        ('sat_grau_1', 1.00, 'SAT/GIIL-RAT - Grau de risco 1 (leve)'),
        ('sat_grau_2', 2.00, 'SAT/GIIL-RAT - Grau de risco 2 (médio)'),
        ('sat_grau_3', 3.00, 'SAT/GIIL-RAT - Grau de risco 3 (grave)'),

        # Férias e 13º
        ('decimo_terceiro', 8.33, '13º Salário (1/12 da remuneração)'),
        ('ferias', 8.33, 'Férias (1/12 da remuneração)'),
        ('adicional_ferias', 33.33, 'Adicional de férias (1/3)'),

        # Tributos
        ('pis_cumulativo', 0.65, 'PIS - Regime cumulativo'),
        ('cofins_cumulativo', 3.00, 'COFINS - Regime cumulativo'),
        ('pis_nao_cumulativo', 1.65, 'PIS - Regime não cumulativo'),
        ('cofins_nao_cumulativo', 7.60, 'COFINS - Regime não cumulativo'),
        ('iss_maximo', 5.00, 'ISS - Alíquota máxima'),

        # Lucro
        ('lucro_minimo', 3.90, 'Lucro mínimo (cenário de atenção)'),
        ('lucro_maximo', 6.79, 'Lucro máximo (cenário normal)'),

        # Custos Indiretos
        ('custo_indireto_min', 2.00, 'Custo indireto mínimo'),
        ('custo_indireto_max', 6.00, 'Custo indireto máximo'),
    ]

    for nome, valor, descricao in parametros_padrao:
        parametro = ParametrosLegislacao.query.filter_by(nome_parametro=nome).first()
        if not parametro:
            parametro = ParametrosLegislacao(
                nome_parametro=nome,
                valor_percentual=valor,
                descricao=descricao
            )
            db.session.add(parametro)

    db.session.commit()


def criar_segmentos_padrao():
    """
    Cria segmentos padrão de serviços
    """
    segmentos_padrao = [
        {
            'nome': 'Vigilância',
            'descricao': 'Serviços de vigilância patrimonial',
            'citl_minimo': 17.75,
            'citl_maximo': 25.35,
            'custo_indireto_min': 2.00,
            'custo_indireto_max': 6.00,
            'tem_periculosidade': True,
            'grau_risco_padrao': 3,
            'pis_cofins_cumulativo': True
        },
        {
            'nome': 'Limpeza e Conservação',
            'descricao': 'Serviços de limpeza e conservação predial',
            'citl_minimo': 16.04,
            'citl_maximo': 30.45,
            'custo_indireto_min': 3.50,
            'custo_indireto_max': 6.00,
            'tem_insalubridade': True,
            'grau_risco_padrao': 2,
            'pis_cofins_cumulativo': False
        },
        {
            'nome': 'Tecnologia da Informação',
            'descricao': 'Serviços de TI e desenvolvimento',
            'citl_minimo': 18.00,
            'citl_maximo': 28.00,
            'custo_indireto_min': 3.00,
            'custo_indireto_max': 5.00,
            'grau_risco_padrao': 1,
            'pis_cofins_cumulativo': False
        },
        {
            'nome': 'Saúde',
            'descricao': 'Serviços de saúde e assistência médica',
            'citl_minimo': 18.00,
            'citl_maximo': 28.00,
            'custo_indireto_min': 3.00,
            'custo_indireto_max': 5.00,
            'tem_insalubridade': True,
            'grau_risco_padrao': 2,
            'pis_cofins_cumulativo': False
        },
        {
            'nome': 'Engenharia',
            'descricao': 'Serviços de engenharia e consultoria técnica',
            'citl_minimo': 18.00,
            'citl_maximo': 28.00,
            'custo_indireto_min': 3.00,
            'custo_indireto_max': 5.00,
            'grau_risco_padrao': 2,
            'pis_cofins_cumulativo': False
        },
        {
            'nome': 'Geral',
            'descricao': 'Outros serviços não especificados',
            'citl_minimo': 18.00,
            'citl_maximo': 28.00,
            'custo_indireto_min': 3.00,
            'custo_indireto_max': 6.00,
            'grau_risco_padrao': 2,
            'pis_cofins_cumulativo': False
        }
    ]

    for dados_segmento in segmentos_padrao:
        segmento = SegmentoServico.query.filter_by(nome=dados_segmento['nome']).first()
        if not segmento:
            segmento = SegmentoServico(**dados_segmento)
            db.session.add(segmento)

    db.session.commit()


# ============================================================================
# SCRIPT DE MIGRAÇÃO
# ============================================================================

def executar_migracao_legislacao():
    """
    Executa a migração completa para conformidade com legislação
    EXECUTE APENAS UMA VEZ após backup da base de dados
    """
    try:
        # 1. Criar novas tabelas
        db.create_all()

        # 2. Criar dados padrão
        criar_parametros_padrao()
        criar_segmentos_padrao()

        print("✅ Migração executada com sucesso!")
        print("📋 Novas tabelas criadas:")
        print("   - parametros_legislacao")
        print("   - segmento_servico")
        print("   - convencao_coletiva")
        print("   - servico_legislacao")
        print("   - historico_calculo_legislacao")
        print()
        print("⚠️  IMPORTANTE: Execute os comandos SQL manualmente para adicionar")
        print("   campos às tabelas existentes (ver comentários no código)")

        return True

    except Exception as e:
        print(f"❌ Erro na migração: {str(e)}")
        db.session.rollback()
        return False