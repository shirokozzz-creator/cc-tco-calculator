import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# ==========================================
# 0. 核心設定 & 風格
# ==========================================
st.set_page_config(page_title="RAV4 世代 TCO 戰情室", page_icon="📉", layout="wide")

# 模擬「航太工程師」的深色儀表板風格
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .card-stat { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #41444e; text-align: center; }
    .highlight { color: #ff4b4b; font-weight: bold; }
    .gold { color: #ffd700; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 數據引擎 (自動讀取拍場資料)
# ==========================================
@st.cache_data
def get_auction_price_avg():
    # 預設值 (萬)，萬一讀不到 CSV 時使用
    default_gas_5_5 = 68
    default_hybrid_5_5 = 78
    
    csv_path = "cars.csv"
    if not os.path.exists(csv_path):
        return default_gas_5_5, default_hybrid_5_5, "⚠️ 使用預設行情 (未讀取到 CSV)"

    try:
        df = pd.read_csv(csv_path, on_bad_lines='skip')
        # 簡單清洗：取出數字
        if '成本底價' in df.columns:
             df['成本底價'] = df['成本底價'].astype(str).str.replace(',', '').str.replace('$', '').astype(float).astype(int)
        
        # 篩選 RAV4
        rav4_df = df[df['車款名稱'].str.contains('RAV4', case=False, na=False)]
        
        # 區分汽油與油電 (這裡做個簡單篩選，實際要看你的 CSV 命名規則)
        hybrid_df = rav4_df[rav4_df['車款名稱'].str.contains('HYBRID|油電', case=False, na=False)]
        gas_df = rav4_df[~rav4_df['車款名稱'].str.contains('HYBRID|油電', case=False, na=False)]
        
        # 計算平均 (單位換算成萬)
        avg_hybrid = int(hybrid_df['成本底價'].mean() / 10000) if not hybrid_df.empty else default_hybrid_5_5
        avg_gas = int(gas_df['成本底價'].mean() / 10000) if not gas_df.empty else default_gas_5_5
        
        return avg_gas, avg_hybrid, "✅ 已載入 2026/01 拍場均價"
    except:
        return default_gas_5_5, default_hybrid_5_5, "⚠️ 讀取錯誤，使用預設值"

# ==========================================
# 2. TCO 運算核心 (航太級模型)
# ==========================================
def calculate_tco_curve(years, mileage_per_year, gas_price, car_models):
    # car_models = {'Name': {'price': 萬, 'km_l': 油耗, 'tax': 稅金, 'maintain': 保養}}
    data = {}
    
    x_axis = list(range(years + 1)) # 0 ~ 10 年
    
    for name, specs in car_models.items():
        costs = []
        base_price = specs['price'] * 10000 # 換算成元
        current_total = base_price
        costs.append(current_total)
        
        # 每年增加的成本
        yearly_fuel = (mileage_per_year / specs['km_l']) * gas_price
        yearly_tax = specs['tax']
        yearly_maintain = specs['maintain']
        
        for i in range(1, years + 1):
            # 隨著車齡增加，保養費通常會變貴 (簡單模擬：每年 +5%)
            adjusted_maintain = yearly_maintain * (1.05 ** (i-1))
            current_total += (yearly_fuel + yearly_tax + adjusted_maintain)
            costs.append(current_total)
            
        data[name] = costs
        
    return x_axis, data

# ==========================================
# 3. UI 介面
# ==========================================
def main():
    st.title("📊 RAV4 世代 TCO 終極戰情室")
    st.markdown("用數據告訴你：**現在抄底 5.5 代，還是等 6 代？**")

    # --- 側邊欄：實驗室參數 ---
    with st.sidebar:
        st.header("⚙️ 實驗室參數設定")
        mileage = st.slider("📅 每年行駛里程 (km)", 5000, 40000, 15000)
        gas_price = st.number_input("⛽ 目前油價 (元/L)", 28.0, 40.0, 31.0)
        years = st.slider("⏳ 預計持有年份", 3, 15, 10)
        
        st.markdown("---")
        st.caption("由 Brian 的拍場數據庫驅動")

    # --- 載入數據 ---
    auction_gas, auction_hybrid, status_msg = get_auction_price_avg()
    if "⚠️" in status_msg:
        st.warning(status_msg)
    else:
        st.success(status_msg)

    # --- 核心參數輸入 (可手動微調) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🏎️ 5.5代 汽油 (中古)")
        p1 = st.number_input("拍場入手價 (萬)", 50, 100, auction_gas, key="p1")
        fuel1 = 12.0 # 平均油耗
        tax1 = 17410 # 2.0稅金
    
    with c2:
        st.markdown("### 🔋 5.5代 油電 (中古)")
        p2 = st.number_input("拍場入手價 (萬)", 60, 120, auction_hybrid, key="p2")
        fuel2 = 20.0 
        tax2 = 22410 # 2.5稅金 (比較貴!)
        
    with c3:
        st.markdown("### 🚀 6代 油電 (新車)")
        p3 = st.number_input("預估上市價 (萬)", 110, 180, 135, key="p3")
        fuel3 = 24.0 # 預估新科技油耗
        tax3 = 17410 # 預估 2.5 會改引擎? 先假設跟汽油一樣或是用2.5稅金，這裡先設2.5比較保守
        # 修正：如果6代進台灣是2.5 Hybrid，稅金還是貴。如果是PHEV或新引擎可能不同。
        # 這裡為了對比，先假設 6 代是 2.5 Hybrid (稅金貴)
        tax3 = 22410 

    # --- 運算 ---
    models = {
        '5.5代 汽油 (中古)': {'price': p1, 'km_l': fuel1, 'tax': tax1, 'maintain': 10000},
        '5.5代 油電 (中古)': {'price': p2, 'km_l': fuel2, 'tax': tax2, 'maintain': 8000}, # 油電保養較省
        '6代 油電 (預估新車)': {'price': p3, 'km_l': fuel3, 'tax': tax3, 'maintain': 6000} # 新車保養最省
    }
    
    x_axis, y_data = calculate_tco_curve(years, mileage, gas_price, models)

    # --- 繪圖 (Plotly) ---
    st.markdown("---")
    st.subheader("📈 成本黃金交叉圖 (10年累積花費)")
    
    fig = go.Figure()
    
    # 顏色設定：汽油(紅/警示), 5.5油電(藍/理性), 6代(綠/昂貴但省油?)
    colors = {'5.5代 汽油 (中古)': '#ff4b4b', '5.5代 油電 (中古)': '#2196f3', '6代 油電 (預估新車)': '#00c853'}
    
    for name, costs in y_data.items():
        fig.add_trace(go.Scatter(
            x=x_axis, y=costs, 
            mode='lines+markers', 
            name=name,
            line=dict(width=3, color=colors[name]),
            marker=dict(size=6)
        ))

    fig.update_layout(
        title="累積總花費 (車價 + 油錢 + 稅金 + 保養)",
        xaxis_title="持有年數",
        yaxis_title="累積台幣 (元)",
        template="plotly_dark", # 深色模式
        hovermode="x unified",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- 結論分析 ---
    # 計算 10 年後的總花費
    final_cost_gas = y_data['5.5代 汽油 (中古)'][-1]
    final_cost_hybrid_old = y_data['5.5代 油電 (中古)'][-1]
    final_cost_hybrid_new = y_data['6代 油電 (預估新車)'][-1]
    
    diff_new_vs_old_hybrid = final_cost_hybrid_new - final_cost_hybrid_old
    
    st.markdown("### 💡 航太工程師的短影音腳本重點：")
    
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.info(f"""
        **重點 1：新車 vs 中古 (價差驚人)**
        * 買 6 代新車，10 年後總花費約 **{int(final_cost_hybrid_new/10000)} 萬**。
        * 買 5.5 代油電，10 年後總花費約 **{int(final_cost_hybrid_old/10000)} 萬**。
        * 結論：即使 6 代比較省油，但因為車價太貴，開了 10 年你還是 **多花了 {int(diff_new_vs_old_hybrid/10000)} 萬！**
        """)
        
    with c_res2:
        if final_cost_hybrid_old < final_cost_gas:
             st.success(f"""
             **重點 2：汽油 vs 油電 (中古對決)**
             * 5.5 代油電雖然稅金貴，但因為油耗優勢，大約在 **第 {3} 年** 就會產生黃金交叉！
             * 長期持有絕對是 **油電版** 比較划算。
             """)
        else:
             st.warning(f"""
             **重點 2：里程太少，買汽油就好**
             * 因為你設定的里程很低 ({mileage}km)，油電省回來的油錢補不回稅金跟車價差。
             * 建議直接買 **5.5 代汽油版** 最省現金流。
             """)

    st.caption("※ 數據模型假設：油價浮動與通膨未計入，僅供趨勢參考。")

if __name__ == "__main__":
    main()
