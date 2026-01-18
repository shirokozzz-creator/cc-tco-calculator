import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import time
import math

# --- 頁面設定 ---
st.set_page_config(page_title="航太級 TCO 精算機", page_icon="✈️")
st.title("✈️ 航太工程師的 CC 購車精算機")

# --- 頂部狀態列 ---
st.markdown(
    """
    <div style="display: flex; gap: 10px;">
        <img src="https://img.shields.io/badge/Data-Real_Auction_Verified-0052CC?style=flat-square" alt="Data">
        <img src="https://img.shields.io/badge/Chart-Axis_Fixed-success?style=flat-square" alt="Fix">
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

st.caption("🚀 系統更新：修正時間軸排序問題，折舊模型導入真實拍賣數據。")

# --- 側邊欄輸入 ---
st.sidebar.header("1. 設定您的入手價格")
st.sidebar.info("💡 預設價差約 10-12 萬")
gas_car_price = st.sidebar.number_input("⛽ 汽油版 - 入手價", value=760000, step=10000)
hybrid_car_price = st.sidebar.number_input("⚡ 油電版 - 入手價", value=880000, step=10000)

st.sidebar.header("2. 用車習慣 (飛行計畫)")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 3000, 60000, 15000) 
years_to_keep = st.sidebar.slider("預計持有幾年", 1, 15, 10) # 預設改為10年方便看圖
gas_price = st.sidebar.number_input("目前油價", value=31.0)

st.sidebar.header("3. 維修參數 (飛安係數)")
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)
force_battery = st.sidebar.checkbox("⚠️ 強制列入電池更換費", value=False)

# --- [核心升級] 大數據折舊模型 ---
def get_resale_value(initial_price, year, car_type):
    if year <= 0: return initial_price
    if car_type == 'gas':
        k = 0.096
        initial_drop = 0.82
    else:
        k = 0.104
        initial_drop = 0.80

    if year == 1:
        return initial_price * initial_drop
    else:
        p1 = initial_price * initial_drop
        return p1 * math.exp(-k * (year - 1))

# --- 黃金交叉點計算 (Chart Data) ---
chart_data_rows = []
for y in range(1, 12): # 算到第11年，讓圖表寬一點
    g_resale = get_resale_value(gas_car_price, y, 'gas')
    h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
    
    g_total = (gas_car_price - g_resale) + ((annual_km * y / 12.0) * gas_price) + (11920 * y)
    
    h_bat = 0
    if force_battery or (annual_km * y > 160000) or (y > 8):
        h_bat = battery_cost
    
    h_total = (hybrid_car_price - h_resale) + ((annual_km * y / 21.0) * gas_price) + (11920 * y) + h_bat
    
    chart_data_rows.append({
        "持有年份": y, # 🔥 關鍵修正：這裡改成純數字 (Integer)，不要加中文
        "汽油版累積花費": int(g_total),
        "油電版累積花費": int(h_total)
    })

chart_df = pd.DataFrame(chart_data_rows)

# --- 單點計算 ---
gas_resale_final = get_resale_value(gas_car_price, years_to_keep, 'gas')
hybrid_resale_final = get_resale_value(hybrid_car_price, years_to_keep, 'hybrid')
total_km = annual_km * years_to_keep
battery_risk_cost = 0
battery_status_msg = "✅ 系統檢測正常"
if force_battery or total_km > 160000 or years_to_keep > 8:
    battery_risk_cost = battery_cost
    battery_status_msg = "⚠️ 風險預警：已計入電池更換"

tco_gas = (gas_car_price - gas_resale_final) + ((total_km / 12.0) * gas_price) + (11920 * years_to_keep)
tco_hybrid = (hybrid_car_price - hybrid_resale_final) + ((total_km / 21.0) * gas_price) + (11920 * years_to_keep) + battery_risk_cost
diff = tco_gas - tco_hybrid

# --- PDF 引擎 ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    font_path = "TaipeiSans.ttf"
    if not os.path.exists(font_path): return None
    try:
        pdf.add_font("TaipeiSans", fname=font_path)
        pdf.set_font("TaipeiSans", size=16)
        pdf.cell(0, 10, "Toyota Corolla Cross TCO 分析報告", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(5)
        pdf.set_font("TaipeiSans", size=10)
        pdf.cell(0, 10, f"參數：持有 {years_to_keep} 年 / 每年 {annual_km:,} km", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("TaipeiSans", size=12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(95, 10, "項目", border=1, align='C', fill=True)
        pdf.cell(47, 10, "汽油版", border=1, align='C', fill=True)
        pdf.cell(47, 10, "油電版", border=1, new_x="LMARGIN", new_y="NEXT", align='C', fill=True)

        def add_row(name, val1, val2):
            pdf.cell(95, 10, str(name), border=1)
            pdf.cell(47, 10, f"${int(val1):,}", border=1, align='R')
            pdf.cell(47, 10, f"${int(val2):,}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')

        add_row("車價折舊損失", gas_car_price - gas_resale_final, hybrid_car_price - hybrid_resale_final)
        add_row("總油錢支出", (total_km / 12.0) * gas_price, (total_km / 21.0) * gas_price)
        add_row("稅金總額", 11920 * years_to_keep, 11920 * years_to_keep)
        add_row("大電池風險", 0, battery_risk_cost)
        
        pdf.cell(95, 12, "【總持有成本 TCO】", border=1)
        pdf.cell(47, 12, f"${int(tco_gas):,}", border=1, align='R')
        pdf.cell(47, 12, f"${int(tco_hybrid):,}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')
        
        pdf.ln(5)
        pdf.set_font("TaipeiSans", size=14)
        if diff > 0:
            pdf.cell(0, 10, f"🏆 建議：【油電版】 (省 ${int(diff):,})", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 10, f"🏆 建議：【汽油版】 (省 ${int(abs(diff)):,})", new_x="LMARGIN", new_y="NEXT")

        # 災情表 (略縮減以防 PDF 跑版)
        pdf.ln(10)
        pdf.set_fill_color(255, 240, 240)
        pdf.cell(0, 10, "⚠️ 重點災情檢查表 (驗車必看)", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("TaipeiSans", size=11)
        pdf.ln(3)
        issues = ["1. 車頂架漏水 (A/C柱水痕)", "2. 避震器過軟 (暈車)", "3. 車機死機/訊號差", "4. 油電電池濾網清潔", "5. 煞車總泵滋滋聲", "6. CVT低速頓挫"]
        for i in issues: pdf.cell(0, 8, i, new_x="LMARGIN", new_y="NEXT")
        
        return bytes(pdf.output())
    except: return None

# --- 顯示網頁 ---
st.subheader("📈 成本累積圖 (越上面的線 = 越花錢)")
st.caption("X軸=持有年份，Y軸=累積噴掉的錢。兩線交叉點就是回本的時候。")

st.line_chart(
    chart_df,
    x="持有年份",
    y=["汽油版累積花費", "油電版累積花費"],
    color=["#FF4B4B", "#0052CC"]
)

col1, col2 = st.columns(2)
with col1: st.metric("汽油版總花費", f"${int(tco_gas):,}")
with col2: st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")

if diff > 0: st.success(f"🏆 結論：【油電版】比較省！省下 **${int(diff):,}**")
else: st.error(f"🏆 結論：【汽油版】比較省！省下 **${int(abs(diff)):,}**")

st.markdown("---")
# PDF 下載區
pdf_bytes = create_pdf()
if pdf_bytes:
    st.download_button("👉 下載完整 PDF 報告", pdf_bytes, "CC_Aero_Report.pdf", "application/pdf")

st.markdown("---")
# 假門測試
st.markdown("#### 👨‍🔧 想像檢查飛機一樣檢查二手車？")
col_a, col_b = st.columns([3, 1])
with col_a: st.markdown("👉 **《航太級 CC 驗車圖文手冊》 (Coming Soon)**")
with col_b:
    if st.button("🔥 搶先預約"):
        st.toast("🙏 收到預約！手冊最終校對中。", icon="✈️")
