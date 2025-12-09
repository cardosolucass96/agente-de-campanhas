"""
Tool para enviar botões interativos no WhatsApp (máximo 3 botões)
"""
from langchain_core.tools import tool
from typing import List, Dict

# Variável global para armazenar os botões pendentes
pending_buttons = None

@tool
async def send_whatsapp_buttons(
    body_text: str,
    buttons: List[Dict[str, str]],
    footer_text: str = None
) -> str:
    """
    Envia botões interativos no WhatsApp (máximo 3 botões).
    Use para oferecer 1-3 opções rápidas após apresentar dados/análise.
    
    QUANDO USAR:
    - Após mostrar desempenho → oferecer 1-2 ações rápidas
    - Após comparações → oferecer próximos insights
    - Quando há 2-3 opções simples de escolha
    
    IMPORTANTE:
    - Máximo 3 botões
    - Título do botão: máximo 20 caracteres
    - Use para sugestões rápidas, NÃO para menus grandes
    
    Args:
        body_text: Texto principal da mensagem (pergunta/sugestão)
        buttons: Lista de botões, cada um com:
            - id: identificador único (ex: "1", "2", "3")
            - title: texto do botão (máx 20 caracteres)
        footer_text: Texto opcional no rodapé (pequeno, discreto)
    
    Exemplos:
        buttons=[
            {"id": "1", "title": "📊 Ver CTR"},
            {"id": "2", "title": "📈 Comparar"}
        ]
    
    Returns:
        Confirmação de que os botões foram preparados
    """
    global pending_buttons
    
    # Validações
    if not buttons or len(buttons) > 3:
        return "❌ Erro: Você deve fornecer de 1 a 3 botões (máximo 3)"
    
    if not body_text or len(body_text) < 1:
        return "❌ Erro: body_text não pode estar vazio"
    
    # Validar cada botão
    for i, btn in enumerate(buttons):
        if "id" not in btn or "title" not in btn:
            return f"❌ Erro: Botão {i+1} deve ter 'id' e 'title'"
        
        if len(btn["title"]) > 20:
            return f"❌ Erro: Botão '{btn['title']}' tem mais de 20 caracteres (máx: 20)"
    
    print(f"🔘 FERRAMENTA send_whatsapp_buttons CHAMADA!")
    print(f"   body_text: {body_text}")
    print(f"   buttons: {buttons}")
    if footer_text:
        print(f"   footer_text: {footer_text}")
    
    # Armazenar na variável global
    pending_buttons = {
        "type": "button",
        "body": {"text": body_text},
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {
                        "id": btn["id"],
                        "title": btn["title"]
                    }
                }
                for btn in buttons
            ]
        }
    }
    
    if footer_text:
        pending_buttons["footer"] = {"text": footer_text}
    
    num_buttons = len(buttons)
    return f"✅ {num_buttons} botão(ões) preparado(s) para envio. Os botões serão anexados à mensagem."
