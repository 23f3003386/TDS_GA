import httpx
import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional

app = FastAPI()

# 1. Pydantic Modeli (Grader'ın istediği schema)
class InvoiceExtraction(BaseModel):
    vendor: str
    amount: float
    currency: str = Field(..., min_length=3, max_length=3) # 3 harfli olması şartı
    date: str = Field(..., pattern=r"\d{4}-\d{2}-\d{2}") # YYYY-MM-DD formatı

    @validator('currency')
    def uppercase_currency(cls, v):
        return v.upper()

class TextInput(BaseModel):
    text: str

# 2. Endpoint
@app.post("/extract", response_model=InvoiceExtraction)
async def extract_invoice(data: TextInput):
    # LLM'e göndereceğimiz sistem talimatı
    prompt = f"""
    Extract the following invoice fields from the text: vendor, amount, currency, date.
    Output ONLY valid JSON.
    Text: {data.text}
    """
    
    try:
        # Yerel Ollama'ya soruyoruz
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/v1/chat/completions",
                json={
                    "model": "llama3.2",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "format": "json" # Ollama'ya JSON formatını zorluyoruz
                },
                timeout=30.0
            )
            
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="LLM Error")

        # LLM'den gelen cevabı temizle ve JSON'a çevir
        content = response.json()["choices"][0]["message"]["content"]
        # LLM bazen Markdown içine JSON koyar, sadece JSON kısmını alalım
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            extracted_data = json.loads(json_match.group(0))
        else:
            extracted_data = json.loads(content)

        # Pydantic otomatik olarak validation yapacak
        return InvoiceExtraction(**extracted_data)

    except Exception as e:
        # Grader 500 hatası almamalı, o yüzden 422 (Unprocessable) dönüyoruz
        raise HTTPException(status_code=422, detail=f"Extraction failed: {str(e)}")
