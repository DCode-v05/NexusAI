"""FAISS IndexFlatIP singleton — loads on first access."""
import json
import numpy as np
from pathlib import Path

INDEX_PATH = Path(__file__).parent / "data" / "faiss_index" / "nexus.index"
MAP_PATH = Path(__file__).parent / "data" / "faiss_index" / "nexus.index.map"


class FAISSIndexer:
    _index = None
    _id_map: dict[int, int] = {}  # faiss_pos → resource_id

    @classmethod
    def load(cls):
        if cls._index is not None:
            return
        if not INDEX_PATH.exists():
            cls._auto_build()
        import faiss
        cls._index = faiss.read_index(str(INDEX_PATH))
        with open(MAP_PATH) as f:
            raw = json.load(f)
        cls._id_map = {int(k): int(v) for k, v in raw.items()}

    @classmethod
    def _auto_build(cls):
        """Build the FAISS index on first run — runs synchronously via asyncio.run()."""
        import asyncio
        import sys
        from pathlib import Path

        print("FAISS index not found — building from seed resources (first-run setup)...")
        # Add project root so build_index imports resolve
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from rag.scripts.build_index import build
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Inside an async context — schedule as a coroutine and block
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, build())
                    future.result()
            else:
                loop.run_until_complete(build())
        except RuntimeError:
            asyncio.run(build())
        print("FAISS index built successfully.")

    @classmethod
    def search(cls, query_vector: np.ndarray, top_k: int = 10) -> list[int]:
        cls.load()
        vec = query_vector.reshape(1, -1).astype(np.float32)
        distances, indices = cls._index.search(vec, top_k)
        resource_ids = []
        for idx in indices[0]:
            if idx >= 0 and idx in cls._id_map:
                resource_ids.append(cls._id_map[idx])
        return resource_ids

    @classmethod
    def is_loaded(cls) -> bool:
        return cls._index is not None
