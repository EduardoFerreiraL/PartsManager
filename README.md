# Gerenciador de Pecas

Sistema web para gerenciamento de pecas com FastAPI + Supabase, incluindo:
- autenticacao de usuarios com aprovacao por niveis;
- cadastro e consulta de pecas;
- upload de planilhas Excel;
- atualizacao em massa por planilha;
- dashboard com analises por periodo e comparativos.

## Visao Geral

O projeto serve frontend e backend na mesma aplicacao FastAPI:
- paginas HTML em `frontend/`;
- API em `backend/` sob prefixo `/api`;
- assets estaticos (JS, imagens e componentes) entregues por rotas dedicadas.

## Tecnologias

### Backend
- FastAPI
- Uvicorn
- Supabase Python SDK
- Psycopg2 (conexao direta opcional com PostgreSQL)
- Pandas + OpenPyXL (planilhas)
- PyJWT + bcrypt (autenticacao)

### Frontend
- HTML + JavaScript
- Tailwind CSS via CDN
- Font Awesome
- Chart.js (dashboard)

## Estrutura do Projeto

```text
gerenciador-de-pecas/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── auth/
│   ├── config/
│   ├── database/
│   ├── routes/
│   ├── services/
│   └── scripts/
├── frontend/
│   ├── index.html
│   ├── adicionar.html
│   ├── visualizar.html
│   ├── atualizacao-em-massa.html
│   ├── dashboard.html
│   ├── login.html
│   ├── novo-usuario.html
│   ├── aprovar-usuarios.html
│   ├── auth.js
│   ├── config.js
│   ├── user-menu.js
│   └── script.js
└── README.md
```

## Configuracao

Crie `backend/.env` com:

```env
SUPABASE_URL="https://SEU-PROJETO.supabase.co"
SUPABASE_KEY="SUA_CHAVE_SERVICE_ROLE"

# Opcional: habilita consultas SQL diretas (melhor performance em alguns endpoints)
DIRECT_URL="postgresql://usuario:senha@host:5432/db"

# JWT
SECRET_KEY="troque-esta-chave-em-producao"
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Opcional: criar admin inicial via script
ADMIN_EMAIL="admin@empresa.com"
ADMIN_PASSWORD="senha-forte-aqui"
```

## Como Executar

1. Instale dependencias do backend:

```bash
cd backend
pip install -r requirements.txt
```

2. Inicie a aplicacao:

```bash
uvicorn main:app --reload
```

3. Acesse:
- App: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Importante: rode o comando a partir da pasta `backend/` para os caminhos relativos de paginas funcionarem corretamente.

## Autenticacao e Niveis de Acesso

Autenticacao JWT com rotas em `/api/auth`.

Perfis:
- `nivel 0`: administrador maximo;
- `nivel 1`: administrador;
- `nivel 2`: operador;
- `nivel 3`: consulta.

A visibilidade de menus no frontend usa `data-permission-min`, seguindo a regra de que valores menores tem mais privilegio.

## Paginas da Aplicacao

- `/` - Menu principal
- `/adicionar` - Upload de planilha para inclusao
- `/visualizar` - Busca, filtros e manutencao de pecas
- `/atualizacao-em-massa` - Fluxo de exportar/editar/importar planilha
- `/dashboard` - Graficos e comparativos
- `/login` - Login
- `/novo-usuario` - Cadastro de novo usuario
- `/aprovar-usuarios` - Gestao de usuarios (aprovacao e niveis)

## Principais Endpoints da API

### Auth (`/api/auth`)
- `POST /login`
- `POST /registro`
- `GET /me`
- `GET /pendentes`
- `PATCH /aprovar/{user_id}`
- `GET /usuarios`
- `PATCH /usuarios/{user_id}/nivel`
- `DELETE /usuarios/{user_id}`
- `PATCH /usuarios/{user_id}/senha`

