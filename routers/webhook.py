from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import SessionLocal
from models.conversa import Conversa
from twilio.twiml.messaging_response import MessagingResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    form = await request.form()

    telefone = form.get("From")
    mensagem = form.get("Body")

    twiml = MessagingResponse()

    if not telefone or not mensagem or not mensagem.strip():
        twiml.message("Erro ao processar mensagem ❌")
        return Response(str(twiml), media_type="application/xml")

    telefone = telefone.replace("whatsapp:", "")
    mensagem = mensagem.strip()

    conversa = db.query(Conversa).filter_by(
        telefone_whatsapp=telefone
    ).first()

    if not conversa:
        conversa = Conversa(
            telefone_whatsapp=telefone,
            estado="aguardando_produto"
        )
        db.add(conversa)
        db.commit()

        twiml.message("Olá! 👋 Qual produto você deseja?")
        return Response(str(twiml), media_type="application/xml")

    if conversa.estado == "aguardando_produto":
        conversa.estado = "aguardando_quantidade"
        db.commit()

        twiml.message("Qual a quantidade?")
        return Response(str(twiml), media_type="application/xml")

    if conversa.estado == "aguardando_quantidade":
        conversa.estado = "aguardando_prazo"
        db.commit()

        twiml.message("Qual o prazo desejado?")
        return Response(str(twiml), media_type="application/xml")

    if conversa.estado == "aguardando_prazo":
        conversa.estado = "finalizado"
        db.commit()

        twiml.message("Perfeito! ✅ Pedido enviado para análise.")
        return Response(str(twiml), media_type="application/xml")

    # reset automático
    conversa.estado = "aguardando_produto"
    db.commit()

    twiml.message("Vamos começar novamente 😊 Qual produto?")
    return Response(str(twiml), media_type="application/xml")
