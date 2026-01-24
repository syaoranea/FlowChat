from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from database import supabase  # seu cliente Supabase já criado

router = APIRouter()

TABLE_CONVERSA = "conversas"  # nome da tabela no Supabase

@router.post("/webhook")
async def webhook(request: Request):
    form = await request.form()

    telefone = form.get("From")
    mensagem = form.get("Body")

    twiml = MessagingResponse()

    if not telefone or not mensagem or not mensagem.strip():
        twiml.message("Erro ao processar mensagem ❌")
        return Response(str(twiml), media_type="application/xml")

    telefone = telefone.replace("whatsapp:", "")
    mensagem = mensagem.strip()

    # busca conversa no Supabase
    response = supabase.table(TABLE_CONVERSA).select("*").eq("telefone_whatsapp", telefone).execute()
    conversa_data = response.data[0] if response.data else None

    # cria nova conversa se não existir
    if not conversa_data:
        supabase.table(TABLE_CONVERSA).insert({
            "telefone_whatsapp": telefone,
            "estado": "aguardando_produto"
        }).execute()
        twiml.message("Olá! 👋 Qual produto você deseja?")
        return Response(str(twiml), media_type="application/xml")

    estado = conversa_data["estado"]

    if estado == "aguardando_produto":
        supabase.table(TABLE_CONVERSA).update({"estado": "aguardando_quantidade"}).eq("telefone_whatsapp", telefone).execute()
        twiml.message("Qual a quantidade?")
        return Response(str(twiml), media_type="application/xml")

    if estado == "aguardando_quantidade":
        supabase.table(TABLE_CONVERSA).update({"estado": "aguardando_prazo"}).eq("telefone_whatsapp", telefone).execute()
        twiml.message("Qual o prazo desejado?")
        return Response(str(twiml), media_type="application/xml")

    if estado == "aguardando_prazo":
        supabase.table(TABLE_CONVERSA).update({"estado": "finalizado"}).eq("telefone_whatsapp", telefone).execute()
        twiml.message("Perfeito! ✅ Pedido enviado para análise.")
        return Response(str(twiml), media_type="application/xml")

    # reset automático
    supabase.table(TABLE_CONVERSA).update({"estado": "aguardando_produto"}).eq("telefone_whatsapp", telefone).execute()
    twiml.message("Vamos começar novamente 😊 Qual produto?")
    return Response(str(twiml), media_type="application/xml")
