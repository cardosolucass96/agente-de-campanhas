# 🤖 Agente de Campanhas - Facebook Ads Assistant

Assistente inteligente via WhatsApp para gerenciamento de campanhas do Facebook Ads usando IA.

## 📋 Funcionalidades

- ✅ Consulta de desempenho de campanhas Facebook Ads
- ✅ Análise de métricas (CTR, CPC, gastos, resultados)
- ✅ Comparação entre períodos
- ✅ Histórico de otimizações
- ✅ Interface via WhatsApp (Evolution API ou WhatsApp Business API)
- ✅ Menus interativos com listas e botões
- ✅ Sistema de empilhamento de mensagens (debounce)
- ✅ Suporte a múltiplas contas de anúncio

## 🚀 Início Rápido

### Opção 1: Docker (Recomendado)

```bash
# 1. Clone o repositório
git clone <repo-url>
cd agente-de-campanhas

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Execute o script de inicialização
# Windows:
.\start-docker.ps1

# Linux/Mac:
chmod +x start-docker.sh
./start-docker.sh
```

**Acesse:**
- API: http://localhost:8000
- Health Check: http://localhost:8000/health
- Documentação: http://localhost:8000/docs

📖 **[Documentação completa do Docker](DOCKER.md)**

### Opção 2: Instalação Local

#### Pré-requisitos

- Python 3.11+
- pip
- Conta OpenAI com API key
- Token de acesso Facebook/Meta
- WhatsApp configurado (Evolution API ou WhatsApp Business API)

#### Instalação

```bash
# 1. Clone o repositório
git clone <repo-url>
cd agente-de-campanhas

# 2. Crie ambiente virtual
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 5. Execute a aplicação
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```env
# OpenAI
OPENAI_API_KEY=sk-proj-your-key

# Facebook/Meta
FACEBOOK_ACCESS_TOKEN=your-token
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-secret

# WhatsApp Business API (Meta Cloud)
WHATSAPP_PHONE_NUMBER_ID=your-phone-id
WHATSAPP_ACCESS_TOKEN=your-token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-verify-token

# Evolution API (alternativo)
EVOLUTION_API_URL=http://your-api-url
EVOLUTION_API_KEY=your-api-key
EVOLUTION_INSTANCE=your-instance

# Provider ativo
ACTIVE_WHATSAPP_PROVIDER=evolution  # ou 'whatsapp_business'
```

### Contas de Anúncio Padrão

As contas são configuradas em `default_accounts.py`:

```python
DEFAULT_AD_ACCOUNTS = {
    "611132268404060": {"name": "Vorp Scale", ...},
    "766769481380236": {"name": "Vorp Edu (MasterMind)", ...},
    # ... mais contas
}
```

**Aliases disponíveis:** scale, mastermind, eventos, tech, matchsales, cda

## 📱 Uso via WhatsApp

### Menu Inicial

Envie "oi" ou "olá" para receber menu interativo com opções:
- 📊 Desempenho de campanhas
- 📈 Comparações entre períodos
- 🔍 Histórico de otimizações
- 💰 Status e saldos das contas

### Comandos Exemplo

```
"Como está a Vorp Scale?"
"Desempenho das campanhas"
"Compare semana passada com esta semana"
"Histórico da conta Tech"
"Saldos de todas as contas"
"Gastos da última semana"
```

### Botões Interativos

O agente oferece botões clicáveis após apresentar dados:
- "📊 Ver CTR/CPC"
- "📈 Comparar"
- "🔍 Ver histórico"
- "📊 Outra conta"

## 🛠️ Arquitetura

### Stack Tecnológico

- **Backend:** FastAPI + Python 3.11
- **IA:** OpenAI GPT-4o-mini (gpt-4.1-mini) + LangChain + LangGraph
- **Database:** SQLite
- **WhatsApp:** Evolution API / WhatsApp Business API
- **Facebook:** Graph API v21.0
- **Deploy:** Docker + Docker Compose

### Estrutura de Arquivos

```
agente-de-campanhas/
├── main.py                    # FastAPI app + webhooks
├── agent.py                   # LangGraph agent
├── database.py                # SQLAlchemy models
├── models.py                  # Database schemas
├── default_accounts.py        # Configuração de contas
├── whatsapp_config.py         # Config WhatsApp providers
├── whatsapp_adapters.py       # Adapters para WhatsApp
├── tools/                     # Ferramentas do agente
│   ├── facebook_*.py          # Ferramentas Facebook Ads
│   └── whatsapp_*.py          # Ferramentas WhatsApp
├── Dockerfile                 # Docker image
├── docker-compose.yml         # Orquestração
├── requirements.txt           # Dependências Python
└── data/                      # Banco de dados SQLite
```

### Fluxo de Mensagens

```
WhatsApp → Webhook → Debounce (6s) → Agent → Tools → Response → WhatsApp
                         ↓
                   Stack messages
                   (combinar múltiplas)
