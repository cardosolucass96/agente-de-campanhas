# Sistema de Empilhamento de Mensagens (Message Stacking)

## 📦 Como Funciona

O sistema agora **empilha mensagens** que chegam em sequência rápida antes de processá-las com o agente, e **marca automaticamente como lidas** após 1.5s.

### Comportamento

1. **Mensagem chega** → Salva no banco + adiciona à fila
2. **1.5s depois** → Marca mensagem como lida ✓✓
3. **Timer de 12s inicia** (ou reinicia se já estava contando)
4. **Nova mensagem** → Adiciona à fila + reinicia timer + marca como lida após 1.5s
5. **Após 12s sem novas mensagens** → Processa TODAS juntas

### Exemplo Prático

**Usuário envia:**
```
[00:00] oi
[00:02] tudo bem?
[00:05] como estão as campanhas?
```

**Sistema:**
- 00:00: Recebe "oi" → Timer 12s iniciado → Marca como lida após 1.5s
- 00:02: Recebe "tudo bem?" → Timer REINICIADO (12s novamente) → Marca como lida após 1.5s
- 00:05: Recebe "como estão as campanhas?" → Timer REINICIADO → Marca como lida após 1.5s
- 00:17: 12s sem mensagens → PROCESSA TUDO JUNTO
- 00:17: Envia resposta única

**Agente recebe:**
```
oi
tudo bem?
como estão as campanhas?
```

## ⚙️ Configuração

### Tempo de Espera
Editável em `main.py`:
```python
DEBOUNCE_TIME = 12  # segundos
```

### Estrutura da Fila

Cada contato (número de telefone) tem sua própria fila:
```python
message_queue[phone_number] = {
    "messages": ["msg1", "msg2", "msg3"],
    "timer": Timer object,
    "contact_name": "Nome do Contato",
    "conversation_id": 123
}
```

## 🎯 Vantagens

✅ **Contexto completo**: Usuário pode enviar pensamentos fragmentados  
✅ **Menos processamentos**: Economia de tokens e API calls  
✅ **Respostas melhores**: Agente vê toda a pergunta de uma vez  
✅ **UX natural**: Usuários podem digitar como em conversa real  

## 📊 Logs do Sistema

Quando mensagens chegam:
```
📥 Mensagem adicionada à fila (1 total)
⏱️ Timer de 12s iniciado para 5585...

📥 Mensagem adicionada à fila (2 total)
⏱️ Timer cancelado para 5585..., reagendando...
⏱️ Timer de 12s iniciado para 5585...

📦 Processando 2 mensagem(ns) empilhada(s) de 5585...
💬 Mensagem combinada: oi\ntudo bem?
✅ Resposta enviada para 5585...
```

## 🔧 Funções Principais

### `schedule_message_processing(phone)`
- Agenda o processamento após DEBOUNCE_TIME
- Cancela timer anterior se existir
- Cria novo timer

### `process_stacked_messages(phone)`
- Junta todas as mensagens com `\n`
- Busca contexto (últimas 5 mensagens)
- Processa com o agente
- Envia resposta
- Limpa a fila

## 🧪 Como Testar

### Via WhatsApp Real
1. Envie múltiplas mensagens rápidas
2. Aguarde 12 segundos
3. Receba UMA resposta contemplando TODAS as mensagens

### Via Script de Teste
```bash
python test_message_stacking.py
```

### Via Webhook Manual
```python
import requests

# Mensagem 1
requests.post("http://localhost:8000/evo", json={
    "event": "messages.upsert",
    "data": {
        "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": False},
        "message": {"conversation": "oi"}
    }
})

# Mensagem 2 (dentro de 12s)
requests.post("http://localhost:8000/evo", json={
    "event": "messages.upsert",
    "data": {
        "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": False},
        "message": {"conversation": "tudo bem?"}
    }
})

# Aguardar 12s → Recebe resposta única
```

## ⚠️ Considerações

- **Mensagens são salvas individualmente** no banco
- **Processamento é consolidado** em uma chamada ao agente
- **Timer é POR CONTATO** (não global)
- **Fila persiste** apenas em memória (reiniciar servidor limpa)

## 🚀 Status

✅ Sistema implementado  
✅ Debounce de 12s configurado  
✅ Empilhamento funcionando  
✅ Logs informativos  
✅ Teste automatizado criado
