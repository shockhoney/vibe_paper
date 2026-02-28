"""去中心化路由：每个 Agent 根据当前状态自主决定下一步。"""

import json
from backend.agents.state import PaperState


def route_after_literature(state: PaperState) -> str:
    """文献 Agent 完成后 -> 大纲 Agent。"""
    return "outline_agent"


def route_after_outline(state: PaperState) -> str:
    """大纲 Agent 完成后 -> 写作 Agent。"""
    outline = state.get("outline", {})
    if not outline or not outline.get("sections"):
        return "outline_agent"  # 大纲不完整，重试
    return "writer_agent"


def route_after_writer(state: PaperState) -> str:
    """写作 Agent 完成后：检查是否所有章节已写完。"""
    outline = state.get("outline", {})
    sections = state.get("sections", {})
    expected = {s["title"] for s in outline.get("sections", [])}
    completed = set(sections.keys())

    if expected - completed:
        return "writer_agent"  # 还有章节未完成，继续写
    return "reviewer_agent"  # 全部写完，交审阅


def route_after_reviewer(state: PaperState) -> str:
    """审阅 Agent 完成后：根据审阅结果决定回写或交格式检查。"""
    messages = state.get("messages", [])

    # 从审阅结果中判断是否通过
    for msg in reversed(messages):
        if hasattr(msg, "name") and msg.name == "reviewer_agent":
            try:
                start = msg.content.find("{")
                end = msg.content.rfind("}") + 1
                if start >= 0 and end > start:
                    review = json.loads(msg.content[start:end])
                    if review.get("passed", False):
                        return "formatter_agent"
            except (json.JSONDecodeError, KeyError):
                pass
            break

    # 检查迭代次数，防止无限循环
    iteration = state.get("iteration", 0)
    if iteration >= 3:
        return "formatter_agent"  # 超过 3 轮直接进格式检查

    return "writer_agent"  # 未通过，回写作修改


def route_after_formatter(state: PaperState) -> str:
    """格式检查 Agent 完成后：有严重问题回写作，否则结束。"""
    messages = state.get("messages", [])

    for msg in reversed(messages):
        if hasattr(msg, "name") and msg.name == "formatter_agent":
            try:
                start = msg.content.find("{")
                end = msg.content.rfind("}") + 1
                if start >= 0 and end > start:
                    fmt = json.loads(msg.content[start:end])
                    if fmt.get("passed", False):
                        return "__end__"
            except (json.JSONDecodeError, KeyError):
                pass
            break

    iteration = state.get("iteration", 0)
    if iteration >= 4:
        return "__end__"  # 防止无限循环

    return "writer_agent"
