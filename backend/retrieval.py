"""Lexical retrieval: hand-rolled BM25 + manual TF-IDF cosine blend.

CPU-only, no downloads, no external ML dependencies, deterministic.
"""
import math
import re
from collections import Counter

TOKEN = re.compile(r"[a-z0-9]+")

STOP = frozenset(
    "the,a,an,and,or,of,for,to,in,on,with,by,is,are,as,at,from,that,this,it,its,be,shall,should,must,required,including,includes,into,per,all,any,our,which,have,has,need,needs,specification,procurement".split(",")
)


def tokenize(text: str) -> list[str]:
    return [w for w in TOKEN.findall(text.lower()) if w not in STOP and len(w) > 1]


def doc_text(standard: dict) -> str:
    return " ".join([
        standard["standard_id"], standard["title"], standard["product_category"],
        standard["scope_summary"], " ".join(standard["keywords"]),
        " ".join(standard["covers"]), standard["role"],
    ])


class Index:
    def __init__(self, standards: list[dict]):
        self.standards = standards
        self.docs = [tokenize(doc_text(s)) for s in standards]
        self.N = len(self.docs)
        self.df = Counter()
        for d in self.docs:
            for tok in set(d):
                self.df[tok] += 1
        self.doc_len = [len(d) for d in self.docs]
        self.avgdl = sum(self.doc_len) / max(1, self.N)
        # TF-IDF vectors (manual, deterministic)
        self.idf = {t: math.log(1 + (self.N - df + 0.5) / (df + 0.5)) for t, df in self.df.items()}
        self.doc_vecs = []
        for d in self.docs:
            tf = Counter(d)
            n = len(d) or 1
            vec = {t: (c / n) * self.idf.get(t, 0.0) for t, c in tf.items()}
            self.doc_vecs.append(vec)

    def _bm25(self, q: list[str], k1=1.5, b=0.75) -> list[float]:
        scores = []
        for i, d in enumerate(self.docs):
            tf = Counter(d)
            dl = self.doc_len[i] or 1
            s = 0.0
            for tok in q:
                if tok not in tf:
                    continue
                idf = self.idf.get(tok, 0.0)
                f = tf[tok]
                s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / self.avgdl))
            scores.append(s)
        return scores

    def _cosine(self, q: list[str]) -> list[float]:
        qtf = Counter(q)
        n = len(q) or 1
        qv = {t: (c / n) * self.idf.get(t, math.log(1 + (self.N + 0.5) / 0.5)) for t, c in qtf.items()}
        qn = math.sqrt(sum(v * v for v in qv.values())) or 1.0
        out = []
        for vec in self.doc_vecs:
            dot = sum(qv.get(t, 0.0) * v for t, v in vec.items())
            dn = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            out.append(dot / (qn * dn))
        return out

    def search(self, query: str) -> list[tuple[int, float, float, float]]:
        q = tokenize(query + " valve pressure steel flanged test safety")
        bm = self._bm25(q)
        co = self._cosine(q)
        max_bm = max(bm) or 1.0
        results = []
        for i in range(self.N):
            nb = bm[i] / max_bm
            blended = 0.5 * nb + 0.5 * co[i]
            results.append((i, round(blended, 4), round(nb, 4), round(co[i], 4)))
        results.sort(key=lambda r: r[1], reverse=True)
        return results


def expand_query(spec_text: str, requirements: list[dict]) -> str:
    parts = [spec_text]
    for r in requirements:
        if r["value"]:
            parts.append(str(r["value"]))
            parts.append(r["label"])
    return " ".join(parts)
