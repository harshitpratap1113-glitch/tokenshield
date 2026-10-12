"""
TokenShield Unified Master Gateway
Coordinates Engine 1 (Text Aliasing), Engine 2 (ROI Vision Cropper),
and Engine 3 (0-Token Visual Cache) into a single high-performance pipeline.
"""
from typing import Optional, Dict
from core.text_aliaser import TextAliaser
from core.vision_cropper import VisionCropper
from core.visual_cache import VisualCache

class TokenShieldGateway:
    def __init__(self, db_path: str = r"D:\TokenShield\visual_cache.db"):
        self.text_aliaser = TextAliaser(min_length=12, min_occurrences=2)
        self.vision_cropper = VisionCropper(padding_ratio=0.10)
        self.visual_cache = VisualCache(db_path=db_path, max_hamming_dist=4)

    def optimize_text(self, prompt: str) -> Dict:
        """Runs Engine 1: Context Aliasing & Variable Substitution."""
        return self.text_aliaser.compress(prompt)

    def optimize_vision(self, image_input, output_crop_path: Optional[str] = None) -> Dict:
        """
        Runs Engine 3 (Visual Cache check).
        If CACHE HIT: returns 0 tokens spent immediately!
        If CACHE MISS: runs Engine 2 (ROI Cropping) to slash resolution tokens.
        """
        # 1. Check Visual Cache first
        cache_result = self.visual_cache.lookup(image_input)
        if cache_result.get("hit"):
            return {
                "source": "VISUAL_CACHE_HIT",
                "cached_response": cache_result["response"],
                "similarity_pct": cache_result["similarity_pct"],
                "tokens_spent": 0,
                "savings_pct": 100.0,
                "message": "⚡ ZERO TOKENS! Result fetched from local perceptual cache in ~2ms."
            }

        # 2. Cache miss -> Crop Saliency
        crop_result = self.vision_cropper.crop_saliency(image_input, output_path=output_crop_path)
        crop_result["source"] = "CROPPED_FOR_INFERENCE"
        return crop_result

    def cache_vision_result(self, image_input, response_text: str):
        """Stores result in Engine 3 cache after LLM response."""
        self.visual_cache.store(image_input, response_text)

    def optimize_all(self, prompt: Optional[str] = None, image_input = None) -> Dict:
        """Unified one-call optimizer for multimodal requests."""
        results = {}
        total_tokens_before = 0
        total_tokens_after = 0

        if prompt:
            text_res = self.optimize_text(prompt)
            results["text"] = text_res
            total_tokens_before += text_res["original_tokens_est"]
            total_tokens_after += text_res["compressed_tokens_est"]

        if image_input:
            vis_res = self.optimize_vision(image_input)
            results["vision"] = vis_res
            if vis_res.get("source") == "VISUAL_CACHE_HIT":
                # Original would have been ~1,530 tokens, now 0
                total_tokens_before += 1530
                total_tokens_after += 0
            else:
                total_tokens_before += vis_res["original_tokens_est"]
                total_tokens_after += vis_res["cropped_tokens_est"]

        net_saved = max(0, total_tokens_before - total_tokens_after)
        net_pct = round((net_saved / total_tokens_before) * 100, 2) if total_tokens_before > 0 else 0.0

        results["summary"] = {
            "total_tokens_before": total_tokens_before,
            "total_tokens_after": total_tokens_after,
            "net_tokens_saved": net_saved,
            "net_savings_pct": net_pct
        }
        return results
