import time
import streamlit as st
import bcrypt
from src.db.supabase_client import get_supabase

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

st.title("新規会員登録")

# ── フォームの外に戻るボタン ──────────────────────
if st.button("ログインページに戻る"):
    st.switch_page("app.py")

# ── 登録フォーム ──────────────────────────────────
with st.form("register_form"):
    name = st.text_input("お名前")
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")
    password_confirm = st.text_input("パスワード（確認）", type="password")
    age = st.number_input("年齢", min_value=0, max_value=120, step=1)
    sex = st.selectbox("性別", ["M", "F"])

    submitted = st.form_submit_button("登録する", type="primary")

if submitted:
    # ── バリデーション ────────────────────────────
    if not all([name, email, password, password_confirm]):
        st.error("すべての項目を入力してください")
    elif password != password_confirm:
        st.error("パスワードが一致しません")
    else:
        # ── ハッシュ化 ────────────────────────────
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        try:
            supabase = get_supabase()
            supabase.table("user").insert(
                {
                    "name": name,
                    "email": email,
                    "password": hashed_password,
                    "age": int(age),
                    "sex": sex,
                }
            ).execute()

            # ── 2秒後にログインページへ ────────────
            st.success("✅ 登録が完了しました！2秒後にログインページへ移動します...")
            time.sleep(2)
            st.switch_page("app.py")

        except Exception as e:
            if "duplicate" in str(e).lower():
                st.error("このメールアドレスはすでに登録されています")
            else:
                st.error(f"登録に失敗しました：{e}")
