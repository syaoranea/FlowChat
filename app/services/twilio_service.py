"""
Serviço de integração com Twilio WhatsApp API.
"""
import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import get_settings

logger = logging.getLogger(__name__)


class TwilioService:
    """Serviço para envio de mensagens via Twilio WhatsApp."""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa cliente Twilio."""
        if self._client is None:
            self._initialize_twilio()
    
    def _initialize_twilio(self):
        """Inicializa o cliente Twilio."""
        settings = get_settings()
        try:
            if settings.twilio_account_sid and settings.twilio_auth_token:
                self._client = Client(
                    settings.twilio_account_sid,
                    settings.twilio_auth_token
                )
                logger.info("Twilio client inicializado com sucesso")
            else:
                logger.warning("Credenciais Twilio não configuradas")
        except Exception as e:
            logger.error(f"Erro ao inicializar Twilio: {e}")
    
    def send_message(self, to: str, body: str) -> Optional[str]:
        """
        Envia mensagem WhatsApp via Twilio.
        
        Args:
            to: Número do destinatário (formato: whatsapp:+5511999999999)
            body: Corpo da mensagem
            
        Returns:
            SID da mensagem se enviada com sucesso, None caso contrário
        """
        settings = get_settings()
        
        if self._client is None:
            logger.error("Cliente Twilio não inicializado")
            return None
        
        try:
            # Garante que o número está no formato correto
            if not to.startswith("whatsapp:"):
                to = f"whatsapp:{to}"
            
            message = self._client.messages.create(
                from_=settings.twilio_whatsapp_from,
                body=body,
                to=to
            )
            
            logger.info(f"Mensagem enviada para {to}: SID={message.sid}")
            return message.sid
            
        except TwilioRestException as e:
            logger.error(f"Erro Twilio ao enviar mensagem: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return None
    
    def send_message_with_template(
        self,
        to: str,
        template_sid: str,
        template_variables: dict
    ) -> Optional[str]:
        """
        Envia mensagem usando template aprovado do WhatsApp.
        
        Args:
            to: Número do destinatário
            template_sid: SID do template
            template_variables: Variáveis do template
            
        Returns:
            SID da mensagem se enviada com sucesso
        """
        settings = get_settings()
        
        if self._client is None:
            logger.error("Cliente Twilio não inicializado")
            return None
        
        try:
            if not to.startswith("whatsapp:"):
                to = f"whatsapp:{to}"
            
            message = self._client.messages.create(
                from_=settings.twilio_whatsapp_from,
                to=to,
                content_sid=template_sid,
                content_variables=template_variables
            )
            
            logger.info(f"Template enviado para {to}: SID={message.sid}")
            return message.sid
            
        except TwilioRestException as e:
            logger.error(f"Erro Twilio ao enviar template: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao enviar template: {e}")
            return None


# Instância global do serviço
twilio_service = TwilioService()
