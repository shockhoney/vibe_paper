"""LangGraph 状态图构建：去中心化多智能体工作流。"""

from langgraph.graph import StateGraph, END

from backend.agents.state import PaperState
from backend.agents.literature import literature_agent
from backend.agents.outline import outline_agent
from backend.agents.writer import writer_agent
from backend.agents.reviewer import reviewer_agent
from backend.agents.formatter import formatter_agent
from backend.agents.router import (
    route_after_literature,
    route_after_outline,
    route_after_writer,
    route_after_reviewer,
    route_after_formatter,
)


def _increment_iteration(state: PaperState) -> dict:
    """辅助节点：递增迭代计数器。"""
    return {"iteration": state.get("iteration", 0) + 1}


def build_paper_graph() -> StateGraph:
    """构建论文写作状态图。

    流程：
    literature -> outline -> writer <-> reviewer <-> formatter -> END
                                ^                      |
                                |______________________|
    """
    graph = StateGraph(PaperState)

    # 添加 Agent 节点
    graph.add_node("literature_agent", literature_agent)
    graph.add_node("outline_agent", outline_agent)
    graph.add_node("writer_agent", writer_agent)
    graph.add_node("reviewer_agent", reviewer_agent)
    graph.add_node("formatter_agent", formatter_agent)
    graph.add_node("increment_iteration", _increment_iteration)

    # 设置入口
    graph.set_entry_point("literature_agent")

    # 去中心化条件边：每个 Agent 自主决定下一步
    graph.add_conditional_edges("literature_agent", route_after_literature)
    graph.add_conditional_edges("outline_agent", route_after_outline)
    graph.add_conditional_edges("writer_agent", route_after_writer)

    # 审阅完成后先递增迭代计数
    graph.add_edge("reviewer_agent", "increment_iteration")
    graph.add_conditional_edges("increment_iteration", route_after_reviewer)

    graph.add_conditional_edges("formatter_agent", route_after_formatter)

    return graph


def get_compiled_graph():
    """获取编译后的图实例。"""
    graph = build_paper_graph()
    return graph.compile()
