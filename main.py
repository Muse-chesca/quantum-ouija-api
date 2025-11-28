import os, string
from typing import List, Literal
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, conint
import httpx

API_KEY = os.getenv("API_KEY")  # set this in hosting (Render: Environment)
QRNG_URL = os.getenv("QRNG_URL", "https://qrng.anu.edu.au/API/jsonI.php")
QRNG_MAX = 256  # max bytes per fetch

app = FastAPI(
    title="Quantum Ouija API",
    version="1.0.0",
    description="Generate 'planchette' letters and sentences using quantum-random bytes (ANU QRNG)."
)

ALPHABET = list(string.ascii_uppercase) + [" ", ".", ",", "?", "!"]  # 31 symbols

class LettersRequest(BaseModel):
    n: conint(gt=0, le=500) = Field(60, description="How many symbols to draw")

class LettersResponse(BaseModel):
    symbols: List[str]
    raw_bytes: List[int]

class MessageRequest(BaseModel):
    max_symbols: conint(gt=0, le=600) = 120
    stop_on: List[Literal[".", "!", "?"]] = ["."]
    min_word_len: conint(ge=1, le=12) = 1

class MessageResponse(BaseModel):
    message: str
    steps: List[str]
    raw_bytes: List[int]

def _require_auth(x_api_key: str | None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

async def _qrng_bytes(n: int) -> List[int]:
    out = []
    async with httpx.AsyncClient(timeout=20) as client:
        need = n
        while need > 0:
            take = min(QRNG_MAX, need)
            r = await client.get(QRNG_URL, params={"length": take, "type": "uint8"})
            r.raise_for_status()
            data = r.json()
            if not data or not data.get("success"):
                raise HTTPException(status_code=502, detail="QRNG upstream error")
            out.extend(data["data"])
            need -= take
    return out

def _bytes_to_symbols(bts: List[int]) -> List[str]:
    symbols = []
    for b in bts:
        idx = b % len(ALPHABET)
        symbols.append(ALPHABET[idx])
    return symbols

@app.post("/letters", response_model=LettersResponse, summary="Draw quantum letters")
async def letters(req: LettersRequest, x_api_key: str | None = Header(default=None)):
    _require_auth(x_api_key)
    bts = await _qrng_bytes(req.n)
    syms = _bytes_to_symbols(bts)
    return LettersResponse(symbols=syms, raw_bytes=bts)

@app.post("/message", response_model=MessageResponse, summary="Compose a quantum message")
async def message(req: MessageRequest, x_api_key: str | None = Header(default=None)):
    _require_auth(x_api_key)
    bts = await _qrng_bytes(req.max_symbols)
    syms = _bytes_to_symbols(bts)

    text = []
    steps = []
    for i, s in enumerate(syms):
        steps.append(f"Step {i+1}: {s}")
        text.append(s)
        if s in req.stop_on and len(text) >= 8:
            break

    msg = "".join(text)
    while "  " in msg:
        msg = msg.replace("  ", " ")
    msg = msg.strip(" .,?!")
    if not msg.endswith(tuple(req.stop_on)):
        msg += "."

    return MessageResponse(message=msg, steps=steps, raw_bytes=bts)

@app.get("/healthz")
def healthz():
    return {"ok": True}
