import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# ==========================================
# 1. UI 設定與系統初始化
# ==========================================
st.set_page_config(page_title="Naval Motors 鑑定防禦系統", layout="wide")
st.markdown("""
    <style>
    .main-title { font-size: 36px; font-weight: 900; color: #1E3A8A; }
    .sub-title { font-size: 16px; color: #64748B; margin-bottom: 20px; }
    .script-box { background-color: #F8FAFC; border-left: 4px solid #3B82F6; padding: 15px; font-family: monospace; }
    </style>
    <div class='main-title'>Naval Motors 資產防禦報告 v0.6</div>
    <div class='sub-title'>系統已載入 17 個月拍賣大數據 ｜ 啟動五大市場恐懼消除協議</div>
    """, unsafe_allow_html=True)

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

# ==========================================
# 2. 側邊欄：實體特徵輸入 (The Hook)
# ==========================================
try:
    models = pd.read_sql("SELECT DISTINCT 車系與車型 FROM auctions_time_series", sqlite3.connect("cars_time_series.db"))['車系與車型'].tolist()
except: models = []

st.sidebar.markdown("### 🛠️ 標的物參數設定")
selected_model = st.sidebar.selectbox("評估車型", models, index=models.index('NX200') if 'NX200' in models else 0)
df_car = get_model_data(selected_model)

