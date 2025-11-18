from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List
from datetime import datetime

from database import create_document, get_documents
from schemas import Wish

app = FastAPI(title="Birthday Wishes API", version="1.0.0")

# CORS - allow all origins for dev preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WishOut(BaseModel):
    id: str
    name: str
    relation: str | None = None
    message: str
    is_public: bool
    created_at: datetime | None = None


@app.get("/")
async def root() -> Dict[str, str]:
    return {"status": "ok", "message": "Birthday Wishes API"}


@app.get("/test")
async def test_db() -> Dict[str, Any]:
    """Quick DB connectivity test."""
    try:
        # just attempt a simple list on a non-critical collection
        _ = get_documents("wish", {}, limit=1)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/wishes", response_model=List[WishOut])
async def list_public_wishes(limit: int | None = 100):
    try:
        docs = get_documents("wish", {"is_public": True}, limit=limit)
        # sort newest first if created_at exists
        docs.sort(key=lambda d: d.get("created_at", datetime.min), reverse=True)
        result: List[WishOut] = []
        for d in docs:
            result.append(
                WishOut(
                    id=str(d.get("_id")),
                    name=d.get("name", "Someone"),
                    relation=d.get("relation"),
                    message=d.get("message", ""),
                    is_public=bool(d.get("is_public", True)),
                    created_at=d.get("created_at"),
                )
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/wishes", response_model=WishOut, status_code=201)
async def create_wish(payload: Wish):
    try:
        inserted_id = create_document("wish", payload)
        # Build response
        now = datetime.utcnow()
        return WishOut(
            id=inserted_id,
            name=payload.name,
            relation=payload.relation,
            message=payload.message,
            is_public=payload.is_public,
            created_at=now,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
