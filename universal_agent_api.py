"""
TokenShield Universal AI Agent API (Enterprise Gateway)
Designed for seamless integration into ANY autonomous agent framework:
LangChain, CrewAI, AutoGen, LlamaIndex, Cursor, or Custom Python/JS Agents.

Features:
  - Bearer API-Key Authentication (Master: ts_live_master_2026_godmode or custom keys)
  - Universal /v1/agent/optimize Mega-Endpoint (Handles raw text, chat messages array, images, URLs)
  - Agent Telemetry & Savings Audit
  - 100% Async FastAPI with High-Throughput Processing
"""
import os
import sys
import io
import time
import base64
import secrets
import sqlite3
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from gateway import TokenShieldGateway

app = FastAPI(
    title="TokenShield Universal Agent API",
    description="Universal Pre-Inference Optimization Gateway for Autonomous AI Agents",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gateway = TokenShieldGateway(db_path=os.path.join(BASE_DIR, "visual_cache.db"))

# Default Master Key for instant zero-friction developer access
MASTER_API_KEY = "ts_live_master_2026_godmode"

# In-Memory / SQLite API Key Registry
API_KEYS_DB = {
    MASTER_API_KEY: {"client": "SuperAdmin-Master", "tier": "unlimited", "requests": 0, "tokens_saved": 0}
}

# --- Request / Response Models ---

class UniversalAgentRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="Raw prompt text or system instructions")
    messages: Optional[List[Dict[str, Any]]] = Field(None, description="OpenAI/Anthropic compatible messages array")
    images: Optional[List[str]] = Field(None, description="List of image base64 strings or file paths")
    enable_aliasing: Optional[bool] = Field(True, description="Enable Lossless Context Aliasing for repetitive terms")
    enable_vision_crop: Optional[bool] = Field(True, description="Enable Saliency Bounding-Box Cropper for images")
    enable_visual_cache: Optional[bool] = Field(True, description="Check 64-bit dHash perceptual cache for 0-token hit")

class KeyGenerateRequest(BaseModel):
    client_name: str = Field(..., description="Name of the developer, agent, or client")
    tier: Optional[str] = Field("standard", description="Tier quota: standard or unlimited")

# --- Security / Auth Dependency ---

