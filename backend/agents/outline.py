"""大纲规划 Agent：基于文献分析生成论文大纲。"""

import dashscope
from langchain_core.messages import AIMessage

from backend.agents.state import PaperState
from backend.config import get_settings

SYSTEM_PROMPT = """你是一位学术论文大纲规划专家。你的任务是：
1. 根据文献分析结果和用户的研究主题，规划一份完整的学术论文大纲
2. 大纲应包含标准学术论文结构：Abstract, Introduction, Related Work, Method, Experiments, Conclusion
3. 每个章节需要列出 2-4 个子节点和简要描述

请以 JSON 格式输出大纲，结构如下：
{
  "title": "论文标题",
  "sections": [
    {
      "id": "1",
      "title": "章节名",
      "description": "该章节应覆盖的内容要点",
      "subsections": [
        {"id": "1.1", "title": "子章节名", "description": "要点"}
      ]
    }
  ]
}"""


def outline_agent(state: PaperState) -> dict:
    """大纲规划 Agent 节点。"""
    settings = get_settings()

    # 收集前序 Agent 的分析结果
    prev_messages = []
    for msg in state.get("messages", []):
        if hasattr(msg, "name") and msg.name == "literature_agent":
            prev_messages.append(msg.content)

    context = "\n".join(prev_messages[-3:]) if prev_messages else "暂无文献分析结果"
    instruction = state.get("user_instruction", "")
    existing_outline = state.get("outline", {})

    user_msg = f"用户指令：{instruction}\n\n文献分析结果：\n{context}"
    if existing_outline:
        user_msg += f"\n\n当前大纲（需优化）：\n{existing_outline}"

    if state.get("review_feedback"):
        feedback_text = "\n".join(
            f"- {fb.get('comment', '')}" for fb in state["review_feedback"][-5:]
        )
        user_msg += f"\n\n审阅反馈（请据此修改）：\n{feedback_text}"

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

    # 尝试提取 JSON 大纲
    import json
    outline = {}
    try:
        # 尝试从回复中提取 JSON
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            outline = json.loads(content[start:end])
    except json.JSONDecodeError:
        pass

    return {
        "messages": [AIMessage(content=content, name="outline_agent")],
        "outline": outline if outline else state.get("outline", {}),
        "current_agent": "outline",
        "status": "outline",
    }
