import streamlit as st
import pandas as pd
import os
import math
import altair as alt
from datetime import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="Toyota 全車系 TCO 精算機", page_icon="🚗", layout="wide")

# ==========================================
# 🧠 數據中樞 (三台車的預設參數)
# ==========================================
car_db = {
    "Corolla Cross": {
        "gas_price": 760000, "hybrid_price": 880000, "battery": 49000,
        "advice_gas": "適合年跑1萬公里以下，首選 2024 汽油版，租賃退役CP值最高。",
        "advice_hybrid": "適合通勤族，首選 2022 年式，低於 45 萬通常是營業車。",
    },
    "RAV4": {
        "gas_price": 950000, "hybrid_price": 1150000, "battery": 65000,
        "advice_gas": "首選 2.0 旗艦。2.5 油電稅金一年多繳 5千，非高里程不划算。",
        "advice_hybrid": "注意 2019-2020 車頂架漏水通病。建議找 2021 後出廠車型。",
    },
    "Altis": {
        "gas_price": 650000, "hybrid_price": 780000, "battery": 49000,
        "advice_gas": "強烈建議買 2019.3 後的 TNGA 世代 (12代)。操控性大升級。",
        "advice_hybrid": "極高機率買到計程車退役。若不懂看車，建議買汽油版最安全。",
    }
}

# --- 初始化 Session State ---
if 'submitted' not in st.session_state: st.session_state.submitted = False

# --- 名單儲存功能 ---
def save_lead(email, model):
    file_name = "leads.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 如果檔案不存在，先建立標題列
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding='utf-8') as f:
            f.write("Time,Model,Email,Status\n") # 多加一個 Status 欄位
    # 寫入資料 (標記為 Waitlist)
    with open(file_name, "a", encoding='utf-8') as f:
        f.write(f"{timestamp},{model},{email},Waitlist\n")

# --- 側邊欄：設定與後台 ---
with st.sidebar:
    st.title("⚙️ 參數設定")
    
    # 1. 車型選擇
    selected_model = st.selectbox("請選擇車款", ["Corolla Cross", "RAV4", "Altis"])
    params = car_db[selected_model]
    
    st.markdown("---")
    # 2. 價格設定
    gas_car_price = st.number_input("⛽ 汽油版 - 入手價", value=params["gas_price"], step=10000)
    hybrid_car_price = st.number_input("⚡ 油電版 - 入手價", value=params["hybrid_price"], step=10000)
    
    # 3. 習慣設定
    annual_km = st.slider("年行駛里程 (km)", 5000, 60000, 15000) 
    years_to_keep = st.slider("預計持有年分", 1, 15, 10)
    gas_price = st.number_input("目前油價", value=31.0)
    
    # 4. 電池設定
    battery_cost = st.number_input("大電池更換預算", value=params["battery"])
    force_battery = st.checkbox("⚠️ 強制列入電池成本", value=False)
    
    # 5. 🕵️‍♂️ 管理員後台 (密碼 uc0088)
    with st.expander("🕵️‍♂️ 管理員專區"):
        if st.text_input("密碼", type="password") == "uc0088":
            if os.path.exists("leads.csv"):
                df_leads = pd.read_csv("leads.csv")
                st.dataframe(df_leads)
                st.download_button("📥 下載名單", df_leads.to_csv(index=False).encode('utf-8-sig'), "leads.csv")
            else:
                st.info("暫無名單")

# --- 主畫面標題 ---
st.title(f"✈️ 航太工程師的 {selected_model} 購車精算機")
st.caption("運用航太級 TCO 模型，幫您算出符合數學邏輯的最佳選擇。")

# ==========================================
# 📘 TCO 定義區塊
# ==========================================
with st.expander("❓ 什麼是 TCO？為什麼工程師買車都看這個？"):
    st.markdown("""
    ### 🚗 買車就像一座冰山，您只看到了水面上的「車價」...
    **公式 = (買入價 - 未來賣出價) + 累積油錢 + 累積稅金 + 維修風險**
    > **💡 數據魔人的結論：** 不要只看現在花多少錢買車，要看未來幾年您**總共會花掉多少錢**。
    """)
st.markdown("---")

# --- 核心運算邏輯 (保持不變) ---
def get_resale_value(initial_price, year, car_type):
    k = 0.096 if car_type == 'gas' else 0.104
    initial_drop = 0.82 if car_type == 'gas' else 0.80 
    if year <= 1: return initial_price * initial_drop
    else: return (initial_price * initial_drop) * math.exp(-k * (year - 1))

chart_data_rows = []
cross_point = None
prev_diff = None
prev_g_total = 0
calc_range = years_to_keep + 3
tax_gas = 17410 if selected_model == "RAV4" else 11920
tax_hybrid = 22410 if selected_model == "RAV4" else 11920

for y in range(0, calc_range):
    g_resale = get_resale_value(gas_car_price, y, 'gas')
    h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
    g_total = (gas_car_price - g_resale) + ((annual_km * y / 12.0) * gas_price) + (tax_gas * y)
    h_bat = battery_cost if (force_battery or (annual_km * y > 160000) or (y > 8)) else 0
    h_total = (hybrid_car_price - h_resale) + ((annual_km * y / 21.0) * gas_price) + (tax_hybrid * y) + h_bat
    chart_data_rows.append({"年份": y, "車型": "汽油版", "累積花費": int(g_total)})
    chart_data_rows.append({"年份": y, "車型": "油電版", "累積花費": int(h_total)})
    curr_diff = g_total - h_total
    if y > 0 and prev_diff is not None:
        if prev_diff < 0 and curr_diff >= 0:
            frac = abs(prev_diff) / (abs(prev_diff) + curr_diff)
            exact_year = (y - 1) + frac
            exact_cost = prev_g_total + (g_total - prev_g_total) * frac
            if exact_year <= years_to_keep:
                cross_point = {"年份": exact_year, "花費": exact_cost}
    prev_diff = curr_diff; prev_g_total = g_total

