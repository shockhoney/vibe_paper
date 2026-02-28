"""Agent 监控页面。"""

import json
import streamlit as st
from frontend.utils import api_get
from frontend.components.sidebar import render_sidebar
from frontend.components.chat import render_agent_messages


def render():
    render_sidebar()
    st.header("Agent 监控")

    pid = st.session_state.get("current_project_id")
    if not pid:
        st.warning("请先在侧边栏选择一个项目。")
        return

    # 自动刷新
    auto_refresh = st.toggle("自动刷新", value=True)

    try:
        status = api_get(f"/agents/status/{pid}")
    except Exception as e:
        st.error(f"无法获取状态: {e}")
        return

    # 状态指示器
    col1, col2, col3 = st.columns(3)
    with col1:
        is_running = status.get("running", False)
        st.metric("运行状态", "运行中" if is_running else "空闲")
    with col2:
        state = status.get("state", {})
        st.metric("当前 Agent", state.get("current_agent", "无"))
    with col3:
        st.metric("迭代轮次", state.get("iteration", 0))

    st.divider()

    # 最近事件
    st.subheader("执行日志")
    events = status.get("recent_events", [])
    if events:
        render_agent_messages(events)
    else:
        st.info("暂无执行记录。启动 Agent 后此处将显示实时日志。")

    # 审阅反馈
    review = state.get("review_feedback", [])
    if review:
        st.subheader("审阅反馈")
        for fb in review:
            severity = fb.get("severity", "info")
            icon = {"critical": ":red_circle:", "major": ":orange_circle:", "minor": ":large_yellow_circle:"}.get(severity, ":white_circle:")
            st.markdown(f"{icon} **[{fb.get('section', '全局')}]** {fb.get('comment', '')}")

    # 格式问题
    fmt = state.get("format_issues", [])
    if fmt:
        st.subheader("格式问题")
        for issue in fmt:
            st.markdown(f"- **{issue.get('type', '')}** [{issue.get('section', '')}]: {issue.get('detail', '')}")

    if auto_refresh and is_running:
        import time
        time.sleep(3)
        st.rerun()


if __name__ == "__main__":
    render()
