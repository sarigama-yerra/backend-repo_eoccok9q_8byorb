import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import create_document, get_documents, db
from schemas import Wish

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Birthday Wishes API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

# Wishes Endpoints
class WishResponse(BaseModel):
    id: str
    name: str
    relation: Optional[str] = None
    message: str
    is_public: bool
    created_at: Optional[str] = None

@app.get("/api/wishes", response_model=List[WishResponse])
def list_wishes(limit: int = 50, public_only: bool = True):
    try:
        filt = {"is_public": True} if public_only else {}
        docs = get_documents("wish", filt, limit=limit)
        results = []
        for d in docs:
            results.append(WishResponse(
                id=str(d.get("_id")),
                name=d.get("name", "Anonymous"),
                relation=d.get("relation"),
                message=d.get("message", ""),
                is_public=bool(d.get("is_public", True)),
                created_at=(d.get("created_at").isoformat() if d.get("created_at") else None)
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wishes", status_code=201)
def create_wish(payload: Wish):
    try:
        wish_id = create_document("wish", payload)
        return {"id": wish_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
