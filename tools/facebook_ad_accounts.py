"""
Tool para buscar contas de anúncio do Facebook
"""
import httpx
import os
from langchain_core.tools import tool
from dotenv import load_dotenv
from default_accounts import DEFAULT_AD_ACCOUNTS, DEFAULT_ACCOUNT_IDS, get_account_name

load_dotenv()

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")


@tool
async def get_facebook_ad_accounts(business_id: str = None) -> str:
    """
    Lista todas as contas de anúncio configuradas (5 contas padrão do Grupo Vorp).
    Use quando o usuário perguntar "quais contas" ou "liste as contas".
    
    IMPORTANTE: Esta ferramenta lista as contas mas NÃO mostra dados de campanhas!
    Para ver campanhas e desempenho, use get_campaign_insights ou get_all_accounts_insights.
    
    Args:
        business_id: (ignorado, mantido por compatibilidade)
    
    Retorna: nome da conta, status (Ativa), saldo e ID de cada conta.
    """
    # Mapeamento de status
    account_status_map = {
        1: 'Ativa',
        2: 'Suspensa',
        3: 'Desativada',
        4: 'Aguardando verificação',
        5: 'Em revisão',
        6: 'Fechada'
    }
    
    # SEMPRE usar contas padrão configuradas
    accounts = [
        {
            "id": info["act_id"],
            "name": info["name"],
            "account_status": 1,  # Ativa
            "currency": "BRL",
            "balance": 0
        }
        for acc_id, info in DEFAULT_AD_ACCOUNTS.items()
    ]
    
    result = f"📊 *{len(accounts)} Contas de Anúncio:*\n\n"
    for idx, acc in enumerate(accounts, 1):
        status_code = acc.get('account_status', 0)
        status_text = account_status_map.get(status_code, f'Desconhecido ({status_code})')
        
        # Formatar valores monetários com 2 casas decimais
        balance = float(acc.get('balance', 0)) / 100
        currency = acc.get('currency', 'BRL')
        currency_symbol = 'R$' if currency == 'BRL' else currency
        
        # Nome da conta (simplificado se muito longo)
        name = acc.get('name', 'Sem nome')
        
        result += f"{idx}. *{name}*\n"
        result += f"   - Status: {status_text}\n"
        result += f"   - Saldo: {currency_symbol} {balance:.2f}\n"
        result += f"   - ACT: `{acc.get('id')}`\n\n"
    
    return result
