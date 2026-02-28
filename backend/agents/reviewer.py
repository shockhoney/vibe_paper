"""审阅优化 Agent：检查学术规范、逻辑连贯性、语言质量。"""

import json
import dashscope
from langchain_core.messages import AIMessage

from backend.agents.state import PaperState
from backend.config import get_settings

SYSTEM_PROMPT = """你是一位严格的学术论文审稿专家。请从以下维度审阅论文内容：
1. 学术规范：引用是否充分、术语使用是否准确
2. 逻辑连贯性：章节之间的衔接、论证是否自洽
3. 语言质量：是否简洁清晰、无语法错误
4. 创新性：是否突出了研究贡献

请以 JSON 格式输出审阅报告：
{
  "overall_score": 1-10,
  "passed": true/false,
  "feedback": [
    {
      "section": "章节名",
      "severity": "critical/major/minor",
      "comment": "具体修改建议"
    }
  ],
  "summary": "总体评价"
}

- overall_score >= 7 且无 critical 问题时，passed 为 true
- 审阅应严格但公正，给出可操作的修改建议"""


def reviewer_agent(state: PaperState) -> dict:
    """审阅优化 Agent 节点。"""
    settings = get_settings()
    sections = state.get("sections", {})

    if not sections:
        return {
            "messages": [AIMessage(content="暂无章节内容可审阅。", name="reviewer_agent")],
            "current_agent": "reviewer",
            "status": "reviewing",
        }

    # 构建待审阅内容
    paper_text = ""
    for title, content in sections.items():
        paper_text += f"\n## {title}\n{content}\n"

    user_msg = f"请审阅以下论文内容：\n{paper_text}"

    # 如果有之前的反馈，附加上下文
    prev_feedback = state.get("review_feedback", [])
    if prev_feedback:
        user_msg += f"\n\n上一轮审阅意见（检查是否已修改）：\n{json.dumps(prev_feedback[-5:], ensure_ascii=False)}"

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

    # 解析审阅结果
    review_feedback = []
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            review_data = json.loads(content[start:end])
            review_feedback = review_data.get("feedback", [])
    except json.JSONDecodeError:
        pass

    return {
        "messages": [AIMessage(content=content, name="reviewer_agent")],
        "review_feedback": review_feedback,
        "current_agent": "reviewer",
        "status": "reviewing",
    }
