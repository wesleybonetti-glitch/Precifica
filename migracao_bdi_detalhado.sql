-- ============================================================
-- Migração: BDI Detalhado para Licitações
-- Adiciona campos configuráveis para cada componente do BDI
-- ============================================================

USE precificaja;  -- Substitua pelo nome do seu banco

-- Adicionar campos de BDI detalhado na tabela svc_scenarios
ALTER TABLE svc_scenarios
ADD COLUMN IF NOT EXISTS bdi_administracao_central FLOAT DEFAULT 5.0 COMMENT 'Administração Central (%)',
ADD COLUMN IF NOT EXISTS bdi_seguros FLOAT DEFAULT 0.5 COMMENT 'Seguros (%)',
ADD COLUMN IF NOT EXISTS bdi_garantias FLOAT DEFAULT 0.5 COMMENT 'Garantias (%)',
ADD COLUMN IF NOT EXISTS bdi_riscos FLOAT DEFAULT 1.0 COMMENT 'Riscos (%)',
ADD COLUMN IF NOT EXISTS bdi_despesas_financeiras FLOAT DEFAULT 1.2 COMMENT 'Despesas Financeiras (%)',
ADD COLUMN IF NOT EXISTS bdi_lucro FLOAT DEFAULT 8.0 COMMENT 'Lucro (%)',
ADD COLUMN IF NOT EXISTS bdi_outros FLOAT DEFAULT 0.0 COMMENT 'Outros (%)';

-- Verificar se as colunas foram criadas
SELECT 
    'bdi_administracao_central' AS campo,
    COUNT(*) AS existe
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'svc_scenarios'
AND COLUMN_NAME = 'bdi_administracao_central'

UNION ALL

SELECT 
    'bdi_seguros' AS campo,
    COUNT(*) AS existe
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'svc_scenarios'
AND COLUMN_NAME = 'bdi_seguros'

UNION ALL

SELECT 
    'bdi_garantias' AS campo,
    COUNT(*) AS existe
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'svc_scenarios'
AND COLUMN_NAME = 'bdi_garantias'

UNION ALL

SELECT 
    'bdi_riscos' AS campo,
    COUNT(*) AS existe
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'svc_scenarios'
AND COLUMN_NAME = 'bdi_riscos'

UNION ALL

SELECT 
    'bdi_despesas_financeiras' AS campo,
    COUNT(*) AS existe
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'svc_scenarios'
AND COLUMN_NAME = 'bdi_despesas_financeiras'

UNION ALL

SELECT 
    'bdi_lucro' AS campo,
    COUNT(*) AS existe
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'svc_scenarios'
AND COLUMN_NAME = 'bdi_lucro'

UNION ALL

SELECT 
    'bdi_outros' AS campo,
    COUNT(*) AS existe
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'svc_scenarios'
AND COLUMN_NAME = 'bdi_outros';

SELECT '✅ Migração BDI Detalhado concluída com sucesso!' AS status;
