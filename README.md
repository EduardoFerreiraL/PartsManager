# 🚀 Gerenciador de Peças - Frontend e Backend Separados

Sistema para gerenciamento de peças com upload de Excel e busca rápida, com arquitetura separada entre Frontend e Backend.

## 📁 Estrutura do Projeto

```
gerenciador-de-pecas/
├── backend/                 # API FastAPI
│   ├── main.py            # Servidor principal
│   ├── requirements.txt   # Dependências Python
│   └── .env              # Configurações (criar manualmente)
├── frontend/              # Interface web
│   ├── index.html        # Página principal com Tailwind CSS
│   ├── script.js         # Lógica JavaScript
│   └── tailwind.config.js # Configuração do Tailwind (opcional)
└── README.md             # Este arquivo
```

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI** - Framework web Python
- **Supabase** - Banco de dados PostgreSQL
- **Pandas** - Processamento de dados Excel
- **Uvicorn** - Servidor ASGI

### Frontend
- **HTML5** - Estrutura da página
- **Tailwind CSS** - Framework CSS utilitário para design moderno
- **JavaScript ES6+** - Lógica da aplicação
- **Font Awesome** - Ícones

## 🎨 Tailwind CSS

Este projeto utiliza **Tailwind CSS** para estilização, oferecendo:

- **Design System Consistente** - Cores, espaçamentos e tipografia padronizados
- **Classes Utilitárias** - Desenvolvimento rápido sem sair do HTML
- **Responsividade Nativa** - Breakpoints automáticos para mobile/desktop
- **Componentes Reutilizáveis** - Botões, cards e formulários padronizados
- **Customização Fácil** - Tema personalizado com cores primárias e secundárias

