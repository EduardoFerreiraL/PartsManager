// frontend/navbar.js
class NavBar extends HTMLElement {
    // IMPORTÂNCIA: Armazena o HTML em cache após o primeiro carregamento
    // Evita múltiplas requisições HTTP desnecessárias
    static htmlCache = null;
    static loadingPromise = null;

    async connectedCallback() {
        // Lê qual aba deve ficar ativa (padrão: 'home' para "Menu Principal")
        // IMPORTÂNCIA: Permite que cada página escolha facilmente qual aba fica em destaque
        this.active = (this.getAttribute('active') || 'home').toLowerCase();
        
        // IMPORTÂNCIA: Carrega o HTML do navbar de forma assíncrona
        // Se já está carregando, aguarda o carregamento anterior (evita múltiplas requisições)
        if (!NavBar.htmlCache) {
            if (!NavBar.loadingPromise) {
                NavBar.loadingPromise = this.loadNavbarHTML();
            }
            await NavBar.loadingPromise;
        }
        
        // Renderiza a barra de navegação com o HTML carregado
        this.innerHTML = NavBar.htmlCache;

        // Liga os handlers do menu mobile
        this.setupMobileMenuHandlers();
        
        // Aplica o destaque da aba ativa
        setTimeout(() => this.applyActive(), 0);
        // Aplica visibilidade por permissão (se usuário já estiver carregado)
        if (window.currentUser != null) this.applyPermissions(window.currentUser.nivelPermissao);
    }

    /** Mostra/oculta itens do menu conforme nivelPermissao (0=máx, 3=mín). Visível se nivel <= data-permission-min. */
    applyPermissions(nivel) {
        if (nivel == null || nivel === undefined) return;
        this.querySelectorAll('[data-permission-min]').forEach(el => {
            const min = parseInt(el.getAttribute('data-permission-min'), 10);
            el.style.display = (nivel <= min) ? '' : 'none';
        });
    }

    // IMPORTÂNCIA: Carrega o HTML do arquivo navbar.html via Fetch API
    // Este método é assíncrono e cacheia o resultado para reutilização
    async loadNavbarHTML() {
        // Lista de caminhos possíveis para tentar
        const paths = [
            'components/navbar.html',           // Caminho relativo (desenvolvimento local)
            '/static/components/navbar.html',   // Caminho absoluto (servido pelo FastAPI)
            './components/navbar.html'           // Caminho relativo alternativo
        ];
        
        for (const path of paths) {
            try {
                const response = await fetch(path);
                if (response.ok) {
                    NavBar.htmlCache = await response.text();
                    NavBar.loadingPromise = null;
                    return; // Sucesso, sair do loop
                }
            } catch (error) {
                // Continuar tentando o próximo caminho
                continue;
            }
        }
        
        // Se nenhum caminho funcionou, usar fallback
        console.warn('Não foi possível carregar navbar.html de nenhum caminho. Usando fallback.');
        NavBar.htmlCache = this.getFallbackHTML();
        NavBar.loadingPromise = null;
    }

