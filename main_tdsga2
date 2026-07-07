import uuid
import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import statistics

app = FastAPI()

# Strict CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dash-j1ukwz.example.com"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Custom Middleware for Headers
@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    # Format process time to a clean decimal string
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    return response

@app.get("/stats")
async def get_stats(values: str):
    # Parse input
    nums = [float(x) for x in values.split(",")]
    
    # Calculate statistics
    return {
        "email": "23f3003386@ds.study.iitm.ac.in",
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums)
    }
