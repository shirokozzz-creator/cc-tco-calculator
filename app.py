import streamlit as st
import pandas as pd
import numpy as np

# --- 頁面設定 ---
st.set_page_config(page_title="Corolla Cross TCO 終極精算機", page_icon="🚙")

st.title("🚙 Corolla Cross 油電 vs. 汽油：TCO 終極決戰")
st.markdown("### 👨‍🔧 中油工程師幫你算：加上「折舊」後的真實成本")

# --- 側邊欄：使用者輸入 ---
st.sidebar.header("1. 用車習慣")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 5000, 60000, 20000)
years_to_keep = st.sidebar.slider("預計持有幾年", 1, 15, 5)
gas_price = st.sidebar.number_input("目前油價 (95無鉛)", value=31.0)

st.sidebar.header("2. 車價設定 (新車/中古價)")
# 預設為 CC 2024 新車價格區間
gas_car_price = st.sidebar.number_input("汽油版購入價", value=859000)
hybrid_car_price = st.sidebar.number_input("油電版購入價", value=915000)

st.sidebar.header("3. 進階參數 (工程師專用)")
depreciation_rate = st.sidebar.slider("每年折舊率 (%)", 5, 20, 12, help="Toyota 神車通常折舊低，約 10-13%")
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)

# --- 核心計算引擎 ---

# 1. 基礎數據
total_km = annual_km * years_to_keep
gas_mpg = 12.0     # 汽油版油耗
hybrid_mpg = 21.0  # 油電版油耗
tax_gas = 11920 * years_to_keep   # 1.8L 稅金 (兩者相同)
tax_hybrid = 11920 * years_to_keep

# 2. 油錢計算
gas_fuel_cost = (total_km / gas_mpg) * gas_price
hybrid_fuel_cost = (total_km / hybrid_mpg) * gas_price

# 3. 折舊與殘值計算 (Future Value Calculation)
# 公式：殘值 = 買入價 * (1 - 折舊率)^年數
# 注意：高里程會加速折舊 (工程師修正係數)
mileage_penalty = 0
if annual_km > 25000:
    mileage_penalty = 0.03 * years_to_keep # 每年多扣 3% 因為里程高

real_depreciation = (depreciation_rate / 100) + (mileage_penalty / years_to_keep)

# 汽油版殘值
gas_resale_value = gas_car_price * ((1 - real_depreciation) ** years_to_keep)
# 油電版殘值
hybrid_resale_value = hybrid_car_price * ((1 - real_depreciation) ** years_to_keep)

# 4. 大電池風險邏輯
battery_risk_cost = 0
battery_msg = "✅ 里程與年份在安全範圍內"
if total_km > 160000 or years_to_keep > 8:
    battery_risk_cost = battery_cost
    battery_msg = "⚠️ 預計需更換大電池 (已計入成本)"

# 5. TCO 總結 (總持有成本 = 買車 - 賣車 + 油錢 + 稅金 + 電池)
tco_gas = (gas_car_price - gas_resale_value) + gas_fuel_cost + tax_gas
tco_hybrid = (hybrid_car_price - hybrid_resale_value) + hybrid_fuel_cost + tax_hybrid + battery_risk_cost

# 誰贏了？
diff = tco_gas - tco_hybrid

# --- 視覺化輸出區 ---

st.header(f"📊 {years_to_keep} 年後的真實帳單")

# 三欄大數據
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("汽油版總花費", f"${int(tco_gas):,}", help="含折舊、油錢、稅金")
with col2:
    st.metric("油電版總花費", f"${int(tco_hybrid):,}", delta=f"差額 ${int(diff):,}", help="含折舊、油錢、稅金、電池")
with col3:
    if diff > 0:
        st.success(f"🏆 油電版獲勝！\n省下 ${int(diff):,}")
    else:
        st.error(f"📉 汽油版獲勝！\n省下 ${int(abs(diff)):,}")

st.markdown("---")

# 詳細費用拆解 (Stacked Bar Chart)
st.subheader("💰 錢都花去哪了？ (成本結構分析)")

cost_data = pd.DataFrame({
    "項目": ["折舊損失 (買-賣)", "油錢支出", "稅金總額", "大電池風險"],
    "汽油版": [gas_car_price - gas_resale_value, gas_fuel_cost, tax_gas, 0],
    "油電版": [hybrid_car_price - hybrid_resale_value, hybrid_fuel_cost, tax_hybrid, battery_risk_cost]
})

st.bar_chart(cost_data.set_index("項目"))

# 殘值預測表
st.markdown("### 📉 二手殘值預測 (這台車還剩多少錢?)")
st.write(f"如果 {years_to_keep} 年後賣掉，預估回收金額：")
col_r1, col_r2 = st.columns(2)
col_r1.info(f"⛽ 汽油版殘值：${int(gas_resale_value):,}")
col_r2.success(f"⚡ 油電版殘值：${int(hybrid_resale_value):,}")

# --- 工程師分析報告 ---
st.markdown("---")
st.markdown("### 👨‍🔧 中油工程師的 TCO 分析報告")

if diff > 0:
    st.write(f"""
    **結論：建議直上油電版！**
    雖然油電版新車貴了 **${int(hybrid_car_price - gas_car_price):,}**，但是：
    1. 油錢幫你省了 **${int(gas_fuel_cost - hybrid_fuel_cost):,}**。
    2. 賣車時，油電版還可以多賣 **${int(hybrid_resale_value - gas_resale_value):,}** (因為殘值較高)。
    3. 就算換了一顆 **${int(battery_cost):,}** 的電池，你還是賺！
    """)
else:
    st.write(f"""
    **結論：買汽油版就好！**
    你的里程數太少 ({annual_km} km/年)，油錢省不夠多。
    加上油電版新車價差與潛在電池風險，**硬買油電反而多花錢**。
    """)

st.markdown(f"**電池狀態備註：** {battery_msg}")

# --- 變現與導流 (CTA) ---
st.markdown("---")
st.markdown("#### 想知道更詳細的驗車眉角？")
st.markdown("👉 [**下載：Corolla Cross 二手車驗車檢查表 (PDF) - $199**](#)")
