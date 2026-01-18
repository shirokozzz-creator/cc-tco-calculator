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
        <img src="https://img.shields.io/badge/Scenario-Dual_Analysis-orange?style=flat-square" alt="Scenario">
        <img src="https://img.shields.io/badge/Status-Defects_List_Restored-success?style=flat-square" alt="Status">
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

st.caption("🚀 系統更新：新增「換電池 vs 免換電池」雙情境分析，並修復災情表顯示。")

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
st.sidebar.caption("註：圖表將同時顯示「換」與「不換」的兩條曲線供您參考。")

# --- [核心] 大數據折舊模型 ---
def get_resale_value(initial_price, year, car_type):
    # 落地折舊參數 (根據 2026 拍賣場數據)
    if car_type == 'gas':
        k = 0.096
        initial_drop = 0.82 
    else:
        k = 0.104
        initial_drop = 0.80 

    if year == 0:
        return initial_price * initial_drop
    elif year == 1:
        return initial_price * initial_drop
    else:
        p1 = initial_price * initial_drop
        return p1 * math.exp(-k * (year - 1))

# --- 數據計算 & 雙重情境分析 ---
chart_data_rows = []
cross_point_opt = None # 樂觀情境 (免換電池)
cross_point_pes = None # 悲觀情境 (換電池)
prev_diff_opt = None
prev_diff_pes = None

# 從第0年開始算，到第12年
for y in range(0, 13): 
    # 1. 基礎數據
    g_resale = get_resale_value(gas_car_price, y, 'gas')
    h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
    
    # 2. 汽油版累積成本 (基準線)
    g_dep = gas_car_price - g_resale
    g_fuel = (annual_km * y / 12.0) * gas_price
    g_tax = 11920 * y
    g_total = g_dep + g_fuel + g_tax
    
    # 3. 油電版 (基礎成本)
    h_dep = hybrid_car_price - h_resale
    h_fuel = (annual_km * y / 21.0) * gas_price
    h_tax = 11920 * y
    h_base = h_dep + h_fuel + h_tax
    
    # 情境 A: 免換電池 (Optimistic)
    h_total_opt = h_base
    
    # 情境 B: 換電池 (Pessimistic) - 假設第 8 年或 16萬公里發生
    # 為了圖表平滑，我們設定如果 y >= 8 就加上去，讓線跳起來
    h_bat_cost = 0
    if (annual_km * y > 160000) or (y >= 8):
        h_bat_cost = battery_cost
    h_total_pes = h_base + h_bat_cost

    # 寫入圖表數據
    chart_data_rows.append({"年份": y, "情境": "1. 汽油版", "累積花費": int(g_total)})
    chart_data_rows.append({"年份": y, "情境": "2. 油電 (免換電池)", "累積花費": int(h_total_opt)})
    chart_data_rows.append({"年份": y, "情境": "3. 油電 (需換電池)", "累積花費": int(h_total_pes)})

    # --- 計算交叉點 (雙軌制) ---
    # 1. 樂觀交叉
    curr_diff_opt = g_total - h_total_opt
    if y > 0 and prev_diff_opt is not None:
        if prev_diff_opt < 0 and curr_diff_opt >= 0:
            frac = abs(prev_diff_opt) / (abs(prev_diff_opt) + curr_diff_opt)
            cross_point_opt = (y - 1) + frac
    prev_diff_opt = curr_diff_opt
    
    # 2. 悲觀交叉
    curr_diff_pes = g_total - h_total_pes
    if y > 0 and prev_diff_pes is not None:
        if prev_diff_pes < 0 and curr_diff_pes >= 0:
            frac = abs(prev_diff_pes) / (abs(prev_diff_pes) + curr_diff_pes)
            cross_point_pes = (y - 1) + frac
    prev_diff_pes = curr_diff_pes

chart_df = pd.DataFrame(chart_data_rows)

# --- 單點計算 (用於 Metrics 與 PDF) ---
# 這裡我們計算持有年限(years_to_keep)當下的狀況
gas_final = (gas_car_price - get_resale_value(gas_car_price, years_to_keep, 'gas')) + \
            ((annual_km * years_to_keep / 12.0) * gas_price) + (11920 * years_to_keep)

h_base_final = (hybrid_car_price - get_resale_value(hybrid_car_price, years_to_keep, 'hybrid')) + \
               ((annual_km * years_to_keep / 21.0) * gas_price) + (11920 * years_to_keep)

