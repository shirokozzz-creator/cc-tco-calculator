import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px

# ==========================================
# 1. UI 與 Naval Motors 視覺規範
# ==========================================
st.set_page_config(page_title="Naval Motors 鑑定防禦系統", layout="wide")
st.markdown("""
    <style>
    .main-title { font-size: 36px; font-weight: 900; color: #1E3A8A; }
    .sub-title { font-size: 16px; color: #64748B; margin-bottom: 20px; }
    .metric-box { padding: 10px; border-radius: 5px; background-color: #F1F5F9; border-left: 4px solid #3B82F6; margin-bottom: 10px;}
    </style>
    <div class='main-title'>Naval Motors 資產量化防禦系統 v0.7</div>
    <div class='sub-title'>動態資料衍生物引擎啟動 ｜ 流動性與物理折現率精算 TWD</div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料萃取與清洗引擎
# ==========================================
def extract_color(raw_text):
    colors = ['白', '黑', '銀', '灰', '淺棕', '紅', '藍', '深灰', '鐵灰', '深綠']
    for c in colors:
        if c in str(raw_text): return c
    return '其他'

@st.cache_data
def get_model_data(model_name):
    conn = sqlite3.connect("cars_time_series.db")
    df = pd.read_sql_query(f"SELECT 成交月份, 出廠年月, 車輛評價, 里程數, 得標價, 原始紀錄 FROM auctions_time_series WHERE 車系與車型 = '{model_name}'", conn)
    conn.close()
    if not df.empty:
        df['出廠年份'] = df['出廠年月'].apply(lambda x: int(float(x)))
        df['車色'] = df['原始紀錄'].apply(extract_color)
        df['車輛評價'] = df['車輛評價'].fillna('未記載')
    return df

# ==========================================
# 3. 側邊欄：雙階段防呆 SOP 參數輸入
# ==========================================
try:
    models = pd.read_sql("SELECT DISTINCT 車系與車型 FROM auctions_time_series", sqlite3.connect("cars_time_series.db"))['車系與車型'].tolist()
except: models = []

st.sidebar.markdown("### 🛠️ 核心變數提取 (SOP)")
selected_model = st.sidebar.selectbox("車系與車型 (Model)", models, index=models.index('NX200') if 'NX200' in models else 0)
df_car = get_model_data(selected_model)

if not df_car.empty:
    selected_year = st.sidebar.selectbox("出廠年份 (Year)", sorted(df_car['出廠年份'].unique(), reverse=True))
    target_mileage = st.sidebar.number_input("里程數 (Mileage) km", value=75000, step=5000)
    vehicle_grade = st.sidebar.selectbox("鑑定評價 (Grade)", ["A / A+", "B / B+", "未記載"])
    
    st.sidebar.markdown("### 💰 交易條件")
    dealer_price = st.sidebar.number_input("終端零售開價 (TWD)", value=800000, step=10000)
    is_hybrid = st.sidebar.toggle("Hybrid 系統 (計算大電池 TCO)")

    # 基礎篩選 (同年份)
    df_yr = df_car[df_car['出廠年份'] == selected_year]
    
    # ==========================================
    # 4. 衍生數據運算 (量化金融模組)
    # ==========================================
    if not df_yr.empty:
        # A. 流動性運算
        trade_count = len(df_yr)
        liquidity_status = "極佳 (易脫手)" if trade_count > 30 else ("普通" if trade_count > 10 else "極差 (流動性陷阱)")
        
        # B. 降級懲罰金運算 (A級 vs B級 價差)
        grade_a_median = df_yr[df_yr['車輛評價'].str.contains('A', na=False)]['得標價'].median()
        grade_b_median = df_yr[df_yr['車輛評價'].str.contains('B', na=False)]['得標價'].median()
        penalty = 0
        if pd.notna(grade_a_median) and pd.notna(grade_b_median):
            penalty = grade_a_median - grade_b_median
            
        # C. 里程折現率 (線性迴歸)
        mileage_slope = 0
        if trade_count > 5:
            # 排除極端值後計算斜率
            q1 = df_yr['得標價'].quantile(0.1)
            q9 = df_yr['得標價'].quantile(0.9)
            valid_df = df_yr[(df_yr['得標價'] >= q1) & (df_yr['得標價'] <= q9)]
            if len(valid_df) > 5:
                slope, _ = np.polyfit(valid_df['里程數'], valid_df['得標價'], 1)
                mileage_slope = slope * 10000 # 每萬公里折價
        
        retail_floor = df_yr['得標價'].median() * 1.08
        
        # ==========================================
        # 5. 報告渲染
        # ==========================================
        st.markdown("---")
        
        # 模組一：市場宏觀與流動性
        st.subheader(f"📊 模組一：資產流動性與物理折現率 ({selected_year}年 {selected_model})")
        c1, c2, c3 = st.columns(3)
        c1.metric("樣本數據量 (17個月)", f"{trade_count} 台", liquidity_status, delta_color="off")
        
        if mileage_slope < 0:
            c2.metric("每萬公里殘值折損", f"{mileage_slope:,.0f} TWD", "線性衰變參數", delta_color="inverse")
        else:
            c2.metric("每萬公里殘值折損", "樣本過少無法精算", "需人工輔助判定", delta_color="off")
            
        if penalty > 0:
            c3.metric("B級瑕疵降級懲罰金", f"-{penalty:,.0f} TWD", "A級與B級中位數落差", delta_color="inverse")
        else:
            c3.metric("B級瑕疵降級懲罰金", "無顯著價差", "樣本分佈過於集中", delta_color="off")

        # 模組二：定價與評價風險
        st.subheader("⚠️ 模組二：定價釣魚與車況黑箱偵測")
        p1, p2 = st.columns(2)
        with p1:
            st.markdown(f"<div class='metric-box'><b>防禦基準線：</b> 合理零售門檻為 {retail_floor:,.0f} TWD</div>", unsafe_allow_html=True)
            if dealer_price < retail_floor:
                st.error("🚨 釣魚/重大事故警報：開價異常低於批發水位。期望值為負，請立即中止交易。")
            else:
                st.success(f"✅ 開價溢價約 {dealer_price - retail_floor:,.0f} TWD，屬正常商業套利區間。")
                
        with p2:
            st.markdown(f"<div class='metric-box'><b>當前輸入評價：</b> {vehicle_grade}</div>", unsafe_allow_html=True)
            if vehicle_grade == "未記載":
                st.error(f"☠️ 結構黑箱風險：未確認評價。根據大數據，若此車實為B級，您將承擔約 {penalty:,.0f} TWD 的未實現資產減損。")
            elif vehicle_grade == "B / B+":
                st.warning("⚠️ 瑕疵折現：此車帶有修復歷或瑕疵。請確認車商是否已將降級懲罰金反映於售價上。")
            else:
                st.success("✅ 結構健全：A級評價確保殘值穩固，免於降級懲罰。")

        # 模組三：TCO 與談判
        st.subheader("🛠️ 模組三：TCO 總體持有成本與談判籌碼")
        tco_base = 42000 
        battery_fund = 55000 if (is_hybrid and target_mileage > 100000) else 0
        total_tco = tco_base + battery_fund
        
        st.info(f"👉 **未來三年物理耗損準備金 (TCO)： {total_tco:,.0f} TWD**")
        if battery_fund > 0: st.warning(f"包含大電池與冷卻系統高頻失效準備金 {battery_fund:,.0f} TWD。")
        
        script = f"「老闆，這台 {selected_model} 大數據盤價約 {df_yr['得標價'].median()/10000:.1f} 萬。里程 {target_mileage/10000:.1f} 萬，每多一萬公里殘值會掉 {-mileage_slope/10000:.1f} 萬。加上未來三年我要準備 {total_tco/10000:.1f} 萬保養，如果能以 {retail_floor/10000:.1f} 萬現金成交，我們馬上處理。」"
        st.markdown(f"**高期望值談判腳本：**\n> {script}")

    else:
        st.warning("該條件組合在資料庫中無足夠樣本。")
