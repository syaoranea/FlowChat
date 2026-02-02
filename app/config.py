"""
Configurações da aplicação usando variáveis de ambiente.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente."""
    
    # Firebase
    firebase_project_id: str = "flowchat-72383"
    firebase_credentials_path: str = "./firebase-credentials.json"
    
    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    
    # App
    company_name: str = "Minha Empresa"
    orcamento_validade_dias: int = 10
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
