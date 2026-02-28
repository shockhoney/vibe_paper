"""语义检索：从 Chroma 中检索相关文本块。"""

from dataclasses import dataclass
from backend.database.chroma_client import get_chroma_client, get_or_create_collection
from backend.rag.embedder import embed_query


@dataclass
class RetrievalResult:
    text: str
    ref_id: int
    chunk_index: int
    section: str
    score: float


def retrieve(
    query: str,
    top_k: int = 5,
    filter_ref_ids: list[int] | None = None,
) -> list[RetrievalResult]:
    """语义检索：将查询嵌入后从 Chroma 中搜索最相关的文本块。"""
    query_vec = embed_query(query)
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    # 构建过滤条件
    where_filter = None
    if filter_ref_ids:
        where_filter = {
            "ref_id": {"$in": filter_ref_ids}
        }

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=top_k,
        where=where_filter,
    )

    retrieval_results = []
    
    if not results["documents"] or not results["documents"][0]:
        return retrieval_results
        
    documents = results["documents"][0]
    metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
    distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)
    
    for doc, meta, dist in zip(documents, metadatas, distances):
        retrieval_results.append(RetrievalResult(
            text=doc,
            ref_id=meta.get("ref_id", 0),
            chunk_index=meta.get("chunk_index", 0),
            section=meta.get("section", ""),
            score=dist,
        ))

    return retrieval_results
