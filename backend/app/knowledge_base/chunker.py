"""
Semantic-first chunking: split on markdown "##" section boundaries (natural
topic units), then further split any section that exceeds CHUNK_SIZE using a
sliding window with overlap so no single chunk loses surrounding context.
"""
import re
import glob
import os
from app.config import settings


def _split_long_section(text: str, chunk_size: int, overlap: int):
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def load_and_chunk_role_docs(role_key: str):
    """Returns list of dicts: {chunk_id, role, topic, text}"""
    path = os.path.join(settings.KB_DIR, f"{role_key}.md")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    sections = re.split(r"\n(?=## )", raw)
    chunks = []
    idx = 0
    for section in sections:
        section = section.strip()
        if not section or section.startswith("# "):
            continue
        header_match = re.match(r"## (.+)", section)
        topic = header_match.group(1).strip() if header_match else "General"
        body = section
        for piece in _split_long_section(body, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP):
            chunks.append({
                "chunk_id": f"{role_key}-{idx}",
                "role": role_key,
                "topic": topic,
                "text": piece.strip(),
            })
            idx += 1
    return chunks


def available_roles():
    files = glob.glob(os.path.join(settings.KB_DIR, "*.md"))
    return sorted(os.path.splitext(os.path.basename(f))[0] for f in files)
