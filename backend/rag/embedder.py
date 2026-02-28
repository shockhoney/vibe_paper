"""文本嵌入：调用 Qwen text-embedding-v3 模型。"""

import logging
from dashscope import TextEmbedding

from backend.config import get_settings

logger = logging.getLogger(__name__)
BATCH_SIZE = 25  # DashScope 单次最多处理的文本数量


def embed_texts(texts: list[str]) -> list[list[float]]:
    """将文本列表转换为嵌入向量。分批处理以避免 token 限制。"""
    settings = get_settings()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = TextEmbedding.call(
            model=settings.qwen_embedding_model,
            input=batch,
            api_key=settings.dashscope_api_key,
        )
        if resp.status_code != 200:
            logger.error("Embedding API error: %s", resp.message)
            raise RuntimeError(f"Embedding failed: {resp.message}")

        for item in resp.output["embeddings"]:
            all_embeddings.append(item["embedding"])

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """将单条查询文本转换为嵌入向量。"""
    result = embed_texts([query])
    return result[0]
