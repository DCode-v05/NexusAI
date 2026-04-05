"""High-level retriever: query string → list[Resource]."""
from rag.embedder import ResourceEmbedder
from rag.indexer import FAISSIndexer
from rag.resource_db import Resource, get_by_ids


class ResourceRetriever:
    def __init__(self):
        self._embedder = ResourceEmbedder()

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        domain_filter: str | None = None,
    ) -> list[Resource]:
        query_vec = await self._embedder.embed_single(query)
        resource_ids = FAISSIndexer.search(query_vec, top_k=top_k * 3)  # over-fetch for domain filter
        resources = await get_by_ids(resource_ids)

        if domain_filter:
            resources = [r for r in resources if r.domain == domain_filter]

        return resources[:top_k]
