import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# 1. UI 與系統設定 (注入 Naval Motors 視覺風格)
st.set_page_config(page_title="Naval Motors 資產防禦系統", layout="wide")

# 自定義標題色彩樣式 (Premium Look)
st.markdown("""
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 900;
        color: #1E3A8A; /* 深海軍藍 */
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 18px;
        color: #64748B; /* 科技灰 */
        margin-bottom: 30px;
    }
    .highlight-red { color: #DC2626; font-weight: bold; }
    .highlight-green { color: #059669; font-weight: bold; }
    </style>
    <div class='main-title'>Naval Motors 總體持有成本 (TCO) 系統 v0.4</div>
    <div class='sub-title'>台版專屬資產防禦報告 ｜ 數據解析與風險量化</div>
    """, unsafe_allow_html=True)

# 2. 資料萃取引擎 (加入車色萃取邏輯)
def extract_color(raw_text):
    # 定義台灣市場常見車色關鍵字
    colors = ['白', '黑', '銀', '灰', '淺棕', '紅', '藍', '深灰', '鐵灰', '深綠']
    for c in colors:
        if c in str(raw_text):
            return c
    return '其他'

@st.cache_data
def get_model_data(model_name):
    conn = sqlite3.connect("cars_time_series.db")
    query = f"SELECT 成交月份, 出廠年月, 車輛評價, 里程數, 得標價, 原始紀錄 FROM auctions_time_series WHERE 車系與車型 = '{model_name}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df['出廠年份'] = df['出廠年月'].apply(lambda x: int(float(x)))
        # 動態萃取車色
        df['車色'] = df['原始紀錄'].apply(extract_color)
    return df

# 3. 系統初始化與資料庫掃描
try:
    conn = sqlite3.connect("cars_time_series.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT 車系與車型 FROM auctions_time_series")
    models = [row[0] for row in cursor.fetchall()]
    conn.close()
except Exception as e:
    st.error(f"資料庫掛載失敗: {e}")
    st.stop()

# 4. 前端引流與參數輸入區 (側邊欄)
st.sidebar.markdown("### ⚙️ 1. 目標車輛現況")
selected_model = st.sidebar.selectbox("評估車型", models, index=models.index('NX200') if 'NX200' in models else 0)

df_car_full = get_model_data(selected_model)

if not df_car_full.empty:
    available_years = sorted(df_car_full['出廠年份'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("出廠年份", available_years)
    
    target_mileage = st.sidebar.number_input("車商標示里程數 (km)", min_value=0, value=75000, step=5000)
    dealer_price = st.sidebar.number_input("終端車商開價 (TWD)", min_value=100000, value=850000, step=10000)
    
    # 台灣特有防呆選項
    cert_level = st.sidebar.selectbox("檢附第三方認證狀態", ["Tier 1: Goo/YES/萊茵", "Tier 2: SAVE/SUM/HOT 聯盟", "Tier 3: 無認證 / 車行自保"])
    is_hybrid = st.sidebar.toggle("此車為 Hybrid 油電混合車型")

    st.sidebar.markdown("### 🏦 2. 財務工程參數")
    loan_rate = st.sidebar.slider("預計車貸利率 (%)", 2.0, 16.0, 6.0, 0.5)

    # 5. 過濾指定年份數據
    df_target_year = df_car_full[df_car_full['出廠年份'] == selected_year]

    if not df_target_year.empty:
        # 商業邏輯 A：定價與釣魚防禦
        median_auction = df_target_year['得標價'].median()
        retail_floor = median_auction * 1.08  # 台灣車商合理毛利抓 8%
        
        st.subheader(f"🛡️ 模組一：市場盤價解密 ({selected_year}年 {selected_model})")
        col1, col2, col3 = st.columns(3)
        col1.metric("行內批發底價中位數", f"${median_auction:,.0f}")
        col2.metric("合理零售樓地板 (+8%)", f"${retail_floor:,.0f}")
        
        price_diff = dealer_price - retail_floor
        if dealer_price < retail_floor:
            col3.metric("價格溢價空間", f"${price_diff:,.0f}", delta_color="inverse")
            st.error(f"🚨 **釣魚價/重大瑕疵警報**：此開價低於全台批發盤價樓地板。高機率為 8891 釣魚空氣車或重大事故車，請拒絕前往看車。")
        else:
            col3.metric("價格溢價空間", f"+${price_diff:,.0f}", delta_color="normal")
            st.success("✅ 開價位於合理套利空間之上，未觸發低價釣魚警示。")

        st.markdown("---")

        # 商業邏輯 B：認證防禦力
        st.subheader("📋 模組二：實體車況風險折現")
        if cert_level == "Tier 1: Goo/YES/萊茵":
            st.success("✅ **具備頂級防禦**：具備獨立第三方鑑定，車況透明度高。")
        elif cert_level == "Tier 2: SAVE/SUM/HOT 聯盟":
            st.warning("⚠️ **中度防禦風險**：聯盟鑑定員具備球員兼裁判性質，簽約時務必加註「保證非營業用車與無泡水，否則原價買回」。")
        else:
            st.error("☠️ **致命結構風險**：缺乏獨立鑑定。統計上買到重大修復歷車輛機率極高，系統建議將購車預算額外扣除 15% 作為風險準備金。")

        st.markdown("---")

        # 視覺化：市場散佈圖 (加入車色映射)
        st.subheader(f"📊 模組三：{selected_year}年 {selected_model} 市場散佈圖 (顏色分析)")
        df_target_year_plot = df_target_year.copy()
        df_target_year_plot['價格(萬)'] = df_target_year_plot['得標價'] / 10000
        
        # 定義車色的視覺對應字典，讓圖表顏色與真實車色一致
        color_map = {
            '白': '#F8FAFC', '黑': '#0F172A', '銀': '#94A3B8', '灰': '#475569', 
            '淺棕': '#D6D3D1', '紅': '#EF4444', '藍': '#3B82F6', '其他': '#10B981'
        }
        
        fig = px.scatter(
            df_target_year_plot, 
            x="里程數", 
            y="價格(萬)", 
            color="車色", 
            color_discrete_map=color_map,
            hover_data=["車輛評價"],
            title=f"市場交易車色分布與價格折舊曲線"
        )
        # 優化圖表背景，讓白色車的點也看得清楚
        fig.update_layout(plot_bgcolor='#E2E8F0', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning(f"資料庫中無 {selected_year} 年份的 {selected_model} 數據。")
else:
    st.warning("資料庫中無此車型數據。")
