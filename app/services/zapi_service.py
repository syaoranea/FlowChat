"""
Serviço de integração com Z-API para WhatsApp.
Z-API usa WhatsApp Web para envio de mensagens.
"""
import logging
from typing import Optional
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class ZAPIService:
    """Serviço para envio de mensagens via Z-API."""
    
    _instance = None
    _base_url = None
    _client_token = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa configurações da Z-API."""
        if self._base_url is None:
            self._initialize_zapi()
    
    def _initialize_zapi(self):
        """Inicializa configurações da Z-API."""
        settings = get_settings()
        try:
            if settings.zapi_instance_id and settings.zapi_token:
                self._base_url = f"https://api.z-api.io/instances/{settings.zapi_instance_id}/token/{settings.zapi_token}"
                self._client_token = settings.zapi_client_token
                logger.info("Z-API configurado com sucesso")
            else:
                logger.warning("Credenciais Z-API não configuradas")
        except Exception as e:
            logger.error(f"Erro ao configurar Z-API: {e}")
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normaliza número de telefone para formato Z-API.
        Remove formatação e prefixos.
        
        Args:
            phone: Número em qualquer formato
            
        Returns:
            Número limpo (ex: 5511999999999)
        """
        # Remove prefixo whatsapp: se existir (legado Twilio)
        if phone.startswith("whatsapp:"):
            phone = phone[9:]
        
        # Remove caracteres não numéricos
        phone = ''.join(filter(str.isdigit, phone))
        
        # Se começar com 0, remove
        if phone.startswith("0"):
            phone = phone[1:]
        
        # Adiciona código do Brasil se não tiver código de país
        if len(phone) <= 11:
            phone = f"55{phone}"
        
        return phone
    
    def send_message(self, to: str, body: str) -> Optional[str]:
        """
        Envia mensagem WhatsApp via Z-API.
        
        Args:
            to: Número do destinatário (qualquer formato)
            body: Corpo da mensagem
            
        Returns:
            messageId se enviada com sucesso, None caso contrário
        """
        if self._base_url is None:
            logger.error("Z-API não configurado")
            return None
        
        try:
            phone = self._normalize_phone(to)
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Adiciona Client-Token se configurado
            if self._client_token:
                headers["Client-Token"] = self._client_token
            
            payload = {
                "phone": phone,
                "message": body
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self._base_url}/send-text",
                    headers=headers,
                    json=payload
                )
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messageId", data.get("id"))
                logger.info(f"Mensagem enviada para {phone}: ID={message_id}")
                return message_id
            else:
                logger.error(f"Erro Z-API: {response.status_code} - {response.text}")
                return None
                
        except httpx.TimeoutException:
            logger.error(f"Timeout ao enviar mensagem para {to}")
            return None
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return None
    
    def get_status(self) -> dict:
        """
        Verifica status da instância Z-API.
        
        Returns:
            Dict com status da conexão
        """
        if self._base_url is None:
            return {"connected": False, "error": "Z-API não configurado"}
        
        try:
            headers = {}
            if self._client_token:
                headers["Client-Token"] = self._client_token
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self._base_url}/status",
                    headers=headers
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"connected": False, "error": response.text}
                
        except Exception as e:
            return {"connected": False, "error": str(e)}


# Instância global do serviço
zapi_service = ZAPIService()
