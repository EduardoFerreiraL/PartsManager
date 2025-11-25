// Configuração automática da API baseada no hostname atual
// Detecta automaticamente se está rodando localmente ou em rede

(function() {
    // Obtém o hostname atual (pode ser localhost, 127.0.0.1, ou IP da rede)
    const hostname = window.location.hostname;
    const port = window.location.port || '8000';
    
    // Se estiver acessando via localhost ou 127.0.0.1, usa localhost
    // Caso contrário, usa o hostname atual (que será o IP da rede)
    let apiHost;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        apiHost = 'http://127.0.0.1:8000';
    } else {
        // Usa o mesmo hostname e porta da página atual
        apiHost = `http://${hostname}:${port}`;
    }
    
    // Define a URL base da API
    window.API_BASE_URL = `${apiHost}/api`;
    
    // Log para debug (pode ser removido em produção)
    console.log('🌐 Configuração da API:', {
        hostname: hostname,
        port: port,
        apiBaseUrl: window.API_BASE_URL
    });
})();


