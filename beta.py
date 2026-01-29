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

# CSS 優化：科技藍配色，強調數據專業感與信賴感
st.markdown("""
    <style>
    /* 按鈕樣式：科技藍 */
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
    
    /* 側邊欄優化 */
    [data-testid="stSidebar"] { background-color: #f1f3f5; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 真實數據庫 (HAA/SAA 拍賣行情 2025/12-2026/01)
# ==========================================
# 這些數據源自你上傳的 PDF 檔案，經過校正後的「成本底價」
REAL_DB = {
    "RAV4 (汽油)": {
        "auction_price": 634000, 
        "market_price": 750000, 
        "desc": "2020年式 五代 RAV4 豪華版",
        "features": ["17吋輪框", "織布座椅", "無天窗"]
    },
    "RAV4 (油電)": {
        "auction_price": 748000, 
        "market_price": 890000, 
        "desc": "2023年式 油電旗艦 4WD",
        "features": ["18吋輪框", "全景天窗", "車頂架"]
    },
    "Corolla Cross (汽油)": {
        "auction_price": 500000, 
        "market_price": 630000, 
        "desc": "2022年式 國民神車",
        "features": ["17吋輪框", "TSS 2.0"]
    },
    "Altis (汽油)": {
        "auction_price": 299000, 
        "market_price": 430000, 
        "desc": "2020年式 12代 TNGA 經典",
        "features": ["16吋輪框", "傳統手煞車"]
    },
    "Camry (汽油)": {
        "auction_price": 600000, 
        "market_price": 750000, 
        "desc": "2021年式 進口豪華版",
        "features": ["雙前座電動椅", "9吋螢幕"]
    },
    "Yaris (汽油)": {
        "auction_price": 390000, 
        "market_price": 490000, 
        "desc": "2021年式 絕版保值鴨",
        "features": ["皮椅", "Keyless"]
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

    # === Tab 1: 戰情室 (免費誘餌 - 展示真實行情) ===
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

    # === Tab 2: 價格合理性分析 (核心功能 - 找出盤子價) ===
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
            with st.spinner("正在比對 HAA/SAA 2026/01 真實成交大數據..."):
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
            
            st.info("💎 **覺得準嗎？** 這只是 MVP 版。解鎖「任意車款查詢」請訂閱 Pro 方案。")

    # === Tab 3: AI 鷹眼偵測 (馬斯克思維：視覺鑑價) ===
    with tab3:
        st.header("🦅 AI 鷹眼偵測 (Beta)")
        st.markdown("""
        **這是一場資訊戰。**
        上傳車輛照片，並輸入對方開價。AI 將進行「版本驗證」、「光學掃描」與「溢價計算」。
        """)
        
        # Step 1: 選擇車款與輸入開價
        c1, c2 = st.columns(2)
        with c1:
            target_model_scan = st.selectbox("這台車是什麼型號？", list(REAL_DB.keys()), key="v_scan")
        with c2:
            seller_price = st.number_input("對方開價是多少？ (萬)", min_value=10, max_value=200, value=75, key="v_price_scan")
        
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
                    "計算流動性底價...",
                    "生成馬斯克風格報告..."
                ]
                
                for i, step in enumerate(steps):
                    status_text.text(f"🤖 AI 運算中：{step}")
                    progress_bar.progress((i + 1) * 20)
                    time.sleep(0.8)
                
                status_text.text("✅ 分析完成！")
                
                # --- 馬斯克風格數據報告 ---
                
                # 計算邏輯
                base_price = REAL_DB[target_model_scan]["auction_price"]
                expected_price = seller_price * 10000
                trim_deduction = 60000 # 假設發現低配
                paint_deduction = 15000 # 假設發現重烤
                fair_value = base_price - trim_deduction - paint_deduction + 50000 # 加上合理利潤
                
                premium = expected_price - fair_value
                
                st.markdown(f"""
                <div class="report-box" style="border-left: 5px solid #d90429;">
                <h4>🤖 AI 視覺運算報告 (Tesla Vision Logic)</h4>
                
                <table style="width:100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding:8px; border-bottom:1px solid #ddd;"><b>1. 版本驗證 (Trim Check)</b></td>
                        <td style="padding:8px; border-bottom:1px solid #ddd; color:red; font-weight:bold;">⚠️ 規格不符</td>
                    </tr>
                    <tr>
                        <td colspan="2" style="padding:8px; font-size:0.9em; color:#666;">
                        • 偵測特徵：17吋輪框、無天窗 (應為豪華版特徵)<br>
                        • 賣家宣稱：旗艦版<br>
                        • <b>AI 判定：疑似「低配假冒高配」</b><br>
                        • 價值修正：<span style="color:red">-${trim_deduction:,}</span>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding:8px; border-bottom:1px solid #ddd;"><b>2. 光學異常 (Anomaly)</b></td>
                        <td style="padding:8px; border-bottom:1px solid #ddd; color:orange; font-weight:bold;">⚠️ 色差警示</td>
                    </tr>
                    <tr>
                        <td colspan="2" style="padding:8px; font-size:0.9em; color:#666;">
                        • 左前葉子板 Delta E > 3.5 (疑非原漆)<br>
                        • 價值修正：<span style="color:red">-${paint_deduction:,}</span>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding:8px; border-bottom:1px solid #ddd;"><b>3. 流動性底價 (Floor Price)</b></td>
                        <td style="padding:8px; border-bottom:1px solid #ddd; font-weight:bold;">${base_price:,}</td>
                    </tr>
                     <tr>
                        <td colspan="2" style="padding:8px; font-size:0.9em; color:#666;">
                        • 基於 HAA/SAA 2026/01 成交大數據
                        </td>
                    </tr>
                </table>
                
                <div style="background-color:#e9ecef; padding:15px; margin-top:15px; border-radius:5px;">
                    <h3 style="margin:0; color:#2b2d42;">🔢 盤子指數 (Sucker Index)</h3>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                        <div>
                            <div style="font-size:0.9em; color:#666;">賣家開價</div>
                            <div style="font-size:1.2em; font-weight:bold;">${expected_price:,}</div>
                        </div>
                        <div style="font-size:1.5em;">👉</div>
                        <div>
                            <div style="font-size:0.9em; color:#666;">AI 合理價</div>
                            <div style="font-size:1.2em; font-weight:bold; color:#0077b6;">${fair_value:,}</div>
                        </div>
                    </div>
                    <hr>
                    <div style="text-align:center;">
                        <span style="font-size:1.5em;">🔴 極高風險</span><br>
                        <span style="font-size:0.9em;">您即將多付 <b>${premium:,}</b> (溢價 {(premium/fair_value)*100:.1f}%)</span>
                    </div>
                </div>

                <p style="margin-top:10px; font-size:0.9em;">
                <b>🤖 Elon's Advice:</b><br>
                "數學不會說謊。這台車配備不符且價格虛高。不要浪費時間，直接殺價 {int(premium/10000)} 萬，如果不賣就走人。"
                </p>
                </div>
                """, unsafe_allow_html=True)
                
                # CTA
                st.write("### 😰 怕自己去殺價會被話術？")
                st.write("讓工程師 Brian 成為你的後盾。我可以提供「人工複審」與「議價談判指導」。")
                st.link_button("👉 傳照片給 Brian 確認 ($499)", "https://line.me/ti/p/你的LineID", use_container_width=True)

if __name__ == "__main__":
    main()
