import streamlit as st
from src.auth import authenticate, set_session, init_session

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

st.title("🔐 ログイン")
st.markdown("---")

with st.form("login_form"):
    email = st.text_input("メールアドレス", placeholder="example@email.com")
    password = st.text_input("パスワード", type="password", placeholder="password")
    submitted = st.form_submit_button("ログイン", use_container_width=True)

if submitted:
    if not email or not password:
        st.warning("メールアドレスとパスワードを入力してください")
    else:
        with st.spinner("認証中..."):
            user = authenticate(email, password)

        if user:
            set_session(user)
            st.switch_page("pages/home.py")
        else:
            st.error("メールアドレスまたはパスワードが正しくありません")

if st.button("新規会員登録", type="primary"):
    st.switch_page("pages/register.py")