chart_df = pd.DataFrame(chart_data_rows)
total_km = annual_km * years_to_keep
is_battery_included = (force_battery or total_km > 160000 or years_to_keep > 8)
battery_risk_cost = battery_cost if is_battery_included else 0
g_resale_final = get_resale_value(gas_car_price, years_to_keep, 'gas')
h_resale_final = get_resale_value(hybrid_car_price, years_to_keep, 'hybrid')
tco_gas = (gas_car_price - g_resale_final) + ((total_km / 12.0) * gas_price) + (tax_gas * years_to_keep)
tco_hybrid = (hybrid_car_price - h_resale_final) + ((total_km / 21.0) * gas_price) + (tax_hybrid * years_to_keep) + battery_risk_cost
diff = tco_gas - tco_hybrid

# --- 1. 戰情室儀表板 ---
st.subheader("📊 決策戰情室")
if diff > 0:
    st.success(f"🏆 **油電版獲勝！** 持有 {years_to_keep} 年省下 **${int(diff):,}**")
else:
    st.info(f"🏆 **汽油版獲勝！** 持有 {years_to_keep} 年省下 **${int(abs(diff)):,}**")

col1, col2 = st.columns(2)
with col1:
    st.metric("⛽ 汽油版總成本", f"${int(tco_gas):,}", delta="無電池風險", delta_color="off")
with col2:
    if is_battery_included:
        st.metric("⚡ 油電版總成本", f"${int(tco_hybrid):,}", delta=f"⚠️ 含電池 ${int(battery_cost):,}", delta_color="inverse")
    else:
        st.metric("⚡ 油電版總成本", f"${int(tco_hybrid):,}", delta="✅ 保固內 (未計電池)", delta_color="normal")
st.markdown("---")

# --- 2. 互動趨勢圖 ---
st.subheader("📈 成本黃金交叉圖")
nearest = alt.selection_point(nearest=True, on='mouseover', fields=['年份'], empty=False)
base = alt.Chart(chart_df).encode(
    x=alt.X('年份', axis=alt.Axis(tickMinStep=1)), 
    y=alt.Y('累積花費'),
    color=alt.Color('車型', scale=alt.Scale(domain=['汽油版', '油電版'], range=['#FF4B4B', '#0052CC']))
)
lines = base.mark_line(strokeWidth=3)
selectors = base.mark_point().encode(opacity=alt.value(0)).add_params(nearest)
points = base.mark_point(filled=True, size=100).encode(opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
text = base.mark_text(align='left', dx=5, dy=-5).encode(text=alt.condition(nearest, '累積花費', alt.value(' ')), opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
rules = alt.Chart(chart_df).mark_rule(color='gray').encode(x='年份').transform_filter(nearest)
if cross_point:
    pt = pd.DataFrame([cross_point])
    cross_layer = alt.Chart(pt).mark_point(color='red', size=200, filled=True, shape='diamond').encode(x='年份', y='花費')
    st.altair_chart((lines+selectors+points+rules+text+cross_layer).interactive(), use_container_width=True)
else:
    st.altair_chart((lines+selectors+points+rules+text).interactive(), use_container_width=True)

# ==========================================
# 🛑 服務公告與候補區 (修改重點區塊)
# ==========================================
st.markdown("---")
st.subheader(f"📉 {selected_model} 真實拍賣成交行情")

# 1. 黃色警示區塊：告知額滿
st.warning("⚠️ **服務公告：目前諮詢量額滿，暫停即時報價**")

if not st.session_state.submitted:
    # 2. 說明文案：降低期待，但保留誘餌
    st.markdown(f"""
    感謝大家對 TCO 理念的支持！
    因工程師平日仍有國家單位公務，為了確保每一份報告的分析品質，
    我們目前 **暫停提供個別車輛的「即時鑑價」服務**。

    您現在留下的 Email 將自動加入 **「優先候補名單」**。
    待消化完畢後，我會優先將您的 **【{selected_model} 2026 Q1 獨家行情 + 避坑指南】** 寄給您。
    """)
    
    # 3. 候補表單
    with st.form("waitlist_form"):
        email_input = st.text_input("輸入 Email 加入候補名單：", placeholder="請輸入您的 Email")
        submitted = st.form_submit_button("加入優先候補名單")
        
        if submitted:
            if "@" in email_input:
                save_lead(email_input, selected_model)
                st.session_state.submitted = True
                st.session_state.user_email = email_input
                st.rerun()
            else:
                st.error("❌ 請輸入有效的 Email 格式")
else:
    # 4. 送出後的成功畫面
    st.success("✅ 已成功加入候補名單！")
    st.balloons()
    
    st.info(f"""
    您的 Email：**{st.session_state.user_email}** 已紀錄。
    
    一旦恢復服務或新的《工程師避雷懶人包》整理完成，
    我會第一時間寄送給您。請留意信箱。
    """)
    
    if st.button("🔄 重新輸入 Email"):
        st.session_state.submitted = False
        st.rerun()

st.markdown("---")
st.caption("Designed by Aerospace Engineer Brian | 專注於二手車數據分析")
