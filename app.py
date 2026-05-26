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
    .risk-item { padding: 10px; border-bottom: 1px solid #E2E8F0; color: #334155; }
    .risk-high { color: #DC2626; font-weight: bold; }
    </style>
    <div class='main-title'>Naval Motors | 深度資產量化報告 v1.2</div>
    <div class='sub-title'>專業版功能：價格合規防線 ｜ 三年 TCO 瀑布圖 ｜ 汽/油電雙軌維修黑洞預測</div>
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

# --- 新增：維修黑洞精算引擎 ---
def calculate_tco_details(is_hybrid, mileage):
    # 基礎保養 (三年)
    base_maint = 36000 if is_hybrid else 42000 # 油電車煞車皮耗損較低
    heavy_maint = 0
    hybrid_fund = 0
    items = ["全合成機油與濾心 (常規)", "冷氣/引擎濾網 (常規)", "輪胎一組 (常規)"]
    
    if not is_hybrid: # 汽油車邏輯
        items.append("煞車皮與碟盤 (常規耗損)")
        if mileage >= 80000:
            heavy_maint = 35000
            items.extend(["變速箱濾網與油底殼更換 <span class='risk-high'>(8萬公里高風險)</span>", 
                          "引擎腳橡膠老化老化 <span class='risk-high'>(震動風險)</span>", 
                          "水泵浦與冷卻液更新"])
    else: # 油電車邏輯
        if mileage >= 100000:
            hybrid_fund = 55000
            heavy_maint = 25000
            items.extend(["HV 鎳氫/鋰大電池模組 <span class='risk-high'>(10萬公里衰退警戒)</span>", 
                          "變頻器專用冷卻液更新", 
                          "ABS 煞車蓄壓器總泵 <span class='risk-high'>(極高價零件預警)</span>"])
            
    total_maint = base_maint + heavy_maint + hybrid_fund
    return total_maint, base_maint, heavy_maint, hybrid_fund, items

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
        target_mileage = st.number_input("車商標示里程 (km)", value=85000, step=5000)
        dealer_price = st.number_input("車商開價 (TWD)", value=800000, step=10000)
        vehicle_grade = st.selectbox("買家自帶鑑定評級", ["A / A+ (無事故)", "B / B+ (有瑕疵)", "未記載 (車行自保)"])
        is_hybrid = st.toggle("此車為 Hybrid 油電系統", value=True if "CT200H" in selected_model else False)

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
        
        # 調用維修黑洞引擎
        total_maint, base_maint, heavy_maint, battery_fund, maint_items = calculate_tco_details(is_hybrid, target_mileage)
        
        tax_3yr = 52320 # 假設 1.8~2.0L 稅金 (三年)
        total_3yr_expense = total_maint + tax_3yr
        residual_value = median_auction * 0.7 
        true_cost = dealer_price + total_3yr_expense - residual_value

        # 頂部戰略底牌
        st.markdown(f"""
        <div class='premium-box'>
            <h3 style='margin-top:0px; color:#F8FAFC;'>賽局底牌透視：車商潛在毛利與溢價</h3>
            <p>根據全台拍賣大數據，此車型同年份之批發底價中位數為 <b>{median_auction:,.0f} TWD</b>。</p>
            <p>推算目前開價中，包含了 <span class='margin-text'>{dealer_margin:,.0f} TWD</span> 的毛利與整備空間。</p>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs([
            "🏷️ 價格合規防禦", 
            "💸 三年現金流瀑布", 
            "🔧 維修黑洞拆解 (核心)"
        ])

        # Tab 1: 價格合規 (略，維持原樣)
        with tab1:
            st.markdown("### 🎯 車商開價 vs 市場真實合理售價")
            bar_colors = ['#94A3B8', '#1E3A8A', '#DC2626' if dealer_price < retail_floor else '#10B981']
            fig_price_comp = go.Figure(data=[
                go.Bar(x=['行內批發盤價中位數', '系統合理零售價 (門檻)', '當前車商開價標的'],
                       y=[median_auction, retail_floor, dealer_price],
                       text=[f"${median_auction:,.0f}", f"${retail_floor:,.0f}", f"${dealer_price:,.0f}"],
                       textposition='auto', marker_color=bar_colors, width=0.4)
            ])
            fig_price_comp.update_layout(yaxis=dict(title="金額 (TWD)", gridcolor="#E2E8F0"), plot_bgcolor='rgba(0,0,0,0)', height=550)
            st.plotly_chart(fig_price_comp, use_container_width=True)
            
            if dealer_price < retail_floor: st.error("🚨 **高風險釣魚警示**：開價異常低於批發水位。期望值極度負面，強烈建議終止看車。")
            else: st.success("✅ **價格合規**：屬於正常市場營運區間。")

        # Tab 2: 瀑布圖 (略，維持原樣)
        with tab2:
            st.markdown("### 🔮 持有三年之總體現金流預測 (The Real Cost)")
            fig_waterfall = go.Figure(go.Waterfall(
                name="現金流", orientation="v", measure=["relative", "relative", "relative", "total"],
                x=["1. 買車當下支出 (開價)", "2. 三年預計花費 (稅金/耗材)", "3. 三年後賣出殘值 (資金回籠)", "4. 實際持有總成本 (淨流出)"],
                textposition="outside",
                text=[f"${dealer_price/10000:.1f}萬", f"+${total_3yr_expense/10000:.1f}萬", f"-${residual_value/10000:.1f}萬", f"${true_cost/10000:.1f}萬"],
                y=[dealer_price, total_3yr_expense, -residual_value, true_cost],
                connector={"line":{"color":"#94A3B8", "width":2, "dash":"dot"}},
                decreasing={"marker":{"color":"#10B981"}}, increasing={"marker":{"color":"#EF4444"}}, totals={"marker":{"color":"#0F172A"}}
            ))
            fig_waterfall.update_layout(yaxis=dict(gridcolor="#E2E8F0"), plot_bgcolor='rgba(0,0,0,0)', height=550)
            st.plotly_chart(fig_waterfall, use_container_width=True)

        # ==========================================
        # Tab 3：全新的「維修黑洞拆解」模組
        # ==========================================
        with tab3:
            car_type_str = "Hybrid 油電系統" if is_hybrid else "純內燃機 (汽油) 系統"
            st.markdown(f"### ⚙️ {car_type_str} 專屬物理衰變預測")
            st.markdown(f"目標標的里程：**{target_mileage:,} km** ｜ 系統判定防禦等級：**{'進入高頻故障區間' if (is_hybrid and target_mileage >= 100000) or (not is_hybrid and target_mileage >= 80000) else '常規耗損期'}**")
            
            # 財務提列結構
            c1, c2, c3 = st.columns(3)
            c1.metric("基礎耗材提列", f"${base_maint:,.0f}")
            c2.metric("大保養/老化機件提列", f"${heavy_maint:,.0f}", delta="8萬公里觸發" if (not is_hybrid and heavy_maint>0) else None, delta_color="inverse")
            c3.metric("油電大電池提列", f"${battery_fund:,.0f}", delta="10萬公里觸發" if battery_fund>0 else None, delta_color="inverse")
            
            st.markdown("#### 📋 系統強制提列維修清單 (未來三年)")
            for item in maint_items:
                st.markdown(f"<div class='risk-item'>✔️ {item}</div>", unsafe_allow_html=True)
                
            st.markdown("---")
            if battery_fund > 0 or heavy_maint > 0:
                st.warning("⚠️ **工程風險警示**：此車已跨越該動力系統的核心機件衰退期。建議在簽約前，要求車商頂高底盤檢查漏油，並插電腦 (OBD2) 檢測 Hybrid 電池內阻值與 ABS 總泵壓力。")
            else:
                st.success("✅ **工程健康評估**：目前里程尚未觸發系統強制提列的大型維修黑洞，維持常規保養即可。")

        # 底部實戰腳本輸出
        st.markdown("---")
        st.subheader("💡 談判賽局：高期望值殺價腳本")
        script = f"「老闆，我調過大數據，這年份底價約 {median_auction/10000:.1f} 萬。雖然我知道這台車有 {dealer_margin/10000:.1f} 萬的毛利空間，但因為這台車是{car_type_str}且里程已經 {target_mileage/10000:.1f} 萬，接下來三年我必須立刻提列 {total_maint/10000:.1f} 萬的維修準備金（包含系統警示的待修耗材）。如果能以 {retail_floor/10000:.1f} 萬現金成交，我們今天就簽約。」"
        st.markdown(f"> {script}")

    else:
        st.warning("該條件組合在資料庫中無足夠樣本。")
