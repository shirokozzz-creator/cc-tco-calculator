import streamlit as st
import pandas as pd
import altair as alt

# ==========================================
# 0. 全域設定
# ==========================================
st.set_page_config(
    page_title="[戰情室] RAV4 鈔票焚化爐分析", 
    page_icon="🔥", 
    layout="wide"
)

# ==========================================
# 1. 核心功能：RAV4 旗艦大亂鬥 (嚴謹版)
# ==========================================
def main():
    st.title("🔥 RAV4 6代是神車還是「鈔票焚化爐」？")
    st.markdown("### 工程師觀點：加入「隱形持有成本」後的殘酷真相")

    # --- 1. 側邊欄：參數與價格設定 ---
    with st.sidebar:
        st.header("💰 1. 車價設定 (成交價)")
        
        price_gen6 = st.number_input(
            "🔥 6代 2.5 Hybrid 旗艦 (新車)", 
            value=1350000, step=10000,
            help="預估 2026 年式接單價"
        )
        
        price_gen55_hyb = st.number_input(
            "⚡ 5.5代 2.5 Hybrid 旗艦 (二手)", 
            value=1050000, step=10000,
            help="2023-2024 完全體 (TSS 3.0)"
        )
        
        price_gen55_gas = st.number_input(
            "⛽ 5.5代 2.0 汽油 旗艦 (二手)", 
            value=820000, step=10000,
            help="2022-2023 汽油旗艦 (稅金優勢)"
        )
        
        st.markdown("---")
        st.header("⚙️ 2. 用車情境")
        years = st.slider("預計持有年數", 1, 15, 10)
        km_per_year = st.slider("年行駛里程 (km)", 5000, 50000, 15000)
        gas_price = st.number_input("預估平均油價", value=31.0)
        
        st.markdown("---")
        st.header("🕵️‍♂️ 3. 隱形殺手 (工程師專用)")
        st.caption("一般人只算油錢，菁英算的是機會成本")
        
        # 進階參數
        ins_new = st.number_input("新車年保費 (乙式)", value=45000, help="新車前幾年通常被迫保乙式")
        ins_used = st.number_input("二手年保費 (丙式)", value=18000, help="二手車通常保丙式就夠")
        roi_rate = st.slider("資金投資年化報酬率 (%)", 0.0, 10.0, 5.0, step=0.5, 
                             help="如果你把買車的錢拿去投資(如0050)，每年能賺多少？") / 100
        
        st.markdown("---")
        st.write("🔧 **維修風險**")
        battery_cost = st.number_input("油電大電池更換費", value=65000)
        risk_year = st.slider("第幾年更換電池？", 5, 12, 8)

    # --- 2. 選手數據庫 ---
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

    # --- 3. TCO 嚴謹運算邏輯 ---
    chart_rows = []
    final_results = {} 

    for comp in competitors:
        current_val = comp['price']
        
        # 累計成本初始化
        cum_insurance = 0
        cum_lost_interest = 0
        
        for y in range(0, years + 1):
            if y == 0:
                depreciation = 0
                insurance = 0
                interest_loss = 0
            else:
                # A. 折舊 (Depreciation)
                if comp['is_new']:
                    # 新車前三年折舊重
                    if y == 1: drop_rate = 0.20
                    elif y == 2: drop_rate = 0.15
                    else: drop_rate = 0.10
                else:
                    drop_rate = 0.08 # 二手車平緩
                
                depreciation = current_val * drop_rate
                current_val -= depreciation
                
                # B. 保險成本 (Insurance)
                # 新車前5年較貴(遞減)，二手車固定便宜
                if comp['is_new'] and y <= 5:
                    insurance = ins_new * (1 - (y-1)*0.05) 
                else:
                    insurance = ins_used
                cum_insurance += insurance

                # C. 資金機會成本 (Opportunity Cost)
                # 簡單算法：車價 * 利率 (代表這筆錢被鎖在車上，沒辦法生利息的損失)
                interest_loss = comp['price'] * roi_rate
                cum_lost_interest += interest_loss

            # 累計折舊損失
            cum_depreciation = comp['price'] - current_val

            # D. 油錢
            total_km = km_per_year * y
            fuel_cost = (total_km / comp['km_l']) * gas_price
            
            # E. 稅金
            tax_cost = comp['tax'] * y
            
            # F. 電池風險
            battery_risk = 0
            if comp['is_hybrid'] and y >= risk_year:
                battery_risk = battery_cost

            # 總 TCO = 折舊 + 油 + 稅 + 電池 + 保險 + 機會成本
            total_tco = cum_depreciation + fuel_cost + tax_cost + battery_risk + cum_insurance + cum_lost_interest
            
            chart_rows.append({
                "年份": y,
                "車型": comp['name'],
                "累積總成本": int(total_tco)
            })
            
            if y == years:
                final_results[comp['name']] = int(total_tco)

    df_chart = pd.DataFrame(chart_rows)

    # --- 4. 結果展示區 ---
    
    winner_name = min(final_results, key=final_results.get)
    gap = max(final_results.values()) - min(final_results.values())
    
    # 顯示 Metrics
    st.markdown(f"### 📊 {years}年總持有成本 (TCO) 預測")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        name = competitors[0]['name']
        val = final_results[name]
        st.metric(label=name, value=f"${val:,}", delta="基準 (焚化爐)")
    
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

    st.success(f"🏆 **最佳理財工具：{winner_name}**")
    st.info(f"💡 **工程師點評**：考慮折舊、稅金、保險與機會成本後，選擇冠軍車型可幫你守住 **${gap:,}** 的資產。")

    # Altair 圖表
    st.markdown("### 📈 資金燃燒曲線 (越低越好)")
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

    # --- 5. 流量核彈區 (鈔票焚化爐 + 斬殺線) ---
    st.markdown("---")
    st.subheader("🔥 警告：系統判定為「鈔票焚化爐」 (Cash Incinerator)")
    
    with st.expander("💀 點擊查看：工程師的「殘酷真相」報告 (心臟不好勿入)", expanded=True):
        
        # 計算斬殺參數 (6代 vs 5.5代汽油)
        saved_price = competitors[0]['price'] - competitors[2]['price'] # 價差
        
        # 稅金差異
        tax_waste = (22410 - 17410) * years 
        iphone_count = int(tax_waste / 30000) 
        
        # 繞台灣
        gas_amount = saved_price / gas_price if gas_price > 0 else 0
        round_taiwan = gas_amount * competitors[2]['km_l'] / 1000 

        st.markdown("#### ⚡ 階段一：絕對領域分析 (物理攻擊)")
        k1, k2, k3 = st.columns(3)
        
        with k1:
            st.info("⛽ **省下的車價能跑多遠？**")
            st.markdown(f"""
            買 5.5 代汽油版省下的 **${saved_price:,}**，
            夠你加 **{int(gas_amount):,} 公升** 的油。
            相當於可以 **免費繞台灣 {int(round_taiwan)} 圈**！
            """)

        with k2:
            st.warning("💸 **稅金智商稅 (2.5L)**")
            st.markdown(f"""
            若買 6 代 2.5L，{years} 年將多繳 **${tax_waste:,}** 稅金。
            這筆錢沒換來任何馬力，等於 **平白扔掉了 {iphone_count} 支 iPhone**。
            """)
        
        with k3:
             st.success("🛡️ **保險階級差異**")
             ins_diff = (ins_new - ins_used) * 5 # 簡單估算前5年差額
             st.markdown(f"""
             新車被迫保乙式，二手車只需丙式。
             光是保險費，前五年你就多付了約 **${int(ins_diff):,}**。
             這筆錢已經夠你換 4 條頂級輪胎。
             """)

        # === 斬殺線 (Kill Zone) ===
        st.markdown("---")
        st.markdown("#### 🩸 階段二：Brian 的斬殺線 (精神爆擊)")
        
        # 假設月薪 8 萬
        monthly_salary = 80000
        daily_salary = monthly_salary / 22
        work_months = saved_price / monthly_salary
        work_days = saved_price / daily_salary
        
        # 投資複利損失 (10年)
        future_value = saved_price * ((1 + roi_rate) ** years)
        lost_wealth = future_value - saved_price
        
        kz1, kz2 = st.columns(2)
        
        with kz1:
            st.error(f"⚰️ **奴隸指數 (Slave Index)**")
            st.markdown(f"""
            為了買 6 代新車，你多花的錢相當於：
            **你必須不吃不喝工作 {work_months:.1f} 個月**。
            
            也就是說，你接下來的 **{int(work_days)} 個工作天**，
            每天早起、加班、被老闆罵，**全部都是在做白工**。
            你確定要用半年的生命，去換一台車的折舊嗎？
            """)
            
        with kz2:
            st.error(f"📉 **財富失速警告 (Stall Warning)**")
            st.markdown(f"""
            如果把省下的 **${saved_price:,}** 拿去投資 (年化 {roi_rate*100}%)：
            {years} 年後，這筆錢會滾成 **${int(future_value):,}**。
            
            選錯車的代價，不只是現在多付錢，
            而是讓你 **{years} 年後憑空蒸發了 ${int(lost_wealth):,} 的獲利**。
            這是你在為自己的退休金自殺。
            """)

        st.markdown("---")
        with st.expander("查看原始數據表"):
            st.dataframe(df_chart)

if __name__ == "__main__":
    main()
