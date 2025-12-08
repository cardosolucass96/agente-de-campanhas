from fastapi import FastAPI, Request, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import httpx
from typing import Dict, Any
from datetime import datetime
import asyncio
from collections import defaultdict
import hmac
import hashlib

from database import get_db, init_db
from models import Message, Campaign, Contact, Conversation, AgentLog
from agent import run_agent
from whatsapp_config import ACTIVE_WHATSAPP_CONFIG, WhatsAppProvider
from whatsapp_adapters import get_whatsapp_adapter
import re

load_dotenv()

# Inicializar adaptador WhatsApp baseado na config
whatsapp_adapter = get_whatsapp_adapter(ACTIVE_WHATSAPP_CONFIG)

# Sistema de empilhamento de mensagens (debounce)
message_queue: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
    "messages": [],
    "timer": None,
    "contact_name": None,
    "conversation_id": None
})
DEBOUNCE_TIME = 6  # segundos para esperar antes de processar

# Mapeamento LID → remoteJid para tracking de presence
lid_to_jid_map: Dict[str, str] = {}

# Tracking de último evento de digitação
last_composing_time: Dict[str, float] = {}



async def simulate_typing(phone: str, duration: float = 3.0):
    """
    Simula digitação durante um período.
    Alterna entre digitando e pausado para parecer mais natural.
    Silenciosamente ignora se o provedor não suportar.
    """
    try:
        from whatsapp_config import WhatsAppProvider
        
        # Pular se for WhatsApp Business (não suporta)
        if ACTIVE_WHATSAPP_CONFIG.provider == WhatsAppProvider.WHATSAPP_BUSINESS:
            return
        
        # Dividir duração em ciclos de digitação
        cycles = max(1, int(duration / 2))
        cycle_duration = duration / cycles
        
        for i in range(cycles):
            # Começar a digitar
            result = await whatsapp_adapter.send_presence(phone, "composing")
            if result.get("status") == "not_supported":
                return
            
            # Digitar por um tempo
            typing_time = cycle_duration * 0.7  # 70% digitando
            await asyncio.sleep(typing_time)
            
            # Pausar brevemente (exceto no último ciclo)
            if i < cycles - 1:
                await whatsapp_adapter.send_presence(phone, "paused")
                pause_time = cycle_duration * 0.3  # 30% pausado
                await asyncio.sleep(pause_time)
    
    except Exception as e:
        pass  # Silenciar erros de digitação


async def split_long_message(content: str, max_chars: int = 800) -> list[str]:
    """
    Divide mensagem longa em partes menores de forma inteligente.
    
    Critérios de divisão:
    - Respeita parágrafos e seções
    - Máximo de max_chars por parte
    - Divide em pontos naturais (quebras de linha duplas, listas, etc)
    """
    # Se a mensagem é curta, retorna como está
    if len(content) <= max_chars:
        return [content.strip()]
    
    parts = []
    current_part = ""
    
    # Dividir por seções (quebras de linha duplas)
    sections = content.split('\n\n')
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # Se adicionar esta seção ultrapassa o limite
        if len(current_part) + len(section) + 2 > max_chars and current_part:
            # Salvar parte atual e começar nova
            parts.append(current_part.strip())
            current_part = section + '\n\n'
        else:
            current_part += section + '\n\n'
    
    # Adicionar última parte
    if current_part.strip():
        parts.append(current_part.strip())
    
    return parts


def format_message_for_whatsapp(content: str) -> str:
    """
    Formata mensagem removendo Markdown e convertendo para formatação WhatsApp.
    Não divide - apenas formata.
    """
    # Converter Markdown headers ## -> negrito
    content = re.sub(r'###?\s+(.*?)(?:\n|$)', r'*\1*\n', content)
    
    # Markdown bold ** -> WhatsApp bold *
    content = re.sub(r'\*\*(.*?)\*\*', r'*\1*', content)
    
    # Markdown code ` -> remover
    content = re.sub(r'`(.*?)`', r'\1', content)
    
    # Remover links markdown [texto](url) -> texto (url)
    content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', content)
    
    # Limpar quebras de linha excessivas
    content = re.sub(r'\n{3,}', r'\n\n', content)
    
    return content.strip()


