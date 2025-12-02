-- ============================================================
-- Migração V3 - Tabela de Despesas Personalizáveis
-- ============================================================

USE precificaja;  -- Substitua pelo nome do seu banco

-- Criar tabela de despesas personalizáveis
CREATE TABLE IF NOT EXISTS svc_despesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scenario_id INT NOT NULL,
    lote_numero INT DEFAULT 1,
    
    -- Categoria
    categoria VARCHAR(100) NOT NULL,
    subcategoria VARCHAR(100),
    
    -- Descrição
    descricao VARCHAR(300) NOT NULL,
    unidade VARCHAR(50) DEFAULT 'un',
    
    -- Valores
    quantidade FLOAT DEFAULT 1.0,
    valor_unitario FLOAT NOT NULL,
    valor_total FLOAT NOT NULL,
    
    -- Periodicidade
    periodicidade VARCHAR(50) DEFAULT 'unica',
    
    -- Incidências
    incide_encargos BOOLEAN DEFAULT FALSE,
    incide_tributos BOOLEAN DEFAULT TRUE,
    
    -- Observações
    observacoes TEXT,
    
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (scenario_id) REFERENCES svc_scenarios(id) ON DELETE CASCADE,
    INDEX idx_scenario (scenario_id),
    INDEX idx_categoria (categoria),
    INDEX idx_lote (lote_numero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT 'Tabela svc_despesas criada com sucesso!' AS status;
