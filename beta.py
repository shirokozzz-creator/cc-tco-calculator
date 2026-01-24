import streamlit as st
import pandas as pd
import altair as alt

# ==========================================
# 0. 測試版全域設定
# ==========================================
st.set_page_config(
    page_title="[Beta] RAV4 戰情室", 
    page_icon="🚧", 
    layout="wide"
)

# ==========================================
# 1. 核心功能：RAV4 世代大對決
# ==========================================
def main():
    st.title("🚧 工程師內部測試版：RAV4 世代大對決")
    st.caption("Testing Protocol: RAV4 Gen 6 (Hybrid) vs Gen 5.5 (Hybrid) vs Gen 5.5 (Gas)")

    # --- 參數設定區 ---
    with st.sidebar:
        st.header("⚙️ 參數模擬")
        years = st.slider("預計持有年數", 1, 15, 10)
        km_per_year = st.slider("年行駛里程 (km)", 5000, 50000, 15000)
        gas_price = st.number_input("預估平均油價", value=31.0)
        
        st.markdown("---")
        st.write("🔧 **維修/電池參數**")
        battery_cost = st.number_input("油電大電池更換費", value=65000)
        risk_year = st.slider("第幾年更換電池？(風險模擬)", 5, 12, 8)

    # --- 選手數據庫 ---
    competitors = [
        {
            "name": "🔥 6 代 2.5 Hybrid (新車)",
            "price": 1300000,   # 預估接單價
            "tax": 22410,       # 2.5L 稅金
            "km_l": 22.0,       # 新世代油耗
            "color": "#FF4B4B", # 紅色 (警示)
            "is_hybrid": True,
            "is_new": True
        },
        {
            "name": "⚡ 5.5 代 2.5 Hybrid (二手)",
            "price": 950000,    # 目前行情
            "tax": 22410,       # 2.5L 稅金 (痛點)
            "km_l": 21.0,       # 舊世代油耗
            "color": "#0052CC", # 藍色 (油電)
            "is_hybrid": True,
            "is_new": False
        },
        {
            "name": "⛽ 5.5 代 2.0 汽油 (二手)",
            "price": 750000,    # 目前行情
            "tax": 17410,       # 2.0L 稅金 (優勢)
            "km_l": 14.5,       # 汽油版油耗 (劣勢)
            "color": "#2ECC71", # 綠色 (冠軍)
            "is_hybrid": False,
            "is_new": False
        }
    ]

    # --- TCO 運算邏輯 ---
    chart_rows = []
    final_results = {} 

    for comp in competitors:
        current_val = comp['price']
        
        for y in range(0, years + 1):
            # A. 折舊模型
            if y == 0:
                depreciation = 0
            else:
                if comp['is_new']:
                    # 新車前三年折舊重
                    drop_rate = 0.20 if y == 1 else 0.10
                else:
                    # 二手車折舊平緩
                    drop_rate = 0.08
                
                depreciation = current_val * drop_rate
                current_val -= depreciation
            
            # 累計折舊損失
            cum_depreciation = comp['price'] - current_val

            # B. 油錢
            total_km = km_per_year * y
            fuel_cost = (total_km / comp['km_l']) * gas_price
            
            # C. 稅金
            tax_cost = comp['tax'] * y
            
            # D. 電池風險
            battery_risk = 0
            if comp['is_hybrid'] and y >= risk_year:
                battery_risk = battery_cost

            # 總 TCO
            total_tco = cum_depreciation + fuel_cost + tax_cost + battery_risk
            
            chart_rows.append({
                "年份": y,
                "車型": comp['name'],
                "累積總成本": int(total_tco)
            })
            
            if y == years:
                final_results[comp['name']] = int(total_tco)

    df_chart = pd.DataFrame(chart_rows)

    # --- 結果展示 ---
    
    # 計算冠軍與差距
    winner = min(final_results, key=final_results.get)
    gap = max(final_results.values()) - min(final_results.values())
    
    st.info(f"📊 參數條件：年跑 {km_per_year} km，持有 {years} 年")

    # 顯示三個 Metric (數據儀表板)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        val = final_results[competitors[0]['name']]
        st.metric("6 代新車 (基準)", f"${val:,}")
    
    with c2:
        name = competitors[1]['name']
        val = final_results[name]
        diff = final_results[competitors[0]['name']] - val
        st.metric("5.5 代油電", f"${val:,}", f"省 ${diff:,}")

    with c3:
        name = competitors[2]['name']
        val = final_results[name]
        diff = final_results[competitors[0]['name']] - val
        st.metric("5.5 代汽油", f"${val:,}", f"省 ${diff:,}")

    # 冠軍宣告
    if "汽油" in winner:
        st.success(f"🏆 **數據冠軍：{winner}** (因為稅金優勢 + 入手價低，完勝油電車)")
    else:
        st.warning(f"🏆 **數據冠軍：{winner}** (高里程下，油電優勢浮現)")

    # 視覺化圖表
    st.markdown("### 📈 成本曲線圖 (越低越好)")
    chart = alt.Chart(df_chart).mark_line(strokeWidth=4).encode(
        x=alt.X('年份', axis=alt.Axis(tickMinStep=1)),
        y='累積總成本',
        color=alt.Color('車型', scale=alt.Scale(
            domain=[c['name'] for c in competitors],
            range=[c['color'] for c in competitors]
        )),
        tooltip=['年份', '車型', '累積總成本']
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

    # --- 內部除錯區 ---
    with st.expander("🕵️‍♂️ 原始數據表 (Debug Mode)"):
        st.dataframe(df_chart)

if __name__ == "__main__":
    main()
