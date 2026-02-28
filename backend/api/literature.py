"""文献管理路由：上传 PDF 并解析入库。"""

import os
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgres import get_db
from backend.database.models import Reference
from backend.database.chroma_client import get_chroma_client, get_or_create_collection
from backend.schemas.paper import ReferenceOut
from backend.rag.parser import parse_pdf
from backend.rag.embedder import embed_texts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/literature", tags=["literature"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload/{project_id}", response_model=ReferenceOut)
async def upload_literature(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传 PDF 文献，解析内容后存入 PostgreSQL 和 Chroma。"""
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(400, "仅支持 PDF 文件")

    # 保存文件到本地
    save_path = UPLOAD_DIR / f"{project_id}_{file.filename}"
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # 解析 PDF
    chunks = await parse_pdf(str(save_path))

    # 创建参考文献记录
    ref = Reference(
        project_id=project_id,
        title=file.filename.replace(".pdf", ""),
        file_path=str(save_path),
    )
    db.add(ref)
    await db.commit()
    await db.refresh(ref)

    # 嵌入并存入 Chroma
    if chunks:
        texts = [c.text for c in chunks]
        try:
            embeddings = embed_texts(texts)
            chroma = get_chroma_client()
            collection = get_or_create_collection(chroma)
            
            ids = [uuid.uuid4().hex for _ in chunks]
            metadatas = [
                {
                    "ref_id": ref.id,
                    "chunk_index": c.chunk_index,
                    "section": c.section or "",
                }
                for c in chunks
            ]
            
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            logger.info("Inserted %d chunks for ref %d into Chroma", len(ids), ref.id)
        except Exception as e:
            logger.error("Failed to embed/insert: %s", e)

    return ref


@router.get("/{project_id}", response_model=list[ReferenceOut])
async def list_literature(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Reference).where(Reference.project_id == project_id)
    )
    return result.scalars().all()


@router.delete("/{ref_id}")
async def delete_literature(ref_id: int, db: AsyncSession = Depends(get_db)):
    ref = await db.get(Reference, ref_id)
    if not ref:
        raise HTTPException(404, "文献不存在")
    # 删除本地文件
    if ref.file_path and os.path.exists(ref.file_path):
        os.remove(ref.file_path)
    # 删除 Chroma 中的向量
    try:
        chroma = get_chroma_client()
        collection = get_or_create_collection(chroma)
        collection.delete(
            where={"ref_id": ref_id}
        )
    except Exception as e:
        logger.warning("Failed to delete from Chroma: %s", e)
    await db.delete(ref)
    await db.commit()
    return {"ok": True}
