from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import interactions, chat, hcp

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First CRM — HCP Module API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production to settings.FRONTEND_ORIGIN
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router)
app.include_router(chat.router)
app.include_router(hcp.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "AI-First CRM HCP Module"}
