import streamlit as st
from src.auth import init_session, is_logged_in

st.set_page_config(
    page_title="アプリ名",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
    </style>
""",
    unsafe_allow_html=True,
)

init_session()

if not is_logged_in():
    st.switch_page("pages/login.py")
else:
    st.switch_page("pages/home.py")
