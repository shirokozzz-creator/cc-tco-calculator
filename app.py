import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64

# --- 頁面設定 ---
st.set_page_config(page_title="CC TCO 精算機 (災情資料庫版)", page_icon="🚙")
st.title("🚙 CC 油電 vs. 汽油：TCO 分析報告")

# --- 流量計數器 (更換為穩定版) ---
# 使用 hits.seeyoufarm.com，這是 GitHub 開發者最常用的，不會被輕易擋掉
# 我已經把您的網址填入 url 參數中
st.markdown(
    """
    <div style="display: flex; justify-content: center;">
        <img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fcc-tco-calculator-nyscfmvgcj3mfh68rtqpgh.streamlit.app&count_bg=%2322C55E&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=👀+累積訪客&edge_flat=true" alt="Visit Counter">
    </div>
    """,
    unsafe_allow_html=True
)

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

# --- 核心計算引擎 ---
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

# 統一變數名稱
tax_total = 11920 * years_to_keep
tax_gas = tax_total
tax_hybrid = tax_total

battery_risk_cost = 0
if total_km > 160000 or years_to_keep > 8:
    battery_risk_cost = battery_cost

tco_gas = (gas_car_price - gas_resale_value) + gas_fuel_cost + tax_gas
tco_hybrid = (hybrid_car_price - hybrid_resale_value) + hybrid_fuel_cost + tax_hybrid + battery_risk_cost
diff = tco_gas - tco_hybrid

# --- PDF 產生引擎 ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    
    try:
        pdf.add_font('TaipeiSans', '', 'TaipeiSans.ttf', uni=True)
        pdf.set_font('TaipeiSans', '', 16)
    except:
        st.error("❌ 系統找不到字型檔 (TaipeiSans.ttf)。請確認 GitHub 是否有上傳。")
        return None

    pdf.cell(0, 10, 'Toyota Corolla Cross TCO 分析報告', ln=True, align='C')
    pdf.ln(10)

    pdf.set_font('TaipeiSans', '', 12)
    pdf.cell(0, 10, f'分析參數：持有 {years_to_keep} 年 / 每年 {annual_km:,} 公里 / 油價 {gas_price} 元', ln=True)
    pdf.ln(5)

    pdf.set_fill_color(240, 240, 240)
    pdf.cell(95, 10, '項目', 1, 0, 'C', 1)
    pdf.cell(47, 10, '汽油版', 1, 0, 'C', 1)
    pdf.cell(47, 10, '油電版', 1, 1, 'C', 1)

    def add_row(name, val1, val2):
        pdf.cell(95, 10, name, 1)
        pdf.cell(47, 10, f"${int(val1):,}", 1, 0, 'R')
        pdf.cell(47, 10, f"${int(val2):,}", 1, 1, 'R')

    add_row("車價折舊損失 (買-賣)", gas_car_price - gas_resale_value, hybrid_car_price - hybrid_resale_value)
    add_row("總油錢支出", gas_fuel_cost, hybrid_fuel_cost)
    add_row("稅金總額", tax_gas, tax_hybrid)
    add_row("大電池風險", 0, battery_risk_cost)
    
    pdf.cell(95, 12, "【總持有成本 TCO】", 1)
    pdf.cell(47, 12, f"${int(tco_gas):,}", 1, 0, 'R')
    pdf.cell(47, 12, f"${int(tco_hybrid):,}", 1, 1, 'R')
    pdf.ln(10)

    pdf.set_font('TaipeiSans', '', 14)
    if diff > 0:
        pdf.cell(0, 10, f"🏆 建議購買：【油電版】 (省下 ${int(diff):,})", ln=True)
    else:
        pdf.cell(0, 10, f"🏆 建議購買：【汽油版】 (省下 ${int(abs(diff)):,})", ln=True)

    pdf.ln(20)
    pdf.set_font('TaipeiSans', '', 10)
    pdf.cell(0, 10, "本報告由【中油工程師 TCO 計算機】自動生成。", ln=True, align='C')
    
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

st.markdown("---")

# 圖表區
st.subheader("💰 成本結構拆解")
cost_data = pd.DataFrame({
    "項目": ["折舊損失", "油錢", "稅金", "大電池"],
    "汽油版": [gas_car_price - gas_resale_value, gas_fuel_cost, tax_gas, 0],
    "油電版": [hybrid_car_price - hybrid_resale_value, hybrid_fuel_cost, tax_hybrid, battery_risk_cost]
})
st.bar_chart(cost_data.set_index("項目"))

# 殘值表格
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

# 災情資料庫
st.subheader("🔍 工程師的災情資料庫 (驗車必看)")
st.caption("買車前先看缺點，才知道能不能接受。")

with st.expander("🚨 全車系共同通病 (漏水/避震/車機) - 點擊展開"):
    st.markdown("""
    - **💦 車頂架漏水 (2020-2021前期款最慘)**
        - **症狀：** 檢查 A 柱、C 柱飾板是否有水痕，頂蓬是否有霉味。
        - **解法：** 原廠有召回更換防水墊片，買二手需確認是否已處理。
    - **🤢 避震器過軟 (暈車屬性)**
        - **症狀：** 原廠懸吊行程長且軟，後座乘客容易暈車。
        - **建議：** 試駕時請家人坐後座感受，很多人買回後需花 2-3 萬改裝避震。
    - **🖥️ 原廠車機 (Drive+ Connect) 災情**
        - **症狀：** 4G 訊號連不上、導航當機、倒車顯影延遲。
        - **建議：** 不要對原廠車機抱太大期望，改裝安卓機 (約 1.5 萬) 是常見解法。
    """)

tab1, tab2 = st.tabs(["⚡ 油電版要注意", "⛽ 汽油版要注意"])

with tab1:
    st.markdown("""
    - **🔋 大電池散熱網堵塞 (致命傷)**
        - **原因：** 進氣口在後座旁，容易吸入毛髮灰塵。
        - **後果：** 散熱不良導致電池過熱，壽命從 10 年縮短剩 5 年。
        - **檢查：** **必看後座旁濾網是否乾淨！**
    - **🔊 煞車總泵異音**
        - **症狀：** 踩放煞車有明顯「滋滋」電流聲。
        - **判斷：** 輕微是正常作動音，若聲音過大可能是總泵老化 (更換極貴)。
    """)

with tab2:
    st.markdown("""
    - **🐢 CVT 低速頓挫感**
        - **症狀：** 在時速 20-40 km/h 之間，收油再補油會有「拉扯感」。
        - **判斷：** 這是 Toyota Super CVT-i 的物理特性，非故障。
    - **📉 市區油耗落差**
        - **注意：** 純市區行駛油耗可能只有 9-10 km/L，要有心理準備。
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

# CTA 變現區
st.markdown("---")
st.markdown("#### 想知道更詳細的驗車眉角？")
st.markdown("👉 [**下載：CC 驗車懶人包 (PDF) - $199**](#)")
