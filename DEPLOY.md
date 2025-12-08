# 🚀 Guia Rápido de Deploy

## Deploy em VPS (Ubuntu/Debian)

### 1. Preparar Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo apt install docker-compose -y

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Verificar instalação
docker --version
docker-compose --version
```

### 2. Clonar e Configurar

```bash
# Clonar repositório
git clone <seu-repo-url> agente-de-campanhas
cd agente-de-campanhas

# Criar .env
cp .env.example .env
nano .env  # Editar com suas credenciais

# Criar diretório de dados
mkdir -p data
chmod 755 data
```

### 3. Iniciar Aplicação

```bash
# Build e start
docker-compose up -d --build

# Verificar logs
docker-compose logs -f

# Verificar status
docker-compose ps

# Testar
curl http://localhost:8000/health
```

### 4. Configurar Nginx (Reverse Proxy)

```bash
# Instalar Nginx
sudo apt install nginx -y

# Criar configuração
sudo nano /etc/nginx/sites-available/agente-campanhas
```

Adicione:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/agente-campanhas /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 5. Configurar SSL (Let's Encrypt)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Renovação automática (já configurado)
sudo certbot renew --dry-run
```

### 6. Configurar Webhooks

#### WhatsApp Business API

No painel do Facebook Developer:
1. Configure webhook URL: `https://seu-dominio.com/webhook/whatsapp`
2. Verify token: valor de `WHATSAPP_WEBHOOK_VERIFY_TOKEN` no .env
3. Subscribe aos eventos: `messages`, `message_status`

#### Evolution API

No painel da Evolution:
1. Configure webhook: `https://seu-dominio.com/evo`
2. Eventos: `MESSAGES_UPSERT`, `presence.update`

### 7. Monitoramento

```bash
# Ver logs em tempo real
docker-compose logs -f

# Ver apenas últimas 100 linhas
docker-compose logs --tail=100

# Verificar recursos
docker stats

# Health check
curl https://seu-dominio.com/health
```

### 8. Backup Automático

Criar script `/home/usuario/backup-agente.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/usuario/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

docker-compose exec -T agente-campanhas \
  cat /app/data/agente_campanhas.db > $BACKUP_DIR/backup_$DATE.db

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "backup_*.db" -mtime +7 -delete

echo "Backup concluído: backup_$DATE.db"
```

```bash
# Dar permissão
chmod +x /home/usuario/backup-agente.sh

# Adicionar ao crontab (diário às 3h)
crontab -e
# Adicionar linha:
0 3 * * * /home/usuario/backup-agente.sh >> /var/log/backup-agente.log 2>&1
```

### 9. Atualização

```bash
# Pull do código
cd /caminho/para/agente-de-campanhas
git pull origin main

# Backup antes de atualizar
docker-compose exec agente-campanhas \
  cp /app/data/agente_campanhas.db /app/data/backup_before_update.db

# Rebuild e restart
docker-compose up -d --build

# Verificar logs
docker-compose logs -f --tail=50
```

### 10. Troubleshooting

```bash
# Container não inicia
docker-compose logs agente-campanhas

# Verificar portas
sudo netstat -tulpn | grep 8000

# Restart completo
docker-compose down
docker-compose up -d --build

# Limpar tudo e recomeçar
docker-compose down -v
docker system prune -af
docker-compose up -d --build
```

## Deploy com CI/CD (GitHub Actions)

Criar `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /caminho/para/agente-de-campanhas
            git pull origin main
            docker-compose up -d --build
            docker-compose logs --tail=50
```

## Checklist de Deploy ✅

- [ ] Servidor configurado (Docker + Docker Compose)
- [ ] Repositório clonado
- [ ] .env configurado com credenciais de produção
- [ ] Aplicação rodando (`docker-compose up -d`)
- [ ] Nginx configurado como reverse proxy
- [ ] SSL/HTTPS configurado (Let's Encrypt)
- [ ] Webhooks configurados no WhatsApp/Facebook
- [ ] Health check funcionando
- [ ] Backup automático configurado
- [ ] Logs sendo monitorados
- [ ] Firewall configurado (apenas portas 80, 443, 22)

## Segurança Adicional

```bash
# Configurar firewall (UFW)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Desabilitar login root via SSH
sudo nano /etc/ssh/sshd_config
# Alterar: PermitRootLogin no
sudo systemctl restart sshd

# Fail2ban para proteção contra brute force
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

## Monitoramento com Uptime Robot

1. Acesse: https://uptimerobot.com
2. Crie monitor HTTP(S)
3. URL: `https://seu-dominio.com/health`
4. Intervalo: 5 minutos
5. Configure alertas (email/SMS)

---

✅ **Aplicação pronta para produção!**
