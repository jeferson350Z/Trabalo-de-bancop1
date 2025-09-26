from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timezone
from app.config import MONGO_URL, MONGO_DB

_client: Optional[AsyncIOMotorClient] = None

def db():
    """Retorna instância do banco configurado"""
    global _client
    if _client is None:
        if not MONGO_URL:
            raise RuntimeError("Defina MONGO_URL no .env (string do MongoDB Atlas).")
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client[MONGO_DB]

def iso(dt: datetime) -> str:
    """Converte datetime para ISO 8601"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def serialize(doc: dict) -> dict:
    """Serializa documentos MongoDB para JSON"""
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    if "created_at" in d and isinstance(d["created_at"], datetime):
        d["created_at"] = iso(d["created_at"])
    return d
