-- ============================================================
-- Script de Migração V2 - Módulo Nova Lei
-- Adiciona novas colunas à tabela svc_scenarios
-- ============================================================

-- IMPORTANTE: Execute este script no seu banco de dados MySQL
-- antes de acessar o sistema

USE precificaja;  -- Substitua pelo nome do seu banco de dados

-- Adicionar colunas de Dados da Empresa
ALTER TABLE svc_scenarios 
ADD COLUMN cnpj VARCHAR(18) DEFAULT NULL AFTER tipo_servico,
ADD COLUMN razao_social VARCHAR(200) DEFAULT NULL AFTER cnpj,
ADD COLUMN endereco TEXT DEFAULT NULL AFTER razao_social;

-- Adicionar colunas de Dados do Órgão/Processo
ALTER TABLE svc_scenarios 
ADD COLUMN numero_processo VARCHAR(100) DEFAULT NULL AFTER endereco,
ADD COLUMN validade_proposta INT DEFAULT NULL AFTER numero_processo,
ADD COLUMN prazo_pagamento VARCHAR(100) DEFAULT NULL AFTER validade_proposta,
ADD COLUMN local_execucao VARCHAR(200) DEFAULT NULL AFTER prazo_pagamento,
ADD COLUMN prazo_execucao INT DEFAULT NULL AFTER local_execucao;

-- Adicionar colunas de Status
ALTER TABLE svc_scenarios 
ADD COLUMN status VARCHAR(50) DEFAULT 'habilitação' AFTER prazo_execucao,
ADD COLUMN valor_total FLOAT DEFAULT 0.0 AFTER status;

-- Adicionar coluna aliquota_simples (se não existir)
ALTER TABLE svc_scenarios 
ADD COLUMN aliquota_simples FLOAT DEFAULT 14.0 AFTER aliquota_iss;

-- Adicionar coluna data_criacao (alias para criado_em)
ALTER TABLE svc_scenarios 
ADD COLUMN data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP AFTER atualizado_em;

-- Adicionar colunas de agrupamento em svc_jobs
ALTER TABLE svc_jobs 
ADD COLUMN lote_numero INT DEFAULT 1 AFTER scenario_id,
ADD COLUMN lote_nome VARCHAR(200) DEFAULT 'Lote 1' AFTER lote_numero;

-- Adicionar coluna de agrupamento em svc_insumos
ALTER TABLE svc_insumos 
ADD COLUMN lote_numero INT DEFAULT 1 AFTER scenario_id;

-- Adicionar coluna cargo em svc_insumos
ALTER TABLE svc_insumos 
ADD COLUMN cargo VARCHAR(200) DEFAULT 'todos' AFTER periodicidade_meses;

-- ============================================================
-- Verificação (opcional)
-- ============================================================

-- Verificar se as colunas foram adicionadas
DESCRIBE svc_scenarios;
DESCRIBE svc_jobs;
DESCRIBE svc_insumos;

-- ============================================================
-- Concluído!
-- ============================================================

SELECT 'Migração V2 concluída com sucesso!' AS status;
