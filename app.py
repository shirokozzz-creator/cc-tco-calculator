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
    .premium-box { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); color: white; padding: 25px; border-radius: 10px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .margin-text { font-size: 26px; font-weight: bold; color: #10B981; }
    </style>
    <div class='main-title'>Naval Motors | 深度資產量化報告 v0.9</div>
    <div class='sub-title'>專業版功能：全幅大型圖表看板 ｜ 價格合規第一防線 ｜ 決策智庫</div>
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
# 3. 核心運算與大型報告渲染
# ==========================================
if not df_car.empty:
    df_yr = df_car[df_car['出廠年份'] == selected_year]
    
    if not df_yr.empty:
        # --- 數據精算 ---
        median_auction = df_yr['得標價'].median()
        retail_floor = median_auction * 1.08
        dealer_margin = dealer_price - median_auction 
        
        # 里程折現率
        q1, q9 = df_yr['得標價'].quantile(0.1), df_yr['得標價'].quantile(0.9)
        valid_df = df_yr[(df_yr['得標價'] >= q1) & (df_yr['得標價'] <= q9)]
        mileage_slope = np.polyfit(valid_df['里程數'], valid_df['得標價'], 1)[0] * 10000 if len(valid_df) > 5 else 0
        
        # TCO 計算
        tco_base = 42000
        battery_fund = 55000 if (is_hybrid and target_mileage > 100000) else 0
        tax_3yr = 52320 
        residual_value = median_auction * 0.7 
        true_cost = dealer_price + tco_base + battery_fund + tax_3yr - residual_value

        # --- 評分系統 ---
        score_price = max(0, min(100, 100 - ((dealer_price - retail_floor) / retail_floor) * 200)) if dealer_price >= retail_floor else 10
        score_liquidity = min(100, len(df_yr) * 5)
        score_condition = 95 if "A" in vehicle_grade else (50 if "B" in vehicle_grade else 20)
        score_mileage = max(0, min(100, 100 - (target_mileage - 60000)/1500))
        score_tco = max(0, min(100, 100 - (battery_fund/1000)))
        
        # 頂部戰略底牌
        st.markdown(f"""
        <div class='premium-box'>
            <h3 style='margin-top:0px; color:#F8FAFC;'>賽局底牌透視：車商潛在毛利分析</h3>
            <p>根據 17 個月全台成交大數據，此車型同年份之行內批發盤價中位數為 <b>{median_auction:,.0f} TWD</b>。</p>
            <p>推算該車商開價中，包含了 <span class='margin-text'>{dealer_margin:,.0f} TWD</span> 的毛利與整備空間。</p>
        </div>
        """, unsafe_allow_html=True)

        # 四大全新分頁，將價格對比前置化，並全面擴大尺寸
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏷️ 價格合規防禦 (客戶首選)", 
            "📊 六維防禦雷達", 
            "💸 TCO 瀑布模型", 
            "📈 里程折舊曲線"
        ])

        # ==========================================
        # 新增 Tab 1：價格對比防禦 (極致放大版)
        # ==========================================
        with tab1:
            st.markdown("### 🎯 車商開價與市場真實合理售價對比看板")
            
            # 定義柱狀圖顏色：若低於樓地板價則開價亮紅燈(釣魚警示)
            bar_colors = ['#94A3B8', '#1E3A8A', '#DC2626' if dealer_price < retail_floor else '#10B981']
            
            fig_price_comp = go.Figure(data=[
                go.Bar(
                    x=['行內批發盤價中位數', '系統精算合理零售價 (門檻)', '當前車商開價標的'],
                    y=[median_auction, retail_floor, dealer_price],
                    text=[f"${median_auction:,.0f}", f"${retail_floor:,.0f}", f"${dealer_price:,.0f}"],
                    textposition='auto',
                    marker_color=bar_colors,
                    width=0.4
                )
            ])
            
            fig_price_comp.update_layout(
                title="價格定位橫向對比 (TWD)",
                yaxis=dict(title="金額 (元)", gridcolor="#E2E8F0"),
                xaxis=dict(tickfont=dict(size=14, family="Microsoft JhengHei")),
                plot_bgcolor='rgba(0,0,0,0)',
                height=650, # 深度放大
                margin=dict(l=50, r=50, t=80, b=50)
            )
            st.plotly_chart(fig_price_comp, use_container_width=True)
            
            # 輔助判定文字
            price_gap = dealer_price - retail_floor
            if dealer_price < retail_floor:
                st.error(f"🚨 **警告：當前車商開價低於合理零售門檻 ${abs(price_gap):,.0f} 元**。市場上不存在不賺錢的車商，此標的極高機率為低價釣魚假廣告、車體結構有重大重大修復歷、或多元計程車調錶改回，期望值極低，系統建議終止看車。")
            else:
                st.success(f"✅ **價格合規**：車商開價高於零售門檻 ${price_gap:,.0f} 元，屬於正常營運利潤套利區間。可點擊其餘分頁進行進一步物理耗損評估。")

        # ==========================================
        # Tab 2：六維防禦雷達 (放大版)
        # ==========================================
        with tab2:
            fig_radar = go.Figure(data=go.Scatterpolar(
              r=[score_price, score_liquidity, score_condition, score_mileage, score_tco, score_price],
              theta=['價格合理度', '市場流點性', '鑑定健康度', '里程低衰變', 'TCO 維修負荷', '價格合理度'],
              fill='toself', line_color='#1E3A8A', fillcolor='rgba(30, 58, 138, 0.4)'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=12))),
                title="Naval 標的物綜合防禦雷達量表", 
                height=650 # 深度放大
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # ==========================================
        # Tab 3：TCO 瀑布模型 (放大版)
        # ==========================================
        with tab3:
            fig_waterfall = go.Figure(go.Waterfall(
                name="TCO", orientation="v",
                measure=["relative", "relative", "relative", "relative", "relative", "total"],
                x=["車商開價", "三年常規保養", "大電池預備金", "三年稅金", "三年後預估殘值", "最終淨流出 (真 TCO)"],
                textposition="outside",
                text=[f"{dealer_price/10000:.1f}萬", f"{tco_base/10000:.1f}萬", f"{battery_fund/10000:.1f}萬", f"{tax_3yr/10000:.1f}萬", f"-{residual_value/10000:.1f}萬", f"{true_cost/10000:.1f}萬"],
                y=[dealer_price, tco_base, battery_fund, tax_3yr, -residual_value, true_cost],
                connector={"line":{"color":"#475569", "width":2}},
                decreasing={"marker":{"color":"#10B981"}}, increasing={"marker":{"color":"#EF4444"}}, totals={"marker":{"color":"#0F172A"}}
            ))
            fig_waterfall.update_layout(
                title="資產持有三年期間現金流淨現值 (NPV) 衰變矩陣", 
                yaxis=dict(gridcolor="#E2E8F0"),
                height=650 # 深度放大
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)

        # ==========================================
        # Tab 4：里程折舊曲線 (放大版)
        # ==========================================
        with tab4:
            df_yr['價格(萬)'] = df_yr['得標價'] / 10000
            color_map = {'白': '#F8FAFC', '黑': '#0F172A', '銀': '#94A3B8', '灰': '#475569', '淺棕': '#D6D3D1', '紅': '#EF4444', '藍': '#3B82F6', '其他': '#10B981'}
            fig_scatter = px.scatter(
                df_yr, x="里程數", y="價格(萬)", color="車色", color_discrete_map=color_map, 
                title=f"物理折現率實測：此年份每多跑一萬公里，市場盤價實質折損 {-mileage_slope:,.0f} TWD"
            )
            fig_scatter.update_layout(
                plot_bgcolor='#E2E8F0', 
                paper_bgcolor='rgba(0,0,0,0)', 
                yaxis=dict(title="價格 (萬元)"),
                height=650 # 深度放大
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # 底部實戰腳本輸出
        st.markdown("---")
        st.subheader("💡 談判賽局：高期望值殺價腳本")
        tco_total = tco_base + battery_fund
        script = f"「老闆，我調過全台大數據盤價，這年份底價中位數在 {median_auction/10000:.1f} 萬。目前你開的價錢包含合理管銷我懂。但因為這台車里程已經 {target_mileage/10000:.1f} 萬公里，每跑一萬公里在盤面上就少 {-mileage_slope/10000:.1f} 萬的價值，且後續我得立刻提列 {tco_total/10000:.1f} 萬作為三年耗材與油電大電池的更換預算。如果能以 {retail_floor/10000:.1f} 萬現金成交，我們今天就簽約，你們也不用承擔融資利息成本。」"
        st.markdown(f"> {script}")

    else:
        st.warning("該條件組合在資料庫中無足夠樣本。")
