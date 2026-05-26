import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. UI 視覺與 Premium 品牌設定
# ==========================================
st.set_page_config(page_title="Naval Motors 企業級資產防禦系統", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
    .main-title { font-size: 38px; font-weight: 900; color: #0F172A; letter-spacing: -1px; }
    .sub-title { font-size: 16px; color: #475569; margin-bottom: 25px; border-bottom: 2px solid #E2E8F0; padding-bottom: 10px;}
    .premium-box { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .margin-text { font-size: 24px; font-weight: bold; color: #10B981; }
    </style>
    <div class='main-title'>Naval Motors | 深度資產量化報告 v0.8</div>
    <div class='sub-title'>專業版功能：六維雷達分析 ｜ TCO 瀑布模型 ｜ 賽局底牌透視</div>
    """, unsafe_allow_html=True)

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
# 2. 側邊欄：實體特徵輸入
# ==========================================
try:
    models = pd.read_sql("SELECT DISTINCT 車系與車型 FROM auctions_time_series", sqlite3.connect("cars_time_series.db"))['車系與車型'].tolist()
except: models = []

with st.sidebar:
    st.markdown("### 🔍 設定目標標的物")
    selected_model = st.selectbox("車系與車型", models, index=models.index('NX200') if 'NX200' in models else 0)
    df_car = get_model_data(selected_model)
    
    if not df_car.empty:
        selected_year = st.selectbox("出廠年份", sorted(df_car['出廠年份'].unique(), reverse=True))
        selected_color = st.selectbox("車輛顏色", sorted(df_car['車色'].unique()))
        
        st.markdown("### 💰 交易條件與鑑定")
        target_mileage = st.number_input("車商標示里程 (km)", value=75000, step=5000)
        dealer_price = st.number_input("車商開價 (TWD)", value=800000, step=10000)
        vehicle_grade = st.selectbox("買家自帶鑑定評級", ["A / A+ (無事故)", "B / B+ (有瑕疵)", "未記載 (車行自保)"])
        is_hybrid = st.toggle("Hybrid 油電系統")

# ==========================================
# 3. 核心運算與報告渲染
# ==========================================
if not df_car.empty:
    df_yr = df_car[df_car['出廠年份'] == selected_year]
    
    if not df_yr.empty:
        # --- 數據精算 ---
        median_auction = df_yr['得標價'].median()
        retail_floor = median_auction * 1.08
        dealer_margin = dealer_price - median_auction # 推算毛利
        
        # 里程折現率
        q1, q9 = df_yr['得標價'].quantile(0.1), df_yr['得標價'].quantile(0.9)
        valid_df = df_yr[(df_yr['得標價'] >= q1) & (df_yr['得標價'] <= q9)]
        mileage_slope = np.polyfit(valid_df['里程數'], valid_df['得標價'], 1)[0] * 10000 if len(valid_df) > 5 else 0
        
        # TCO 計算
        tco_base = 42000
        battery_fund = 55000 if (is_hybrid and target_mileage > 100000) else 0
        tax_3yr = 52320 # 假設 1.8-2.0 級距三年稅金
        residual_value = median_auction * 0.7 # 粗估三年後殘值 (七折)
        true_cost = dealer_price + tco_base + battery_fund + tax_3yr - residual_value

        # --- 評分系統 (0-100) ---
        score_price = max(0, min(100, 100 - ((dealer_price - retail_floor) / retail_floor) * 200)) if dealer_price >= retail_floor else 10 # 釣魚價給極低分
        score_liquidity = min(100, len(df_yr) * 5)
        score_condition = 95 if "A" in vehicle_grade else (50 if "B" in vehicle_grade else 20)
        score_mileage = max(0, min(100, 100 - (target_mileage - 60000)/1500))
        score_tco = max(0, min(100, 100 - (battery_fund/1000)))
        
        # ==========================================
        # 報告板塊 A：高管視角 (Executive Summary)
        # ==========================================
        st.markdown(f"""
        <div class='premium-box'>
            <h3 style='margin-top:0px;'>賽局底牌透視：車商潛在毛利分析</h3>
            <p>根據 17 個月大數據，此車型同年份之行內批發盤價中位數為 <b>{median_auction:,.0f} TWD</b>。</p>
            <p>推算該車商開價中，包含了 <span class='margin-text'>{dealer_margin:,.0f} TWD</span> 的毛利空間 (含整備與利潤)。</p>
            <p style='font-size: 14px; color: #94A3B8;'>策略建議：以此水位向下遞減 {dealer_margin * 0.4:,.0f} 至 {dealer_margin * 0.7:,.0f} 進行首輪議價，確保期望值最大化。</p>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📊 六維防禦雷達", "💸 TCO 瀑布模型", "📈 里程折舊曲線"])

        # ==========================================
        # 報告板塊 B：雷達圖 (Radar Chart)
        # ==========================================
        with tab1:
            fig_radar = go.Figure(data=go.Scatterpolar(
              r=[score_price, score_liquidity, score_condition, score_mileage, score_tco, score_price],
              theta=['價格合理度', '市場流動性', '鑑定健康度', '里程低衰變', 'TCO 維修負荷', '價格合理度'],
              fill='toself', line_color='#3B82F6', fillcolor='rgba(59, 130, 246, 0.4)'
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Naval 標的物綜合防禦評級", height=450)
            st.plotly_chart(fig_radar, use_container_width=True)

        # ==========================================
        # 報告板塊 C：TCO 瀑布圖 (Waterfall Chart)
        # ==========================================
        with tab2:
            fig_waterfall = go.Figure(go.Waterfall(
                name="TCO", orientation="v",
                measure=["relative", "relative", "relative", "relative", "relative", "total"],
                x=["車商開價", "三年常規保養", "大電池預備金", "三年稅金", "三年後預估殘值", "最終淨流出 (真 TCO)"],
                textposition="outside",
                text=[f"{dealer_price/10000:.1f}萬", f"{tco_base/10000:.1f}萬", f"{battery_fund/10000:.1f}萬", f"{tax_3yr/10000:.1f}萬", f"-{residual_value/10000:.1f}萬", f"{true_cost/10000:.1f}萬"],
                y=[dealer_price, tco_base, battery_fund, tax_3yr, -residual_value, true_cost],
                connector={"line":{"color":"rgb(63, 63, 63)"}},
                decreasing={"marker":{"color":"#10B981"}}, increasing={"marker":{"color":"#EF4444"}}, totals={"marker":{"color":"#1E3A8A"}}
            ))
            fig_waterfall.update_layout(title="未來三年現金流淨現值 (NPV) 推演", height=450)
            st.plotly_chart(fig_waterfall, use_container_width=True)

        # ==========================================
        # 報告板塊 D：散佈圖與折現率
        # ==========================================
        with tab3:
            df_yr['價格(萬)'] = df_yr['得標價'] / 10000
            color_map = {'白': '#F8FAFC', '黑': '#0F172A', '銀': '#94A3B8', '灰': '#475569', '淺棕': '#D6D3D1', '紅': '#EF4444', '藍': '#3B82F6', '其他': '#10B981'}
            fig_scatter = px.scatter(df_yr, x="里程數", y="價格(萬)", color="車色", color_discrete_map=color_map, 
                                     title=f"物理折現率精算：每萬公里殘值減損 {-mileage_slope:,.0f} TWD")
            fig_scatter.update_layout(plot_bgcolor='#E2E8F0', paper_bgcolor='rgba(0,0,0,0)', height=450)
            st.plotly_chart(fig_scatter, use_container_width=True)

    else:
        st.warning("資料庫樣本不足，無法生成高級圖表。")
