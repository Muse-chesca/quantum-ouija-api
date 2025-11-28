# Quantum Ouija API (ANU QRNG)

A tiny FastAPI service that turns **quantum-random bytes** from **ANU QRNG** into
letters and short "planchette" messages—perfect for a **Custom GPT Action**.

## Endpoints
- `POST /message` → returns a composed message + planchette steps
- `POST /letters` → returns raw quantum letters
- `GET /healthz` → health check

Auth: Add header `x-api-key: YOUR_SECRET_KEY` (set on hosting).

---

## Deploy on Render (Free Tier)

1. Fork or upload this repo to your GitHub (public is required for Render free).
2. Go to **render.com → New → Web Service** and select this repo.
3. Settings:
   - Environment: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Environment Variables:
   - `API_KEY` → set to a long random value (or Render will auto-generate from `render.yaml`)
   - (Optional) `QRNG_URL` → defaults to ANU: `https://qrng.anu.edu.au/API/jsonI.php`

When deployed, you'll get a URL like:
```
https://quantum-ouija-api.onrender.com
```

---

## Test locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_KEY="your-long-random-key"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# test:
curl -s -X POST http://localhost:8000/message  -H "Content-Type: application/json"  -H "x-api-key: your-long-random-key"  -d '{"max_symbols":120,"stop_on":[".", "!", "?"],"min_word_len":1}' | jq
```

---

## Connect to a Custom GPT (Actions)

In ChatGPT:
- **Explore GPTs → Create → Configure → Actions → Add Action (by OpenAPI)**  
- Paste `openapi.yaml` (change `https://YOUR_DEPLOY_URL` to your Render URL).

Action Auth:
- Method: **API key**
- Header name: `x-api-key`
- Value: (exactly the same as your Render `API_KEY`)

### Suggested GPT Instructions
```
You are Quantum Ouija GPT. When the user asks a question or theme,
call the `spellMessage` endpoint with `max_symbols=120` and `stop_on=[".", "!", "?"]`.
Display a short "Planchette Steps" list (3–10 steps) from the API's `steps`,
and then show `Message: "<text>"`. Always use the Action (never fake randomness).
Add the disclaimer: "For entertainment only."
```

---

## Safety / Usage Notes
- This is for entertainment; do not rely on outputs for decisions.
- Keep the API key secret (set as a Render env var and in GPT action auth).
- If you expect high traffic, consider rate limits or keep the GPT unlisted.
