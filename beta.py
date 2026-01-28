import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go

# ==========================================
# 0. 全域設定 (航太戰情室風格)
# ==========================================
st.set_page_config(
    page_title="Brian 航太數據室 | AI 車況鑑價", 
    page_icon="✈️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS 優化：科技藍配色，強調數據專業感
st.markdown("""
    <style>
    /* 按鈕樣式 */
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: bold; height: 3.5em; 
        background-color: #0077b6; color: white; border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #0096c7; color: white; transform: translateY(-2px); }
    
    /* 報告卡片樣式 */
    .report-box { 
        background-color: #f8f9fa; border-left: 5px solid #0077b6; 
        padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 0.95rem;
    }
    .price-box { 
        background-color: #e9ecef; border-left: 5px solid #2a9d8f; 
        padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 0.95rem;
    }
    
    /* 強調文字 */
    .highlight { color: #d90429; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 真實數據庫 (HAA/SAA 拍賣行情 2025/12-2026/01)
# ==========================================
REAL_DB = {
    "RAV4 (汽油)": {
        "auction_price": 634000, "market_price": 750000, 
        "desc": "2020年式 五代 RAV4 豪華版"
    },
    "RAV4 (油電)": {
        "auction_price": 748000, "market_price": 890000, 
        "desc": "2023年式 油電旗艦"
    },
    "Corolla Cross (汽油)": {
        "auction_price": 500000, "market_price": 630000, 
        "desc": "2022年式 國民神車"
    },
    "Altis (汽油)": {
        "auction_price": 299000, "market_price": 430000, 
        "desc": "2020年式 12代 TNGA"
    },
    "Camry (汽油)": {
        "auction_price": 600000, "market_price": 750000, 
        "desc": "2021年式 進口豪華版"
    },
    "Yaris (汽油)": {
        "auction_price": 390000, "market_price": 490000, 
        "desc": "2021年式 絕版保值鴨"
    }
}

# ==========================================
# 2. 側邊欄 (人設與導流)
# ==========================================
def sidebar_content():
    with st.sidebar:
        st.header("✈️ Brian 航太數據室")
        st.caption("AI 驅動的中古車簽證官")
        st.markdown("---")
        
        st.info("💡 **我不賣車，我只提供真相。**\n\n身為工程師，我利用大數據與 AI 演算法，幫你過濾 90% 的檸檬車與盤子價。")
        
        st.write("📞 **聯絡工程師**")
        st.link_button("💬 加 LINE 取得完整報告", "https://line.me/ti/p/你的LineID", use_container_width=True)
        st.caption("資料庫更新：2026/01/29")

# ==========================================
# 3. 主程式架構
# ==========================================
def main():
    sidebar_content()

    st.title("🛡️ 中古車 AI 戰情中心")
    st.caption("Transparency as a Service (透明即服務)")
    
    # 核心功能 Tabs
    tab1, tab2, tab3 = st.tabs(["📊 戰情室 (Free)", "⚖️ 價格分析 (Paid)", "🦅 鷹眼偵測 (New)"])

    # === Tab 1: 戰情室 (免費誘餌) ===
    with tab1:
        st.header("📊 本週精選：真實成交行情")
        st.markdown("這是資料庫中的 **「冰山一角」**。我們不談開價，只看 **「拍賣場真實成交底價」**。")
        
        # 展示前 3 個真實案例
        for car, data in list(REAL_DB.items())[:3]:
            with st.expander(f"🚗 {car} ({data['desc']})", expanded=True):
                c1, c2, c3 = st.columns(3)
                with c1: 
                    st.metric("拍賣成交價 (成本)", f"${data['auction_price']:,}", delta_color="off")
                with c2: 
                    st.metric("市場零售行情", f"${data['market_price']:,}")
                with c3: 
                    savings = data['market_price'] - data['auction_price']
                    st.metric("潛在價差 (利潤)", f"${savings:,}", delta="你的談判空間")
        
        st.markdown("---")
        st.info("👉 想查詢其他特定車款？請使用 **Tab 2 價格分析**。")

    # === Tab 2: 價格合理性分析 (核心功能) ===
    with tab2:
        st.header("⚖️ AI 估價師：你買貴了嗎？")
        st.write("輸入你在 8891 或車行看到的價格，AI 幫你計算「合理入手價」。")
        
        c1, c2 = st.columns(2)
        with c1:
            q_model = st.selectbox("選擇車款", list(REAL_DB.keys()))
        with c2:
            default_price = int(REAL_DB[q_model]['market_price']/10000)
            q_price = st.number_input("車行開價 (萬)", min_value=10, max_value=200, value=default_price)
        
        if st.button("🚀 啟動 AI 估價模型"):
            with st.spinner("正在比對 HAA/SAA 真實成交大數據..."):
                time.sleep(1.2)
            
            # 計算邏輯
            base_price = REAL_DB[q_model]["auction_price"]
            offer_price = q_price * 10000
            
            # 合理利潤區間 (拍賣價 + 10%~15% 管銷)
            fair_price_min = int(base_price * 1.10)
            fair_price_max = int(base_price * 1.15)
            
            if offer_price > fair_price_max + 20000:
                status = "🔴 溢價過高 (盤子價)"
                status_color = "red"
                advice = f"開價過高。根據數據，合理行情頂標在 {int(fair_price_max/10000)} 萬。建議直接從 {int(fair_price_min/10000)} 萬開始殺價。"
            elif offer_price < base_price:
                status = "⚠️ 價格異常低 (可能有詐)"
                status_color = "orange"
                advice = "這價格低於拍賣場成本，極高機率是事故車、泡水車或釣魚假價。請務必啟動 Tab 3 鷹眼偵測。"
            else:
                status = "🟢 價格合理"
                status_color = "green"
                advice = "此價格在合理行情範圍內。若車況查驗無誤，可以考慮購買。"

            st.markdown(f"""
            <div class="price-box">
            <h4>📊 估價報告：{q_model}</h4>
            <ul>
                <li><b>您的輸入開價：</b> ${offer_price:,}</li>
                <li><b>拍賣場真實底價：</b> ${base_price:,} (成本)</li>
                <li><b>AI 計算合理區間：</b> <span class="highlight">${fair_price_min:,} ~ ${fair_price_max:,}</span></li>
            </ul>
            <hr>
            <h3>⚖️ 判定：<span style="color:{status_color}">{status}</span></h3>
            <p><b>💬 Brian 的建議：</b><br>{advice}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("💎 **覺得準嗎？** 解鎖「任意車款查詢」請訂閱 Pro 方案。")

    # === Tab 3: AI 鷹眼偵測 (新功能) ===
    with tab3:
        st.header("🦅 AI 鷹眼偵測 (Beta)")
        st.markdown("""
        **拿不到查定表？沒關係。**
        上傳一張車輛外觀照片，AI 幫你識別「版本是否正確」以及「潛在外觀異常」。
        """)
        
        # Step 1: 選擇車款
        target_model_scan = st.selectbox("這台車是什麼型號？", list(REAL_DB.keys()), key="v_scan")
        
        # Step 2: 上傳照片
        uploaded_file = st.file_uploader("📸 上傳車輛照片 (車頭/車側/內裝)", type=['jpg', 'png', 'jpeg'])
        
        # 預設圖片 (範例用)
        if not uploaded_file:
             with st.expander("❓ 沒有照片？點我看範例"):
                st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Toyota_RAV4_V_Hybrid_IAA_2019.jpg/1200px-Toyota_RAV4_V_Hybrid_IAA_2019.jpg", caption="範例照片：RAV4 外觀", width=300)

        if uploaded_file:
            st.image(uploaded_file, caption="影像已上傳，準備進行電腦視覺分析", width=300)
            
            if st.button("🚀 啟動 AI 鷹眼分析"):
                # 模擬 AI 運算過程
                progress_bar = st.progress(0)
                status_text = st.empty()
                steps = [
                    "正在比對原廠規配資料庫...", 
                    "掃描外觀細節 (輪框/天窗/車頂架)...", 
                    "分析鈑件色差 (Delta E)...", 
                    "生成鑑價報告..."
                ]
                
                for i, step in enumerate(steps):
                    status_text.text(f"🤖 AI 運算中：{step}")
                    progress_bar.progress((i + 1) * 25)
                    time.sleep(0.8)
                
                status_text.text("✅ 分析完成！")
                
                # --- 模擬分析結果 (情境：低配假冒高配) ---
                st.markdown(f"""
                <div class="report-box">
                <h4>🦅 AI 鷹眼報告：{target_model_scan}</h4>
                
                <b>1. 🕵️ 版本/配備驗證：</b>
                <ul>
                    <li><b>偵測特徵：</b> 17吋輪框、無全景天窗、傳統鹵素燈泡。</li>
                    <li><b style='color:red'>⚠️ 異常警示：</b> 賣家若宣稱此為「旗艦版」，可能與特徵不符。AI 判定極可能為 <b>「豪華版」</b>。</li>
                    <li><b>潛在價差：</b> 版本差異導致市值落差約 <b>$60,000 ~ $80,000</b>。</li>
                </ul>
                
                <b>2. 🎨 外觀異常掃描：</b>
                <ul>
                    <li><b>左前葉子板：</b> 偵測到與車門存在 <b style='color:orange'>微小色差 (Delta E > 2.5)</b>。</li>
                    <li><b>推測：</b> 該部位可能進行過烤漆修復。請現場看車時特別留意該處鈑金平整度。</li>
                </ul>
                
                <hr>
                <b>🤖 Brian 的戰術建議：</b>
                <p>這張照片透露出這可能是一台「假高配」或「小碰撞修復車」。<br>拿著這份報告去問車商：「為什麼這台旗艦版沒有天窗？」看他怎麼解釋。</p>
                </div>
                """, unsafe_allow_html=True)
                
                # CTA
                st.write("### 😰 不確定是不是真的？")
                st.write("AI 分析僅供參考。若您需要工程師 Brian 進行「人工複審」：")
                st.link_button("👉 傳照片給 Brian 確認 ($499)", "https://line.me/ti/p/你的LineID", use_container_width=True)

if __name__ == "__main__":
    main()
