"""
Configuração de Integração WhatsApp
Suporta Evolution API e WhatsApp Business API
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()


class WhatsAppProvider(str, Enum):
    """Provedores de WhatsApp disponíveis"""
    EVOLUTION = "evolution"
    WHATSAPP_BUSINESS = "whatsapp_business"


class WhatsAppConfig(BaseModel):
    """Configuração base para WhatsApp"""
    provider: WhatsAppProvider
    enabled: bool = True


class EvolutionConfig(WhatsAppConfig):
    """Configuração específica para Evolution API"""
    provider: WhatsAppProvider = WhatsAppProvider.EVOLUTION
    api_url: str
    api_key: str
    instance: str
    
    @classmethod
    def from_env(cls):
        return cls(
            api_url=os.getenv("EVOLUTION_API_URL", ""),
            api_key=os.getenv("EVOLUTION_API_KEY", ""),
            instance=os.getenv("EVOLUTION_INSTANCE", "")
        )


class WhatsAppBusinessConfig(WhatsAppConfig):
    """Configuração específica para WhatsApp Business API"""
    provider: WhatsAppProvider = WhatsAppProvider.WHATSAPP_BUSINESS
    access_token: str
    phone_number_id: str
    business_account_id: str
    webhook_verify_token: str
    app_secret: Optional[str] = None
    
    @classmethod
    def from_env(cls):
        return cls(
            access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
            phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
            business_account_id=os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
            webhook_verify_token=os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", ""),
            app_secret=os.getenv("WHATSAPP_APP_SECRET")
        )


# Configuração global - selecionar qual provider usar
def get_active_whatsapp_config() -> WhatsAppConfig:
    """
    Retorna a configuração ativa baseado no .env
    """
    provider = os.getenv("WHATSAPP_PROVIDER", "evolution").lower()
    
    if provider == "whatsapp_business":
        return WhatsAppBusinessConfig.from_env()
    else:
        return EvolutionConfig.from_env()


# Singleton da config ativa
ACTIVE_WHATSAPP_CONFIG = get_active_whatsapp_config()
