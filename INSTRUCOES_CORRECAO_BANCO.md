# 🔧 Instruções para Correção da Estrutura do Banco de Dados

## 📋 Problema Identificado

Baseado na imagem fornecida, a estrutura atual do banco de dados não corresponde ao que o código espera. Foram identificadas as seguintes diferenças:

### Estrutura Atual do Banco (da imagem):
- `part_number` (int8)
- `chinese_description` (text)
- `description` (text)
- `ncm` (int8)
- `origin` (int2)
- `date_of_creation` (date)
- `review_date` (date)
- `requester` (text)
- `machine` (text)

### Estrutura Esperada pelo Código (antes da correção):
- `part_number` (string)
- `chinese_description` (string)
- `description` (string)
- `ncm` (string)
- `date_of_creation` (date)
- `review_date` (date)
- `process` (string)
- `machine` (string)

## 🛠️ Solução

Execute os seguintes comandos SQL no Supabase para corrigir a estrutura:

### 1. Acesse o Supabase
1. Vá para [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Selecione seu projeto
3. Clique em "SQL Editor" no menu lateral

### 2. Execute os Comandos SQL

```sql
-- Comandos SQL para corrigir a estrutura da tabela pecas
-- Execute estes comandos no SQL Editor do Supabase

-- 1. Adicionar colunas que podem estar faltando
ALTER TABLE pecas ADD COLUMN IF NOT EXISTS chinese_description TEXT;
ALTER TABLE pecas ADD COLUMN IF NOT EXISTS origin INT2;
ALTER TABLE pecas ADD COLUMN IF NOT EXISTS requester TEXT;

-- 2. Renomear colunas para corresponder à imagem (se necessário)
-- ALTER TABLE pecas RENAME COLUMN chinese_desc TO chinese_description;
-- ALTER TABLE pecas RENAME COLUMN date_of_crea TO date_of_creation;

-- 3. Ajustar tipos de dados
ALTER TABLE pecas ALTER COLUMN part_number TYPE BIGINT;
ALTER TABLE pecas ALTER COLUMN ncm TYPE BIGINT;

-- 4. Remover coluna process se existir
ALTER TABLE pecas DROP COLUMN IF EXISTS process;

-- 5. Verificar estrutura final
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'pecas' ORDER BY ordinal_position;
```

### 3. Verificação

Após executar os comandos, a estrutura deve ficar igual à imagem fornecida:

| Nome da Coluna | Tipo |
|----------------|------|
| part_number | int8 |
| chinese_description | text |
| description | text |
| ncm | int8 |
| origin | int2 |
| date_of_creation | date |
| review_date | date |
| requester | text |
| machine | text |

## ✅ Alterações Feitas no Código

### Backend (`backend/main.py`):
- ✅ Atualizado `column_types` para usar os nomes corretos
- ✅ Atualizado `available_columns` na função de upload
- ✅ Atualizado filtros de busca para usar `date_of_crea`
- ✅ Atualizado `allowed_fields` na função de atualização
- ✅ Atualizado validação de campos obrigatórios

### Frontend (`frontend/visualizar.html`):
- ✅ Atualizado campos obrigatórios para usar `date_of_crea`
- ✅ Atualizado `getFieldDisplayName` para incluir novos campos
- ✅ Adicionado suporte para todas as colunas da imagem

## 🧪 Teste Após Correção

1. **Reinicie o servidor backend**:
   ```bash
   cd backend
   python main.py
   ```

2. **Teste a funcionalidade**:
   - Acesse `frontend/visualizar.html`
   - Verifique se as colunas aparecem corretamente
   - Teste a edição de células
   - Teste a validação de campos obrigatórios

3. **Verifique os logs**:
   - Observe se não há erros de coluna não encontrada
   - Verifique se os dados são carregados corretamente

## ⚠️ Importante

- **Faça backup dos dados** antes de executar os comandos SQL
- **Execute os comandos em ordem** para evitar erros
- **Teste o sistema** após cada alteração
- **Verifique se os dados existentes** foram preservados

## 🆘 Em Caso de Problemas

Se algo der errado:

1. **Verifique os logs do Supabase** para erros SQL
2. **Verifique os logs do backend** para erros de conexão
3. **Teste a conexão** com o endpoint `/api/debug-structure`
4. **Restaure o backup** se necessário

## 📞 Suporte

Se precisar de ajuda:
1. Verifique os logs de erro
2. Teste a conexão com o banco
3. Verifique se todas as colunas foram criadas corretamente
4. Execute o comando de verificação final

---

**Status**: ✅ Código atualizado para trabalhar com a estrutura correta do banco
**Próximo passo**: Execute os comandos SQL no Supabase
