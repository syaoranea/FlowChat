from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models.usuario import Usuario
from core.security import hash_senha, criar_token

router = APIRouter(prefix="/auth")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(dados: dict, db: Session = Depends(get_db)):
    email = dados.get("email")
    senha = dados.get("senha")

    if not email or not senha:
        raise HTTPException(status_code=400, detail="Email e senha são obrigatórios")

    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    # 🔹 CRIA USUÁRIO AUTOMÁTICO (DEV)
    if not usuario:
        usuario = Usuario(
            email=email,
            senha_hash=hash_senha(senha)
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    
    
    if usuario.senha_hash != hash_senha(senha):
        raise HTTPException(status_code=401, detail="Login inválido")

    return {
        "access_token": criar_token({"sub": usuario.email})
    }
