/**
 * Painel de usuário lateral (drawer esquerdo) com informações e logout.
 * Escuta o evento 'userReady' disparado por auth.checkAuth.
 */
(function() {
    const NIVEL_LABELS = {
        0: 'Administrador',
        1: 'Gerente',
        2: 'Operador',
        3: 'Visualizador'
    };

    function getNivelLabel(nivel) {
        return NIVEL_LABELS[nivel] != null ? NIVEL_LABELS[nivel] : 'Usuário';
    }

    function getInicial(nome) {
        if (!nome || typeof nome !== 'string') return '?';
        const parts = nome.trim().split(/\s+/);
        if (parts.length >= 2) {
            return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        }
        return nome[0].toUpperCase();
    }

    function createPanel() {
        const overlay = document.createElement('div');
        overlay.id = 'user-panel-overlay';
        overlay.className = 'fixed inset-0 bg-black/40 z-[9998] hidden transition-opacity';
        overlay.setAttribute('aria-hidden', 'true');

        const panel = document.createElement('div');
        panel.id = 'user-panel';
        panel.className = 'fixed left-0 top-0 h-full w-[280px] max-w-[85vw] bg-white/95 backdrop-blur-md shadow-xl z-[9999] transform -translate-x-full transition-transform duration-300 ease-out flex flex-col';
        panel.setAttribute('aria-hidden', 'true');

        panel.innerHTML = `
            <div class="relative p-6 border-b border-gray-200">
                <button type="button" id="user-panel-close" class="absolute top-4 right-4 text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-colors" aria-label="Fechar">
                    <i class="fas fa-times text-lg"></i>
                </button>
                <div id="user-panel-avatar" class="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold mb-4"></div>
                <h3 id="user-panel-nome" class="text-lg font-semibold text-gray-800"></h3>
                <p id="user-panel-email" class="text-sm text-gray-600 truncate"></p>
                <span id="user-panel-nivel" class="inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium bg-primary-50 text-primary-600"></span>
            </div>
            <div class="flex-1 p-4">
                <button type="button" id="user-panel-logout" class="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 font-medium transition-colors">
                    <i class="fas fa-sign-out-alt"></i> Sair
                </button>
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(panel);

        return { overlay, panel };
    }

    function openPanel(user) {
        const overlay = document.getElementById('user-panel-overlay');
        const panel = document.getElementById('user-panel');
        if (!overlay || !panel) return;

        document.getElementById('user-panel-avatar').textContent = getInicial(user.nome);
        document.getElementById('user-panel-nome').textContent = user.nome || '';
        document.getElementById('user-panel-email').textContent = user.email || '';
        document.getElementById('user-panel-nivel').textContent = getNivelLabel(user.nivelPermissao);

        overlay.classList.remove('hidden');
        panel.classList.remove('-translate-x-full');
        overlay.setAttribute('aria-hidden', 'false');
        panel.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    function closePanel() {
        const overlay = document.getElementById('user-panel-overlay');
        const panel = document.getElementById('user-panel');
        if (!overlay || !panel) return;

        overlay.classList.add('hidden');
        panel.classList.add('-translate-x-full');
        overlay.setAttribute('aria-hidden', 'true');
        panel.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    function logout() {
        if (window.auth && typeof window.auth.clearToken === 'function') {
            window.auth.clearToken();
        }
        sessionStorage.removeItem('auth_return_url');
        window.location.href = '/login';
    }

    function setupPanelListeners() {
        const overlay = document.getElementById('user-panel-overlay');
        const panel = document.getElementById('user-panel');
        const closeBtn = document.getElementById('user-panel-close');
        const logoutBtn = document.getElementById('user-panel-logout');

        function handleClose() {
            closePanel();
        }

        if (overlay) overlay.addEventListener('click', handleClose);
        if (closeBtn) closeBtn.addEventListener('click', handleClose);
        if (panel) panel.addEventListener('click', function(e) { e.stopPropagation(); });
        if (logoutBtn) logoutBtn.addEventListener('click', logout);

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const panelEl = document.getElementById('user-panel');
                if (panelEl && !panelEl.classList.contains('-translate-x-full')) {
                    closePanel();
                }
            }
        });
    }

    function renderTrigger(user) {
        const root = document.getElementById('user-menu-root');
        if (!root) return;

        const inicial = getInicial(user.nome);
        root.innerHTML = `
            <button type="button" id="user-menu-trigger" class="flex items-center gap-2 px-3 py-2 rounded-lg text-white hover:bg-white/20 transition-colors" aria-label="Abrir menu do usuário">
                <span class="w-8 h-8 rounded-full bg-white/30 flex items-center justify-center text-sm font-semibold">${inicial}</span>
                <span class="hidden sm:inline font-medium max-w-[120px] truncate">${(user.nome || '').trim() || 'Usuário'}</span>
                <i class="fas fa-chevron-down text-xs opacity-75 hidden sm:inline"></i>
            </button>
        `;

        root.querySelector('#user-menu-trigger').addEventListener('click', function() {
            openPanel(user);
        });
    }

    function init(user) {
        if (!user) return;
        if (!document.getElementById('user-panel')) {
            createPanel();
            setupPanelListeners();
        }
        renderTrigger(user);
    }

    window.addEventListener('userReady', function(e) {
        init(e.detail || window.currentUser);
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            if (window.currentUser) init(window.currentUser);
        });
    } else if (window.currentUser) {
        init(window.currentUser);
    }
})();
