# Sistema de Histórico e CTRL+Z - Gerenciador de Peças

## Visão Geral

O sistema implementa um histórico robusto de alterações que permite desfazer ações usando **Ctrl+Z** tanto em células individuais quanto globalmente.

## Como Funciona

### 1. Histórico por Célula
- Cada célula mantém seu próprio histórico de alterações
- Máximo de **10 alterações** por célula
- Armazena: valor antigo, valor novo e timestamp

### 2. Histórico Global
- Mantém todas as alterações de todas as células
- Máximo de **50 alterações** globais
- Permite desfazer a última alteração feita em qualquer célula

### 3. Comportamento do CTRL+Z

#### Quando uma célula está em edição:
- **Ctrl+Z** desfaz a última alteração naquela célula específica
- Restaura o valor anterior no textarea
- Mantém a célula em modo de edição

#### Quando nenhuma célula está em edição:
- **Ctrl+Z** desfaz a última alteração global
- Restaura o valor anterior na célula correspondente
- Funciona mesmo se a célula não estiver visível na página atual

### 4. Comportamento do ESC
- **ESC** cancela a edição atual
- Restaura o valor original da célula
- Remove a célula do modo de edição
- **NÃO** afeta o histórico

## Estrutura de Dados

```javascript
appState = {
    editHistory: Map,           // Histórico por célula
    globalEditHistory: Array,   // Histórico global
    maxHistorySize: 10,         // Máximo por célula
    maxGlobalHistorySize: 50    // Máximo global
}
```

## Funções Principais

### `addToEditHistory(cellId, oldValue, newValue)`
- Adiciona entrada ao histórico da célula
- Adiciona entrada ao histórico global
- Gerencia limites de tamanho

### `undoLastEdit(cellId)`
- Desfaz última alteração de uma célula específica
- Atualiza interface e appState
- Retorna true se bem-sucedido

### `undoLastGlobalEdit()`
- Desfaz última alteração global
- Remove entrada do histórico da célula
- Atualiza interface e appState

### `clearEditHistory()`
- Limpa todo o histórico
- Útil para resetar o sistema

### `showHistoryInfo()`
- Mostra informações sobre o estado do histórico
- Útil para debug e monitoramento

## Fluxo de Uso

1. **Editar célula**: Duplo-clique na célula
2. **Fazer alterações**: Digite no textarea
3. **Desfazer com Ctrl+Z**: Desfaz última alteração na célula
4. **Salvar**: Enter ou clique fora
5. **Desfazer global**: Ctrl+Z fora de edição

## Exemplos de Uso

### Desfazer alteração em célula específica:
```javascript
// Célula deve estar em modo de edição
undoLastEdit('cell_0_1');
```

### Desfazer última alteração global:
```javascript
// Funciona de qualquer lugar
undoLastGlobalEdit();
```

### Verificar histórico:
```javascript
showHistoryInfo();
```

## Debug e Teste

### Botões de teste disponíveis:
- **Testar Copiar/Colar + Ctrl+Z + ESC**: Testa funcionalidades básicas
- **Testar Fluxo de Edição**: Testa ciclo completo de edição
- **Info do Histórico**: Mostra estado atual do histórico
- **Limpar Histórico**: Reseta todo o sistema

### Console logs:
- Todas as operações são logadas no console
- Formato: emoji + descrição + detalhes
- Útil para debug e monitoramento

## Considerações Técnicas

### Performance:
- Histórico limitado para evitar consumo excessivo de memória
- Operações O(1) para desfazer
- Limpeza automática de entradas antigas

### Consistência:
- AppState sempre sincronizado com interface
- Histórico mantido mesmo com mudança de página
- Validação de dados antes de aplicar alterações

### Robustez:
- Tratamento de erros em todas as operações
- Fallbacks para casos extremos
- Logs detalhados para debug

## Troubleshooting

### Problema: Ctrl+Z não funciona
**Solução**: Verificar se há alterações no histórico usando `showHistoryInfo()`

### Problema: Histórico não persiste
**Solução**: Verificar se `addToEditHistory()` está sendo chamada

### Problema: Valores não são restaurados
**Solução**: Verificar se `appState.allResults` está sendo atualizado

### Problema: Interface não atualiza
**Solução**: Verificar se `data-value` e `textContent` estão sincronizados

## Melhorias Futuras

1. **Persistência**: Salvar histórico no localStorage
2. **Redo**: Implementar Ctrl+Y para refazer
3. **Histórico visual**: Interface para navegar no histórico
4. **Agrupamento**: Agrupar alterações relacionadas
5. **Sincronização**: Sincronizar histórico entre abas
