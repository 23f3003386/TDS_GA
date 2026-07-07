import uuid
import time
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict

app = FastAPI()

@app.middleware("http")
async def debug_headers(request: Request, call_next):
    # Sadece OPTIONS isteklerini izleyelim
    if request.method == "OPTIONS":
        print(f"DEBUG: OPTIONS Request from Origin: {request.headers.get('origin')}")
    return await call_next(request)

# 1. CORS Middleware (En Dış Katman)
# Exam page origin'i buraya eklemeyi unutma, yoksa grader seni reddeder.
origins = [
    "https://app-avashw.example.com",
    "https://exam.sanand.workers.dev" # Buraya sınav sayfasının URL'ini ekle
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Rate Limit Deposu
rate_limits = defaultdict(list)

# 2. Rate Limit Middleware
@app.middleware("http")
async def rate_limiter_middleware(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        # 10 saniyelik pencere
        rate_limits[client_id] = [t for t in rate_limits[client_id] if now - t < 10]
        
        if len(rate_limits[client_id]) >= 15: # 15 Req / 10s
            return Response(status_code=429, content="Too Many Requests")
        
        rate_limits[client_id].append(now)
    
    return await call_next(request)

# 3. Request Context Middleware
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    # 1. ID'yi belirle
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    
    # 2. STATE'İ ÖNCE SET ET (Endpoint bunun sayesinde okuyabilecek)
    request.state.request_id = request_id
    
    # 3. İsteği endpoint'e gönder
    response = await call_next(request)
    
    # 4. Header'ı cevaba ekle
    response.headers["X-Request-ID"] = request_id
    
    return response

# Endpoint
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "23f3003386@ds.study.iitm.ac.in", # Grader'ın beklediği tam adres
        "request_id": request.state.request_id
    }
