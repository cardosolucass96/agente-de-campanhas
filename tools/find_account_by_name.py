"""
Tool auxiliar para encontrar ID de conta pelo nome
"""
import httpx
import os
from langchain_core.tools import tool
from dotenv import load_dotenv
from default_accounts import DEFAULT_AD_ACCOUNTS, ACCOUNT_ALIASES, get_account_id_by_alias

load_dotenv()

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")


@tool
async def find_account_by_name(account_name: str) -> str:
    """
    Encontra o ID de uma conta de anúncio pelo nome.
    Use quando o usuário mencionar o NOME da conta mas você precisar do ID.
    
    IMPORTANTE: Use esta ferramenta ANTES de chamar get_campaign_insights quando tiver apenas o nome!
    
    Args:
        account_name: Nome da conta (ex: "Vorp Scale", "Vorp Experts")
    
    Retorna o ID da conta (act_xxxxx) ou mensagem de erro se não encontrar.
    """
    # Primeiro, tentar buscar pelo apelido nas contas padrão
    alias_id = get_account_id_by_alias(account_name)
    if alias_id:
        account_info = DEFAULT_AD_ACCOUNTS[alias_id]
        return f"✅ Conta encontrada: *{account_info['name']}*\n🆔 ID: `{account_info['act_id']}`"
    
    # Buscar nas contas padrão pelo nome
    account_name_lower = account_name.lower()
    for acc_id, acc_info in DEFAULT_AD_ACCOUNTS.items():
        if account_name_lower in acc_info['name'].lower():
            return f"✅ Conta encontrada: *{acc_info['name']}*\n🆔 ID: `{acc_info['act_id']}`"
    
    # Não encontrou nas contas padrão
    available = [acc['name'] for acc in DEFAULT_AD_ACCOUNTS.values()]
    return f"❌ Conta '{account_name}' não encontrada.\n\n📋 Contas disponíveis:\n" + "\n".join([f"• {name}" for name in available])
