"""
Motor de Cálculo - Calculadora de Serviços Nova Lei
Implementa os 6 módulos obrigatórios do modelo SEGES
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any


class MotorCalculoNovaLei:
    """
    Motor de cálculo baseado no modelo SEGES para composição de custos
    e formação de preços em serviços com dedicação exclusiva de mão de obra.
    
    Módulos obrigatórios:
    1. Remuneração
    2. Encargos e Benefícios
    3. Provisões rescisórias/ausências
    4. Reposição de profissional ausente
    5. Insumos (uniformes, EPIs, materiais)
    6. CITL (Custos Indiretos, Tributos e Lucro)
    """
    
    def __init__(self, parametros: Dict[str, Any]):
        """
        Inicializa o motor com os parâmetros do cenário
        
        Args:
            parametros: Dicionário com todos os parâmetros necessários
        """
        self.parametros = parametros
        self.resultado = {}
    
    def calcular(self, postos: List[Dict], insumos: List[Dict] = None) -> Dict:
        """
        Executa o cálculo completo para todos os postos
        
        Args:
            postos: Lista de dicionários com dados dos postos
            insumos: Lista de dicionários com dados dos insumos
            
        Returns:
            Dicionário com resultado completo do cálculo
        """
        resultado_postos = []
        
        for posto in postos:
            resultado_posto = self._calcular_posto(posto, insumos or [])
            resultado_postos.append(resultado_posto)
        
        # Consolidar totais
        total_contrato = self._consolidar_totais(resultado_postos)
        
        return {
            'postos': resultado_postos,
            'total_contrato': total_contrato,
            'parametros_utilizados': self.parametros
        }
    
    def _calcular_posto(self, posto: Dict, insumos: List[Dict]) -> Dict:
        """
        Calcula todos os módulos para um posto específico
        """
        quantidade = posto.get('quantidade_postos', 1)
        
        # Módulo 1: Remuneração
        remuneracao = self._modulo_1_remuneracao(posto)
        
        # Módulo 2: Encargos e Benefícios
        encargos_beneficios = self._modulo_2_encargos_beneficios(remuneracao, posto)
        
        # Módulo 3: Provisões rescisórias/ausências
        provisoes = self._modulo_3_provisoes(remuneracao)
        
        # Módulo 4: Reposição
        reposicao = self._modulo_4_reposicao(remuneracao, encargos_beneficios, provisoes)
        
        # Módulo 5: Insumos
        insumos_posto = self._modulo_5_insumos(posto, insumos)
        
        # Subtotal (antes de CITL)
        subtotal_posto = (
            remuneracao['total'] +
            encargos_beneficios['total'] +
            provisoes['total'] +
            reposicao['total'] +
            insumos_posto['total']
        )
        
        # Módulo 6: CITL
        citl = self._modulo_6_citl(subtotal_posto)
        
        # Total por posto (unitário)
        total_unitario = subtotal_posto + citl['total']
        
        # Total considerando quantidade de postos
        total_posto = total_unitario * quantidade
        
        return {
            'cargo': posto.get('cargo', ''),
            'quantidade_postos': quantidade,
            'jornada_tipo': posto.get('jornada_tipo', ''),
            'modulo_1_remuneracao': remuneracao,
            'modulo_2_encargos_beneficios': encargos_beneficios,
            'modulo_3_provisoes': provisoes,
            'modulo_4_reposicao': reposicao,
            'modulo_5_insumos': insumos_posto,
            'subtotal_antes_citl': self._arredondar(subtotal_posto),
            'modulo_6_citl': citl,
            'total_unitario': self._arredondar(total_unitario),
            'total_posto': self._arredondar(total_posto)
        }
    
    def _modulo_1_remuneracao(self, posto: Dict) -> Dict:
        """
        Módulo 1: Remuneração
        Calcula salário base + adicionais (insalubridade, periculosidade, 
        gratificação, adicional noturno)
        """
        salario_base = Decimal(str(posto.get('salario_base', 0)))
        
        # Adicionais
        insalubridade = Decimal(str(posto.get('adicional_insalubridade', 0)))
        periculosidade = Decimal(str(posto.get('adicional_periculosidade', 0)))
        gratificacao = Decimal(str(posto.get('gratificacao', 0)))
        
        # Adicional noturno (aplicado se jornada for noturna)
        adicional_noturno = Decimal('0')
        if '12x36_noturno' in posto.get('jornada_tipo', '').lower() or 'noturno' in posto.get('jornada_tipo', '').lower():
            percentual_noturno = Decimal(str(posto.get('adicional_noturno_percentual', 20))) / Decimal('100')
            adicional_noturno = salario_base * percentual_noturno
        
        total_remuneracao = salario_base + insalubridade + periculosidade + gratificacao + adicional_noturno
        
        return {
            'salario_base': self._arredondar(salario_base),
            'adicional_insalubridade': self._arredondar(insalubridade),
            'adicional_periculosidade': self._arredondar(periculosidade),
            'adicional_noturno': self._arredondar(adicional_noturno),
            'gratificacao': self._arredondar(gratificacao),
            'total': self._arredondar(total_remuneracao)
        }
    
    def _modulo_2_encargos_beneficios(self, remuneracao: Dict, posto: Dict) -> Dict:
        """
        Módulo 2: Encargos e Benefícios
        Calcula 13º salário, férias + 1/3, GPS/FGTS, e benefícios diários/mensais
        """
        base_calculo = Decimal(str(remuneracao['total']))
        
        # 13º salário (1/12 da remuneração)
        decimo_terceiro = base_calculo / Decimal('12')
        
        # Férias + 1/3 (1/12 da remuneração + 1/3)
        ferias = base_calculo / Decimal('12')
        terco_ferias = ferias / Decimal('3')
        ferias_total = ferias + terco_ferias
        
        # Encargos previdenciários/terceiros (GPS/FGTS)
        inss_patronal = base_calculo * (Decimal(str(self.parametros.get('inss_patronal', 20))) / Decimal('100'))
        salario_educacao = base_calculo * (Decimal(str(self.parametros.get('salario_educacao', 2.5))) / Decimal('100'))
        
        # RAT/SAT com FAP
        rat_sat_base = Decimal(str(self.parametros.get('rat_sat', 3))) / Decimal('100')
        fap = Decimal(str(self.parametros.get('fap_multiplicador', 1.0)))
        rat_sat = base_calculo * rat_sat_base * fap
        
        # Terceiros (SESC/SENAC, SEBRAE, INCRA)
        sesc_senac = base_calculo * (Decimal(str(self.parametros.get('sesc_senac', 1.5))) / Decimal('100'))
        sebrae = base_calculo * (Decimal(str(self.parametros.get('sebrae', 0.6))) / Decimal('100'))
        incra = base_calculo * (Decimal(str(self.parametros.get('incra', 0.2))) / Decimal('100'))
        
        # FGTS (8%)
        fgts = base_calculo * Decimal('0.08')
        
        # Benefícios (VT, VR/VA, saúde, cesta, etc.) - valores do posto
        beneficios_total = Decimal('0')
        beneficios_detalhados = {}
        
        # VT
        vt_valor_unitario = Decimal(str(posto.get('vt_valor_unitario', 0)))
        vt_dias = Decimal(str(posto.get('vt_dias', 0)))
        vt_total = vt_valor_unitario * vt_dias
        beneficios_detalhados['vale_transporte'] = self._arredondar(vt_total)
        beneficios_total += vt_total
        
        # VR/VA
        vr_valor_dia = Decimal(str(posto.get('vr_valor_dia', 0)))
        vr_dias = Decimal(str(posto.get('vr_dias', 0)))
        vr_total = vr_valor_dia * vr_dias
        beneficios_detalhados['vale_refeicao'] = self._arredondar(vr_total)
        beneficios_total += vr_total
        
        # Saúde
        saude = Decimal(str(posto.get('saude_mensal', 0)))
        beneficios_detalhados['plano_saude'] = self._arredondar(saude)
        beneficios_total += saude
        
        # Cesta básica
        cesta = Decimal(str(posto.get('cesta_mensal', 0)))
        beneficios_detalhados['cesta_basica'] = self._arredondar(cesta)
        beneficios_total += cesta
        
        total_encargos_beneficios = (
            decimo_terceiro + ferias_total + inss_patronal + salario_educacao +
            rat_sat + sesc_senac + sebrae + incra + fgts + beneficios_total
        )
        
        return {
            'decimo_terceiro': self._arredondar(decimo_terceiro),
            'ferias': self._arredondar(ferias),
            'terco_ferias': self._arredondar(terco_ferias),
            'ferias_total': self._arredondar(ferias_total),
            'inss_patronal': self._arredondar(inss_patronal),
            'salario_educacao': self._arredondar(salario_educacao),
            'rat_sat': self._arredondar(rat_sat),
            'sesc_senac': self._arredondar(sesc_senac),
            'sebrae': self._arredondar(sebrae),
            'incra': self._arredondar(incra),
            'fgts': self._arredondar(fgts),
            'beneficios': beneficios_detalhados,
            'beneficios_total': self._arredondar(beneficios_total),
            'total': self._arredondar(total_encargos_beneficios)
        }
    
    def _modulo_3_provisoes(self, remuneracao: Dict) -> Dict:
        """
        Módulo 3: Provisões rescisórias/ausências
        Considera férias, afastamentos, etc.
        Base legal: IN 05/2017 e anexos
        """
        base_calculo = Decimal(str(remuneracao['total']))
        
        # Provisão para rescisão (estimativa baseada em hipóteses legais)
        # Aviso prévio indenizado, multa FGTS, etc.
        # Simplificado: ~5% da remuneração mensal
        provisao_rescisao = base_calculo * Decimal('0.05')
        
        # Provisão para ausências (afastamentos legais)
        # Simplificado: ~2% da remuneração mensal
        provisao_ausencias = base_calculo * Decimal('0.02')
        
        total_provisoes = provisao_rescisao + provisao_ausencias
        
        return {
            'provisao_rescisao': self._arredondar(provisao_rescisao),
            'provisao_ausencias': self._arredondar(provisao_ausencias),
            'total': self._arredondar(total_provisoes)
        }
    
    def _modulo_4_reposicao(self, remuneracao: Dict, encargos: Dict, provisoes: Dict) -> Dict:
        """
        Módulo 4: Reposição de profissional ausente
        Fundamentado em hipóteses legais de ausências
        """
        base_calculo = Decimal(str(remuneracao['total']))
        
        # Custo de reposição (estimativa baseada em ausências previstas)
        # Simplificado: ~3% do custo total de mão de obra
        custo_reposicao = base_calculo * Decimal('0.03')
        
        return {
            'custo_reposicao': self._arredondar(custo_reposicao),
            'total': self._arredondar(custo_reposicao)
        }
    
    def _modulo_5_insumos(self, posto: Dict, insumos_lista: List[Dict]) -> Dict:
        """
        Módulo 5: Insumos (uniformes, EPIs, materiais)
        SEM natureza salarial - amortizado por período de reposição
        """
        total_insumos = Decimal('0')
        insumos_detalhados = []
        
        # Filtrar insumos deste posto
        cargo = posto.get('cargo', '')
        
        for insumo in insumos_lista:
            if insumo.get('cargo') == cargo or insumo.get('cargo') == 'todos':
                custo_unitario = Decimal(str(insumo.get('custo_unitario', 0)))
                quantidade = Decimal(str(insumo.get('quantidade_por_posto', 1)))
                periodicidade_meses = Decimal(str(insumo.get('periodicidade_meses', 12)))
                
                # Custo mensal amortizado
                custo_total = custo_unitario * quantidade
                custo_mensal = custo_total / periodicidade_meses
                
                insumos_detalhados.append({
                    'descricao': insumo.get('descricao', ''),
                    'tipo': insumo.get('tipo', ''),
                    'custo_unitario': self._arredondar(custo_unitario),
                    'quantidade': float(quantidade),
                    'periodicidade_meses': float(periodicidade_meses),
                    'custo_mensal': self._arredondar(custo_mensal)
                })
                
                total_insumos += custo_mensal
        
        return {
            'insumos_detalhados': insumos_detalhados,
            'total': self._arredondar(total_insumos)
        }
    
    def _modulo_6_citl(self, subtotal: Decimal) -> Dict:
        """
        Módulo 6: CITL (Custos Indiretos, Tributos e Lucro)
        Parametrizado por regime tributário
        """
        subtotal_decimal = Decimal(str(subtotal))
        
        # Custos Indiretos
        custos_indiretos_perc = Decimal(str(self.parametros.get('custos_indiretos_percentual', 5))) / Decimal('100')
        custos_indiretos = subtotal_decimal * custos_indiretos_perc
        
        # Base para tributos
        base_tributos = subtotal_decimal + custos_indiretos
        
        # Tributos (PIS/COFINS + ISS)
        regime = self.parametros.get('regime_tributario', 'simples')
        
        if regime == 'simples':
            # Simples Nacional - Anexo IV
            # Alíquota efetiva varia conforme faturamento
            # Simplificado: usar alíquota média
            aliquota_simples = Decimal(str(self.parametros.get('aliquota_simples', 14.0))) / Decimal('100')
            tributos_total = base_tributos * aliquota_simples
            
            tributos_detalhados = {
                'regime': 'Simples Nacional - Anexo IV',
                'aliquota_efetiva': float(aliquota_simples * 100),
                'valor': self._arredondar(tributos_total)
            }
        else:
            # Presumido ou Real
            pis_perc = Decimal(str(self.parametros.get('aliquota_pis', 0.65))) / Decimal('100')
            cofins_perc = Decimal(str(self.parametros.get('aliquota_cofins', 3.0))) / Decimal('100')
            iss_perc = Decimal(str(self.parametros.get('aliquota_iss', 5.0))) / Decimal('100')
            
            pis = base_tributos * pis_perc
            cofins = base_tributos * cofins_perc
            iss = base_tributos * iss_perc
            
            tributos_total = pis + cofins + iss
            
            tributos_detalhados = {
                'regime': 'Lucro Presumido/Real',
                'pis': self._arredondar(pis),
                'cofins': self._arredondar(cofins),
                'iss': self._arredondar(iss),
                'valor': self._arredondar(tributos_total)
            }
        
        # Lucro
        lucro_perc = Decimal(str(self.parametros.get('lucro_percentual', 8))) / Decimal('100')
        base_lucro = subtotal_decimal + custos_indiretos + tributos_total
        lucro = base_lucro * lucro_perc
        
        total_citl = custos_indiretos + tributos_total + lucro
        
        return {
            'custos_indiretos': self._arredondar(custos_indiretos),
            'tributos': tributos_detalhados,
            'tributos_total': self._arredondar(tributos_total),
            'lucro': self._arredondar(lucro),
            'total': self._arredondar(total_citl)
        }
    
    def _consolidar_totais(self, resultado_postos: List[Dict]) -> Dict:
        """
        Consolida os totais de todos os postos
        """
        total_remuneracao = Decimal('0')
        total_encargos = Decimal('0')
        total_provisoes = Decimal('0')
        total_reposicao = Decimal('0')
        total_insumos = Decimal('0')
        subtotal_antes_citl = Decimal('0')
        
        total_custos_indiretos = Decimal('0')
        total_tributos = Decimal('0')
        total_lucro = Decimal('0')
        total_citl = Decimal('0')
        total_geral = Decimal('0')
        
        for posto in resultado_postos:
            quantidade = posto['quantidade_postos']
            
            total_remuneracao += Decimal(str(posto['modulo_1_remuneracao']['total'])) * quantidade
            total_encargos += Decimal(str(posto['modulo_2_encargos_beneficios']['total'])) * quantidade
            total_provisoes += Decimal(str(posto['modulo_3_provisoes']['total'])) * quantidade
            total_reposicao += Decimal(str(posto['modulo_4_reposicao']['total'])) * quantidade
            total_insumos += Decimal(str(posto['modulo_5_insumos']['total'])) * quantidade
            
            # Subtotal antes do CITL
            subtotal_antes_citl += Decimal(str(posto['subtotal_antes_citl'])) * quantidade
            
            # CITL detalhado
            citl = posto['modulo_6_citl']
            total_custos_indiretos += Decimal(str(citl['custos_indiretos'])) * quantidade
            total_tributos += Decimal(str(citl['tributos_total'])) * quantidade
            total_lucro += Decimal(str(citl['lucro'])) * quantidade
            total_citl += Decimal(str(citl['total'])) * quantidade
            
            total_geral += Decimal(str(posto['total_posto']))
        
        return {
            'total_remuneracao': self._arredondar(total_remuneracao),
            'total_encargos_beneficios': self._arredondar(total_encargos),
            'total_provisoes': self._arredondar(total_provisoes),
            'total_reposicao': self._arredondar(total_reposicao),
            'total_insumos': self._arredondar(total_insumos),
            'subtotal_antes_citl': self._arredondar(subtotal_antes_citl),
            'custos_indiretos': self._arredondar(total_custos_indiretos),
            'tributos': self._arredondar(total_tributos),
            'lucro': self._arredondar(total_lucro),
            'total_citl': self._arredondar(total_citl),
            'total_contrato': self._arredondar(total_geral)
        }
    
    def calcular_desconto_maximo(self, preco_referencia: float, lucro_minimo_percentual: float = 0) -> Dict:
        """
        Calcula o desconto máximo possível mantendo o lucro mínimo
        
        Args:
            preco_referencia: Preço de referência do lance
            lucro_minimo_percentual: Lucro mínimo desejado (%)
            
        Returns:
            Dicionário com desconto máximo, preço final e margem
        """
        preco_ref = Decimal(str(preco_referencia))
        lucro_min = Decimal(str(lucro_minimo_percentual)) / Decimal('100')
        
        # Recalcular com lucro mínimo
        parametros_temp = self.parametros.copy()
        parametros_temp['lucro_percentual'] = float(lucro_minimo_percentual)
        
        # Aqui seria necessário recalcular todo o cenário
        # Por simplicidade, vamos calcular baseado no resultado atual
        
        # Preço mínimo = custo total + lucro mínimo
        # Desconto máximo = (preco_referencia - preco_minimo) / preco_referencia
        
        return {
            'preco_referencia': self._arredondar(preco_ref),
            'desconto_maximo_percentual': 0.0,  # Placeholder
            'desconto_maximo_valor': 0.0,  # Placeholder
            'preco_minimo': 0.0,  # Placeholder
            'margem_liquida': 0.0  # Placeholder
        }
    
    @staticmethod
    def _arredondar(valor) -> float:
        """
        Arredonda valor para 2 casas decimais
        """
        if isinstance(valor, Decimal):
            return float(valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        else:
            return round(float(valor), 2)
