import time
from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from pydantic import BaseModel

app = FastAPI()

# --- CORS Ayarları ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Her yerden gelen isteğe izin ver
    allow_credentials=True,
    allow_methods=["*"], # POST, GET, OPTIONS her şeye izin ver
    allow_headers=["*"],
)
# --- Veri Yapıları (In-memory) ---
# T=48
CATALOG = [{"id": i, "name": f"Order {i}"} for i in range(1, 49)]
idempotency_store: Dict[str, dict] = {} # Key -> Order
rate_limit_store: Dict[str, List[float]] = {} # ClientID -> List of timestamps

# --- Pattern 1: Idempotent POST ---
@app.post("/orders", status_code=201)
async def create_order(request: Request, idempotency_key: str = Header(..., alias="Idempotency-Key")):
    if idempotency_key in idempotency_store:
        return idempotency_store[idempotency_key]
    
    new_order = {"id": f"ord_{len(idempotency_store) + 1}", "status": "created"}
    idempotency_store[idempotency_key] = new_order
    return new_order

# --- Pattern 2: Cursor Pagination ---
@app.get("/orders")
async def get_orders(limit: int = 10, cursor: Optional[int] = 0):
    if cursor >= len(CATALOG):
        return {"items": [], "next_cursor": None}
    
    end = min(cursor + limit, len(CATALOG))
    items = CATALOG[cursor:end]
    next_cursor = end if end < len(CATALOG) else None
    
    return {"items": items, "next_cursor": next_cursor}

# --- Pattern 3: Rate Limiting ---
@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        # Temizlik: 10 saniyeden eski olanları sil
        rate_limit_store[client_id] = [t for t in rate_limit_store.get(client_id, []) if now - t < 10]
        
        if len(rate_limit_store[client_id]) >= 15:
            retry_after = 10 - (now - rate_limit_store[client_id][0])
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests"},
                headers={"Retry-After": str(int(retry_after))}
            )
        
        rate_limit_store[client_id].append(now)
    
    return await call_next(request)
