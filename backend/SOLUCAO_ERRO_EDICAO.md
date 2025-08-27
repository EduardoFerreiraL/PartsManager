# 🔧 **Solução para Erro de Edição - "PUT /api/pecas/undefined"**

## 🚨 **Problema identificado:**
O erro `"PUT /api/pecas/undefined HTTP/1.1" 422 Unprocessable Content` indica que o ID da peça está chegando como `undefined` no frontend.

## 🔍 **Causas possíveis:**

### **1. Estrutura dos dados incorreta**
- O campo `id` pode não estar sendo retornado pela API
- O campo `id` pode ter um nome diferente
- Os dados podem estar vazios

### **2. Problema na construção da tabela**
- O atributo `data-peca-id` pode não estar sendo definido corretamente
- O índice da linha pode estar incorreto

## 🛠️ **Soluções implementadas:**

### **1. Adicionado atributo `data-peca-id`**
```html
<!-- Antes -->
<td data-row="${rowIndex}" data-col="${colIndex}" data-column="${column}">

<!-- Depois -->
<td data-row="${rowIndex}" data-col="${colIndex}" data-column="${column}" data-peca-id="${peca.id}">
```

### **2. Corrigida função `saveCell`**
```javascript
// Antes: buscava ID através do índice da linha
const actualRowIndex = (appState.currentPage - 1) * appState.itemsPerPage + rowIndex;
const peca = appState.allResults[actualRowIndex];
const pecaId = peca.id;

// Depois: busca ID diretamente do atributo da célula
const pecaId = cell.getAttribute('data-peca-id');
```

### **3. Adicionado debug e validação**
```javascript
if (!pecaId || pecaId === 'undefined') {
    throw new Error('ID da peça não encontrado');
}

console.log('Salvando célula:', { pecaId, column, newValue, updateData });
```

## 🧪 **Como testar:**

### **1. Verificar console do navegador**
1. Abra a tela "Visualizar Itens"
2. Pressione F12 para abrir o DevTools
3. Vá para a aba "Console"
4. Procure por mensagens de debug:
   - "Dados carregados: ..."
   - "Salvando célula: ..."

### **2. Verificar estrutura dos dados**
1. No console, procure por:
   ```
   Dados carregados: {
     total: X,
     primeiraPeca: {...},
     colunas: [...]
   }
   ```
2. Verifique se `primeiraPeca` tem um campo `id`
3. Verifique se `colunas` inclui `id`

### **3. Testar edição**
1. Clique duas vezes em uma célula
2. Digite um novo valor
3. Pressione Enter
4. Verifique no console se aparece:
   ```
   Salvando célula: { pecaId: "123", column: "description", newValue: "...", updateData: {...} }
   ```

## 🚀 **Passos para resolver:**

### **Passo 1: Verificar se o servidor está rodando**
```bash
cd backend
uvicorn main:app --reload
```

### **Passo 2: Verificar se há dados no banco**
1. Acesse a tela "Visualizar Itens"
2. Verifique se aparecem peças na tabela
3. Se não aparecer, carregue dados primeiro

### **Passo 3: Verificar estrutura dos dados**
1. Abra o console do navegador (F12)
2. Procure por mensagens de debug
3. Verifique se o campo `id` está presente

### **Passo 4: Testar edição**
1. Clique duas vezes em uma célula
2. Digite um valor de teste
3. Pressione Enter
4. Verifique se salva sem erro

## 🔍 **Se ainda não funcionar:**

### **1. Verificar banco de dados**
```sql
-- No Supabase, execute:
SELECT * FROM pecas LIMIT 5;
```
Verifique se a tabela tem uma coluna `id` com valores.

### **2. Verificar API diretamente**
```bash
# Teste a API diretamente
curl http://localhost:8000/api/pecas?limit=1
```
Verifique se retorna um campo `id`.

### **3. Verificar estrutura da tabela**
```sql
-- No Supabase, execute:
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pecas';
```
Verifique se existe uma coluna `id` do tipo `SERIAL` ou `INTEGER`.

## 📋 **Checklist de verificação:**

- [ ] Servidor está rodando (`uvicorn main:app --reload`)
- [ ] Banco de dados está conectado
- [ ] Tabela `pecas` existe e tem dados
- [ ] Coluna `id` existe na tabela
- [ ] API retorna campo `id` nas peças
- [ ] Console mostra "Dados carregados" com ID
- [ ] Edição mostra "Salvando célula" com ID correto

## 🎯 **Resultado esperado:**
Após as correções, a edição deve funcionar assim:
1. **Clique duas vezes** na célula
2. **Digite** o novo valor
3. **Pressione Enter**
4. **Célula fica verde** (salvo com sucesso)
5. **Valor persiste** após recarregar a página

---

**🔧 Se ainda houver problemas, execute o script de teste:**
```bash
cd backend
python teste_dados.py
```

