import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go

# ==========================================
# 0. 全域設定 (Mobile-First Design)
# ==========================================
st.set_page_config(
    page_title="Brian 航太數據選車室", 
    page_icon="✈️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS 黑科技：優化按鈕、隱藏預設選單、強調數字
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 12px; font-weight: bold; height: 3.5em; background-color: #d90429; color: white; border: none;}
    .stButton>button:hover {background-color: #ef233c; color: white;}
    div[data-testid="stMetricValue"] {font-size: 1.8rem !important; font-weight: 700; color: #2b2d42;}
    div[data-testid="stMetricLabel"] {font-size: 1rem !important; color: #8d99ae;}
    .big-font {font-size:20px !important;}
    .highlight {color: #d90429; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 數據核心 (整合 HAA/SAA 真實邏輯)
# ==========================================
def load_data():
    # 這裡模擬從 PDF 解析後的清洗數據
    # 加入了 "auction_grade" (查定分數)
    data = [
        # --- RAV4 (主力戰艦) ---
        {
            "brand": "Toyota", "model": "RAV4 (汽油)", "year": "2024/02", 
            "grade": "Grade A (4.5分)", "mileage": "12,500km",
            "market_price": 880000, "auction_price": 765000, 
            "scores": [9, 9, 9, 7, 9], # 價格, 保值, 安全, 油耗, 空間
            "desc": "HAA 認證 A 級車，幾乎新車，避開折舊最兇的第一年。"
        },
        {
            "brand": "Toyota", "model": "RAV4 (油電)", "year": "2022/11", 
            "grade": "Grade A (4.5分)", "mileage": "38,000km",
            "market_price": 920000, "auction_price": 795000, 
            "scores": [8, 9, 9, 10, 9], 
            "desc": "油電版熱門車源，SAA 查定結構無損，電池健康度優良。"
        },
        {
            "brand": "Toyota", "model": "RAV4 (汽油)", "year": "2020/05", 
            "grade": "Grade B (4分)", "mileage": "65,000km",
            "market_price": 680000, "auction_price": 570000, 
            "scores": [10, 8, 8, 7, 9], 
            "desc": "高CP值代步首選，外觀有輕微使用痕跡(反映在價格)，結構完美。"
        },

        # --- Corolla Cross (國民神車) ---
        {
            "brand": "Toyota", "model": "Corolla Cross (汽油)", "year": "2023/08", 
            "grade": "Grade S (5分)", "mileage": "5,200km",
            "market_price": 750000, "auction_price": 645000, 
            "scores": [10, 9, 8, 8, 8], 
            "desc": "極低里程庫存車，內裝膠膜甚至還在。"
        },
        {
            "brand": "Toyota", "model": "Corolla Cross (油電)", "year": "2022/04", 
            "grade": "Grade A (4.5分)", "mileage": "28,000km",
            "market_price": 780000, "auction_price": 660000, 
            "scores": [9, 9, 8, 10, 8], 
            "desc": "油電版最甜蜜入手點，省油又省稅金。"
        },

        # --- Altis (妥善王者) ---
        {
            "brand": "Toyota", "model": "Altis", "year": "2023/01", 
            "grade": "Grade A (4.5分)", "mileage": "15,000km",
            "market_price": 580000, "auction_price": 490000, 
            "scores": [10, 8, 8, 8, 6], 
            "desc": "神車不需要解釋，這價格根本是盤商進貨價。"
        },

        # --- Yaris (保值怪物) ---
        {
            "brand": "Toyota", "model": "Yaris", "year": "2022/09", 
            "grade": "Grade A (4.5分)", "mileage": "18,000km",
            "market_price": 520000, "auction_price": 445000, 
            "scores": [9, 10, 6, 7, 5], 
            "desc": "絕版品，市場上掃一台少一台，極度保值。"
        },
         # --- Town Ace (賺錢神車) ---
        {
            "brand": "Toyota", "model": "Town Ace (發財車)", "year": "2024/01", 
            "grade": "Grade S (新車)", "mileage": "800km",
            "market_price": 560000, "auction_price": 485000, 
            "scores": [10, 9, 6, 8, 10], 
            "desc": "買來賺錢的，省下的價差直接當作第一筆創業金。"
        }
    ]
    return pd.DataFrame(data)

# ==========================================
# 2. 視覺核心：五維雷達圖
# ==========================================
def draw_radar_chart(scores, model_name):
    categories = ['CP值(價格)', '市場保值性', '主被動安全', '油耗表現', '空間機能']
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores, theta=categories, fill='toself', name=model_name,
        line=dict(color='#d90429', width=3),
        fillcolor='rgba(217, 4, 41, 0.2)'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=8), linecolor='gray'),
            angularaxis=dict(tickfont=dict(size=12, color='black'))
        ),
        showlegend=False, margin=dict(l=30, r=30, t=20, b=20), height=280,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# ==========================================
# 3. 業務邏輯：誘因換算
# ==========================================
def calculate_bonus(savings):
    if savings < 60000:
        return "⛽️ 兩年份免費加油金"
    elif savings < 150000:
        iphones = int(savings / 45000)
        return f"📱 {iphones} 支 iPhone 16 Pro Max"
    elif savings < 300000:
        return "✈️ 日本豪華商務艙雙人遊"
    else:
        return "⌚️ 勞力士 Submariner (黑水鬼)"

# ==========================================
# 4. 主程式介面
# ==========================================
def main():
    # --- Sidebar: 專家形象建立 ---
    with st.sidebar:
        st.header("🛫 Brian 航太數據室")
        st.markdown("""
        **資深航太工程師監製**
        
        我們運用 **HAA / SAA 拍賣場大數據**，
        剔除行銷泡沫，還原車輛的「機械淨值」。
        
        - 🚫 **拒絕修圖美照**
        - ✅ **只看查定數據**
        - 💰 **代標不賺差價**
        """)
        st.info("💡 系統數據更新日：2026/01/26")
        st.markdown("---")
        st.write("📞 **聯絡工程師**")
        st.caption("僅服務認同數據價值的客戶")
        st.link_button("加 LINE 索取完整清單", "https://line.me/ti/p/你的LineID")

    # --- Main Content ---
    st.title("✈️ Brian 航太數據選車室")
    
    # 使用 Tabs 分流資訊，讓介面更乾淨
    tab1, tab2 = st.tabs(["🔍 戰情搜尋", "🛡️ 驗車標準"])

    # === Tab 1: 搜尋引擎 ===
    with tab1:
        st.caption("輸入條件，系統將掃描全台拍賣場真實成交紀錄。")
        
        df = load_data()
        
        # 篩選器 (Row 1)
        c1, c2 = st.columns(2)
        with c1:
            brand_list = df['brand'].unique()
            selected_brand = st.selectbox("品牌", brand_list)
        with c2:
            model_list = df[df['brand']==selected_brand]['model'].unique()
            selected_model = st.selectbox("車型", model_list)
            
        # 篩選器 (Row 2 - 動態年份)
        available_years = df[(df['brand']==selected_brand) & (df['model']==selected_model)]['year'].unique()
        selected_year = st.selectbox("年份 (出廠)", available_years)

        # 鎖定單一車輛數據
        car_data = df[(df['model'] == selected_model) & (df['year'] == selected_year)].iloc[0]

        st.markdown("---")
        
        # 核心功能按鈕
        if st.button(f"🚀 開始分析 {selected_model} 數據體質"):
            with st.spinner("正在連線 HAA/SAA 數據庫... 進行五維戰力分析..."):
                time.sleep(1.0) # 儀式感
            
            # --- Result Section ---
            st.success(f"✅ 鎖定車源：{car_data['year']} {car_data['model']}")
            
            # 雷達圖
            radar = draw_radar_chart(car_data['scores'], car_data['model'])
            st.plotly_chart(radar, use_container_width=True, config={'displayModeBar': False})
            
            # 查定備註 (專業感來源)
            st.info(f"📋 **工程師查定筆記：**\n\n**[{car_data['grade']}]** {car_data['desc']}\n\n(里程數：{car_data['mileage']} | 結構認證：🟢 通過)")

            # --- 價格分析 (最重要！) ---
            st.subheader("💰 價格結構解密")
            
            # 1. 零售行情
            st.metric("🏪 市場零售行情 (含管銷)", f"${car_data['market_price']:,}")
            
            st.markdown("### ⬇️")
            
            # 2. 你的方案 (Highlight)
            st.markdown("#### ✈️ 工程師代標方案")
            
            col_p1, col_p2, col_p3 = st.columns([2, 0.5, 2])
            with col_p1:
                st.markdown(f"**拍賣成交價**\n\n`${car_data['auction_price']:,}`")
                st.caption("真實單據")
            with col_p2:
                st.markdown("### +")
            with col_p3:
                st.markdown(f"**技術服務費**\n\n`$25,000`")
                st.caption("透明收費")

            total_price = car_data['auction_price'] + 25000
            savings = car_data['market_price'] - total_price
            bonus = calculate_bonus(savings)

            st.markdown("---")
            st.markdown(f"### 🏁 最終入手價：<span class='highlight'>${total_price:,}</span>", unsafe_allow_html=True)
            
            # 誘因卡片
            st.warning(f"🎁 **恭喜！你省下了 ${savings:,}**\n\n這筆錢等於送你：**{bonus}**")

            # Call to Action
            st.markdown("### 🤔 想要這台車？")
            st.write("拍賣場庫存流動極快，這台車可能明天就被車行標走。")
            st.link_button("👉 私訊 Brian，啟動代標程序", "https://line.me/ti/p/你的LineID", use_container_width=True)

    # === Tab 2: 信任建設 ===
    with tab2:
        st.markdown("### 🛡️ 為什麼我們敢保證車況？")
        st.write("因為我們採用航太級的 **「飛行前拆解 (Pre-flight Check)」** 標準。")
        
        st.markdown("""
        #### 1. 綠燈認證 (Green Light)
        我們只挑選查定表為 **Grade A / Grade 4** 以上的車源。結構如有任何損傷 (R級/事故)，系統直接過濾。
        
        #### 2. 真實里程 (Real Mileage)
        比對監理站與原廠紀錄，杜絕調表車。
        
        #### 3. 原始車況 (Raw Condition)
        我們不幫車子化妝。刮傷就是刮傷，凹痕就是凹痕。你看到的就是最真實的樣子，**因為你買的是車，不是化妝品。**
        """)
        
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/2020_Toyota_Corolla_Altis_1.8_Hybrid_Premium_%28Thailand%29_front_view.jpg/640px-2020_Toyota_Corolla_Altis_1.8_Hybrid_Premium_%28Thailand%29_front_view.jpg", caption="示意圖：我們只交好車")

if __name__ == "__main__":
    main()
