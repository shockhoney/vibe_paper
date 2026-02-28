"""内容写作 Agent：分章节生成学术论文内容。"""

import dashscope
from langchain_core.messages import AIMessage

from backend.agents.state import PaperState
from backend.config import get_settings
from backend.rag.retriever import retrieve

SYSTEM_PROMPT = """你是一位学术论文写作专家，能够撰写高质量的学术文章。请遵循以下原则：
1. 使用严谨的学术语言，逻辑清晰，论证充分
2. 合理引用参考文献（使用 [数字] 格式）
3. 每个段落围绕一个核心观点展开
4. 确保前后章节的逻辑连贯性
5. 适当使用学术领域的专业术语

请根据大纲和参考文献，撰写指定章节的内容。"""


def writer_agent(state: PaperState) -> dict:
    """内容写作 Agent 节点。"""
    settings = get_settings()
    outline = state.get("outline", {})
    sections = dict(state.get("sections", {}))

    # 找到需要写的章节（尚未完成的）
    target_sections = []
    for sec in outline.get("sections", []):
        title = sec.get("title", "")
        if title and title not in sections:
            target_sections.append(sec)
    
    if not target_sections:
        # 所有章节已写完
        return {
            "messages": [AIMessage(content="所有章节已完成写作。", name="writer_agent")],
            "current_agent": "writer",
            "status": "writing",
        }

    # 逐个写作（每次处理一个章节）
    sec = target_sections[0]
    sec_title = sec["title"]
    sec_desc = sec.get("description", "")

    # RAG 检索相关文献
    query = f"{sec_title} {sec_desc}"
    ref_texts = ""
    try:
        results = retrieve(query, top_k=5)
        for r in results:
            ref_texts += f"\n[参考文献 {r.ref_id}]: {r.text[:500]}\n"
    except Exception:
        pass

    # 已完成章节的摘要（提供上下文）
    completed = ""
    for title, content in sections.items():
        completed += f"\n### {title}\n{content[:200]}...\n"

    # 审阅反馈
    feedback = ""
    if state.get("review_feedback"):
        for fb in state["review_feedback"]:
            if fb.get("section") == sec_title:
                feedback += f"\n- {fb.get('comment', '')}"

    user_msg = (
        f"请撰写以下章节：\n"
        f"章节标题：{sec_title}\n"
        f"章节描述：{sec_desc}\n"
    )
    if ref_texts:
        user_msg += f"\n相关参考文献：\n{ref_texts}"
    if completed:
        user_msg += f"\n已完成的章节（保持连贯性）：\n{completed}"
    if feedback:
        user_msg += f"\n审阅者修改建议：\n{feedback}"

    resp = dashscope.Generation.call(
        model=settings.qwen_model,
        api_key=settings.dashscope_api_key,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        result_format="message",
    )

    from http import HTTPStatus
    if resp.status_code != HTTPStatus.OK:
        raise Exception(f"DashScope API Error: {resp.code} - {resp.message} (Please check your API Key in .env)")
    
    content = resp.output.choices[0].message.content
    sections[sec_title] = content

    return {
        "messages": [AIMessage(content=f"[{sec_title}] 写作完成。", name="writer_agent")],
        "sections": sections,
        "current_agent": "writer",
        "status": "writing",
    }
