import math
import re
from collections import Counter
from typing import Iterable, List


def tokenize(text: str) -> List[str]:
    """Simple whitespace and punctuation tokenizer."""
    return re.findall(r"\w+", text.lower())


class BM25:
    """Minimal BM25 implementation for small corpora."""

    def __init__(self, corpus: Iterable[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = [tokenize(doc) for doc in corpus]
        self.doc_freqs = []
        self.doc_lens = []
        self.idf = {}
        self.avgdl = 0.0
        self._initialize()

    def _initialize(self) -> None:
        df = Counter()
        for doc in self.documents:
            freqs = Counter(doc)
            self.doc_freqs.append(freqs)
            self.doc_lens.append(len(doc))
            for word in freqs:
                df[word] += 1
        self.avgdl = sum(self.doc_lens) / len(self.documents) if self.documents else 0.0
        total_docs = len(self.documents)
        for word, freq in df.items():
            self.idf[word] = math.log(1 + (total_docs - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: Iterable[str]) -> List[float]:
        """Calculate BM25 scores for a query."""
        scores = [0.0] * len(self.documents)
        query_terms = list(query)
        for idx, doc in enumerate(self.documents):
            freqs = self.doc_freqs[idx]
            doc_len = self.doc_lens[idx]
            score = 0.0
            for term in query_terms:
                if term not in freqs:
                    continue
                idf = self.idf.get(term, 0.0)
                tf = freqs[term]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score += idf * numerator / denominator
            scores[idx] = score
        return scores
