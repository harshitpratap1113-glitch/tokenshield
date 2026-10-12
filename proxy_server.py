"""
TokenShield Universal Drop-in Reverse Proxy Server
OpenAI-compatible local API proxy running on http://127.0.0.1:8765/v1

Any developer using OpenAI SDK, LangChain, or Cursor can simply change ONE line:
  client = OpenAI(base_url="http://127.0.0.1:8765/v1")

TokenShield intercepts the request, compresses text & crops images on the fly,
logs live token savings, and forwards the lightweight request to the real LLM provider!
"""
import os
import sys
import io
import base64
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import urllib.request
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from gateway import TokenShieldGateway

app = FastAPI(title="TokenShield Drop-in Proxy Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gateway = TokenShieldGateway(db_path=os.path.join(BASE_DIR, "visual_cache.db"))

@app.get("/health")
def health_check():
    return {"status": "ONLINE", "service": "TokenShield Universal Proxy", "port": 8765}

@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "gpt-4o", "object": "model", "owned_by": "tokenshield-proxy"},
            {"id": "gpt-4o-mini", "object": "model", "owned_by": "tokenshield-proxy"},
            {"id": "claude-3-5-sonnet", "object": "model", "owned_by": "tokenshield-proxy"}
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: Optional[str] = Header(None)):
    t0 = time.perf_counter()
    body = await request.json()
    messages = body.get("messages", [])

    total_tokens_saved = 0
    optimized_messages = []

    for msg in messages:
        content = msg.get("content")
        role = msg.get("role")

        # 1. Plain text content
        if isinstance(content, str):
            opt = gateway.optimize_text(content)
            if opt["tokens_saved_est"] > 0:
                total_tokens_saved += opt["tokens_saved_est"]
                optimized_messages.append({"role": role, "content": opt["compressed_text"]})
            else:
                optimized_messages.append(msg)

        # 2. Multimodal array content (Vision: text + image_url)
        elif isinstance(content, list):
            new_content = []
            for part in content:
                if part.get("type") == "text":
                    opt = gateway.optimize_text(part.get("text", ""))
                    total_tokens_saved += opt["tokens_saved_est"]
                    new_content.append({"type": "text", "text": opt["compressed_text"]})

                elif part.get("type") == "image_url":
                    img_data = part.get("image_url", {}).get("url", "")
                    if img_data.startswith("data:image"):
                        try:
                            # Decode base64 image
                            header_part, base64_data = img_data.split(",", 1)
                            raw_bytes = base64.b64decode(base64_data)
                            pil_img = Image.open(io.BytesIO(raw_bytes))

                            # Run TokenShield Engine 2 (Saliency Cropping)
                            crop_res = gateway.optimize_vision(pil_img)
                            total_tokens_saved += crop_res.get("tokens_saved_est", 0)

                            # Re-encode cropped image
                            buf = io.BytesIO()
                            crop_res["cropped_image"].save(buf, format="PNG")
                            new_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                            new_url = f"data:image/png;base64,{new_b64}"
                            new_content.append({"type": "image_url", "image_url": {"url": new_url}})
                        except Exception as e:
                            # Fallback if decode fails
                            new_content.append(part)
                    else:
                        new_content.append(part)
                else:
                    new_content.append(part)
            optimized_messages.append({"role": role, "content": new_content})
        else:
            optimized_messages.append(msg)

    body["messages"] = optimized_messages
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000

    print(f"[TOKENSHIELD PROXY] Intercepted Request | Saved: ~{total_tokens_saved} Tokens | Latency: {latency_ms:.2f}ms")

    # If user provided an upstream API key, forward to OpenAI
    if authorization and authorization.startswith("Bearer sk-"):
        try:
            req_data = json.dumps(body).encode("utf-8")
            forward_req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=req_data,
                headers={"Content-Type": "application/json", "Authorization": authorization}
            )
            with urllib.request.urlopen(forward_req, timeout=30) as resp:
                upstream_resp = json.loads(resp.read().decode("utf-8"))
                return JSONResponse(content=upstream_resp)
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": f"Upstream proxy forwarding failed: {str(e)}"})

    # Offline / Local Inspection Mode (Returns optimized payload metrics)
    return JSONResponse(content={
        "id": "tokenshield-mock-cmpl-01",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.get("model", "tokenshield-optimized"),
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": f"[TokenShield Optimizer Active]: Request successfully intercepted & optimized. Tokens saved: ~{total_tokens_saved}."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens_saved": total_tokens_saved,
            "optimization_latency_ms": round(latency_ms, 2)
        },
        "optimized_payload": body
    })

def start_server():
    import uvicorn
    print("="*65)
    print("🛡️  TOKENSHIELD DROP-IN PROXY GATEWAY RUNNING")
    print("="*65)
    print("Endpoint : http://127.0.0.1:8765/v1")
    print("One-Line Integration:")
    print("  client = OpenAI(base_url='http://127.0.0.1:8765/v1')")
    print("="*65)
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")

if __name__ == "__main__":
    start_server()
