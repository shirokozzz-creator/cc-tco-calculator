import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# 1. UI 設定
st.set_page_config(page_title="Naval Motors 鑑定防禦系統", layout="wide")
st.markdown("""
    <style>
    .main-title { font-size: 36px; font-weight: 900; color: #1E3A8A; }
    .sub-title { font-size: 16px; color: #64748B; margin-bottom: 20px; }
    </style>
    <div class='main-title'>Naval Motors 資產鑑定防禦系統 v0.5</div>
    <div class='sub-title'>實體車況決策中心 ｜ 針對性防禦隱藏瑕疵</div>
    """, unsafe_allow_html=True)

# 2. 資料引擎
def extract_color(raw_text):
    colors = ['白', '黑', '銀', '灰', '淺棕', '紅', '藍', '深灰', '鐵灰', '深綠']
    for c in colors:
        if c in str(raw_text): return c
    return '其他'

@st.cache_data
def get_model_data(model_name):
    conn = sqlite3.connect("cars_time_series.db")
    df = pd.read_sql_query(f"SELECT 出廠年月, 里程數, 得標價, 原始紀錄 FROM auctions_time_series WHERE 車系與車型 = '{model_name}'", conn)
    conn.close()
    if not df.empty:
        df['出廠年份'] = df['出廠年月'].apply(lambda x: int(float(x)))
        df['車色'] = df['原始紀錄'].apply(extract_color)
    return df

# 3. 側邊欄輸入區
try:
    models = pd.read_sql("SELECT DISTINCT 車系與車型 FROM auctions_time_series", sqlite3.connect("cars_time_series.db"))['車系與車型'].tolist()
except: models = []

st.sidebar.markdown("### 🛠️ 車況參數設定")
selected_model = st.sidebar.selectbox("評估車型", models)
df_car = get_model_data(selected_model)

if not df_car.empty:
    selected_year = st.sidebar.selectbox("出廠年份", sorted(df_car['出廠年份'].unique(), reverse=True))
    selected_color = st.sidebar.selectbox("車輛顏色", sorted(df_car['車色'].unique()))
    
    target_mileage = st.sidebar.number_input("車商標示里程 (km)", value=75000, step=5000)
    dealer_price = st.sidebar.number_input("車商售價 (TWD)", value=800000, step=10000)
    
    # 修正後的鑑定欄位
    has_third_party = st.sidebar.radio("是否有第三方鑑定書 (如 Goo/YES/萊茵)", ["是", "否"])
    is_hybrid = st.sidebar.toggle("是否為 Hybrid 車型")

    # 4. 數據篩選 (加入車色與年份)
    df_filtered = df_car[(df_car['出廠年份'] == selected_year) & (df_car['車色'] == selected_color)]
    
    # 5. 核心邏輯輸出
    if not df_filtered.empty:
        median_auction = df_filtered['得標價'].median()
        retail_floor = median_auction * 1.08
        
        st.subheader(f"🛡️ 模組一：市場盤價防禦 ({selected_year}年 {selected_color} {selected_model})")
        col1, col2, col3 = st.columns(3)
        col1.metric("批發盤價中位數", f"${median_auction:,.0f}")
        col2.metric("合理零售門檻", f"${retail_floor:,.0f}")
        
        if dealer_price < retail_floor:
            col3.error("釣魚價警示")
            st.error("🚨 售價低於盤價，極高機率為空氣車或重大瑕疵車，系統強烈建議「禁止前往」。")
        else:
            col3.success("價格合理")
            st.success("✅ 售價位於市場合理行情內，進入下一階段鑑定檢查。")

        st.subheader("📋 模組二：鑑定與物理風險")
        if has_third_party == "是":
            st.success("✅ 具備第三方鑑定書：建議買家確認書中是否有針對「骨架」、「泡水」的明確定義，切勿單看總分。")
        else:
            st.error("☠️ 無鑑定書風險：缺乏第三方背書，請務必現場確認引擎溫度、機油油漬與底盤生鏽程度。系統建議保留 10% 預備金作為隱藏風險抵扣。")

        # 顯示該車色市場分布
        st.subheader("📊 該車色市場走勢")
        df_filtered['價格(萬)'] = df_filtered['得標價'] / 10000
        st.plotly_chart(px.scatter(df_filtered, x="里程數", y="價格(萬)", title="里程 vs 成交價"), use_container_width=True)
    else:
        st.warning("該條件組合在資料庫中無足夠樣本。")
