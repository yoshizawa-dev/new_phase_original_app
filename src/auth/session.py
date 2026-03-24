import streamlit as st

# セッションキーの定数
SESSION_KEYS = {
    "logged_in": False,
    "user_id": None,
    "name": None,  # 表示名（DB: name）
    "email": None,  # メールアドレス（DB: email）
    "age": None,  # 年齢（DB: age）
    "sex": None,  # 性別 "M" / "F"（DB: sex）
}


def init_session():
    """セッションの初期化（未セットのキーのみ）"""
    for key, default in SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def set_session(user: dict):
    """認証成功後にセッションへユーザー情報をセット"""
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["user_id"]
    st.session_state["name"] = user["name"]
    st.session_state["email"] = user["email"]
    st.session_state["age"] = user["age"]
    st.session_state["sex"] = user["sex"]


def clear_session():
    """ログアウト時にセッションをクリア"""
    for key, default in SESSION_KEYS.items():
        st.session_state[key] = default


def is_logged_in() -> bool:
    """ログイン状態を確認"""
    return st.session_state.get("logged_in", False)


def get_user_id() -> int | None:
    """ログイン中のuser_idを取得"""
    return st.session_state.get("user_id")


def get_name() -> str | None:
    """ログイン中のユーザー名を取得"""
    return st.session_state.get("name")


def get_email() -> str | None:
    """ログイン中のメールアドレスを取得"""
    return st.session_state.get("email")


def get_sex() -> str | None:
    """ログイン中の性別を取得（'M' or 'F'）"""
    return st.session_state.get("sex")


def require_login():
    """未ログインならログインページにリダイレクト"""
    init_session()
    if not is_logged_in():
        st.switch_page("app.py")
