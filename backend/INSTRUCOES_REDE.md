# 🌐 **Configurando Acesso em Rede Local**

## 📋 **O que este guia faz:**
Permite que outros dispositivos na mesma rede Wi-Fi/LAN acessem sua aplicação Gerenciador de Peças.

## 🚀 **Métodos de Execução:**

### **Método 1: Arquivo Batch (Mais Fácil - Windows)**
1. **Clique duas vezes** no arquivo `executar_rede.bat`
2. O servidor iniciará automaticamente
3. Siga as instruções na tela

### **Método 2: Comando Python Direto**
```bash
# Navegue para a pasta backend
cd backend

# Execute o script de rede
python run_network.py --reload
```

### **Método 3: Uvicorn Direto**
```bash
# Navegue para a pasta backend
cd backend

# Execute com uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 **Configurações Importantes:**

### **1. Arquivo .env**
Certifique-se de que existe um arquivo `.env` na pasta `backend` com:
```env
SUPABASE_URL=sua_url_do_supabase
SUPABASE_KEY=sua_chave_do_supabase
```

### **2. Firewall do Windows**
- **Windows Defender**: Permitir conexões na porta 8000
- **Firewall do Windows**: Criar regra para permitir Python/uvicorn

### **3. Rede Wi-Fi**
- Todos os dispositivos devem estar na **mesma rede Wi-Fi**
- **Não funciona** entre redes diferentes

## 📱 **Como Acessar:**

### **Do seu computador (local):**
```
http://localhost:8000
```

### **De outros dispositivos na mesma rede:**
```
http://SEU_IP_LOCAL:8000
```
**Exemplo:** `http://192.168.1.100:8000`

## 🔍 **Descobrir seu IP Local:**

### **Windows:**
```cmd
ipconfig
```
Procure por "IPv4 Address" na sua rede Wi-Fi.

### **Ou use o script:**
O script `run_network.py` mostra automaticamente seu IP local.

## ⚠️ **Segurança e Limitações:**

### **✅ O que funciona:**
- Acesso de dispositivos na **mesma rede Wi-Fi**
- Acesso de dispositivos na **mesma rede LAN** (cabo)
- Acesso de **celulares, tablets, outros PCs** na mesma rede

### **❌ O que NÃO funciona:**
- Acesso da **internet externa**
- Acesso de **redes Wi-Fi diferentes**
- Acesso de **outras localizações**

### **🔒 Segurança:**
- **Apenas use em redes confiáveis** (casa, trabalho)
- **Não exponha na internet** sem configurações de segurança
- **Desligue o servidor** quando não estiver usando

## 🚨 **Solução de Problemas:**

### **Erro: "Porta já em uso"**
```bash
# Encerre processos na porta 8000
netstat -ano | findstr :8000
taskkill /PID NUMERO_DO_PROCESSO /F
```

### **Erro: "Firewall bloqueando"**
1. Abra "Firewall do Windows Defender"
2. Clique em "Permitir um aplicativo"
3. Adicione Python/uvicorn
4. Marque "Privado" e "Público"

### **Erro: "Conexão recusada"**
1. Verifique se o servidor está rodando
2. Verifique se o IP está correto
3. Verifique se estão na mesma rede

### **Erro: "Arquivo .env não encontrado"**
1. Crie o arquivo `.env` na pasta `backend`
2. Adicione suas credenciais do Supabase
3. Reinicie o servidor

## 📞 **Suporte:**
Se encontrar problemas:
1. Verifique se todas as dependências estão instaladas
2. Verifique se o arquivo `.env` está configurado
3. Verifique se o firewall permite conexões
4. Verifique se estão na mesma rede Wi-Fi

## 🎯 **Resumo Rápido:**
1. **Configure o arquivo `.env`**
2. **Execute `executar_rede.bat`** (Windows)
3. **Copie o IP mostrado na tela**
4. **Acesse de outros dispositivos** usando `http://IP:8000`
5. **Para parar**: Ctrl+C no terminal

---
**🎉 Agora sua aplicação pode ser acessada por qualquer dispositivo na mesma rede!**