if not df_car.empty:
    selected_year = st.sidebar.selectbox("出廠年份", sorted(df_car['出廠年份'].unique(), reverse=True))
    selected_color = st.sidebar.selectbox("車輛顏色", sorted(df_car['車色'].unique()))
    
    st.sidebar.markdown("### 📉 交易與車況條件")
    target_mileage = st.sidebar.number_input("車商標示里程 (km)", value=75000, step=5000)
    dealer_price = st.sidebar.number_input("車商開價 (TWD)", value=800000, step=10000)
    has_third_party = st.sidebar.radio("具備第三方鑑定書 (Goo/YES/萊茵)?", ["是", "否"])
    is_hybrid = st.sidebar.toggle("此為 Hybrid 油電車型")

    # 數據篩選
    df_filtered = df_car[(df_car['出廠年份'] == selected_year) & (df_car['車色'] == selected_color)]
    
    # ==========================================
    # 3. 主畫面：五大恐懼防禦報告 (The Value)
    # ==========================================
    if not df_filtered.empty:
        median_auction = df_filtered['得標價'].median()
        retail_floor = median_auction * 1.08 # 8% 系統認定合理利潤
        
        st.markdown("---")
        st.markdown(f"### 🛡️ {selected_year}年 {selected_color} {selected_model} 專屬防禦健檢")
        
        # 恐懼 1：釣魚價防禦 (Price Phishing)
        st.subheader("1. 價格防禦 (防範 8891 釣魚空氣車)")
        col1, col2, col3 = st.columns(3)
        col1.metric("行內批發盤價中位數", f"${median_auction:,.0f}")
        col2.metric("合理零售樓地板 (+8%)", f"${retail_floor:,.0f}")
        
        if dealer_price < retail_floor:
            col3.metric("溢價空間", f"${dealer_price - retail_floor:,.0f}", delta_color="inverse")
            st.error(f"🚨 **釣魚/重大瑕疵警報**：開價低於全台批發底價。高機率為假自售、空氣車或隱瞞重大事故，**期望值為負，系統強烈建議禁止前往看車。**")
        else:
            col3.metric("溢價空間", f"+${dealer_price - retail_floor:,.0f}", delta_color="normal")
            st.success("✅ 開價位於合理套利空間之上，未觸發釣魚警示，可進行下一步談判。")

        # 恐懼 2：里程調錶防禦 (Odometer Rollback)
        st.subheader("2. 里程常態稽核 (防範惡意調錶)")
        # 假設當前為 2026 年
        car_age = max(1, 2026 - selected_year)
        annual_mileage = target_mileage / car_age
        if annual_mileage < 8000:
            st.warning(f"⚠️ **異常低里程警示**：此車年均里程僅 {annual_mileage:,.0f} km，遠低於台灣平均水準 (1.5萬km)。極大機率遭調錶，**請務必強制查驗監理站 APP 歷史驗車紀錄**。")
        else:
            st.info(f"ℹ️ 年均里程約 {annual_mileage:,.0f} km，屬於市場常態衰變範圍。")

        # 恐懼 3：事故車防禦 (Structural Risk)
        st.subheader("3. 結構與產權防禦 (防範重大修復歷/泡水)")
        if has_third_party == "是":
            st.success("✅ **具備頂級防禦**：擁有第三方鑑定。簽約時請核對車身號碼，並要求將「鑑定表無記載之重大事故原價買回」寫入合約。")
        else:
            st.error("☠️ **致命結構風險**：無獨立第三方背書。統計上買到重大修復歷機率飆升，系統建議將購車預算額外扣除 15% 作為風險準備金。")

        # 恐懼 4：維修黑洞防禦 (TCO & Maintenance)
        st.subheader("4. 未來三年 TCO 維修黑洞預測")
        tco_base = 42000 # 三年常規保養與耗材
        battery_fund = 55000 if (is_hybrid and target_mileage > 100000) else 0
        
        tco_c1, tco_c2 = st.columns(2)
        tco_c1.info(f"**三年常規保養與耗材預估：** ${tco_base:,.0f} TWD")
        if battery_fund > 0:
            tco_c2.error(f"🔧 **高風險機件衰變觸發：大電池準備金 ${battery_fund:,.0f} TWD** (因里程突破十萬公里，系統強制提列)")
        elif target_mileage > 100000:
            tco_c2.warning("🔧 **機件衰變觸發**：里程突破十萬，需預先提列底盤橡膠、避震器與冷卻系統更新準備金。")
        else:
            tco_c2.success("✅ 核心機件尚未進入高頻失效期。")

        # 恐懼 5：車貸陷阱防禦 (Opportunity Cost)
        st.subheader("5. 財務陷阱防禦 (機會成本與談判話術)")
        etf_return = dealer_price * ((1 + 0.07)**3 - 1)
        st.warning(f"💸 **高利貸/現金機會成本**：若您接受車商高利貸款，或投入全額現金，相較於將同等資金 ({dealer_price:,.0f}) 投入年化 7% 的大盤 ETF，您未來三年將產生高達 **${etf_return:,.0f} TWD** 的隱藏財富損失。")
        
        st.markdown("💡 **Naval Motors 實戰殺價腳本 (請直接複製使用)：**")
        script = f"「老闆你好，我看過這台 {selected_year} 年 {selected_model} 的數據了，目前盤價大約在 {median_auction/10000:.0f} 萬上下。因為車子里程已經 {target_mileage/10000:.1f} 萬，後續我要準備一筆 {int((tco_base+battery_fund)/10000)} 萬的預防性保養金。如果能以 {retail_floor/10000:.1f} 萬成交，且合約註明第三方檢驗無誤，我今天就能現金/自辦信貸結清，不需讓你們辦車貸。」"
        st.markdown(f"<div class='script-box'>{script}</div>", unsafe_allow_html=True)

        # 視覺化：市場散佈圖
        st.markdown("---")
        st.subheader("📊 模組六：同級距市場散佈圖")
        df_filtered['價格(萬)'] = df_filtered['得標價'] / 10000
        color_map = {'白': '#F8FAFC', '黑': '#0F172A', '銀': '#94A3B8', '灰': '#475569', '淺棕': '#D6D3D1', '紅': '#EF4444', '藍': '#3B82F6', '其他': '#10B981'}
        fig = px.scatter(df_filtered, x="里程數", y="價格(萬)", color="車色", color_discrete_map=color_map, title=f"市場交易價格與折舊曲線")
        fig.update_layout(plot_bgcolor='#E2E8F0', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("該條件組合在資料庫中無足夠樣本。請嘗試放寬年份或顏色條件。")
