
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
# 🛠️ 終極字型修復引擎 (Auto-Fix Font v2)
# ==========================================
def check_and_download_font():
    font_filename = "TaipeiSans.ttf"
    
    # 1. 檢查檔案是否已經存在
    if os.path.exists(font_filename):
        # 讀取檔案前 4 個 bytes，看看是不是真的字型 (字型檔通常以 0x00 或 O 開頭)
        try:
            with open(font_filename, 'rb') as f:
                header = f.read(4)
            # 如果開頭是 "<" (代表是 HTML 網頁)，那就是壞檔！
            if header.startswith(b'<') or header.startswith(b'<!DO'):
                st.warning("⚠️ 偵測到損毀的字型檔 (是網頁不是字型)，正在自動刪除重抓...")
                os.remove(font_filename)
        except:
            os.remove(font_filename)

    # 2. 如果檔案不在了 (被刪了或是本來就沒有)，開始下載
    if not os.path.exists(font_filename):
        with st.spinner('正在從 Google 下載正版字型 (Noto Sans TC)...'):
            try:
                # 使用 Google Fonts 的官方原始檔，最穩定
                url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/NotoSansTC-Regular.ttf"
                # 偽裝成瀏覽器，避免被擋
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    with open(font_filename, "wb") as f:
                        f.write(response.content)
                    st.success("✅ 字型檔修復完成！")
                else:
                    st.error(f"❌ 下載失敗，伺服器回應代碼：{response.status_code}")
            except Exception as e:
                st.error(f"❌ 字型下載發生錯誤: {str(e)}")

# 執行修復
check_and_download_font()
# ==========================================

# --- 側邊欄輸入 ---
st.sidebar.header("1. 設定您的入手價格")
gas_car_price = st.sidebar.number_input("⛽ 汽油版 - 入手價", value=760000, step=10000)
hybrid_car_price = st.sidebar.number_input("⚡ 油電版 - 入手價", value=880000, step=10000)

st.sidebar.header("2. 用車習慣")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 3000, 50000, 15000) 
years_to_keep = st.sidebar.slider("預計持有幾年", 1, 10, 5)
gas_price = st.sidebar.number_input("目前油價", value=31.0)

st.sidebar.header("3. 維修參數")
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)
force_battery = st.sidebar.checkbox("⚠️ 強制列入電池更換費 (最壞打算)", value=False)

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
battery_status_msg = "✅ 安全範圍"
if force_battery or total_km > 160000 or years_to_keep > 8:
    battery_risk_cost = battery_cost
    battery_status_msg = "⚠️ 已計入大電池費用"

tco_gas = (gas_car_price - gas_resale_value) + gas_fuel_cost + tax_gas
tco_hybrid = (hybrid_car_price - hybrid_resale_value) + hybrid_fuel_cost + tax_hybrid + battery_risk_cost
diff = tco_gas - tco_hybrid

# --- PDF 產生引擎 (fpdf2) ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    
    # 載入字型
    try:
        # 直接指定我們剛剛下載好的 Noto Sans
        pdf.add_font("TaipeiSans", fname="TaipeiSans.ttf")
        pdf.set_font("TaipeiSans", size=16)
    except Exception as e:
        st.error(f"❌ PDF 引擎錯誤: {str(e)}")
        # 如果失敗，嘗試刪除壞檔讓使用者再按一次
        if os.path.exists("TaipeiSans.ttf"):
            os.remove("TaipeiSans.ttf")
        return None

    # 內容生成
    pdf.cell(0, 10, "Toyota Corolla Cross TCO 分析報告", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(5)

    pdf.set_font("TaipeiSans", size=12)
    pdf.cell(0, 10, f"分析參數：持有 {years_to_keep} 年 / 每年 {annual_km:,} km", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # 表格
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(95, 10, "項目", border=1, align='C', fill=True)
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
    
    # 總結
    pdf.cell(95, 12, "【總持有成本 TCO】", border=1)
    pdf.cell(47, 12, f"${int(tco_gas):,}", border=1, align='R')
    pdf.cell(47, 12, f"${int(tco_hybrid):,}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.ln(10)

    pdf.set_font("TaipeiSans", size=14)
    if diff > 0:
        pdf.cell(0, 10, f"🏆 建議購買：【油電版】 (省下 ${int(diff):,})", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 10, f"🏆 建議購買：【汽油版】 (省下 ${int(abs(diff)):,})", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font("TaipeiSans", size=10)
    pdf.cell(0, 10, "本報告由【中油工程師 TCO 計算機】自動生成。", align='C')
    
    return pdf.output()

# --- 顯示網頁 ---
col1, col2 = st.columns(2)
with col1:
    st.metric("汽油版總花費", f"${int(tco_gas):,}")
with col2:
    st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")

if diff > 0:
    st.success(f"🏆 油電版獲勝！省下 **${int(diff):,}**")
else:
    st.error(f"🏆 汽油版獲勝！省下 **${int(abs(diff)):,}**")

st.info(f"💡 電池狀態：{battery_status_msg}")
st.markdown("---")

# 圖表
cost_data = pd.DataFrame({
    "項目": ["折舊", "油錢", "稅金", "大電池"],
    "汽油版": [gas_car_price - gas_resale_value, gas_fuel_cost, tax_gas, 0],
    "油電版": [hybrid_car_price - hybrid_resale_value, hybrid_fuel_cost, tax_hybrid, battery_risk_cost]
})
st.bar_chart(cost_data.set_index("項目"))

st.subheader("📉 未來 10 年殘值預測")
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
st.subheader("🔍 工程師的災情資料庫")
with st.expander("🚨 全車系共同通病 (點擊展開)"):
    st.markdown("""
    - **💦 車頂架漏水**：20-21年式最慘，買二手必驗頂蓬水痕。
    - **🤢 避震器過軟**：後座易暈車，建議試駕或預留改裝費。
    - **🖥️ 車機災情**：原廠車機易當機/訊號差。
    """)
st.markdown("---")

st.subheader("📥 下載您的分析報告")
if st.button("📄 生成 A4 報告 (PDF)"):
    pdf_bytes = create_pdf()
    if pdf_bytes:
        st.download_button("👉 點此下載報告", pdf_bytes, "CC_Report.pdf", "application/pdf")

st.markdown("---")
st.markdown("#### 👉 [下載：CC 驗車懶人包 (PDF) - $199](#)")
