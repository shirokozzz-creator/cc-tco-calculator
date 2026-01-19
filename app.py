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

# ==========================================
# 🕵️‍♂️ 管理員後台 (密碼 1234)
# ==========================================
with st.sidebar:
    st.markdown("---")
    with st.expander("🕵️‍♂️ 管理員專區"):
        admin_pwd = st.text_input("輸入密碼", type="password")
        if admin_pwd == "1234":
            st.success("✅ 登入成功")
            if os.path.exists("leads.csv"):
                df_leads = pd.read_csv("leads.csv")
                st.dataframe(df_leads, use_container_width=True)
                csv_data = df_leads.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載名單 (CSV)", csv_data, "leads.csv", "text/csv")
            else:
                st.warning("暫無名單")

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

# --- 核心折舊模型 ---
def get_resale_value(initial_price, year, car_type):
    if car_type == 'gas':
        k = 0.096; initial_drop = 0.82 
    else:
        k = 0.104; initial_drop = 0.80 

    if year == 0: return initial_price * initial_drop
    elif year == 1: return initial_price * initial_drop
    else: return (initial_price * initial_drop) * math.exp(-k * (year - 1))

# --- 計算邏輯 (含內插法) ---
chart_data_rows = []
cross_point = None 
prev_diff = None 
prev_g_total = 0 
calc_range = years_to_keep + 3 

for y in range(0, calc_range): 
    g_resale = get_resale_value(gas_car_price, y, 'gas')
    h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
    g_total = (gas_car_price - g_resale) + ((annual_km * y / 12.0) * gas_price) + (11920 * y)
    h_bat = battery_cost if (force_battery or (annual_km * y > 160000) or (y > 8)) else 0
    h_total = (hybrid_car_price - h_resale) + ((annual_km * y / 21.0) * gas_price) + (11920 * y) + h_bat

    chart_data_rows.append({"年份": y, "車型": "汽油版", "累積花費": int(g_total)})
    chart_data_rows.append({"年份": y, "車型": "油電版", "累積花費": int(h_total)})

    # 黃金交叉點
    curr_diff = g_total - h_total
    if y > 0 and prev_diff is not None:
        if prev_diff < 0 and curr_diff >= 0:
            frac = abs(prev_diff) / (abs(prev_diff) + curr_diff)
            exact_year = (y - 1) + frac
            exact_cost = prev_g_total + (g_total - prev_g_total) * frac
            if exact_year <= years_to_keep:
                cross_point = {"年份": exact_year, "花費": exact_cost}
    prev_diff = curr_diff
    prev_g_total = g_total

chart_df = pd.DataFrame(chart_data_rows)

# TCO 總結
gas_resale_final = get_resale_value(gas_car_price, years_to_keep, 'gas')
hybrid_resale_final = get_resale_value(hybrid_car_price, years_to_keep, 'hybrid')
total_km = annual_km * years_to_keep

# 判斷電池是否計入
is_battery_included = (force_battery or total_km > 160000 or years_to_keep > 8)
battery_risk_cost = battery_cost if is_battery_included else 0

tco_gas = (gas_car_price - gas_resale_final) + ((total_km / 12.0) * gas_price) + (11920 * years_to_keep)
tco_hybrid = (hybrid_car_price - hybrid_resale_final) + ((total_km / 21.0) * gas_price) + (11920 * years_to_keep) + battery_risk_cost
diff = tco_gas - tco_hybrid

# ================= 顯示層 =================

# 1. 戰情室儀表板
st.subheader("📊 購車決策戰情室")

# 勝負判定顯示
if diff > 0:
    st.success(f"🏆 **油電版獲勝！** 預計省下 **${int(diff):,}**")
else:
    st.info(f"🏆 **汽油版獲勝！** 預計省下 **${int(abs(diff)):,}**")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ⛽ 汽油版總成本")
    st.metric("Total Cost", f"${int(tco_gas):,}", delta="無大電池風險", delta_color="off")

with col2:
    st.markdown("### ⚡ 油電版總成本")
    # 電池狀態顯示
    if is_battery_included:
        bat_status = f"⚠️ 已計入大電池 (${int(battery_cost):,})"
        bat_color = "inverse" # 紅色
    else:
        bat_status = "✅ 未計入大電池 (保固內)"
        bat_color = "normal" # 綠色
        
    st.metric("Total Cost", f"${int(tco_hybrid):,}", delta=bat_status, delta_color=bat_color)

st.markdown("---")

# 2. 進階趨勢圖 (升級版)
st.subheader("📈 成本累積趨勢 (互動式)")
st.caption("滑鼠移動到線條上，可查看每年的具體金額。")

# 建立互動選取器
nearest = alt.selection_point(nearest=True, on='mouseover', fields=['年份'], empty=False)

# 基礎線條
base = alt.Chart(chart_df).encode(
    x=alt.X('年份', axis=alt.Axis(title='持有年份', tickMinStep=1)),
    y=alt.Y('累積花費', axis=alt.Axis(title='累積總花費 (NTD)')),
    color=alt.Color('車型', scale=alt.Scale(domain=['汽油版', '油電版'], range=['#FF4B4B', '#0052CC']))
)

# 繪製線條
lines = base.mark_line(strokeWidth=4)

# 繪製透明點 (為了讓滑鼠容易抓到)
selectors = base.mark_point().encode(
    opacity=alt.value(0),
).add_params(
    nearest
)

# 繪製選取時的圓點
points = base.mark_point(filled=True, size=100).encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)

# 繪製選取時的文字標籤
text = base.mark_text(align='left', dx=5, dy=-5).encode(
    text=alt.condition(nearest, '累積花費', alt.value(' ')),
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)

# 繪製選取時的垂直輔助線
rules = alt.Chart(chart_df).mark_rule(color='gray').encode(
    x='年份',
).transform_filter(
    nearest
)

# 黃金交叉點 (紅點)
if cross_point:
    cross_df = pd.DataFrame([cross_point])
    cross_layer = alt.Chart(cross_df).mark_point(color='red', size=300, shape='diamond', filled=True).encode(
        x='年份', y='花費', tooltip=['年份', '花費']
    )
    final_chart = (lines + selectors + points + rules + text + cross_layer).interactive()
    
    st.altair_chart(final_chart, use_container_width=True)
    st.write(f"📍 **黃金交叉點**：第 **{cross_point['年份']:.1f} 年**")
else:
    st.altair_chart((lines + selectors + points + rules + text).interactive(), use_container_width=True)

st.markdown("---")

# 3. 拍賣行情區
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
    google_sheet_url = "https://docs.google.com/spreadsheets/d/15q0bWKD8PTa01uDZjOQ_fOt5dOTUh0A1D_SrviYP8Lc/edit?gid=0#gid=0"
    st.link_button("📊 開啟 Google Sheets 行情表", google_sheet_url, type="primary")
    st.info("💡 建議將表格連結加入書籤，資料將不定期更新。")

st.markdown("---")
st.caption("Designed by Aerospace Engineer. Powered by Python.")
