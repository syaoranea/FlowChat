"""
WhatsApp E-commerce Chatbot - Main Application
FastAPI backend com webhook para Z-API WhatsApp.
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings
from app.handlers.message_handler import message_handler
from app.services.zapi_service import zapi_service


# Configuração de logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    logger.info("🚀 Iniciando WhatsApp E-commerce Bot...")
    logger.info(f"📱 Empresa: {settings.company_name}")
    logger.info(f"📞 Z-API Instance: {settings.zapi_instance_id[:8]}..." if settings.zapi_instance_id else "📞 Z-API: não configurado")
    yield
    logger.info("👋 Encerrando aplicação...")


app = FastAPI(
    title="WhatsApp E-commerce Chatbot",
    description="Backend para chatbot WhatsApp de e-commerce com Z-API e Firebase",
    version="2.0.0",
    lifespan=lifespan
)


# ==================== MODELOS ====================

class ZAPIWebhookMessage(BaseModel):
    """Modelo para mensagem recebida via webhook Z-API."""
    phone: str
    messageId: Optional[str] = None
    fromMe: bool = False
    momment: Optional[int] = None  # timestamp
    type: Optional[str] = None  # ReceivedCallback, MessageStatusCallback, etc
    text: Optional[dict] = None  # {"message": "texto"}
    # Outros tipos de mensagem
    image: Optional[dict] = None
    audio: Optional[dict] = None
    video: Optional[dict] = None
    document: Optional[dict] = None
    sticker: Optional[dict] = None
    contact: Optional[dict] = None
    location: Optional[dict] = None


class TestMessage(BaseModel):
    """Modelo para teste de mensagem."""
    phone: str
    message: str


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Endpoint raiz - health check."""
    return {
        "status": "online",
        "service": "WhatsApp E-commerce Chatbot",
        "company": settings.company_name,
        "version": "2.0.0",
        "provider": "Z-API"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/zapi/status")
async def zapi_status():
    """Verifica status da conexão Z-API."""
    status = zapi_service.get_status()
    return status


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Webhook para receber mensagens do WhatsApp via Z-API.
    
    Z-API envia dados como JSON.
    Formato esperado:
    {
        "phone": "5511999999999",
        "fromMe": false,
        "messageId": "...",
        "text": {"message": "texto da mensagem"},
        "type": "ReceivedCallback"
    }
    """
    try:
        data = await request.json()
        
        # Log para debug
        logger.info(f"📨 Webhook recebido: {data}")
        
        # Ignora mensagens enviadas pelo próprio bot
        if data.get("fromMe", False):
            logger.info("⏭️ Ignorando mensagem própria (fromMe=true)")
            return JSONResponse(content={"status": "ignored", "reason": "fromMe"})
        
        # Ignora callbacks de status
        callback_type = data.get("type", "")
        if callback_type in ["MessageStatusCallback", "StatusCallback", "DeliveryCallback"]:
            logger.info(f"⏭️ Ignorando callback de status: {callback_type}")
            return JSONResponse(content={"status": "ignored", "reason": "status_callback"})
        
        # Extrai número do remetente
        phone = data.get("phone", "")
        if not phone:
            logger.warning("⚠️ Webhook sem número de telefone")
            return JSONResponse(content={"status": "error", "reason": "no_phone"}, status_code=400)
        
        # Extrai mensagem de texto
        message = ""
        if data.get("text") and isinstance(data["text"], dict):
            message = data["text"].get("message", "")
        elif data.get("text") and isinstance(data["text"], str):
            message = data["text"]
        
        # Se não for texto, pode ser mídia
        if not message:
            if data.get("image"):
                message = "[Imagem recebida]"
            elif data.get("audio"):
                message = "[Áudio recebido]"
            elif data.get("video"):
                message = "[Vídeo recebido]"
            elif data.get("document"):
                message = "[Documento recebido]"
            elif data.get("sticker"):
                message = "[Figurinha recebida]"
            elif data.get("contact"):
                message = "[Contato recebido]"
            elif data.get("location"):
                message = "[Localização recebida]"
            else:
                logger.warning(f"⚠️ Tipo de mensagem não suportado: {data}")
                return JSONResponse(content={"status": "ignored", "reason": "unsupported_type"})
        
        logger.info(f"📨 Mensagem de {phone}: {message}")
        
        # Processa mensagem
        response_text = message_handler.process_message(
            phone=phone,
            message=message
        )
        
        logger.info(f"📤 Resposta para {phone}: {response_text[:100]}...")
        
        # Envia resposta via Z-API
        message_id = zapi_service.send_message(phone, response_text)
        
        if message_id:
            return JSONResponse(content={
                "status": "success",
                "messageId": message_id
            })
        else:
            logger.error(f"❌ Falha ao enviar resposta para {phone}")
            return JSONResponse(content={
                "status": "error",
                "reason": "send_failed"
            }, status_code=500)
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "reason": str(e)},
            status_code=500
        )


@app.post("/api/test/message")
async def test_message(data: TestMessage):
    """
    Endpoint para testar processamento de mensagens sem Z-API.
    Útil para desenvolvimento e debug.
    """
    logger.info(f"🧪 Teste - Phone: {data.phone}, Message: {data.message}")
    
    try:
        response = message_handler.process_message(
            phone=data.phone,
            message=data.message
        )
        
        return {
            "success": True,
            "phone": data.phone,
            "message_received": data.message,
            "response": response
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send")
async def send_message(phone: str, message: str):
    """
    Endpoint para enviar mensagem manualmente via Z-API.
    """
    message_id = zapi_service.send_message(phone, message)
    
    if message_id:
        return {"success": True, "message_id": message_id}
    else:
        raise HTTPException(status_code=500, detail="Falha ao enviar mensagem")


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
