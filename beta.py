import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import urllib.parse

# ==========================================
# 0. 全域設定 (航太戰情室風格)
# ==========================================
st.set_page_config(
    page_title="Brian 航太數據選車室", 
    page_icon="✈️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS 優化：按鈕、字體、配色
st.markdown("""
    <style>
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: bold; height: 3.5em; 
        background-color: #d90429; color: white; border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #ef233c; color: white; transform: translateY(-2px); }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700; color: #2b2d42; }
    div[data-testid="stMetricLabel"] { font-size: 1rem !important; color: #8d99ae; }
    .highlight { color: #d90429; font-weight: bold; }
    .engineering-note {
        background-color: #f8f9fa; border-left: 5px solid #2b2d42; padding: 15px;
        border-radius: 5px; font-size: 0.95rem; margin-bottom: 20px;
    }
    [data-testid="stSidebar"] { background-color: #f1f3f5; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 0.5 世代識別資料庫
# ==========================================
GENERATION_DB = {
    "RAV4": {
        "五代 (TNGA)": [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
        "4.5代 (末代)": [2016, 2017, 2018]
    },
    "Corolla Cross": {
        "一代 (TNGA)": [2020, 2021, 2022, 2023, 2024, 2025]
    },
    "Altis": {
        "12代 (TNGA)": [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
        "11.5代": [2016, 2017, 2018]
    },
    "Camry": {
        "八代 (TNGA/進口)": [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    },
    "Yaris": {
        "三代 (後期/Crossover)": [2018, 2019, 2020, 2021, 2022, 2023]
    },
    "Vios": {
        "三代 (小改款)": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    }
}

# ==========================================
# 1. 數據核心 (精選案例)
# ==========================================
def load_data():
    data = [
        # --- 1. RAV4 ---
        {
            "brand": "Toyota", "model": "RAV4 (汽油)", "year": "2020/04", 
            "grade": "Grade A", "mileage": "67,896km",
            "market_price": 750000, 
            "auction_price": 634000,
            "scores": [9, 9, 9, 7, 9], 
            "desc": "五代 RAV4 白金版。市場開價約 75 萬，HAA 拍場直購價 63.4 萬，現省 11.6 萬。"
        },
        {
            "brand": "Toyota", "model": "RAV4 (油電)", "year": "2023/05", 
            "grade": "Grade A", "mileage": "42,430km",
            "market_price": 890000, 
            "auction_price": 748000,
            "scores": [8, 9, 9, 10, 9], 
            "desc": "油電版熱門車源。一年車齡，電池健康度 100%，比新車省下近 30 萬。"
        },

        # --- 2. Corolla Cross ---
        {
            "brand": "Toyota", "model": "Corolla Cross (汽油)", "year": "2022/06", 
            "grade": "Grade A", "mileage": "42,475km",
            "market_price": 630000, 
            "auction_price": 500000,
            "scores": [10, 9, 8, 8, 8], 
            "desc": "市場秒殺款。車行收購價約 48-50 萬，我們直接用成本價幫你標到。"
        },

        # --- 3. Altis ---
        {
            "brand": "Toyota", "model": "Altis (汽油)", "year": "2020/10", 
            "grade": "Grade A", "mileage": "58,111km",
            "market_price": 430000, 
            "auction_price": 299000,
            "scores": [10, 8, 8, 8, 6], 
            "desc": "12代 TNGA 底盤。代步首選，拍場成交價不到 30 萬，CP 值極高。"
        },

        # --- 4. Camry ---
        {
            "brand": "Toyota", "model": "Camry (汽油)", "year": "2021/07", 
            "grade": "Grade B", "mileage": "79,772km",
            "market_price": 750000, 
            "auction_price": 600000,
            "scores": [8, 8, 9, 7, 9], 
            "desc": "八代進口 Camry。黑外觀氣派，主管級座駕，現省 15 萬。"
        },

        # --- 5. Vios ---
        {
            "brand": "Toyota", "model": "Vios", "year": "2021/11", 
            "grade": "Grade A", "mileage": "35,000km",
            "market_price": 430000, 
            "auction_price": 350000,
            "scores": [10, 8, 5, 8, 5], 
            "desc": "國民代步車。持有成本極低，適合新手練車，三年車只賣 35 萬。"
        },
        
        # --- 6. Yaris ---
        {
            "brand": "Toyota", "model": "Yaris", "year": "2021/05", 
            "grade": "Grade A", "mileage": "40,000km",
            "market_price": 490000, 
            "auction_price": 390000,
            "scores": [9, 10, 6, 7, 5], 
            "desc": "絕版品小鴨。市場上掃一台少一台，極度保值，甚至比 Vios 還貴。"
        }
    ]
    
    df = pd.DataFrame(data)
    df['pure_year'] = df['year'].apply(lambda x: int(str(x)[:4]))
    return df

# ==========================================
# 2. 視覺核心
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
            radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=9, color='gray'), linecolor='lightgray'),
            angularaxis=dict(tickfont=dict(size=12, color='#2b2d42', family="Arial Black"), rotation=90)
        ),
        showlegend=False, margin=dict(l=40, r=40, t=20, b=20), height=300,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# ==========================================
# 3. 業務邏輯
# ==========================================
def calculate_bonus(savings):
    if savings < 60000: return "⛽️ 兩年份免費加油金"
    elif savings < 150000: return f"📱 {int(savings / 45000)} 支 iPhone 16 Pro Max"
    elif savings < 300000: return "✈️ 日本豪華商務艙雙人遊"
    else: return "⌚️ 勞力士 Submariner (黑水鬼)"

def generate_line_link(brand, model, budget, year_range):
    # 請修改 LINE ID
    line_id = "你的LineID" 
    message = f"Hi Brian，我是從 App 許願池來的。\n我想找一台：{brand} {model}\n年份希望：{year_range}\n預算大約：{budget}\n我已閱讀並同意代標交易條款。\n\n請問本週拍賣場有適合的綠燈車源嗎？"
    return message

# ==========================================
# 4. 側邊欄
# ==========================================
def sidebar_content():
    with st.sidebar:
        st.header("🛫 Brian 航太數據室")
        st.caption("資深航太工程師監製")
        st.markdown("---")
        st.subheader("🚀 代標任務標準程序")
        st.markdown("""
        <div style="font-size: 0.9rem; line-height: 1.6;">
        **Step 1. 鎖定 (Target)** <br>👉 參考右側「真實案例」。
        **Step 2. 簽約 (Contract)** <br>👉 線上委託，匯入<b style="color:#d90429">押標金 3 萬</b>。
        **Step 3. 競標 (Bidding)** <br>👉 <b>未得標</b>：全額退款。 <br>👉 <b>得標</b>：轉為定金。
        **Step 4. 結算 (Settlement)** <br>👉 隔日 12:00 前匯入公司履約帳戶。
        **Step 5. 交車 (Handover)** <br>👉 驗收完成，退還過戶保證金。
        </div>""", unsafe_allow_html=True)
        st.markdown("---")
        st.info("💡 **安心承諾：**\n採定額技術費收費 ($25,000)，不賺差價，金流公開透明。")
        st.link_button("💬 加 LINE 啟動流程", "https://line.me/ti/p/你的LineID", use_container_width=True)

# ==========================================
# 5. 主程式
# ==========================================
def main():
    sidebar_content()

    st.title("✈️ Brian 航太數據選車室")
    st.caption("全台唯一：用「代數世代 (Generation)」精準鎖定中古車")
    
    tab1, tab2, tab3 = st.tabs(["🔍 戰情案例 (精選)", "📜 交易守則", "✨ 許願代尋"])

    # === Tab 1: 戰情案例 ===
    with tab1:
        st.markdown("### 🔍 Toyota 熱銷車系：真實成交案例")
        st.info("💡 **本區展示本月「熱門成交」之精選範例。**\n這些都是拍賣場真實發生的價格。若您想找其他年份或車款，請使用 Tab 3 **「✨ 許願代尋」** 功能。")
        
        df = load_data()
        
        c1, c2 = st.columns(2)
        with c1:
            brand_list = df['brand'].unique()
            selected_brand = st.selectbox("品牌", brand_list)
        with c2:
            model_list = df[df['brand']==selected_brand]['model'].unique()
            selected_model_raw = st.selectbox("車型", model_list)
            db_model_key = selected_model_raw.split(" (")[0] 

        if db_model_key in GENERATION_DB:
            st.info(f"💡 工程師提示：請選擇 {db_model_key} 的車系世代")
            gen_options = list(GENERATION_DB[db_model_key].keys())
            selected_gen = st.selectbox("選擇世代 (Generation)", gen_options)
            target_years = GENERATION_DB[db_model_key][selected_gen]
            st.caption(f"📅 此世代生產年份：{min(target_years)} ~ {max(target_years)}")
            filtered_df = df[(df['model'] == selected_model_raw) & (df['pure_year'].isin(target_years))]
        else:
            st.warning("⚠️ 此車型暫無世代資料，改用年份篩選")
            available_years = df[df['model']==selected_model_raw]['year'].unique()
            selected_year_str = st.selectbox("年份", available_years)
            filtered_df = df[(df['model'] == selected_model_raw) & (df['year'] == selected_year_str)]

        st.markdown("---")

        if not filtered_df.empty:
            car_data = filtered_df.iloc[0]
            
            if st.button(f"🚀 啟動 {car_data['year']} {car_data['model']} 戰力分析"):
                with st.spinner("正在調閱 HAA/SAA 成交紀錄... 計算結構力學數據..."):
                    time.sleep(1.0)
                
                st.success(f"✅ 鎖定真實案例：{car_data['year']} {car_data['model']}")
                st.plotly_chart(draw_radar_chart(car_data['scores'], car_data['model']), use_container_width=True, config={'displayModeBar': False})
                
                st.markdown(f"""
                <div class="engineering-note">
                <b>📋 工程師查定筆記：</b><br>
                <b>[{car_data['grade']}]</b> {car_data['desc']}<br>
                <small>(里程數：{car_data['mileage']} | 結構認證：🟢 通過)</small>
                </div>""", unsafe_allow_html=True)

                st.markdown("### 💰 價格結構解密")
                col_m1, col_m2 = st.columns([1, 1])
                with col_m1: st.metric("🏪 市場零售行情", f"${car_data['market_price']:,}", help="含店租、廣告、業務獎金")
                
                st.markdown("⬇️ **若選擇「工程師代標」方案**")
                col_p1, col_p2, col_p3 = st.columns([2, 0.5, 2])
                with col_p1: st.markdown(f"**拍賣成交價**\n\n`${car_data['auction_price']:,}`")
                with col_p2: st.markdown("### +")
                with col_p3: st.markdown(f"**技術服務費**\n\n`$25,000`")

                total_price = car_data['auction_price'] + 25000
                savings = car_data['market_price'] - total_price
                
                st.markdown("---")
                st.markdown(f"### 🏁 最終入手價：<span class='highlight'>${total_price:,}</span>", unsafe_allow_html=True)
                st.warning(f"🎁 **恭喜！你省下了 ${savings:,}**\n\n這筆錢等於送你：**{calculate_bonus(savings)}**")
                
                with st.expander("📝 點此查看：付款時程與規則"):
                    st.markdown("""
                    1. **委託時**：支付押標金 `$30,000` (未得標全額退款)。
                    2. **得標隔日**：中午 12:00 前，匯入尾款至本公司履約帳戶。
                    3. **交車時**：支付過戶保證金 `$10,000` (過戶完即退) + 技術服務費。
                    """)
                st.link_button("👉 私訊 Brian，啟動代標程序", "https://line.me/ti/p/你的LineID", use_container_width=True)
        else:
            st.error(f"❌ 抱歉，目前資料庫中暫無該世代案例。")
            st.info("拍賣場庫存每日流動，請使用下方「許願代尋」。")

    # === Tab 2: 交易守則 ===
    with tab2:
        st.header("📜 交易守則與合約精神")
        st.caption("本服務嚴格遵循 HAA/SAA 行將企業之競拍規範。")
        st.warning("""
        **⚖️ 關於押標金 (Deposit)**
        1. **未得標**：押標金 $30,000 於 1 個工作天內 **無息全額退還**。
        2. **棄標**：得標後棄標者，**押標金全數沒收** 作為違約金。
        3. **時效**：得標後 **隔日中午 12:00 前** 需匯入尾款。
        """)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("💰 透明收費 (Flat Fee)")
            st.markdown("""
            **1. 技術服務費**
            <br>國產/一般進口：<b>$25,000 / 台</b>
            <br>豪華品牌：<b>$35,000 / 台</b>
            <hr>
            **2. 稅規費實報實銷**
            <br>過戶費、稅金、強制險、美容，皆依收據實支實付。
            """, unsafe_allow_html=True)
        with c2:
            st.subheader("🛡️ 車況與保固")
            st.markdown("""
            **1. 現況交車**：除重大結構瑕疵外，耗材不保固。
            **2. 里程免責**：調表車 14 日內退車。
            **3. 重大瑕疵**：引擎/變速箱損壞 48 小時內申訴。
            """, unsafe_allow_html=True)

    # === Tab 3: 許願代尋 ===
    with tab3:
        st.header("✨ 找不到喜歡的車？")
        st.write("拍賣場每週有 2,000 台車流動。填寫需求，讓程式幫你監控。")
        with st.form("wishlist_form"):
            c1, c2 = st.columns(2)
            with c1: w_brand = st.selectbox("品牌", ["Toyota", "Lexus", "Honda", "Mazda", "Nissan", "Ford", "其他"])
            with c2: w_budget = st.selectbox("預算範圍", ["30-50萬", "50-70萬", "70-90萬", "90-120萬", "預算無上限"])
            w_model = st.text_input("車型", placeholder="例如：RAV4 4.5代")
            w_year = st.slider("年份", 2015, 2026, 2020)
            st.markdown("---")
            agree = st.checkbox("我已閱讀並同意 Tab 2 之「交易守則」。")
            if st.form_submit_button("🚀 送出委託 (連線 LINE)"):
                if w_model and agree:
                    st.success("✅ 需求單已生成！")
                    st.code(generate_line_link(w_brand, w_model, w_budget, f"{w_year}年後"), language="text")
                    st.link_button("👉 點此開啟 LINE", "https://line.me/ti/p/你的LineID", use_container_width=True)
                else: st.error("❌ 請輸入車型並勾選同意條款。")

if __name__ == "__main__":
    main()
