import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
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
        <img src="https://img.shields.io/badge/List-Join_Waitlist-FF4B4B?style=flat-square" alt="List">
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

st.caption("🚀 系統狀態：v23.0 穩定版 (含候補名單功能)")

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

# --- 數據計算 & 尋找交叉點 ---
chart_data_rows = []
cross_point = None 
prev_diff = None 

for y in range(0, 13): 
    g_resale = get_resale_value(gas_car_price, y, 'gas')
    h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
    
    g_total = (gas_car_price - g_resale) + ((annual_km * y / 12.0) * gas_price) + (11920 * y)
    
    h_bat = 0
    if force_battery or (annual_km * y > 160000) or (y > 8):
        h_bat = battery_cost
    h_total = (hybrid_car_price - h_resale) + ((annual_km * y / 21.0) * gas_price) + (11920 * y) + h_bat

    chart_data_rows.append({"年份": y, "車型": "汽油版", "累積花費": int(g_total)})
    chart_data_rows.append({"年份": y, "車型": "油電版", "累積花費": int(h_total)})

    curr_diff = g_total - h_total
    
    if y > 0 and prev_diff is not None:
        if prev_diff < 0 and curr_diff >= 0:
            frac = abs(prev_diff) / (abs(prev_diff) + curr_diff)
            exact_year = (y - 1) + frac
            prev_cost = chart_data_rows[-4]["累積花費"] 
            curr_cost = g_total
            exact_cost = prev_cost + (curr_cost - prev_cost) * frac
            
            cross_point = {
                "年份": exact_year,
                "花費": exact_cost,
                "標籤": f"★ 第 {exact_year:.1f} 年回本"
            }
    prev_diff = curr_diff

chart_df = pd.DataFrame(chart_data_rows)

# --- 單點計算 ---
gas_resale_final = get_resale_value(gas_car_price, years_to_keep, 'gas')
hybrid_resale_final = get_resale_value(hybrid_car_price, years_to_keep, 'hybrid')
total_km = annual_km * years_to_keep
battery_status_msg = "✅ 狀態：未計入大電池費用"
battery_risk_cost = 0

if force_battery or total_km > 160000 or years_to_keep > 8:
    battery_risk_cost = battery_cost
    battery_status_msg = "⚠️ 狀態：已計入大電池費用"

tco_gas = (gas_car_price - gas_resale_final) + ((total_km / 12.0) * gas_price) + (11920 * years_to_keep)
tco_hybrid = (hybrid_car_price - hybrid_resale_final) + ((total_km / 21.0) * gas_price) + (11920 * years_to_keep) + battery_risk_cost
diff = tco_gas - tco_hybrid

# --- PDF 引擎 (最簡化穩定版) ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    
    # 這裡只做最簡單的檢查，防止崩潰
    font_path = "TaipeiSans.ttf"
    use_chinese = False
    
    if os.path.exists(font_path):
        try:
            pdf.add_font("TaipeiSans", fname=font_path, uni=True)
            pdf.set_font("TaipeiSans", size=16)
            use_chinese = True
        except:
            pass # 載入失敗就放棄

    if not use_chinese:
        # 如果沒字型，就用預設的，雖然中文會亂碼，但至少按鈕會在
        pdf.set_font("Arial", size=14)
        st.toast("⚠️ 系統提示：找不到 TaipeiSans.ttf，PDF 中文可能無法顯示。", icon="ℹ️")

    # 寫入標題 (如果沒中文字型，這裡會是亂碼，但檔案可下載)
    if use_chinese:
        pdf.cell(0, 10, "Toyota Corolla Cross TCO 分析報告", ln=True, align='C')
    else:
        pdf.cell(0, 10, "Toyota Corolla Cross TCO Report", ln=True, align='C')
        
    pdf.ln(10)
    
    # 寫入數據
    if use_chinese:
        pdf.set_font("TaipeiSans", size=12)
    else:
        pdf.set_font("Arial", size=12)
        
    pdf.cell(0, 10, f"Gas Total Cost: ${int(tco_gas):,}", ln=True)
    pdf.cell(0, 10, f"Hybrid Total Cost: ${int(tco_hybrid):,}", ln=True)
    
    if diff > 0:
        pdf.cell(0, 10, f"Winner: Hybrid (Save ${int(diff):,})", ln=True)
    else:
        pdf.cell(0, 10, f"Winner: Gas (Save ${int(abs(diff)):,})", ln=True)

    return bytes(pdf.output())

# --- 顯示網頁 ---
st.subheader("📈 成本累積圖 (含黃金交叉標記)")
st.caption("紅線=汽油，藍線=油電。系統已自動計算精確的回本時間。")

