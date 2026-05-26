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
    .metric-card { background-color: #F8FAFC; padding: 20px; border-radius: 8px; border-left: 5px solid #3B82F6; margin-bottom: 15px;}
    .metric-title { font-size: 16px; color: #64748B; font-weight: 600; margin-bottom: 5px;}
    .metric-value { font-size: 28px; color: #0F172A; font-weight: 900;}
    </style>
    <div class='main-title'>Naval Motors | 深度資產量化報告 v1.0</div>
    <div class='sub-title'>專業版功能：價格合規防線 ｜ 三年 TCO 與殘值終局預測 ｜ 大數據折舊曲線</div>
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
    st.markdown("### 🔍 標的物條件設定")
    selected_model = st.selectbox("車系與車型", models, index=models.index('NX200') if 'NX200' in models else 0)
    df_car = get_model_data(selected_model)
    
    if not df_car.empty:
        selected_year = st.selectbox("出廠年份", sorted(df_car['出廠年份'].unique(), reverse=True))
        selected_color = st.selectbox("車輛顏色", sorted(df_car['車色'].unique()))
        
        st.markdown("### 💰 交易與耗損參數")
        target_mileage = st.number_input("車商標示里程 (km)", value=75000, step=5000)
        dealer_price = st.number_input("車商開價 (TWD)", value=800000, step=10000)
        vehicle_grade = st.selectbox("買家自帶鑑定評級", ["A / A+ (無事故)", "B / B+ (有瑕疵)", "未記載 (車行自保)"])
        is_hybrid = st.toggle("此車為 Hybrid 油電系統")

# ==========================================
# 3. 核心運算與大型報告渲染
# ==========================================
if not df_car.empty:
    df_yr = df_car[df_car['出廠年份'] == selected_year]
    
    if not df_yr.empty:
        # --- 基礎數據精算 ---
        median_auction = df_yr['得標價'].median()
        retail_floor = median_auction * 1.08
        dealer_margin = dealer_price - median_auction 
        
        # 里程折現率 (排除極端值)
        q1, q9 = df_yr['得標價'].quantile(0.1), df_yr['得標價'].quantile(0.9)
        valid_df = df_yr[(df_yr['得標價'] >= q1) & (df_yr['得標價'] <= q9)]
        mileage_slope = np.polyfit(valid_df['里程數'], valid_df['得標價'], 1)[0] * 10000 if len(valid_df) > 5 else 0
        
        # --- TCO 與殘值精算 ---
        tco_maintenance = 42000 # 三年常規保養 (含機油、輪胎等)
        battery_fund = 55000 if (is_hybrid and target_mileage > 100000) else 0 # 高風險提列
        tax_3yr = 52320 # 假設 1.8~2.0L 稅金 (三年)
        total_3yr_expense = tco_maintenance + battery_fund + tax_3yr
        
        # 三年後殘值預估 (以當前盤價為基底，預估再折舊 30% 加上里程自然耗損)
        expected_future_mileage = target_mileage + 45000 # 假設三年開 4.5 萬公里
        residual_value = median_auction * 0.7 # 基準七折
        
        # 真實總成本 = 買車錢 + 三年養車錢 - 三年後賣掉的錢
        true_cost = dealer_price + total_3yr_expense - residual_value

        # 頂部戰略底牌
        st.markdown(f"""
        <div class='premium-box'>
            <h3 style='margin-top:0px; color:#F8FAFC;'>賽局底牌透視：車商潛在毛利與溢價</h3>
            <p>根據全台拍賣大數據，此車型同年份之批發底價中位數為 <b>{median_auction:,.0f} TWD</b>。</p>
            <p>推算目前開價中，包含了 <span class='margin-text'>{dealer_margin:,.0f} TWD</span> 的毛利與整備空間。</p>
        </div>
        """, unsafe_allow_html=True)

        # 簡化為三大核心分頁
        tab1, tab2, tab3 = st.tabs([
            "🏷️ 價格合規防禦 (首頁)", 
            "💸 三年 TCO 與殘值預測 (核心)", 
            "📈 里程折舊實測"
        ])

        # ==========================================
        # Tab 1：價格對比防禦
        # ==========================================
        with tab1:
            st.markdown("### 🎯 車商開價 vs 市場真實合理售價")
            bar_colors = ['#94A3B8', '#1E3A8A', '#DC2626' if dealer_price < retail_floor else '#10B981']
            
            fig_price_comp = go.Figure(data=[
                go.Bar(
                    x=['行內批發盤價中位數', '系統合理零售價 (門檻)', '當前車商開價標的'],
                    y=[median_auction, retail_floor, dealer_price],
                    text=[f"${median_auction:,.0f}", f"${retail_floor:,.0f}", f"${dealer_price:,.0f}"],
                    textposition='auto',
                    marker_color=bar_colors,
                    width=0.4
                )
            ])
            fig_price_comp.update_layout(
                yaxis=dict(title="金額 (TWD)", gridcolor="#E2E8F0"),
                xaxis=dict(tickfont=dict(size=15, family="Microsoft JhengHei", color="#0F172A")),
                plot_bgcolor='rgba(0,0,0,0)', height=600, margin=dict(t=50)
            )
            st.plotly_chart(fig_price_comp, use_container_width=True)
            
            if dealer_price < retail_floor:
                st.error("🚨 **高風險釣魚警示**：開價異常低於批發水位。期望值極度負面，強烈建議終止看車。")
            else:
                st.success("✅ **價格合規**：開價高於底價門檻，屬於正常市場營運區間，可進入下一步 TCO 財務精算。")

        # ==========================================
        # Tab 2：三年 TCO 與殘值預測 (全新簡單版瀑布圖)
        # ==========================================
        with tab2:
            st.markdown("### 🔮 持有三年之總體現金流預測 (The Real Cost)")
            
            # 上方顯示三個簡單的數字總結
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div class='metric-card'><div class='metric-title'>預計三年維修保養與稅金</div><div class='metric-value'>${total_3yr_expense:,.0f}</div></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-card' style='border-color:#10B981;'><div class='metric-title'>預計三年後可賣出殘值 (資金回籠)</div><div class='metric-value' style='color:#10B981;'>${residual_value:,.0f}</div></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='metric-card' style='border-color:#EF4444;'><div class='metric-title'>三年真實持有淨成本 (總折舊+花費)</div><div class='metric-value' style='color:#EF4444;'>${true_cost:,.0f}</div></div>", unsafe_allow_html=True)
            
            # 極度簡化的瀑布圖
            fig_waterfall = go.Figure(go.Waterfall(
                name="現金流", orientation="v",
                measure=["relative", "relative", "relative", "total"],
                x=["1. 買車當下支出 (開價)", "2. 三年預計花費 (稅金/保養/耗材)", "3. 三年後賣出殘值 (資金收回)", "4. 實際持有總成本 (淨流出)"],
                textposition="outside",
                text=[f"${dealer_price/10000:.1f}萬", f"+${total_3yr_expense/10000:.1f}萬", f"-${residual_value/10000:.1f}萬", f"${true_cost/10000:.1f}萬"],
                y=[dealer_price, total_3yr_expense, -residual_value, true_cost],
                connector={"line":{"color":"#94A3B8", "width":2, "dash":"dot"}},
                decreasing={"marker":{"color":"#10B981"}}, increasing={"marker":{"color":"#EF4444"}}, totals={"marker":{"color":"#0F172A"}}
            ))
            fig_waterfall.update_layout(
                yaxis=dict(gridcolor="#E2E8F0"),
                xaxis=dict(tickfont=dict(size=14, fontweight='bold')),
                plot_bgcolor='rgba(0,0,0,0)', height=550, margin=dict(t=50)
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)
            
            if battery_fund > 0:
                st.warning(f"⚠️ **高風險耗材提醒**：上述「三年預計花費」已自動為您提列 **${battery_fund:,.0f} TWD** 的 Hybrid 大電池與散熱系統預防性更換準備金 (因里程突破 10 萬公里觸發)。")

        # ==========================================
        # Tab 3：里程折舊曲線
        # ==========================================
        with tab3:
            st.markdown("### 📉 物理衰變實測 (大數據迴歸)")
            df_yr['價格(萬)'] = df_yr['得標價'] / 10000
            color_map = {'白': '#F8FAFC', '黑': '#0F172A', '銀': '#94A3B8', '灰': '#475569', '淺棕': '#D6D3D1', '紅': '#EF4444', '藍': '#3B82F6', '其他': '#10B981'}
            fig_scatter = px.scatter(
                df_yr, x="里程數", y="價格(萬)", color="車色", color_discrete_map=color_map, 
                title=f"此年份每多跑一萬公里，市場盤價實質折損 {-mileage_slope:,.0f} TWD"
            )
            fig_scatter.update_layout(
                plot_bgcolor='#E2E8F0', paper_bgcolor='rgba(0,0,0,0)', 
                yaxis=dict(title="價格 (萬元)"), height=650
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # 底部實戰腳本輸出
        st.markdown("---")
        st.subheader("💡 談判賽局：高期望值殺價腳本")
        script = f"「老闆，我調過全台大數據盤價，這年份底價中位數在 {median_auction/10000:.1f} 萬。雖然我知道這台車有 {dealer_margin/10000:.1f} 萬的毛利空間，但因為這台車後續我得立刻提列 {total_3yr_expense/10000:.1f} 萬作為三年耗材與稅金預算。如果能以 {retail_floor/10000:.1f} 萬現金成交，我們今天就簽約，你們也不用承擔融資利息成本。」"
        st.markdown(f"> {script}")

    else:
        st.warning("該條件組合在資料庫中無足夠樣本。")
