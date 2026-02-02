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
    # JSON das credenciais Firebase diretamente (para Vercel)
    firebase_credentials_json: str = ""
    
    # Z-API (substitui Twilio)
    zapi_instance_id: str = ""
    zapi_token: str = ""
    zapi_client_token: str = ""  # Security Token (opcional mas recomendado)
    
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
