import uuid
import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict

app = FastAPI()

# 1. CORS Middleware (Native ve En Üstte)
origins = [
    "https://app-avashw.example.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Debug Middleware (Origin'i loglara yazdırır)
@app.middleware("http")
async def log_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin:
        print(f"DEBUG_ORIGIN: {origin}") # Render loglarına bak, buraya ne düşüyor?
    return await call_next(request)

# Rate Limit Deposu
rate_limits = defaultdict(list)

# 2. Rate Limit & Context (Middleware Stack)
@app.middleware("http")
async def combined_middleware(request: Request, call_next):
    # OPTIONS isteği gelirse rate limit'e takılmasın
    if request.method == "OPTIONS":
        return await call_next(request)

    # --- Rate Limit ---
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        rate_limits[client_id] = [t for t in rate_limits[client_id] if now - t < 10]
        if len(rate_limits[client_id]) >= 15:
            return Response(status_code=429, content="Too Many Requests")
        rate_limits[client_id].append(now)

    # --- Context ---
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "23f3003386@ds.study.iitm.ac.in",
        "request_id": request.state.request_id
    }