### Cores do Tema
- **Primary**: Azul (#3b82f6) para ações principais
- **Secondary**: Cinza (#64748b) para elementos secundários
- **Success**: Verde para mensagens de sucesso
- **Error**: Vermelho para mensagens de erro
- **Info**: Azul claro para informações

## 🚀 Como Executar

### 1. Configurar o Backend

#### Instalar dependências:
```bash
cd backend
pip install -r requirements.txt
```

#### Criar arquivo .env:
```env
SUPABASE_URL="https://seu-projeto.supabase.co"
SUPABASE_KEY="sua-chave-de-servico-aqui"
```

#### Executar o servidor:
```bash
uvicorn main:app --reload
```

O backend estará disponível em: `http://127.0.0.1:8000`

### 2. Executar o Frontend

#### Abrir o arquivo HTML:
- Navegue até a pasta `frontend`
- Abra `index.html` no seu navegador
- O Tailwind CSS é carregado via CDN automaticamente

#### Com Python (servidor local):
```bash
cd frontend
python -m http.server 3000
```

Acesse: `http://localhost:3000`

## 🔧 Funcionalidades

### ✅ Implementadas
- **Status da API** - Verificação de conectividade com indicador visual
- **Estatísticas** - Contagem de peças no banco com cards informativos
- **Upload de Excel** - Interface drag & drop para arquivos .xlsx
- **Busca de Peças** - Filtros por código, nome e categoria
- **Interface Responsiva** - Funciona perfeitamente em desktop e mobile
- **Design Moderno** - Cards elevados, gradientes e animações suaves

### 🚧 Futuras Implementações
- Paginação de resultados
- Exportação de dados
- Edição de peças
- Sistema de usuários
- Logs de atividades

## 📊 Endpoints da API

### GET `/api/health`
Verifica o status da API e conexão com o banco

### GET `/api/stats`
Retorna estatísticas do banco de dados

### POST `/api/upload-excel`
Recebe arquivo Excel e insere dados no banco

### GET `/api/pecas`
Busca peças com filtros opcionais

## 🎨 Interface do Usuário

### Design Features
- **Gradiente Moderno** - Fundo azul/roxo com transições suaves
- **Cards Elevados** - Efeito de profundidade com sombras
- **Animações CSS** - Transições e hover effects
- **Ícones Intuitivos** - Font Awesome para melhor UX
- **Responsividade Total** - Grid system adaptativo
- **Sistema de Cores** - Paleta consistente e acessível

### Componentes Tailwind
1. **Header** - Título com gradiente e sombra
2. **Status Card** - Monitoramento da API com indicadores visuais
3. **Stats Card** - Estatísticas em grid responsivo
4. **Upload Card** - Área de upload com drag & drop visual
5. **Search Card** - Formulário de busca com validação
6. **Results Container** - Tabela responsiva com hover effects

## 🔍 Como Usar

### 1. Verificar Status
- Clique em "Verificar" no card de status
- Aguarde a resposta da API
- Indicador visual mostra o status (verde = online, vermelho = offline)

### 2. Upload de Dados
- Clique em "Selecionar arquivo Excel"
- Escolha um arquivo .xlsx
- Clique em "Enviar Arquivo"
- Feedback visual mostra o progresso

### 3. Buscar Peças
- Preencha pelo menos um campo de busca
- Pressione Enter ou clique em "Buscar"
- Visualize os resultados na tabela responsiva
- Use o botão "Limpar" para resetar os campos

## ⚠️ Configurações Importantes

### CORS
O backend está configurado para aceitar requisições de qualquer origem (`allow_origins=["*"]`). Em produção, especifique apenas os domínios permitidos.

### Supabase
- Crie uma conta em [supabase.com](https://supabase.com)
- Crie um novo projeto
- Obtenha as credenciais em Settings → API
- Crie a tabela `pecas` ou deixe o sistema criar automaticamente

### Tailwind CSS
- **CDN**: Carregado automaticamente via CDN
- **Configuração Local**: Use `tailwind.config.js` para desenvolvimento
- **Customização**: Modifique as cores no arquivo de configuração

## 🐛 Solução de Problemas

### Erro de Conexão com API
- Verifique se o backend está rodando
- Confirme a URL no arquivo `script.js`
- Verifique as configurações CORS

### Erro de Upload
- Confirme que o arquivo é .xlsx
- Verifique a estrutura das colunas
- Confirme as credenciais do Supabase

### Problemas de Estilo
- Verifique se o Tailwind CDN está carregando
- Confirme se o Font Awesome está acessível
- Teste em diferentes navegadores

## 📱 Compatibilidade

### Navegadores Suportados
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

### Dispositivos
- Desktop (Windows, macOS, Linux)
- Tablet (iOS, Android)
- Mobile (iOS, Android)

## 🔒 Segurança

### Recomendações
- Use HTTPS em produção
- Implemente autenticação de usuários
- Valide arquivos de entrada
- Configure CORS adequadamente
- Use variáveis de ambiente para credenciais

## 📈 Performance

### Otimizações
- Upload em lote para grandes arquivos
- Paginação de resultados
- Cache de consultas frequentes
- Compressão de respostas
- Tailwind CSS otimizado via CDN

## 🎨 Personalização do Tailwind

### Cores Customizadas
```javascript
// No arquivo tailwind.config.js
colors: {
  primary: {
    500: '#3b82f6', // Azul principal
    600: '#2563eb', // Azul escuro
  }
}
```

### Componentes Reutilizáveis
```html
<!-- Botão primário -->
<button class="btn-primary">
  <i class="fas fa-upload"></i>Enviar
</button>

<!-- Card padrão -->
<div class="bg-white rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300">
  <!-- Conteúdo -->
</div>
```

## 🤝 Contribuição

Para contribuir com o projeto:
1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Implemente as mudanças
4. Teste thoroughly
5. Envie um pull request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma issue no repositório
- Consulte a documentação da API
- Verifique os logs do console
- Consulte a documentação do Tailwind CSS

---

**Desenvolvido com ❤️ e Tailwind CSS para resolver problemas de performance com Excel**
