// Configuração da API
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Elementos do DOM
const elements = {
    checkStatusBtn: document.getElementById('checkStatusBtn'),
    refreshStatsBtn: document.getElementById('refreshStatsBtn'),
    uploadForm: document.getElementById('uploadForm'),
    searchBtn: document.getElementById('searchBtn'),
    clearBtn: document.getElementById('clearBtn'),
    apiStatus: document.getElementById('apiStatus'),
    totalPecas: document.getElementById('totalPecas'),
    tabelaNome: document.getElementById('tabelaNome'),
    uploadMessage: document.getElementById('uploadMessage'),
    searchResults: document.getElementById('searchResults'),
    resultsContainer: document.getElementById('resultsContainer'),
    resultsTable: document.getElementById('resultsTable')
};

// Estado da aplicação
let appState = {
    apiConnected: false,
    stats: null
};

// Inicialização da aplicação
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

// Configuração dos event listeners
function setupEventListeners() {
    elements.checkStatusBtn.addEventListener('click', checkApiStatus);
    elements.refreshStatsBtn.addEventListener('click', refreshStats);
    elements.uploadForm.addEventListener('submit', handleFileUpload);
    elements.searchBtn.addEventListener('click', handleSearch);
    elements.clearBtn.addEventListener('click', clearForms);
}

// Inicialização da aplicação
async function initializeApp() {
    showLoadingState();
    await checkApiStatus();
    await refreshStats();
    hideLoadingState();
}

// Verificar status da API
async function checkApiStatus() {
    try {
        elements.checkStatusBtn.innerHTML = '<span class="inline-block w-5 h-5 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin"></span> Verificando...';
        elements.checkStatusBtn.disabled = true;
        
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateApiStatus(true, 'API funcionando e conectada ao Supabase');
            appState.apiConnected = true;
        } else {
            updateApiStatus(false, data.message);
            appState.apiConnected = false;
        }
    } catch (error) {
        updateApiStatus(false, 'Erro ao conectar com a API');
        appState.apiConnected = false;
        console.error('Erro ao verificar status da API:', error);
    } finally {
        elements.checkStatusBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Verificar';
        elements.checkStatusBtn.disabled = false;
    }
}

// Atualizar estatísticas
async function refreshStats() {
    try {
        elements.refreshStatsBtn.innerHTML = '<span class="inline-block w-5 h-5 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin"></span> Atualizando...';
        elements.refreshStatsBtn.disabled = true;
        
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        
        if (data.status === 'success') {
            updateStats(data);
            appState.stats = data;
        } else {
            throw new Error(data.detail || 'Erro ao obter estatísticas');
        }
    } catch (error) {
        showMessage('Erro ao carregar estatísticas: ' + error.message, 'error');
        console.error('Erro ao atualizar estatísticas:', error);
    } finally {
        elements.refreshStatsBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar';
        elements.refreshStatsBtn.disabled = false;
    }
}

// Upload de arquivo
async function handleFileUpload(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showMessage('Por favor, selecione um arquivo Excel.', 'error');
        return;
    }
    
    if (!file.name.endsWith('.xlsx')) {
        showMessage('Apenas arquivos .xlsx são aceitos.', 'error');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        showMessage('Enviando arquivo...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/upload-excel`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showMessage(result.message, 'success');
            fileInput.value = '';
            
            // Atualizar estatísticas após upload
            setTimeout(() => refreshStats(), 1000);
        } else {
            showMessage(result.detail || 'Erro ao processar o arquivo.', 'error');
        }
    } catch (error) {
        showMessage('Erro de conexão com o servidor.', 'error');
        console.error('Erro no upload:', error);
    }
}

