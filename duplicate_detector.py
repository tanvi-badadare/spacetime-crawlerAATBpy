import re
import hashlib
import threading


class DuplicateDetector:
    """
    Detects exact duplicates (SHA256 hash) and near-duplicates using shingle-based
    fingerprinting with Jaccard similarity. Uses k-shingles (k consecutive words)
    to create fingerprints for comparison.
    """
    def __init__(self, k_shingle: int = 3, fingerprint_size: int = 20, similarity_threshold: float = 0.5):
        self.k_shingle = k_shingle
        self.fingerprint_size = fingerprint_size
        self.similarity_threshold = similarity_threshold
        self._seen_hashes = set()  # Exact duplicate detection
        self._fingerprints = []  # Near-duplicate fingerprints
        self._lock = threading.Lock()  # Thread-safe for multithreaded crawler

    def _normalize_text(self, text: str) -> str:
        if not text or not text.strip():
            return ""
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def _text_to_words(self, text: str) -> list[str]:
        if not text:
            return []
        words = re.findall(r"[a-z0-9]+", text.lower())
        return words

    def _get_content_hash(self, normalized_text: str) -> str:
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    def _get_shingles(self, words: list[str]) -> list[tuple]:
        if len(words) < self.k_shingle:
            return []
        shingles = []
        for i in range(len(words) - self.k_shingle + 1):
            shingle = tuple(words[i : i + self.k_shingle])
            shingles.append(shingle)
        return shingles

    def _hash_shingle(self, shingle: tuple) -> int:
        data = " ".join(shingle).encode("utf-8")
        h = hashlib.sha256(data).hexdigest()[:16]
        return int(h, 16)

    def _compute_fingerprint(self, words: list[str]) -> frozenset[int]:
        # Create fingerprint from smallest hash values (minhash approach)
        shingles = self._get_shingles(words)
        if not shingles:
            return frozenset()

        hashes = [self._hash_shingle(s) for s in shingles]
        sorted_hashes = sorted(hashes)
        fingerprint = frozenset(sorted_hashes[: self.fingerprint_size])
        return fingerprint

    def _jaccard_similarity(self, fp_a: frozenset[int], fp_b: frozenset[int]) -> float:
        # Jaccard similarity through intersection size / union size
        if not fp_a and not fp_b:
            return 1.0
        if not fp_a or not fp_b:
            return 0.0
        inter = len(fp_a & fp_b)
        union = len(fp_a | fp_b)
        return inter / union if union else 0.0

    def _is_near_duplicate(self, fingerprint: frozenset[int]) -> bool:
        if not fingerprint:
            return False
        for existing in self._fingerprints:
            sim = self._jaccard_similarity(fingerprint, existing)
            if sim >= self.similarity_threshold:
                return True
        return False

    def is_duplicate(self, text: str) -> bool:
        normalized = self._normalize_text(text)
        if not normalized:
            return True
        content_hash = self._get_content_hash(normalized)
        words = self._text_to_words(normalized)
        fingerprint = self._compute_fingerprint(words)
        with self._lock:
            if content_hash in self._seen_hashes:
                return True
            if self._is_near_duplicate(fingerprint):
                return True
            self._seen_hashes.add(content_hash)
            self._fingerprints.append(fingerprint)
            return False