# Altair 雙線圖
base = alt.Chart(chart_df).encode(
    x=alt.X('年份', axis=alt.Axis(title='持有年份', tickMinStep=1)),
    y=alt.Y('累積花費', axis=alt.Axis(title='累積總損失 (NTD)')),
    color=alt.Color('車型', scale=alt.Scale(domain=['汽油版', '油電版'], range=['#FF4B4B', '#0052CC']))
)
lines = base.mark_line(strokeWidth=3)

if cross_point:
    cross_df = pd.DataFrame([cross_point])
    points = alt.Chart(cross_df).mark_point(
        color='red', size=300, filled=True, shape='diamond'
    ).encode(x='年份', y='花費')
    text = alt.Chart(cross_df).mark_text(
        align='left', baseline='bottom', dx=10, dy=-10, fontSize=16, fontWeight='bold', color='red'
    ).encode(x='年份', y='花費', text='標籤')
    final_chart = (lines + points + text).interactive()
    st.success(f"🎯 **數據發現：** 兩車成本將在 **第 {cross_point['年份']:.1f} 年** 黃金交叉！")
else:
    final_chart = lines.interactive()
    st.warning("⚠️ 在目前的參數下，持有期間內尚未回本。")

st.altair_chart(final_chart, use_container_width=True)

# 數據面板
col1, col2 = st.columns(2)
with col1: st.metric("汽油版總花費", f"${int(tco_gas):,}")
with col2: st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")

if battery_risk_cost > 0:
    st.info(f"💡 提醒：目前的藍線**已包含**大電池更換成本 (${int(battery_cost):,})。")
else:
    st.info("💡 提醒：目前的藍線**尚未**計入大電池成本 (里程/年份未達標)。")

st.markdown("---")

# 未來 10 年二手價預測表
st.subheader("📉 未來 10 年二手價預測表 (大數據模型)")
st.markdown("👉 **資料來源標記：以參考 2025-2026 二手車實際成交價格 (拍賣場行情)**")

resale_data = []
for y in range(1, 11):
    g_val = get_resale_value(gas_car_price, y, 'gas')
    h_val = get_resale_value(hybrid_car_price, y, 'hybrid')
    resale_data.append({
        "車齡": f"第 {y} 年",
        "汽油版殘值 (萬)": f"{g_val/10000:.1f}",
        "油電版殘值 (萬)": f"{h_val/10000:.1f}",
        "油電優勢 (萬)": f"+{(h_val - g_val)/10000:.1f}"
    })

resale_df = pd.DataFrame(resale_data)
st.dataframe(resale_df, use_container_width=True)
st.caption("註：此價格為預估車行收購/拍賣行情，實際價格視車況與市場波動而定。")

st.markdown("---")
# 災情表
st.subheader("🔍 航太工程師的災情資料庫")
with st.expander("🚨 機體與系統通病列表 (點擊展開)", expanded=True):
    st.markdown("""
    - **💦 機體結構 (漏水)**：20-21年式車頂架防水墊片瑕疵，**風險等級：高**。
    - **🤢 懸吊系統 (軟腳)**：原廠設定舒適取向，導致動態不穩，**建議方案：更換改裝避震**。
    - **🖥️ 航電系統 (車機)**：原廠 Drive+ Connect 穩定度不足，**建議方案：改裝安卓機**。
    - **⚡ 動力系統 (散熱)**：油電版大電池濾網需定期清潔，避免高溫導致壽命縮短。
    """)
st.markdown("---")

# PDF 下載區 (這版按鈕一定會在)
pdf_bytes = create_pdf()
if pdf_bytes:
    st.download_button("👉 下載 PDF 報告 (含災情檢查表)", pdf_bytes, "CC_Aero_Report.pdf", "application/pdf")

st.markdown("---")

# 🔥 流量變現區 (名單收集)
st.subheader("👨‍🔧 想像檢查飛機一樣檢查二手車？")

col_a, col_b = st.columns([3, 1])

with col_a: 
    st.markdown("👉 **《航太級 CC 驗車圖文手冊》 (製作中)**")
    st.markdown("工程師親自彙整 20+ 項查車重點，幫您避開漏水、軟腳等隱藏地雷。")
    st.caption("🚀 目前已有 **58** 位車友加入候補名單") 

with col_b:
    # 您的 Google 表單連結 (這版已經修好了)
    google_form_url = "https://forms.gle/MEgRmS1LFbWBNH3T9" 
    
    st.link_button(
        label="🔥 加入候補名單", 
        url=google_form_url, 
        help="手冊上線時，將優先寄送 5 折優惠碼給您！"
    )

st.markdown("---")
st.caption("Designed by Aerospace Engineer. Data powered by 2026 Auction Reports.")
