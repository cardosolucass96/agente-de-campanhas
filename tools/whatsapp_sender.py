"""
Tool para enviar mensagens via WhatsApp usando Evolution API
"""
import httpx
import os
import re
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE")


def format_message_for_whatsapp(content: str) -> str:
    """
    Formata mensagem removendo Markdown e convertendo para formatação WhatsApp.
    """
    # Converter Markdown headers ## -> negrito
    content = re.sub(r'###?\s+(.*?)(?:\n|$)', r'*\1*\n', content)
    
    # Markdown bold ** -> WhatsApp bold *
    content = re.sub(r'\*\*(.*?)\*\*', r'*\1*', content)
    
    # Markdown code ` -> remover
    content = re.sub(r'`(.*?)`', r'\1', content)
    
    # Remover links markdown [texto](url) -> texto (url)
    content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', content)
    
    return content.strip()


@tool
async def send_whatsapp_message(phone: str, message: str) -> str:
    """
    Envia uma mensagem via WhatsApp usando a Evolution API.
    A mensagem é automaticamente formatada para WhatsApp.
    
    Args:
        phone: Número do telefone com código do país (ex: 5511999999999)
        message: Texto da mensagem a ser enviada
    
    Returns:
        String confirmando o envio ou descrevendo o erro
    """
    try:
        # OBRIGATÓRIO: Formatar mensagem para WhatsApp
        formatted_message = format_message_for_whatsapp(message)
        
        base_url = EVOLUTION_API_URL.replace('/manager', '')
        url = f"{base_url}/message/sendText/{EVOLUTION_INSTANCE}"
        
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY
        }
        
        payload = {
            "number": phone,
            "text": formatted_message
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()
        
        if response.status_code == 201:
            return f"Mensagem enviada com sucesso para {phone}"
        else:
            return f"Erro ao enviar mensagem: {data}"
    except Exception as e:
        return f"Erro ao enviar mensagem via WhatsApp: {str(e)}"
