"""文献管理页面。"""

import streamlit as st
from frontend.utils import api_get, api_post, api_delete
from frontend.components.sidebar import render_sidebar


def render():
    render_sidebar()
    st.header("文献管理")

    pid = st.session_state.get("current_project_id")
    if not pid:
        st.warning("请先在侧边栏选择一个项目。")
        return

    # 上传文献
    st.subheader("上传文献 PDF")
    uploaded = st.file_uploader("选择 PDF 文件", type=["pdf"], accept_multiple_files=True)
    if uploaded and st.button("上传并解析"):
        for f in uploaded:
            with st.spinner(f"正在解析 {f.name}..."):
                try:
                    api_post(
                        f"/literature/upload/{pid}",
                        files={"file": (f.name, f.getvalue(), "application/pdf")},
                    )
                    st.success(f"{f.name} 上传成功")
                except Exception as e:
                    st.error(f"{f.name} 上传失败: {e}")
        st.rerun()

    # 文献列表
    st.subheader("已上传文献")
    try:
        refs = api_get(f"/literature/{pid}")
    except Exception:
        refs = []

    if not refs:
        st.info("暂无文献，请上传 PDF。")
        return

    for r in refs:
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{r['title']}**")
                info_parts = []
                if r.get("authors"):
                    info_parts.append(r["authors"])
                if r.get("year"):
                    info_parts.append(str(r["year"]))
                if r.get("doi"):
                    info_parts.append(f"DOI: {r['doi']}")
                if info_parts:
                    st.caption(" | ".join(info_parts))
                if r.get("abstract"):
                    with st.expander("查看摘要"):
                        st.write(r["abstract"])
            with col2:
                if st.button("删除", key=f"ref_del_{r['id']}"):
                    api_delete(f"/literature/{r['id']}")
                    st.rerun()


if __name__ == "__main__":
    render()
