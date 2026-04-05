"""
tabs/tab_record_list.py — 記録一覧タブ
通常の絞り込み表示 + TF-IDF キーワード検索を統合したビュー
"""

import streamlit as st
from src.db.supabase_client import get_supabase
from src.research.search import build_search_index, search_posts

BASE_STORAGE_URL = "https://coxtvfeghmlvdrmgrlzf.supabase.co/storage/v1/object/public"


# ─────────────────────────────────────────────
#  インデックス初期化（セッション内で1回だけ）
# ─────────────────────────────────────────────


def _ensure_index():
    """セッション内で初回だけ TF-IDF インデックスを構築する"""
    if not st.session_state.get("search_index_built"):
        with st.spinner("検索インデックスを構築中..."):
            build_search_index()
        st.session_state["search_index_built"] = True


# ─────────────────────────────────────────────
#  カード描画ヘルパー
# ─────────────────────────────────────────────


def _render_card(post: dict, category_names: dict, show_score: bool = False):
    """1件分のカードを描画する"""
    with st.container(border=True):
        img_path = post.get("image_path")
        if img_path and str(img_path).strip():
            full_url = f"{BASE_STORAGE_URL}/{str(img_path).strip()}"
            try:
                st.image(full_url, use_container_width=True)
            except Exception:
                st.warning("画像を読み込めませんでした")
        else:
            st.info("画像データがありません")

        # 検索結果のときだけ関連度バッジを表示
        if show_score:
            score = post.get("relevance_score", 0)
            st.markdown(
                f'<div style="'
                f"display:inline-block;background:#FF6B6B;color:white;"
                f"font-size:0.75rem;font-weight:bold;"
                f"padding:2px 8px;border-radius:999px;margin-bottom:6px;"
                f'">関連度 {score}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(f"### {post['item_name']}")

        # 検索結果は store_name キーに直接入っている
        # 通常一覧は store キー（dict）経由で取得する
        store_name = post.get("store_name", "")
        if not store_name:
            store = post.get("store") or {}
            store_name = store.get("store_name", "")
        st.markdown(f"🏪 {store_name}")
        st.markdown(f"🗓️ {post.get('visit_date', '')}")

        # category_name は検索結果に直接入っている。記録一覧は category_id から逆引き
        category_label = post.get("category_name") or category_names.get(
            post.get("category_id"), "不明"
        )
        st.markdown(f"🏷️ {category_label}")

        rating = post.get("rating")
        if rating:
            st.markdown(f"⭐ {'★' * rating}{'☆' * (5 - rating)}")

        price = post.get("price")
        if price:
            st.markdown(f"💴 ¥{price:,}")

        if post.get("comment"):
            st.caption(f"💬 {post['comment']}")


# ─────────────────────────────────────────────
#  メイン render 関数
# ─────────────────────────────────────────────


def render(CATEGORIES: dict):
    st.subheader("記録一覧")

    # TF-IDF インデックスを初期化
    _ensure_index()

    # ── 検索フォーム ──────────────────────────
    with st.form(key="search_form"):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            query = st.text_input(
                label="キーワード検索",
                placeholder="例：チョコレート、コーデュロイカフェ、タルト...",
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("🔍 検索", use_container_width=True)

    # ── 検索モード ────────────────────────────
    if submitted and query.strip():
        results = search_posts(query.strip(), top_n=20)

        if not results:
            st.warning(f"「{query}」に一致する投稿が見つかりませんでした。")
            return

        st.markdown(f"**「{query}」の検索結果：{len(results)} 件**（関連度順）")

        category_names = {v: k for k, v in CATEGORIES.items()}
        cols = st.columns(3)
        for i, post in enumerate(results):
            with cols[i % 3]:
                _render_card(post, category_names, show_score=True)
        return

    # ── 通常モード（絞り込み表示） ────────────
    supabase = get_supabase()
    try:
        res = (
            supabase.table("post")
            .select(
                "post_id, item_name, visit_date, rating, price, comment,"
                " category_id, image_path,"
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

    st.markdown(f"**{len(posts)} 件**")

    category_names = {v: k for k, v in CATEGORIES.items()}
    cols = st.columns(3)
    for i, post in enumerate(posts):
        with cols[i % 3]:
            _render_card(post, category_names, show_score=False)
