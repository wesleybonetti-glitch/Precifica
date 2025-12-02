"""
Motor de Cálculo V3 - Universal
Suporta qualquer tipo de serviço com despesas personalizáveis
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any


class MotorCalculoUniversal:
    """
    Motor de cálculo universal para qualquer tipo de serviço
    
    Suporta:
    - Mão de obra com encargos completos
    - Despesas personalizáveis por categoria
    - BDI/CITL configurável
    - Recálculo automático quando parâmetros mudam
    """
    
    def __init__(self, parametros: Dict[str, Any]):
        self.parametros = parametros
    
    def calcular(self, postos: List[Dict] = None, insumos: List[Dict] = None, despesas: List[Dict] = None) -> Dict:
        """
        Calcula o orçamento completo
        
        Args:
            postos: Lista de postos de trabalho (mão de obra)
            insumos: Lista de insumos (uniformes, EPIs, materiais)
            despesas: Lista de despesas personalizáveis
        
        Returns:
            Dicionário com resultado completo
        """
        postos = postos or []
        insumos = insumos or []
        despesas = despesas or []
        
        # Calcular mão de obra
        resultado_mao_obra = self._calcular_mao_obra(postos, insumos)
        
        # Calcular despesas personalizáveis
        resultado_despesas = self._calcular_despesas(despesas)
        
        # Subtotal (antes de BDI/CITL)
        subtotal = resultado_mao_obra['total'] + resultado_despesas['total']
        
        # Calcular BDI/CITL
        bdi_citl = self._calcular_bdi_citl(subtotal)
        
        # Total geral
        total_geral = subtotal + bdi_citl['total']
        
        return {
            'mao_obra': resultado_mao_obra,
            'despesas_personalizadas': resultado_despesas,
            'subtotal_antes_bdi': self._arredondar(subtotal),
            'bdi_citl': bdi_citl,
            'total_geral': self._arredondar(total_geral),
            'parametros': self.parametros
        }
    
    def _calcular_mao_obra(self, postos: List[Dict], insumos: List[Dict]) -> Dict:
        """
        Calcula todos os custos de mão de obra
        """
        total_remuneracao = Decimal('0')
        total_encargos = Decimal('0')
        total_provisoes = Decimal('0')
        total_reposicao = Decimal('0')
        total_insumos = Decimal('0')
        
        detalhes_postos = []
        
        for posto in postos:
            # Remuneração
            remuneracao = self._calcular_remuneracao(posto)
            
            # Encargos
            encargos = self._calcular_encargos(remuneracao)
            
            # Provisões
            provisoes = self._calcular_provisoes(remuneracao)
            
            # Reposição
            reposicao = self._calcular_reposicao(remuneracao, encargos, provisoes)
            
            # Insumos do posto
            insumos_posto = self._calcular_insumos_posto(posto, insumos)
            
            # Total do posto
            total_posto = remuneracao + encargos + provisoes + reposicao + insumos_posto
            
            quantidade = posto.get('quantidade_postos', 1)
            
            total_remuneracao += remuneracao * quantidade
            total_encargos += encargos * quantidade
            total_provisoes += provisoes * quantidade
            total_reposicao += reposicao * quantidade
            total_insumos += insumos_posto * quantidade
            
            detalhes_postos.append({
                'cargo': posto.get('cargo', ''),
                'quantidade': quantidade,
                'remuneracao': self._arredondar(remuneracao),
                'encargos': self._arredondar(encargos),
                'provisoes': self._arredondar(provisoes),
                'reposicao': self._arredondar(reposicao),
                'insumos': self._arredondar(insumos_posto),
                'total_unitario': self._arredondar(total_posto),
                'total': self._arredondar(total_posto * quantidade)
            })
        
        total_mao_obra = total_remuneracao + total_encargos + total_provisoes + total_reposicao + total_insumos
        
        return {
            'remuneracao': self._arredondar(total_remuneracao),
            'encargos': self._arredondar(total_encargos),
            'provisoes': self._arredondar(total_provisoes),
            'reposicao': self._arredondar(total_reposicao),
            'insumos': self._arredondar(total_insumos),
            'total': self._arredondar(total_mao_obra),
            'detalhes_postos': detalhes_postos
        }
    
    def _calcular_remuneracao(self, posto: Dict) -> Decimal:
        """Calcula remuneração total do posto"""
        salario = Decimal(str(posto.get('salario_base', 0)))
        insalubridade = Decimal(str(posto.get('adicional_insalubridade', 0)))
        periculosidade = Decimal(str(posto.get('adicional_periculosidade', 0)))
        gratificacao = Decimal(str(posto.get('gratificacao', 0)))
        
        # Adicional noturno
        adicional_noturno = Decimal('0')
        if 'noturno' in posto.get('jornada_tipo', '').lower():
            perc_noturno = Decimal(str(posto.get('adicional_noturno_percentual', 20))) / Decimal('100')
            adicional_noturno = salario * perc_noturno
        
        return salario + insalubridade + periculosidade + gratificacao + adicional_noturno
    
    def _calcular_encargos(self, remuneracao: Decimal) -> Decimal:
        """Calcula encargos sociais"""
        inss = Decimal(str(self.parametros.get('inss_patronal', 20))) / Decimal('100')
        salario_educacao = Decimal(str(self.parametros.get('salario_educacao', 2.5))) / Decimal('100')
        rat_sat = Decimal(str(self.parametros.get('rat_sat', 3))) / Decimal('100')
        fap = Decimal(str(self.parametros.get('fap_multiplicador', 1)))
        sesc_senac = Decimal(str(self.parametros.get('sesc_senac', 1.5))) / Decimal('100')
        sebrae = Decimal(str(self.parametros.get('sebrae', 0.6))) / Decimal('100')
        incra = Decimal(str(self.parametros.get('incra', 0.2))) / Decimal('100')
        
        # 13º salário
        decimo_terceiro = remuneracao / Decimal('12')
        
        # Férias + 1/3
        ferias = (remuneracao / Decimal('12')) * Decimal('1.333333')
        
        # Encargos sobre remuneração + 13º + férias
        base_encargos = remuneracao + decimo_terceiro + ferias
        
        total_encargos = base_encargos * (inss + salario_educacao + (rat_sat * fap) + sesc_senac + sebrae + incra)
        
        # FGTS (8%)
        fgts = base_encargos * Decimal('0.08')
        
        return total_encargos + fgts
    
    def _calcular_provisoes(self, remuneracao: Decimal) -> Decimal:
        """Calcula provisões rescisórias e ausências"""
        # Aviso prévio + multa FGTS
        provisao = remuneracao * Decimal('0.07')  # ~7% da remuneração
        return provisao
    
    def _calcular_reposicao(self, remuneracao: Decimal, encargos: Decimal, provisoes: Decimal) -> Decimal:
        """Calcula custo de reposição de profissional ausente"""
        # Férias, licenças, afastamentos (~3%)
        base_reposicao = remuneracao + encargos + provisoes
        reposicao = base_reposicao * Decimal('0.03')
        return reposicao
    
    def _calcular_insumos_posto(self, posto: Dict, insumos: List[Dict]) -> Decimal:
        """Calcula insumos específicos do posto"""
        total = Decimal('0')
        cargo = posto.get('cargo', '')
        
        for insumo in insumos:
            # Verificar se o insumo se aplica a este cargo
            if insumo.get('cargo', 'todos') in ['todos', cargo]:
                custo = Decimal(str(insumo.get('custo_unitario', 0)))
                quantidade = Decimal(str(insumo.get('quantidade_por_posto', 1)))
                periodicidade = Decimal(str(insumo.get('periodicidade_meses', 12)))
                
                # Custo mensal do insumo
                custo_mensal = (custo * quantidade) / periodicidade
                total += custo_mensal
        
        return total
    
    def _calcular_despesas(self, despesas: List[Dict]) -> Dict:
        """
        Calcula despesas personalizáveis por categoria
        """
        categorias = {}
        total_despesas = Decimal('0')
        
        for despesa in despesas:
            categoria = despesa.get('categoria', 'outra')
            quantidade = Decimal(str(despesa.get('quantidade', 1)))
            valor_unitario = Decimal(str(despesa.get('valor_unitario', 0)))
            valor_total = quantidade * valor_unitario
            
            if categoria not in categorias:
                categorias[categoria] = {
                    'itens': [],
                    'total': Decimal('0')
                }
            
            categorias[categoria]['itens'].append({
                'descricao': despesa.get('descricao', ''),
                'unidade': despesa.get('unidade', 'un'),
                'quantidade': self._arredondar(quantidade),
                'valor_unitario': self._arredondar(valor_unitario),
                'valor_total': self._arredondar(valor_total)
            })
            
            categorias[categoria]['total'] += valor_total
            total_despesas += valor_total
        
        # Converter totais das categorias
        for cat in categorias:
            categorias[cat]['total'] = self._arredondar(categorias[cat]['total'])
        
        return {
            'categorias': categorias,
            'total': self._arredondar(total_despesas)
        }
    
    def _calcular_bdi_citl(self, subtotal: Decimal) -> Dict:
        """
        Calcula BDI/CITL (Benefícios e Despesas Indiretas / Custos Indiretos, Tributos e Lucro)
        """
        subtotal_dec = Decimal(str(subtotal))
        
        # Custos indiretos
        perc_custos_indiretos = Decimal(str(self.parametros.get('custos_indiretos_percentual', 5))) / Decimal('100')
        custos_indiretos = subtotal_dec * perc_custos_indiretos
        
        # Tributos
        regime = self.parametros.get('regime_tributario', 'simples')
        
        if regime == 'simples':
            aliq_simples = Decimal(str(self.parametros.get('aliquota_simples', 14))) / Decimal('100')
            base_tributos = subtotal_dec + custos_indiretos
            tributos_total = base_tributos * aliq_simples / (Decimal('1') - aliq_simples)
            
            tributos_detalhados = {
                'simples_nacional': self._arredondar(tributos_total)
            }
        else:
            aliq_pis = Decimal(str(self.parametros.get('aliquota_pis', 0.65))) / Decimal('100')
            aliq_cofins = Decimal(str(self.parametros.get('aliquota_cofins', 3))) / Decimal('100')
            aliq_iss = Decimal(str(self.parametros.get('aliquota_iss', 5))) / Decimal('100')
            
            base_tributos = subtotal_dec + custos_indiretos
            pis = base_tributos * aliq_pis / (Decimal('1') - aliq_pis - aliq_cofins - aliq_iss)
            cofins = base_tributos * aliq_cofins / (Decimal('1') - aliq_pis - aliq_cofins - aliq_iss)
            iss = base_tributos * aliq_iss / (Decimal('1') - aliq_pis - aliq_cofins - aliq_iss)
            
            tributos_total = pis + cofins + iss
            
            tributos_detalhados = {
                'pis': self._arredondar(pis),
                'cofins': self._arredondar(cofins),
                'iss': self._arredondar(iss)
            }
        
        # Lucro
        perc_lucro = Decimal(str(self.parametros.get('lucro_percentual', 8))) / Decimal('100')
        base_lucro = subtotal_dec + custos_indiretos + tributos_total
        lucro = base_lucro * perc_lucro
        
        total_bdi = custos_indiretos + tributos_total + lucro
        
        return {
            'custos_indiretos': self._arredondar(custos_indiretos),
            'tributos': tributos_detalhados,
            'tributos_total': self._arredondar(tributos_total),
            'lucro': self._arredondar(lucro),
            'total': self._arredondar(total_bdi)
        }
    
    @staticmethod
    def _arredondar(valor) -> float:
        """Arredonda para 2 casas decimais"""
        if isinstance(valor, Decimal):
            return float(valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        return round(float(valor), 2)
