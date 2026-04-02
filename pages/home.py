import streamlit as st
from src.auth import require_login
from src.db.category import get_categories
from tabs import tab_record_add, tab_record_list, tab_store, tab_analysis

# --- ページ設定 ---
st.set_page_config(
    page_title="アプリ名",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- サイドバー非表示 ---
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

# --- ログインチェック ---
require_login()

# --- カテゴリー取得 ---
CATEGORIES = get_categories()

st.title("🍰 スイーツ記録")

# --- タブ ---
tab1, tab2, tab3, tab4 = st.tabs(["記録追加", "記録一覧", "店舗登録", "データ分析"])

# =========================
# 記録追加
# =========================
with tab1:
    tab_record_add.render(CATEGORIES)

# =========================
# 記録一覧
# =========================
with tab2:
    tab_record_list.render(CATEGORIES)

# =========================
# 店舗登録
# =========================
with tab3:
    tab_store.render()

# =========================
# データ分析
# =========================
with tab4:
    tab_analysis.render()