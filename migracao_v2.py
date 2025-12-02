"""
Script de Migração V2 - Módulo Nova Lei
Adiciona novas colunas ao banco de dados usando SQLAlchemy

Execute este script ANTES de acessar o sistema:
python3 migracao_v2.py
"""

from app import app, db
from sqlalchemy import text

def executar_migracao():
    """
    Executa a migração adicionando novas colunas
    """
    print("="*60)
    print("MIGRAÇÃO V2 - Módulo Nova Lei")
    print("="*60)
    
    with app.app_context():
        try:
            # Lista de comandos SQL para executar
            comandos = [
                # Dados da Empresa
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS cnpj VARCHAR(18) DEFAULT NULL",
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS razao_social VARCHAR(200) DEFAULT NULL",
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS endereco TEXT DEFAULT NULL",
                
                # Dados do Órgão/Processo
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS numero_processo VARCHAR(100) DEFAULT NULL",
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS validade_proposta INT DEFAULT NULL",
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS prazo_pagamento VARCHAR(100) DEFAULT NULL",
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS local_execucao VARCHAR(200) DEFAULT NULL",
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS prazo_execucao INT DEFAULT NULL",
                
                # Status
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'habilitação'",
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS valor_total FLOAT DEFAULT 0.0",
                
                # Alíquota Simples
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS aliquota_simples FLOAT DEFAULT 14.0",
                
                # Data criação (alias)
                "ALTER TABLE svc_scenarios ADD COLUMN IF NOT EXISTS data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP",
                
                # Agrupamento em svc_jobs
                "ALTER TABLE svc_jobs ADD COLUMN IF NOT EXISTS lote_numero INT DEFAULT 1",
                "ALTER TABLE svc_jobs ADD COLUMN IF NOT EXISTS lote_nome VARCHAR(200) DEFAULT 'Lote 1'",
                
                # Agrupamento em svc_insumos
                "ALTER TABLE svc_insumos ADD COLUMN IF NOT EXISTS lote_numero INT DEFAULT 1",
                "ALTER TABLE svc_insumos ADD COLUMN IF NOT EXISTS cargo VARCHAR(200) DEFAULT 'todos'"
            ]
            
            print("\nExecutando comandos SQL...")
            
            for i, comando in enumerate(comandos, 1):
                try:
                    db.session.execute(text(comando))
                    print(f"✓ Comando {i}/{len(comandos)} executado com sucesso")
                except Exception as e:
                    # Se a coluna já existe, ignora o erro
                    if "Duplicate column name" in str(e) or "already exists" in str(e):
                        print(f"⚠ Comando {i}/{len(comandos)} - Coluna já existe (ignorado)")
                    else:
                        print(f"✗ Erro no comando {i}/{len(comandos)}: {e}")
                        raise
            
            db.session.commit()
            
            print("\n" + "="*60)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*60)
            print("\nVocê pode agora acessar o sistema normalmente.")
            print("URL: http://localhost:5000/precificaja/servicos/nova-lei/simulacao")
            
        except Exception as e:
            db.session.rollback()
            print("\n" + "="*60)
            print("❌ ERRO NA MIGRAÇÃO")
            print("="*60)
            print(f"\nErro: {e}")
            print("\nTente executar o script SQL manualmente:")
            print("mysql -u seu_usuario -p seu_banco < migracao_v2.sql")
            return False
    
    return True


def verificar_colunas():
    """
    Verifica se as colunas foram adicionadas corretamente
    """
    print("\n" + "="*60)
    print("VERIFICAÇÃO DAS COLUNAS")
    print("="*60)
    
    with app.app_context():
        try:
            # Verificar svc_scenarios
            result = db.session.execute(text("DESCRIBE svc_scenarios"))
            colunas = [row[0] for row in result]
            
            colunas_necessarias = [
                'cnpj', 'razao_social', 'endereco', 'numero_processo',
                'validade_proposta', 'prazo_pagamento', 'local_execucao',
                'prazo_execucao', 'status', 'valor_total', 'aliquota_simples',
                'data_criacao'
            ]
            
            print("\nTabela svc_scenarios:")
            for coluna in colunas_necessarias:
                if coluna in colunas:
                    print(f"  ✓ {coluna}")
                else:
                    print(f"  ✗ {coluna} (FALTANDO)")
            
            # Verificar svc_jobs
            result = db.session.execute(text("DESCRIBE svc_jobs"))
            colunas = [row[0] for row in result]
            
            print("\nTabela svc_jobs:")
            for coluna in ['lote_numero', 'lote_nome']:
                if coluna in colunas:
                    print(f"  ✓ {coluna}")
                else:
                    print(f"  ✗ {coluna} (FALTANDO)")
            
            # Verificar svc_insumos
            result = db.session.execute(text("DESCRIBE svc_insumos"))
            colunas = [row[0] for row in result]
            
            print("\nTabela svc_insumos:")
            for coluna in ['lote_numero', 'cargo']:
                if coluna in colunas:
                    print(f"  ✓ {coluna}")
                else:
                    print(f"  ✗ {coluna} (FALTANDO)")
            
        except Exception as e:
            print(f"\nErro na verificação: {e}")


if __name__ == '__main__':
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  MIGRAÇÃO V2 - MÓDULO NOVA LEI".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    print("\n")
    
    resposta = input("Deseja executar a migração? (s/n): ")
    
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        sucesso = executar_migracao()
        
        if sucesso:
            verificar_colunas()
    else:
        print("\nMigração cancelada.")
        print("Execute manualmente quando estiver pronto.")
