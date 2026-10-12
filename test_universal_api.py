"""
TokenShield Universal Agent API Live Test Suite
Simulates an Autonomous AI Agent (LangChain / CrewAI / Custom Bot)
connecting via API Key and getting real-time token optimization.
"""
import sys
import os
import json

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, r"D:\TokenShield")
from fastapi.testclient import TestClient
from universal_agent_api import app, MASTER_API_KEY

def run_universal_api_tests():
    print("="*75)
    print("🌐 TOKENSHIELD: UNIVERSAL AGENT API LIVE VERIFICATION")
    print("="*75)

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {MASTER_API_KEY}"}

    # -------------------------------------------------------------
    # TEST 1: Health Check
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Health Endpoint: GET /v1/health ...")
    resp = client.get("/v1/health")
    print(f"  • Status : {resp.status_code} ({resp.reason_phrase})")
    assert resp.status_code == 200, "Health check failed!"

    # -------------------------------------------------------------
    # TEST 2: Generate New Agent API Key
    # -------------------------------------------------------------
    print("\n" + "-"*75)
    print("[TEST 2] Generating Dynamic Agent API Key: POST /v1/keys/generate ...")
    key_resp = client.post(
        "/v1/keys/generate",
        headers=headers,
        json={"client_name": "AutonomousTradingAgent-v4", "tier": "standard"}
    )
    print(f"  • Status : {key_resp.status_code} (Created)")
    key_data = key_resp.json()
    new_agent_key = key_data["api_key"]
    print(f"  • Generated API Key : {new_agent_key}")
    print(f"  • Assigned Client   : {key_data['client']}")
    assert key_resp.status_code == 200, "Key generation failed!"

    # -------------------------------------------------------------
    # TEST 3: Universal Agent Optimization (Prompt + Chat History)
    # -------------------------------------------------------------
    print("\n" + "-"*75)
    print("[TEST 3] Calling Universal Endpoint with New Key: POST /v1/agent/optimize ...")
    agent_headers = {"Authorization": f"Bearer {new_agent_key}"}

    agent_request_payload = {
        "prompt": "Analyze all schema rows for 'GlobalFinancialLiquidityLedger' partition.",
        "messages": [
            {
                "role": "system",
                "content": "You are a database optimizer for 'GlobalFinancialLiquidityLedger' cluster."
            },
            {
                "role": "user",
                "content": (
                    "Please query 'GlobalFinancialLiquidityLedger' and cross-verify "
                    "'GlobalFinancialLiquidityLedger' with yesterday's snapshot. "
                    "Write updates to 'GlobalFinancialLiquidityLedger' audit stream."
                )
            }
        ],
        "enable_aliasing": True
    }

    opt_resp = client.post("/v1/agent/optimize", headers=agent_headers, json=agent_request_payload)
    print(f"  • Status : {opt_resp.status_code} (OK)")
    res_data = opt_resp.json()
    print("  • Telemetry Data :")
    print(json.dumps(res_data["telemetry"], indent=4))
    print("  • Optimized User Message :")
    print(f"    {res_data['optimized_messages'][1]['content']}")
    assert opt_resp.status_code == 200, "Optimization endpoint failed!"

    # -------------------------------------------------------------
    # TEST 4: Telemetry Audit Check
    # -------------------------------------------------------------
    print("\n" + "-"*75)
    print("[TEST 4] Querying Agent Telemetry: GET /v1/telemetry ...")
    telem_resp = client.get("/v1/telemetry", headers=agent_headers)
    print(f"  • Status : {telem_resp.status_code} (OK)")
    print(json.dumps(telem_resp.json(), indent=4))
    assert telem_resp.status_code == 200, "Telemetry failed!"

    # -------------------------------------------------------------
    # TEST 5: Security Rejection Test (Unauthorized Access)
    # -------------------------------------------------------------
    print("\n" + "-"*75)
    print("[TEST 5] Security Check: Rejecting Fake API Key ...")
    bad_resp = client.get("/v1/telemetry", headers={"Authorization": "Bearer fake_key_123"})
    print(f"  • Status : {bad_resp.status_code} (Forbidden - Blocked Successfully!)")
    assert bad_resp.status_code == 403, "Security check failed!"

    print("\n" + "="*75)
    print("🏆 UNIVERSAL AGENT API: 100% OPERATIONAL & VERIFIED!")
    print("="*75)

if __name__ == "__main__":
    run_universal_api_tests()
