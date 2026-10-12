"""
TokenShield REST API Live Verification Suite
Executes live HTTP requests against all FastAPI endpoints using TestClient.
"""
import sys
import os
import io
import json
from PIL import Image, ImageDraw

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, r"D:\TokenShield")
from fastapi.testclient import TestClient
from api_server import app

def run_api_tests():
    print("="*75)
    print("🚀 TOKENSHIELD: LIVE REST API VERIFICATION SUITE")
    print("="*75)

    client = TestClient(app)

    # -------------------------------------------------------------
    # TEST 1: GET /api/v1/status
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Health Endpoint: GET /api/v1/status ...")
    resp = client.get("/api/v1/status")
    print(f"  • HTTP Status Code : {resp.status_code} ({resp.reason_phrase})")
    print(f"  • Response Payload  :")
    print(json.dumps(resp.json(), indent=4))
    assert resp.status_code == 200, "Health endpoint failed!"

    # -------------------------------------------------------------
    # TEST 2: POST /api/v1/optimize/text
    # -------------------------------------------------------------
    print("\n" + "-"*75)
    print("[TEST 2] Testing Text Endpoint: POST /api/v1/optimize/text ...")
    text_payload = {
        "prompt": (
            "Select all records from 'OrderProcessingMicroservicePartition' where "
            "'OrderProcessingMicroservicePartition' status is active. "
            "Then update 'OrderProcessingMicroservicePartition' metadata table."
        ),
        "max_aliases": 5
    }
    resp = client.post("/api/v1/optimize/text", json=text_payload)
    print(f"  • HTTP Status Code : {resp.status_code} ({resp.reason_phrase})")
    data = resp.json()
    print(f"  • Tokens Saved     : {data['metrics']['tokens_saved']} ({data['metrics']['savings_pct']})")
    print(f"  • Latency          : {data['metrics']['latency_ms']} ms")
    print(f"  • Compressed Body  :\n    {data['compressed_prompt']}")
    assert resp.status_code == 200, "Text optimization endpoint failed!"

    # -------------------------------------------------------------
    # TEST 3: POST /api/v1/optimize/vision (Multipart File Upload)
    # -------------------------------------------------------------
    print("\n" + "-"*75)
    print("[TEST 3] Testing Vision Endpoint: POST /api/v1/optimize/vision (File Upload) ...")
    # Generate test image in memory
    img = Image.new("RGB", (1200, 800), color=(240, 242, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([400, 250, 800, 550], fill=(15, 23, 42))
    draw.text((450, 380), "[DATABASE TIMEOUT ERROR 504]", fill=(255, 255, 255))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("screenshot.png", buf.getvalue(), "image/png")}
    resp = client.post("/api/v1/optimize/vision", files=files)
    print(f"  • HTTP Status Code : {resp.status_code} ({resp.reason_phrase})")
    vis_data = resp.json()
    print(f"  • Engine Action    : {vis_data['status']}")
    print(f"  • Resolution Drop  : {vis_data['original_resolution']} -> {vis_data['cropped_resolution']}")
    print(f"  • Tokens Saved     : {vis_data['tokens_saved']} ({vis_data['savings_pct']})")
    print(f"  • Latency          : {vis_data['latency_ms']} ms")
    assert resp.status_code == 200, "Vision endpoint failed!"

    # -------------------------------------------------------------
    # TEST 4: Swagger Documentation: GET /docs
    # -------------------------------------------------------------
    print("\n" + "-"*75)
    print("[TEST 4] Testing Swagger UI Documentation: GET /docs ...")
    resp = client.get("/docs")
    print(f"  • HTTP Status Code : {resp.status_code} ({resp.reason_phrase})")
    print(f"  • Interactive Docs : Verified Live Swagger UI Ready!")
    assert resp.status_code == 200, "Swagger UI docs failed!"

    print("\n" + "="*75)
    print("🏆 ALL REST API ENDPOINTS VERIFIED & 100% OPERATIONAL!")
    print("="*75)

if __name__ == "__main__":
    run_api_tests()
