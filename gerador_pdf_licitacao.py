"""
Gerador de PDF Profissional para Licitações
Com lotes detalhados e BDI separado
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime


class GeradorPDFLicitacao:
    """
    Gera PDF profissional para licitações com:
    - Lotes detalhados
    - BDI separado e configurável
    - Formato exigido em licitações
    """
    
    def __init__(self, empresa, cenario, resultado_calculo, postos_por_lote):
        self.empresa = empresa
        self.cenario = cenario
        self.resultado = resultado_calculo
        self.postos_por_lote = postos_por_lote  # Dicionário: {lote_numero: [postos]}
        
        # Configurações
        self.buffer = BytesIO()
        self.pdf = canvas.Canvas(self.buffer, pagesize=A4)
        self.width, self.height = A4
        self.MARGIN_X = 50
        self.MARGIN_Y = 50
        self.CONTENT_WIDTH = self.width - 2 * self.MARGIN_X
        self.y = self.height - self.MARGIN_Y
        self.pagina_atual = 1
    
    def gerar(self):
        """Gera o PDF completo"""
        self.desenha_pagina_capa()
        self.pdf.showPage()
        self.pagina_atual += 1
        
        self.y = self.height - self.MARGIN_Y
        self.desenha_dados_proposta()
        self.desenha_resumo_geral()
        
        self.pdf.showPage()
        self.pagina_atual += 1
        
        self.y = self.height - self.MARGIN_Y
        self.desenha_detalhamento_lotes()
        
        self.pdf.showPage()
        self.pagina_atual += 1
        
        self.y = self.height - self.MARGIN_Y
        self.desenha_composicao_bdi()
        self.desenha_resumo_final()
        
        self.desenha_rodape_todas_paginas()
        
        self.pdf.save()
        self.buffer.seek(0)
        return self.buffer
    
    def desenha_pagina_capa(self):
        """Desenha página de capa"""
        # Logo centralizada
        if self.empresa and self.empresa.logo:
            try:
                logo_width = 150
                logo_height = 75
                logo_x = (self.width - logo_width) / 2
                logo = ImageReader(self.empresa.logo)
                self.pdf.drawImage(
                    logo,
                    logo_x,
                    self.height - 150,
                    width=logo_width,
                    height=logo_height,
                    mask='auto'
                )
            except Exception as e:
                print(f"Erro ao carregar logo: {e}")
        
        # Título principal
        self.pdf.setFont("Helvetica-Bold", 18)
        self.pdf.drawCentredString(self.width / 2, self.height - 250, "PROPOSTA TÉCNICA E COMERCIAL")
        
        self.pdf.setFont("Helvetica", 14)
        self.pdf.drawCentredString(self.width / 2, self.height - 280, f"{self.cenario.tipo_servico}")
        
        # Box com dados da empresa
        y_box = self.height - 400
        self.pdf.rect(self.MARGIN_X, y_box - 120, self.CONTENT_WIDTH, 120, stroke=1, fill=0)
        
        self.pdf.setFont("Helvetica-Bold", 12)
        self.pdf.drawCentredString(self.width / 2, y_box - 20, "EMPRESA PROPONENTE")
        
        self.pdf.setFont("Helvetica", 10)
        if self.empresa:
            linhas = [
                f"Razão Social: {self.empresa.razao_social}",
                f"CNPJ: {self.empresa.cnpj}",
                f"Endereço: {self.empresa.endereco}",
                f"Telefone: {self.empresa.telefone or 'Não informado'}",
                f"E-mail: {self.empresa.email or 'Não informado'}"
            ]
            
            y_texto = y_box - 40
            for linha in linhas:
                self.pdf.drawCentredString(self.width / 2, y_texto, linha)
                y_texto -= 15
        
        # Dados do processo
        y_processo = y_box - 180
        self.pdf.setFont("Helvetica-Bold", 12)
        self.pdf.drawString(self.MARGIN_X, y_processo, "PROCESSO LICITATÓRIO")
        
        self.pdf.setFont("Helvetica", 10)
        y_processo -= 20
        
        dados_processo = [
            f"Órgão: {self.cenario.razao_social or 'Não informado'}",
            f"Processo nº: {self.cenario.numero_processo or 'Não informado'}",
            f"Local de Execução: {self.cenario.local_execucao or 'Não informado'}",
            f"Prazo de Execução: {self.cenario.prazo_execucao or 0} meses",
            f"Validade da Proposta: {self.cenario.validade_proposta or 0} dias"
        ]
        
        for linha in dados_processo:
            self.pdf.drawString(self.MARGIN_X + 10, y_processo, linha)
            y_processo -= 15
        
        # Data
        self.pdf.setFont("Helvetica", 10)
        self.pdf.drawCentredString(
            self.width / 2,
            100,
            f"{datetime.now().strftime('%d de %B de %Y')}"
        )
    
    def desenha_dados_proposta(self):
        """Desenha dados da proposta"""
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.drawString(self.MARGIN_X, self.y, "1. DADOS DA PROPOSTA")
        self.y -= 25
        
        self.pdf.setFont("Helvetica", 10)
        
        dados = [
            f"Proposta ID: {self.cenario.id}",
            f"Tipo de Serviço: {self.cenario.tipo_servico}",
            f"Data de Elaboração: {datetime.now().strftime('%d/%m/%Y')}",
            f"Regime Tributário: {self.cenario.regime_tributario.upper()}",
        ]
        
        for linha in dados:
            self.pdf.drawString(self.MARGIN_X + 10, self.y, linha)
            self.y -= 15
        
        self.y -= 20
    
    def desenha_resumo_geral(self):
        """Desenha resumo geral"""
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.drawString(self.MARGIN_X, self.y, "2. RESUMO GERAL")
        self.y -= 25
        
        total = self.resultado.get('total_contrato', {})
        
        # Tabela de resumo
        data = [
            ['DESCRIÇÃO', 'VALOR (R$)'],
            ['Mão de Obra (Remuneração)', f"R$ {total.get('total_remuneracao', 0):,.2f}"],
            ['Encargos Sociais e Trabalhistas', f"R$ {total.get('total_encargos_beneficios', 0):,.2f}"],
            ['Provisões e Rescisões', f"R$ {total.get('total_provisoes', 0):,.2f}"],
            ['Reposição de Profissionais', f"R$ {total.get('total_reposicao', 0):,.2f}"],
            ['Insumos e Materiais', f"R$ {total.get('total_insumos', 0):,.2f}"],
            ['SUBTOTAL (Custo Direto)', f"R$ {total.get('subtotal_antes_citl', 0):,.2f}"],
        ]
        
        table = Table(data, colWidths=[350, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D9E1F2')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        table.wrapOn(self.pdf, self.CONTENT_WIDTH, 400)
        table.drawOn(self.pdf, self.MARGIN_X, self.y - 150)
        
        self.y -= 180
    
    def desenha_detalhamento_lotes(self):
        """Desenha detalhamento por lote"""
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.drawString(self.MARGIN_X, self.y, "3. DETALHAMENTO POR LOTE")
        self.y -= 25
        
        for lote_num, postos in sorted(self.postos_por_lote.items()):
            self.verifica_espaco(150)
            
            # Cabeçalho do lote
            lote_nome = postos[0].get('lote_nome', f'Lote {lote_num}') if postos else f'Lote {lote_num}'
            
            self.pdf.setFont("Helvetica-Bold", 12)
            self.pdf.drawString(self.MARGIN_X, self.y, f"LOTE {lote_num}: {lote_nome}")
            self.y -= 20
            
            # Tabela de postos do lote
            data = [['Cargo', 'Qtd', 'Valor Unit.', 'Total']]
            
            total_lote = 0
            for posto in postos:
                data.append([
                    posto['cargo'],
                    str(posto['quantidade_postos']),
                    f"R$ {posto['total_unitario']:,.2f}",
                    f"R$ {posto['total_posto']:,.2f}"
                ])
                total_lote += posto['total_posto']
            
            data.append(['TOTAL DO LOTE', '', '', f"R$ {total_lote:,.2f}"])
            
            table = Table(data, colWidths=[250, 50, 100, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D9E1F2')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            altura_tabela = len(data) * 20 + 20
            table.wrapOn(self.pdf, self.CONTENT_WIDTH, altura_tabela)
            table.drawOn(self.pdf, self.MARGIN_X, self.y - altura_tabela)
            
            self.y -= altura_tabela + 30
    
    def desenha_composicao_bdi(self):
        """Desenha composição detalhada do BDI"""
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.drawString(self.MARGIN_X, self.y, "4. COMPOSIÇÃO DO BDI")
        self.y -= 25
        
        self.pdf.setFont("Helvetica", 10)
        self.pdf.drawString(
            self.MARGIN_X,
            self.y,
            "Benefícios e Despesas Indiretas conforme legislação vigente:"
        )
        self.y -= 20
        
        # Tabela de BDI
        data = [
            ['ITEM', 'PERCENTUAL (%)'],
            ['Administração Central', f"{self.cenario.bdi_administracao_central:.2f}%"],
            ['Seguros', f"{self.cenario.bdi_seguros:.2f}%"],
            ['Garantias', f"{self.cenario.bdi_garantias:.2f}%"],
            ['Riscos', f"{self.cenario.bdi_riscos:.2f}%"],
            ['Despesas Financeiras', f"{self.cenario.bdi_despesas_financeiras:.2f}%"],
            ['Lucro', f"{self.cenario.bdi_lucro:.2f}%"],
        ]
        
        if self.cenario.bdi_outros > 0:
            data.append(['Outros', f"{self.cenario.bdi_outros:.2f}%"])
        
        # Total BDI
        total_bdi_perc = (
            self.cenario.bdi_administracao_central +
            self.cenario.bdi_seguros +
            self.cenario.bdi_garantias +
            self.cenario.bdi_riscos +
            self.cenario.bdi_despesas_financeiras +
            self.cenario.bdi_lucro +
            self.cenario.bdi_outros
        )
        
        data.append(['TOTAL BDI', f"{total_bdi_perc:.2f}%"])
        
        table = Table(data, colWidths=[400, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D9E1F2')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        table.wrapOn(self.pdf, self.CONTENT_WIDTH, 300)
        table.drawOn(self.pdf, self.MARGIN_X, self.y - 200)
        
        self.y -= 220
    
    def desenha_resumo_final(self):
        """Desenha resumo final com valor total"""
        self.verifica_espaco(150)
        
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.drawString(self.MARGIN_X, self.y, "5. VALOR TOTAL DA PROPOSTA")
        self.y -= 25
        
        total = self.resultado.get('total_contrato', {})
        
        # Box com valor total
        self.pdf.rect(self.MARGIN_X, self.y - 80, self.CONTENT_WIDTH, 80, stroke=2, fill=0)
        
        self.pdf.setFont("Helvetica-Bold", 16)
        self.pdf.drawCentredString(
            self.width / 2,
            self.y - 40,
            f"VALOR TOTAL: R$ {total.get('total_contrato', 0):,.2f}"
        )
        
        self.pdf.setFont("Helvetica", 10)
        self.pdf.drawCentredString(
            self.width / 2,
            self.y - 60,
            f"(Valor mensal por {self.cenario.prazo_execucao or 12} meses)"
        )
    
    def desenha_rodape_todas_paginas(self):
        """Desenha rodapé em todas as páginas"""
        for pagina in range(1, self.pagina_atual + 1):
            self.pdf.setFont("Helvetica", 8)
            self.pdf.drawCentredString(
                self.width / 2,
                30,
                f"Página {pagina} de {self.pagina_atual} - Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
            )
    
    def verifica_espaco(self, altura_necessaria):
        """Verifica espaço e cria nova página se necessário"""
        if self.y - altura_necessaria < self.MARGIN_Y + 50:
            self.pdf.showPage()
            self.pagina_atual += 1
            self.y = self.height - self.MARGIN_Y
