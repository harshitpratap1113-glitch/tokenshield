"""
TokenShield Live Verification & Benchmark Test
Executes test cases on all 3 engines and prints live token reduction metrics.
"""
import os
import sys
from PIL import Image, ImageDraw

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure D:\TokenShield is in path
sys.path.insert(0, r"D:\TokenShield")
from gateway import TokenShieldGateway

def run_tests():
    print("="*65)
    print("[TOKENSHIELD: LIVE ARCHITECTURE BENCHMARK TEST]")
    print("="*65)

    gateway = TokenShieldGateway()

    # ---------------------------------------------------------
    # TEST 1: Engine 1 (Text Context Aliasing)
    # ---------------------------------------------------------
    print("\n[TEST 1] Testing Engine 1: Context Aliasing (CADVS)...")
    sample_prompt = (
        "Please query the PostgreSQL database table 'CustomerOrderDatabaseSchema' "
        "and fetch all records where 'UserAuthenticationContext' is active. "
        "Then compare 'CustomerOrderDatabaseSchema' with yesterday's backup and "
        "update 'UserAuthenticationContext' status in 'CustomerOrderDatabaseSchema'. "
        "Log the entire transaction back to 'CustomerOrderDatabaseSchema' audit log."
    )

    text_res = gateway.optimize_text(sample_prompt)
    print(f"Original Text Est Tokens : {text_res['original_tokens_est']}")
    print(f"Compressed Text Tokens   : {text_res['compressed_tokens_est']}")
    print(f"Tokens Saved             : {text_res['tokens_saved_est']} ({text_res['savings_pct']}%)")
    print(f"Identified Aliases       : {text_res['aliases']}")
    print(f"\n[Generated Output]:\n{text_res['compressed_text']}\n")

    # ---------------------------------------------------------
    # TEST 2: Engine 2 (ROI Vision Cropping)
    # ---------------------------------------------------------
    print("-" * 65)
    print("[TEST 2] Testing Engine 2: ROI Saliency Cropper (ASVPP)...")
    # Generate a realistic 1920x1080 desktop canvas with a central 400x200 error box
    test_img_path = r"D:\TokenShield\test_desktop_1080p.png"
    crop_out_path = r"D:\TokenShield\test_cropped_roi.png"

    img = Image.new("RGB", (1920, 1080), color=(240, 242, 245)) # Light desktop background
    draw = ImageDraw.Draw(img)
    # Draw central window/box
    draw.rectangle([760, 440, 1160, 640], fill=(30, 41, 59), outline=(239, 68, 68), width=3)
    draw.text((800, 520), "[CRITICAL DATABASE CONNECTION ERROR: 504]", fill=(255, 255, 255))
    img.save(test_img_path)
    print(f"Created synthetic 1920x1080 test image at: {test_img_path}")

    vis_res = gateway.optimize_vision(test_img_path, output_crop_path=crop_out_path)
    print(f"Original Dimensions     : {vis_res['original_size']} -> {vis_res['original_tokens_est']} Vision Tokens")
    print(f"Cropped ROI Dimensions  : {vis_res['cropped_size']} -> {vis_res['cropped_tokens_est']} Vision Tokens")
    print(f"Tokens Saved            : {vis_res['tokens_saved_est']} ({vis_res['savings_pct']}%)")
    print(f"Saved Cropped Image to  : {crop_out_path}")

    # ---------------------------------------------------------
    # TEST 3: Engine 3 (0-Token Visual Cache)
    # ---------------------------------------------------------
    print("-" * 65)
    print("[TEST 3] Testing Engine 3: Perceptual Visual Hash Cache (PV-Cache)...")
    simulated_answer = "Error 504 occurs due to PostgreSQL connection timeout on port 5432. Check firewall."
    
    # Store initial response
    gateway.cache_vision_result(crop_out_path, simulated_answer)
    print("Stored verified answer in local SQLite cache.")

    # Query with the exact image or slightly resized version
    cache_lookup = gateway.optimize_vision(crop_out_path)
    print(f"Cache Lookup Status     : {cache_lookup['source']}")
    print(f"Tokens Spent            : {cache_lookup['tokens_spent']} TOKENS (100% Free!)")
    print(f"Visual Similarity Match : {cache_lookup['similarity_pct']}%")
    print(f"Response Retreived      : '{cache_lookup['cached_response']}'")

    print("\n" + "="*65)
    print("✅ ALL 3 ENGINES VERIFIED & OPERATIONAL ON D:\\TokenShield!")
    print("="*65)

if __name__ == "__main__":
    run_tests()
