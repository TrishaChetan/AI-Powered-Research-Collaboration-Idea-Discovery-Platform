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
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR, settings=chromadb.Settings(anonymized_telemetry=False))
    return _chroma_client


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name="paper_chunks")


def extract_text_by_page(file_path: str) -> List[str]:
    doc = fitz.open(file_path)
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return pages


def chunk_pages(pages: List[str], chunk_size: int = 800, overlap: int = 150) -> List[Dict]:
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


def index_paper(paper_id: int, file_path: str) -> int:
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


def retrieve_relevant_chunks(paper_id: int, question: str, top_k: int = 4) -> List[Dict]:
    embedder = get_embedder()
    query_embedding = embedder.encode([question], show_progress_bar=False, normalize_embeddings=True).tolist()

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


def answer_question(paper_id: int, question: str) -> Dict:
    chunks = retrieve_relevant_chunks(paper_id, question, top_k=3)
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
    answer = ollama_client.generate(prompt, num_predict=140)
    sources = [{"page": c["page"], "excerpt": c["text"][:200]} for c in chunks]
    return {"answer": answer, "sources": sources}


def summarize_paper(paper_id: int, full_text_sample: str) -> str:
    prompt = (
        "Summarize the following research paper content. Cover: research objective, "
        "methodology, dataset used, key results, and conclusion. Be concise and use "
        "short bullet points under each heading -- one line per bullet, no repetition.\n\n"
        f"PAPER CONTENT:\n{full_text_sample[:3000]}\n"
    )
    return ollama_client.generate(prompt, num_predict=180)


def identify_research_gaps(full_text_sample: str) -> str:
    prompt = (
        "Analyze this research paper's methodology, results, and limitations. "
        "Identify exactly 3 research gaps or weaknesses. Each gap must be about a "
        "DIFFERENT aspect of the paper (e.g. one about the dataset, one about the "
        "method, one about evaluation) -- do not repeat the same point twice in "
        "different words. For each gap, give one sentence naming the gap and one "
        "sentence suggesting an extension. Be concise -- no more than 2 sentences per gap.\n"
        "Format exactly like this:\n"
        "1. Gap: ... | Extension: ...\n"
        "2. Gap: ... | Extension: ...\n"
        "3. Gap: ... | Extension: ...\n\n"
        f"PAPER CONTENT:\n{full_text_sample[:3000]}\n"
    )
    return ollama_client.generate(prompt, num_predict=140)


def compare_papers(paper_samples: List[Dict]) -> Dict:
    dimensions = [
        "Research Objective",
        "Methodology",
        "Dataset Used",
        "Key Results",
        "Limitations",
    ]

    analyses = []

    for paper in paper_samples:
        prompt = (
            "Analyze ONLY this research paper content. "
            "Extract the requested information from the CONTENT, not from the title. "
            "Return ONLY valid JSON with exactly these five fields: "
            "research_objective, methodology, dataset_used, key_results, limitations. "
            "Each value must be one concise sentence. "
            "If information is not present, write 'Not specified in the provided content'. "
            "Do not invent information. Do not return markdown.\n\n"
            f"TITLE: {paper['title']}\n"
            f"CONTENT:\n{paper['text'][:1800]}\n\n"
            "FORMAT:\n"
            '{"research_objective":"...",'
            '"methodology":"...",'
            '"dataset_used":"...",'
            '"key_results":"...",'
            '"limitations":"..."}'
        )

        result = ollama_client.generate_json(prompt, num_predict=220)
        analyses.append(result)

    rows = []

    field_map = {
        "Research Objective": "research_objective",
        "Methodology": "methodology",
        "Dataset Used": "dataset_used",
        "Key Results": "key_results",
        "Limitations": "limitations",
    }

    for dimension in dimensions:
        field = field_map[dimension]
        values = []

        for analysis in analyses:
            if isinstance(analysis, dict):
                values.append(
                    str(analysis.get(field, "Not specified in the provided content"))
                )
            else:
                values.append("Not specified in the provided content")

        rows.append({
            "dimension": dimension,
            "values": values,
        })

    return {"rows": rows}


def build_on_idea(parent_idea: Dict, num_ideas: int = 2) -> List[Dict]:
    prompt = (
        "A researcher previously proposed this idea:\n"
        f"Title: {parent_idea['title']}\n"
        f"Problem: {parent_idea['problem']}\n"
        f"Approach: {parent_idea['approach']}\n\n"
        f"Propose {num_ideas} concrete follow-up ideas that build directly on top of this one "
        "(e.g. the next logical step, a harder variant, or a real-world deployment of it). "
        f"Respond with ONLY a valid JSON array containing EXACTLY {num_ideas} objects, no other text. Each object must be complete and detailed. Do not stop after the first idea. Make all ideas meaningfully different. Use exactly this format:\n"
        '[{"title": "...", "problem": "...", "approach": "...", '
        '"required_skills": ["skill1", "skill2"], "difficulty": "Beginner|Intermediate|Advanced"}]\n'
    )
    result = ollama_client.generate_json(prompt, num_predict=220)
    if isinstance(result, dict):
        result = result.get("ideas", [])
    return result


def generate_research_ideas(full_text_sample: str, interests: List[str], num_ideas: int = 3) -> List[Dict]:
    interests_str = ", ".join(interests) if interests else "general improvements on this paper"
    prompt = (
        f"Based on the research paper content below and the user's interests "
        f"({interests_str}), propose EXACTLY {num_ideas} different, detailed, concrete, specific project/research "
        "ideas that build on or extend this paper. "
        f"Respond with ONLY a valid JSON array containing EXACTLY {num_ideas} objects, no other text. Each object must be complete and detailed. Do not stop after the first idea. Make all ideas meaningfully different. Use exactly this format:\n"
        '[{"title": "...", "problem": "...", "approach": "...", '
        '"required_skills": ["skill1", "skill2"], "difficulty": "Beginner|Intermediate|Advanced"}]\n\n'
        f"PAPER CONTENT:\n{full_text_sample[:2000]}\n"
    )
    result = ollama_client.generate_json(prompt, num_predict=600)
    if isinstance(result, dict):
        result = result.get("ideas", [])
    return result













