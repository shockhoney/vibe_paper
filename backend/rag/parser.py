"""PDF 文档解析：GROBID 优先，PyMuPDF 兜底。"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

import fitz  # PyMuPDF
import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)

TEI_NS = "{http://www.tei-c.org/ns/1.0}"


@dataclass
class TextChunk:
    text: str
    page: int = 0
    chunk_index: int = 0
    section: str = ""
    metadata: dict = field(default_factory=dict)


# ---------- GROBID 通道 ----------

async def _parse_with_grobid(file_path: str) -> list[TextChunk] | None:
    """调用 GROBID 服务解析 PDF，失败返回 None。"""
    settings = get_settings()
    url = f"{settings.grobid_url}/api/processFulltextDocument"
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            with open(file_path, "rb") as f:
                resp = await client.post(url, files={"input": f})
            if resp.status_code != 200:
                logger.warning("GROBID returned status %d", resp.status_code)
                return None
            return _parse_tei_xml(resp.text)
    except Exception as e:
        logger.warning("GROBID unavailable: %s", e)
        return None


def _parse_tei_xml(xml_text: str) -> list[TextChunk]:
    """解析 GROBID 返回的 TEI XML，提取各章节文本。"""
    root = ElementTree.fromstring(xml_text)
    chunks: list[TextChunk] = []
    idx = 0

    # 提取摘要
    abstract_el = root.find(f".//{TEI_NS}abstract")
    if abstract_el is not None:
        text = " ".join(abstract_el.itertext()).strip()
        if text:
            chunks.append(TextChunk(text=text, chunk_index=idx, section="abstract"))
            idx += 1

    # 提取正文各章节
    body = root.find(f".//{TEI_NS}body")
    if body is not None:
        for div in body.findall(f"{TEI_NS}div"):
            head = div.find(f"{TEI_NS}head")
            section_title = head.text.strip() if head is not None and head.text else "untitled"
            paragraphs = []
            for p in div.findall(f"{TEI_NS}p"):
                p_text = " ".join(p.itertext()).strip()
                if p_text:
                    paragraphs.append(p_text)
            if paragraphs:
                chunks.append(TextChunk(
                    text="\n".join(paragraphs),
                    chunk_index=idx,
                    section=section_title,
                ))
                idx += 1

    return chunks


# ---------- PyMuPDF 兜底通道 ----------

def _parse_with_pymupdf(file_path: str, chunk_size: int = 500) -> list[TextChunk]:
    """使用 PyMuPDF 提取纯文本并按固定长度分块。"""
    doc = fitz.open(file_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()

    # 按字符数分块，尽量在换行处断开
    chunks: list[TextChunk] = []
    lines = full_text.split("\n")
    buffer, idx = "", 0
    for line in lines:
        if len(buffer) + len(line) > chunk_size and buffer:
            chunks.append(TextChunk(text=buffer.strip(), chunk_index=idx))
            idx += 1
            buffer = ""
        buffer += line + "\n"
    if buffer.strip():
        chunks.append(TextChunk(text=buffer.strip(), chunk_index=idx))

    return chunks


# ---------- 统一入口 ----------

async def parse_pdf(file_path: str) -> list[TextChunk]:
    """解析 PDF：优先使用 GROBID，失败则回退到 PyMuPDF。"""
    chunks = await _parse_with_grobid(file_path)
    if chunks:
        logger.info("Parsed %s with GROBID: %d chunks", Path(file_path).name, len(chunks))
        return chunks
    chunks = _parse_with_pymupdf(file_path)
    logger.info("Parsed %s with PyMuPDF: %d chunks", Path(file_path).name, len(chunks))
    return chunks


def extract_metadata_from_grobid_xml(xml_text: str) -> dict:
    """从 GROBID TEI XML 中提取论文元数据（标题、作者、年份等）。"""
    root = ElementTree.fromstring(xml_text)
    meta = {}

    title_el = root.find(f".//{TEI_NS}titleStmt/{TEI_NS}title")
    if title_el is not None and title_el.text:
        meta["title"] = title_el.text.strip()

    authors = []
    for author in root.findall(f".//{TEI_NS}fileDesc//{TEI_NS}author"):
        forename = author.find(f".//{TEI_NS}forename")
        surname = author.find(f".//{TEI_NS}surname")
        name_parts = []
        if forename is not None and forename.text:
            name_parts.append(forename.text)
        if surname is not None and surname.text:
            name_parts.append(surname.text)
        if name_parts:
            authors.append(" ".join(name_parts))
    if authors:
        meta["authors"] = ", ".join(authors)

    date_el = root.find(f".//{TEI_NS}publicationStmt/{TEI_NS}date")
    if date_el is not None:
        when = date_el.get("when", "")
        if when and len(when) >= 4:
            try:
                meta["year"] = int(when[:4])
            except ValueError:
                pass

    doi_el = root.find(f".//{TEI_NS}idno[@type='DOI']")
    if doi_el is not None and doi_el.text:
        meta["doi"] = doi_el.text.strip()

    abstract_el = root.find(f".//{TEI_NS}abstract")
    if abstract_el is not None:
        meta["abstract"] = " ".join(abstract_el.itertext()).strip()

    return meta