    // IMPORTÂNCIA: HTML de fallback caso o arquivo não carregue
    // Garante que a navbar sempre apareça, mesmo sem conexão
    getFallbackHTML() {
        return `<nav class="bg-white/10 backdrop-blur-md border-b border-white/20 sticky top-0 z-50">
            <div class="container mx-auto px-4">
                <div class="flex items-center justify-between h-16">
                    <div class="flex items-center space-x-4">
                        <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                            <i class="fas fa-cogs text-white text-lg"></i>
                        </div>
                        <h1 class="text-xl font-bold text-white hidden sm:block">Gerenciador de Peças</h1>
                    </div>
                    <div class="hidden md:flex items-center space-x-1">
                        <a href="/" data-key="home" data-permission-min="3" class="nav-link group flex items-center px-4 py-2 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-home text-white text-lg mr-2 group-hover:scale-110 transition-transform"></i>
                            <span class="font-medium text-white">Menu Principal</span>
                        </a>
                        <a href="/adicionar" data-key="adicionar" data-permission-min="2" class="nav-link group flex items-center px-4 py-2 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-plus text-white text-lg mr-2 group-hover:scale-110 transition-transform"></i>
                            <span class="font-medium text-white">Adicionar Itens</span>
                        </a>
                        <a href="/visualizar" data-key="visualizar" data-permission-min="3" class="nav-link group flex items-center px-4 py-2 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-search text-white text-lg mr-2 group-hover:scale-110 transition-transform"></i>
                            <span class="font-medium text-white">Visualizar Itens</span>
                        </a>
                        <a href="/atualizacao-em-massa" data-key="atualizacao-em-massa" data-permission-min="2" class="nav-link group flex items-center px-4 py-2 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-file-excel text-white text-lg mr-2 group-hover:scale-110 transition-transform"></i>
                            <span class="font-medium text-white">Atualização em massa</span>
                        </a>
                        <a href="/dashboard" data-key="dashboard" data-permission-min="2" class="nav-link group flex items-center px-4 py-2 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-chart-line text-white text-lg mr-2 group-hover:scale-110 transition-transform"></i>
                            <span class="font-medium text-white">Dashboard</span>
                        </a>
                        <a href="/aprovar-usuarios" data-key="aprovar-usuarios" data-permission-min="1" class="nav-link group flex items-center px-4 py-2 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-user-check text-white text-lg mr-2 group-hover:scale-110 transition-transform"></i>
                            <span class="font-medium text-white">Aprovar usuários</span>
                        </a>
                    </div>
                    <div id="user-menu-root" class="flex items-center ml-4"></div>
                    <div class="md:hidden">
                        <button class="js-mobile-menu-btn text-white hover:text-gray-200 transition-colors p-2">
                            <i class="fas fa-bars text-xl"></i>
                        </button>
                    </div>
                </div>
                <div class="js-mobile-menu md:hidden hidden border-t border-white/20 pt-4 pb-4">
                    <div class="flex flex-col space-y-2">
                        <a href="/" data-key="home" data-permission-min="3" class="mobile-nav-link flex items-center px-4 py-3 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-home text-white text-lg mr-3"></i>
                            <span class="font-medium text-white">Menu Principal</span>
                        </a>
                        <a href="/adicionar" data-key="adicionar" data-permission-min="2" class="mobile-nav-link flex items-center px-4 py-3 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-plus text-white text-lg mr-3"></i>
                            <span class="font-medium text-white">Adicionar Itens</span>
                        </a>
                        <a href="/visualizar" data-key="visualizar" data-permission-min="3" class="mobile-nav-link flex items-center px-4 py-3 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-search text-white text-lg mr-3"></i>
                            <span class="font-medium text-white">Visualizar Itens</span>
                        </a>
                        <a href="/atualizacao-em-massa" data-key="atualizacao-em-massa" data-permission-min="2" class="mobile-nav-link flex items-center px-4 py-3 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-file-excel text-white text-lg mr-3"></i>
                            <span class="font-medium text-white">Atualização em massa</span>
                        </a>
                        <a href="/dashboard" data-key="dashboard" data-permission-min="2" class="mobile-nav-link flex items-center px-4 py-3 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-chart-line text-white text-lg mr-3"></i>
                            <span class="font-medium text-white">Dashboard</span>
                        </a>
                        <a href="/aprovar-usuarios" data-key="aprovar-usuarios" data-permission-min="1" class="mobile-nav-link flex items-center px-4 py-3 rounded-lg transition-all duration-300 hover:bg-white/20">
                            <i class="fas fa-user-check text-white text-lg mr-3"></i>
                            <span class="font-medium text-white">Aprovar usuários</span>
                        </a>
                    </div>
                </div>
            </div>
        </nav>`;
    }

    setupMobileMenuHandlers() {
        const btn = this.querySelector('.js-mobile-menu-btn');
        const menu = this.querySelector('.js-mobile-menu');
        if (!btn || !menu) return;

        btn.addEventListener('click', () => {
            if (menu.classList.contains('hidden')) {
                menu.classList.remove('hidden');
                menu.classList.add('mobile-menu-enter');
                btn.innerHTML = '<i class="fas fa-times text-xl"></i>';
            } else {
                menu.classList.add('mobile-menu-exit');
                setTimeout(() => {
                    menu.classList.add('hidden');
                    menu.classList.remove('mobile-menu-enter', 'mobile-menu-exit');
                    btn.innerHTML = '<i class="fas fa-bars text-xl"></i>';
                }, 300);
            }
        });

        document.addEventListener('click', (e) => {
            if (!this.contains(e.target) && !menu.classList.contains('hidden')) {
                menu.classList.add('mobile-menu-exit');
                setTimeout(() => {
                    menu.classList.add('hidden');
                    menu.classList.remove('mobile-menu-enter', 'mobile-menu-exit');
                    btn.innerHTML = '<i class="fas fa-bars text-xl"></i>';
                }, 300);
            }
        });
    }

    applyActive() {
        this.querySelectorAll('.nav-link, .mobile-nav-link').forEach(a => {
            a.classList.remove('active', 'current-page');
        });

        const targets = this.querySelectorAll(`[data-key="${this.active}"]`);
        targets.forEach(t => t.classList.add('active', 'current-page'));

        if (targets.length === 0) {
            this.active = 'home';
            this.querySelectorAll('[data-key="home"]').forEach(t => t.classList.add('active', 'current-page'));
        }
    }
}

customElements.define('nav-bar', NavBar);