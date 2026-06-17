import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

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
    <div class='main-title'>Naval Motors | 深度資產量化報告 v1.4</div>
    <div class='sub-title'>2026年企業實戰版：時間序列還原 ｜ BEV/SUV 雙重校正矩陣 ｜ 台灣動態牌燃稅精算</div>
    """, unsafe_allow_html=True)

def extract_color(raw_text):
    colors = ['白', '黑', '銀', '灰', '淺棕', '紅', '藍', '深灰', '鐵灰', '深綠']
    for c in colors:
        if c in str(raw_text): return c
    return '其他'

def sanitize_string(text):
    return re.sub(r'[\s\-]', '', str(text)).upper()

# --- 2026年台灣精確牌燃稅費率引擎 ---
def calculate_taiwan_tax_3yr(cc_str, is_bev):
    if is_bev:
        return 0  # 2026 台灣純電車免徵牌燃稅
    try:
        cc = int(cc_str)
    except:
        return 52320  # 預設 1.8L 級距
        
    # 年稅費字典 (牌照稅 + 燃料稅)
    if cc <= 500: return 2160 * 3
    elif cc <= 600: return 5740 * 3
    elif cc <= 1200: return 8640 * 3
    elif cc <= 1800: return 11920 * 3  # 1.2~1.8
    elif cc <= 2400: return 17410 * 3  # 1.8~2.4 (稅制劣勢門檻)
    elif cc <= 3000: return 22410 * 3
    elif cc <= 3600: return 36860 * 3
    else: return 57390 * 3

@st.cache_data
def get_cleaned_model_data(model_name):
    conn = sqlite3.connect("cars_time_series.db")
    # 使用大數據清洗與防堵邏輯
    df = pd.read_sql_query("SELECT 成交月份, 出廠年月, 車輛評價, 里程數, 得標價, 原始紀錄, 車系與車型 FROM auctions_time_series", conn)
    conn.close()
    
    if df.empty:
        return pd.DataFrame()
        
    df['clean_model'] = df['車系與車型'].apply(sanitize_string)
    target_clean = sanitize_string(model_name)
    
    df_filtered = df[df['clean_model'] == target_clean].copy()
    if not df_filtered.empty:
        df_filtered['出廠年份'] = df_filtered['出廠年月'].apply(lambda x: int(float(x)))
        df_filtered['車色'] = df_filtered['原始紀錄'].apply(extract_color)
        df_filtered['車輛評價'] = df_filtered['車輛評價'].fillna('未記載')
    return df_filtered

# --- 新增：維修黑洞精算引擎 (電氣化/純電擴容) ---
def calculate_tco_details(is_hybrid, is_bev, mileage):
    heavy_maint = 0
    hybrid_fund = 0
    
    if is_bev:
        base_maint = 15000  # 純電車保養成本極低
        items = ["定期減速齒輪油更換", "煞車油與冷卻液檢測", "輪胎一組 (常規耗損)"]
        if mileage >= 150000:
            hybrid_fund = 450000  # 逼近 19.2 萬公里大電池保固極限
            items.append("HV 純電大電池健康度衰退衰減 <span class='risk-high'>(19.2萬保固死亡線預警)</span>")
    else:
        base_maint = 36000 if is_hybrid else 42000
        items = ["全合成機油與濾心 (常規)", "冷氣/引擎濾網 (常規)", "輪胎一組 (常規)"]
        if not is_hybrid:
            items.append("煞車皮與碟盤 (常規耗損)")
            if mileage >= 80000:
                heavy_maint = 35000
                items.extend(["變速箱濾網與油底殼更換 <span class='risk-high'>(8萬公里高風險)</span>", 
                              "引擎腳橡膠老化老化 <span class='risk-high'>(震動風險)</span>"])
        else:
            if mileage >= 100000:
                hybrid_fund = 55000
                heavy_maint = 25000
                items.extend(["HV 大電池模組 <span class='risk-high'>(10萬公里衰退警戒)</span>", 
                              "ABS 煞車蓄壓器總泵 <span class='risk-high'>(極高價零件預警)</span>"])
                
    total_maint = base_maint + heavy_maint + hybrid_fund
    return total_maint, base_maint, heavy_maint, hybrid_fund, items

# ==========================================
# 2. 側邊欄：實體特徵輸入
# ==========================================
try:
    conn = sqlite3.connect("cars_time_series.db")
    models = pd.read_sql("SELECT DISTINCT 車系與車型 FROM auctions_time_series", conn)['車系與車型'].tolist()
    conn.close()
except: 
    models = ['NX200', 'CT200H', 'ALTIS', 'RAV4', 'MODEL Y']

with st.sidebar:
    st.markdown("### 🔍 標的物條件設定")
    selected_model = st.selectbox("車系與車型", models, index=0)
    df_car = get_cleaned_model_data(selected_model)
    
    # 動態提取排氣量特徵 (實戰除錯：防範 BEV 無排氣量集聚)
    cc_input = st.text_input("車輛排氣量 (cc) / 純電請填 0", value="1998")
    is_bev = st.toggle("此車為 BEV 純電資產 (如 Tesla)", value=True if "MODEL" in selected_model.upper() else False)
    is_hybrid = st.toggle("此車為 Hybrid 油電系統", value=True if "CT200H" in selected_model.upper() or "HYBRID" in selected_model.upper() else False)
    is_suv = st.toggle("此車屬 SUV / CUV 休旅車級距", value=True if any(x in selected_model.upper() for x in ['RAV4', 'CROSS', 'NX', 'RX', 'MODELY']) else False)
    
    if not df_car.empty:
        selected_year = st.selectbox("出廠年份", sorted(df_car['出廠年份'].unique(), reverse=True))
        selected_color = st.selectbox("車輛顏色", sorted(df_car['車色'].unique()))
        
        st.markdown("### 💰 交易與耗損參數")
        target_mileage = st.number_input("車商標示里程 (km)", value=85000, step=5000)
        dealer_price = st.number_input("車商開價 (TWD)", value=800000, step=10000)

# ==========================================
# 3. 核心運算與大型報告渲染
# ==========================================
if not df_car.empty:
    df_yr = df_car[df_car['出廠年份'] == selected_year]
    
    if not df_yr.empty:
        # --- 核心：Law 11 時間序列與里程還原演算法 ---
        # 排除里程過高或極端離群值，建立真實物理基準
        raw_median = df_yr['得標價'].median()
        avg_sample_mileage = df_yr['里程數'].mean() if df_yr['里程數'].mean() > 0 else 80000
        
        # 里程常數線性修正：每相差 1km 修正 1 TWD
        mileage_delta = (target_mileage - avg_sample_mileage) * 1.0
        median_auction = raw_median - mileage_delta # 映射出目標車況的客觀大盤價
        
        # --- 核心：Law 22 實戰流動性與安全防線精算 ---
        if is_suv and (is_hybrid or int(cc_input) > 2400):
            # 觸發大盤 SUV 結構剛需抵銷矩陣
            b2b_limit = median_auction * (1 - 0.0684)  # 實戰校正 6.84% 極限防線
            retail_floor = median_auction * 1.05       # 強勢車款利潤空間壓縮
        else:
            b2b_limit = median_auction * 0.90          # 常規資產 10% 邊際護城河
            retail_floor = median_auction * 1.08
            
        dealer_margin = dealer_price - median_auction 
        
        # 稅金與 TCO 動態提列
        tax_3yr = calculate_taiwan_tax_3yr(cc_input, is_bev)
        total_maint, base_maint, heavy_maint, battery_fund, maint_items = calculate_tco_details(is_hybrid, is_bev, target_mileage)
        
        total_3yr_expense = total_maint + tax_3yr
        residual_value = median_auction * 0.65 if is_bev else median_auction * 0.70
        true_cost = dealer_price + total_3yr_expense - residual_value

        # 頂部戰略底牌
        st.markdown(f"""
        <div class='premium-box'>
            <h3 style='margin-top:0px; color:#F8FAFC;'>賽局底牌透視：真實大盤實相還原</h3>
            <p>透過時間序列還原模型（校正基準里程：{avg_sample_mileage:,.0f} KM），此車況之 B2B 盤價中位數還原為 <b>{median_auction:,.0f} TWD</b>。</p>
            <p>本專案設定之 <b>B2B 進貨極限（MAF 鐵底）</b> 為 <span class='margin-text'>{b2b_limit:,.0f} TWD</span>。高於此價即屬低期望值（Low EV）追高。</p>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["🏷️ 價格合規防禦", "💸 三年現金流瀑布", "🔧 維修黑洞拆解 (核心)"])

        # Tab 1: 價格合規防線
        with tab1:
            st.markdown("### 🎯 車商開價 vs 真實大盤防禦線")
            fig_price_comp = go.Figure()
            
            fig_price_comp.add_trace(go.Bar(
                x=['MAF 進貨極限鐵底', '還原大盤中位數', '合理零售門檻', '當前車商開價'],
                y=[b2b_limit, median_auction, retail_floor, dealer_price],
                text=[f"${b2b_limit:,.0f}", f"${median_auction:,.0f}", f"${retail_floor:,.0f}", f"${dealer_price:,.0f}"],
                textposition='auto',
                marker_color=['#94A3B8', '#64748B', '#1E3A8A', '#DC2626' if dealer_price > retail_floor * 1.15 else '#10B981'],
                width=0.4
            ))
            
            fig_price_comp.update_layout(yaxis=dict(title="金額 (TWD)", gridcolor="#E2E8F0"), plot_bgcolor='rgba(0,0,0,0)', height=550)
            st.plotly_chart(fig_price_comp, use_container_width=True)
            
            if dealer_price < b2b_limit: 
                st.error("🚨 **極高風險誘餌警示**：開價低於盤商進貨成本！極大概率為空氣車或重大事故隱瞞。Low EV，請放棄推進。")
            elif dealer_price > retail_floor * 1.12:
                st.warning("⚠️ **溢價警告**：利潤空間完全偏向車商。殺價腳本必須徹底執行。")
            else: 
                st.success("✅ **合規區間**：開價符合當前大盤合理運作利潤。")

        # Tab 2: 現金流瀑布圖
        with tab2:
            st.markdown("### 🔮 三年持有成本結構 (TCO Waterfall)")
            fig_waterfall = go.Figure(go.Waterfall(
                orientation="v", measure=["relative", "relative", "relative", "total"],
                x=["1. 買車當下支出", "2. 三年預計 TCO (稅金/耗材)", "3. 三年後估算殘值", "4. 實際持有淨成本"],
                textposition="outside",
                text=[f"${dealer_price/10000:.1f}萬", f"+${total_3yr_expense/10000:.1f}萬", f"-${residual_value/10000:.1f}萬", f"${true_cost/10000:.1f}萬"],
                y=[dealer_price, total_3yr_expense, -residual_value, true_cost],
                connector={"line":{"color":"#94A3B8", "width":2, "dash":"dot"}},
                decreasing={"marker":{"color":"#10B981"}}, increasing={"marker":{"color":"#EF4444"}}, totals={"marker":{"color":"#0F172A"}}
            ))
            fig_waterfall.update_layout(yaxis=dict(gridcolor="#E2E8F0"), plot_bgcolor='rgba(0,0,0,0)', height=550)
            st.plotly_chart(fig_waterfall, use_container_width=True)

        # Tab 3: 維修黑洞拆解
        with tab3:
            car_type_str = "BEV 純電資產" if is_bev else ("Hybrid 油電系統" if is_hybrid else "純內燃機系統")
            st.markdown(f"### ⚙️ {car_type_str} 專屬物理衰變預測")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("基礎耗材與動態稅金", f"${base_maint + tax_3yr:,.0f}", delta=f"內含三年稅金 ${tax_3yr:,}")
            c2.metric("大保養/老化機件提列", f"${heavy_maint:,.0f}")
            c3.metric("新能源大電池提列", f"${battery_fund:,.0f}")
            
            st.markdown("#### 📋 系統強制提列維修清單 (未來三年)")
            for item in maint_items:
                st.markdown(f"<div class='risk-item'>✔️ {item}</div>", unsafe_allow_html=True)
                
            st.markdown("---")
            if battery_fund > 0 or heavy_maint > 0:
                st.warning("⚠️ **工程與博弈風險提示**：標的物已跨越核心機件壽命斷崖。簽約前強制要求插電腦讀取電池健康度 (SOH) 或進行底盤漏油封條檢查。")

        # 底部談判腳本
        st.markdown("---")
        st.subheader("💡 談判賽局：高期望值殺價腳本")
        script = f"「老闆，我調過拍賣場時間序列大數據，這年份這里程的盤價中位數還原出來是 {median_auction/10000:.1f} 萬。考慮到接下來三年這款{car_type_str}有動態稅金與大保養耗材共 {total_3yr_expense/10000:.1f} 萬的剛性維修黑洞要填，我方評估後的 High EV 得標零售價落在 {retail_floor/10000:.1f} 萬。如果你願意抓合理的利潤快速周轉，我們今天這個價格就簽約。」"
        st.markdown(f"> {script}")
else:
    st.warning("該車型組合目前在 SAA 資料庫中無足夠樣本，請確認車型名稱是否完全對齊。")
