import streamlit as st
import pandas as pd
import os
import math
import altair as alt
from datetime import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="航太級 TCO 精算機", page_icon="✈️", layout="wide")
st.title("✈️ 航太工程師的 CC 購車精算機")

# --- 初始化 Session State ---
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

# --- 側邊欄 ---
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

# --- 核心折舊模型 ---
def get_resale_value(initial_price, year, car_type):
    if car_type == 'gas':
        k = 0.096; initial_drop = 0.82 
    else:
        k = 0.104; initial_drop = 0.80 

    if year == 0: return initial_price * initial_drop
    elif year == 1: return initial_price * initial_drop
    else: return (initial_price * initial_drop) * math.exp(-k * (year - 1))

# --- 計算邏輯 (V25 精準修正版) ---
chart_data_rows = []
cross_point = None 
prev_diff = None 
prev_g_total = 0 # 紀錄上一年的花費，用來做內插運算

# 計算範圍動態調整
calc_range = years_to_keep + 3 

for y in range(0, calc_range): 
    g_resale = get_resale_value(gas_car_price, y, 'gas')
    h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
    
    g_total = (gas_car_price - g_resale) + ((annual_km * y / 12.0) * gas_price) + (11920 * y)
    h_bat = battery_cost if (force_battery or (annual_km * y > 160000) or (y > 8)) else 0
    h_total = (hybrid_car_price - h_resale) + ((annual_km * y / 21.0) * gas_price) + (11920 * y) + h_bat

    chart_data_rows.append({"年份": y, "車型": "汽油版", "累積花費": int(g_total)})
    chart_data_rows.append({"年份": y, "車型": "油電版", "累積花費": int(h_total)})

    # 黃金交叉點計算 (使用線性內插法 Linear Interpolation)
    curr_diff = g_total - h_total
    if y > 0 and prev_diff is not None:
        if prev_diff < 0 and curr_diff >= 0: # 發現交叉 (負轉正)
            # 算出交叉點在 y-1 到 y 之間的比例 (fraction)
            frac = abs(prev_diff) / (abs(prev_diff) + curr_diff)
            exact_year = (y - 1) + frac
            
            # 關鍵修正：花費也要依比例計算，不能直接拿年底的 g_total
            exact_cost = prev_g_total + (g_total - prev_g_total) * frac
            
            if exact_year <= years_to_keep:
                cross_point = {"年份": exact_year, "花費": exact_cost, "標籤": f"★ 第 {exact_year:.1f} 年回本"}
    
    prev_diff = curr_diff
    prev_g_total = g_total # 更新上一年花費

chart_df = pd.DataFrame(chart_data_rows)

# TCO 總結
gas_resale_final = get_resale_value(gas_car_price, years_to_keep, 'gas')
hybrid_resale_final = get_resale_value(hybrid_car_price, years_to_keep, 'hybrid')
total_km = annual_km * years_to_keep
battery_risk_cost = battery_cost if (force_battery or total_km > 160000 or years_to_keep > 8) else 0
tco_gas = (gas_car_price - gas_resale_final) + ((total_km / 12.0) * gas_price) + (11920 * years_to_keep)
tco_hybrid = (hybrid_car_price - hybrid_resale_final) + ((total_km / 21.0) * gas_price) + (11920 * years_to_keep) + battery_risk_cost
diff = tco_gas - tco_hybrid

# ================= 顯示層 =================

# 1. 趨勢圖 (Chart 1)
st.subheader("📈 成本累積趨勢圖")
st.caption("紅線=汽油版，藍線=油電版。紅點為精確回本時間點。")

base = alt.Chart(chart_df).encode(
    x=alt.X('年份', axis=alt.Axis(title='持有年份', tickMinStep=1), scale=alt.Scale(domain=[0, years_to_keep + 1])),
    y=alt.Y('累積花費', axis=alt.Axis(title='累積總花費 (NTD)')),
    color=alt.Color('車型', scale=alt.Scale(domain=['汽油版', '油電版'], range=['#FF4B4B', '#0052CC']))
)

lines = base.mark_line(strokeWidth=3)

# 組合圖表
if cross_point:
    cross_df = pd.DataFrame([cross_point])
    points = alt.Chart(cross_df).mark_point(color='red', size=200, filled=True).encode(
        x='年份', 
        y='花費',
        tooltip=['年份', '花費']
    )
    final_chart = (lines + points).interactive()
    st.altair_chart(final_chart, use_container_width=True)
    st.success(f"🎯 **精算結果**：預計在 **第 {cross_point['年份']:.1f} 年** 油電版總成本會低於汽油版！")
else:
    st.altair_chart(lines.interactive(), use_container_width=True)

# 顯示數字
col1, col2 = st.columns(2)
with col1: st.metric("汽油版總成本", f"${int(tco_gas):,}")
with col2: st.metric("油電版總成本", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")

st.markdown("---")

# 2. 拍賣行情區
st.subheader("📉 2026 最新拍賣場成交行情 (413筆)")

preview_data = pd.DataFrame([
    {"年份": 2025, "動力": "油電", "成交價": "71.6萬", "備註": "極新車"},
    {"年份": 2024, "動力": "汽油", "成交價": "57.6萬", "備註": "折舊高"},
    {"年份": "...", "動力": "...", "成交價": "🔒", "備註": "VIP限定"},
])
st.table(preview_data)

if not st.session_state.unlocked:
    st.warning("🔒 這是 VIP 限定資料")
    st.markdown("這份 **Google Sheets 行情表** 完整收錄：")
    st.markdown("✅ **2026 Q1 最新拍賣成交價**")
    st.markdown("✅ **車行預估收購成本分析**")
    st.markdown("✅ **市場行情與價差分析**")
    
    with st.form("unlock_form"):
        email_input = st.text_input("請輸入 Email 查看完整報表", placeholder="example@gmail.com")
        submit_btn = st.form_submit_button("🔓 解鎖", type="primary")
        
        if submit_btn:
            if "@" in email_input:
                st.session_state.unlocked = True
                save_lead(email_input)
                st.rerun()
            else:
                st.error("Email 格式不正確")
else:
    st.success("✅ 已解鎖！")
    st.markdown("### 👇 點擊下方按鈕，開啟完整行情表：")
    
    # 您的 Google Sheets 連結
    google_sheet_url = "https://docs.google.com/spreadsheets/d/15q0bWKD8PTa01uDZjOQ_fOt5dOTUh0A1D_SrviYP8Lc/edit?gid=0#gid=0"
    
    st.link_button("📊 開啟 Google Sheets 行情表", google_sheet_url, type="primary")
    st.info("💡 建議將表格連結加入書籤，資料將不定期更新。")

st.markdown("---")
st.caption("Designed by Aerospace Engineer. Powered by Python.")
