"""
Tools para o agente interagir com WhatsApp (listas, botões, etc)
"""
from typing import List, Dict, Any


def create_list_message(
    body_text: str,
    button_text: str,
    sections: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Cria mensagem com lista de opções para WhatsApp.
    
    Args:
        body_text: Texto principal da mensagem
        button_text: Texto do botão que abre a lista (ex: "Ver opções")
        sections: Lista de seções, cada uma com title e rows
                  Ex: [{"title": "Categoria", "rows": [{"id": "1", "title": "Opção 1", "description": "Desc"}]}]
    
    Returns:
        Dict com formato padronizado para envio
    """
    # Validar entrada
    if not body_text or not button_text:
        raise ValueError("body_text e button_text são obrigatórios")
    
    if not sections or len(sections) == 0:
        raise ValueError("É necessário pelo menos uma seção")
    
    # Validar seções
    for section in sections:
        if "rows" not in section or len(section["rows"]) == 0:
            raise ValueError("Cada seção precisa ter pelo menos uma row")
        
        # Validar rows
        for row in section["rows"]:
            if "id" not in row or "title" not in row:
                raise ValueError("Cada row precisa ter id e title")
    
    return {
        "type": "list",
        "body": body_text,
        "button": button_text,
        "sections": sections
    }


def create_simple_list(
    body_text: str,
    button_text: str,
    options: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Cria lista simples com opções (sem seções).
    
    Args:
        body_text: Texto principal
        button_text: Texto do botão
        options: Lista de opções
                 Ex: [{"id": "1", "title": "Opção 1", "description": "Descrição opcional"}]
    
    Returns:
        Dict com formato de lista
    """
    if not options or len(options) == 0:
        raise ValueError("É necessário pelo menos uma opção")
    
    if len(options) > 10:
        raise ValueError("Máximo de 10 opções por lista")
    
    # Criar seção única
    sections = [{
        "title": "Opções",
        "rows": options
    }]
    
    return create_list_message(body_text, button_text, sections)


def format_list_as_text(list_data: Dict[str, Any]) -> str:
    """
    Converte lista em texto formatado (fallback para APIs que não suportam listas).
    
    Args:
        list_data: Dados da lista criados por create_list_message
    
    Returns:
        String formatada com as opções
    """
    text = list_data["body"] + "\n\n"
    
    for section in list_data["sections"]:
        if "title" in section and section["title"]:
            text += f"*{section['title']}*\n"
        
        for i, row in enumerate(section["rows"], 1):
            text += f"{i}. {row['title']}"
            if "description" in row and row["description"]:
                text += f" - {row['description']}"
            text += "\n"
        
        text += "\n"
    
    return text.strip()


# Tool schema para o agente
SEND_LIST_TOOL = {
    "type": "function",
    "function": {
        "name": "send_whatsapp_list",
        "description": "Envia uma lista de opções interativa no WhatsApp. Use quando precisar dar múltiplas escolhas ao usuário (ex: menu, opções de serviço, etc). Máximo 10 opções.",
        "parameters": {
            "type": "object",
            "properties": {
                "body_text": {
                    "type": "string",
                    "description": "Texto principal da mensagem explicando as opções"
                },
                "button_text": {
                    "type": "string",
                    "description": "Texto do botão que abre a lista (ex: 'Ver opções', 'Escolher', 'Selecionar')"
                },
                "options": {
                    "type": "array",
                    "description": "Lista de opções disponíveis",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "ID único da opção (ex: '1', '2', 'opt_horario')"
                            },
                            "title": {
                                "type": "string",
                                "description": "Título da opção (máximo 24 caracteres)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Descrição opcional da opção (máximo 72 caracteres)"
                            }
                        },
                        "required": ["id", "title"]
                    },
                    "minItems": 1,
                    "maxItems": 10
                }
            },
            "required": ["body_text", "button_text", "options"]
        }
    }
}