# 判斷當下是否已經超過電池更換期
bat_is_due = (annual_km * years_to_keep > 160000) or (years_to_keep >= 8)
h_final_opt = h_base_final
h_final_pes = h_base_final + (battery_cost if bat_is_due else 0)

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
        pdf.cell(65, 10, "項目", border=1, align='C', fill=True)
        pdf.cell(40, 10, "汽油版", border=1, align='C', fill=True)
        pdf.cell(40, 10, "油電(免換)", border=1, align='C', fill=True)
        pdf.cell(40, 10, "油電(換電)", border=1, new_x="LMARGIN", new_y="NEXT", align='C', fill=True)

        def add_row_3(name, v1, v2, v3):
            pdf.cell(65, 10, str(name), border=1)
            pdf.cell(40, 10, f"${int(v1):,}", border=1, align='R')
            pdf.cell(40, 10, f"${int(v2):,}", border=1, align='R')
            pdf.cell(40, 10, f"${int(v3):,}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')

        # 這裡簡化顯示，直接秀總 TCO
        add_row_3("總持有成本 (TCO)", gas_final, h_final_opt, h_final_pes)
        
        pdf.ln(5)
        diff_opt = gas_final - h_final_opt
        diff_pes = gas_final - h_final_pes
        
        pdf.set_font("TaipeiSans", size=11)
        pdf.cell(0, 10, f"情境 A (運氣好)：油電省下 ${int(diff_opt):,}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"情境 B (需換電)：油電省下 ${int(diff_pes):,}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(10)
        pdf.set_fill_color(255, 240, 240)
        pdf.cell(0, 10, "⚠️ 重點災情檢查表 (驗車必看)", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        issues = ["1. 車頂架漏水 (A/C柱水痕)", "2. 避震器過軟 (暈車)", "3. 車機死機/訊號差", "4. 油電電池濾網清潔", "5. 煞車總泵滋滋聲", "6. CVT低速頓挫"]
        for i in issues: pdf.cell(0, 8, i, new_x="LMARGIN", new_y="NEXT")
        
        return bytes(pdf.output())
    except: return None

# --- 顯示網頁 ---
st.subheader("📈 雙情境成本分析圖")
st.caption("同時比較「換電池」與「不換電池」的成本差異。")

# 🔥 Altair 三線圖
base = alt.Chart(chart_df).encode(
    x=alt.X('年份', axis=alt.Axis(title='持有年份', tickMinStep=1)),
    y=alt.Y('累積花費', axis=alt.Axis(title='累積總損失 (NTD)')),
    color=alt.Color('情境', scale=alt.Scale(
        domain=['1. 汽油版', '2. 油電 (免換電池)', '3. 油電 (需換電池)'],
        range=['#FF4B4B', '#0052CC', '#FFA500'] # 紅、藍、橘
    )),
    strokeDash=alt.condition(
        alt.datum['情境'] == '3. 油電 (需換電池)',
        alt.value([5, 5]),  # 虛線
        alt.value([0])      # 實線
    )
)
lines = base.mark_line(strokeWidth=3).interactive()

st.altair_chart(lines, use_container_width=True)

# 交叉點情報
msg = ""
if cross_point_opt:
    msg += f"✅ **運氣好 (免換電池)：** 第 {cross_point_opt:.1f} 年回本\n\n"
if cross_point_pes:
    msg += f"⚠️ **運氣差 (換大電池)：** 第 {cross_point_pes:.1f} 年回本\n\n"
else:
    msg += f"⚠️ **運氣差 (換大電池)：** 目前參數下，持有期間內尚未回本"

st.success(msg)

# 數據面板 (三欄位)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("1. 汽油版 TCO", f"${int(gas_final):,}")
with col2:
    diff_opt = gas_final - h_final_opt
    st.metric("2. 油電 (免換)", f"${int(h_final_opt):,}", delta=f"省 ${int(diff_opt):,}")
with col3:
    diff_pes = gas_final - h_final_pes
    st.metric("3. 油電 (換電)", f"${int(h_final_pes):,}", delta=f"省 ${int(diff_pes):,}")

st.markdown("---")
# 🔥 [修復] 災情表回歸
st.subheader("🔍 航太工程師的災情資料庫")
with st.expander("🚨 機體與系統通病列表 (點擊展開)", expanded=True):
    st.markdown("""
    - **💦 機體結構 (漏水)**：20-21年式車頂架防水墊片瑕疵，**風險等級：高**。
    - **🤢 懸吊系統 (軟腳)**：原廠設定舒適取向，導致動態不穩，**建議方案：更換改裝避震**。
    - **🖥️ 航電系統 (車機)**：原廠 Drive+ Connect 穩定度不足，**建議方案：改裝安卓機**。
    - **⚡ 動力系統 (散熱)**：油電版大電池濾網需定期清潔，避免高溫導致壽命縮短。
    """)
st.markdown("---")

# PDF 下載區
pdf_bytes = create_pdf()
if pdf_bytes:
    st.download_button("👉 下載 PDF 報告 (含雙情境分析)", pdf_bytes, "CC_Aero_Report.pdf", "application/pdf")

st.markdown("---")
# 假門測試
st.markdown("#### 👨‍🔧 想像檢查飛機一樣檢查二手車？")
col_a, col_b = st.columns([3, 1])
with col_a: st.markdown("👉 **《航太級 CC 驗車圖文手冊》 (Coming Soon)**")
with col_b:
    if st.button("🔥 搶先預約"):
        st.toast("🙏 收到預約！手冊最終校對中。", icon="✈️")
