"""MCP Resource RAG Server — port 9003.

Tools: search_resources, get_scheme_details, embed_query, rank_results
Delegates to rag/ package mounted at /app/rag via Docker volume.
"""
import sys
from pathlib import Path

# Add project root so rag/ package is importable
sys.path.insert(0, "/app")
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load FAISS index at startup
    try:
        from rag.indexer import FAISSIndexer
        FAISSIndexer.load()
        print("FAISS index loaded.")
    except FileNotFoundError:
        print("FAISS index not found — run build_index.py first.")
    yield

app = FastAPI(title="MCP Resource RAG Server", lifespan=lifespan)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    domain_filter: str | None = None


class EmbedRequest(BaseModel):
    text: str


class RankRequest(BaseModel):
    query: str
    candidates: list[dict]


@app.get("/health")
async def health():
    from rag.indexer import FAISSIndexer
    return {"status": "ok", "service": "mcp-resource-rag", "index_loaded": FAISSIndexer.is_loaded()}


@app.post("/tools/search_resources")
async def search_resources(req: SearchRequest):
    from rag.retriever import ResourceRetriever
    retriever = ResourceRetriever()
    resources = await retriever.retrieve(req.query, top_k=req.top_k, domain_filter=req.domain_filter)
    return [
        {
            "id": r.id,
            "title": r.title,
            "url": r.url,
            "description": r.description,
            "tags": r.tags,
            "domain": r.domain,
            "type": r.type,
        }
        for r in resources
    ]


@app.post("/tools/get_scheme_details")
async def get_scheme_details(scheme_id: int):
    from rag.resource_db import get_by_ids
    resources = await get_by_ids([scheme_id])
    if not resources:
        return {"error": "Scheme not found"}
    r = resources[0]
    return {"id": r.id, "title": r.title, "url": r.url, "description": r.description, "tags": r.tags}


@app.post("/tools/embed_query")
async def embed_query(req: EmbedRequest):
    from rag.embedder import ResourceEmbedder
    embedder = ResourceEmbedder()
    vec = await embedder.embed_single(req.text)
    return {"embedding": vec.tolist()}


@app.post("/tools/rank_results")
async def rank_results(req: RankRequest):
    from rag.embedder import ResourceEmbedder
    import numpy as np

    embedder = ResourceEmbedder()
    query_vec = await embedder.embed_single(req.query)

    scored = []
    for candidate in req.candidates:
        text = f"{candidate.get('title', '')} {candidate.get('description', '')}"
        cand_vec = await embedder.embed_single(text)
        score = float(np.dot(query_vec, cand_vec))
        scored.append({**candidate, "relevance_score": score})

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored
