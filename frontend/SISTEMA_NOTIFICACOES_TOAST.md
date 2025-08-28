# Sistema de Notificações Toast - Gerenciador de Peças

## Visão Geral

O sistema implementa notificações toast modernas que aparecem no canto superior direito da tela, substituindo as mensagens antigas que apareciam no quadro principal. Isso permite que o usuário veja os avisos sem precisar rolar a tela.

## Características

### 🎯 **Posicionamento**
- **Localização**: Canto superior direito da tela
- **Z-index**: 10000 (sempre visível)
- **Empilhamento**: Múltiplas notificações empilhadas verticalmente

### 🎨 **Design**
- **Estilo**: Cards modernos com gradientes
- **Cores**: Diferentes para cada tipo de mensagem
- **Bordas**: Borda esquerda colorida indicando o tipo
- **Sombras**: Efeitos de profundidade

### ⏱️ **Comportamento**
- **Auto-remoção**: Configurável (padrão: 5 segundos)
- **Animações**: Slide in/out suaves
- **Barra de progresso**: Visual indica tempo restante
- **Fechamento manual**: Botão X para fechar

## Tipos de Notificação

### 1. **Success** ✅
- **Cor**: Verde (#10b981)
- **Ícone**: check-circle
- **Uso**: Operações bem-sucedidas

### 2. **Error** ❌
- **Cor**: Vermelho (#ef4444)
- **Ícone**: exclamation-circle
- **Uso**: Erros e falhas

### 3. **Warning** ⚠️
- **Cor**: Amarelo (#f59e0b)
- **Ícone**: exclamation-triangle
- **Uso**: Avisos e alertas

### 4. **Info** ℹ️
- **Cor**: Azul (#3b82f6)
- **Ícone**: info-circle
- **Uso**: Informações gerais

## Funções Principais

### `showToast(message, type, duration)`
```javascript
// Exemplo de uso
showToast('Operação realizada com sucesso!', 'success', 5000);
showToast('Erro ao processar dados', 'error', 8000);
showToast('Aviso importante', 'warning', 0); // Sem auto-remoção
```

**Parâmetros:**
- `message`: Texto da notificação
- `type`: Tipo (success, error, warning, info)
- `duration`: Duração em ms (0 = persistente)

### `removeToast(toastId)`
```javascript
// Remove toast específico
removeToast('toast-123');
```

### `clearAllToasts()`
```javascript
// Remove todas as notificações
clearAllToasts();
```

## Mensagens Convertidas

### ✅ **Operações de Sucesso**
- "X peça(s) carregada(s) automaticamente"
- "X peça(s) encontrada(s)"
- "Arquivo CSV exportado com sucesso!"
- "Célula salva com sucesso!"
- "Alteração desfeita com sucesso!"
- "Histórico de edições limpo com sucesso!"

### ❌ **Erros**
- "Erro ao carregar itens: [detalhes]"
- "Erro ao realizar busca: [detalhes]"
- "Erro ao exportar arquivo: [detalhes]"
- "Erro ao salvar: [detalhes]"
- "Nenhum resultado para exportar"

### ℹ️ **Informações**
- "Nenhuma peça encontrada no banco de dados"
- "Nada para desfazer nesta célula"
- "Edição cancelada - valor original restaurado"
- "Histórico: X células, Y alterações globais"

### 🎯 **Ações**
- "Célula copiada!"
- "X células copiadas!"

## Botões de Teste

### **Testar Toasts** 🔔
- Demonstra todos os tipos de notificação
- Mostra diferentes durações
- Testa sistema de empilhamento

### **Limpar Toasts** 🗑️
- Remove todas as notificações ativas
- Útil para limpar a tela

## CSS e Animações

### **Entrada (Slide In)**
```css
@keyframes toastSlideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

### **Saída (Slide Out)**
```css
@keyframes toastSlideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}
```

### **Barra de Progresso**
```css
@keyframes toastProgress {
    from { width: 100%; }
    to { width: 0%; }
}
```

## Estrutura HTML

```html
<div class="toast-container">
    <div class="toast success">
        <i class="fas fa-check-circle toast-icon"></i>
        <span class="toast-message">Mensagem de sucesso</span>
        <button class="toast-close">
            <i class="fas fa-times"></i>
        </button>
        <div class="toast-progress"></div>
    </div>
</div>
```

## Responsividade

### **Mobile**
- Máxima largura: 90vw
- Padding ajustado
- Fonte otimizada

### **Desktop**
- Máxima largura: 400px
- Sombras mais pronunciadas
- Animações suaves

## Compatibilidade

### **Navegadores Suportados**
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### **Fallbacks**
- Sistema antigo mantido para compatibilidade
- Função `showMessage()` redireciona para toast
- Sem quebra de funcionalidade

## Debug e Monitoramento

### **Console Logs**
```javascript
console.log(`🍞 Toast ${type}: ${message}`);
```

### **IDs Únicos**
- Cada toast recebe ID único
- Formato: `toast-{contador}`
- Útil para debug e controle

## Melhorias Futuras

1. **Som**: Notificações sonoras opcionais
2. **Posicionamento**: Configuração de posição
3. **Temas**: Modo escuro/claro
4. **Agrupamento**: Agrupar notificações similares
5. **Histórico**: Log de notificações
6. **Personalização**: Cores e estilos customizáveis

## Troubleshooting

### **Problema: Toasts não aparecem**
**Solução**: Verificar se `toastContainer` existe no DOM

### **Problema: Z-index conflitante**
**Solução**: Ajustar z-index se necessário

### **Problema: Animações travadas**
**Solução**: Verificar se CSS está carregado corretamente

### **Problema: Múltiplos toasts**
**Solução**: Usar `clearAllToasts()` para limpar

## Exemplos de Uso

### **Notificação Simples**
```javascript
showToast('Operação concluída!', 'success');
```

### **Notificação Persistente**
```javascript
showToast('Processando...', 'info', 0);
// Remover manualmente depois
removeToast(toastId);
```

### **Notificação de Erro Longa**
```javascript
showToast('Erro detalhado com muitas informações...', 'error', 10000);
```

### **Múltiplas Notificações**
```javascript
showToast('Primeira mensagem', 'info');
setTimeout(() => {
    showToast('Segunda mensagem', 'success');
}, 1000);
```

