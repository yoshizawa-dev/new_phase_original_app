"""
search.py — Tech0 Search v1.3（Supabase 対応 + 日本語分かち書き）
TF-IDF ベースの検索関数（post / category / store テーブル対応）

対象フィールド（TF-IDF 検索）:
  - post.item_name
  - post.comment
  - category.category_name
  - store.store_name

返却フィールド（カード表示用）:
  - post.image_path / rating / price も含む

事前インストール:
  pip install fugashi unidic-lite
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
from datetime import datetime
import fugashi

from src.db.supabase_client import get_supabase


# ─────────────────────────────────────────────
#  日本語トークナイザー（MeCab / fugashi）
# ─────────────────────────────────────────────

# モジュールロード時に1度だけ初期化する（重い処理なのでキャッシュ）
_tagger = fugashi.Tagger()


def _tokenize(text: str) -> List[str]:
    """
    日本語テキストを形態素解析して単語リストを返す。
    TfidfVectorizer の tokenizer に渡す。

    例:
      "ストロベリーショートケーキ" → ["ストロベリー", "ショート", "ケーキ"]
      "チョコレート タルト"        → ["チョコレート", "タルト"]
    """
    return [word.surface for word in _tagger(text) if word.surface.strip()]


# ─────────────────────────────────────────────
#  データ取得ヘルパー（Supabase）
# ─────────────────────────────────────────────


def fetch_search_documents() -> List[Dict[str, Any]]:
    """
    Supabase から検索対象ドキュメントを取得する。

    post + store は FK 結合、category は FK 結合済みであれば結合取得。

    Returns:
        検索ドキュメントのリスト。各要素は以下のキーを持つ dict:
          - doc_id        : "post_{post_id}" 形式の一意 ID
          - post_id       : int
          - item_name     : str
          - comment       : str
          - category_name : str
          - store_name    : str
          - visit_date    : str（新鮮度ボーナス用）
          - image_path    : str（カード表示用）
          - rating        : int | None（カード表示用）
          - price         : int | None（カード表示用）
    """
    client = get_supabase()

    # post + store + category を結合取得
    post_res = (
        client.table("post")
        .select(
            "post_id, item_name, comment, visit_date, "
            "image_path, rating, price, category_id, "
            "category(category_name), "
            "store(store_name)"
        )
        .execute()
    )

    documents = []
    for row in post_res.data:
        category = row.get("category") or {}
        store = row.get("store") or {}

        documents.append(
            {
                "doc_id": f"post_{row['post_id']}",
                "post_id": row["post_id"],
                "item_name": row.get("item_name", "") or "",
                "comment": row.get("comment", "") or "",
                "category_name": category.get("category_name", "") or "",
                "store_name": store.get("store_name", "") or "",
                "visit_date": str(row.get("visit_date", "")) or "",
                # カード表示用（TF-IDF スコアリングには使わない）
                "image_path": row.get("image_path", "") or "",
                "rating": row.get("rating"),
                "price": row.get("price"),
            }
        )

    return documents


# ─────────────────────────────────────────────
#  TF-IDF 検索エンジン（コアロジック）
# ─────────────────────────────────────────────


class SearchEngine:
    """TF-IDF ベースの検索エンジン（日本語分かち書き対応）"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),  # ユニグラム + バイグラム
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,  # TF の対数スケーリング
            tokenizer=_tokenize,  # MeCab による日本語分かち書き
            token_pattern=None,  # tokenizer を使うので無効化
        )
        self.tfidf_matrix = None
        self.documents: List[Dict[str, Any]] = []
        self.is_fitted = False

    def build_index(self, documents: List[Dict[str, Any]]):
        """
        ドキュメントリストから TF-IDF インデックスを構築する。

        重みづけ方針:
          - item_name    : × 3（最重要）
          - store_name   : × 2
          - category_name: × 2
          - comment      : × 1（本文）
        """
        if not documents:
            return

        self.documents = documents
        corpus = []

        for doc in documents:
            text = " ".join(
                [
                    (doc["item_name"] + " ") * 3,
                    (doc["store_name"] + " ") * 2,
                    (doc["category_name"] + " ") * 2,
                    (doc["comment"] + " ") * 1,
                ]
            )
            corpus.append(text)

        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True

    def search(self, query: str, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        クエリに対して TF-IDF 検索を実行し、関連度順で返す。

        Args:
            query : 検索文字列
            top_n : 最大返却件数（デフォルト 20）

        Returns:
            スコア付き検索結果リスト。各要素に以下を追加:
              - relevance_score : 最終スコア（0〜100）
              - base_score      : TF-IDF コサイン類似度（0〜100）
        """
        if not self.is_fitted or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        results = []
        for idx, base_score in enumerate(similarities):
            if base_score > 0.01:
                doc = self.documents[idx].copy()
                final_score = self._calculate_final_score(doc, base_score, query)
                doc["relevance_score"] = round(float(final_score) * 100, 1)
                doc["base_score"] = round(float(base_score) * 100, 1)
                results.append(doc)

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_n]

    def _calculate_final_score(
        self,
        doc: Dict[str, Any],
        base_score: float,
        query: str,
    ) -> float:
        """
        TF-IDF ベーススコアに各種ボーナスを掛け合わせて最終スコアを算出する。

        ボーナス内訳:
          1. item_name 完全一致        : × 1.8
          2. item_name 部分一致        : × 1.4
          3. store_name に含まれる     : × 1.3
          4. category_name に含まれる  : × 1.2
          5. 新鮮度（90日以内）        : 最大 × 1.2
        """
        score = base_score
        q = query.lower()

        # 1 & 2. 商品名マッチボーナス
        item_name = doc.get("item_name", "").lower()
        if q == item_name:
            score *= 1.8
        elif q in item_name:
            score *= 1.4

        # 3. 店名マッチボーナス
        if q in doc.get("store_name", "").lower():
            score *= 1.3

        # 4. カテゴリマッチボーナス
        if q in doc.get("category_name", "").lower():
            score *= 1.2

        # 5. 新鮮度ボーナス（90日以内の投稿は最大 +20%）
        visit_date = doc.get("visit_date", "")
        if visit_date:
            try:
                dt = datetime.fromisoformat(str(visit_date).replace("Z", "+00:00"))
                days_old = (datetime.now() - dt.replace(tzinfo=None)).days
                if days_old <= 90:
                    score *= 1 + (0.2 * (90 - days_old) / 90)
            except Exception:
                pass

        return score


# ─────────────────────────────────────────────
#  シングルトン管理
# ─────────────────────────────────────────────

_engine: SearchEngine | None = None


def get_engine() -> SearchEngine:
    """SearchEngine のシングルトンを返す"""
    global _engine
    if _engine is None:
        _engine = SearchEngine()
    return _engine


# ─────────────────────────────────────────────
#  公開 API（外部から呼び出す関数）
# ─────────────────────────────────────────────


def build_search_index():
    """
    Supabase からドキュメントを取得してインデックスを構築する。
    アプリ起動時 / データ更新後に一度だけ呼び出す。

    使用例（tab_record_list.py など）:
        from src.research.search import build_search_index
        build_search_index()
    """
    documents = fetch_search_documents()
    engine = get_engine()
    engine.build_index(documents)


def search_posts(query: str, top_n: int = 20) -> List[Dict[str, Any]]:
    """
    キーワードで投稿を検索し、関連度順に返す。

    事前に build_search_index() を呼んでインデックスを構築しておくこと。

    Args:
        query : 検索キーワード（例: "ストロベリー"、"コーデュロイカフェ"）
        top_n : 最大返却件数（デフォルト 20）

    Returns:
        関連度スコア順の検索結果リスト。各要素:
          {
            "doc_id"         : "post_1",
            "post_id"        : 1,
            "item_name"      : "ストロベリーショートケーキ",
            "comment"        : "人気メニュー",
            "category_name"  : "ショートケーキ",
            "store_name"     : "コーデュロイカフェ CORDUROY cafe 大名店",
            "visit_date"     : "2025-05-23",
            "relevance_score": 85.3,
            "base_score"     : 60.1,
          }

    使用例:
        results = search_posts("ストロベリー")
        for r in results:
            print(r["item_name"], r["relevance_score"])
    """
    engine = get_engine()
    return engine.search(query, top_n=top_n)
