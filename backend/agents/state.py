"""LangGraph 共享状态定义。"""

from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class PaperState(TypedDict):
    """多智能体共享的论文写作状态。"""
    project_id: int
    current_agent: str                               # 当前活跃 Agent
    messages: Annotated[list[BaseMessage], add_messages]  # 对话历史（自动追加）
    outline: dict                                    # 大纲结构
    sections: dict[str, str]                         # 各章节内容 {section_title: content}
    references: list[dict]                           # 检索到的参考文献摘要
    review_feedback: list[dict]                      # 审阅意见
    format_issues: list[dict]                        # 格式问题
    iteration: int                                   # 当前迭代轮次
    status: str                                      # 整体状态: init / literature / outline / writing / reviewing / formatting / done
    user_instruction: str                            # 用户附加指令
