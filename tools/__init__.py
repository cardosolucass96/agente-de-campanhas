"""
Inicializador do módulo de tools
Importa e expõe todas as ferramentas do agente
"""
from tools.facebook_ad_accounts import get_facebook_ad_accounts
from tools.facebook_business_info import get_facebook_business_info
from tools.whatsapp_sender import send_whatsapp_message
from tools.whatsapp_list import send_whatsapp_list
from tools.whatsapp_buttons import send_whatsapp_buttons
from tools.budget_calculator import calculate_ad_budget
from tools.facebook_campaign_insights import get_campaign_insights
from tools.facebook_all_accounts_insights import get_all_accounts_insights
from tools.find_account_by_name import find_account_by_name
from tools.compare_periods import compare_campaign_periods
from tools.facebook_activity_history import get_activity_history

# Lista de todas as tools disponíveis para o agente
AGENT_TOOLS = [
    get_facebook_ad_accounts,
    get_facebook_business_info,
    send_whatsapp_message,
    send_whatsapp_list,
    send_whatsapp_buttons,
    calculate_ad_budget,
    get_campaign_insights,
    get_all_accounts_insights,
    find_account_by_name,
    compare_campaign_periods,
    get_activity_history
]

__all__ = [
    'AGENT_TOOLS',
    'get_facebook_ad_accounts',
    'get_facebook_business_info',
    'send_whatsapp_message',
    'calculate_ad_budget',
    'get_campaign_insights'
]
