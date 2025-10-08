# 🔧 Solução para Erro PGRST205 - Cache de Esquema

## 📋 **Problema Identificado**

Você está enfrentando o erro:
```
"Erro na conexão com o banco: {'message': "Could not find the table 'public.pecas' in the schema cache", 'code': 'PGRST205', 'hint': None, 'details': None}"
```

## 🔍 **O que aconteceu?**

Este erro ocorre quando você **reativa o banco de dados** no Supabase. O problema é que:

1. **Cache de esquema desatualizado**: O PostgREST (serviço usado pelo Supabase) mantém um cache do esquema do banco
2. **Após reativação**: O cache não é atualizado automaticamente
3. **Tabela existe**: A tabela `pecas` existe no banco, mas o cache não a reconhece

## ✅ **Soluções Disponíveis**

### **Solução 1: Recarregar Cache Automaticamente (Recomendada)**

Execute o comando abaixo para tentar recarregar o cache automaticamente:

```bash
# No terminal, dentro da pasta backend
python -c "import requests; response = requests.post('http://localhost:8000/api/reload-schema-cache'); print('Status:', response.status_code); print('Resposta:', response.json())"
```

### **Solução 2: Recarregar Cache Manualmente**

1. **Acesse o Supabase Dashboard**:
   - Vá para [https://supabase.com/dashboard](https://supabase.com/dashboard)
   - Selecione seu projeto

2. **Abra o SQL Editor**:
   - Clique em "SQL Editor" no menu lateral

3. **Execute o comando**:
   ```sql
   NOTIFY pgrst, 'reload schema';
   ```

4. **Clique em "Run"** para executar

### **Solução 3: Aguardar Atualização Automática**

- **Aguarde 5-10 minutos** - O cache é atualizado automaticamente
- **Teste novamente** após o tempo de espera

### **Solução 4: Verificar Status da Tabela**

Execute este comando para verificar se a tabela está acessível:

```bash
# No terminal, dentro da pasta backend
python -c "import requests; response = requests.get('http://localhost:8000/api/check-table'); print('Status:', response.status_code); print('Resposta:', response.json())"
```

## 🚀 **Passos para Resolver**

### **Passo 1: Testar Conexão Direta**
```bash
cd backend
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
try:
    response = supabase.table('pecas').select('*').limit(1).execute()
    print('✅ Conexão direta OK - Tabela existe')
except Exception as e:
    print(f'❌ Erro na conexão direta: {e}')
"
```

### **Passo 2: Recarregar Cache**
```bash
# Execute o endpoint de recarregamento
python -c "import requests; response = requests.post('http://localhost:8000/api/reload-schema-cache'); print(response.json())"
```

### **Passo 3: Testar Aplicação**
1. Acesse a aplicação no navegador
2. Tente carregar dados
3. Se ainda der erro, aguarde alguns minutos e tente novamente

## 🔧 **Prevenção Futura**

Para evitar este problema no futuro, você pode:

### **1. Configurar Recarregamento Automático**

Execute este SQL no Supabase para configurar recarregamento automático:

```sql
-- Criar função para notificar PostgREST
CREATE OR REPLACE FUNCTION pgrst_watch() RETURNS event_trigger
  LANGUAGE plpgsql
  AS $$
BEGIN
  NOTIFY pgrst, 'reload schema';
END;
$$;

-- Criar trigger de evento
CREATE EVENT TRIGGER pgrst_watch
  ON ddl_command_end
  EXECUTE FUNCTION pgrst_watch();
```

### **2. Monitorar Status**

Use este endpoint para monitorar o status da tabela:

```bash
# Verificar status da tabela
curl http://localhost:8000/api/check-table
```

## 📊 **Verificação de Sucesso**

Após aplicar a solução, você deve ver:

1. **Conexão OK**: `✅ Conexão com banco OK - Tabela pecas existe`
2. **API funcionando**: Status 200 nas requisições
3. **Dados carregando**: Registros aparecendo na aplicação

## 🆘 **Se Nada Funcionar**

Se todas as soluções falharem:

1. **Reinicie o servidor Supabase** (se possível)
2. **Aguarde 15-30 minutos** para atualização completa
3. **Verifique se a tabela existe**:
   ```sql
   SELECT * FROM information_schema.tables 
   WHERE table_schema = 'public' AND table_name = 'pecas';
   ```

## 📞 **Suporte**

Se o problema persistir:
- Verifique os logs do servidor: `uvicorn main:app --reload`
- Teste a conexão direta com o banco
- Verifique se as credenciais estão corretas no arquivo `.env`

---

**💡 Dica**: Este erro é comum após reativação de bancos Supabase. A solução mais eficaz é executar `NOTIFY pgrst, 'reload schema';` no SQL Editor.