### Pecas (`/api`)
- `GET /pecas`
- `GET /pecas/count`
- `GET /pecas/all`
- `POST /pecas/by-part-numbers`
- `POST /pecas`
- `PUT /pecas/part_number/{part_number}`
- `DELETE /pecas/part_number/{part_number}`

### Upload e Atualizacao
- `POST /upload-excel`
- `POST /analyze-excel`
- `POST /export-pecas-for-update`
- `GET /export-pecas-all/latest`
- `GET /export-pecas-all/download`
- `POST /export-pecas-all/generate`
- `POST /upload-excel-update`

### Dashboard
- `GET /dashboard/cadastrados`
- `GET /dashboard/modificados`
- `GET /dashboard/origin`
- `GET /dashboard/situation-osgt`

### Sistema/Admin
- `GET /health`
- `GET /stats`
- `GET /direct-connection`
- `GET /direct-query`
- `GET /table-structure`
- `GET /test-model-compatibility`
- `GET /download-model`
- `GET /check-table`
- `POST /optimize-database`
- `GET /database-performance`
- `GET /debug-structure`
- `POST /reload-schema-cache`
- `POST /migrate-position-field`

## Scripts Uteis

Criar admin inicial (nivel 0):

```bash
cd backend
python -m scripts.create_admin
```

## Notas de Operacao

- `frontend/config.js` detecta hostname/porta para montar `window.API_BASE_URL`.
- CORS esta aberto para facilitar desenvolvimento. Em producao, restrinja origens.
- Se `DIRECT_URL` nao estiver configurada ou falhar, partes do sistema usam fallback via Supabase.

## Solucao de Problemas

- Erro de autenticacao: confirme `SECRET_KEY`, token no navegador e permissao do usuario.
- Falha ao iniciar backend: valide `SUPABASE_URL` e `SUPABASE_KEY` no `.env`.
- Dashboard lento/inconsistente: configure `DIRECT_URL` para consultas SQL diretas.
- Problemas com planilha: valide formato `.xlsx` e colunas esperadas pelo backend.

## Quickstart Producao

### 1) Ambiente e segredos
- Gere uma `SECRET_KEY` forte e unica para producao.
- Defina `SUPABASE_URL`, `SUPABASE_KEY` e (opcionalmente) `DIRECT_URL` no ambiente do servidor.
- Nao versionar `.env` com credenciais reais.

Exemplo de `.env` de producao:

```env
SUPABASE_URL="https://SEU-PROJETO.supabase.co"
SUPABASE_KEY="SUA_CHAVE_SERVICE_ROLE"
DIRECT_URL="postgresql://usuario:senha@host:5432/db"
SECRET_KEY="uma-chave-grande-aleatoria-e-secreta"
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### 2) Dependencias e execucao do app

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Para operacao continua, rode com um gerenciador de processo (ex.: systemd, supervisor, container orchestration).

### 3) Proxy reverso e HTTPS
- Publique o FastAPI atras de Nginx/Traefik/Caddy.
- Termine TLS (HTTPS) no proxy reverso.
- Encaminhe trafego externo para `127.0.0.1:8000`.
- Aplique limites de tamanho/upload e timeout no proxy conforme necessidade das planilhas.

### 4) CORS e superficie de ataque
- Hoje o backend aceita `allow_origins=["*"]` (adequado para dev, nao ideal para prod).
- Em producao, restrinja para os dominios reais do frontend.
- Exponha somente portas necessarias (80/443 publicas; 8000 privada/interna).

### 5) Checklist rapido
- [ ] `SECRET_KEY` forte em producao
- [ ] CORS restrito ao(s) dominio(s) oficial(is)
- [ ] HTTPS ativo no dominio
- [ ] Logs e monitoramento habilitados
- [ ] Backup e politica de rotacao de credenciais

## Licenca

Defina a licenca do projeto conforme a politica do repositorio (arquivo `LICENSE`, se aplicavel).
