"""
Configuração de Integração WhatsApp Business API (Oficial)
"""
from typing import Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()


class WhatsAppBusinessConfig(BaseModel):
    """Configuração para WhatsApp Business API"""
    access_token: str
    phone_number_id: str
    business_account_id: str
    webhook_verify_token: str
    app_secret: Optional[str] = None
    enabled: bool = True
    
    @classmethod
    def from_env(cls):
        return cls(
            access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
            phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
            business_account_id=os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
            webhook_verify_token=os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", ""),
            app_secret=os.getenv("WHATSAPP_APP_SECRET")
        )


# Singleton da config ativa
ACTIVE_WHATSAPP_CONFIG = WhatsAppBusinessConfig.from_env()

