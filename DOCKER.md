# Docker Setup - Agente de Campanhas

Este documento explica como executar a aplicação usando Docker.

## 🐳 Pré-requisitos

- Docker instalado ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose instalado (geralmente incluído com Docker Desktop)

## 🚀 Quick Start

### 1. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e preencha as variáveis:

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:
- `OPENAI_API_KEY`
- `FACEBOOK_ACCESS_TOKEN`
- Configurações do WhatsApp (Evolution ou WhatsApp Business)

### 2. Build e Start

```bash
# Build da imagem e start dos containers
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Verificar status
docker-compose ps
```

### 3. Acessar a aplicação

A aplicação estará disponível em:
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Docs**: http://localhost:8000/docs

## 📦 Comandos Úteis

### Gerenciamento de Containers

```bash
# Iniciar containers
docker-compose up -d

# Parar containers
docker-compose stop

# Parar e remover containers
docker-compose down

# Parar e remover tudo (incluindo volumes)
docker-compose down -v

# Rebuild completo
docker-compose up -d --build --force-recreate
```

### Logs e Debug

```bash
# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f agente-campanhas

# Ver últimas 100 linhas
docker-compose logs --tail=100

# Entrar no container
docker-compose exec agente-campanhas /bin/bash
```

### Banco de Dados

```bash
# Backup do banco de dados
docker-compose exec agente-campanhas cp /app/data/agente_campanhas.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db

# Acessar banco de dados SQLite
docker-compose exec agente-campanhas sqlite3 /app/data/agente_campanhas.db
```

## 🔧 Desenvolvimento com Docker

### Modo desenvolvimento com hot-reload

Edite `docker-compose.yml` e adicione volumes para código:

```yaml
volumes:
  - ./data:/app/data
  - .:/app  # Mapear código fonte
```

E modifique o comando para usar `--reload`:

```yaml
command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Executar comandos no container

```bash
# Python shell
docker-compose exec agente-campanhas python

# Executar script
docker-compose exec agente-campanhas python calculate_token_cost.py 10

# Executar testes
docker-compose exec agente-campanhas python -m pytest
```

## 🌐 Deploy em Produção

### 1. Variáveis de Ambiente

Configure todas as variáveis necessárias no servidor:

```bash
# Criar .env no servidor
nano .env
```

### 2. Build e Deploy

```bash
# Pull do código
git pull origin main

# Build e start
docker-compose up -d --build

# Verificar health
curl http://localhost:8000/health
```

### 3. Configurar Reverse Proxy (Nginx)

Exemplo de configuração Nginx:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (se necessário)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4. HTTPS com Let's Encrypt

```bash
# Instalar certbot
sudo apt-get install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com
```

## 🔐 Segurança

### Práticas Recomendadas

1. **Nunca commitar .env** - Já está no `.gitignore`
2. **Usar secrets** em produção (Docker Swarm/Kubernetes)
3. **Limitar recursos**:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

4. **Configurar firewall** - Apenas portas necessárias abertas
5. **Monitoramento** - Logs e health checks ativos

## 📊 Monitoramento

### Health Check

O container inclui health check automático:

```bash
# Ver status do health check
docker inspect --format='{{json .State.Health}}' agente-campanhas | jq
```

### Logs estruturados

Configurar logging driver no `docker-compose.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs de erro
docker-compose logs agente-campanhas

# Verificar configuração
docker-compose config

# Rebuild do zero
docker-compose down -v
docker-compose up -d --build
```

### Problemas de permissão

```bash
# Ajustar permissões da pasta data
chmod -R 755 ./data
```

### Banco de dados corrompido

```bash
# Remover e recriar
docker-compose down -v
rm -rf ./data/*.db
docker-compose up -d
```

### Problemas de rede

```bash
# Recriar rede
docker network prune
docker-compose up -d
```

## 📝 Estrutura de Arquivos

```
agente-de-campanhas/
├── Dockerfile              # Definição da imagem Docker
├── docker-compose.yml      # Orquestração dos containers
├── .dockerignore          # Arquivos ignorados no build
├── .env                   # Variáveis de ambiente (não versionado)
├── requirements.txt       # Dependências Python
├── main.py               # Aplicação FastAPI
├── agent.py              # Lógica do agente
├── data/                 # Banco de dados SQLite (volume)
│   └── agente_campanhas.db
└── tools/                # Ferramentas do agente
```

## 🔄 Atualizações

```bash
# Atualizar código e rebuild
git pull origin main
docker-compose up -d --build

# Backup antes de atualizar
docker-compose exec agente-campanhas cp /app/data/agente_campanhas.db /app/data/backup_before_update.db
```

## 💡 Dicas

1. **Desenvolvimento local**: Use `docker-compose` com volumes mapeados
2. **Produção**: Configure CI/CD para deploy automático
3. **Backup**: Automatize backup do volume `/app/data`
4. **Logs**: Configure rotação de logs para evitar disco cheio
5. **Monitoring**: Integre com Prometheus/Grafana se necessário

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs: `docker-compose logs -f`
2. Teste o health check: `curl http://localhost:8000/health`
3. Verifique as variáveis: `docker-compose config`
4. Rebuild completo: `docker-compose down -v && docker-compose up -d --build`
