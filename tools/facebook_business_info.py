"""
Tool para buscar informações do Business Manager do Facebook
"""
import httpx
import os
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")


@tool
async def get_facebook_business_info(business_id: str) -> str:
    """
    Busca informações gerais de um Business Manager do Facebook.
    
    Args:
        business_id: ID do Business Manager
    
    Returns:
        String com informações do Business Manager
    """
    try:
        url = f"https://graph.facebook.com/v21.0/{business_id}"
        
        params = {
            "access_token": FACEBOOK_ACCESS_TOKEN,
            "fields": "id,name,created_time,link,verification_status"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
        
        if "error" in data:
            return f"Erro ao buscar informações: {data['error'].get('message', 'Erro desconhecido')}"
        
        result = f"Business Manager: {data.get('name')}\n"
        result += f"ID: {data.get('id')}\n"
        result += f"Criado em: {data.get('created_time', 'N/A')}\n"
        result += f"Status de verificação: {data.get('verification_status', 'N/A')}\n"
        
        return result
    except Exception as e:
        return f"Erro ao buscar informações do Business: {str(e)}"
