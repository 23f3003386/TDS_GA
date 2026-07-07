import uuid
import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict

app = FastAPI()

# 1. CORS (En dış katman - Preflight'ı bu karşılamalı)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app-avashw.example.com"], # Buraya sınavın URL'ini yaz
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Rate Limit Deposu
rate_limits = defaultdict(list)

# 2. Rate Limiter (OPTIONS isteğini gördüğünde direkt pas geçmeli)
@app.middleware("http")
async def rate_limiter_middleware(request: Request, call_next):
    # Eğer ön kontrol (OPTIONS) ise hiç dokunma, direkt bir sonraki adıma geç
    if request.method == "OPTIONS":
        return await call_next(request)
        
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        rate_limits[client_id] = [t for t in rate_limits[client_id] if now - t < 10]
        
        if len(rate_limits[client_id]) >= 15:
            return Response(status_code=429, content="Too Many Requests")
        
        rate_limits[client_id].append(now)
    
    return await call_next(request)

# 3. Request Context (En iç katman - İş mantığından hemen önce)
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    response.headers["X-Request-ID"] = request_id
    return response

# Endpoint
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "23f3003386@ds.study.iitm.ac.in",
        "request_id": request.state.request_id
    }
