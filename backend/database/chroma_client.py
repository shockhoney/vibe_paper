"""Chroma 客户端：使用本地文件系统存储向量，无需独立服务器。"""

from pathlib import Path
import chromadb
from chromadb.config import Settings

COLLECTION_NAME = "doc_embeddings"


def get_chroma_client() -> chromadb.ClientAPI:
    # 存储在项目根目录的 chroma_data 文件夹下
    db_path = Path("./chroma_data")
    db_path.mkdir(exist_ok=True)
    return chromadb.PersistentClient(path=str(db_path))

def get_or_create_collection(client: chromadb.ClientAPI):
    """获取或创建文档嵌入集合（如果不存在）。"""
    # Chroma 会自动处理集合的创建和获取，使用的是余弦距离。
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
