import streamlit as st
from datetime import date
from src.auth import get_user_id
from src.db.supabase_client import get_supabase


def render(CATEGORIES: dict):
    st.subheader("記録追加")

    supabase = get_supabase()

    # --- 店舗リスト取得 ---
    try:
        store_res = supabase.table("store").select("store_id, store_name").execute()
        store_list = {row["store_name"]: row["store_id"] for row in store_res.data}
    except Exception as e:
        st.error(f"店舗情報の取得に失敗しました：{e}")
        store_list = {}
    
    # --- 画像アップロード ---
    uploaded_file = st.file_uploader("写真をアップロード", type=["jpg", "png"])

    # --- フォーム ---
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

    # --- 投稿処理 ---
    if submitted:
        if not item_name:
            st.warning("商品名は必須です")
        else:
            try:
                image_url = ""

                # --- 画像アップロード処理 ---
                if uploaded_file is not None:
                    file_path = f"post/{get_user_id()}_{uploaded_file.name}"

                    # アップロード
                    supabase.storage.from_("images").upload(
                        file_path,
                        uploaded_file.getvalue(),
                    )

                    # 公開URL取得
                    public_url = supabase.storage.from_("images").get_public_url(file_path)

                    # get_public_url の戻り値対策
                    if isinstance(public_url, dict):
                        image_url = public_url.get("publicUrl", "")
                    else:
                        image_url = public_url

                # --- DB保存 ---
                supabase.table("post").insert(
                    {
                        "user_id": get_user_id(),
                        "store_id": store_list[store_name],
                        "category_id": CATEGORIES[category],
                        "visit_date": str(visit_date),
                        "item_name": item_name,
                        "image_path": image_url,
                        "comment": comment,
                        "rating": rating,
                        "price": int(price),
                    }
                ).execute()

                st.success("✅ 投稿しました！")

            except Exception as e:
                st.error(f"投稿に失敗しました：{e}")