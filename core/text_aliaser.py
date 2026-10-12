"""
Engine 1: Context Aliasing & Dynamic Variable Substitution (CADVS)
Reduces prompt tokens by identifying repeated long sequences (entities, variable names,
SQL schema terms, boilerplate) and replacing them with compact variable aliases.
"""
import re
from collections import Counter
from typing import Dict, Tuple, List

class TextAliaser:
    def __init__(self, min_length: int = 12, min_occurrences: int = 2):
        self.min_length = min_length
        self.min_occurrences = min_occurrences

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 characters per token for English/Code."""
        return max(1, len(text) // 4)

    def find_candidates(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Finds repeated candidate phrases (words, camelCase entities, URLs, schemas).
        Returns list of (phrase, frequency, estimated_token_savings).
        """
        # Match tokens, camelCase identifiers, snake_case, or multi-word entities
        pattern = r'\b[A-Za-z0-9_\-\.\/]{' + str(self.min_length) + r',}\b'
        matches = re.findall(pattern, text)
        counts = Counter(matches)

        candidates = []
        for phrase, count in counts.items():
            if count >= self.min_occurrences:
                phrase_tokens = self._estimate_tokens(phrase)
                # Overhead = 1 alias definition (phrase + alias) = ~phrase_tokens + 2
                # Savings = count * phrase_tokens - (phrase_tokens + 2 + count * 1)
                savings = (count - 1) * phrase_tokens - count
                if savings > 0:
                    candidates.append((phrase, count, savings))

        # Sort by maximum token savings descending
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates

    def compress(self, text: str, max_aliases: int = 10) -> Dict:
        """
        Compresses the prompt by replacing top repeated phrases with variable aliases.
        Injects a minimal header definition readable by any LLM.
        """
        candidates = self.find_candidates(text)[:max_aliases]
        if not candidates:
            return {
                "compressed_text": text,
                "aliases": {},
                "original_tokens_est": self._estimate_tokens(text),
                "compressed_tokens_est": self._estimate_tokens(text),
                "tokens_saved_est": 0,
                "savings_pct": 0.0
            }

        alias_map = {}
        for idx, (phrase, _, _) in enumerate(candidates, start=1):
            alias_map[f"$V{idx}"] = phrase

        compressed_body = text
        for var, phrase in alias_map.items():
            # Replace exact occurrences
            compressed_body = compressed_body.replace(phrase, var)

        # Build compact definition header
        header_defs = ", ".join([f"{var}={phrase}" for var, phrase in alias_map.items()])
        header = f"[ALIAS_DEF: {header_defs}]\n"
        final_text = header + compressed_body

        orig_tokens = self._estimate_tokens(text)
        comp_tokens = self._estimate_tokens(final_text)
        saved_tokens = max(0, orig_tokens - comp_tokens)
        savings_pct = round((saved_tokens / orig_tokens) * 100, 2) if orig_tokens > 0 else 0.0

        return {
            "compressed_text": final_text,
            "aliases": alias_map,
            "original_tokens_est": orig_tokens,
            "compressed_tokens_est": comp_tokens,
            "tokens_saved_est": saved_tokens,
            "savings_pct": savings_pct
        }
