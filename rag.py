import os
import numpy as np
from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer

# Local embedding model (downloaded on first use, ~90 MB)
EMBED_MODEL = "all-MiniLM-L6-v2"
# Free HF Inference API model — change via HF_LLM_MODEL env var
LLM_MODEL = os.environ.get("HF_LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
# Number of most relevant pages to pass to the LLM
TOP_K = 5

_embed_model: SentenceTransformer | None = None


def _get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL)
    return _embed_model


def _get_llm_client() -> InferenceClient:
    # HF_TOKEN env var — get a free token at https://huggingface.co/settings/tokens
    return InferenceClient(
        model=LLM_MODEL,
        token=os.environ.get("HF_TOKEN"),
    )


def build_index(pages: dict[int, str]) -> dict:
    """Embed all page texts and return a searchable index."""
    model = _get_embed_model()
    page_nums = sorted(pages.keys())
    texts = [pages[p] for p in page_nums]
    print("Building embeddings index...")
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    return {"page_nums": page_nums, "embeddings": np.array(embeddings)}


def answer_question(question: str, index: dict, pages: dict[int, str]) -> str:
    """Retrieve the most relevant pages and ask the LLM to answer with citations."""
    model = _get_embed_model()
    q_emb = model.encode([question], normalize_embeddings=True)[0]

    # Cosine similarity (embeddings are already L2-normalised)
    scores = index["embeddings"] @ q_emb
    top_indices = np.argsort(scores)[::-1][:TOP_K]

    retrieved = [
        (index["page_nums"][i], pages[index["page_nums"][i]], float(scores[i]))
        for i in top_indices
    ]

    context = "\n\n".join(
        f"[Page {pn}]\n{text[:3000]}" for pn, text, _ in retrieved
    )

    client = _get_llm_client()

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert assistant for oil and gas well reports. "
                    "Answer questions using only the page excerpts provided. "
                    "Always cite the page number(s) your answer is based on using "
                    "the format (Page N). If the answer is not found in the "
                    "excerpts, clearly state that."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    return response.choices[0].message.content
