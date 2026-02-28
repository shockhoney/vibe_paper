"""Streamlit 主入口：多页面导航。"""

import sys
from pathlib import Path

# 将项目根目录加入 sys.path，使页面能导入 frontend/backend 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Vibe Paper - 多智能体论文写作助手",
    page_icon=":memo:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 页面路由
page = st.navigation([
    st.Page("pages/project.py", title="项目管理", icon=":material/folder:"),
    st.Page("pages/literature.py", title="文献管理", icon=":material/library_books:"),
    st.Page("pages/editor.py", title="论文编辑", icon=":material/edit:"),
    st.Page("pages/monitor.py", title="Agent 监控", icon=":material/monitoring:"),
])

page.run()
