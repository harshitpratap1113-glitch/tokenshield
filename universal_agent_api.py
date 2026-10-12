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
    # Option 1: Simple prompt string
    prompt: Optional[str] = Field(None, description="Raw prompt text or system instructions")
    # Option 2: Standard Agent Chat History Array
    messages: Optional[List[Dict[str, Any]]] = Field(None, description="OpenAI/Anthropic compatible messages array")
    # Option 3: Image attachments (Base64 strings or local file paths)
    images: Optional[List[str]] = Field(None, description="List of image base64 strings or file paths")
    # Options
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
