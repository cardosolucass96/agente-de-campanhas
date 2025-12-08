"""
Tool para enviar listas interativas no WhatsApp
"""
from typing import List, Dict
from langchain_core.tools import tool
from whatsapp_tools import create_simple_list, format_list_as_text


# Armazenar lista pendente globalmente
pending_list = {"phone": None, "list_data": None}


@tool
async def send_whatsapp_list(
    body_text: str,
    button_text: str,
    options: List[Dict[str, str]]
) -> str:
    """
    Prepara uma lista interativa para envio no WhatsApp.
    Use esta ferramenta quando precisar dar múltiplas escolhas ao usuário.
    
    Args:
        body_text: Texto explicativo sobre as opções (ex: "Escolha uma das opções abaixo:")
        button_text: Texto do botão que abre a lista (ex: "Ver opções", "Escolher")
        options: Lista de dicionários com id, title e description opcional
                 Ex: [{"id": "1", "title": "Opção 1", "description": "Desc"}]
    
    Returns:
        Confirmação de que a lista foi preparada
    
    Example:
        await send_whatsapp_list(
            body_text="Como posso ajudar você hoje?",
            button_text="Escolher opção",
            options=[
                {"id": "1", "title": "Consultar campanhas", "description": "Ver status das suas campanhas"},
                {"id": "2", "title": "Criar nova campanha", "description": "Configurar uma nova campanha"},
                {"id": "3", "title": "Suporte", "description": "Falar com atendente"}
            ]
        )
    """
    print(f"🔧 FERRAMENTA send_whatsapp_list CHAMADA!")
    print(f"   body_text: {body_text}")
    print(f"   button_text: {button_text}")
    print(f"   options: {options}")
    
    try:
        # Validar número de opções
        if len(options) > 10:
            return "❌ Erro: Máximo de 10 opções permitidas. Por favor, reduza o número de opções."
        
        if len(options) == 0:
            return "❌ Erro: É necessário pelo menos uma opção."
        
        # Validar comprimento dos títulos
        for opt in options:
            if len(opt.get("title", "")) > 24:
                return f"❌ Erro: O título '{opt['title']}' excede 24 caracteres."
            if "description" in opt and len(opt["description"]) > 72:
                return f"❌ Erro: A descrição de '{opt['title']}' excede 72 caracteres."
        
        # Criar lista
        list_data = create_simple_list(body_text, button_text, options)
        
        # Armazenar para envio posterior (será enviada pelo main.py)
        global pending_list
        pending_list["list_data"] = list_data
        
        # Retornar versão em texto como fallback
        text_version = format_list_as_text(list_data)
        
        return f"✅ Lista preparada para envio. Versão texto:\n\n{text_version}"
        
    except Exception as e:
        return f"❌ Erro ao criar lista: {str(e)}"


def get_pending_list() -> Dict:
    """Retorna e limpa lista pendente"""
    global pending_list
    data = pending_list.copy()
    pending_list = {"phone": None, "list_data": None}
    return data
