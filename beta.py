import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go

# ==========================================
# 0. 全域設定
# ==========================================
st.set_page_config(
    page_title="Brian 航太數據室 | AI 車況鑑價", 
    page_icon="✈️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS 優化
st.markdown("""
    <style>
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: bold; height: 3.5em; 
        background-color: #0077b6; color: white; border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #0096c7; color: white; transform: translateY(-2px); }
    .report-box { background-color: #f8f9fa; border-left: 5px solid #0077b6; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .price-box { background-color: #e9ecef; border-left: 5px solid #2a9d8f; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 真實數據庫 (從 PDF 提取)
# ==========================================
# 這裡放入你剛剛提供的 HAA/SAA 真實成交價
REAL_DB = {
    "RAV4 (汽油)": {
        "auction_price": 634000, # 參考 2020/04 成交價
        "market_price": 750000,  # 市場開價
        "desc": "2020年式 五代 RAV4"
    },
    "RAV4 (油電)": {
        "auction_price": 748000, # 參考 2023/05 成交價
        "market_price": 890000,
        "desc": "2023年式 油電旗艦"
    },
    "Corolla Cross (汽油)": {
        "auction_price": 500000, # 參考 2022/06 成交價
        "market_price": 630000,
        "desc": "2022年式 國民神車"
    },
    "Altis (汽油)": {
        "auction_price": 299000, # 參考 2020/10 成交價
        "market_price": 430000,
        "desc": "2020年式 12代 TNGA"
    },
    "Camry (汽油)": {
        "auction_price": 600000, # 參考 2021/07 成交價
        "market_price": 750000,
        "desc": "2021年式 進口豪華版"
    }
}

# ==========================================
# 2. 側邊欄
# ==========================================
def sidebar_content():
    with st.sidebar:
        st.header("✈️ Brian 航太數據室")
        st.caption("AI 驅動的中古車簽證官")
        st.markdown("---")
        st.info("💡 **我不賣車，我只提供真相。**\n利用大數據與 AI 演算法，幫你過濾 90% 的檸檬車與盤子價。")
        st.write("📞 **聯絡工程師**")
        st.link_button("💬 加 LINE 取得報告", "https://line.me/ti/p/你的LineID", use_container_width=True)

# ==========================================
# 3. 主程式
# ==========================================
def main():
    sidebar_content()

    st.title("🛡️ 中古車 AI 戰情中心")
    st.caption("Transparency as a Service (透明即服務)")
    
    # 重新安排 Tabs：免費誘餌在前，付費功能在後
    tab1, tab2, tab3 = st.tabs(["📊 戰情室 (Free)", "⚖️ 價格分析 (Paid)", "🩺 查定翻譯 (Paid)"])

    # === Tab 1: 戰情室 (免費展示區) ===
    with tab1:
        st.header("📊 本週精選：真實成交行情")
        st.info("💡 這是我們資料庫中的 **「冰山一角」**。這些都是真實發生的成交價格。")
        
        # 展示 3 個真實案例
        for car, data in list(REAL_DB.items())[:3]:
            with st.expander(f"🚗 {car} ({data['desc']})"):
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("拍賣成交價 (底價)", f"${data['auction_price']:,}")
                with c2: st.metric("市場零售行情", f"${data['market_price']:,}")
                with c3: 
                    savings = data['market_price'] - data['auction_price']
                    st.metric("潛在價差", f"${savings:,}", delta="你的談判空間")
                st.caption("數據來源：HAA/SAA 拍賣場 (2025/12 - 2026/01)")

        st.markdown("---")
        st.warning("👉 想查詢其他車款？請使用 **Tab 2 價格分析**。")

    # === Tab 2: 價格合理性分析 (核心付費功能模擬) ===
    with tab2:
        st.header("⚖️ AI 估價師：你買貴了嗎？")
        st.write("輸入你在 8891 或車行看到的價格，AI 幫你計算「合理入手價」。")
        
        c1, c2 = st.columns(2)
        with c1:
            # 使用真實資料庫的選項
            q_model = st.selectbox("選擇車款", list(REAL_DB.keys()))
        with c2:
            q_price = st.number_input("車行開價 (萬)", min_value=10, max_value=200, value=int(REAL_DB[q_model]['market_price']/10000))
        
        if st.button("🚀 啟動 AI 估價模型"):
            with st.spinner("正在比對 HAA/SAA 真實成交大數據..."):
                time.sleep(1.5)
            
            # 計算邏輯
            base_price = REAL_DB[q_model]["auction_price"]
            offer_price = q_price * 10000
            # 假設合理利潤區間 (拍賣價 + 10%~15% 管銷)
            fair_price_min = int(base_price * 1.10)
            fair_price_max = int(base_price * 1.15)
            
            diff = offer_price - fair_price_max
            
            if offer_price > fair_price_max + 20000:
                status = "🔴 溢價過高 (盤子價)"
                advice = f"開價過高。根據數據，合理行情頂標在 {int(fair_price_max/10000)} 萬。建議直接從 {int(fair_price_min/10000)} 萬開始殺價。"
            elif offer_price < base_price:
                status = "⚠️ 價格異常低 (可能有詐)"
                advice = "這價格低於拍賣場成本，極高機率是事故車、泡水車或釣魚假價。請要求出示查定表。"
            else:
                status = "🟢 價格合理"
                advice = "此價格在合理行情範圍內。若車況良好，可以考慮購買。"

            st.markdown(f"""
            <div class="price-box">
            <h4>📊 估價報告：{q_model}</h4>
            <ul>
                <li><b>您的輸入開價：</b> ${offer_price:,}</li>
                <li><b>拍賣場真實底價：</b> ${base_price:,} (成本)</li>
                <li><b>AI 計算合理區間：</b> ${fair_price_min:,} ~ ${fair_price_max:,}</li>
            </ul>
            <hr>
            <h3>⚖️ 判定：{status}</h3>
            <p><b>💬 Brian 的建議：</b><br>{advice}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("💎 **覺得準嗎？** 這是免費試用版。解鎖「任意車款查詢」請訂閱 Pro 方案。")

    # === Tab 3: AI 查定翻譯 (模擬功能) ===
    with tab3:
        st.header("🩺 AI 車況聽診器")
        st.write("看不懂查定表的 W2、X3？上傳照片，AI 幫你翻譯成「維修成本」。")
        
        uploaded_file = st.file_uploader("📸 上傳查定表照片 (範例)", type=['jpg', 'png'])
        
        if uploaded_file is not None:
            with st.spinner("🤖 AI 正在掃描結構代碼..."):
                time.sleep(2.0)
            
            st.success("✅ 分析完成！")
            st.markdown("""
            <div class="report-box">
            <h4>📋 AI 診斷報告</h4>
            <b>1. 結構掃描：</b> <span style='color:red'>🔴 B 柱 (左) W2</span>
            <ul>
                <li><b>AI 解讀：</b> 曾經發生碰撞，板金修復。屬事故車風險。</li>
                <li><b>建議：</b> <b style='color:red'>強烈建議跳過</b>。</li>
            </ul>
            <b>2. 外觀瑕疵：</b> 🟡 前保桿 A3
            <ul>
                <li><b>AI 解讀：</b> 大面積刮傷。預估修復 $4,000。</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🔴 單次報告 $499")
                st.button("👉 取得完整報告")
            with c2:
                st.markdown("### 👑 Pro 會員 $1,499")
                st.button("👉 無限次查詢")

if __name__ == "__main__":
    main()
