"""
Core RAG pipeline:

PDF -> extract text (PyMuPDF) -> chunk -> embed (Sentence Transformers)
    -> store in ChromaDB -> retrieve relevant chunks for a question
    -> build a grounded prompt -> generate with Ollama

Each function is intentionally small and testable on its own so it maps
cleanly onto the pipeline diagram in the project write-up.
"""
import os
import fitz  # PyMuPDF
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict

from . import ollama_client

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_store")
os.makedirs(CHROMA_DIR, exist_ok=True)

_embedder = None
_chroma_client = None


def get_embedder():
    global _embedder
    if _embedder is None:
        # Small, fast, free, good-enough-quality embedding model.
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _chroma_client


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name="paper_chunks")


# ---------------------------------------------------------------------------
# Step 1-2: Extract text from PDF
# ---------------------------------------------------------------------------

def extract_text_by_page(file_path: str) -> List[str]:
    """Returns a list of page texts, index 0 = page 1."""
    doc = fitz.open(file_path)
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return pages


# ---------------------------------------------------------------------------
# Step 3: Chunk the text
# ---------------------------------------------------------------------------

def chunk_pages(pages: List[str], chunk_size: int = 800, overlap: int = 150) -> List[Dict]:
    """
    Simple sliding-window chunker over each page's text, keeping track of
    which page each chunk came from so we can cite sources later.
    """
    chunks = []
    for page_num, text in enumerate(pages, start=1):
        text = text.strip()
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page": page_num})
            if end == len(text):
                break
            start = end - overlap
    return chunks


# ---------------------------------------------------------------------------
# Step 4-5: Embed & store
# ---------------------------------------------------------------------------

def index_paper(paper_id: int, file_path: str) -> int:
    """
    Processes a PDF end-to-end and stores its chunks in ChromaDB,
    namespaced by paper_id so retrieval can be scoped to one paper.
    Returns the number of chunks stored.
    """
    pages = extract_text_by_page(file_path)
    chunks = chunk_pages(pages)
    if not chunks:
        return 0

    embedder = get_embedder()
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

    collection = get_collection()
    ids = [f"paper{paper_id}_chunk{i}" for i in range(len(chunks))]
    metadatas = [{"paper_id": paper_id, "page": c["page"]} for c in chunks]

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return len(chunks)


# ---------------------------------------------------------------------------
# Step 6-7: Retrieval
# ---------------------------------------------------------------------------

def retrieve_relevant_chunks(paper_id: int, question: str, top_k: int = 4) -> List[Dict]:
    embedder = get_embedder()
    query_embedding = embedder.encode([question]).tolist()

    collection = get_collection()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where={"paper_id": paper_id},
    )

    chunks = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for doc, meta in zip(docs, metas):
        chunks.append({"text": doc, "page": meta.get("page")})
    return chunks


# ---------------------------------------------------------------------------
# Step 8-9: Build grounded prompt & generate
# ---------------------------------------------------------------------------

def answer_question(paper_id: int, question: str) -> Dict:
    chunks = retrieve_relevant_chunks(paper_id, question)
    if not chunks:
        return {
            "answer": "I couldn't find relevant content in this paper for that question. "
                      "Try re-phrasing, or confirm the paper finished processing.",
            "sources": [],
        }

    context = "\n\n".join(f"[Page {c['page']}]\n{c['text']}" for c in chunks)
    prompt = (
        "You are a research assistant. Answer the question using ONLY the context "
        "below, which was extracted from a research paper. If the answer isn't in "
        "the context, say you don't have enough information from the paper.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer clearly and concisely, and mention which page(s) support your answer."
    )
    answer = ollama_client.generate(prompt)
    sources = [{"page": c["page"], "excerpt": c["text"][:200]} for c in chunks]
    return {"answer": answer, "sources": sources}


def summarize_paper(paper_id: int, full_text_sample: str) -> str:
    prompt = (
        "Summarize the following research paper content. Cover: research objective, "
        "methodology, dataset used, key results, and conclusion. Be concise and use "
        "short bullet points under each heading.\n\n"
        f"PAPER CONTENT:\n{full_text_sample}\n"
    )
    return ollama_client.generate(prompt)


def identify_research_gaps(full_text_sample: str) -> str:
    prompt = (
        "Analyze this research paper's methodology, results, and limitations. "
        "Identify 2-4 concrete research gaps or weaknesses, and for each one suggest "
        "a possible extension or improvement. Format as a numbered list with "
        "'Gap:' and 'Possible extension:' for each.\n\n"
        f"PAPER CONTENT:\n{full_text_sample}\n"
    )
    return ollama_client.generate(prompt)


def generate_research_ideas(full_text_sample: str, interests: List[str], num_ideas: int = 3) -> List[Dict]:
    interests_str = ", ".join(interests) if interests else "general improvements on this paper"
    prompt = (
        f"Based on the research paper content below and the user's interests "
        f"({interests_str}), propose {num_ideas} concrete, specific project/research "
        "ideas that build on or extend this paper. "
        "Respond with ONLY a JSON array, no other text, in exactly this format:\n"
        '[{"title": "...", "problem": "...", "approach": "...", '
        '"required_skills": ["skill1", "skill2"], "difficulty": "Beginner|Intermediate|Advanced"}]\n\n'
        f"PAPER CONTENT:\n{full_text_sample}\n"
    )
    result = ollama_client.generate_json(prompt)
    if isinstance(result, dict):
        result = result.get("ideas", [])
    return result
