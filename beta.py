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

# CSS 優化：科技感配色
st.markdown("""
    <style>
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: bold; height: 3.5em; 
        background-color: #0077b6; color: white; border: none; /* 改用科技藍 */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #0096c7; color: white; transform: translateY(-2px); }
    .highlight { color: #d90429; font-weight: bold; }
    .report-box {
        background-color: #f8f9fa; border-left: 5px solid #0077b6; padding: 15px;
        border-radius: 5px; font-size: 0.95rem; margin-bottom: 20px;
    }
    .price-box {
        background-color: #e9ecef; border-left: 5px solid #2a9d8f; padding: 15px;
        border-radius: 5px; font-size: 0.95rem; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 假資料庫 (模擬 AI 腦袋裡的數據)
# ==========================================
# 這裡我們只放範例，真實運作時會從後端撈取
DEMO_DATA = {
    "RAV4": {"auction": 634000, "market": 750000},
    "Corolla Cross": {"auction": 500000, "market": 630000},
    "Altis": {"auction": 299000, "market": 430000}
}

# ==========================================
# 2. 側邊欄 (你的身份)
# ==========================================
def sidebar_content():
    with st.sidebar:
        st.header("✈️ Brian 航太數據室")
        st.caption("全台唯一：AI 驅動的中古車簽證官")
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
    
    # 三大核心功能
    tab1, tab2, tab3 = st.tabs(["🩺 AI 查定翻譯", "⚖️ 價格合理性分析", "💎 訂閱與方案"])

    # === Tab 1: AI 查定翻譯 (模擬功能) ===
    with tab1:
        st.header("🩺 看不懂查定表？交給 AI")
        st.write("拍賣場的 W2, X3, A1 代表什麼？上傳查定表，AI 幫你翻譯成「維修成本」。")
        
        uploaded_file = st.file_uploader("📸 上傳查定表照片 (範例)", type=['jpg', 'png'])
        
        if uploaded_file is not None:
            # 這裡模擬 AI 思考的過程 (增加儀式感)
            with st.spinner("🤖 AI 正在掃描結構代碼... 分析鈑件狀況..."):
                time.sleep(2.0)
            
            # 顯示模擬的 AI 報告
            st.success("✅ 分析完成！")
            st.markdown("""
            <div class="report-box">
            <h4>📋 AI 診斷報告：Toyota RAV4 (2020)</h4>
            
            <b>1. 結構掃描 (Structural)：</b> <span style='color:red'>🔴 B 柱 (左) W2</span>
            <ul>
                <li><b>AI 解讀：</b> 該處曾發生碰撞，並進行板金修復。屬於「結構性損傷」。</li>
                <li><b>安全風險：</b> 高。可能影響車體剛性與二次碰撞安全性。</li>
                <li><b>工程師建議：</b> <b style='color:red'>強烈建議跳過 (Pass)</b>。</li>
            </ul>
            
            <b>2. 外觀瑕疵 (Cosmetic)：</b> 🟡 前保桿 A3
            <ul>
                <li><b>AI 解讀：</b> 大面積刮傷，已見底漆。</li>
                <li><b>預估復原成本：</b> 約 $3,500 ~ $4,500 (局部烤漆)。</li>
            </ul>
            
            <hr>
            <b>🤖 綜合判定：❌ 不推薦購買</b>
            </div>
            """, unsafe_allow_html=True)
            st.warning("👉 這只是範例展示。想分析您手上的車？請至 Tab 3 訂閱服務。")

    # === Tab 2: 價格合理性分析 (模擬功能) ===
    with tab2:
        st.header("⚖️ 你買貴了嗎？")
        st.write("輸入你在 8891 或車行看到的價格，AI 幫你計算「真實底價」。")
        
        c1, c2 = st.columns(2)
        with c1:
            q_model = st.selectbox("車款", ["Toyota RAV4", "Corolla Cross", "Altis"])
        with c2:
            q_price = st.number_input("車行開價 (萬)", min_value=10, max_value=200, value=75)
        
        if st.button("🚀 啟動 AI 估價模型"):
            with st.spinner("正在調閱 HAA/SAA 近三個月成交大數據..."):
                time.sleep(1.5)
            
            # 簡單的計算邏輯
            target_key = q_model.split(" ")[-1] # 取車型
            if target_key in DEMO_DATA:
                base_price = DEMO_DATA[target_key]["auction"]
                market_price = DEMO_DATA[target_key]["market"]
                offer_price = q_price * 10000
                diff = offer_price - (base_price * 1.15) # 假設合理利潤 15%
                
                status = "🔴 溢價過高 (盤子價)" if diff > 50000 else "🟢 價格合理" if diff < 0 else "🟡 略貴 (可議價)"
                
                st.markdown(f"""
                <div class="price-box">
                <h4>📊 估價結果：{q_model}</h4>
                
                <ul>
                    <li><b>您的輸入開價：</b> ${offer_price:,}</li>
                    <li><b>AI 計算合理行情：</b> ${int(base_price * 1.15):,} (含整備利潤)</li>
                    <li><b>拍賣場真實底價：</b> ${base_price:,} (參考成本)</li>
                </ul>
                <hr>
                <h3>⚖️ 判定：{status}</h3>
                <p><b>💬 AI 議價建議：</b><br>
                "老闆，根據大數據，這年份的行情底價約在 {int(base_price/10000)} 萬。考慮到折舊，{int(offer_price/10000)-2} 萬我現在可以下訂。"</p>
                </div>
                """, unsafe_allow_html=True)

    # === Tab 3: 訂閱與方案 ===
    with tab3:
        st.header("💎 訂閱 Brian 的數據服務")
        st.write("我不賣車，所以我敢說真話。")
        
        c1, c2 = st.columns(2)
        with c1:
            st.image("https://cdn-icons-png.flaticon.com/512/2921/2921222.png", width=80)
            st.subheader("🔴 單次鑑價")
            st.metric("費用", "$499 / 次")
            st.markdown("""
            - ✅ 指定車輛 **真實底價**
            - ✅ **查定表** 風險翻譯
            - ✅ 提供 **議價劇本**
            """)
            st.button("👉 取得單次報告")
            
        with c2:
            st.image("https://cdn-icons-png.flaticon.com/512/6403/6403485.png", width=80)
            st.subheader("👑 Pro 通行證")
            st.metric("費用", "$1,499 / 月")
            st.markdown("""
            - ♾️ **無限次** 查詢底價
            - ♾️ **無限次** 查定表解讀
            - 🚀 **VIP 優先** 審閱
            """)
            st.button("👉 成為 Pro 會員")

        st.info("⚠️ 本服務僅提供數據顧問，不涉及車輛買賣。交易風險請自行評估。")

if __name__ == "__main__":
    main()
