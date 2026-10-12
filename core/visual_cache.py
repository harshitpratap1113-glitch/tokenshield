"""
Engine 3: Perceptual Visual Hash Gateway & 0-Token Cache (PV-Cache)
Computes a robust 64-bit visual fingerprint (dHash/pHash) for any input image.
Matches against a persistent local SQLite database using Hamming Distance.
Produces instant 0-TOKEN cache hits for duplicate/near-duplicate image queries!
"""
import sqlite3
import os
from typing import Optional, Dict, Tuple
from PIL import Image

class VisualCache:
    def __init__(self, db_path: str = r"D:\TokenShield\visual_cache.db", max_hamming_dist: int = 4):
        self.db_path = db_path
        self.max_hamming_dist = max_hamming_dist
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Drop old table if it had the problematic hash_int column
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visual_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash_hex TEXT UNIQUE,
                    response_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @staticmethod
    def compute_dhash(image_input) -> Tuple[str, int]:
        """
        Computes a 64-bit Difference Hash (dHash) by comparing adjacent pixels in a 9x8 grayscale image.
        Extremely fast (~2ms on CPU) and resilient to minor scaling, compression, or noise.
        """
        if isinstance(image_input, str):
            img = Image.open(image_input)
        else:
            img = image_input

        # Convert to 9x8 grayscale
        resized = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(resized.getdata())

        difference = []
        for row in range(8):
            for col in range(8):
                idx = row * 9 + col
                left = pixels[idx]
                right = pixels[idx + 1]
                difference.append(left > right)

        # Convert 64 booleans to 64-bit integer & hex string
        hash_int = 0
        for bit in difference:
            hash_int = (hash_int << 1) | bit

        hash_hex = f"{hash_int:016x}"
        return hash_hex, hash_int

    @staticmethod
    def hamming_distance(h1: int, h2: int) -> int:
        """Counts the number of differing bits between two 64-bit integers."""
        return bin(h1 ^ h2).count('1')

    def lookup(self, image_input) -> Optional[Dict]:
        """
        Looks up image in the perceptual cache.
        Returns cached response if Hamming distance <= max_hamming_dist, else None.
        """
        hash_hex, hash_int = self.compute_dhash(image_input)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT hash_hex, response_text FROM visual_cache")
            rows = cursor.fetchall()

            best_match = None
            min_dist = 999

            for stored_hex, response in rows:
                stored_int = int(stored_hex, 16)
                dist = self.hamming_distance(hash_int, stored_int)
                if dist < min_dist:
                    min_dist = dist
                    best_match = response

            if min_dist <= self.max_hamming_dist:
                similarity = round((1 - (min_dist / 64)) * 100, 1)
                return {
                    "hit": True,
                    "response": best_match,
                    "hamming_distance": min_dist,
                    "similarity_pct": similarity,
                    "hash_hex": hash_hex,
                    "tokens_spent": 0  # 100% token savings!
                }

        return {
            "hit": False,
            "hash_hex": hash_hex,
            "hash_int": hash_int
        }

    def store(self, image_input, response_text: str):
        """Stores a verified LLM response for this visual fingerprint."""
        hash_hex, _ = self.compute_dhash(image_input)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO visual_cache (hash_hex, response_text)
                VALUES (?, ?)
            """, (hash_hex, response_text))
            conn.commit()
