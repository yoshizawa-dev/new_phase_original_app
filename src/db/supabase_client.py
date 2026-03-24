import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE"]["SUPABASE_URL"]  # ← 大文字に修正
    key = st.secrets["SUPABASE"]["SUPABASE_KEY"]  # ← 大文字に修正
    return create_client(url, key)


# Streamlitはコードを何度も再実行する仕組みのため、毎回Supabaseに接続すると無駄
# @st.cache_resource をつけると初回だけ接続して使い回す
# データベース接続など「重い処理」に使う

# get_supabase という名前の関数を定義
# -> Client は戻り値の型が Client（Supabaseクライアント）であることを示す

# client = get_supabase()

# # テーブル操作
# client.table("users")        # テーブルを指定

# # 認証
# client.auth                  # 認証関連

# # ストレージ
# client.storage               # ファイル保存関連

# client.table("users")         # usersテーブルを指定
#   .select("id, username, ...")  # 取得するカラムを指定
#   .eq("username", "admin")      # username = 'admin' の条件
#   .eq("is_active", True)        # is_active = true の条件
#   .single()                     # 1件だけ取得
#   .execute()                    # 実行
