import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import google.generativeai as genai

# ==========================================
# 0. 核心設定 & 風格
# ==========================================
st.set_page_config(page_title="RAV4 世代對決 | Brian Auto", page_icon="🥊", layout="wide")

st.markdown("""
    <style>
    /* 全局設定 */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* 1. 規格表樣式 */
    .spec-table {
        width: 100%;
        border-collapse: collapse;
        color: #333;
        background-color: white;
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    .spec-table th { background-color: #1565c0; color: white; padding: 10px; text-align: center; }
    .spec-table td { padding: 10px; text-align: center; border-bottom: 1px solid #ddd; }
    .winner { color: #2e7d32; font-weight: bold; background-color: #e8f5e9; }
    .loser { color: #c62828; background-color: #ffebee; }

    /* 2. 痛苦指數卡片 */
    .pain-card {
        background: linear-gradient(135deg, #d32f2f 0%, #ff5252 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(211, 47, 47, 0.4);
        margin-bottom: 20px;
    }
    .pain-num { font-size: 2.5em; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
    
    /* 3. VIP 票根樣式 */
    .ticket-stub {
        background: linear-gradient(90deg, #ffd700 0%, #ffecb3 100%);
        border: 2px dashed #b71c1c;
        border-radius: 10px;
        padding: 15px;
        color: #333;
        text-align: center;
        position: relative;
        margin-top: 20px;
    }
    .ticket-title { font-weight: bold; font-size: 1.2em; color: #b71c1c; }
    
    /* 一般文字框修復 */
    .vs-box { background-color: #262730; padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px; border: 1px solid #41444e;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 邏輯核心 (無 CSV，直接用參數)
# ==========================================
def calculate_tco_curve(years, mileage_per_year, gas_price, models):
    # 這裡跟上一版一樣，用數學算累積成本
    x_axis = list(range(years + 1))
    data = {}
    for name, specs in models.items():
        costs = []
        base_price = specs['price'] * 10000 
        current_total = base_price
        costs.append(current_total)
        
        yearly_fuel = (mileage_per_year / specs['km_l']) * gas_price
        yearly_tax = specs['tax']
        yearly_maintain = specs['maintain']
        
        for i in range(1, years + 1):
            adjusted_maintain = yearly_maintain * (1.05 ** (i-1))
            current_total += (yearly_fuel + yearly_tax + adjusted_maintain)
            costs.append(current_total)
        data[name] = costs
    return x_axis, data

def generate_video_script(api_key, gen5_price, gen6_est_price, verdict):
    if not api_key: return "⚠️ 請先設定 API Key"
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        你是汽車自媒體 Brian。寫一個 30秒短影音腳本。
        主題：5.5代中古 vs 6代新車 RAV4。
        數據：5代 {gen5_price}萬, 6代 {gen6_est_price}萬。
        結論：{verdict}。
        風格：要有爆點，結尾引導加Line。
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"Error: {str(e)}"

# ==========================================
# 2. 主程式
# ==========================================
def main():
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = None

    st.title("🥊 RAV4 世代大對決：現在買 vs 再等等")
    
    # 側邊欄設定
    with st.sidebar:
        st.header("⚙️ 參數設定")
        if not api_key: api_key = st.text_input("API Key", type="password")
        mileage = st.slider("年里程 (km)", 5000, 40000, 15000)
        gas_price = 31.0
        years = 10
        st.markdown("---")
        # 直接在這裡手動微調價格，取代 CSV
        p_gas = st.number_input("5.5代 汽油價", 60, 90, 68)
        p_hybrid = st.number_input("5.5代 油電價", 70, 100, 78)
        p_new = st.number_input("6代 預估價", 110, 160, 135)
        wait_months = st.slider("等待月數", 6, 24, 12)

    # --- 功能 1：規格生死鬥 (Spec Face-off) ---
    st.subheader("1. 規格生死鬥 (Spec Face-off)")
    st.markdown("不用看密密麻麻的規配表，一張圖看懂誰才是 CP 值之王。")
    
    # 用 HTML 表格做比較
    st.markdown(f"""
    <table class="spec-table">
        <tr>
            <th>項目</th>
            <th>5.5代 汽油 (中古)</th>
            <th>5.5代 油電 (中古)</th>
            <th>6代 油電 (新車)</th>
        </tr>
        <tr>
            <td><b>入手價格</b></td>
            <td class="winner">{p_gas} 萬 (勝)</td>
            <td class="winner">{p_hybrid} 萬</td>
            <td class="loser">{p_new} 萬 (貴爆)</td>
        </tr>
        <tr>
            <td><b>每年稅金</b></td>
            <td class="winner">1.7 萬</td>
            <td class="loser">2.2 萬</td>
            <td class="loser">2.2 萬 (預估)</td>
        </tr>
        <tr>
            <td><b>平均油耗</b></td>
            <td class="loser">12 km/L</td>
            <td class="winner">20 km/L</td>
            <td class="winner">24 km/L (預估)</td>
        </tr>
        <tr>
            <td><b>等待時間</b></td>
            <td class="winner">0 天 (現車)</td>
            <td class="winner">0 天 (現車)</td>
            <td class="loser">{wait_months} 個月</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

    # --- 功能 2：等待痛苦指數 (Daily Pain Metric) ---
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("2. 等待痛苦指數")
        # 計算：價差 + (等待月數 * 1.5萬租車費)
        total_wait_cost = (p_new - p_gas) * 10000 + (wait_months * 15000)
        daily_loss = int(total_wait_cost / (wait_months * 30))
        
        st.markdown(f"""
        <div class='pain-card'>
            <div>為了等 6 代，你每天正在損失...</div>
            <div class='pain-num'>${daily_loss} 元</div>
            <div style='font-size:0.8em; margin-top:5px;'>包含車價漲幅與無車可用的隱形成本</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        # 圖表區域 (Plotly)
        st.subheader("3. 十年總花費曲線 (TCO)")
        models = {
            '5.5代 汽油': {'price': p_gas, 'km_l': 12.0, 'tax': 17410, 'maintain': 10000},
            '5.5代 油電': {'price': p_hybrid, 'km_l': 20.0, 'tax': 22410, 'maintain': 8000},
            '6代 新車': {'price': p_new, 'km_l': 24.0, 'tax': 22410, 'maintain': 6000}
        }
        x, y_data = calculate_tco_curve(years, mileage, gas_price, models)
        
        fig = go.Figure()
        colors = ['#ef5350', '#42a5f5', '#66bb6a']
        i = 0
        for name, costs in y_data.items():
            fig.add_trace(go.Scatter(x=x, y=costs, mode='lines', name=name, line=dict(color=colors[i], width=3)))
            i+=1
        
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    # --- 功能 3：早鳥排隊票根 (Call to Action) ---
    st.markdown("---")
    
    col_cta1, col_cta2 = st.columns([2, 1])
    
    with col_cta1:
        # 這裡生成腳本
        if st.button("🎬 生成 Brian 的爆款腳本"):
            with st.spinner("Writing..."):
                verdict = "買 5.5 代油電" if y_data['5.5代 油電'][-1] < y_data['6代 新車'][-1] else "等 6 代"
                script = generate_video_script(api_key, p_gas, p_new, verdict)
                st.info(script)
                
    with col_cta2:
        # 黃金票根 UI
        st.markdown(f"""
        <div class='ticket-stub'>
            <div class='ticket-title'>🎟️ Brian 嚴選・早鳥卡</div>
            <hr style='border-top: 1px dashed #b71c1c;'>
            <div style='font-size: 0.9em; margin: 10px 0;'>
                想第一時間收到<br>
                <b>「5.5 代 RAV4 崩盤價」</b>通知？
            </div>
            <a href='https://line.me/ti/p/你的ID' target='_blank' 
               style='background-color:#d32f2f; color:white; padding:8px 15px; text-decoration:none; border-radius:5px; font-weight:bold; display:block;'>
               👉 點我領取號碼牌
            </a>
            <div style='font-size:0.7em; color:#666; margin-top:5px;'>目前已有 1,248 人排隊中</div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
