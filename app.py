import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import time

# --- 頁面設定 ---
st.set_page_config(page_title="航太級 TCO 精算機", page_icon="✈️")
st.title("✈️ 航太工程師的 CC 購車精算機")

# --- 頂部狀態列 ---
st.markdown(
    """
    <div style="display: flex; gap: 10px;">
        <img src="https://img.shields.io/badge/Standard-Aerospace_Grade-0052CC?style=flat-square" alt="Standard">
        <img src="https://img.shields.io/badge/System-Safety_Check-success?style=flat-square" alt="Safety">
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

st.caption("用「飛機維修」的高標準，重新審視汽車的持有成本與妥善率。")

# --- 側邊欄輸入 ---
st.sidebar.header("1. 設定您的入手價格")
st.sidebar.info("💡 請輸入最終成交價")
gas_car_price = st.sidebar.number_input("⛽ 汽油版 - 入手價", value=760000, step=10000)
hybrid_car_price = st.sidebar.number_input("⚡ 油電版 - 入手價", value=880000, step=10000)

st.sidebar.header("2. 用車習慣 (飛行計畫)")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 3000, 50000, 15000) 
years_to_keep = st.sidebar.slider("預計持有幾年", 1, 10, 5)
gas_price = st.sidebar.number_input("目前油價", value=31.0)

st.sidebar.header("3. 維修參數 (飛安係數)")
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)
force_battery = st.sidebar.checkbox("⚠️ 強制列入電池更換費 (風險控管)", value=False)

# --- 計算邏輯 ---
def get_residual_rate(year):
    if year <= 0: return 1.0
    elif year == 1: return 0.80
    else: return max(0.80 - ((year - 1) * 0.05), 0.0)

current_rate = get_residual_rate(years_to_keep)
gas_resale_value = gas_car_price * current_rate
hybrid_resale_value = hybrid_car_price * current_rate

total_km = annual_km * years_to_keep
gas_fuel_cost = (total_km / 12.0) * gas_price
hybrid_fuel_cost = (total_km / 21.0) * gas_price
tax_total = 11920 * years_to_keep
tax_gas = tax_total
tax_hybrid = tax_total

battery_risk_cost = 0
battery_status_msg = "✅ 系統檢測正常 (里程低，暫不計入)"
if force_battery or total_km > 160000 or years_to_keep > 8:
    battery_risk_cost = battery_cost
    battery_status_msg = "⚠️ 系統風險預警：已計入大電池更換成本"

tco_gas = (gas_car_price - gas_resale_value) + gas_fuel_cost + tax_gas
tco_hybrid = (hybrid_car_price - hybrid_resale_value) + hybrid_fuel_cost + tax_hybrid + battery_risk_cost
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
        
        # 標題
        pdf.cell(0, 10, "Toyota Corolla Cross TCO 分析報告 (航太級)", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(5)

        # 參數
        pdf.set_font("TaipeiSans", size=10)
        pdf.cell(0, 10, f"飛行任務參數：持有 {years_to_keep} 年 / 每年 {annual_km:,} km", new_x="LMARGIN", new_y="NEXT")
        
        # 表格
        pdf.set_font("TaipeiSans", size=12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(95, 10, "監測項目", border=1, align='C', fill=True)
        pdf.cell(47, 10, "汽油版", border=1, align='C', fill=True)
        pdf.cell(47, 10, "油電版", border=1, new_x="LMARGIN", new_y="NEXT", align='C', fill=True)

        def add_row(name, val1, val2):
            pdf.cell(95, 10, str(name), border=1)
            pdf.cell(47, 10, f"${int(val1):,}", border=1, align='R')
            pdf.cell(47, 10, f"${int(val2):,}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')

        add_row("車價折舊損失", gas_car_price - gas_resale_value, hybrid_car_price - hybrid_resale_value)
        add_row("總油錢支出", gas_fuel_cost, hybrid_fuel_cost)
        add_row("稅金總額", tax_gas, tax_hybrid)
        add_row("大電池風險", 0, battery_risk_cost)
        
        pdf.cell(95, 12, "【總持有成本 TCO】", border=1)
        pdf.cell(47, 12, f"${int(tco_gas):,}", border=1, align='R')
        pdf.cell(47, 12, f"${int(tco_hybrid):,}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')
        
        # 結論
        pdf.ln(5)
        pdf.set_font("TaipeiSans", size=14)
        if diff > 0:
            pdf.cell(0, 10, f"🏆 推薦型號：【油電版】 (預計節省 ${int(diff):,})", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 10, f"🏆 推薦型號：【汽油版】 (預計節省 ${int(abs(diff)):,})", new_x="LMARGIN", new_y="NEXT")

        # 災情表
        pdf.ln(10)
        pdf.set_fill_color(255, 240, 240)
        pdf.set_font("TaipeiSans", size=14)
        pdf.cell(0, 10, "⚠️ 機體結構與系統弱點檢查表 (驗車必看)", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("TaipeiSans", size=11)
        pdf.ln(3)
        issues = [
            "1. [機體結構] 車頂架漏水：A柱/C柱水痕、頂蓬霉味 (2020-2021年式好發)。",
            "2. [懸吊系統] 避震器過軟：後座乘客易產生暈眩，建議試駕確認。",
            "3. [航電系統] 原廠車機：易發生死機、訊號延遲。",
            "4. [動力系統] 油電版電池濾網：位於後座側邊，堵塞將導致散熱失效。",
            "5. [制動系統] 煞車總泵異音：踩放時有滋滋電流聲(正常特性)，過大需注意。",
            "6. [傳動系統] CVT頓挫：低速收油再補油有拉扯感，屬物理特性。"
        ]
        for issue in issues:
            pdf.cell(0, 8, issue, new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(10)
        pdf.set_font("TaipeiSans", size=10)
        pdf.cell(0, 10, "本報告由【航太工程師 TCO 計算機】自動生成。", align='C')
        
        # 強制轉型
        return bytes(pdf.output())

    except Exception as e:
        st.error(f"❌ PDF 生成失敗: {str(e)}")
        return None

# --- 顯示網頁 ---
col1, col2 = st.columns(2)
with col1:
    st.metric("汽油版總花費", f"${int(tco_gas):,}")
with col2:
    st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")

if diff > 0:
    st.success(f"🏆 數據顯示：【油電版】更具經濟效益！省下 **${int(diff):,}**")
else:
    st.error(f"🏆 數據顯示：【汽油版】更具經濟效益！省下 **${int(abs(diff)):,}**")

st.info(f"💡 電池模組狀態：{battery_status_msg}")
st.markdown("---")

# 圖表
st.subheader("📊 全生命週期成本分析 (LCC Analysis)")
cost_data = pd.DataFrame({
    "項目": ["折舊", "油錢", "稅金", "大電池"],
    "汽油版": [gas_car_price - gas_resale_value, gas_fuel_cost, tax_gas, 0],
    "油電版": [hybrid_car_price - hybrid_resale_value, hybrid_fuel_cost, tax_hybrid, battery_risk_cost]
})
st.bar_chart(cost_data.set_index("項目"))

st.subheader("📉 資產殘值預測曲線")
years_range = list(range(1, 11))
rates = [get_residual_rate(y) for y in years_range]
resale_df = pd.DataFrame({
    "年份": years_range,
    "殘值率": [f"{int(r*100)}%" for r in rates],
    "汽油版殘值": [int(gas_car_price * r) for r in rates],
    "油電版殘值": [int(hybrid_car_price * r) for r in rates]
})
st.dataframe(resale_df, use_container_width=True)

st.markdown("---")
st.subheader("🔍 航太工程師的災情資料庫")
st.caption("就像飛機起飛前的 Pre-flight Check，買車前務必確認這些項目。")

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
else:
    st.warning("⚠️ 系統初始化中，請確認字型檔是否正確掛載...")

st.markdown("---")

# ==========================================
# 🚀 假門測試 (Smoke Test) - Mobile01 安全版
# ==========================================
st.markdown("#### 👨‍🔧 想像檢查飛機一樣檢查二手車？")
st.markdown("我正在將航太維修的 SOP 轉化為二手車驗車手冊。")

col_a, col_b = st.columns([3, 1])

with col_a:
    # 修改點：把價格拿掉，改成 Coming Soon
    st.markdown("👉 **《航太級 CC 驗車圖文手冊》 (Coming Soon)**")

with col_b:
    if st.button("🔥 搶先預約"):
        st.toast("🙏 收到您的預約請求！", icon="✈️")
        time.sleep(1)
        st.toast("本手冊正在進行最終飛安校對 (Final Check)。", icon="👨‍🔧")
        time.sleep(1)
        st.toast("上線後將優先通知您！", icon="📅")
