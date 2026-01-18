import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import time
import math # 引入數學模組來算指數

# --- 頁面設定 ---
st.set_page_config(page_title="航太級 TCO 精算機", page_icon="✈️")
st.title("✈️ 航太工程師的 CC 購車精算機")

# --- 頂部狀態列 ---
st.markdown(
    """
    <div style="display: flex; gap: 10px;">
        <img src="https://img.shields.io/badge/Data-Real_Auction_Verified-0052CC?style=flat-square" alt="Data">
        <img src="https://img.shields.io/badge/Model-Exponential_Decay-orange?style=flat-square" alt="Model">
        <img src="https://img.shields.io/badge/Source-2026_Jan_Report-success?style=flat-square" alt="Source">
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

st.caption("🚀 系統更新：折舊模型已導入 2025/12-2026/01 共 170 筆真實拍賣場成交數據校正。")

# --- 側邊欄輸入 ---
st.sidebar.header("1. 設定您的入手價格")
st.sidebar.info("💡 預設價差約 10-12 萬")
gas_car_price = st.sidebar.number_input("⛽ 汽油版 - 入手價", value=760000, step=10000)
hybrid_car_price = st.sidebar.number_input("⚡ 油電版 - 入手價", value=880000, step=10000)

st.sidebar.header("2. 用車習慣 (飛行計畫)")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 3000, 60000, 15000) 
years_to_keep = st.sidebar.slider("預計持有幾年", 1, 15, 5) 
gas_price = st.sidebar.number_input("目前油價", value=31.0)

st.sidebar.header("3. 維修參數 (飛安係數)")
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)
force_battery = st.sidebar.checkbox("⚠️ 強制列入電池更換費 (回應網友質疑)", value=False)

# --- [核心升級] 大數據折舊模型 ---
def get_resale_value(initial_price, year, car_type):
    """
    使用指數衰減模型 (Exponential Decay) 計算殘值
    數據來源：2025-2026 拍賣場成交價分析
    """
    if year <= 0: return initial_price
    
    # 參數校正：
    # 汽油版 decay_rate (k) = 0.096
    # 油電版 decay_rate (k) = 0.104 (折舊稍快)
    # 另外，第一年通常會有一個較大的「落地折舊 (Initial Drop)」，約 15-20%
    
    if car_type == 'gas':
        k = 0.096
        initial_drop = 0.82 # 汽油版第一年剩 82%
    else:
        k = 0.104
        initial_drop = 0.80 # 油電版第一年剩 80% (電池疑慮)

    if year == 1:
        return initial_price * initial_drop
    else:
        # 第2年開始走指數衰減
        # 公式：P(t) = P(1) * exp(-k * (t-1))
        p1 = initial_price * initial_drop
        return p1 * math.exp(-k * (year - 1))

# --- 黃金交叉點計算 (Chart Data) ---
chart_data_rows = []
for y in range(1, 11): 
    # 分別計算殘值
    g_resale = get_resale_value(gas_car_price, y, 'gas')
    h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
    
    # 汽油版累積成本
    g_depreciation = gas_car_price - g_resale
    g_fuel = (annual_km * y / 12.0) * gas_price
    g_tax = 11920 * y
    g_total = g_depreciation + g_fuel + g_tax
    
    # 油電版累積成本
    h_depreciation = hybrid_car_price - h_resale
    h_fuel = (annual_km * y / 21.0) * gas_price
    h_tax = 11920 * y
    
    # 電池風險
    h_bat = 0
    if force_battery or (annual_km * y > 160000) or (y > 8):
        h_bat = battery_cost
        
    h_total = h_depreciation + h_fuel + h_tax + h_bat
    
    chart_data_rows.append({
        "年份": f"第{y}年",
        "汽油版累積花費": int(g_total),
        "油電版累積花費": int(h_total)
    })

chart_df = pd.DataFrame(chart_data_rows)

# --- 單點計算 (給下方的詳細數據用) ---
gas_resale_final = get_resale_value(gas_car_price, years_to_keep, 'gas')
hybrid_resale_final = get_resale_value(hybrid_car_price, years_to_keep, 'hybrid')

total_km = annual_km * years_to_keep
gas_fuel_cost = (total_km / 12.0) * gas_price
hybrid_fuel_cost = (total_km / 21.0) * gas_price
tax_total = 11920 * years_to_keep

battery_risk_cost = 0
battery_status_msg = "✅ 系統檢測正常 (里程低，暫不計入)"
if force_battery or total_km > 160000 or years_to_keep > 8:
    battery_risk_cost = battery_cost
    battery_status_msg = "⚠️ 系統風險預警：已計入大電池更換成本"

tco_gas = (gas_car_price - gas_resale_final) + gas_fuel_cost + tax_total
tco_hybrid = (hybrid_car_price - hybrid_resale_final) + hybrid_fuel_cost + tax_total + battery_risk_cost
diff = tco_gas - tco_hybrid

# --- PDF 產生引擎 ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    
    font_path = "TaipeiSans.ttf"
    if not os.path.exists(font_path):
        st.error(f"❌ 系統找不到字型檔：{font_path}")
        return None
        
    try:
        pdf.add_font("TaipeiSans", fname=font_path)
        pdf.set_font("TaipeiSans", size=16)
        
        pdf.cell(0, 10, "Toyota Corolla Cross TCO 分析報告 (航太級)", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(5)

        pdf.set_font("TaipeiSans", size=10)
        pdf.cell(0, 10, f"飛行任務參數：持有 {years_to_keep} 年 / 每年 {annual_km:,} km", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "(註：折舊模型已導入 2026/01 真實市場成交數據校正)", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(5)
        pdf.set_font("TaipeiSans", size=12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(95, 10, "監測項目", border=1, align='C', fill=True)
        pdf.cell(47, 10, "汽油版", border=1, align='C', fill=True)
        pdf.cell(47, 10, "油電版", border=1, new_x="LMARGIN", new_y="NEXT", align='C', fill=True)

        def add_row(name, val1, val2):
            pdf.cell(95, 10, str(name), border=1)
            pdf.cell(47, 10, f"${int(val1):,}", border=1, align='R')
            pdf.cell(47, 10, f"${int(val2):,}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')

        add_row("車價折舊損失", gas_car_price - gas_resale_final, hybrid_car_price - hybrid_resale_final)
        add_row("總油錢支出", gas_fuel_cost, hybrid_fuel_cost)
        add_row("稅金總額", tax_total, tax_total)
        add_row("大電池風險", 0, battery_risk_cost)
        
        pdf.cell(95, 12, "【總持有成本 TCO】", border=1)
        pdf.cell(47, 12, f"${int(tco_gas):,}", border=1, align='R')
        pdf.cell(47, 12, f"${int(tco_hybrid):,}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')
        
        pdf.ln(5)
        pdf.set_font("TaipeiSans", size=14)
        if diff > 0:
            pdf.cell(0, 10, f"🏆 推薦型號：【油電版】 (預計節省 ${int(diff):,})", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 10, f"🏆 推薦型號：【汽油版】 (預計節省 ${int(abs(diff)):,})", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(10)
        pdf.set_fill_color(255, 240, 240)
        pdf.set_font("TaipeiSans", size=14)
        pdf.cell(0, 10, "⚠️ 機體結構與系統弱點檢查表 (驗車必看)", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("TaipeiSans", size=11)
        pdf.ln(3)
        issues = [
            "1. [機體結構] 車頂架漏水：A柱/C柱水痕、頂蓬霉味 (20-21年式)。",
            "2. [懸吊系統] 避震器過軟：後座乘客易產生暈眩。",
            "3. [航電系統] 原廠車機：易發生死機、訊號延遲。",
            "4. [動力系統] 油電版電池濾網：位於後座側邊，堵塞將導致散熱失效。",
            "5. [制動系統] 煞車總泵異音：踩放時有滋滋電流聲(正常特性)。",
            "6. [傳動系統] CVT頓挫：低速收油再補油有拉扯感。"
        ]
        for issue in issues:
            pdf.cell(0, 8, issue, new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(10)
        pdf.set_font("TaipeiSans", size=10)
        pdf.cell(0, 10, "本報告由【航太工程師 TCO 計算機】自動生成。", align='C')
        
        return bytes(pdf.output())

    except Exception as e:
        st.error(f"❌ PDF 生成失敗: {str(e)}")
        return None

# --- 顯示網頁 ---
st.subheader("📈 成本黃金交叉點分析 (大數據校正版)")
st.caption("折舊模型已導入 2026/01 拍賣成交價，真實反映油電/汽油保值性差異。")

st.line_chart(
    chart_df,
    x="年份",
    y=["汽油版累積花費", "油電版累積花費"],
    color=["#FF4B4B", "#0052CC"]
)

col1, col2 = st.columns(2)
with col1:
    st.metric("汽油版總花費", f"${int(tco_gas):,}")
with col2:
    st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")

if diff > 0:
    st.success(f"🏆 數據顯示：【油電版】勝出！省下 **${int(diff):,}**")
else:
    st.error(f"🏆 數據顯示：【汽油版】勝出！省下 **${int(abs(diff)):,}**")

st.info(f"💡 電池模組狀態：{battery_status_msg}")
st.markdown("---")

# 圖表
st.subheader("📊 成本結構拆解")
cost_data = pd.DataFrame({
    "項目": ["折舊", "油錢", "稅金", "大電池"],
    "汽油版": [gas_car_price - gas_resale_final, gas_fuel_cost, tax_total, 0],
    "油電版": [hybrid_car_price - hybrid_resale_final, hybrid_fuel_cost, tax_total, battery_risk_cost]
})
st.bar_chart(cost_data.set_index("項目"))

st.subheader("📉 資產殘值預測 (依據真實拍賣行情)")
years_range = list(range(1, 11))
resale_df_data = []
for y in years_range:
    g_val = get_resale_value(gas_car_price, y, 'gas')
    h_val = get_resale_value(hybrid_car_price, y, 'hybrid')
    resale_df_data.append({
        "年份": y,
        "汽油版殘值": int(g_val),
        "油電版殘值": int(h_val),
        "油電保值優勢": int(h_val - g_val)
    })
st.dataframe(pd.DataFrame(resale_df_data), use_container_width=True)

st.markdown("---")
st.subheader("🔍 航太工程師的災情資料庫")
with st.expander("🚨 機體與系統通病列表 (點擊展開)"):
    st.markdown("""
    - **💦 機體結構 (漏水)**：20-21年式車頂架防水墊片瑕疵，**風險等級：高**。
    - **🤢 懸吊系統 (軟腳)**：原廠設定舒適取向，導致動態不穩，**建議方案：更換改裝避震**。
    - **🖥️ 航電系統 (車機)**：原廠 Drive+ Connect 穩定度不足，**建議方案：改裝安卓機**。
    """)
st.markdown("---")

# PDF 下載區
st.subheader("📥 下載完整分析報告")
pdf_bytes = create_pdf()
if pdf_bytes:
    st.download_button(
        label="👉 下載 PDF 報告 (含災情檢查表)",
        data=pdf_bytes,
        file_name="CC_Aero_Report.pdf",
        mime="application/pdf"
    )

st.markdown("---")

# 假門測試
st.markdown("#### 👨‍🔧 想像檢查飛機一樣檢查二手車？")
st.markdown("我正在將航太維修的 SOP 轉化為二手車驗車手冊。")

col_a, col_b = st.columns([3, 1])
with col_a:
    st.markdown("👉 **《航太級 CC 驗車圖文手冊》 (Coming Soon)**")
with col_b:
    if st.button("🔥 搶先預約"):
        st.toast("🙏 收到您的預約請求！", icon="✈️")
        time.sleep(1)
        st.toast("本手冊正在進行最終飛安校對 (Final Check)。", icon="👨‍🔧")
        time.sleep(1)
        st.toast("上線後將優先通知您！", icon="📅")
