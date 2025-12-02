"""
Gerador de PDF Timbrado - Módulo Nova Lei
Segue o padrão do sistema (imprimir_proposta)
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from io import BytesIO
from datetime import datetime


class GeradorPDFNovaLei:
    """
    Gera PDF timbrado para propostas de serviços
    """
    
    def __init__(self, empresa, cenario, resultado_calculo):
        self.empresa = empresa
        self.cenario = cenario
        self.resultado = resultado_calculo
        
        # Configurações
        self.buffer = BytesIO()
        self.pdf = canvas.Canvas(self.buffer, pagesize=A4)
        self.width, self.height = A4
        self.MARGIN_X = 50
        self.MARGIN_Y = 50
        self.CONTENT_WIDTH = self.width - 2 * self.MARGIN_X
        self.y = self.height - self.MARGIN_Y
        self.pagina_inicial = True
    
    def gerar(self):
        """
        Gera o PDF completo
        """
        self.desenha_marca_dagua()
        self.desenha_cabecalho()
        self.desenha_dados_proposta()
        self.desenha_resumo_financeiro()
        self.desenha_detalhamento_custos()
        self.desenha_rodape()
        
        self.pdf.save()
        self.buffer.seek(0)
        return self.buffer
    
    def desenha_marca_dagua(self):
        """Adiciona marca d'água da empresa"""
        if self.empresa and self.empresa.logo:
            try:
                self.pdf.saveState()
                self.pdf.setFillAlpha(0.1)
                logo = ImageReader(self.empresa.logo)
                self.pdf.drawImage(
                    logo,
                    self.width / 4,
                    self.height / 3,
                    width=300,
                    height=150,
                    mask='auto'
                )
                self.pdf.restoreState()
            except Exception as e:
                print(f"Erro ao carregar marca d'água: {e}")
    
    def desenha_cabecalho(self):
        """Desenha cabeçalho timbrado"""
        # Logo centralizada
        logo_width = 120
        logo_height = 60
        logo_x = (self.width - logo_width) / 2
        
        if self.empresa and self.empresa.logo:
            try:
                logo = ImageReader(self.empresa.logo)
                self.pdf.drawImage(
                    logo,
                    logo_x,
                    self.y - logo_height,
                    width=logo_width,
                    height=logo_height,
                    mask='auto'
                )
            except Exception as e:
                print(f"Erro ao carregar logo: {e}")
        
        self.y -= logo_height + 30
        
        # Título
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.drawCentredString(self.width / 2, self.y, "PROPOSTA DE SERVIÇOS - NOVA LEI")
        self.y -= 30
        
        # Box com dados da empresa
        if self.empresa:
            max_width = self.CONTENT_WIDTH - 20
            style = ParagraphStyle('normal', fontName="Helvetica", fontSize=10, leading=12)
            
            info_empresa = [
                f"Razão Social: {self.empresa.razao_social}",
                f"CNPJ: {self.empresa.cnpj}",
                f"Endereço: {self.empresa.endereco}",
                f"Telefone: {self.empresa.telefone if self.empresa.telefone else 'Não informado'}",
                f"E-mail: {self.empresa.email if self.empresa.email else 'Não informado'}"
            ]
            
            # Calcular altura do box
            total_height = 20
            paragraph_heights = []
            
            for linha in info_empresa:
                p = Paragraph(linha, style)
                w, h = p.wrap(max_width, 0)
                paragraph_heights.append(h)
                total_height += h + 5
            
            total_height += 10
            
            # Desenhar box
            self.y -= total_height
            self.pdf.rect(self.MARGIN_X, self.y, self.CONTENT_WIDTH, total_height, stroke=1, fill=0)
            
            # Escrever conteúdo
            linha_y = self.y + total_height - 15
            for i, linha in enumerate(info_empresa):
                p = Paragraph(linha, style)
                w, h = p.wrap(max_width, 0)
                p.drawOn(self.pdf, self.MARGIN_X + 10, linha_y - h)
                linha_y -= h + 5
            
            self.y -= 30
    
    def desenha_dados_proposta(self):
        """Desenha dados da proposta"""
        self.pdf.setFont("Helvetica-Bold", 12)
        self.pdf.drawString(self.MARGIN_X, self.y, "Dados da Proposta:")
        self.y -= 15
        
        self.pdf.setFont("Helvetica", 10)
        
        dados = [
            f"Proposta ID: {self.cenario.id}",
            f"Tipo de Serviço: {self.cenario.tipo_servico}",
            f"Órgão Vinculado: {self.cenario.razao_social or 'Não informado'}",
            f"Número do Processo: {self.cenario.numero_processo or 'Não informado'}",
            f"Local de Execução: {self.cenario.local_execucao or 'Não informado'}",
            f"Prazo de Execução: {self.cenario.prazo_execucao or 0} meses",
            f"Validade da Proposta: {self.cenario.validade_proposta or 0} dias",
            f"Data de Criação: {self.cenario.criado_em.strftime('%d/%m/%Y %H:%M') if self.cenario.criado_em else 'Não informado'}"
        ]
        
        for linha in dados:
            self.pdf.drawString(self.MARGIN_X + 10, self.y, linha)
            self.y -= 15
        
        self.y -= 20
    
    def desenha_resumo_financeiro(self):
        """Desenha resumo financeiro"""
        self.pdf.setFont("Helvetica-Bold", 12)
        self.pdf.drawString(self.MARGIN_X, self.y, "Resumo Financeiro:")
        self.y -= 20
        
        # Tabela de resumo
        total = self.resultado.get('total_contrato', {})
        
        dados_resumo = [
            ("Remuneração", total.get('total_remuneracao', 0)),
            ("Encargos e Benefícios", total.get('total_encargos_beneficios', 0)),
            ("Provisões", total.get('total_provisoes', 0)),
            ("Reposição", total.get('total_reposicao', 0)),
            ("Insumos", total.get('total_insumos', 0)),
            ("Subtotal", total.get('subtotal_antes_citl', 0)),
            ("Custos Indiretos", total.get('custos_indiretos', 0)),
            ("Tributos", total.get('tributos', 0)),
            ("Lucro", total.get('lucro', 0)),
        ]
        
        self.pdf.setFont("Helvetica", 10)
        
        for descricao, valor in dados_resumo:
            self.pdf.drawString(self.MARGIN_X + 10, self.y, descricao)
            self.pdf.drawRightString(self.width - self.MARGIN_X - 10, self.y, f"R$ {valor:,.2f}")
            self.y -= 15
        
        # Linha separadora
        self.pdf.line(self.MARGIN_X, self.y, self.width - self.MARGIN_X, self.y)
        self.y -= 20
        
        # Total geral
        self.pdf.setFont("Helvetica-Bold", 12)
        self.pdf.drawString(self.MARGIN_X + 10, self.y, "VALOR TOTAL DA PROPOSTA")
        self.pdf.drawRightString(
            self.width - self.MARGIN_X - 10,
            self.y,
            f"R$ {total.get('total_contrato', 0):,.2f}"
        )
        self.y -= 30
    
    def desenha_detalhamento_custos(self):
        """Desenha detalhamento dos custos por posto"""
        self.verifica_espaco(200)
        
        self.pdf.setFont("Helvetica-Bold", 12)
        self.pdf.drawString(self.MARGIN_X, self.y, "Detalhamento por Posto:")
        self.y -= 20
        
        postos = self.resultado.get('postos', [])
        
        self.pdf.setFont("Helvetica", 9)
        
        for posto in postos:
            self.verifica_espaco(80)
            
            # Cabeçalho do posto
            self.pdf.setFont("Helvetica-Bold", 10)
            self.pdf.drawString(
                self.MARGIN_X + 10,
                self.y,
                f"{posto['cargo']} - Quantidade: {posto['quantidade_postos']}"
            )
            self.y -= 15
            
            self.pdf.setFont("Helvetica", 9)
            
            # Detalhes
            detalhes = [
                f"  Remuneração: R$ {posto['modulo_1_remuneracao']['total']:,.2f}",
                f"  Encargos: R$ {posto['modulo_2_encargos_beneficios']['total']:,.2f}",
                f"  Provisões: R$ {posto['modulo_3_provisoes']['total']:,.2f}",
                f"  Reposição: R$ {posto['modulo_4_reposicao']['total']:,.2f}",
                f"  Insumos: R$ {posto['modulo_5_insumos']['total']:,.2f}",
                f"  Subtotal: R$ {posto['subtotal_antes_citl']:,.2f}",
                f"  CITL: R$ {posto['modulo_6_citl']['total']:,.2f}",
                f"  Total Unitário: R$ {posto['total_unitario']:,.2f}",
                f"  Total Posto: R$ {posto['total_posto']:,.2f}"
            ]
            
            for detalhe in detalhes:
                self.pdf.drawString(self.MARGIN_X + 20, self.y, detalhe)
                self.y -= 12
            
            self.y -= 10
    
    def desenha_rodape(self):
        """Desenha rodapé em todas as páginas"""
        self.pdf.setFont("Helvetica", 8)
        self.pdf.drawCentredString(
            self.width / 2,
            30,
            f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} - Precificalá"
        )
    
    def verifica_espaco(self, altura_necessaria):
        """Verifica se há espaço na página, senão cria nova"""
        if self.y - altura_necessaria < self.MARGIN_Y + 50:
            self.pdf.showPage()
            self.desenha_marca_dagua()
            self.desenha_rodape()
            self.y = self.height - self.MARGIN_Y
            self.pagina_inicial = False
