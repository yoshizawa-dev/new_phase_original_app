import streamlit as st
from src.db.supabase_client import get_supabase


def render(CATEGORIES: dict):
    st.subheader("記録一覧")
    supabase = get_supabase()

    try:
        res = (
            supabase.table("post")
            .select(
                "post_id, item_name, visit_date, rating, price, comment, category_id, image_path,"
                "store(store_name)"
            )
            .order("visit_date", desc=True)
            .execute()
        )
        posts = res.data
    except Exception as e:
        st.error(f"データ取得に失敗しました：{e}")
        posts = []

    if not posts:
        st.info("まだ記録がありません")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_store = st.selectbox(
            "店舗名で絞り込み",
            ["すべて"] + sorted(set(p["store"]["store_name"] for p in posts)),
        )
    with col2:
        filter_category = st.selectbox(
            "カテゴリーで絞り込み", ["すべて"] + list(CATEGORIES.keys())
        )
    with col3:
        filter_rating = st.selectbox(
            "評価で絞り込み",
            ["すべて", 5, 4, 3, 2, 1],
            format_func=lambda x: "すべて" if x == "すべて" else "★" * x,
        )

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

    category_names = {v: k for k, v in CATEGORIES.items()}
    cols = st.columns(3)

# 1. バケット名の手前までのURLにする
    BASE_STORAGE_URL = "https://coxtvfeghmlvdrmgrlzf.supabase.co/storage/v1/object/public"

    for i, post in enumerate(filtered):
        with cols[i % 3]:
            with st.container(border=True):
                img_path = post.get("image_path")

                if img_path and str(img_path).strip():
                    full_url = f"{BASE_STORAGE_URL}/{str(img_path).strip()}" 
                    try:
                        st.image(full_url, use_container_width=True)
                    except Exception as e:
                        st.warning(f"画像を読み込めませんでした")
                else:
                    st.info("画像データがありません")

                st.markdown(f"### {post['item_name']}")
                st.markdown(f"🏪 {post['store']['store_name']}")
                st.markdown(f"🗓️ {post['visit_date']}")
                st.markdown(f"🏷️ {category_names.get(post['category_id'], '不明')}")
                st.markdown(f"⭐ {'★' * post['rating']}{'☆' * (5 - post['rating'])}")
                st.markdown(f"💴 ¥{post['price']:,}")
                if post["comment"]:
                    st.caption(f"💬 {post['comment']}")
