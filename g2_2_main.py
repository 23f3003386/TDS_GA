from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt

app = FastAPI()

# The RS256 Public Key provided
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-vvhjltla.apps.exam.local"

class TokenRequest(BaseModel):
    token: str

@app.post("/verify")
async def verify_token(req: TokenRequest):
    try:
        # PyJWT handles signature, issuer, audience, and exp validation automatically
        payload = jwt.decode(
            req.token, 
            PUBLIC_KEY, 
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=ISSUER
        )
        
        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud")
        }
    except jwt.PyJWTError:
        # Return 401 with the required structure for invalid tokens
        return JSONResponse(status_code=401, content={"valid": False})
