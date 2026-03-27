import streamlit as st
from datetime import date
from src.auth import require_login, get_user_id
from src.db.supabase_client import get_supabase
from src.db.supabase_client import get_supabase
from src.db.category import get_categories
from tabs import tab_record_add, tab_record_list, tab_store, tab_analysis


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

# sessionの状態確認
require_login()

# ── カテゴリーリスト（category_idと紐付け）──
CATEGORIES = get_categories()

st.title("🍰 スイーツ記録")

tab1, tab2, tab3, tab4 = st.tabs(["記録追加", "記録一覧", "店舗登録", "データ分析"])

with tab1:
    st.subheader("記録追加")

    supabase = get_supabase()

    # ── 店舗リストをSupabaseから取得 ──
    try:
        store_res = supabase.table("store").select("store_id, store_name").execute()
        store_list = {row["store_name"]: row["store_id"] for row in store_res.data}
    except Exception as e:
        st.error(f"店舗情報の取得に失敗しました：{e}")
        store_list = {}

    with st.form("record_form"):
        store_name = st.selectbox("店舗名", list(store_list.keys()))
        visit_date = st.date_input("来店日", value=date.today())
        item_name = st.text_input("商品名", placeholder="商品名を入力")
        category = st.selectbox("カテゴリー", list(CATEGORIES.keys()))
        rating = st.select_slider(
            "評価", options=[1, 2, 3, 4, 5], value=3, format_func=lambda x: "★" * x
        )
        price = st.number_input("価格", min_value=0, step=10)
        comment = st.text_area("コメント", placeholder="コメントを入力")

        submitted = st.form_submit_button(
            "投稿する", type="primary", use_container_width=True
        )

    if submitted:
        if not item_name:
            st.warning("商品名は必須です")
        else:
            try:
                supabase.table("post").insert(
                    {
                        "user_id": get_user_id(),
                        "store_id": store_list[store_name],
                        "category_id": CATEGORIES[category],
                        "visit_date": str(visit_date),
                        "item_name": item_name,
                        "image_path": "",
                        "comment": comment,
                        "rating": rating,
                        "price": int(price),
                    }
                ).execute()

                st.success("✅ 投稿しました！")

            except Exception as e:
                st.error(f"投稿に失敗しました：{e}")

with tab2:
    st.subheader("記録一覧")

    supabase = get_supabase()

    # ── データ取得（postとstoreをJOIN）──
    try:
        res = (
            supabase.table("post")
            .select(
                "post_id, item_name, visit_date, rating, price, comment, category_id, "
                "store(store_name)"
            )
            .order("visit_date", desc=True)
            .execute()
        )
        posts = res.data
    except Exception as e:
        st.error(f"データ取得に失敗しました：{e}")
        posts = []

    if posts:
        # ── 絞り込みUI ──────────────────────────
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_store = st.selectbox(
                "店舗名で絞り込み",
                ["すべて"] + sorted(set(p["store"]["store_name"] for p in posts)),
            )
        with col2:
            category_names = {v: k for k, v in CATEGORIES.items()}
            filter_category = st.selectbox(
                "カテゴリーで絞り込み", ["すべて"] + list(CATEGORIES.keys())
            )
        with col3:
            filter_rating = st.selectbox(
                "評価で絞り込み",
                ["すべて", 5, 4, 3, 2, 1],
                format_func=lambda x: "すべて" if x == "すべて" else "★" * x,
            )

        # ── 絞り込み処理 ──────────────────────────
        filtered = posts
        if filter_store != "すべて":
            filtered = [p for p in filtered if p["store"]["store_name"] == filter_store]
        if filter_category != "すべて":
            filtered = [
                p for p in filtered if p["category_id"] == CATEGORIES[filter_category]
            ]
        if filter_rating != "すべて":
            filtered = [p for p in filtered if p["rating"] == filter_rating]

        st.markdown(f"**{len(filtered)} 件**")

        # ── カード表示（3列）──────────────────────
        cols = st.columns(3)
        for i, post in enumerate(filtered):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"### {post['item_name']}")
                    st.markdown(f"🏪 {post['store']['store_name']}")
                    st.markdown(f"🗓️ {post['visit_date']}")
                    st.markdown(f"🏷️ {category_names.get(post['category_id'], '不明')}")
                    st.markdown(
                        f"⭐ {'★' * post['rating']}{'☆' * (5 - post['rating'])}"
                    )
                    st.markdown(f"💴 ¥{post['price']:,}")
                    if post["comment"]:
                        st.caption(f"💬 {post['comment']}")
    else:
        st.info("まだ記録がありません")


with tab3:
    st.subheader("店舗登録")


with tab4:
    st.subheader("データ分析")
