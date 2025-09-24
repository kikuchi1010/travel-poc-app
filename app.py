import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st

# Local modules
from utils.data_loader import (
    load_regions_countries,
    load_spots_df,
    load_costs_df,
    load_airfare_df,
)
from utils.estimators import (
    estimate_airfare_jpy,
    estimate_daily_cost,
    total_budget_range,
)

st.set_page_config(page_title="Travel Idea Finder (PoC)", page_icon="🧭", layout="wide")

# -----------------------------
# Session bootstrap
# -----------------------------
if "compare_items" not in st.session_state:
    st.session_state.compare_items = []  # {country_iso2, name, days, cost_level, month}

# -----------------------------
# Header
# -----------------------------
st.title("🧭 ざっくり観光地 & 概算予算 PoC")
st.caption(
    "エリア→国→目的タグを選ぶと、代表的な観光地と概算費用（成田発の航空券＋滞在費）を試算します。\n"
    "※価格はダミーデータ（モック）です。将来API接続で置換可能。"
)

# -----------------------------
# Sidebar: Filters
# -----------------------------
with st.sidebar:
    st.header("検索条件")

    regions = load_regions_countries()
    region = st.selectbox("エリア", list(regions.keys()), index=0)

    countries = regions[region]
    country_label_list = [f"{c['flag']} {c['name_ja']} ({c['name_en']})" for c in countries]
    country_idx = st.selectbox("国", list(range(len(country_label_list))), format_func=lambda i: country_label_list[i])
    current_country = countries[country_idx]
    country_iso2 = current_country["iso2"]

    tags_all = [
        "世界遺産","料理","自然","都市散策","写真映え","建築","歴史","ナイトライフ","クルーズ","ハイキング"
    ]
    selected_tags = st.multiselect("目的タグ（複数可）", tags_all, default=["世界遺産","料理"]) 

    # Month options from airfare cache (plus '指定なし')
    airfare_df_all = load_airfare_df()
    month_options = ["指定なし"] + sorted(list({m for m in airfare_df_all["month"].dropna().unique()}))
    month_label = st.selectbox("旅行月（任意）", month_options, index=0)
    month_val = None if month_label == "指定なし" else month_label

    origin = st.selectbox("出発空港", ["NRT（成田）"], index=0)
    days = st.slider("旅行日数", min_value=3, max_value=21, value=7, step=1)
    cost_level = st.select_slider("滞在費の基準", options=["low","med","high"], value="med")

    st.markdown("---")
    st.caption("※本PoCでは航空券・滞在費はモックデータから算出しています。API連携時はSecretsにキーを保存してください。")

# -----------------------------
# Load data
# -----------------------------
spots_df = load_spots_df()
cost_df = load_costs_df()
airfare_df = airfare_df_all

# Filter & rank spots for the country
_df = spots_df[spots_df["country_iso2"] == country_iso2].copy()
if selected_tags:
    _df["tag_score"] = _df["tags"].apply(lambda ts: sum(1 for t in ts if t in selected_tags))
    _df = _df.sort_values(["tag_score"], ascending=False, kind="mergesort")
else:
    _df["tag_score"] = 0

# Estimates
airfare_median, airfare_min = estimate_airfare_jpy(airfare_df, origin="NRT", country_iso2=country_iso2, month=month_val)
daily_cost = estimate_daily_cost(cost_df, country_iso2=country_iso2, level=cost_level)
low_total, high_total = total_budget_range(airfare_median, daily_cost, days)

# -----------------------------
# Summary row
# -----------------------------
colA, colB, colC = st.columns([2, 2, 3])
with colA:
    st.subheader("🗺️ 選択中")
    st.write(f"**{region} / {current_country['flag']} {current_country['name_ja']} ({current_country['name_en']})**")
    st.write(f"旅行日数: **{days}日** / 滞在費レベル: **{cost_level}**")

with colB:
    st.subheader("💰 概算費用")
    if airfare_median and daily_cost:
        st.write(f"航空券(中央値): **¥{airfare_median:,}** / 1日あたり滞在費: **¥{daily_cost:,}**")
        st.write(f"合計（{days}日）: **¥{low_total:,} – ¥{high_total:,}**")
    else:
        st.info("価格データが不足しています（PoCモック）。")

with colC:
    st.subheader("🗓 ベストシーズン")
    top3 = _df.head(3)["best_months"].dropna().tolist()
    st.write(" / ".join(top3) if top3 else "—")

st.markdown("---")

# -----------------------------
# Results list (cards)
# -----------------------------
st.subheader("🎯 候補スポット")
if _df.empty:
    st.warning("候補が見つかりませんでした。タグを減らして再検索してください。")
else:
    for _, row in _df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
            with c1:
                st.markdown(f"### {row['name']}")
                st.caption(f"{row['country_ja']}｜タグ: {', '.join(row['tags'])}")
                st.write(row.get("summary", ""))
            with c2:
                st.write("**ベストシーズン**")
                st.write(row.get("best_months", "—"))
                st.write("**体験タイプ**")
                st.write(row.get("type", "—"))
            with c3:
                if airfare_median and daily_cost:
                    low_i, high_i = total_budget_range(airfare_median, daily_cost, days)
                    st.metric("概算合計", f"¥{low_i:,} – ¥{high_i:,}")
                else:
                    st.metric("概算合計", "—")
            with c4:
                st.write("地点（緯度, 経度）")
                st.write(f"{float(row['lat']):.2f}, {float(row['lng']):.2f}")
                if st.button("比較に追加", key=f"add_{row['name']}"):
                    st.session_state.compare_items.append({
                        "country_iso2": row["country_iso2"],
                        "name": row["name"],
                        "days": days,
                        "cost_level": cost_level,
                        "month": month_val,
                    })
                    st.success("比較に追加しました。（ページ上部メニュー『🧮 比較ビュー』で確認）")

st.markdown("")
st.info("**注意**：表示中の価格はPoC用の目安値です。実際の航空券・ホテル料金は検索時点で変動します。")

st.markdown("---")
st.caption("© Travel Idea Finder PoC — Data: mock + curated; Currency: JPY")
