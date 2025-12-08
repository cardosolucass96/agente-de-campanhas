"""
Contas de anúncio padrão do Grupo Vorp
"""

DEFAULT_AD_ACCOUNTS = {
    "611132268404060": {
        "name": "Vorp Scale",
        "id": "611132268404060",
        "act_id": "act_611132268404060"
    },
    "766769481380236": {
        "name": "Vorp Edu (MasterMind)",
        "id": "766769481380236",
        "act_id": "act_766769481380236"
    },
    "343431767385008": {
        "name": "Vorp Edu (Eventos)",
        "id": "343431767385008",
        "act_id": "act_343431767385008"
    },
    "4429673283720645": {
        "name": "Vorp Tech",
        "id": "4429673283720645",
        "act_id": "act_4429673283720645"
    },
    "2190755121126699": {
        "name": "CDA. MatchSales",
        "id": "2190755121126699",
        "act_id": "act_2190755121126699"
    }
}

# Lista ordenada dos IDs
DEFAULT_ACCOUNT_IDS = [
    "611132268404060",  # Vorp Scale
    "766769481380236",  # Vorp Edu (MasterMind)
    "343431767385008",  # Vorp Edu (Eventos)
    "4429673283720645",  # Vorp Tech
    "2190755121126699"   # CDA. MatchSales
]

# Mapeamento de apelidos para IDs
ACCOUNT_ALIASES = {
    "scale": "611132268404060",
    "vorp scale": "611132268404060",
    "mastermind": "766769481380236",
    "edu mastermind": "766769481380236",
    "vorp edu mastermind": "766769481380236",
    "eventos": "343431767385008",
    "edu eventos": "343431767385008",
    "vorp edu eventos": "343431767385008",
    "tech": "4429673283720645",
    "vorp tech": "4429673283720645",
    "matchsales": "2190755121126699",
    "match sales": "2190755121126699",
    "cda": "2190755121126699",
    "cda matchsales": "2190755121126699"
}


def get_account_name(account_id: str) -> str:
    """Retorna o nome da conta dado o ID"""
    # Remove prefixo 'act_' se presente
    clean_id = account_id.replace("act_", "")
    return DEFAULT_AD_ACCOUNTS.get(clean_id, {}).get("name", f"Conta {clean_id}")


def get_account_id_by_alias(alias: str) -> str:
    """Retorna o ID da conta dado um apelido"""
    return ACCOUNT_ALIASES.get(alias.lower())


def get_all_accounts():
    """Retorna todas as contas padrão"""
    return DEFAULT_AD_ACCOUNTS
