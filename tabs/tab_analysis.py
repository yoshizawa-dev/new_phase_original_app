"""
tabs/tab_analysis.py — データ分析タブ（評価スコアBI）
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.db.supabase_client import get_supabase


# ─────────────────────────────────────────────
#  データ取得
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def _fetch_posts():
    """post + store + category を結合して取得"""
    supabase = get_supabase()
    res = (
        supabase.table("post")
        .select(
            "post_id, item_name, visit_date, rating, price, comment,"
            " category_id, store_id,"
            "store(store_name),"
            "category(category_name)"
        )
        .order("visit_date", desc=True)
        .execute()
    )
    rows = res.data
    if not rows:
        return pd.DataFrame()

    # フラット化
    for r in rows:
        r["store_name"] = (r.pop("store", None) or {}).get("store_name", "不明")
        r["category_name"] = (r.pop("category", None) or {}).get("category_name", "不明")
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
#  KPI カード
# ─────────────────────────────────────────────

def _render_kpi(df: pd.DataFrame):
    cols = st.columns(4)
    with cols[0]:
        st.metric("投稿数", f"{len(df)} 件")
    with cols[1]:
        st.metric("平均スコア", f"{df['rating'].mean():.2f}")
    with cols[2]:
        mode_val = df["rating"].mode().iloc[0]
        st.metric("最頻スコア", f"⭐ {int(mode_val)}")
    with cols[3]:
        avg_price = df["price"].dropna().mean()
        st.metric("平均価格", f"¥{avg_price:,.0f}" if pd.notna(avg_price) else "—")


# ─────────────────────────────────────────────
#  グラフ描画
# ─────────────────────────────────────────────

def _chart_rating_distribution(df: pd.DataFrame):
    """評価スコアの全体分布（棒グラフ）"""
    st.markdown("#### 📊 評価スコアの分布")
    counts = df["rating"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0).sort_index()
    fig = px.bar(
        x=counts.index.astype(str),
        y=counts.values,
        labels={"x": "評価（★）", "y": "件数"},
        color=counts.values,
        color_continuous_scale="Oranges",
        text=counts.values,
    )
    fig.update_layout(
        showlegend=False, coloraxis_showscale=False,
        xaxis_title="評価（★）", yaxis_title="件数",
        height=350, margin=dict(t=20, b=40),
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


def _chart_category_avg(df: pd.DataFrame):
    """カテゴリ別 平均評価（横棒グラフ）"""
    st.markdown("#### 🏷️ カテゴリ別 平均評価")
    cat_avg = (
        df.groupby("category_name")["rating"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "平均評価", "count": "件数"})
        .query("件数 >= 2")
        .sort_values("平均評価", ascending=True)
    )
    if cat_avg.empty:
        st.info("表示に必要なデータが不足しています（2件以上のカテゴリが必要）")
        return
    fig = px.bar(
        cat_avg,
        x="平均評価",
        y=cat_avg.index,
        orientation="h",
        text=cat_avg["平均評価"].round(2),
        color="平均評価",
        color_continuous_scale="YlOrRd",
        hover_data={"件数": True},
    )
    fig.update_layout(
        coloraxis_showscale=False,
        xaxis=dict(range=[0, 5.5], title="平均評価"),
        yaxis_title="",
        height=max(300, len(cat_avg) * 32 + 60),
        margin=dict(t=20, b=40),
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


def _chart_store_top(df: pd.DataFrame, top_n: int = 10):
    """店舗別 平均評価 TOP N（横棒グラフ）"""
    st.markdown(f"#### 🏪 店舗別 平均評価 TOP{top_n}")
    store_avg = (
        df.groupby("store_name")["rating"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "平均評価", "count": "件数"})
        .query("件数 >= 1")
        .sort_values("平均評価", ascending=False)
        .head(top_n)
        .sort_values("平均評価", ascending=True)
    )
    if store_avg.empty:
        st.info("表示に必要なデータが不足しています")
        return
    fig = px.bar(
        store_avg,
        x="平均評価",
        y=store_avg.index,
        orientation="h",
        text=store_avg["平均評価"].round(2),
        color="平均評価",
        color_continuous_scale="Blues",
        hover_data={"件数": True},
    )
    fig.update_layout(
        coloraxis_showscale=False,
        xaxis=dict(range=[0, 5.5], title="平均評価"),
        yaxis_title="",
        height=max(300, len(store_avg) * 32 + 60),
        margin=dict(t=20, b=40),
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
#  メイン render 関数
# ─────────────────────────────────────────────

def render():
    st.subheader("📈 データ分析")

    df = _fetch_posts()

    if df.empty:
        st.info("まだ記録がありません。記録を追加すると分析結果が表示されます。")
        return

    # KPI
    _render_kpi(df)

    st.divider()

    # 評価スコア分布
    _chart_rating_distribution(df)

    st.divider()

    # カテゴリ別・店舗別（2カラム）
    col_left, col_right = st.columns(2)
    with col_left:
        _chart_category_avg(df)
    with col_right:
        _chart_store_top(df)