async def send_and_save_message(phone: str, message: str, conversation_id: int, db):
    """
    Envia mensagem via WhatsApp adapter e salva no banco.
    Se mensagem for longa, divide e envia múltiplas partes.
    """
    # Formatar mensagem
    formatted_message = format_message_for_whatsapp(message)
    
    # Dividir se necessário
    parts = await split_long_message(formatted_message, max_chars=800)
    
    print(f"📤 Enviando {len(parts)} parte(s) para {phone}")
    
    # Enviar cada parte com pequeno delay entre elas
    for i, part in enumerate(parts, 1):
        if len(parts) > 1:
            print(f"   Parte {i}/{len(parts)}: {len(part)} caracteres")
        
        # Enviar via WhatsApp adapter
        result = await whatsapp_adapter.send_message(phone, part)
        
        if result.get("status") != "success":
            print(f"⚠️ Erro ao enviar mensagem: {result.get('error', 'Unknown error')}")
        else:
            print(f"✅ Mensagem enviada com sucesso")
        
        # Salvar no banco (salva cada parte como mensagem separada)
        new_message = Message(
            conversation_id=conversation_id,
            text=part,
            direction="outgoing",
            status="sent"
        )
        db.add(new_message)
        db.commit()
        
        # Delay entre mensagens (se houver múltiplas partes)
        if i < len(parts):
            await asyncio.sleep(1.5)  # 1.5s entre cada parte para parecer mais natural


async def process_stacked_messages(phone: str):
    """
    Processa mensagens empilhadas após o tempo de debounce.
    Junta todas as mensagens em uma única string e processa com o agente.
    """
    try:
        queue_data = message_queue[phone]
        messages = queue_data["messages"]
        contact_name = queue_data["contact_name"]
        conversation_id = queue_data["conversation_id"]
        
        if not messages:
            return
        
        # Juntar todas as mensagens com quebra de linha
        combined_message = "\n".join(messages)
        
        print(f"📦 Processando {len(messages)} mensagem(ns) empilhada(s) de {phone}")
        print(f"💬 Mensagem combinada: {combined_message}")
        
        # Buscar últimas 5 mensagens para contexto
        from database import SessionLocal
        db = SessionLocal()
        
        try:
            # Buscar conversação
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                print(f"⚠️ Conversação {conversation_id} não encontrada")
                return
            
            # Buscar últimas 5 mensagens
            previous_messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(5).all()
            
            previous_messages.reverse()
            
            # Iniciar digitação em paralelo ao processamento
            typing_task = asyncio.create_task(simulate_typing(phone, duration=8.0))
            
            try:
                # Processar com o agente (enquanto simula digitação em paralelo)
                print(f"🤖 Chamando agente com mensagem: {combined_message}")
                response = await run_agent(
                    message=combined_message,
                    conversation_id=conversation_id,
                    previous_messages=previous_messages,
                    contact_name=contact_name
                )
                print(f"🤖 Resposta do agente: {response[:100]}...")
                
                # Verificar se há lista ou botões pendentes
                from tools.whatsapp_list import get_pending_list
                from tools.whatsapp_buttons import pending_buttons
                
                pending_list = get_pending_list()
                
                if pending_list.get("list_data"):
                    # Enviar lista interativa
                    print(f"📋 Enviando lista interativa para {phone}")
                    result = await whatsapp_adapter.send_list(phone, pending_list["list_data"])
                    
                    if result.get("status") == "success":
                        print(f"✅ Lista enviada com sucesso")
                    else:
                        # Fallback: enviar como texto formatado
                        print(f"⚠️ Falha ao enviar lista, enviando como texto: {result.get('error')}")
                        from whatsapp_tools import format_list_as_text
                        text_version = format_list_as_text(pending_list["list_data"])
                        await send_and_save_message(phone, text_version, conversation_id, db)
                
                elif pending_buttons:
                    # Enviar botões interativos
                    print(f"🔘 Enviando botões interativos para {phone}")
                    result = await whatsapp_adapter.send_buttons(phone, response, pending_buttons)
                    
                    if result.get("status") == "success":
                        print(f"✅ Botões enviados com sucesso")
                    else:
                        # Fallback: enviar como texto normal
                        print(f"⚠️ Falha ao enviar botões, enviando como texto: {result.get('error')}")
                        await send_and_save_message(phone, response, conversation_id, db)
                    
                    # Limpar botões pendentes
                    import tools.whatsapp_buttons
                    tools.whatsapp_buttons.pending_buttons = None
                
                else:
                    # Enviar resposta normal
                    await send_and_save_message(phone, response, conversation_id, db)
                
                print(f"✅ Resposta enviada para {phone}")
                
            finally:
                # Cancelar digitação se ainda estiver rodando
                if not typing_task.done():
                    typing_task.cancel()
            
        finally:
            db.close()
        
        # Limpar fila
        message_queue[phone] = {
            "messages": [],
            "timer": None,
            "contact_name": None,
            "conversation_id": None
        }
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagens empilhadas: {str(e)}")
        import traceback
        traceback.print_exc()


