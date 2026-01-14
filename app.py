import streamlit as st
import pandas as pd

# --- 頁面設定 ---
st.set_page_config(page_title="CC TCO 精算機 (自由輸入版)", page_icon="🚙")

st.title("🚙 CC 油電 vs. 汽油：客製化 TCO 分析")
st.markdown("### ✍️ 請直接輸入您的「入手價格」，AI 幫您算折舊與回本")

# --- 側邊欄：使用者輸入 ---
st.sidebar.header("1. 設定您的入手價格 (關鍵)")
st.sidebar.info("💡 不管是新車還是二手，請輸入您談到的最終價格")

# 改為完全自由輸入，預設值設為目前常見行情
gas_car_price = st.sidebar.number_input("⛽ 汽油版 - 入手價 (元)", value=760000, step=10000)
hybrid_car_price = st.sidebar.number_input("⚡ 油電版 - 入手價 (元)", value=880000, step=10000)

# 即時顯示價差
price_diff = hybrid_car_price - gas_car_price
if price_diff > 0:
    st.sidebar.write(f"👉 油電版貴了：**${price_diff:,}**")
else:
    st.sidebar.write(f"👉 汽油版貴了：**${abs(price_diff):,}** (罕見情況)")

st.sidebar.markdown("---")

st.sidebar.header("2. 用車習慣")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 3000, 50000, 15000) 
years_to_keep = st.sidebar.slider("預計持有幾年 (Max 10年)", 1, 10, 5)
gas_price = st.sidebar.number_input("目前油價 (95無鉛)", value=31.0)

st.sidebar.header("3. 維修與折舊參數")
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)
st.sidebar.caption("註：採用車商折舊公式 (首年8折, 之後-5%)")

# --- 核心計算引擎 ---

# 1. 定義折舊函數 (首年8折，之後每年5%)
def get_residual_rate(year):
    if year <= 0:
        return 1.0
    elif year == 1:
        return 0.80
    else:
        # 公式：0.80 - ( (年數 - 1) * 0.05 )
        rate = 0.80 - ((year - 1) * 0.05)
        return max(rate, 0.0)

# 2. 計算殘值 (Resale Value)
current_rate = get_residual_rate(years_to_keep)
gas_resale_value = gas_car_price * current_rate
hybrid_resale_value = hybrid_car_price * current_rate

# 3. 基礎 TCO 計算
total_km = annual_km * years_to_keep
gas_mpg = 12.0
hybrid_mpg = 21.0
tax_gas = 11920 * years_to_keep
tax_hybrid = 11920 * years_to_keep

# 油錢
gas_fuel_cost = (total_km / gas_mpg) * gas_price
hybrid_fuel_cost = (total_km / hybrid_mpg) * gas_price

# 4. 電池風險 (超過16萬公里 或 持有超過8年)
battery_risk_cost = 0
battery_msg = "✅ 安全範圍 (暫不計入電池成本)"
if total_km > 160000 or years_to_keep > 8:
    battery_risk_cost = battery_cost
    battery_msg = "⚠️ 預計需換大電池 (已計入成本)"

# 5. 總結算
# TCO = (買價 - 賣價) + 油錢 + 稅金 + 電池
tco_gas = (gas_car_price - gas_resale_value) + gas_fuel_cost + tax_gas
tco_hybrid = (hybrid_car_price - hybrid_resale_value) + hybrid_fuel_cost + tax_hybrid + battery_risk_cost

diff = tco_gas - tco_hybrid

# --- 結果顯示區 ---

st.header(f"📊 分析結果 ({years_to_keep}年 / {total_km:,}公里)")

col1, col2 = st.columns(2)
with col1:
    st.metric("汽油版總花費", f"${int(tco_gas):,}")
    st.caption(f"預估賣出價: ${int(gas_resale_value):,}")
with col2:
    st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}")
    st.caption(f"預估賣出價: ${int(hybrid_resale_value):,}")

st.markdown("---")

# 判決邏輯
if diff > 0:
    st.success(f"🏆 **油電版獲勝！**\n\n省下 **${int(diff):,}**\n(雖然入手貴 ${price_diff:,}，但油錢和二手價幫你賺回來了)")
else:
    st.error(f"🏆 **汽油版獲勝！**\n\n省下 **${int(abs(diff)):,}**\n(因為你里程太少，或者汽油版入手的價格實在太便宜了)")

st.info(f"💡 電池狀態：{battery_msg}")

# 詳細圖表
st.subheader("💰 錢花去哪了？ (成本結構)")
cost_data = pd.DataFrame({
    "項目": ["折舊損失 (買-賣)", "總油錢", "稅金", "大電池風險"],
    "汽油版": [gas_car_price - gas_resale_value, gas_fuel_cost, tax_gas, 0],
    "油電版": [hybrid_car_price - hybrid_resale_value, hybrid_fuel_cost, tax_hybrid, battery_risk_cost]
})
st.bar_chart(cost_data.set_index("項目"))

# 殘值走勢預覽
st.subheader("📉 未來 10 年殘值預測表")
st.caption(f"基於您輸入的入手價：汽油 ${gas_car_price:,} / 油電 ${hybrid_car_price:,}")

years_range = list(range(1, 11))
rates = [get_residual_rate(y) for y in years_range]
resale_df = pd.DataFrame({
    "年份": years_range,
    "折舊後剩餘價值 (%)": [f"{int(r*100)}%" for r in rates],
    "汽油版剩餘價值": [int(gas_car_price * r) for r in rates],
    "油電版剩餘價值": [int(hybrid_car_price * r) for r in rates]
})
st.dataframe(resale_df, use_container_width=True)

# CTA
st.markdown("---")
st.markdown("#### 想知道更詳細的驗車眉角？")
st.markdown("👉 [**下載：CC 驗車懶人包 (PDF) - $199**](#)")
