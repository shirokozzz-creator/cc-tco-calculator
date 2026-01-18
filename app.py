import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import time
import math
import altair as alt

# --- 頁面設定 ---
st.set_page_config(page_title="航太級 TCO 精算機", page_icon="✈️")
st.title("✈️ 航太工程師的 CC 購車精算機")

# --- 頂部狀態列 ---
st.markdown(
    """
    <div style="display: flex; gap: 10px;">
        <img src="https://img.shields.io/badge/Data-Real_Auction_Verified-0052CC?style=flat-square" alt="Data">
        <img src="https://img.shields.io/badge/Chart-Logic_Fixed-success?style=flat-square" alt="Fixed">
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

st.caption("🚀 系統更新：修正圖表第0年定義誤差，呈現真實「累積淨損失」曲線。")

# --- 側邊欄輸入 ---
st.sidebar.header("1. 設定您的入手價格")
st.sidebar.info("💡 預設價差約 10-12 萬")
gas_car_price = st.sidebar.number_input("⛽ 汽油版 - 入手價", value=760000, step=10000)
hybrid_car_price = st.sidebar.number_input("⚡ 油電版 - 入手價", value=880000, step=10000)

st.sidebar.header("2. 用車習慣 (飛行計畫)")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 3000, 60000, 15000) 
years_to_keep = st.sidebar.slider("預計持有幾年", 1, 15, 10)
gas_price = st.sidebar.number_input("目前油價", value=31.0)

st.sidebar.header("3. 維修參數 (飛安係數)")
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)
force_battery = st.sidebar.checkbox("⚠️ 強制列入電池更換費", value=False)

# --- [核心] 大數據折舊模型 ---
def get_resale_value(initial_price, year, car_type):
    # 落地折舊參數 (根據 2026 拍賣場數據)
    if car_type == 'gas':
        k = 0.096
        initial_drop = 0.82 # 汽油版第一年剩 82%
    else:
        k = 0.104
        initial_drop = 0.80 # 油電版第一年剩 80%

    if year == 0:
        # 第0年(落地當下)的殘值 = 原價 * 落地折數
        # 這樣計算第0年的損失才不會是0，而是「落地折舊費」
        return initial_price * initial_drop
    elif year == 1:
        return initial_price * initial_drop
    else:
        p1 = initial_price * initial_drop
        return p1 * math.exp(-k * (year - 1))

# --- 數據計算 & 尋找黃金交叉點 ---
chart_data_rows = []
cross_point = None 
previous_diff = None 

# 從第0年開始算，到第12年
for y in range(0, 13): 
    # 計算該年份的殘值
    g_resale = get_resale_value(gas_car_price, y, 'gas')
    h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
    
    # 計算累積花費 (TCO) = 折舊損失 + 油錢 + 稅金 + 維修
    # 第0年：雖然里程是0，但已經產生「落地折舊損失」
    
    # 汽油版累積成本
    g_depreciation = gas_car_price - g_resale
    g_fuel = (annual_km * y / 12.0) * gas_price
    g_tax = 11920 * y
    g_total = g_depreciation + g_fuel + g_tax
    
    # 油電版累積成本
    h_depreciation = hybrid_car_price - h_resale
    h_fuel = (annual_km * y / 21.0) * gas_price
    h_tax = 11920 * y
    
    h_bat = 0
    # 邏輯：超過8年或16萬公里才計入電池
    if force_battery or (annual_km * y > 160000) or (y > 8):
        h_bat = battery_cost
        
    h_total = h_depreciation + h_fuel + h_tax + h_bat

    chart_data_rows.append({"年份": y, "車型": "汽油版", "累積花費": int(g_total)})
    chart_data_rows.append({"年份": y, "車型": "油電版", "累積花費": int(h_total)})

    # --- 計算交叉點邏輯 (線性插值) ---
    current_diff = g_total - h_total
    
    if y > 0 and previous_diff is not None:
        if previous_diff < 0 and current_diff >= 0:
            fraction = abs(previous_diff) / (abs(previous_diff) + current_diff)
            exact_year = (y - 1) + fraction
            prev_cost = chart_data_rows[-4]["累積花費"] 
            curr_cost = g_total
            exact_cost = prev_cost + (curr_cost - prev_cost) * fraction
            
            cross_point = {
                "年份": exact_year,
                "花費": exact_cost,
                "標籤": f"★ 黃金交叉：第 {exact_year:.1f} 年"
            }
            
    previous_diff = current_diff

chart_df = pd.DataFrame(chart_data_rows)

# --- 單點計算 (PDF與數據用) ---
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
        pdf.cell(0, 10, f"參數：持有 {years_to_keep} 年 / 每年 {annual_km:,} km", new_x="LMARGIN", new_y="NEXT", align='C')
        
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
        
        if cross_point:
             pdf.cell(0, 10, f"⚡ 回本時間點：{cross_point['標籤']}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(5)
        pdf.set_fill_color(255, 240, 240)
        pdf.cell(0, 10, "⚠️ 重點災情檢查表 (驗車必看)", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("TaipeiSans", size=11)
        pdf.ln(3)
        issues = ["1. 車頂架漏水 (A/C柱水痕)", "2. 避震器過軟 (暈車)", "3. 車機死機/訊號差", "4. 油電電池濾網清潔", "5. 煞車總泵滋滋聲", "6. CVT低速頓挫"]
        for i in issues: pdf.cell(0, 8, i, new_x="LMARGIN", new_y="NEXT")
        
        return bytes(pdf.output())
    except: return None

# --- 顯示網頁 ---
st.subheader("📈 成本累積圖 (含黃金交叉標記)")
st.caption("紅線=汽油，藍線=油電。我們幫您算出了精確的回本時間點。")

# 🔥 Altair 圖表 (修正版)
base = alt.Chart(chart_df).encode(
    x=alt.X('年份', axis=alt.Axis(title='持有年份', tickMinStep=1)),
    y=alt.Y('累積花費', axis=alt.Axis(title='累積總損失 (NTD)')),
    color=alt.Color('車型', scale=alt.Scale(domain=['汽油版', '油電版'], range=['#FF4B4B', '#0052CC']))
)
lines = base.mark_line(strokeWidth=3)

if cross_point:
    cross_df = pd.DataFrame([cross_point])
    points = alt.Chart(cross_df).mark_point(
        color='red', size=200, filled=True, shape='diamond'
    ).encode(x='年份', y='花費')
    
    text = alt.Chart(cross_df).mark_text(
        align='left', baseline='bottom', dx=10, dy=-10, fontSize=16, fontWeight='bold', color='red'
    ).encode(x='年份', y='花費', text='標籤')
    
    final_chart = (lines + points + text).interactive()
    st.success(f"🎯 **數據發現：** 兩車成本將在 **第 {cross_point['年份']:.1f} 年** 黃金交叉！此後油電版開始倒賺。")
else:
    final_chart = lines.interactive()
    st.warning("⚠️ 在目前的里程參數下，油電版可能需要開超過 12 年才能回本 (或無法回本)。")

st.altair_chart(final_chart, use_container_width=True)

# 數據面板
col1, col2 = st.columns(2)
with col1: st.metric("汽油版總花費", f"${int(tco_gas):,}")
with col2: st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")

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
