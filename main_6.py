import time
import uuid
import collections
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()

# 1. Observability State
START_TIME = time.time()
LOG_BUFFER = collections.deque(maxlen=100) # Son 100 logu tutalım
# Prometheus Counter
REQUEST_COUNTER = Counter('http_requests_total', 'Total HTTP requests')

# 2. Middleware (Tüm endpoint'ler için log ve metrik)
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    path = request.url.path
    
    # Metrik artır
    REQUEST_COUNTER.inc()
    
    # Log kaydet
    log_entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": path,
        "request_id": request_id
    }
    LOG_BUFFER.append(log_entry)
    
    response = await call_next(request)
    return response

# 3. Endpoints
@app.get("/work")
def do_work(n: int):
    # n units of work (placeholder)
    return {"email": "23f3003386@ds.study.iitm.ac.in", "done": n}

@app.get("/metrics")
def get_metrics():
    return PlainTextResponse(generate_latest(REQUEST_COUNTER), media_type=CONTENT_TYPE_LATEST)

@app.get("/healthz")
def health():
    uptime = time.time() - START_TIME
    return {"status": "ok", "uptime_s": round(uptime, 4)}

@app.get("/logs/tail")
def get_logs(limit: int = 10):
    # Son N logu döndür (listeye çevirip dilimle)
    logs = list(LOG_BUFFER)
    return logs[-limit:]
