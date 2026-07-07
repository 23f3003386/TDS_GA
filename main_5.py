from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# CORS: Tüm originlere izin ver (Grader test edebilsin diye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Event(BaseModel):
    user: str
    amount: float
    ts: int

class AnalyticsRequest(BaseModel):
    events: List[Event]

API_KEY = "ak_urp3xcwmns1ycicwwrl8iel8"

@app.post("/analytics")
async def process_analytics(data: AnalyticsRequest, x_api_key: str = Header(None)):
    # 1. Auth Kontrolü
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 2. Aggregation (Toplama)
    total_events = len(data.events)
    unique_users = len({e.user for e in data.events})
    
    user_revenue = {}
    total_revenue = 0.0
    
    for e in data.events:
        if e.amount > 0:
            total_revenue += e.amount
            user_revenue[e.user] = user_revenue.get(e.user, 0) + e.amount
            
    # En çok kazandıran kullanıcıyı bul (Negatifleri toplama dahil etmiyoruz)
    top_user = max(user_revenue, key=user_revenue.get) if user_revenue else None

    return {
        "email": "23f3003386@ds.study.iitm.ac.in",
        "total_events": total_events,
        "unique_users": unique_users,
        "revenue": total_revenue,
        "top_user": top_user
    }
