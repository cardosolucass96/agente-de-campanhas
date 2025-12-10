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
from whatsapp_config import ACTIVE_WHATSAPP_CONFIG
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


async def simulate_typing(phone: str, duration: float = 3.0):
    """
    Simula digitação durante um período.
    WhatsApp Business API não suporta este recurso.
    """
    # WhatsApp Business API não suporta envio de presence
    return


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
    # Validar mensagem antes de processar
    if not message or not message.strip():
        print(f"⚠️ Tentativa de enviar mensagem vazia para {phone}")
        return
    
    # Formatar mensagem
    formatted_message = format_message_for_whatsapp(message)
    
    # Validar após formatação
    if not formatted_message or not formatted_message.strip():
        print(f"⚠️ Mensagem ficou vazia após formatação. Original: {message[:100]}")
        return
    
    # Dividir se necessário
    parts = await split_long_message(formatted_message, max_chars=800)
    
    print(f"📤 Enviando {len(parts)} parte(s) para {phone}")
    
    # Enviar cada parte com pequeno delay entre elas
    for i, part in enumerate(parts, 1):
        if len(parts) > 1:
            print(f"   Parte {i}/{len(parts)}: {len(part)} caracteres")
        
        # Debug: mostrar preview da mensagem
        print(f"   Preview: {part[:100]}...")
        
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
                
                # Debug detalhado da resposta
                print(f"🤖 Resposta do agente recebida:")
                print(f"   - Tipo: {type(response)}")
                print(f"   - Tamanho: {len(response) if response else 0} caracteres")
                print(f"   - Preview: {response[:100] if response else 'VAZIO'}...")
                
                # Validar resposta
                if not response or not response.strip():
                    print("❌ ERRO: Agente retornou resposta vazia!")
                    response = "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
                
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
                        # Salvar mensagem no banco para manter contexto
                        list_text = response if response else pending_list["list_data"].get("body", "Lista de opções")
                        new_message = Message(
                            conversation_id=conversation_id,
                            text=list_text,
                            direction="outgoing",
                            status="sent"
                        )
                        db.add(new_message)
                        db.commit()
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
                        # Salvar mensagem no banco para manter contexto
                        new_message = Message(
                            conversation_id=conversation_id,
                            text=response,
                            direction="outgoing",
                            status="sent"
                        )
                        db.add(new_message)
                        db.commit()
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
    init_db()
    print("Banco de dados inicializado!")
    print(f"⏱️ Sistema de empilhamento: {DEBOUNCE_TIME}s de espera entre mensagens")
    print(f"📱 Provider: WhatsApp Business API (Oficial)")
    print(f"✅ Envio de mensagens: Suportado")
    print(f"✅ Recebimento de webhooks: Suportado")
    print(f"✅ Status de entrega: Suportado")
    print(f"✅ Marcar como lida: Suportado")

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Agente de Campanhas API"}