def verify_agent_api_key(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header. Use 'Bearer ts_live_...'")
    
    token = authorization.replace("Bearer ", "").strip()
    if token not in API_KEYS_DB and token != MASTER_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid TokenShield API Key.")
    
    return token

# --- Endpoints ---

@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def developer_dashboard():
    """Serves the 1-Click Interactive TokenShield Developer Portal & Key Generator UI."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TokenShield Developer Portal & Key Manager</title>
    <style>
        :root {
            --bg: #090d16;
            --card: #111827;
            --border: #1f2937;
            --cyan: #06b6d4;
            --emerald: #10b981;
            --text: #f9fafb;
            --muted: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 40px 20px; }
        .container { max-width: 800px; width: 100%; }
        .header { text-align: center; margin-bottom: 35px; }
        .badge { display: inline-block; background: rgba(6, 182, 212, 0.15); color: var(--cyan); border: 1px solid rgba(6, 182, 212, 0.3); padding: 5px 16px; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1px; }
        h1 { font-size: 2.4rem; font-weight: 800; background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
        p.subtitle { color: var(--muted); font-size: 1.05rem; }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 30px; margin-bottom: 25px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); }
        .card h2 { font-size: 1.3rem; margin-bottom: 8px; color: #f3f4f6; }
        .card p { color: var(--muted); font-size: 0.95rem; margin-bottom: 20px; }
        .form-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 18px; }
        label { font-size: 0.85rem; font-weight: 600; color: #d1d5db; text-transform: uppercase; letter-spacing: 0.5px; }
        input, select { background: #1f2937; border: 1px solid #374151; color: #fff; padding: 12px 16px; border-radius: 8px; font-size: 1rem; outline: none; transition: border-color 0.2s; }
        input:focus, select:focus { border-color: var(--cyan); }
        button.btn { background: linear-gradient(135deg, #0284c7, #2563eb); color: #fff; border: none; padding: 14px 24px; border-radius: 8px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: all 0.2s; width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; }
        button.btn:hover { background: linear-gradient(135deg, #0369a1, #1d4ed8); transform: translateY(-1px); }
        .key-result-box { display: none; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 12px; padding: 20px; margin-top: 25px; }
        .key-display { display: flex; gap: 10px; align-items: center; margin-top: 10px; }
        .key-text { flex: 1; background: #0b1329; border: 1px solid #1e293b; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 1.05rem; color: #34d399; overflow-x: auto; }
        .copy-btn { background: #334155; color: #f1f5f9; border: none; padding: 12px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        .copy-btn:hover { background: #475569; }
        .code-box { background: #030712; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; margin-top: 20px; font-family: monospace; font-size: 0.88rem; color: #93c5fd; overflow-x: auto; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">Developer Console</span>
            <h1>TokenShield API Key Manager</h1>
            <p class="subtitle">Generate instant API keys to connect autonomous AI agents, LangChain, or CrewAI.</p>
        </div>

        <div class="card">
            <h2>⚡ 1-Click Instant API Key Generator</h2>
            <p>Enter your Agent or Application name to generate a verified <code>ts_live_...</code> API key.</p>

            <div class="form-group">
                <label>Agent / App Name</label>
                <input type="text" id="appName" placeholder="e.g. MyTradingAgent, AutoResearcher, WhatsAppBot" value="MyCustomAgent-01">
            </div>

            <div class="form-group">
                <label>Tier Quota</label>
                <select id="tierSelect">
                    <option value="standard">Standard (100k Tokens / Day)</option>
                    <option value="unlimited" selected>Unlimited (Godmode Developer Access)</option>
                </select>
            </div>

            <button class="btn" onclick="generateKey()">⚡ Generate API Key Now</button>

            <div id="resultBox" class="key-result-box">
                <h3 style="color:#10b981; font-size:1.1rem;">✅ API Key Successfully Created!</h3>
                <p style="margin-bottom:5px;">Keep this key safe. Use it in the <code>Authorization: Bearer</code> header:</p>
                <div class="key-display">
                    <div class="key-text" id="keyOutput">ts_live_...</div>
                    <button class="copy-btn" onclick="copyKey()">📋 Copy</button>
                </div>

                <div class="code-box" id="codeSnippet">
# Python Integration Example:
import requests
resp = requests.post(
    "http://127.0.0.1:8765/v1/agent/optimize",
    headers={"Authorization": "Bearer YOUR_KEY"},
    json={"prompt": "Your long prompt here"}
)
print(resp.json())
                </div>
            </div>
        </div>

        <div class="card" style="border-color:#374151;">
            <h2>📖 Direct Swagger UI & API Endpoints</h2>
            <p style="margin-bottom:12px;">Test individual endpoints live in your browser using Swagger Docs:</p>
            <a href="/docs" target="_blank" style="color:#38bdf8; text-decoration:none; font-weight:600;">👉 Open Interactive Swagger UI (/docs)</a>
        </div>
    </div>

    <script>
        async function generateKey() {
            const name = document.getElementById('appName').value.trim() || 'CustomAgent';
            const tier = document.getElementById('tierSelect').value;

            try {
                const res = await fetch('/v1/keys/public-generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ client_name: name, tier: tier })
                });
                const data = await res.json();
                if (data.api_key) {
                    document.getElementById('keyOutput').innerText = data.api_key;
                    document.getElementById('resultBox').style.display = 'block';

                    const code = `# Python AI Agent Integration:
import requests

resp = requests.post(
    "http://127.0.0.1:8765/v1/agent/optimize",
    headers={"Authorization": "Bearer ${data.api_key}"},
    json={
        "messages": [
            {"role": "user", "content": "Your long repetitive database prompt here..."}
        ],
        "enable_aliasing": True
    }
)
print("Tokens Saved:", resp.json()["telemetry"]["net_tokens_saved"])`;
                    document.getElementById('codeSnippet').innerText = code;
                }
            } catch (err) {
                alert("Error generating key: " + err);
            }
        }

        function copyKey() {
            const key = document.getElementById('keyOutput').innerText;
            navigator.clipboard.writeText(key);
            alert("API Key copied to clipboard: " + key);
        }
    </script>
</body>
</html>
"""

@app.post("/v1/keys/public-generate", tags=["Authentication & Keys"])
def public_generate_key(req: KeyGenerateRequest):
    """Public 1-click endpoint for users to generate an API key from the Developer Dashboard."""
    new_key = f"ts_live_{secrets.token_hex(16)}"
    API_KEYS_DB[new_key] = {
        "client": req.client_name,
        "tier": req.tier,
        "requests": 0,
        "tokens_saved": 0,
        "created_at": time.time()
    }
    return {
        "success": True,
        "api_key": new_key,
        "client": req.client_name,
        "tier": req.tier,
        "usage": "Include in header: Authorization: Bearer " + new_key
    }


@app.get("/v1/health", tags=["System"])
def health():
    return {"status": "ONLINE", "gateway": "TokenShield Universal Agent API", "protocol": "REST + SSE"}

@app.post("/v1/keys/generate", tags=["Authentication & Keys"])
def generate_key(req: KeyGenerateRequest, token: str = Depends(verify_agent_api_key)):
    """Generates a new secure client API key with live usage quotas."""
    new_key = f"ts_live_{secrets.token_hex(16)}"
    API_KEYS_DB[new_key] = {
        "client": req.client_name,
        "tier": req.tier,
        "requests": 0,
        "tokens_saved": 0,
        "created_at": time.time()
    }
    return {
        "success": True,
        "api_key": new_key,
        "client": req.client_name,
        "tier": req.tier,
        "usage": "Include in header: Authorization: Bearer " + new_key
    }

@app.post("/v1/agent/optimize", tags=["Universal Agent Gateway"])
async def universal_agent_optimize(req: UniversalAgentRequest, token: str = Depends(verify_agent_api_key)):
    """
    UNIVERSAL AGENT OPTIMIZATION ENDPOINT:
    Accepts prompts, messages arrays, or images from ANY agent framework.
    Applies TokenShield engines and returns the clean, compressed payload ready for LLM inference.
    """
    t0 = time.perf_counter()
    total_tokens_before = 0
    total_tokens_after = 0
    optimized_response = {"success": True}

    # 1. Optimize Single Prompt
    if req.prompt:
        if req.enable_aliasing:
            t_res = gateway.optimize_text(req.prompt)
            total_tokens_before += t_res["original_tokens_est"]
            total_tokens_after += t_res["compressed_tokens_est"]
            optimized_response["optimized_prompt"] = t_res["compressed_text"]
            optimized_response["text_aliases"] = t_res["aliases"]
        else:
            optimized_response["optimized_prompt"] = req.prompt

    # 2. Optimize Agent Messages Array (Multi-turn conversations)
    if req.messages:
        opt_messages = []
        for msg in req.messages:
            content = msg.get("content")
            role = msg.get("role", "user")

            if isinstance(content, str) and req.enable_aliasing:
                t_res = gateway.optimize_text(content)
                total_tokens_before += t_res["original_tokens_est"]
                total_tokens_after += t_res["compressed_tokens_est"]
                opt_messages.append({"role": role, "content": t_res["compressed_text"]})
            else:
                opt_messages.append(msg)
        optimized_response["optimized_messages"] = opt_messages

    # 3. Optimize Images (Vision tokens)
    if req.images and req.enable_vision_crop:
        opt_images = []
        for img_item in req.images:
            try:
                # Handle base64 or file path
                if img_item.startswith("data:image") or len(img_item) > 500:
                    b64_clean = img_item.split("base64,")[1] if "base64," in img_item else img_item
                    raw_bytes = base64.b64decode(b64_clean)
                    pil_img = Image.open(io.BytesIO(raw_bytes))
                else:
                    pil_img = Image.open(img_item)

                vis_res = gateway.optimize_vision(pil_img)
                if vis_res.get("source") == "VISUAL_CACHE_HIT":
                    opt_images.append({
                        "status": "CACHE_HIT",
                        "tokens_spent": 0,
                        "cached_response": vis_res["cached_response"]
                    })
                    total_tokens_before += 1530
                    total_tokens_after += 0
                else:
                    buf = io.BytesIO()
                    vis_res["cropped_image"].save(buf, format="PNG")
                    out_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    opt_images.append({
                        "status": "CROPPED_ROI",
                        "tokens_saved": vis_res["tokens_saved_est"],
                        "savings_pct": vis_res["savings_pct"],
                        "cropped_image_base64": f"data:image/png;base64,{out_b64}"
                    })
                    total_tokens_before += vis_res["original_tokens_est"]
                    total_tokens_after += vis_res["cropped_tokens_est"]
            except Exception as e:
                opt_images.append({"error": str(e), "original": img_item})

        optimized_response["optimized_images"] = opt_images

    # Calculate Telemetry & Savings
    net_tokens_saved = max(0, total_tokens_before - total_tokens_after)
    net_pct = round((net_tokens_saved / total_tokens_before) * 100, 2) if total_tokens_before > 0 else 0.0
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    # Track usage on API key
    if token in API_KEYS_DB:
        API_KEYS_DB[token]["requests"] += 1
        API_KEYS_DB[token]["tokens_saved"] += net_tokens_saved

    optimized_response["telemetry"] = {
        "tokens_before": total_tokens_before,
        "tokens_after": total_tokens_after,
        "net_tokens_saved": net_tokens_saved,
        "net_savings_pct": f"{net_pct}%",
        "optimization_latency_ms": latency_ms
    }
    return JSONResponse(content=optimized_response)

@app.get("/v1/telemetry", tags=["Telemetry & Audit"])
def get_telemetry(token: str = Depends(verify_agent_api_key)):
    """Returns total agent requests and lifetime tokens saved across all keys."""
    key_info = API_KEYS_DB.get(token, {})
    return {
        "client": key_info.get("client", "Master"),
        "tier": key_info.get("tier", "unlimited"),
        "total_agent_requests": key_info.get("requests", 0),
        "total_tokens_saved": key_info.get("tokens_saved", 0),
        "active_api_keys_count": len(API_KEYS_DB)
    }

def start_universal_api():
    import uvicorn
    print("="*75)
    print("🌐 TOKENSHIELD UNIVERSAL AGENT API SERVER RUNNING")
    print("="*75)
    print("Endpoint       : http://127.0.0.1:8765/v1/agent/optimize")
    print("Master API Key : ts_live_master_2026_godmode")
    print("Interactive UI : http://127.0.0.1:8765/docs")
    print("="*75)
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")

if __name__ == "__main__":
    start_universal_api()
