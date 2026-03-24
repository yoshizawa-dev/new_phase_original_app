import bcrypt
from src.db.supabase_client import get_supabase


def authenticate(email: str, password: str) -> dict | None:
    """
    メールアドレスとパスワードで認証する。
    成功時はユーザー情報のdictを返す。失敗時はNoneを返す。
    """
    try:
        supabase = get_supabase()
        response = supabase.table("user").select("*").eq("email", email).execute()

        if not response.data:
            return None  # メールアドレスが存在しない

        user = response.data[0]

        # パスワード照合
        is_valid = bcrypt.checkpw(
            password.encode("utf-8"), user["password"].encode("utf-8")
        )

        if not is_valid:
            return None  # パスワード不一致

        return user  # 認証成功

    except Exception as e:
        raise RuntimeError(f"認証中にエラーが発生しました: {e}")
