import streamlit as st
import pandas as pd
import os
import math
import altair as alt
from datetime import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="航太級 TCO 精算機", page_icon="✈️")
st.title("✈️ 航太工程師的 CC 購車精算機 (V23 修訂版)")

# --- 初始化 Session State (記憶解鎖狀態) ---
if 'unlocked' not in st.session_state:
    st.session_state.unlocked = False

# --- 名單儲存功能 ---
def save_lead(email):
    file_name = "leads.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding='utf-8') as f:
            f.write("Time,Email\n")
    with open(file_name, "a", encoding='utf-8') as f:
        f.write(f"{timestamp},{email}\n")

# --- 側邊欄輸入區 ---
st.sidebar.header("1. 設定您的入手價格")
gas_car_price = st.sidebar.number_input("⛽ 汽油版 - 入手價", value=760000, step=10000)
hybrid_car_price = st.sidebar.number_input("⚡ 油電版 - 入手價", value=880000, step=10000)

st.sidebar.header("2. 用車習慣")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 3000, 60000, 15000)
years_to_keep = st.sidebar.slider("預計持有幾年", 1, 15, 10)
gas_price = st.sidebar.number_input("目前油價", value=31.0)

st.sidebar.header("3. 維修參數")
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)
force_battery = st.sidebar.checkbox("⚠️ 強制列入電池更換費", value=False)

# --- [核心] 航太級折舊模型 ---
def get_resale_value(initial_price, year, car_type):
    if car_type == 'gas':
        k = 0.096
        initial_drop = 0.82
    else:
        k = 0.104
        initial_drop = 0.80

    if year == 0: return initial_price * initial_drop
    elif year == 1: return initial_price * initial_drop
    else: return (initial_price * initial_drop) * math.exp(-k * (year - 1))

# --- 計算邏輯 ---
chart_data_rows = []
cross_point = None
prev_diff = None

for y in range(0, 13):
    g_resale = get_resale_value(gas_car_price, y, 'gas')
    h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
    g_total = (gas_car_price - g_resale) + ((annual_km * y / 12.0) * gas_price) + (11920 * y)
    h_bat = battery_cost if (force_battery or (annual_km * y > 160000) or (y > 8)) else 0
    h_total = (hybrid_car_price - h_resale) + ((annual_km * y / 21.0) * gas_price) + (11920 * y) + h_bat

    chart_data_rows.append({"年份": y, "車型": "汽油版", "累積花費": int(g_total)})
    chart_data_rows.append({"年份": y, "車型": "油電版", "累積花費": int(h_total)})

    curr_diff = g_total - h_total
    if y > 0 and prev_diff is not None:
        if prev_diff < 0 and curr_diff >= 0:
            frac = abs(prev_diff) / (abs(prev_diff) + curr_diff)
            exact_year = (y - 1) + frac
            cross_point = {"年份": exact_year, "花費": g_total, "標籤": f"★ 第 {exact_year:.1f} 年回本"}
    prev_diff = curr_diff

chart_df = pd.DataFrame(chart_data_rows)

gas_resale_final = get_resale_value(gas_car_price, years_to_keep, 'gas')
hybrid_resale_final = get_resale_value(hybrid_car_price, years_to_keep, 'hybrid')
total_km = annual_km * years_to_keep
battery_risk_cost = battery_cost if (force_battery or total_km > 160000 or years_to_keep > 8) else 0

tco_gas = (gas_car_price - gas_resale_final) + ((total_km / 12.0) * gas_price) + (11920 * years_to_keep)
tco_hybrid = (hybrid_car_price - hybrid_resale_final) + ((total_km / 21.0) * gas_price) + (11920 * years_to_keep) + battery_risk_cost
diff = tco_gas - tco_hybrid

# ================= 顯示層 =================

# 1. 趨勢圖
st.subheader("📈 成本累積圖 (TCO)")
st.caption("紅線=汽油，藍線=油電。運用指數衰退模型預測。")

base = alt.Chart(chart_df).encode(
    x=alt.X('年份', axis=alt.Axis(title='持有年份', tickMinStep=1)),
    y=alt.Y('累積花費', axis=alt.Axis(title='累積總損失 (NTD)')),
    color=alt.Color('車型', scale=alt.Scale(domain=['汽油版', '油電版'], range=['#FF4B4B', '#0052CC']))
)
lines = base.mark_line(strokeWidth=3)

if cross_point:
    cross_df = pd.DataFrame([cross_point])
    points = alt.Chart(cross_df).mark_point(color='red', size=200, filled=True).encode(x='年份', y='花費')
    st.altair_chart((lines + points).interactive(), use_container_width=True)
    st.success(f"🎯 **精算結果**：若您打算開超過 **{cross_point['年份']:.1f} 年**，買油電版才划算！")
else:
    st.altair_chart(lines.interactive(), use_container_width=True)

col1, col2 = st.columns(2)
with col1: st.metric("汽油版總花費", f"${int(tco_gas):,}")
with col2: st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")

st.markdown("---")

# 2. 鎖碼區 (名單收集器)
st.subheader("📉 獨家揭露：拍賣場真實成交行情 (413筆)")

# 預覽表格
preview_data = pd.DataFrame([
    {"年份": 2025, "動力": "油電", "成交價": "71.6萬", "備註": "極新車"},
    {"年份": 2024, "動力": "汽油", "成交價": "57.6萬", "備註": "折舊高"},
    {"年份": "...", "動力": "...", "成交價": "🔒", "備註": "VIP限定"},
])
st.table(preview_data)

if not st.session_state.unlocked:
    st.warning("🔒 此為 VIP 限定資料")
    st.markdown("想要查看完整的 **Google Sheets 行情表**？")
    # 這裡的文字已經修改，移除了「代拍」的說法
    st.markdown("包含：**2026 Q1 最新拍賣價**、**預估車行收購成本**、**完整行情分析報告**")

    with st.form("unlock_form"):
        email_input = st.text_input("您的 Email", placeholder="example@gmail.com")
        submit_btn = st.form_submit_button("🔓 解鎖並查看完整報表", type="primary")
        if submit_btn:
            if "@" in email_input:
                st.session_state.unlocked = True
                save_lead(email_input)
                st.rerun()
            else:
                st.error("請輸入有效的 Email 格式")
else:
    st.success("✅ 已解鎖！")
    st.markdown("### 👇 點擊下方按鈕，開啟完整行情表：")
    # 您的 Google Sheets 連結
    google_sheet_url = "https://docs.google.com/spreadsheets/d/15q0bWKD8PTa01uDZjOQ_fOt5dOTUh0A1D_SrviYP8Lc/edit?gid=0#gid=0"
    st.link_button("📊 開啟完整 Google Sheets 行情表", google_sheet_url, type="primary")
    st.info("💡 建議將表格加入書籤，資料將不定期更新。")

st.markdown("---")
st.caption("Designed by Aerospace Engineer. Powered by Python & Streamlit.")
