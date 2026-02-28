"""格式检查 Agent：检查引用格式、章节结构、术语一致性。"""

import json
import dashscope
from langchain_core.messages import AIMessage

from backend.agents.state import PaperState
from backend.config import get_settings

SYSTEM_PROMPT = """你是一位学术论文格式检查专家。请检查以下方面：
1. 引用格式：是否统一使用 [数字] 格式，引用编号是否连续
2. 章节结构：是否包含完整的学术论文结构（Abstract, Introduction, Related Work, Method, Experiments, Conclusion）
3. 术语一致性：同一概念在全文中是否使用统一的术语
4. 图表引用：是否存在未被引用的图表或未定义的引用
5. 数学符号：是否一致使用同一符号表示同一变量

请以 JSON 格式输出检查结果：
{
  "passed": true/false,
  "issues": [
    {
      "type": "citation/structure/terminology/figure/math",
      "section": "章节名",
      "detail": "具体问题描述",
      "suggestion": "修复建议"
    }
  ],
  "summary": "格式检查总结"
}

仅当无 critical 或 major 问题时 passed 为 true。"""


def formatter_agent(state: PaperState) -> dict:
    """格式检查 Agent 节点。"""
    settings = get_settings()
    sections = state.get("sections", {})
    outline = state.get("outline", {})

    if not sections:
        return {
            "messages": [AIMessage(content="暂无内容可检查格式。", name="formatter_agent")],
            "current_agent": "formatter",
            "status": "formatting",
        }

    # 构建检查内容
    paper_text = ""
    for title, content in sections.items():
        paper_text += f"\n## {title}\n{content}\n"

    user_msg = f"请检查以下论文的格式规范：\n\n大纲结构：{json.dumps(outline, ensure_ascii=False)}\n\n论文内容：\n{paper_text}"

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

    # 解析格式检查结果
    format_issues = []
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            fmt_data = json.loads(content[start:end])
            format_issues = fmt_data.get("issues", [])
    except json.JSONDecodeError:
        pass

    return {
        "messages": [AIMessage(content=content, name="formatter_agent")],
        "format_issues": format_issues,
        "current_agent": "formatter",
        "status": "formatting",
    }
