"""文献管理 Agent：分析已上传文献，提取关键信息，识别研究空白。"""

import json
import dashscope

from langchain_core.messages import AIMessage

from backend.agents.state import PaperState
from backend.config import get_settings
from backend.rag.retriever import retrieve

SYSTEM_PROMPT = """你是一位资深学术文献分析专家。你的任务是：
1. 分析用户提供的参考文献，提取每篇文献的核心贡献、方法论和关键发现
2. 识别文献之间的关联关系和研究趋势
3. 指出当前研究领域的空白和潜在的创新点
4. 为论文写作提供文献综述的框架建议

请以结构化 JSON 格式输出分析结果，包含以下字段：
- literature_summary: 各文献的核心摘要列表
- research_gaps: 识别到的研究空白
- connections: 文献间的关联关系
- suggestions: 对论文写作的建议"""


def literature_agent(state: PaperState) -> dict:
    """文献管理 Agent 节点。"""
    settings = get_settings()
    project_id = state["project_id"]

    # 检索项目相关文献
    query = state.get("user_instruction", "") or "研究背景和相关工作"
    retrieval_results = []
    try:
        retrieval_results = retrieve(query, top_k=10)
    except Exception:
        pass  # Milvus 可能未初始化

    # 构建 LLM 输入
    refs_text = ""
    ref_dicts = []
    for r in retrieval_results:
        refs_text += f"\n[文献 {r.ref_id}, 章节: {r.section}]\n{r.text}\n"
        ref_dicts.append({
            "ref_id": r.ref_id,
            "section": r.section,
            "text": r.text[:300],
            "score": r.score,
        })

    user_msg = f"请分析以下参考文献并给出综述框架：\n{refs_text}" if refs_text else "暂无已上传的文献，请提示用户上传参考文献 PDF。"

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

    return {
        "messages": [AIMessage(content=content, name="literature_agent")],
        "references": ref_dicts,
        "current_agent": "literature",
        "status": "literature",
    }
