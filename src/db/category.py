from src.db.supabase_client import get_supabase


def get_categories() -> dict:
    """category_idをキー、category_nameを値にしたdictを返す"""
    supabase = get_supabase()
    res = supabase.table("category").select("category_id, category_name").execute()
    return {row["category_name"]: row["category_id"] for row in res.data}
