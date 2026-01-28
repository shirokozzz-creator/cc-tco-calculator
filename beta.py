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

# CSS 優化：科技感配色 (深藍/科技灰)
st.markdown("""
    <style>
    /* 按鈕樣式：科技藍 */
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: bold; height: 3.5em; 
        background-color: #0077b6; color: white; border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #0096c7; color: white; transform: translateY(-2px); }
    
    /* 報告區塊樣式 */
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
# 1. 真實數據庫 (從 PDF 提取的 HAA/SAA 真實行情)
# ==========================================
# 這是你的核心資產，目前採 Hard-code 方式，未來可接 Google Sheets
REAL_DB = {
    "RAV4 (汽油)": {
        "auction_price": 634000, # 參考 2020/04 成交
        "market_price": 750000,  # 8891 平均開價
        "desc": "2020年式 五代 RAV4 豪華版"
    },
    "RAV4 (油電)": {
        "auction_price": 748000, # 參考 2023/05 成交
        "market_price": 890000,
        "desc": "2023年式 油電旗艦"
    },
    "Corolla Cross (汽油)": {
        "auction_price": 500000, # 參考 2022/06 成交
        "market_price": 630000,
        "desc": "2022年式 國民神車"
    },
    "Altis (汽油)": {
        "auction_price": 299000, # 參考 2020/10 成交
        "market_price": 430000,
        "desc": "2020年式 12代 TNGA"
    },
    "Camry (汽油)": {
        "auction_price": 600000, # 參考 2021/07 成交
        "market_price": 750000,
        "desc": "2021年式 進口豪華版"
    },
    "Yaris (汽油)": {
        "auction_price": 390000, # 參考 2021/05 成交
        "market_price": 490000,
        "desc": "2021年式 絕版保值鴨"
    }
}

# ==========================================
# 2. 側邊欄 (人設與聲明)
# ==========================================
def sidebar_content():
    with st.sidebar:
        st.header("✈️ Brian 航太數據室")
        st.caption("AI 驅動的中古車簽證官")
        st.markdown("---")
        
        st.info("💡 **我不賣車，我只提供真相。**\n\n身為工程師，我利用大數據與 AI 演算法，幫你過濾 90% 的檸檬車與盤子價。")
        
        st.write("📞 **聯絡工程師**")
        st.link_button("💬 加 LINE 取得完整報告", "https://line.me/ti/p/你的LineID", use_container_width=True)
        st.caption("數據來源：HAA/SAA 真實成交紀錄 (2025/12 - 2026/01)")

# ==========================================
# 3. 業務邏輯函式
# ==========================================
def generate_line_msg(topic, content):
    line_id = "你的LineID"
    msg = f"Hi Brian，我使用了 App 的【{topic}】功能。\n{content}\n請問能幫我做進一步的人工複審嗎？"
    return msg

# ==========================================
# 4. 主程式架構
# ==========================================
def main():
    sidebar_content()

    st.title("🛡️ 中古車 AI 戰情中心")
    st.caption("Transparency as a Service (透明即服務)")
    
    # 三大核心功能 Tab
    tab1, tab2, tab3 = st.tabs(["📊 戰情室 (Free)", "⚖️ 價格分析 (Paid)", "🩺 查定翻譯 (Paid)"])

    # === Tab 1: 戰情室 (免費誘餌) ===
    with tab1:
        st.header("📊 本週精選：真實成交行情")
        st.markdown("""
        這是資料庫中的 **「冰山一角」**。
        我們不談「開價」，我們只看 **「拍賣場真實成交底價」**。
        """)
        
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
            # 使用真實資料庫的選項
            q_model = st.selectbox("選擇車款", list(REAL_DB.keys()))
        with c2:
            # 預設值抓市場價
            default_price = int(REAL_DB[q_model]['market_price']/10000)
            q_price = st.number_input("車行開價 (萬)", min_value=10, max_value=200, value=default_price)
        
        if st.button("🚀 啟動 AI 估價模型"):
            with st.spinner("正在比對 HAA/SAA 真實成交大數據..."):
                time.sleep(1.2)
            
            # 計算邏輯
            base_price = REAL_DB[q_model]["auction_price"]
            offer_price = q_price * 10000
            
            # 假設合理利潤區間 (拍賣價 + 10%~15% 管銷)
            fair_price_min = int(base_price * 1.10)
            fair_price_max = int(base_price * 1.15)
            
            # 判定狀態
            if offer_price > fair_price_max + 20000:
                status = "🔴 溢價過高 (盤子價)"
                status_color = "red"
                advice = f"開價過高。根據數據，合理行情頂標在 {int(fair_price_max/10000)} 萬。建議直接從 {int(fair_price_min/10000)} 萬開始殺價。"
            elif offer_price < base_price:
                status = "⚠️ 價格異常低 (可能有詐)"
                status_color = "orange"
                advice = "這價格低於拍賣場成本，極高機率是事故車、泡水車或釣魚假價。請務必要求出示查定表。"
            else:
                status = "🟢 價格合理"
                status_color = "green"
                advice = "此價格在合理行情範圍內。若車況查驗無誤，可以考慮購買。"

            # 顯示結果卡片
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

    # === Tab 3: AI 查定翻譯 (圖片上傳功能) ===
    with tab3:
        st.header("🩺 AI 車況聽診器")
        st.markdown("""
        拍賣場的查定表就像醫生的病歷，充滿了行話 (W2, X3, A1)。
        **看不懂沒關係，拍照上傳，AI 幫你翻譯成「維修成本」。**
        """)
        
        # 1. 檔案上傳區
        uploaded_file = st.file_uploader("📸 請上傳查定表或車況照片 (JPG/PNG)", type=['jpg', 'png', 'jpeg'])
        
        # 2. 範例圖
        if not uploaded_file:
            with st.expander("❓ 不知道要傳什麼？點我看範例"):
                st.image("https://www.sinjang.com.tw/Portal/Images/Car_C.jpg", caption="標準 HAA 查定表範例", width=300)

        # 3. 處理上傳圖片與模擬分析
        if uploaded_file is not None:
            st.image(uploaded_file, caption="您的圖片已上傳", width=300)
            
            if st.button("🚀 開始 AI 結構掃描"):
                # 模擬進度條
                progress_bar = st.progress(0)
                status_text = st.empty()
                steps = ["正在進行 OCR 文字識別...", "偵測車體結構代碼 (W/X/U)...", "比對 HAA/SAA 瑕疵資料庫...", "計算預估維修成本...", "生成最終報告..."]
                
                for i, step in enumerate(steps):
                    status_text.text(f"🤖 AI 運算中：{step}")
                    progress_bar.progress((i + 1) * 20)
                    time.sleep(0.6)
                
                status_text.text("✅ 分析完成！")
                
                # --- 模擬分析結果 (教育客戶用) ---
                st.markdown("""
                <div class="report-box">
                <h4>📋 AI 診斷報告</h4>
                <div style="background-color:#ffe6e6; padding:10px; border-radius:5px; margin-bottom:10px;">
                <b>⚠️ 警告：偵測到潛在結構風險！</b>
                </div>
                
                <b>1. 左側 B 柱：標記 [W2]</b>
                <ul>
                    <li><b>解讀：</b> 該處曾發生碰撞，並進行「板金修復」。</li>
                    <li><b>影響：</b> B柱為車輛核心剛性結構，修復後可能影響二次碰撞的安全性。</li>
                    <li><b>判讀：</b> 此為 <b>R級 (修復歷)</b> 或 <b>C級</b> 車輛。</li>
                </ul>
                
                <b>2. 後車廂底板：標記 [XX]</b>
                <ul>
                    <li><b>解讀：</b> 更換鈑件。推測曾發生追尾事故。</li>
                </ul>
                
                <hr>
                <b>💰 估值影響：</b>
                此車況應低於行情 <b>15%~20%</b>。若您購買的價格沒有便宜這麼多，<b>您買貴了</b>。
                
                <br><br>
                <b>🤖 AI 建議：</b> 此車況複雜，結構有疑慮，建議不要貿然下單。
                </div>
                """, unsafe_allow_html=True)
                
                # CTA: 導流到真人諮詢
                st.markdown("### 😰 覺得怕怕的？")
                st.write("AI 分析僅供參考 (此為模擬範例)，若您手上的單據需要工程師 Brian 親自為您把關：")
                
                msg_content = generate_line_msg("查定表翻譯", "我上傳了一張圖片，AI 顯示有結構風險，請幫我確認。")
                # 這裡需要對 msg_content 進行 url encode，但為了簡化，直接放連結
                st.link_button("👉 傳送這張圖給 Brian (真人複審 $499)", "https://line.me/ti/p/你的LineID", use_container_width=True)

if __name__ == "__main__":
    main()
