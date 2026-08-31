import os
import re
import math
from collections import Counter
from typing import List, Dict
from pypdf import PdfReader

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")

ROLE_FILES = {
    "AI / Machine Learning Engineer": "ai_ml_engineer.txt",
    "Data Scientist / Applied ML": "data_scientist.txt",
    "Backend Engineer": "backend_engineer.txt"
}

def extract_text_from_pdf(file_bytes: bytes) -> str:
    from io import BytesIO
    reader = PdfReader(BytesIO(file_bytes))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)
    return "\n".join(pages_text)

def chunk_text(text: str, chunk_size: int = 350, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 30:
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks

def load_role_knowledge(role: str) -> List[Dict]:
    filename = ROLE_FILES.get(role, "ai_ml_engineer.txt")
    filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    raw_chunks = chunk_text(content)
    corpus = []
    for idx, chunk in enumerate(raw_chunks):
        title_match = re.search(r"(CHAPTER \d+:[^\n]+)", chunk)
        source_title = title_match.group(1) if title_match else f"Section {idx+1}"
        corpus.append({
            "chunk_id": idx + 1,
            "source": source_title,
            "role": role,
            "text": chunk
        })
    return corpus

def tokenize(text: str) -> List[str]:
    return re.findall(r"\b[a-z0-9_]{2,}\b", text.lower())

def compute_cosine_similarity(query_tokens: List[str], doc_tokens: List[str]) -> float:
    query_counts = Counter(query_tokens)
    doc_counts = Counter(doc_tokens)
    dot_product = sum(query_counts[t] * doc_counts[t] for t in query_counts if t in doc_counts)
    query_norm = math.sqrt(sum(v * v for v in query_counts.values()))
    doc_norm = math.sqrt(sum(v * v for v in doc_counts.values()))
    if query_norm == 0 or doc_norm == 0:
        return 0.0
    return dot_product / (query_norm * doc_norm)

def retrieve_relevant_context(role: str, query: str, top_k: int = 2) -> List[Dict]:
    corpus = load_role_knowledge(role)
    if not corpus:
        return []
    query_tokens = tokenize(query)
    scored_items = []
    for item in corpus:
        doc_tokens = tokenize(item["text"])
        score = compute_cosine_similarity(query_tokens, doc_tokens)
        scored_item = dict(item)
        scored_item["score"] = round(score, 4)
        scored_items.append(scored_item)
    scored_items.sort(key=lambda x: x["score"], reverse=True)
    selected = scored_items[:top_k]
    if not any(item["score"] > 0.01 for item in selected):
        return [corpus[0]] if corpus else []
    return selected
