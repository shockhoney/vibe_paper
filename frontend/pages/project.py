"""项目管理页面。"""

import streamlit as st
from frontend.utils import api_get, api_post, api_patch, api_delete
from frontend.components.sidebar import render_sidebar


def render():
    render_sidebar()
    st.header("项目管理")

    # 创建新项目
    with st.expander("创建新项目", expanded=False):
        title = st.text_input("论文标题")
        abstract = st.text_area("摘要（可选）")
        if st.button("创建"):
            if title:
                api_post("/papers/projects", {"title": title, "abstract": abstract})
                st.success("项目创建成功")
                st.rerun()
            else:
                st.warning("请输入标题")

    # 项目列表
    st.subheader("项目列表")
    try:
        projects = api_get("/papers/projects")
    except Exception as e:
        st.error(f"无法连接后端服务: {e}")
        return

    if not projects:
        st.info("暂无项目")
        return

    for p in projects:
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.markdown(f"**{p['title']}**")
                if p["abstract"]:
                    st.caption(p["abstract"][:100])
            with col2:
                status_colors = {"draft": "blue", "writing": "orange", "reviewing": "violet", "done": "green"}
                st.markdown(f":{status_colors.get(p['status'], 'gray')}[{p['status']}]")
                st.caption(p["created_at"][:10])
            with col3:
                if st.button("删除", key=f"del_{p['id']}"):
                    api_delete(f"/papers/projects/{p['id']}")
                    st.rerun()


if __name__ == "__main__":
    render()