// Busca de peças
async function handleSearch() {
    const codigo = document.getElementById('codigoSearch').value.trim();
    const nome = document.getElementById('nomeSearch').value.trim();
    const categoria = document.getElementById('categoriaSearch').value.trim();
    
    if (!codigo && !nome && !categoria) {
        showMessage('Por favor, preencha pelo menos um campo de busca.', 'error');
        return;
    }
    
    try {
        elements.searchBtn.innerHTML = '<span class="inline-block w-5 h-5 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin"></span> Buscando...';
        elements.searchBtn.disabled = true;
        
        const params = new URLSearchParams();
        if (codigo) params.append('codigo', codigo);
        if (nome) params.append('nome', nome);
        if (categoria) params.append('categoria', categoria);
        
        const response = await fetch(`${API_BASE_URL}/pecas?${params.toString()}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displaySearchResults(data.pecas);
        } else {
            throw new Error(data.detail || 'Erro na busca');
        }
    } catch (error) {
        showMessage('Erro ao realizar busca: ' + error.message, 'error');
        console.error('Erro na busca:', error);
    } finally {
        elements.searchBtn.innerHTML = '<i class="fas fa-search"></i> Buscar';
        elements.searchBtn.disabled = false;
    }
}

// Exibir resultados da busca
function displaySearchResults(pecas) {
    if (!pecas || pecas.length === 0) {
        elements.searchResults.innerHTML = `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                <p class="text-blue-800 font-medium">Nenhuma peça encontrada com os critérios especificados.</p>
            </div>
        `;
        elements.resultsContainer.style.display = 'none';
        return;
    }
    
    // Criar cabeçalho da tabela baseado nas colunas disponíveis
    const columns = Object.keys(pecas[0]);
    
    let tableHTML = `
        <div class="overflow-x-auto">
            <table class="w-full border-collapse bg-white rounded-xl overflow-hidden shadow-lg">
                <thead>
                    <tr>
    `;
    
    columns.forEach(column => {
        tableHTML += `<th class="bg-primary-500 text-white px-4 py-4 text-left font-semibold">${formatColumnName(column)}</th>`;
    });
    
    tableHTML += '</tr></thead><tbody>';
    
    // Adicionar linhas de dados
    pecas.forEach((peca, index) => {
        const rowClass = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';
        tableHTML += `<tr class="${rowClass} hover:bg-blue-50 transition-colors">`;
        
        columns.forEach(column => {
            const value = peca[column];
            tableHTML += `<td class="px-4 py-4 border-b border-gray-100">${value !== null && value !== undefined ? value : '-'}</td>`;
        });
        
        tableHTML += '</tr>';
    });
    
    tableHTML += '</tbody></table></div>';
    
    elements.resultsTable.innerHTML = tableHTML;
    elements.resultsContainer.style.display = 'block';
    
    // Mostrar mensagem de sucesso
    elements.searchResults.innerHTML = `
        <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
            <p class="text-green-800 font-medium">${pecas.length} peça(s) encontrada(s).</p>
        </div>
    `;
}

// Formatar nome da coluna para exibição
function formatColumnName(columnName) {
    return columnName
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .trim();
}

// Atualizar status da API na interface
function updateApiStatus(isOnline, message) {
    const statusIndicator = elements.apiStatus.querySelector('span:first-child');
    const statusText = elements.apiStatus.querySelector('span:last-child');
    
    if (isOnline) {
        statusIndicator.className = 'w-3 h-3 rounded-full inline-block bg-green-500 shadow-lg shadow-green-500/50';
        statusText.textContent = message;
        statusText.className = 'text-green-600 font-medium';
    } else {
        statusIndicator.className = 'w-3 h-3 rounded-full inline-block bg-red-500 shadow-lg shadow-red-500/50';
        statusText.textContent = message;
        statusText.className = 'text-red-600 font-medium';
    }
}

// Atualizar estatísticas na interface
function updateStats(data) {
    elements.totalPecas.textContent = data.total_pecas.toLocaleString('pt-BR');
    elements.tabelaNome.textContent = data.tabela;
}

// Mostrar mensagens para o usuário
function showMessage(message, type = 'info') {
    const messageElement = elements.uploadMessage;
    
    // Remover classes anteriores
    messageElement.className = 'mt-4 p-4 rounded-lg font-medium text-center';
    
    // Adicionar classes baseadas no tipo
    if (type === 'success') {
        messageElement.classList.add('bg-green-100', 'text-green-800', 'border', 'border-green-200');
    } else if (type === 'error') {
        messageElement.classList.add('bg-red-100', 'text-red-800', 'border', 'border-red-200');
    } else {
        messageElement.classList.add('bg-blue-100', 'text-blue-800', 'border', 'border-blue-200');
    }
    
    messageElement.textContent = message;
    
    // Limpar mensagem após 5 segundos
    setTimeout(() => {
        messageElement.className = 'mt-4';
        messageElement.textContent = '';
    }, 5000);
}

// Mostrar estado de carregamento
function showLoadingState() {
    // Implementar se necessário
}

// Esconder estado de carregamento
function hideLoadingState() {
    // Implementar se necessário
}

// Função utilitária para fazer requisições HTTP
async function makeRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Erro na requisição:', error);
        throw error;
    }
}

// Função para limpar formulários
function clearForms() {
    document.getElementById('codigoSearch').value = '';
    document.getElementById('nomeSearch').value = '';
    document.getElementById('categoriaSearch').value = '';
    document.getElementById('fileInput').value = '';
    
    // Limpar resultados
    elements.searchResults.innerHTML = '';
    elements.resultsContainer.style.display = 'none';
}

// Função para exportar resultados (futura implementação)
function exportResults(data, format = 'csv') {
    // Implementar exportação de dados
    console.log('Exportando dados:', data, 'Formato:', format);
}

// Função para paginação (futura implementação)
function setupPagination(totalItems, itemsPerPage = 20) {
    // Implementar paginação
    console.log('Configurando paginação:', totalItems, 'itens por página:', itemsPerPage);
}

// Event listener para mudanças no arquivo selecionado
document.getElementById('fileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const fileLabel = document.querySelector('label[for="fileInput"] span');
        fileLabel.textContent = `Arquivo selecionado: ${file.name}`;
        fileLabel.className = 'text-lg text-green-600 font-medium';
    }
});

// Função para testar conexão com a API
function testApiConnection() {
    return new Promise((resolve) => {
        const startTime = Date.now();
        fetch(`${API_BASE_URL}/health`)
            .then(response => {
                const endTime = Date.now();
                const latency = endTime - startTime;
                resolve({
                    connected: response.ok,
                    latency: latency,
                    status: response.status
                });
            })
            .catch(() => {
                resolve({
                    connected: false,
                    latency: null,
                    status: 'error'
                });
            });
    });
}

// Função para mostrar informações de debug
function showDebugInfo() {
    console.log('Estado da aplicação:', appState);
    console.log('URL da API:', API_BASE_URL);
    console.log('Elementos DOM:', elements);
}

// Adicionar funcionalidade de tecla Enter nos campos de busca
document.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        if (event.target.id === 'codigoSearch' || 
            event.target.id === 'nomeSearch' || 
            event.target.id === 'categoriaSearch') {
            handleSearch();
        }
    }
});
