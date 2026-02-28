"""Agent 对话组件：展示 Agent 消息流。"""

import streamlit as st


def render_agent_messages(events: list[dict]):
    """渲染 Agent 事件消息列表。"""
    agent_icons = {
        "literature_agent": "📚",
        "outline_agent": "📄",
        "writer_agent": "📝",
        "reviewer_agent": "🔍",
        "formatter_agent": "🎨",
        "error": "❌",
    }

    for event in events:
        agent = event.get("agent", "system")
        icon = agent_icons.get(agent, "🤖")
        label = agent.replace("_agent", "").replace("_", " ").title()

        with st.chat_message(label, avatar=icon):
            data = event.get("data", "")
            # 截断过长的输出
            if len(data) > 2000:
                data = data[:2000] + "..."
            st.markdown(data)