async def schedule_message_processing(phone: str):
    """
    Agenda o processamento das mensagens após o tempo de debounce.
    Se uma nova mensagem chegar, cancela o timer anterior e cria um novo.
    """
    queue_data = message_queue[phone]
    
    # Cancelar timer anterior se existir
    if queue_data["timer"] is not None:
        queue_data["timer"].cancel()
        print(f"⏱️ Timer cancelado para {phone}, reagendando...")
    
    # Criar novo timer
    loop = asyncio.get_event_loop()
    timer = loop.call_later(
        DEBOUNCE_TIME,
        lambda: asyncio.create_task(process_stacked_messages(phone))
    )
    
    queue_data["timer"] = timer
    print(f"⏱️ Timer de {DEBOUNCE_TIME}s iniciado para {phone}")


async def mark_message_as_read(phone: str, message_id: str, delay: float = 1.5):
    """
    Marca a mensagem como lida após um delay (1-2s).
    Envia requisição via WhatsApp adapter para marcar como lida.
    Silenciosamente ignora se o provedor não suportar.
    """
    try:
        from whatsapp_config import WhatsAppProvider
        
        # Pular se for WhatsApp Business (não suporta)
        if ACTIVE_WHATSAPP_CONFIG.provider == WhatsAppProvider.WHATSAPP_BUSINESS:
            return
        
        # Aguardar o delay
        await asyncio.sleep(delay)
        
        print(f"👀 Marcando mensagem como lida para {phone} (ID: {message_id})")
        
        # Marcar como lida via adapter
        result = await whatsapp_adapter.mark_as_read(phone, message_id)
        
        if result.get("status") == "success":
            print(f"✅ Mensagem marcada como lida para {phone}")
        elif result.get("status") == "not_supported":
            pass  # Silenciar
        else:
            error = result.get('error', {})
            if isinstance(error, dict):
                # Silenciar erros conhecidos da API oficial
                return
            print(f"⚠️ Falha ao marcar como lida")
    
    except Exception as e:
        pass  # Silenciar erros de marcar como lida


load_dotenv()

app = FastAPI()

# Inicializar banco de dados na inicialização da aplicação
@app.on_event("startup")
async def startup_event():
    from whatsapp_config import WhatsAppProvider
    
    init_db()
    print("Banco de dados inicializado!")
    print(f"⏱️ Sistema de empilhamento: {DEBOUNCE_TIME}s de espera entre mensagens")
    
    # Mostrar recursos disponíveis baseado no provider
    if ACTIVE_WHATSAPP_CONFIG.provider == WhatsAppProvider.EVOLUTION:
        print(f"📱 Provider: Evolution API")
        print(f"👀 Marcar como lida: 1.5s após receber")
        print(f"✍️ Simulação de digitação: Ativada")
        print(f"⚡ Detecção de 'parou de digitar': Processamento imediato ativado")
    else:
        print(f"📱 Provider: WhatsApp Business API (Oficial)")
        print(f"✅ Envio de mensagens: Suportado")
        print(f"✅ Recebimento de webhooks: Suportado")
        print(f"✅ Status de entrega: Suportado")
        print(f"ℹ️ Marcar como lida: Não suportado pela API oficial")
        print(f"ℹ️ Simulação de digitação: Não suportado pela API oficial")

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Agente de Campanhas API"}