@app.post("/test/message")
async def test_message(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint de teste para simular mensagem direta ao agente
    Body: {"message": "sua mensagem aqui", "phone": "5511999999999"}
    """
    try:
        data = await request.json()
        message = data.get("message", "")
        phone = data.get("phone", "5511999999999")
        contact_name = data.get("name", "Teste")
        
        print(f"\n{'='*50}")
        print(f"🧪 TESTE DIRETO - Mensagem: {message}")
        print(f"{'='*50}\n")
        
        # Criar ou buscar contato e conversação
        contact = db.query(Contact).filter(Contact.phone == phone).first()
        
        if not contact:
            contact = Contact(phone=phone, name=contact_name)
            db.add(contact)
            db.commit()
            db.refresh(contact)
        
        conversation = db.query(Conversation).filter(
            Conversation.contact_id == contact.id
        ).first()
        
        if not conversation:
            conversation = Conversation(contact_id=contact.id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # Salvar mensagem recebida
        incoming_msg = Message(
            conversation_id=conversation.id,
            text=message,
            direction="incoming",
            status="received"
        )
        db.add(incoming_msg)
        db.commit()
        
        # Buscar contexto
        previous_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(5).all()
        previous_messages.reverse()
        
        # Chamar agente
        print(f"🤖 Chamando agente...")
        response = await run_agent(
            message=message,
            conversation_id=conversation.id,
            previous_messages=previous_messages,
            contact_name=contact_name
        )
        
        print(f"\n{'='*50}")
        print(f"🤖 RESPOSTA DO AGENTE:")
        print(f"{'='*50}")
        print(f"Tipo: {type(response)}")
        print(f"Tamanho: {len(response) if response else 0} caracteres")
        print(f"Conteúdo:\n{response}")
        print(f"{'='*50}\n")
        
        # Salvar resposta
        outgoing_msg = Message(
            conversation_id=conversation.id,
            text=response,
            direction="outgoing",
            status="sent"
        )
        db.add(outgoing_msg)
        db.commit()
        
        return {
            "status": "success",
            "message": message,
            "response": response,
            "response_length": len(response) if response else 0
        }
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)


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
        from fastapi.responses import PlainTextResponse
        
        config = ACTIVE_WHATSAPP_CONFIG
        
        print(f"🔍 Webhook verification started")
        print(f"🔍 mode={mode}, token={token}, challenge={challenge}")
        
        # Verificar token
        if mode == "subscribe" and token == config.webhook_verify_token:
            print("✅ Webhook verified successfully")
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
    
    Segurança: Valida assinatura X-Hub-Signature-256 do Meta
    """
    try:
        # Ler body uma vez só (necessário para validação de assinatura)
        body = await request.body()
        data = __import__('json').loads(body)
        
        # Validar signature se APP_SECRET estiver configurado
        config = ACTIVE_WHATSAPP_CONFIG
        disable_signature = os.getenv("WHATSAPP_DISABLE_SIGNATURE_VALIDATION", "false").lower() == "true"

        if not disable_signature and config.app_secret:
            signature = request.headers.get("X-Hub-Signature-256", "")
            
            if not signature:
                print("🚫 Requisição sem assinatura - rejeitada")
                return JSONResponse(content={"error": "Missing signature"}, status_code=403)
            
            expected_signature = "sha256=" + hmac.new(
                config.app_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                print(f"🚫 Assinatura inválida - rejeitada")
                return JSONResponse(content={"error": "Invalid signature"}, status_code=403)
            
            print("✅ Assinatura válida")
        elif disable_signature:
            print("⚠️ Validação de assinatura desabilitada")
        
        print(f"📱 WhatsApp Business webhook recebido: {data}")
        
        # Parse webhook usando adaptador
        parsed_data = whatsapp_adapter.parse_webhook(data)
        
        print(f"🔍 Parsed data: {parsed_data}")
        
        if not parsed_data:
            print("❌ Parse retornou None/vazio")
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
            
            # Verificar se é resposta interativa (botão/lista)
            interactive_data = parsed_data.get("interactive_data")
            is_interactive = interactive_data is not None
            
            if is_interactive:
                print(f"🔘 Resposta interativa de {remote_jid}: {text}")
            else:
                print(f"💬 Mensagem de {remote_jid}: {text}")
            
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
            
            # Se for mensagem interativa, enriquecer com contexto
            if is_interactive:
                last_bot_msg = db.query(Message).filter(
                    Message.conversation_id == conversation.id,
                    Message.direction == "outgoing"
                ).order_by(Message.created_at.desc()).first()
                
                if last_bot_msg:
                    context_preview = last_bot_msg.text[:150].replace('\n', ' ')
                    enriched_text = f"[CONTEXTO: O usuário clicou no botão/lista '{text}' em resposta à mensagem: '{context_preview}...']\n\nUsuário selecionou: {text}"
                    print(f"📝 Texto enriquecido com contexto da mensagem anterior")
                else:
                    enriched_text = f"[CONTEXTO: O usuário clicou no botão/lista '{text}']\n\nUsuário selecionou: {text}"
            else:
                enriched_text = text
            
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
            queue_data["messages"].append(enriched_text)  # Usa texto enriquecido se interativo
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

