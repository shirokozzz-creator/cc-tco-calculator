import streamlit as st
import pandas as pd

# --- 頁面設定 ---
st.set_page_config(page_title="Corolla Cross 油電/汽油 終極試算", page_icon="🚗")

st.title("🚗 Corolla Cross 油電 vs. 汽油：到底誰划算？")
st.markdown("### 👨‍🔧 中油工程師幫你算 TCO (總持有成本)")

# --- 側邊欄：使用者輸入 ---
st.sidebar.header("輸入你的用車習慣")
annual_km = st.sidebar.slider("每年行駛里程 (km)", 5000, 50000, 15000)
years_to_keep = st.sidebar.slider("預計持有幾年", 1, 15, 5)
gas_price = st.sidebar.number_input("目前油價 (95無鉛)", value=31.0)

st.sidebar.markdown("---")
st.sidebar.subheader("進階參數 (可手動調整)")
hybrid_premium = st.sidebar.number_input("油電版比汽油版貴多少?", value=60000)
battery_cost = st.sidebar.number_input("大電池更換預算", value=49000)

# --- 計算邏輯 ---
total_km = annual_km * years_to_keep
gas_mpg = 12.0
hybrid_mpg = 21.0

gas_fuel_total = (total_km / gas_mpg) * gas_price
hybrid_fuel_total = (total_km / hybrid_mpg) * gas_price

fuel_savings = gas_fuel_total - hybrid_fuel_total
net_benefit = fuel_savings - hybrid_premium

battery_risk_msg = "✅ 里程低，暫無電池風險"
battery_risk_cost = 0
if total_km > 160000 or years_to_keep > 8:
    battery_risk_msg = "⚠️ 高里程/高年份，已計入換電池成本"
    battery_risk_cost = battery_cost
    net_benefit -= battery_cost

# --- 結果顯示區 ---
st.header(f"📊 分析結果 ({years_to_keep}年 / {total_km:,}公里)")
col1, col2 = st.columns(2)
with col1:
    st.metric("汽油版總油錢", f"${int(gas_fuel_total):,}")
with col2:
    st.metric("油電版總油錢", f"${int(hybrid_fuel_total):,}", delta=f"省下 ${int(fuel_savings):,}")

st.markdown("---")
if net_benefit > 0:
    st.success(f"🏆 **建議買油電版！**\n\n即使扣掉車價差額與潛在電池費，你還**多賺了 ${int(net_benefit):,}**。")
else:
    st.error(f"📉 **建議買汽油版！**\n\n你的里程數不夠多。買油電版你會**多花 ${int(abs(net_benefit)):,}**。")

st.info(f"💡 工程師備註：{battery_risk_msg}")

# 圖表
chart_data = pd.DataFrame({
    '項目': ['車價差額', '油錢支出', '電池風險'],
    '汽油版': [0, gas_fuel_total, 0],
    '油電版': [hybrid_premium, hybrid_fuel_total, battery_risk_cost]
})
st.bar_chart(chart_data.set_index('項目'))

st.markdown("---")
st.markdown("#### 想要買二手 CC 怕踩雷？")
st.markdown("👉 [**點此下載：工程師的二手車驗車檢查表 (PDF) - $199**](#)")