@app.post("/evo")
async def evolution_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para receber webhooks da Evolution API
    Evento: MESSAGES_UPSERT
    """
    try:
        data = await request.json()
        print(f"Webhook recebido: {data}")
        
        # Processar a mensagem recebida
        event = data.get("event")
        instance = data.get("instance")
        
        # Detectar quando usuário parou de digitar
        if event == "presence.update":
            import time
            presence_data = data.get("data", {})
            lid_id = presence_data.get("id", "")  # Vem como 118232061112489@lid
            presences = presence_data.get("presences", {})
            
            # Pegar o presence do usuário
            user_presence = presences.get(lid_id, {})
            presence_status = user_presence.get("lastKnownPresence", "")
            
            # Mapear LID para remoteJid usando nosso mapeamento
            remote_jid = lid_to_jid_map.get(lid_id)
            
            if remote_jid and remote_jid in message_queue:
                queue_data = message_queue[remote_jid]
                
                # Se está digitando, atualizar timestamp
                if presence_status == "composing":
                    last_composing_time[remote_jid] = time.time()
                    print(f"✍️ Usuário digitando... (atualizado)")
                
                # Se parou de digitar (available) E tem mensagens na fila
                elif presence_status == "available" and len(queue_data["messages"]) > 0:
                    print(f"⚡ Usuário parou de digitar (available), processando imediatamente!")
                    # Cancelar timer existente
                    if queue_data["timer"] is not None:
                        queue_data["timer"].cancel()
                    # Processar agora
                    asyncio.create_task(process_stacked_messages(remote_jid))
            
            return {"status": "presence_tracked", "presence": presence_status, "lid": lid_id, "jid": remote_jid}
        
        if event == "messages.upsert":
            message_data = data.get("data", {})
            message = message_data.get("message", {})
            key = message_data.get("key", {})
            
            remote_jid = key.get("remoteJid", "")
            from_me = key.get("fromMe", False)
            message_id = key.get("id", "")
            remote_jid_alt = key.get("remoteJidAlt", "")  # LID format
            
            # Mapear LID para remoteJid para tracking de presence
            if remote_jid_alt:
                lid_to_jid_map[remote_jid_alt] = remote_jid
            
            # Ignorar mensagens enviadas por nós
            if from_me:
                return {"status": "ignored", "reason": "message from me"}
            
            # Extrair texto da mensagem
            text = ""
            if "conversation" in message:
                text = message["conversation"]
            elif "extendedTextMessage" in message:
                text = message["extendedTextMessage"].get("text", "")
            
            # Extrair nome do contato
            push_name = message_data.get("pushName", "")
            
            print(f"Mensagem de {remote_jid}: {text}")
            
            # Verificar/criar contato
            contact = db.query(Contact).filter(Contact.phone == remote_jid).first()
            if not contact:
                contact = Contact(
                    phone=remote_jid,
                    name=push_name,
                    last_interaction=datetime.utcnow()
                )
                db.add(contact)
                db.flush()
            else:
                # Atualizar nome se veio no pushName
                if push_name and not contact.name:
                    contact.name = push_name
                contact.last_interaction = datetime.utcnow()
            
            # Verificar/criar conversação ativa
            conversation = db.query(Conversation).filter(
                Conversation.contact_id == contact.id,
                Conversation.status == "active"
            ).first()
            
            if not conversation:
                conversation = Conversation(
                    contact_id=contact.id,
                    context={}
                )
                db.add(conversation)
                db.flush()
            
            conversation.last_message_at = datetime.utcnow()
            
            # Salvar mensagem recebida no banco de dados
            db_message = Message(
                instance=instance,
                remote_jid=remote_jid,
                message_id=message_id,
                direction="incoming",
                from_me=from_me,
                text=text,
                status="received",
                raw_data=data,
                contact_id=contact.id,
                conversation_id=conversation.id
            )
            db.add(db_message)
            db.commit()
            
            # Log da ação do agente
            agent_log = AgentLog(
                conversation_id=conversation.id,
                action="receive_message",
                input_data={"message_id": message_id, "text": text},
                status="success"
            )
            db.add(agent_log)
            db.commit()
            
            # Marcar mensagem como lida após 1-2s
            asyncio.create_task(mark_message_as_read(remote_jid, message_id, delay=1.5))
            
            # SISTEMA DE EMPILHAMENTO DE MENSAGENS
            # Adicionar mensagem à fila do contato
            queue_data = message_queue[remote_jid]
            queue_data["messages"].append(text)
            queue_data["contact_name"] = contact.name
            queue_data["conversation_id"] = conversation.id
            
            print(f"📥 Mensagem adicionada à fila ({len(queue_data['messages'])} total)")
            
            # Agendar processamento (cancela timer anterior se existir)
            await schedule_message_processing(remote_jid)
            
            return {
                "status": "queued",
                "event": event,
                "instance": instance,
                "from": remote_jid,
                "message": text,
                "saved": True,
                "conversation_id": conversation.id,
                "queue_size": len(queue_data["messages"]),
                "timer_seconds": DEBOUNCE_TIME
            }
        
        return {"status": "received", "event": event}
        
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        db.rollback()
        return {"status": "error", "message": str(e)}


@app.get("/webhook/whatsapp")
async def whatsapp_business_webhook_verify(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Webhook verification para WhatsApp Business API
    GET endpoint usado pelo Facebook para verificar o webhook
    """
    try:
        from whatsapp_config import WhatsAppBusinessConfig
        
        config = ACTIVE_WHATSAPP_CONFIG
        
        print(f"🔍 Webhook verification started")
        
        # Verificar se é WhatsApp Business
        if not isinstance(config, WhatsAppBusinessConfig):
            print("❌ Config not WhatsApp Business")
            return JSONResponse(content={"error": "WhatsApp Business API not configured"}, status_code=400)
        
        print(f"🔍 mode={mode}, token={token}, challenge={challenge}")
        
        # Verificar token
        if mode == "subscribe" and token == config.webhook_verify_token:
            print("✅ Webhook verified successfully")
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            print("⚠️ Webhook verification failed")
            return JSONResponse(content={"error": "Verification failed"}, status_code=403)
    except Exception as e:
        print(f"💥 Exception in webhook verify: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)



@app.post("/webhook/whatsapp")
async def whatsapp_business_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook para receber mensagens da WhatsApp Business API
    POST endpoint para processar eventos do WhatsApp
    """
    try:
        data = await request.json()
        print(f"📱 WhatsApp Business webhook recebido: {data}")
        
        # Validar signature se APP_SECRET estiver configurado
        from whatsapp_config import WhatsAppBusinessConfig
        config = ACTIVE_WHATSAPP_CONFIG
        
        if isinstance(config, WhatsAppBusinessConfig) and config.app_secret:
            signature = request.headers.get("X-Hub-Signature-256", "")
            body = await request.body()
            
            expected_signature = "sha256=" + hmac.new(
                config.app_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                print("⚠️ Invalid signature")
                return JSONResponse(content={"error": "Invalid signature"}, status_code=403)
        
        # Parse webhook usando adaptador
        parsed_data = whatsapp_adapter.parse_webhook(data)
        
        if not parsed_data:
            return {"status": "ignored", "reason": "not a message event"}
        
        if parsed_data["type"] == "message":
            remote_jid = parsed_data["phone"]
            text = parsed_data["text"]
            message_id = parsed_data["message_id"]
            push_name = parsed_data["push_name"]
            from_me = parsed_data["from_me"]
            
            # Ignorar mensagens enviadas por nós
            if from_me:
                return {"status": "ignored", "reason": "message from me"}
            
            print(f"💬 Mensagem de {remote_jid}: {text}")
            
            # Processar igual ao Evolution (mesma lógica)
            # Verificar/criar contato
            contact = db.query(Contact).filter(Contact.phone == remote_jid).first()
            if not contact:
                contact = Contact(
                    phone=remote_jid,
                    name=push_name,
                    last_interaction=datetime.utcnow()
                )
                db.add(contact)
                db.flush()
            else:
                if push_name and not contact.name:
                    contact.name = push_name
                contact.last_interaction = datetime.utcnow()
            
            # Verificar/criar conversação ativa
            conversation = db.query(Conversation).filter(
                Conversation.contact_id == contact.id,
                Conversation.status == "active"
            ).first()
            
            if not conversation:
                conversation = Conversation(contact_id=contact.id, context={})
                db.add(conversation)
                db.flush()
            
            # Salvar mensagem
            db_message = Message(
                instance="whatsapp_business",
                remote_jid=remote_jid,
                message_id=message_id,
                direction="incoming",
                from_me=from_me,
                text=text,
                status="received",
                raw_data=data,
                contact_id=contact.id,
                conversation_id=conversation.id
            )
            db.add(db_message)
            db.commit()
            
            # Log
            agent_log = AgentLog(
                conversation_id=conversation.id,
                action="receive_message",
                input_data={"message_id": message_id, "text": text},
                status="success"
            )
            db.add(agent_log)
            db.commit()
            
            # Marcar como lida
            asyncio.create_task(mark_message_as_read(remote_jid, message_id, delay=1.5))
            
            # Sistema de empilhamento
            queue_data = message_queue[remote_jid]
            queue_data["messages"].append(text)
            queue_data["contact_name"] = contact.name
            queue_data["conversation_id"] = conversation.id
            
            print(f"📥 Mensagem adicionada à fila ({len(queue_data['messages'])} total)")
            
            await schedule_message_processing(remote_jid)
            
            return {
                "status": "queued",
                "from": remote_jid,
                "message": text,
                "saved": True,
                "conversation_id": conversation.id,
                "queue_size": len(queue_data["messages"]),
                "timer_seconds": DEBOUNCE_TIME
            }
        
        elif parsed_data["type"] == "status":
            # Status update (delivered, read, etc)
            print(f"📊 Status update: {parsed_data}")
            return {"status": "received", "type": "status"}
        
        return {"status": "received"}
        
    except Exception as e:
        print(f"❌ Erro ao processar WhatsApp Business webhook: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {"status": "error", "message": str(e)}


# Função send_message removida - usar whatsapp_adapter.send_message() diretamente

@app.post("/send")
async def send_message_endpoint(
    phone: str,
    message: str,
    conversation_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint para enviar mensagens manualmente.
    Se conversation_id não for fornecido, cria/busca conversação automaticamente.
    """
    try:
        # Se não tem conversation_id, buscar ou criar
        if not conversation_id:
            # Buscar/criar contato
            contact = db.query(Contact).filter(Contact.phone == phone).first()
            if not contact:
                contact = Contact(
                    phone=phone,
                    name="Manual",
                    last_interaction=datetime.utcnow()
                )
                db.add(contact)
                db.flush()
            
            # Buscar/criar conversação
            conversation = db.query(Conversation).filter(
                Conversation.contact_id == contact.id,
                Conversation.status == "active"
            ).first()
            
            if not conversation:
                conversation = Conversation(contact_id=contact.id, context={})
                db.add(conversation)
                db.flush()
            
            conversation_id = conversation.id
        
        await send_and_save_message(phone, message, conversation_id, db)
        return {"status": "success", "message": "Message sent"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/facebook/accounts")
async def get_default_accounts():
    """
    Retorna as 5 contas de anúncio padrão configuradas
    """
    try:
        from default_accounts import DEFAULT_AD_ACCOUNTS
        
        accounts = [
            {
                "id": info["act_id"],
                "name": info["name"],
                "account_id": acc_id,
                "status": "configured"
            }
            for acc_id, info in DEFAULT_AD_ACCOUNTS.items()
        ]
        
        return {
            "status": "success",
            "accounts": accounts,
            "total": len(accounts)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/agent/chat")
async def chat_with_agent(message: str, conversation_id: int = None):
    """
    Endpoint para conversar diretamente com o agente
    """
    try:
        response = await run_agent(message, conversation_id=conversation_id)
        return {"status": "success", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}
