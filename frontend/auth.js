/**
 * Controle de autenticação no frontend.
 * Depende de config.js (window.API_BASE_URL) estar carregado antes.
 */
(function() {
    const TOKEN_KEY = 'auth_token';
    const RETURN_URL_KEY = 'auth_return_url';

    function getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    function setToken(token) {
        if (token) localStorage.setItem(TOKEN_KEY, token);
        else localStorage.removeItem(TOKEN_KEY);
    }

    function clearToken() {
        localStorage.removeItem(TOKEN_KEY);
        window.currentUser = null;
    }

    function getAuthHeader() {
        const token = getToken();
        return token ? { 'Authorization': 'Bearer ' + token } : {};
    }

    /**
     * Chama GET /api/auth/me. Se 401, redireciona para /login e salva returnUrl.
     * Se sucesso, define window.currentUser e retorna o usuário.
     * @param {boolean} redirectIfUnauthorized - se true (padrão), redireciona para /login em 401
     * @returns {Promise<object|null>} usuário ou null se não autenticado (e redirectIfUnauthorized false)
     */
    async function checkAuth(redirectIfUnauthorized = true) {
        const token = getToken();
        if (!token) {
            if (redirectIfUnauthorized) {
                sessionStorage.setItem(RETURN_URL_KEY, window.location.pathname + window.location.search);
                window.location.href = '/login';
            }
            return null;
        }
        const base = window.API_BASE_URL || '/api';
        try {
            const res = await fetch(base + '/auth/me', { headers: getAuthHeader() });
            if (res.status === 401 || res.status === 403) {
                clearToken();
                if (redirectIfUnauthorized) {
                    sessionStorage.setItem(RETURN_URL_KEY, window.location.pathname + window.location.search);
                    window.location.href = '/login';
                }
                return null;
            }
            if (!res.ok) return null;
            const user = await res.json();
            window.currentUser = user;
            window.dispatchEvent(new CustomEvent('userReady', { detail: user }));
            return user;
        } catch (_) {
            if (redirectIfUnauthorized) {
                sessionStorage.setItem(RETURN_URL_KEY, window.location.pathname + window.location.search);
                window.location.href = '/login';
            }
            return null;
        }
    }

    function getReturnUrl() {
        const url = sessionStorage.getItem(RETURN_URL_KEY);
        sessionStorage.removeItem(RETURN_URL_KEY);
        return url || '/';
    }

    /** fetch que adiciona automaticamente o header Authorization para a API e redireciona em 401 */
    function fetchWithAuth(url, options) {
        const opts = options || {};
        const headers = Object.assign({}, opts.headers, getAuthHeader());
        return fetch(url, Object.assign({}, opts, { headers })).then(function(res) {
            if (res.status === 401) { clearToken(); sessionStorage.setItem('auth_return_url', window.location.pathname + window.location.search); window.location.href = '/login'; }
            return res;
        });
    }

    var _origFetch = window.fetch;
    window.fetch = function(url, opts) {
        var u = (typeof url === 'string') ? url : (url && url.url);
        var apiBase = window.API_BASE_URL || '';
        var options = opts;
        if (u && apiBase && u.indexOf(apiBase) === 0 && getToken()) {
            options = opts ? Object.assign({}, opts) : {};
            options.headers = Object.assign({}, options.headers || {}, getAuthHeader());
        }
        return _origFetch.call(this, url, options).then(function(res) {
            if (res.status === 401 && u && apiBase && u.indexOf(apiBase) === 0) {
                clearToken();
                sessionStorage.setItem('auth_return_url', window.location.pathname + window.location.search);
                window.location.href = '/login';
            }
            return res;
        });
    };

    window.auth = {
        getToken,
        setToken,
        clearToken,
        getAuthHeader,
        checkAuth,
        getReturnUrl,
        fetchWithAuth
    };
})();
