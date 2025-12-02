"""
Gerenciador de Chaves de API do Gemini
Sistema de rotação automática que detecta qual chave tem quota disponível
"""

import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions


class GerenciadorChavesAPI:
    """
    Gerencia múltiplas chaves de API do Gemini com rotação automática.
    
    Recursos:
    - Suporta número ilimitado de chaves
    - Detecta automaticamente chaves com quota disponível
    - Marca chaves que atingiram o limite
    - Reseta status após período de cooldown
    - Salva estado em arquivo JSON
    """
    
    def __init__(self, arquivo_estado='chaves_api_estado.old.json'):
        """
        Inicializa o gerenciador de chaves.
        
        Args:
            arquivo_estado: Caminho do arquivo para salvar estado das chaves
        """
        self.chaves = []
        self.chave_atual_index = 0
        self.arquivo_estado = arquivo_estado
        self.estado_chaves = {}
        
        # Carrega chaves do .env
        self._carregar_chaves_do_env()
        
        # Carrega estado salvo
        self._carregar_estado()
        
        print(f"📋 Gerenciador inicializado com {len(self.chaves)} chaves de API")
    
    def _carregar_chaves_do_env(self):
        """
        Carrega todas as chaves de API do arquivo .env.
        
        Formatos suportados:
        - GEMINI_API_KEY=chave1
        - GEMINI_API_KEY_1=chave1
        - GEMINI_API_KEY_2=chave2
        - GEMINI_API_KEY_3=chave3
        - ... (sem limite)
        """
        # Tenta carregar chave única
        chave_unica = os.environ.get('GEMINI_API_KEY')
        if chave_unica:
            self.chaves.append(chave_unica)
            print(f"✅ Chave única carregada: {chave_unica[:10]}...")
        
        # Tenta carregar chaves numeradas (1 a 100, mas pode ser mais)
        contador = 1
        while True:
            chave = os.environ.get(f'GEMINI_API_KEY_{contador}')
            if chave:
                self.chaves.append(chave)
                print(f"✅ Chave {contador} carregada: {chave[:10]}...")
                contador += 1
            else:
                # Para quando não encontrar mais chaves
                break
        
        if not self.chaves:
            raise ValueError(
                "❌ Nenhuma chave de API encontrada no .env!\n"
                "Configure pelo menos uma chave:\n"
                "  GEMINI_API_KEY=sua_chave\n"
                "Ou múltiplas chaves:\n"
                "  GEMINI_API_KEY_1=chave1\n"
                "  GEMINI_API_KEY_2=chave2\n"
                "  GEMINI_API_KEY_3=chave3\n"
            )
        
        print(f"📊 Total de {len(self.chaves)} chave(s) carregada(s)")
    
    def _carregar_estado(self):
        """Carrega o estado salvo das chaves (quais atingiram limite, quando, etc)."""
        try:
            if os.path.exists(self.arquivo_estado):
                with open(self.arquivo_estado, 'r') as f:
                    self.estado_chaves = json.load(f)
                print(f"📂 Estado das chaves carregado de {self.arquivo_estado}")
            else:
                # Inicializa estado vazio para todas as chaves
                self.estado_chaves = {
                    chave[:10]: {
                        'bloqueada': False,
                        'bloqueada_em': None,
                        'tentativas': 0,
                        'ultimo_uso': None,
                        'total_requisicoes': 0
                    }
                    for chave in self.chaves
                }
                self._salvar_estado()
        except Exception as e:
            print(f"⚠️ Erro ao carregar estado: {e}")
            self.estado_chaves = {}
    
    def _salvar_estado(self):
        """Salva o estado atual das chaves em arquivo."""
        try:
            with open(self.arquivo_estado, 'w') as f:
                json.dump(self.estado_chaves, f, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar estado: {e}")
    
    def _resetar_chaves_expiradas(self):
        """
        Reseta o status de chaves que já passaram do período de cooldown.
        
        Plano gratuito do Gemini:
        - Limite por minuto: reseta após 1 minuto
        - Limite por dia: reseta após 24 horas
        """
        agora = datetime.now()
        
        for chave_id, estado in self.estado_chaves.items():
            if estado.get('bloqueada') and estado.get('bloqueada_em'):
                bloqueada_em = datetime.fromisoformat(estado['bloqueada_em'])
                
                # Reseta após 2 minutos (margem de segurança para limite por minuto)
                if agora - bloqueada_em > timedelta(minutes=2):
                    print(f"🔓 Chave {chave_id}... desbloqueada (cooldown expirado)")
                    estado['bloqueada'] = False
                    estado['bloqueada_em'] = None
                    self._salvar_estado()
    
    def _marcar_chave_bloqueada(self, chave):
        """Marca uma chave como bloqueada (atingiu limite de quota)."""
        chave_id = chave[:10]
        
        if chave_id not in self.estado_chaves:
            self.estado_chaves[chave_id] = {
                'bloqueada': False,
                'bloqueada_em': None,
                'tentativas': 0,
                'ultimo_uso': None,
                'total_requisicoes': 0
            }
        
        self.estado_chaves[chave_id]['bloqueada'] = True
        self.estado_chaves[chave_id]['bloqueada_em'] = datetime.now().isoformat()
        self.estado_chaves[chave_id]['tentativas'] += 1
        
        self._salvar_estado()
        
        print(f"🚫 Chave {chave_id}... marcada como bloqueada")
    
    def _registrar_uso_chave(self, chave):
        """Registra o uso bem-sucedido de uma chave."""
        chave_id = chave[:10]
        
        if chave_id not in self.estado_chaves:
            self.estado_chaves[chave_id] = {
                'bloqueada': False,
                'bloqueada_em': None,
                'tentativas': 0,
                'ultimo_uso': None,
                'total_requisicoes': 0
            }
        
        self.estado_chaves[chave_id]['ultimo_uso'] = datetime.now().isoformat()
        self.estado_chaves[chave_id]['total_requisicoes'] += 1
        
        self._salvar_estado()
    
    def obter_chave_disponivel(self):
        """
        Obtém a próxima chave disponível (que não atingiu o limite).
        
        Returns:
            str: Chave de API disponível
            
        Raises:
            Exception: Se todas as chaves atingiram o limite
        """
        # Reseta chaves que já passaram do cooldown
        self._resetar_chaves_expiradas()
        
        # Tenta encontrar uma chave disponível
        tentativas = 0
        max_tentativas = len(self.chaves)
        
        while tentativas < max_tentativas:
            chave = self.chaves[self.chave_atual_index]
            chave_id = chave[:10]
            
            # Verifica se a chave está bloqueada
            estado = self.estado_chaves.get(chave_id, {})
            
            if not estado.get('bloqueada', False):
                print(f"✅ Usando chave {self.chave_atual_index + 1}/{len(self.chaves)}: {chave_id}...")
                return chave
            else:
                print(f"⏭️ Chave {self.chave_atual_index + 1} bloqueada, tentando próxima...")
                self.chave_atual_index = (self.chave_atual_index + 1) % len(self.chaves)
                tentativas += 1
        
        # Se chegou aqui, todas as chaves estão bloqueadas
        raise Exception(
            "❌ Todas as chaves de API atingiram o limite de quota!\n"
            f"Total de chaves: {len(self.chaves)}\n"
            "Aguarde alguns minutos ou adicione mais chaves no .env"
        )
    
    def executar_com_rotacao(self, funcao_api, *args, **kwargs):
        """
        Executa uma função que usa a API do Gemini com rotação automática de chaves.
        
        Args:
            funcao_api: Função que recebe a chave de API como primeiro argumento
            *args, **kwargs: Argumentos para passar para a função
            
        Returns:
            Resultado da função
            
        Raises:
            Exception: Se todas as chaves falharem
        """
        tentativas = 0
        max_tentativas = len(self.chaves) * 2  # Tenta cada chave até 2 vezes
        
        while tentativas < max_tentativas:
            try:
                # Obtém chave disponível
                chave = self.obter_chave_disponivel()
                
                # Executa a função com a chave
                resultado = funcao_api(chave, *args, **kwargs)
                
                # Registra uso bem-sucedido
                self._registrar_uso_chave(chave)
                
                # Move para próxima chave (round-robin)
                self.chave_atual_index = (self.chave_atual_index + 1) % len(self.chaves)
                
                return resultado
                
            except google_exceptions.ResourceExhausted as e:
                # Erro 429 - Quota excedida
                print(f"⚠️ Quota excedida na chave atual")
                self._marcar_chave_bloqueada(chave)
                
                # Move para próxima chave
                self.chave_atual_index = (self.chave_atual_index + 1) % len(self.chaves)
                tentativas += 1
                
                # Aguarda um pouco antes de tentar próxima chave
                time.sleep(2)
                
            except Exception as e:
                # Outros erros
                print(f"❌ Erro ao executar função: {e}")
                raise
        
        # Se chegou aqui, todas as tentativas falharam
        raise Exception(
            f"❌ Falha após {max_tentativas} tentativas com todas as chaves!\n"
            "Todas as chaves atingiram o limite ou há outro problema."
        )
    
    def obter_estatisticas(self):
        """
        Retorna estatísticas sobre o uso das chaves.
        
        Returns:
            dict: Estatísticas de uso
        """
        total_chaves = len(self.chaves)
        chaves_bloqueadas = sum(
            1 for estado in self.estado_chaves.values() 
            if estado.get('bloqueada', False)
        )
        chaves_disponiveis = total_chaves - chaves_bloqueadas
        
        total_requisicoes = sum(
            estado.get('total_requisicoes', 0) 
            for estado in self.estado_chaves.values()
        )
        
        return {
            'total_chaves': total_chaves,
            'chaves_disponiveis': chaves_disponiveis,
            'chaves_bloqueadas': chaves_bloqueadas,
            'total_requisicoes': total_requisicoes,
            'detalhes': self.estado_chaves
        }
    
    def imprimir_estatisticas(self):
        """Imprime estatísticas de uso das chaves de forma formatada."""
        stats = self.obter_estatisticas()
        
        print("\n" + "="*60)
        print("📊 ESTATÍSTICAS DE USO DAS CHAVES DE API")
        print("="*60)
        print(f"Total de chaves:       {stats['total_chaves']}")
        print(f"Chaves disponíveis:    {stats['chaves_disponiveis']} ✅")
        print(f"Chaves bloqueadas:     {stats['chaves_bloqueadas']} 🚫")
        print(f"Total de requisições:  {stats['total_requisicoes']}")
        print("-"*60)
        
        for i, chave in enumerate(self.chaves, 1):
            chave_id = chave[:10]
            estado = self.estado_chaves.get(chave_id, {})
            
            status = "🚫 BLOQUEADA" if estado.get('bloqueada') else "✅ DISPONÍVEL"
            requisicoes = estado.get('total_requisicoes', 0)
            
            print(f"Chave {i}: {chave_id}... - {status} - {requisicoes} req")
        
        print("="*60 + "\n")


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA PARA USO NO CÓDIGO EXISTENTE
# ============================================================================

# Instância global do gerenciador
_gerenciador = None


def inicializar_gerenciador():
    """Inicializa o gerenciador de chaves (chamar no início da aplicação)."""
    global _gerenciador
    if _gerenciador is None:
        _gerenciador = GerenciadorChavesAPI()
    return _gerenciador


def obter_gerenciador():
    """Obtém a instância do gerenciador (cria se não existir)."""
    global _gerenciador
    if _gerenciador is None:
        _gerenciador = inicializar_gerenciador()
    return _gerenciador


def configurar_ia_com_rotacao():
    """
    Configura a API do Gemini com rotação automática de chaves.
    Substitui a função configurar_ia() original.
    
    Returns:
        str: Chave de API configurada
    """
    gerenciador = obter_gerenciador()
    chave = gerenciador.obter_chave_disponivel()
    genai.configure(api_key=chave)
    return chave


def executar_com_rotacao(funcao_api, *args, **kwargs):
    """
    Executa uma função que usa a API com rotação automática de chaves.
    
    Exemplo de uso:
        resultado = executar_com_rotacao(analisar_edital_interno, texto_edital)
    """
    gerenciador = obter_gerenciador()
    return gerenciador.executar_com_rotacao(funcao_api, *args, **kwargs)

