"""论文编辑页面。"""

import json
import streamlit as st
from frontend.utils import api_get, api_post, api_patch
from frontend.components.sidebar import render_sidebar


def render():
    render_sidebar()
    st.header("论文编辑")

    pid = st.session_state.get("current_project_id")
    if not pid:
        st.warning("请先在侧边栏选择一个项目。")
        return

    # Agent 状态
    try:
        status = api_get(f"/agents/status/{pid}")
    except Exception:
        status = {"running": False, "state": {}}

    agent_state = status.get("state", {})

    # 启动 Agent 写作
    col_start, col_stop = st.columns(2)
    with col_start:
        instruction = st.text_input("写作指令", placeholder="例如：请撰写关于掌纹识别的论文")
        if st.button("启动 Agent 写作", disabled=status.get("running", False)):
            try:
                api_post("/agents/start", {"project_id": pid, "instruction": instruction})
                st.success("Agent 已启动")
                st.rerun()
            except Exception as e:
                st.error(f"启动失败: {e}")
    with col_stop:
        if status.get("running"):
            st.warning("Agent 正在运行...")
            if st.button("停止"):
                api_post(f"/agents/stop/{pid}")
                st.rerun()

    st.divider()

    # 大纲展示
    outline = agent_state.get("outline", {})
    if outline:
        st.subheader("论文大纲")
        if outline.get("title"):
            st.markdown(f"### {outline['title']}")
        for sec in outline.get("sections", []):
            st.markdown(f"**{sec.get('id', '')} {sec.get('title', '')}**")
            if sec.get("description"):
                st.caption(sec["description"])
            for sub in sec.get("subsections", []):
                st.markdown(f"  - {sub.get('id', '')} {sub.get('title', '')}")

    # 章节内容编辑
    sections = agent_state.get("sections", {})
    if sections:
        st.subheader("章节内容")
        tabs = st.tabs(list(sections.keys()))
        for tab, (title, content) in zip(tabs, sections.items()):
            with tab:
                edited = st.text_area(f"编辑 - {title}", value=content, height=400, key=f"edit_{title}")
                if edited != content and st.button("保存修改", key=f"save_{title}"):
                    # 将修改写回 Redis 状态
                    sections[title] = edited
                    st.success("已保存")

    # 反馈区
    st.subheader("向 Agent 发送反馈")
    feedback = st.text_area("你的修改建议")
    if st.button("发送反馈") and feedback:
        api_post("/agents/feedback", {
            "project_id": pid,
            "feedback": feedback,
        })
        st.success("反馈已发送，下次 Agent 运行时将参考此反馈。")


if __name__ == "__main__":
    render()
