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
    
    accounts = []
    
    # Buscar dados reais de cada conta na API do Facebook
    async with httpx.AsyncClient(timeout=30.0) as client:
        for acc_id, info in DEFAULT_AD_ACCOUNTS.items():
            try:
                # Buscar dados da conta na API
                url = f"https://graph.facebook.com/v21.0/{info['act_id']}"
                params = {
                    "fields": "name,account_status,currency,balance,amount_spent,spend_cap",
                    "access_token": FACEBOOK_ACCESS_TOKEN
                }
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    accounts.append({
                        "id": info["act_id"],
                        "name": info["name"],  # Usar nome configurado
                        "account_status": data.get("account_status", 1),
                        "currency": data.get("currency", "BRL"),
                        "balance": int(data.get("balance", 0)),  # Em centavos
                        "amount_spent": int(data.get("amount_spent", 0)),  # Em centavos
                        "spend_cap": int(data.get("spend_cap", 0)) if data.get("spend_cap") else None
                    })
                else:
                    print(f"⚠️ Erro ao buscar {info['act_id']}: {response.status_code}")
                    # Fallback para dados básicos
                    accounts.append({
                        "id": info["act_id"],
                        "name": info["name"],
                        "account_status": 1,
                        "currency": "BRL",
                        "balance": 0,
                        "amount_spent": 0,
                        "spend_cap": None
                    })
            except Exception as e:
                print(f"⚠️ Erro ao buscar {info['act_id']}: {e}")
                accounts.append({
                    "id": info["act_id"],
                    "name": info["name"],
                    "account_status": 1,
                    "currency": "BRL",
                    "balance": 0,
                    "amount_spent": 0,
                    "spend_cap": None
                })
    
    result = f"📊 *{len(accounts)} Contas de Anúncio:*\n\n"
    for idx, acc in enumerate(accounts, 1):
        status_code = acc.get('account_status', 0)
        status_text = account_status_map.get(status_code, f'Desconhecido ({status_code})')
        
        # Formatar valores monetários (API retorna em centavos)
        balance = float(acc.get('balance', 0)) / 100
        amount_spent = float(acc.get('amount_spent', 0)) / 100
        spend_cap = acc.get('spend_cap')
        
        currency = acc.get('currency', 'BRL')
        currency_symbol = 'R$' if currency == 'BRL' else currency
        
        # Nome da conta (simplificado se muito longo)
        name = acc.get('name', 'Sem nome')
        
        result += f"{idx}. *{name}*\n"
        result += f"   - Status: {status_text}\n"
        result += f"   - Saldo devedor: {currency_symbol} {balance:.2f}\n"
        result += f"   - Total gasto: {currency_symbol} {amount_spent:.2f}\n"
        
        if spend_cap:
            spend_cap_value = float(spend_cap) / 100
            remaining = spend_cap_value - amount_spent
            result += f"   - Limite: {currency_symbol} {spend_cap_value:.2f}\n"
            result += f"   - Disponível: {currency_symbol} {remaining:.2f}\n"
        
        result += f"   - ACT: `{acc.get('id')}`\n\n"
    
    return result
