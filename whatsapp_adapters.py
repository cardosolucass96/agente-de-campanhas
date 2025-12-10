"""
Adaptador para WhatsApp Business API (Oficial)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from whatsapp_config import WhatsAppBusinessConfig


class WhatsAppAdapter(ABC):
    """Interface base para adaptador WhatsApp"""
    
    @abstractmethod
    async def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        """Envia mensagem de texto"""
        pass
    
    @abstractmethod
    async def send_list(self, phone: str, list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envia mensagem com lista de opções interativa"""
        pass
    
    @abstractmethod
    async def send_presence(self, phone: str, presence: str) -> Dict[str, Any]:
        """Envia status de presença (digitando, pausado)"""
        pass
    
    @abstractmethod
    async def mark_as_read(self, phone: str, message_id: str) -> Dict[str, Any]:
        """Marca mensagem como lida"""
        pass
    
    @abstractmethod
    def parse_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse webhook data para formato padronizado"""
        pass


class WhatsAppBusinessAdapter(WhatsAppAdapter):
    """Adaptador para WhatsApp Business API"""
    
    def __init__(self, config: WhatsAppBusinessConfig):
        self.config = config
        self.base_url = "https://graph.facebook.com/v21.0"
    
    async def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.config.phone_number_id}/messages"
        
        # Limpar número (remover @s.whatsapp.net se vier)
        clean_phone = phone.replace("@s.whatsapp.net", "")
        
        # Validar mensagem não vazia
        if not message or not message.strip():
            print(f"⚠️ Tentativa de enviar mensagem vazia para {clean_phone}")
            return {
                "status": "error",
                "error": "Message body is empty"
            }
        
        # Garantir que a mensagem não é apenas whitespace
        message = message.strip()
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            result = response.json()
            
            # Log de erro detalhado
            if response.status_code != 200:
                print(f"❌ Erro ao enviar mensagem: Status {response.status_code}")
                print(f"❌ Resposta: {result}")
                return {
                    "status": "error",
                    "error": result
                }
            
            return {
                "status": "success",
                "data": result
            }
    
    async def send_list(self, phone: str, list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envia lista interativa via WhatsApp Business API"""
        url = f"{self.base_url}/{self.config.phone_number_id}/messages"
        
        clean_phone = phone.replace("@s.whatsapp.net", "")
        
        # Converter formato para WhatsApp Business API
        # https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages#interactive-messages
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": list_data["body"]
                },
                "action": {
                    "button": list_data["button"],
                    "sections": list_data["sections"]
                }
            }
        }
        
        # Header opcional
        if "header" in list_data:
            payload["interactive"]["header"] = {
                "type": "text",
                "text": list_data["header"]
            }
        
        # Footer opcional
        if "footer" in list_data:
            payload["interactive"]["footer"] = {
                "text": list_data["footer"]
            }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                if response.status_code in [200, 201]:
                    return {"status": "success", "response": response.json()}
                else:
                    return {"status": "error", "error": response.json()}
            except Exception as e:
                return {"status": "error", "error": str(e)}
    
    async def send_buttons(self, phone: str, body_text: str, buttons_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envia botões interativos via WhatsApp Business API"""
        url = f"{self.base_url}/{self.config.phone_number_id}/messages"
        
        clean_phone = phone.replace("@s.whatsapp.net", "")
        
        # Formato WhatsApp Business API para botões
        # https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages#interactive-messages
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "interactive",
            "interactive": buttons_data
        }
        
        # Garantir que body_text esteja no formato correto
        if "body" not in payload["interactive"]:
            payload["interactive"]["body"] = {"text": body_text}
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                if response.status_code in [200, 201]:
                    return {"status": "success", "response": response.json()}
                else:
                    return {"status": "error", "error": response.json()}
            except Exception as e:
                return {"status": "error", "error": str(e)}
    
    async def send_presence(self, phone: str, presence: str) -> Dict[str, Any]:
        """
        WhatsApp Business API não suporta envio de presence diretamente
        Retorna mock success
        """
        return {"status": "not_supported", "message": "WhatsApp Business API doesn't support presence"}
    
    async def mark_as_read(self, phone: str, message_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.config.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            return response.json()
    
    def parse_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse WhatsApp Business API webhook"""
        # Webhook format: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components
        
        print(f"🔍 WhatsApp Business parse_webhook - data: {data}")
        
        # Verificar se é um evento válido do WhatsApp Business
        if data.get("object") != "whatsapp_business_account":
            print(f"❌ Object não é whatsapp_business_account: {data.get('object')}")
            return None
        
        entries = data.get("entry", [])
        if not entries:
            print("❌ Sem entries no webhook")
            return None
            
        entry = entries[0]
        changes = entry.get("changes", [])
        if not changes:
            print("❌ Sem changes no webhook")
            return None
            
        change = changes[0]
        value = change.get("value", {})
        
        print(f"🔍 value: {value}")
        
        # Mensagens recebidas
        messages = value.get("messages", [])
        print(f"🔍 messages: {messages}")
        
        if messages:
            msg = messages[0]
            
            # Extrair texto baseado no tipo de mensagem
            text = ""
            msg_type = msg.get("type")
            
            if msg_type == "text":
                text = msg.get("text", {}).get("body", "")
            elif msg_type == "interactive":
                # Resposta de lista interativa ou botão
                interactive = msg.get("interactive", {})
                interactive_type = interactive.get("type")
                
                if interactive_type == "list_reply":
                    # Usuário clicou em uma opção da lista
                    list_reply = interactive.get("list_reply", {})
                    # Usar o título da opção como texto da mensagem
                    text = list_reply.get("title", "")
                elif interactive_type == "button_reply":
                    # Usuário clicou em um botão
                    button_reply = interactive.get("button_reply", {})
                    text = button_reply.get("title", "")
            
            return {
                "type": "message",
                "phone": f"{msg.get('from')}@s.whatsapp.net",  # Normalizar formato
                "message_id": msg.get("id", ""),
                "text": text,
                "from_me": False,
                "push_name": value.get("contacts", [{}])[0].get("profile", {}).get("name", ""),
                "timestamp": msg.get("timestamp"),
                "remote_jid_alt": msg.get('from', ''),
                "interactive_data": msg.get("interactive") if msg_type == "interactive" else None
            }
        
        # Status updates (delivered, read, etc)
        statuses = value.get("statuses", [])
        if statuses:
            status = statuses[0]
            return {
                "type": "status",
                "message_id": status.get("id"),
                "status": status.get("status"),  # sent, delivered, read, failed
                "phone": f"{status.get('recipient_id')}@s.whatsapp.net",
                "timestamp": status.get("timestamp")
            }
        
        return None


def get_whatsapp_adapter(config: WhatsAppBusinessConfig) -> WhatsAppBusinessAdapter:
    """Factory para criar adaptador"""
    return WhatsAppBusinessAdapter(config)

