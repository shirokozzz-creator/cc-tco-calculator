import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import requests

# --- 頁面設定 ---
st.set_page_config(page_title="CC TCO 精算機 (工程師版)", page_icon="🚙")
st.title("🚙 CC 油電 vs. 汽油：TCO 分析報告")

# --- 頂部狀態列 ---
st.markdown(
    """
    <div style="display: flex; gap: 10px;">
        <img src="https://img.shields.io/badge/Version-2026_Pro-blue?style=flat-square" alt="Version">
        <img src="https://img.shields.io/badge/Engineer-Verified-success?style=flat-square" alt="Verified">
        <img src="https://img.shields.io/badge/Update-Daily-orange?style=flat-square" alt="Update">
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 🛠️ 自動修復字型功能 (Auto-Fix Font)
# ==========================================
def check_and_download_font():
    font_filename = "TaipeiSans.ttf"
    # 檢查檔案是否存在或損壞
    if not os.path.exists(font_filename) or os.path.getsize(font_filename) < 1000000:
        with st.spinner('正在自動下載中文字型檔 (第一次會比較久)...'):
            try:
                url = "https://raw.githubusercontent.com/StellarCN/scp_zh/master/fonts/fireflysung.ttf"
                response = requests.get(url)
                with open(font_filename, "wb") as f:
                    f.write(response.content)
                # st.success("✅ 字型檔自動修復完成！")
            except Exception as e:
                st.error(f"❌ 字型下載失敗: {str(e)}")

check_and_download_font()
# ==========================================

# --- 側邊欄輸入 ---
st.sidebar.header("1. 設定您的入手價格")
st.sidebar.info("💡 請輸入您談到的最終成交價")
gas_car_price = st.sidebar.number_input("⛽ 汽油版 - 入手價", value=760000, step=10000)
hybrid_car_price = st.sidebar.number_input("⚡ 油電版 - 入手價", value=880000, step=10000)

st.sidebar.header("2. 用車習慣")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 3000, 50000, 15000) 
years_to_keep = st.sidebar.slider("預計持有幾年", 1, 10, 5)
gas_price = st.sidebar.number_input("目前油價", value=31.0)

st.sidebar.header("3. 維修參數")
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)
force_battery = st.sidebar.checkbox("⚠️ 強制列入電池更換費 (最壞打算)", value=False)

# --- 核心計算 ---
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
battery_status_msg = "✅ 安全範圍 (里程低，暫不計入)"

if force_battery or total_km > 160000 or years_to_keep > 8:
    battery_risk_cost = battery_cost
    if force_battery:
        battery_status_msg = "⚠️ 已強制計入大電池費用 (最壞打算)"
    else:
        battery_status_msg = "⚠️ 高里程/高年份，已自動計入電池費"

tco_gas = (gas_car_price - gas_resale_value) + gas_fuel_cost + tax_gas
tco_hybrid = (hybrid_car_price - hybrid_resale_value) + hybrid_fuel_cost + tax_hybrid + battery_risk_cost
diff = tco_gas - tco_hybrid

# --- PDF 產生引擎 (Strict Mode) ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    
    # 1. 載入字型
    try:
        # 自動搜尋 .ttf 檔案
        found_font = "TaipeiSans.ttf" # 預設
        for f in os.listdir('.'):
            if f.lower().endswith('.ttf'):
                found_font = f
                break
        
        pdf.add_font('TaipeiSans', '', found_font, uni=True)
        pdf.set_font('TaipeiSans', '', 16)
    except Exception as e:
        st.error(f"❌ 字型錯誤: {str(e)}")
        return None

    # 2. 標題 (使用 ln=1 而不是 ln=True)
    pdf.cell(0, 10, 'Toyota Corolla Cross TCO 分析報告', ln=1, align='C')
    pdf.ln(10)

    # 3. 參數
    pdf.set_font('TaipeiSans', '', 12)
    # 強制轉型成字串 str() 避免錯誤
    param_text = f"分析參數：持有 {years_to_keep} 年 / 每年 {annual_km:,} 公里 / 油價 {gas_price} 元"
    pdf.cell(0, 10, str(param_text), ln=1)
    pdf.ln(5)

    # 4. 表格
    pdf.set_fill_color(240, 240, 240)
    # 使用 border=1 明確指定
    pdf.cell(95, 10, '項目', border=1, ln=0, align='C', fill=True)
    pdf.cell(47, 10, '汽油版', border=1, ln=0, align='C', fill=True)
    pdf.cell(47, 10, '油電版', border=1, ln=1, align='C', fill=True) # ln=1 代表換行

    def add_row(name, val1, val2):
        # 確保所有輸入都是字串
        pdf.cell(95, 10, str(name), border=1)
        pdf.cell(47, 10, f"${int(val1):,}", border=1, ln=0, align='R')
        pdf.cell(47, 10, f"${int(val2):,}", border=1, ln=1, align='R')

    add_row("車價折舊損失 (買-賣)", gas_car_price - gas_resale_value, hybrid_car_price - hybrid_resale_value)
    add_row("總油錢支出", gas_fuel_cost, hybrid_fuel_cost)
    add_row("稅金總額", tax_gas, tax_hybrid)
    add_row("大電池風險", 0, battery_risk_cost)
    
    # 5. 總結
    pdf.cell(95, 12, "【總持有成本 TCO】", border=1)
    pdf.cell(47, 12, f"${int(tco_gas):,}", border=1, ln=0, align='R')
    pdf.cell(47, 12, f"${int(tco_hybrid):,}", border=1, ln=1, align='R')
    pdf.ln(10)

    # 6. 建議
    pdf.set_font('TaipeiSans', '', 14)
    if diff > 0:
        pdf.cell(0, 10, f"🏆 建議購買：【油電版】 (省下 ${int(diff):,})", ln=1)
    else:
        pdf.cell(0, 10, f"🏆 建議購買：【汽油版】 (省下 ${int(abs(diff)):,})", ln=1)

    pdf.ln(20)
    pdf.set_font('TaipeiSans', '', 10)
    pdf.cell(0, 10, "本報告由【中油工程師 TCO 計算機】自動生成。", ln=1, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 顯示網頁內容 ---
col1, col2 = st.columns(2)
with col1:
    st.metric("汽油版總花費", f"${int(tco_gas):,}")
with col2:
    st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")

if diff > 0:
    st.success(f"🏆 油電版獲勝！省下 **${int(diff):,}**")
else:
    st.error(f"🏆 汽油版獲勝！省下 **${int(abs(diff)):,}**")

st.info(f"💡 電池計算狀態：{battery_status_msg}")
st.markdown("---")

# 圖表與災情區 (維持原樣)
st.subheader("💰 成本結構拆解")
cost_data = pd.DataFrame({
    "項目": ["折舊損失", "油錢", "稅金", "大電池"],
    "汽油版": [gas_car_price - gas_resale_value, gas_fuel_cost, tax_gas, 0],
    "油電版": [hybrid_car_price - hybrid_resale_value, hybrid_fuel_cost, tax_hybrid, battery_risk_cost]
})
st.bar_chart(cost_data.set_index("項目"))

st.subheader("📉 未來 10 年殘值預測")
years_range = list(range(1, 11))
rates = [get_residual_rate(y) for y in years_range]
resale_df = pd.DataFrame({
    "年份": years_range,
    "折舊後剩餘價值 (%)": [f"{int(r*100)}%" for r in rates],
    "汽油版殘值": [int(gas_car_price * r) for r in rates],
    "油電版殘值": [int(hybrid_car_price * r) for r in rates]
})
st.dataframe(resale_df, use_container_width=True)

st.markdown("---")
st.subheader("🔍 工程師的災情資料庫 (驗車必看)")
st.caption("買車前先看缺點，才知道能不能接受。")

with st.expander("🚨 全車系共同通病 (漏水/避震/車機) - 點擊展開"):
    st.markdown("""
    - **💦 車頂架漏水 (2020-2021前期款最慘)**
        - 解法：原廠有召回更換防水墊片，買二手需確認是否已處理。
    - **🤢 避震器過軟 (暈車屬性)**
        - 建議：試駕時請家人坐後座感受，很多人買回後需花 2-3 萬改裝避震。
    - **🖥️ 原廠車機 (Drive+ Connect) 災情**
        - 建議：不要對原廠車機抱太大期望，改裝安卓機 (約 1.5 萬) 是常見解法。
    """)

tab1, tab2 = st.tabs(["⚡ 油電版要注意", "⛽ 汽油版要注意"])
with tab1:
    st.markdown("""
    - **🔋 大電池散熱網堵塞**：必看後座旁濾網是否乾淨！
    - **🔊 煞車總泵異音**：踩放煞車若有過大「滋滋」聲要注意。
    """)
with tab2:
    st.markdown("""
    - **🐢 CVT 低速頓挫感**：20-40km/h 收油再補會有拉扯感，屬正常特性。
    - **📉 市區油耗**：純市區可能只有 9-10 km/L。
    """)

st.markdown("---")

# PDF 下載區
st.subheader("📥 下載您的分析報告")
if st.button("📄 生成 A4 報告 (PDF)"):
    pdf_bytes = create_pdf()
    if pdf_bytes:
        st.download_button(
            label="👉 點此下載報告",
            data=pdf_bytes,
            file_name="CC_TCO_Report.pdf",
            mime="application/pdf"
        )

st.markdown("---")
st.markdown("#### 想知道更詳細的驗車眉角？")
st.markdown("👉 [**下載：CC 驗車懶人包 (PDF) - $199**](#)")
