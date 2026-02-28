"""侧边栏组件：项目切换和导航。"""

import streamlit as st
from frontend.utils import api_get


def render_sidebar():
    """渲染侧边栏：项目选择和页面导航。"""
    with st.sidebar:
        st.title("Vibe Paper")
        st.caption("多智能体论文写作助手")
        st.divider()

        # 加载项目列表
        try:
            projects = api_get("/papers/projects")
        except Exception:
            projects = []

        if projects:
            project_names = {p["id"]: p["title"] for p in projects}
            selected_id = st.selectbox(
                "当前项目",
                options=list(project_names.keys()),
                format_func=lambda x: project_names[x],
            )
            st.session_state["current_project_id"] = selected_id
        else:
            st.info("暂无项目，请在项目管理页面创建。")
            st.session_state["current_project_id"] = None
