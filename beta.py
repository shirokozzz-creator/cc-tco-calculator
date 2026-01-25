import streamlit as st
import time

# ==========================================
# 0. 全域設定
# ==========================================
st.set_page_config(
    page_title="Brian 航太數據選車室", 
    page_icon="✈️", 
    layout="centered" # 手機版瀏覽體驗最佳
)

# CSS 美化：讓按鈕更像 App，優化數字顯示
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 12px; font-weight: bold; height: 3em; background-color: #FF4B4B; color: white;}
    .reportview-container {margin-top: -2em;}
    div[data-testid="stMetricValue"] {font-size: 1.6rem !important;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 頭部：安全版人設建立
# ==========================================
def header_section():
    st.title("✈️ Brian 航太數據選車室")
    st.caption("資深航太工程師監製 | 拒絕行銷話術，只看機械淨值")
    
    with st.expander("💡 為什麼工程師買車不找車行？"):
        st.markdown("""
        **因為我們懂得計算「成本結構」。**
        
        一般零售價包含：店租、人事、廣告、美容、保固風險。
        但如果你懂看**「原始查定表」**，你可以直接用**「批發價」**入手。
        
        **我不是車商，我是你的購車技術顧問。**
        **代標不賺差價，只收固定技術費。**
        """)

# ==========================================
# 2. 核心：智能報價單系統
# ==========================================
def quote_engine():
    st.markdown("---")
    st.subheader("🔍 查詢「工程師建議入手價」")
    st.write("輸入你的需求，系統將計算目前拍賣場的真實行情。")
    
    # 輸入區
    col1, col2 = st.columns(2)
    with col1:
        budget = st.selectbox("預算範圍", ["50-60萬", "60-75萬", "75-90萬"])
    with col2:
        model_type = st.selectbox("偏好車型", ["Corolla Cross (神車)", "RAV4 (汽油版)", "RAV4 (油電版)"])

    # 計算按鈕
    if st.button("🚀 開始計算 (數據連線中...)"):
        with st.spinner("正在掃描全台拍賣場數據庫..."):
            time.sleep(1.2) # 增加運算的儀式感
            
        # --- 數據邏輯 (這是你的口袋名單，可隨時調整) ---
        if "RAV4 (汽油版)" in model_type:
            target_car = "2022 RAV4 2.0 旗艦版"
            market_price = 850000  # 車行零售行情
            auction_price = 695000 # 拍賣場行情
            my_fee = 25000         # 你的技術費
            bonus_item = "📱 4 支 iPhone 16"
            img_url = "https://images.unsplash.com/photo-1594502184342-28ef379c3727?auto=format&fit=crop&q=80&w=2672"
            
        elif "RAV4 (油電版)" in model_type:
            target_car = "2021 RAV4 2.5 Hybrid"
            market_price = 920000
            auction_price = 780000
            my_fee = 25000
            bonus_item = "✈️ 日本豪華雙人遊"
            img_url = "https://images.unsplash.com/photo-1626077388041-33f1140cea4d?auto=format&fit=crop&q=80&w=2670"
            
        else: # Corolla Cross
            target_car = "2022 Corolla Cross 豪華"
            market_price = 680000
            auction_price = 560000
            my_fee = 25000
            bonus_item = "💰 一年份的加油金"
            img_url = "https://images.unsplash.com/photo-1621007947382-bb3c3968e3bb?auto=format&fit=crop&q=80&w=2670"

        # 計算結果
        total_engineer_price = auction_price + my_fee
        save_amount = market_price - total_engineer_price

        # --- 結果展示區 ---
        st.markdown("---")
        st.success(f"✅ 配對成功：{target_car}")
        st.image(img_url, caption="示意圖：我們只找原版件、綠燈認證車源", use_container_width=True)

        # 重點：價格結構拆解 (最穩健的護身符)
        st.subheader("📊 價格結構分析")
        
        # 1. 市場行情 (對照組 - 不攻擊，只列事實)
        st.metric(
            label="🏪 一般車行零售行情", 
            value=f"${market_price:,}",
            help="包含：店面租金、業務獎金、廣告費、美容費、保固風險成本"
        )
        
        st.markdown("⬇️ **若選擇「工程師代標」方案 (Cost Breakdown)**")
        
        # 2. 你的報價 (實驗組 - 透明結構)
        c1, c2, c3 = st.columns([2, 0.5, 2])
        with c1:
            st.markdown(f"**拍賣場成交價**\n\n `${auction_price:,}`")
            st.caption("實報實銷，附單據")
        with c2:
            st.markdown("### +")
        with c3:
            st.markdown(f"**Brian 技術費**\n\n `${my_fee:,}`")
            st.caption("代標/驗車/過戶")
            
        st.markdown("---")
        # 3. 最終結果與誘因
        st.markdown(f"### 🚀 工程師入手總價：<span style='color:#d90429'>${total_engineer_price:,}</span>", unsafe_allow_html=True)
        
        # iPhone 貨幣轉換
        st.info(f"🎉 **與市場價差：${save_amount:,}** \n\n (這筆錢等於送你：{bonus_item})")

        # --- CTA 行動呼籲區域 ---
        st.markdown("### 🤔 想索取這份報價單？")
        st.write("我是工程師，我不玩話術。每週二、四我會整理一份**「符合綠燈標準」**的批發車源表。")
        
        with st.expander("點我看「代標服務」安全流程"):
            st.markdown("""
            1. **委託**：確認目標車型與預算。
            2. **尋車**：透過程式篩選拍賣場「綠燈認證」好車。
            3. **出價**：提供原始查定表 (Condition Report)，你確認後才出價。
            4. **透明**：**成交價多少，你就匯多少給拍賣場**，我只拿我的技術費。
            """)
        
        # 請記得把下方的 URL 換成你的 LINE 連結
        st.link_button(
            label="👉 私訊 Brian，索取本週「批發車源表」",
            url="https://line.me/ti/p/你的LineID", 
            use_container_width=True
        )
        st.caption("名額有限，僅服務認同數據價值的買家")

# ==========================================
# 主程式
# ==========================================
if __name__ == "__main__":
    header_section()
    quote_engine()
    
    # 頁尾版權宣告 (簡潔)
    st.markdown("---")
    st.caption("© 2024 Brian Aero-Data Lab. All rights reserved. 數據僅供參考，實際成交價依拍賣場當日行情為準。")
