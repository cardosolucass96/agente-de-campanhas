# Configuração de Integração WhatsApp

Este projeto suporta duas opções de integração com WhatsApp:

## 1. Evolution API (Padrão)

API self-hosted para WhatsApp. Ideal para desenvolvimento e uso interno.

### Configuração no `.env`:

```env
WHATSAPP_PROVIDER=evolution

EVOLUTION_API_URL=https://sua-evolution-api.com/manager
EVOLUTION_API_KEY=sua-api-key
EVOLUTION_INSTANCE=sua-instancia
```

### Webhook:
- **Endpoint**: `POST /evo`
- Configure no painel da Evolution API para apontar para: `https://seu-dominio.com/evo`
- Eventos necessários: `messages.upsert`, `presence.update`

---

## 2. WhatsApp Business API (Cloud API)

API oficial do Facebook/Meta. Ideal para produção em escala.

### Configuração no `.env`:

```env
WHATSAPP_PROVIDER=whatsapp_business

WHATSAPP_ACCESS_TOKEN=seu-token-de-acesso
WHATSAPP_PHONE_NUMBER_ID=id-do-numero
WHATSAPP_BUSINESS_ACCOUNT_ID=id-da-conta-business
WHATSAPP_WEBHOOK_VERIFY_TOKEN=token-secreto-para-verificacao
WHATSAPP_APP_SECRET=app-secret-opcional
```

### Obtenção das Credenciais:

1. **Criar App no Facebook Developers**
   - Acesse: https://developers.facebook.com/
   - Crie um novo App do tipo "Business"
   - Adicione o produto "WhatsApp"

2. **Configurar WhatsApp Business API**
   - No painel do app, vá em WhatsApp > Getting Started
   - Copie o `WHATSAPP_ACCESS_TOKEN` (temporário ou permanente)
   - Copie o `WHATSAPP_PHONE_NUMBER_ID` do número de teste ou produção

3. **Business Account ID**
   - No painel, vá em WhatsApp > Settings
   - Copie o Business Account ID

4. **Webhook Configuration**
   - No painel, vá em WhatsApp > Configuration > Webhook
   - **Callback URL**: `https://seu-dominio.com/webhook/whatsapp`
   - **Verify Token**: Crie uma string secreta qualquer (ex: `meu_token_secreto_123`)
     - Esta mesma string vai no `.env` como `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
   - Clique em "Verify and Save"
   - Depois de verificado, subscribe nos seguintes eventos:
     - ✅ `messages` (para receber mensagens)
     - ✅ `message_status` (opcional, para status de entrega)

5. **App Secret (Opcional mas Recomendado)**
   - No painel do app, vá em Settings > Basic
   - Copie o "App Secret"
   - Adicione no `.env` como `WHATSAPP_APP_SECRET`
   - Isso habilita validação de assinatura nos webhooks

### Webhook Endpoints:

- **Verificação (GET)**: `/webhook/whatsapp`
  - Usado pelo Facebook para verificar seu webhook
  - Responde com o challenge code se o verify token estiver correto

- **Recebimento (POST)**: `/webhook/whatsapp`
  - Recebe mensagens e eventos do WhatsApp
  - Valida assinatura se `WHATSAPP_APP_SECRET` estiver configurado

### Testando a Integração:

1. **Verificar Webhook**:
   ```bash
   curl "https://seu-dominio.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=seu-token&hub.challenge=12345"
   ```
   Deve retornar: `12345`

2. **Enviar Mensagem de Teste**:
   - Use o número de teste fornecido pelo Facebook
   - Envie uma mensagem via WhatsApp
   - Verifique os logs do servidor

---

## Diferenças entre as APIs

| Feature | Evolution API | WhatsApp Business API |
|---------|--------------|---------------------|
| **Custo** | Self-hosted (grátis) | Cobrado por conversa |
| **Setup** | Simples | Complexo (requer aprovação) |
| **Status "Digitando"** | ✅ Suportado | ❌ Não suportado |
| **Marca Verificada** | ❌ Não | ✅ Sim (após aprovação) |
| **Escalabilidade** | Limitada | Ilimitada |
| **Documentação** | Comunidade | Oficial Meta |
| **Webhooks** | Customizável | Padrão Meta |

---

## Mudando entre APIs

Para trocar de API, basta alterar o `.env`:

```env
# Para Evolution
WHATSAPP_PROVIDER=evolution

# Para WhatsApp Business
WHATSAPP_PROVIDER=whatsapp_business
```

O sistema detecta automaticamente e usa o adaptador correto.

---

## Arquitetura

### Arquivos Principais:

- **`whatsapp_config.py`**: Configurações e seleção de provider
- **`whatsapp_adapters.py`**: Adaptadores para cada API (padrão Adapter)
- **`main.py`**: Endpoints de webhook e lógica de processamento

### Fluxo de Mensagem:

```
WhatsApp → Webhook → Adapter.parse_webhook() → Queue → Agent → Adapter.send_message() → WhatsApp
```

### Extensibilidade:

Para adicionar um novo provider:

1. Criar config em `whatsapp_config.py`
2. Criar adapter em `whatsapp_adapters.py` implementando `WhatsAppAdapter`
3. Adicionar endpoint no `main.py` se necessário
4. Adicionar opção no `.env`

---

## Troubleshooting

### Evolution API não recebe mensagens
- Verifique se o webhook está configurado corretamente
- Teste o endpoint: `curl -X POST https://seu-dominio.com/evo`
- Verifique logs do Evolution API

### WhatsApp Business webhook não verifica
- Confirme que o `WHATSAPP_WEBHOOK_VERIFY_TOKEN` está correto
- Teste manualmente o GET endpoint
- Verifique se a URL é acessível publicamente (não pode ser localhost)

### Mensagens não são enviadas
- Verifique credenciais no `.env`
- Para WhatsApp Business: confirme que o token não expirou
- Verifique logs do servidor: `print()` statements mostram detalhes

### Erro de signature inválida (WhatsApp Business)
- Verifique se `WHATSAPP_APP_SECRET` está correto
- Confirme que o app secret corresponde ao app no Facebook

---

## Produção

### Checklist:

- [ ] SSL/HTTPS habilitado (obrigatório para WhatsApp Business)
- [ ] Webhook verify token seguro e aleatório
- [ ] App Secret configurado para validação de assinatura
- [ ] Access token permanente (não token temporário)
- [ ] Logs configurados para monitoramento
- [ ] Rate limiting implementado
- [ ] Backup do banco de dados configurado

### URLs Públicas:

Seu domínio precisa ser acessível publicamente. Opções:

- **Cloudflare Tunnel** (atual)
- **ngrok** (desenvolvimento)
- **Heroku/Railway/Render** (produção)
- **VPS próprio** com domínio

---

## Documentação Oficial

- **Evolution API**: https://doc.evolution-api.com/
- **WhatsApp Business API**: https://developers.facebook.com/docs/whatsapp
- **Cloud API Webhooks**: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks
