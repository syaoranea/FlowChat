"""
WhatsApp E-commerce Chatbot - Main Application
FastAPI backend com webhook para Twilio WhatsApp.
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Form, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.config import get_settings
from app.handlers.message_handler import message_handler
from app.services.twilio_service import twilio_service

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
    logger.info(f"📞 WhatsApp From: {settings.twilio_whatsapp_from}")
    yield
    logger.info("👋 Encerrando aplicação...")


app = FastAPI(
    title="WhatsApp E-commerce Chatbot",
    description="Backend para chatbot WhatsApp de e-commerce com Twilio e Firebase",
    version="1.0.0",
    lifespan=lifespan
)


# ==================== MODELOS ====================

class WebhookMessage(BaseModel):
    """Modelo para mensagem recebida via webhook."""
    From: str
    Body: str
    MessageSid: Optional[str] = None
    AccountSid: Optional[str] = None
    To: Optional[str] = None
    NumMedia: Optional[str] = "0"


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
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
    AccountSid: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    NumMedia: str = Form("0")
):
    """
    Webhook para receber mensagens do WhatsApp via Twilio.
    
    Twilio envia dados como form-urlencoded.
    Retorna TwiML para resposta.
    """
    logger.info(f"📨 Mensagem recebida de {From}: {Body}")
    
    try:
        # Processa mensagem
        response_text = message_handler.process_message(
            phone=From,
            message=Body
        )
        
        logger.info(f"📤 Resposta para {From}: {response_text[:100]}...")
        
        # Envia resposta via Twilio (opcional, pode usar TwiML)
        # twilio_service.send_message(From, response_text)
        
        # Retorna TwiML para resposta automática
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{escape_xml(response_text)}</Message>
</Response>"""
        
        return Response(
            content=twiml_response,
            status_code=200,
            headers={
                "Content-Type": "text/xml; charset=utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}", exc_info=True)
        
        # Resposta de erro amigável
        error_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Ops! Ocorreu um erro. Por favor, tente novamente em alguns instantes. 😅</Message>
</Response>"""
        
        return Response(
            content=error_response,
            media_type="application/xml"
        )


@app.post("/webhook/whatsapp/status")
async def whatsapp_status_webhook(request: Request):
    """
    Webhook para receber status de mensagens do Twilio.
    """
    form_data = await request.form()
    
    message_sid = form_data.get("MessageSid")
    message_status = form_data.get("MessageStatus")
    
    logger.info(f"📊 Status update - SID: {message_sid}, Status: {message_status}")
    
    return PlainTextResponse("OK")


@app.post("/api/test/message")
async def test_message(data: TestMessage):
    """
    Endpoint para testar processamento de mensagens sem Twilio.
    Útil para desenvolvimento e debug.
    """
    logger.info(f"🧪 Teste - Phone: {data.phone}, Message: {data.message}")
    
    # Garante formato correto do telefone
    phone = data.phone
    if not phone.startswith("whatsapp:"):
        phone = f"whatsapp:{phone}"
    
    try:
        response = message_handler.process_message(
            phone=phone,
            message=data.message
        )
        
        return {
            "success": True,
            "phone": phone,
            "message_received": data.message,
            "response": response
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send")
async def send_message(phone: str, message: str):
    """
    Endpoint para enviar mensagem manualmente.
    """
    if not phone.startswith("whatsapp:"):
        phone = f"whatsapp:{phone}"
    
    sid = twilio_service.send_message(phone, message)
    
    if sid:
        return {"success": True, "message_sid": sid}
    else:
        raise HTTPException(status_code=500, detail="Falha ao enviar mensagem")


# ==================== UTILS ====================

def escape_xml(text: str) -> str:
    """Escapa caracteres especiais para XML."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


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
