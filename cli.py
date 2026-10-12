"""
TokenShield Command-Line Interface (CLI)
Enables 1-command prompt and vision optimization directly from terminal.

Usage:
  python cli.py --text "Your long database query prompt"
  python cli.py --image "path/to/screenshot.png"
  python cli.py --status
"""
import argparse
import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gateway import TokenShieldGateway

def main():
    parser = argparse.ArgumentParser(description="TokenShield: Multi-Modal Pre-Inference Token Optimizer")
    parser.add_argument("--text", "-t", type=str, help="Text prompt to optimize using Context Aliasing (CADVS)")
    parser.add_argument("--image", "-i", type=str, help="Image path to optimize via Saliency Crop & Visual Cache")
    parser.add_argument("--status", "-s", action="store_true", help="Print TokenShield engine and cache status")
    parser.add_argument("--create-key", "-k", type=str, help="Generate a new instant ts_live_... API key for an agent")

    args = parser.parse_args()
    gateway = TokenShieldGateway()

    if not args.text and not args.image and not args.status and not args.create_key:
        parser.print_help()
        sys.exit(0)

    print("="*65)
    print("🛡️  TOKENSHIELD OPTIMIZER")
    print("="*65)

    if args.create_key:
        import secrets
        new_key = f"ts_live_{secrets.token_hex(16)}"
        print("\n⚡ INSTANT AGENT API KEY GENERATED:")
        print(f"Client Name : {args.create_key}")
        print(f"API Key     : {new_key}")
        print(f"Header      : Authorization: Bearer {new_key}")
        print("\nPython Usage:")
        print(f"  requests.post('http://127.0.0.1:8765/v1/agent/optimize', headers={{'Authorization': 'Bearer {new_key}'}}, json={{'prompt': '...'}})")
        print("="*65)
        sys.exit(0)

    if args.status:
        print(f"Status   : ONLINE")
        print(f"Location : {os.path.dirname(os.path.abspath(__file__))}")
        print(f"Engines  : CADVS (Text), ASVPP (Vision Cropper), PV-Cache (dHash)")

    if args.text:
        print("\n[OPTIMIZING TEXT PROMPT...]")
        res = gateway.optimize_text(args.text)
        print(f"Original Tokens   : {res['original_tokens_est']}")
        print(f"Compressed Tokens : {res['compressed_tokens_est']}")
        print(f"Tokens Saved      : {res['tokens_saved_est']} ({res['savings_pct']}%)")
        print(f"Aliases Created   : {res['aliases']}")
        print(f"\n--- OPTIMIZED PROMPT (Copy & Paste to AI) ---\n")
        print(res["compressed_text"])

    if args.image:
        print(f"\n[OPTIMIZING VISION IMAGE: {args.image}...]")
        if not os.path.exists(args.image):
            print(f"Error: Image file not found: {args.image}")
            sys.exit(1)

        base, ext = os.path.splitext(args.image)
        out_crop = f"{base}_tokenshield_crop{ext}"
        res = gateway.optimize_vision(args.image, output_crop_path=out_crop)

        if res.get("source") == "VISUAL_CACHE_HIT":
            print("⚡ ZERO TOKENS! (Visual Cache Hit)")
            print(f"Similarity Match : {res['similarity_pct']}%")
            print(f"Tokens Spent     : 0 Tokens (100% Free)")
            print(f"Cached Answer    : {res['cached_response']}")
        else:
            print("Cropped ROI Saliency Applied:")
            print(f"Original Resolution : {res['original_size']} -> {res['original_tokens_est']} Vision Tokens")
            print(f"Cropped Resolution  : {res['cropped_size']} -> {res['cropped_tokens_est']} Vision Tokens")
            print(f"Vision Tokens Saved : {res['tokens_saved_est']} ({res['savings_pct']}%)")
            print(f"Cropped Image Saved : {out_crop}")

    print("\n" + "="*65)

if __name__ == "__main__":
    main()