```

## 💰 Custos Estimados

Para 10 mensagens de conversa:

| Cenário | Custo por Conversa | Custo/Mês (100 conv/dia) |
|---------|-------------------|--------------------------|
| Simples | R$ 0,029 | R$ 85,51 |
| Moderado | R$ 0,043 | R$ 129,98 |
| Intensivo | R$ 0,058 | R$ 173,76 |

📊 **[Calculadora de custos](calculate_token_cost.py)**

```bash
python calculate_token_cost.py 10
```

## 🧪 Testes

```bash
# Testar listas interativas
python test_agent_lists.py

# Testar detecção de botões
python test_button_detection.py

# Testar API Facebook
python test_fb_api.py

# Verificar todas as ferramentas
python -c "from tools import AGENT_TOOLS; print(f'Total: {len(AGENT_TOOLS)} ferramentas')"
```

## 📊 Endpoints da API

### Health Check
```bash
GET /health
```

### Webhooks
```bash
# Evolution API
POST /evo

# WhatsApp Business API
GET /webhook/whatsapp  # Verificação
POST /webhook/whatsapp # Eventos
```

### Contas Facebook
```bash
GET /facebook/accounts  # Lista contas padrão
```

### Envio Manual
```bash
POST /send
{
  "phone": "5511999999999",
  "message": "Olá!",
  "conversation_id": 1  # opcional
}
```

## 🐳 Docker - Comandos Úteis

```bash
# Build e start
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Restart
docker-compose restart

# Parar
docker-compose stop

# Remover tudo
docker-compose down -v

# Entrar no container
docker-compose exec agente-campanhas /bin/bash

# Backup do banco
docker-compose exec agente-campanhas cp /app/data/agente_campanhas.db /app/data/backup.db
```

## 🔐 Segurança

- ✅ Validação de signature nos webhooks WhatsApp Business
- ✅ Variáveis de ambiente para credenciais
- ✅ .env não versionado (.gitignore)
- ✅ Logs não expõem dados sensíveis
- ✅ Health checks para monitoramento

## 📈 Monitoramento

### Logs
```bash
# Docker
docker-compose logs -f agente-campanhas

# Local
tail -f logs/app.log  # se configurado
```

### Health Check
```bash
curl http://localhost:8000/health

# Resposta esperada:
{"status": "ok"}
```

## 🚀 Deploy em Produção

1. **Configure servidor** (VPS/Cloud)
2. **Instale Docker**
3. **Clone repositório**
4. **Configure .env** com credenciais de produção
5. **Execute:** `docker-compose up -d --build`
6. **Configure Nginx** como reverse proxy
7. **Configure SSL** (Let's Encrypt)
8. **Configure webhook** do WhatsApp/Facebook

📖 **[Guia completo de deploy](DOCKER.md#-deploy-em-produção)**

## 🤝 Contribuindo

1. Fork o projeto
2. Crie branch para feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para branch (`git push origin feature/nova-funcionalidade`)
5. Abra Pull Request

## 📝 Licença

Este projeto está sob licença MIT.

## 📞 Suporte

- **Documentação:** [DOCKER.md](DOCKER.md)
- **Issues:** Abra uma issue no GitHub
- **Email:** seu-email@exemplo.com

---

Desenvolvido com ❤️ usando FastAPI, LangChain e OpenAI
#   T e s t   d e p l o y  
 #   T e s t   d e p l o y  
 