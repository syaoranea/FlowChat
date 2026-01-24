from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import supabase, get_table_data  # agora usamos Supabase
from routers.webhook import router as webhook_router
from routers.auth import router as auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)
app.include_router(auth_router)

# Removemos a parte do SQLAlchemy
# @app.on_event("startup")
# def startup():
#     Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    data = get_table_data("test")  # exemplo usando Supabase
    return {"status": "ok", "test_data": data}
