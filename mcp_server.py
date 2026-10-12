"""
TokenShield Official MCP (Model Context Protocol) Server
Supports both STDIO (Desktop AI apps) and SSE (Server-Sent Events HTTP on any web AI platform).
"""
from typing import Optional
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mcp.server.fastmcp import FastMCP
from gateway import TokenShieldGateway

# Initialize FastMCP Server
mcp = FastMCP("TokenShield", host="0.0.0.0", port=8000)
gateway = TokenShieldGateway(db_path=os.path.join(BASE_DIR, "visual_cache.db"))

@mcp.tool()
def optimize_prompt_tokens(prompt: str, max_aliases: int = 10) -> dict:
    """
    Compresses repetitive entities, database schemas, and long boilerplate
    in a text prompt using Lossless Context Aliasing (CADVS).
    Returns compressed prompt string with alias dictionary and token savings.
    """
    res = gateway.optimize_text(prompt)
    return {
        "compressed_prompt": res["compressed_text"],
        "original_tokens": res["original_tokens_est"],
        "compressed_tokens": res["compressed_tokens_est"],
        "tokens_saved": res["tokens_saved_est"],
        "savings_percentage": f"{res['savings_pct']}%",
        "aliases_used": res["aliases"]
    }

@mcp.tool()
def optimize_vision_image(image_path: str, output_cropped_path: Optional[str] = None) -> dict:
    """
    Optimizes a high-resolution screenshot or document before sending to a Vision model.
    1. Checks local 64-bit perceptual hash (PV-Cache) for 0-TOKEN instant match.
    2. If cache miss, crops empty borders and extracts the Region of Interest (ROI),
       cutting vision token tiles by 70% to 88%.
    """
    if not os.path.exists(image_path):
        return {"error": f"Image file not found at path: {image_path}"}

    if not output_cropped_path:
        base, ext = os.path.splitext(image_path)
        output_cropped_path = f"{base}_tokenshield_crop{ext}"

    res = gateway.optimize_vision(image_path, output_crop_path=output_cropped_path)
    if res.get("source") == "VISUAL_CACHE_HIT":
        return {
            "status": "CACHE_HIT",
            "message": "⚡ ZERO TOKENS! Cached verified response found.",
            "tokens_spent": 0,
            "similarity_pct": f"{res['similarity_pct']}%",
            "cached_response": res["cached_response"]
        }
    else:
        return {
            "status": "CROPPED_ROI",
            "cropped_image_path": output_cropped_path,
            "original_resolution": res["original_size"],
            "cropped_resolution": res["cropped_size"],
            "original_tokens": res["original_tokens_est"],
            "cropped_tokens": res["cropped_tokens_est"],
            "tokens_saved": res["tokens_saved_est"],
            "savings_percentage": f"{res['savings_pct']}%"
        }

@mcp.tool()
def store_visual_cache(image_path: str, verified_response: str) -> dict:
    """
    Stores a verified solution/diagnosis for an image in the local SQLite visual cache.
    Future uploads of identical or similar images will cost 0 TOKENS!
    """
    if not os.path.exists(image_path):
        return {"error": f"Image file not found: {image_path}"}

    gateway.cache_vision_result(image_path, verified_response)
    return {
        "status": "STORED",
        "message": "Visual fingerprint successfully registered. Future queries for this image will cost 0 tokens."
    }

@mcp.tool()
def get_tokenshield_status() -> dict:
    """
    Returns the health status, storage location, and active engines of TokenShield.
    """
    import sqlite3
    db_path = os.path.join(BASE_DIR, "visual_cache.db")
    cached_count = 0
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM visual_cache")
            cached_count = cursor.fetchone()[0]

    return {
        "engine_status": "ONLINE",
        "location": BASE_DIR,
        "active_engines": [
            "Engine 1: Context Aliasing & Dynamic Variable Substitution (CADVS)",
            "Engine 2: Saliency-Based ROI Vision Cropper (ASVPP)",
            "Engine 3: Perceptual Visual Hash Cache (PV-Cache)"
        ],
        "registered_visual_cache_entries": cached_count
    }

def run_sse():
    """Runs MCP in SSE mode on http://0.0.0.0:8000/sse for web AI clients & 1-click URL connections."""
    print("="*65)
    print("⚡ TOKENSHIELD MCP SSE SERVER RUNNING")
    print("="*65)
    print("URL Connection Endpoint: http://localhost:8000/sse")
    print("In Cursor / Windsurf / LibreChat: Choose Type 'SSE' and paste above URL!")
    print("="*65)
    mcp.run(transport="sse")

def main():
    if "--sse" in sys.argv or "--http" in sys.argv:
        run_sse()
    else:
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
