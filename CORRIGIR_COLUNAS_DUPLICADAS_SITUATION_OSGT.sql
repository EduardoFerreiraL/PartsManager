-- ============================================
-- Script SQL para Corrigir Colunas Duplicadas de Situation_OSGT
-- ============================================
-- Execute este script no SQL Editor do Supabase

-- 1. Verificar todas as colunas da tabela pecas
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'pecas'
AND (
    LOWER(column_name) LIKE '%situation%' 
    OR LOWER(column_name) LIKE '%osgt%'
    OR column_name LIKE '%Situation%'
)
ORDER BY column_name;

-- 2. Verificar se há dados nas colunas duplicadas
-- Substitua 'Situation_osgt' ou outro nome pela coluna duplicada encontrada
SELECT 
    COUNT(*) as total_registros,
    COUNT("Situation_OSGT") as com_situation_osgt,
    COUNT("Situation_osgt") as com_situation_osgt_minusculo,
    COUNT(CASE WHEN "Situation_OSGT" IS NOT NULL THEN 1 END) as nao_nulos_osgt,
    COUNT(CASE WHEN "Situation_osgt" IS NOT NULL THEN 1 END) as nao_nulos_osgt_minusculo
FROM pecas;

-- 3. Migrar dados da coluna duplicada para a coluna correta (se necessário)
-- ATENÇÃO: Execute apenas se houver dados na coluna duplicada que não estão na correta
-- Descomente e ajuste o nome da coluna duplicada conforme necessário

-- UPDATE pecas 
-- SET "Situation_OSGT" = "Situation_osgt"
-- WHERE "Situation_OSGT" IS NULL 
-- AND "Situation_osgt" IS NOT NULL;

-- 4. Remover a coluna duplicada
-- ATENÇÃO: Faça backup antes de executar!
-- Descomente e ajuste o nome da coluna duplicada conforme necessário

-- ALTER TABLE pecas DROP COLUMN IF EXISTS "Situation_osgt";
-- ALTER TABLE pecas DROP COLUMN IF EXISTS "Situation_ O S G T";
-- ALTER TABLE pecas DROP COLUMN IF EXISTS "situation_osgt";

-- 5. Verificar se a constraint CHECK existe e está correta
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'pecas'::regclass 
AND conname LIKE '%situation%';

-- 6. Se a constraint existir com valores antigos, removê-la e recriar
ALTER TABLE pecas DROP CONSTRAINT IF EXISTS check_situation_osgt;

-- 7. Criar a constraint correta com os valores atualizados
ALTER TABLE pecas ADD CONSTRAINT check_situation_osgt 
CHECK ("Situation_OSGT" IS NULL OR "Situation_OSGT" IN ('ENVIADO OSGT', 'RASCUNHO', 'DESATIVADO'));

-- 8. Verificar estrutura final
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'pecas'
ORDER BY ordinal_position;

-- ============================================
-- INSTRUÇÕES:
-- ============================================
-- 1. Execute primeiro a query 1 para identificar todas as colunas relacionadas a Situation_OSGT
-- 2. Execute a query 2 para verificar se há dados nas colunas duplicadas
-- 3. Se houver dados na coluna duplicada que não estão na correta, execute a query 3 (descomentada)
-- 4. Execute a query 4 para remover a coluna duplicada (ajuste o nome conforme necessário)
-- 5. Execute as queries 5, 6 e 7 para corrigir a constraint CHECK
-- 6. Execute a query 8 para verificar a estrutura final
-- ============================================
