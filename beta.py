import streamlit as st
import pandas as pd
import altair as alt

# ==========================================
# 0. 全域設定
# ==========================================
st.set_page_config(
    page_title="[Beta] RAV4 旗艦對決", 
    page_icon="⚔️", 
    layout="wide"
)

# ==========================================
# 1. 核心功能：RAV4 旗艦大亂鬥
# ==========================================
def main():
    st.title("⚔️ RAV4 世代大對決：旗艦版 TCO 試算")
    st.caption("工程師觀點：當三台車都是「旗艦版」，誰才是數學上的贏家？")

    # --- 1. 側邊欄：參數與價格設定 ---
    with st.sidebar:
        st.header("💰 車價設定 (請輸入成交價)")
        st.caption("請輸入您詢問到的價格，系統會即時運算")
        
        # 開放輸入價格 (預設值僅供參考)
        price_gen6 = st.number_input(
            "🔥 6代 2.5 Hybrid 旗艦 (新車)", 
            value=1350000, 
            step=10000,
            help="預估 2026 年式 6 代油電二驅旗艦版的接單價"
        )
        
        price_gen55_hyb = st.number_input(
            "⚡ 5.5代 2.5 Hybrid 旗艦 (二手)", 
            value=1050000, 
            step=10000,
            help="鎖定 2023-2024 年式 (TSS 3.0) 的完全體旗艦"
        )
        
        price_gen55_gas = st.number_input(
            "⛽ 5.5代 2.0 汽油 旗艦 (二手)", 
            value=820000, 
            step=10000,
            help="鎖定 2022-2023 年式 汽油旗艦版"
        )
        
        st.markdown("---")
        st.header("⚙️ 用車情境模擬")
        years = st.slider("預計持有年數", 1, 15, 10)
        km_per_year = st.slider("年行駛里程 (km)", 5000, 50000, 15000)
        gas_price = st.number_input("預估平均油價", value=31.0)
        
        st.markdown("---")
        st.write("🔧 **維修/電池參數**")
        battery_cost = st.number_input("油電大電池更換費", value=65000)
        risk_year = st.slider("第幾年更換電池？(風險模擬)", 5, 12, 8)

    # --- 2. 選手數據庫 (規格固定，價格連動) ---
    competitors = [
        {
            "name": "🔥 6代 Hybrid 旗艦 (新車)",
            "price": price_gen6,
            "tax": 22410,       # 2.5L 稅金 (劣勢)
            "km_l": 22.0,       # 新世代油耗 (優勢)
            "color": "#FF4B4B", # 紅色
            "is_hybrid": True,
            "is_new": True
        },
        {
            "name": "⚡ 5.5代 Hybrid 旗艦 (二手)",
            "price": price_gen55_hyb,
            "tax": 22410,       # 2.5L 稅金 (劣勢)
            "km_l": 21.0,       # 舊世代油耗
            "color": "#0052CC", # 藍色
            "is_hybrid": True,
            "is_new": False
        },
        {
            "name": "⛽ 5.5代 汽油 旗艦 (二手)",
            "price": price_gen55_gas,
            "tax": 17410,       # 2.0L 稅金 (絕對優勢)
            "km_l": 14.5,       # 汽油版油耗 (劣勢)
            "color": "#2ECC71", # 綠色
            "is_hybrid": False,
            "is_new": False
        }
    ]

    # --- 3. TCO 運算邏輯 ---
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
                    # 新車前三年折舊重 (20%, 15%, 10%)
                    if y == 1: drop_rate = 0.20
                    elif y == 2: drop_rate = 0.15
                    else: drop_rate = 0.10
                else:
                    # 二手車折舊相對平緩 (8%)
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

    # --- 4. 結果展示 ---
    
    # 計算數據
    winner_name = min(final_results, key=final_results.get)
    # loser_name = max(final_results.values()) # 暫時不用
    # winner_val = final_results[winner_name] # 暫時不用
    gap = max(final_results.values()) - min(final_results.values())
    
    # 顯示三個 Metric (與價格連動)
    st.markdown("### 📊 10年總持有成本 (TCO) 預測")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        name = competitors[0]['name']
        val = final_results[name]
        st.metric(label=name, value=f"${val:,}", delta="基準")
    
    with c2:
        name = competitors[1]['name']
        val = final_results[name]
        diff = final_results[competitors[0]['name']] - val
        st.metric(label=name, value=f"${val:,}", delta=f"比 6代省 ${diff:,}")

    with c3:
        name = competitors[2]['name']
        val = final_results[name]
        diff = final_results[competitors[0]['name']] - val
        st.metric(label=name, value=f"${val:,}", delta=f"比 6代省 ${diff:,}")

    # 冠軍分析
    st.success(f"🏆 **最佳 CP 值冠軍：{winner_name}**")
    st.info(f"💡 **工程師點評**：在年跑 **{km_per_year:,} km** 的情況下，選擇冠軍車型，可以幫你省下 **${gap:,}** 元 (相當於一台國產小車的錢)。")

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

    # --- 5. 詳細數據與工程師震撼分析 ---
    with st.expander("🕵️‍♂️ 查看工程師的「殘酷真相」分析"):
        
        # === 這裡插入了「工程師的絕對領域分析」 ===
        
        # 計算差額參數 (6代新車 vs 5.5代汽油)
        saved_price = competitors[0]['price'] - competitors[2]['price'] 
        gas_amount = saved_price / gas_price if gas_price > 0 else 0
        round_taiwan = gas_amount * competitors[2]['km_l'] / 1000 
        
        # 稅金差異 (2.5L vs 2.0L)
        tax_waste = (22410 - 17410) * years 
        iphone_count = int(tax_waste / 30000) 
        
        st.markdown("#### ⚡ 工程師的「絕對領域」分析")
        k1, k2, k3 = st.columns(3)
        
        with k1:
            st.info("⛽ **省下的車價能跑多遠？**")
            st.markdown(f"""
            買 5.5 代汽油版省下的 **${saved_price:,}** 價差，
            夠你加 **{int(gas_amount):,} 公升** 的油。
            相當於可以 **免費繞台灣 {int(round_taiwan)} 圈**！
            """)

        with k2:
            st.warning("💸 **稅金陷阱 (2.5L vs 2.0L)**")
            st.markdown(f"""
            若買 6 代或油電版，持有 {years} 年下來，
            你將多繳 **${tax_waste:,}** 給政府。
            這筆錢等於 **平白扔掉了 {iphone_count} 支 iPhone**。
            """)

        with k3:
            st.success("📉 **真正的黃金交叉**")
            # 簡單估算回本里程
            # 每公里油錢成本差異 = (汽油車每公里油錢) - (6代新車每公里油錢)
            cost_per_km_gas = gas_price / competitors[2]['km_l']
            cost_per_km_new = gas_price / competitors[0]['km_l']
            km_diff_cost = cost_per_km_gas - cost_per_km_new
            
            if km_diff_cost > 0:
                # 需追回的總成本 = 車價差 + 稅金差
                total_gap_to_cover = saved_price + tax_waste
                break_even_km = total_gap_to_cover / km_diff_cost
                
                years_to_break_even = break_even_km / km_per_year if km_per_year > 0 else 99
                
                if years_to_break_even < 50:
                    st.markdown(f"""
                    想靠 6 代油電「省油」把車價賺回來？
                    數學告訴我，你必須開 **{int(break_even_km):,} 公里**。
                    以你現在的里程，要開 **{years_to_break_even:.1f} 年** 才能回本。
                    """)
                else:
                     st.markdown("由於車價與稅金差距過大，**這輩子靠省油都賺不回成本**。")
            else:
                 st.markdown("油價或油耗數據異常，無法計算交叉點。")

        st.markdown("---")
        st.markdown("#### 📊 原始運算數據表")
        st.dataframe(df_chart)

if __name__ == "__main__":
    main()
