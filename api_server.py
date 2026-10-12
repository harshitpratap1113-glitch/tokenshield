"""
TokenShield Official REST API Server
Interactive Swagger Documentation available at http://127.0.0.1:8765/docs

Endpoints:
  POST /api/v1/optimize/text    -> Lossless Context Aliasing (CADVS)
  POST /api/v1/optimize/vision  -> Saliency ROI Cropper & 0-Token Perceptual Cache
  POST /api/v1/cache/store      -> Register verified diagnosis/answer into visual cache
  GET  /api/v1/status           -> System health, cache volume & engine status
  POST /v1/chat/completions     -> OpenAI-compatible Drop-in Reverse Proxy
"""
import os
import sys
import io
import time
import base64
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from gateway import TokenShieldGateway

# Initialize FastAPI App
app = FastAPI(
    title="TokenShield AI Gateway API",
    description="Multi-Modal Pre-Inference Optimization Gateway for LLMs & Vision APIs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for web apps and frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gateway = TokenShieldGateway(db_path=os.path.join(BASE_DIR, "visual_cache.db"))

# --- Pydantic Request Models ---
class TextOptimizeRequest(BaseModel):
    prompt: str = Field(..., description="Raw text prompt or database query to optimize")
    max_aliases: Optional[int] = Field(10, description="Maximum number of variable aliases to create")

class CacheStoreRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded string of the image")
    verified_response: str = Field(..., description="Verified answer or diagnosis to cache for 0-token lookups")

class VisionJsonRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded string of the image")
    output_crop_name: Optional[str] = Field("cropped_roi.png", description="File name for cropped result")

# --- REST API Endpoints ---

@app.get("/api/v1/status", tags=["System Health"])
def get_status():
    """Returns engine health, active components, and registered visual cache volume."""
    import sqlite3
    db_path = os.path.join(BASE_DIR, "visual_cache.db")
    cache_entries = 0
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM visual_cache")
            cache_entries = cursor.fetchone()[0]

    return {
        "status": "ONLINE",
        "service": "TokenShield Multi-Modal Optimization API",
        "version": "1.0.0",
        "engines": {
            "engine_1": "Context Aliasing & Dynamic Variable Substitution (CADVS)",
            "engine_2": "Saliency-Based Region of Interest (ROI) Cropper (ASVPP)",
            "engine_3": "Perceptual Visual Hash Cache (PV-Cache)"
        },
        "registered_visual_cache_entries": cache_entries
    }

@app.post("/api/v1/optimize/text", tags=["Text Optimization"])
def optimize_text_endpoint(req: TextOptimizeRequest):
    """
    Compresses text prompts by substituting recurring long entity names,
    schemas, and boilerplate with compact variable aliases ($V1, $V2).
    """
    t0 = time.perf_counter()
    res = gateway.optimize_text(req.prompt)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "success": True,
        "compressed_prompt": res["compressed_text"],
        "metrics": {
            "original_tokens_est": res["original_tokens_est"],
            "compressed_tokens_est": res["compressed_tokens_est"],
            "tokens_saved": res["tokens_saved_est"],
            "savings_pct": f"{res['savings_pct']}%",
            "latency_ms": latency_ms
        },
        "aliases_created": res["aliases"]
    }

@app.post("/api/v1/optimize/vision", tags=["Vision Optimization"])
async def optimize_vision_upload(file: UploadFile = File(...)):
    """
    Accepts an uploaded image file (PNG, JPG, WebP), scans the perceptual hash
    for a 0-token cache hit, or crops empty canvas borders to slash vision tokens.
    """
    t0 = time.perf_counter()
    try:
        image_bytes = await file.read()
        pil_img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    crop_res = gateway.optimize_vision(pil_img)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    if crop_res.get("source") == "VISUAL_CACHE_HIT":
        return {
            "status": "VISUAL_CACHE_HIT",
            "tokens_spent": 0,
            "savings_pct": "100.0%",
            "similarity_pct": f"{crop_res['similarity_pct']}%",
            "cached_response": crop_res["cached_response"],
            "latency_ms": latency_ms,
            "message": "⚡ ZERO TOKENS! Result retrieved from local perceptual cache."
        }

    # If cropped, encode cropped image to base64 for return
    buf = io.BytesIO()
    crop_res["cropped_image"].save(buf, format="PNG")
    cropped_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "status": "CROPPED_ROI",
        "original_resolution": crop_res["original_size"],
        "cropped_resolution": crop_res["cropped_size"],
        "original_tokens_est": crop_res["original_tokens_est"],
        "cropped_tokens_est": crop_res["cropped_tokens_est"],
        "tokens_saved": crop_res["tokens_saved_est"],
        "savings_pct": f"{crop_res['savings_pct']}%",
        "cropped_image_base64": f"data:image/png;base64,{cropped_b64}",
        "latency_ms": latency_ms
    }

@app.post("/api/v1/cache/store", tags=["Vision Cache"])
def store_cache_endpoint(req: CacheStoreRequest):
    """
    Registers an image and its verified answer into the local visual cache.
    Future queries for this image will cost 0 TOKENS!
    """
    try:
        b64_clean = req.image_base64
        if "base64," in b64_clean:
            b64_clean = b64_clean.split("base64,")[1]
        raw_bytes = base64.b64decode(b64_clean)
        pil_img = Image.open(io.BytesIO(raw_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")

    gateway.cache_vision_result(pil_img, req.verified_response)
    return {
        "success": True,
        "message": "Visual fingerprint registered. Future identical or similar queries will cost 0 tokens."
    }

def start_api():
    import uvicorn
    print("="*65)
    print("🚀 TOKENSHIELD REST API & SWAGGER SERVER RUNNING")
    print("="*65)
    print("Base URL       : http://127.0.0.1:8765")
    print("Interactive UI : http://127.0.0.1:8765/docs (Swagger UI)")
    print("Alternative UI : http://127.0.0.1:8765/redoc")
    print("="*65)
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")

if __name__ == "__main__":
    start_api()
