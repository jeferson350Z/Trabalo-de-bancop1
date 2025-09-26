from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Body, HTTPException
from bson import ObjectId
from datetime import datetime, timezone
from app.database import db, serialize
from app.ws_manager import manager

router = APIRouter()

@router.get("/rooms/{room}/messages")
async def get_messages(
    room: str, limit: int = Query(20, ge=1, le=100), before_id: str | None = Query(None)
):
    query = {"room": room}
    if before_id:
        try:
            query["_id"] = {"$lt": ObjectId(before_id)}
        except Exception:
            raise HTTPException(status_code=400, detail="before_id inválido")

    cursor = db()["messages"].find(query).sort("_id", -1).limit(limit)
    docs = [serialize(d) async for d in cursor]
    docs.reverse()
    next_cursor = docs[0]["_id"] if docs else None
    return {"items": docs, "next_cursor": next_cursor}

@router.post("/rooms/{room}/messages", status_code=201)
async def post_message(room: str, username: str = Body(...), content: str = Body(...)):
    content = content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Mensagem não pode ser vazia")

    doc = {
        "room": room,
        "username": username[:50],
        "content": content[:1000],
        "created_at": datetime.now(timezone.utc),
    }
    res = await db()["messages"].insert_one(doc)
    doc["_id"] = res.inserted_id
    return serialize(doc)

@router.websocket("/ws/{room}")
async def ws_room(ws: WebSocket, room: str):
    await manager.connect(room, ws)
    try:
        # histórico inicial
        cursor = db()["messages"].find({"room": room}).sort("_id", -1).limit(20)
        items = [serialize(d) async for d in cursor]
        items.reverse()
        await ws.send_json({"type": "history", "items": items})

        while True:
            payload = await ws.receive_json()
            username = str(payload.get("username", "anon"))[:50]
            content = str(payload.get("content", "")).strip()
            if not content:
                continue
            doc = {
                "room": room,
                "username": username,
                "content": content,
                "created_at": datetime.now(timezone.utc),
            }
            res = await db()["messages"].insert_one(doc)
            doc["_id"] = res.inserted_id
            await manager.broadcast(room, {"type": "message", "item": serialize(doc)})
    except WebSocketDisconnect:
        manager.disconnect(room, ws)
