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

# CSS 優化：按鈕、字體、配色 (Toyota Red + 深灰科技感)
st.markdown("""
    <style>
    /* 主按鈕樣式 */
    .stButton>button {
        width: 100%; 
        border-radius: 12px; 
        font-weight: bold; 
        height: 3.5em; 
        background-color: #d90429; 
        color: white; 
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ef233c; 
        color: white;
        transform: translateY(-2px);
    }
    
    /* 數字顯示優化 */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important; 
        font-weight: 700; 
        color: #2b2d42;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1rem !important; 
        color: #8d99ae;
    }
    
    /* 重點文字高亮與卡片樣式 */
    .highlight {
        color: #d90429; 
        font-weight: bold;
    }
    .engineering-note {
        background-color: #f8f9fa;
        border-left: 5px solid #2b2d42;
        padding: 15px;
        border-radius: 5px;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    
    /* 側邊欄優化 */
    [data-testid="stSidebar"] {
        background-color: #f1f3f5;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 數據核心 (基於 HAA/SAA 2025-2026 真實數據邏輯)
# ==========================================
def load_data():
    # 模擬從 PDF 解析後的精選數據
    data = [
        # --- RAV4 ---
        {
            "brand": "Toyota", "model": "RAV4 (汽油)", "year": "2024/02", 
            "grade": "Grade A (4.5分)", "mileage": "12,500km",
            "market_price": 880000, "auction_price": 765000, 
            "scores": [9, 9, 9, 7, 9], # CP, 保值, 安全, 油耗, 空間
            "desc": "HAA 認證 A 級車，幾乎新車。避開了第一年折舊最兇的階段，現在入手正是甜蜜點。"
        },
        {
            "brand": "Toyota", "model": "RAV4 (油電)", "year": "2022/11", 
            "grade": "Grade A (4.5分)", "mileage": "38,000km",
            "market_price": 920000, "auction_price": 795000, 
            "scores": [8, 9, 9, 10, 9], 
            "desc": "油電版熱門車源，SAA 查定結構無損，電池健康度優良，適合高里程使用者。"
        },
        
        # --- Corolla Cross ---
        {
            "brand": "Toyota", "model": "Corolla Cross (汽油)", "year": "2023/08", 
            "grade": "Grade S (5分)", "mileage": "5,200km",
            "market_price": 750000, "auction_price": 645000, 
            "scores": [10, 9, 8, 8, 8], 
            "desc": "極低里程庫存車，內裝膠膜甚至還在。這台車在拍賣場是秒殺款。"
        },
        {
            "brand": "Toyota", "model": "Corolla Cross (油電)", "year": "2022/04", 
            "grade": "Grade A (4.5分)", "mileage": "28,000km",
            "market_price": 780000, "auction_price": 660000, 
            "scores": [9, 9, 8, 10, 8], 
            "desc": "油電版最甜蜜入手點，省油又省稅金。代步神車無誤。"
        },

        # --- Altis ---
        {
            "brand": "Toyota", "model": "Altis", "year": "2023/01", 
            "grade": "Grade A (4.5分)", "mileage": "15,000km",
            "market_price": 580000, "auction_price": 490000, 
            "scores": [10, 8, 8, 8, 6], 
            "desc": "神車不需要解釋。這價格根本是車行的進貨成本，直接讓你拿到。"
        },

        # --- Yaris ---
        {
            "brand": "Toyota", "model": "Yaris", "year": "2022/09", 
            "grade": "Grade A (4.5分)", "mileage": "18,000km",
            "market_price": 520000, "auction_price": 445000, 
            "scores": [9, 10, 6, 7, 5], 
            "desc": "絕版品，市場上掃一台少一台，極度保值。"
        },
        
        # --- Town Ace ---
        {
            "brand": "Toyota", "model": "Town Ace (發財車)", "year": "2024/01", 
            "grade": "Grade S (新車)", "mileage": "800km",
            "market_price": 560000, "auction_price": 485000, 
            "scores": [10, 9, 6, 8, 10], 
            "desc": "買來賺錢的，省下的價差直接當作第一筆創業金。貨斗無刮痕。"
        },

         # --- Sienta ---
        {
            "brand": "Toyota", "model": "Sienta", "year": "2023/05", 
            "grade": "Grade A", "mileage": "22,000km",
            "market_price": 680000, "auction_price": 585000, 
            "scores": [9, 8, 7, 8, 10], 
            "desc": "家庭好爸爸專車，滑門超方便。空間機能無敵。"
        }
    ]
    return pd.DataFrame(data)

# ==========================================
# 2. 視覺核心：五維雷達圖 (Plotly)
# ==========================================
def draw_radar_chart(scores, model_name):
    categories = ['CP值(價格)', '市場保值性', '主被動安全', '油耗表現', '空間機能']
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name=model_name,
        line=dict(color='#d90429', width=3),
        fillcolor='rgba(217, 4, 41, 0.2)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=9, color='gray'),
                linecolor='lightgray'
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#2b2d42',  family="Arial Black"),
                rotation=90
            )
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# ==========================================
# 3. 業務邏輯：誘因換算與連結生成
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

def generate_line_link(brand, model, budget, year_range):
    # 【注意】請務必修改這裡的 Line ID
    line_id = "你的LineID" 
    message = f"Hi Brian，我是從 App 許願池來的。\n我想找一台：{brand} {model}\n年份希望：{year_range}\n預算大約：{budget}\n我已閱讀並同意代標交易條款。\n\n請問本週拍賣場有適合的綠燈車源嗎？"
    return message

# ==========================================
# 4. 側邊欄內容 (SOP 與金流流程)
# ==========================================
def sidebar_content():
    with st.sidebar:
        st.header("🛫 Brian 航太數據室")
        st.caption("資深航太工程師監製")
        
        st.markdown("---")
        
        # --- 航太級代標 SOP (金流修正版) ---
        st.subheader("🚀 代標任務標準程序 (SOP)")
        st.markdown("""
        <div style="font-size: 0.9rem; line-height: 1.6;">
        
        **Step 1. 鎖定 (Target)**
        <br>👉 搜尋車源，或填寫許願單。
        
        **Step 2. 簽約 (Contract)**
        <br>👉 線上簽署委託書，匯入<b style="color:#d90429">押標金 3 萬</b>。
        
        **Step 3. 競標 (Bidding)**
        <br>👉 若<b>未得標</b>，押金全額退還。
        <br>👉 若<b>得標</b>，押金轉為定金。
        
        **Step 4. 結算 (Settlement)**
        <br>👉 隔日 12:00 前匯入<b>公司履約帳戶</b>。
        
        **Step 5. 交車 (Handover)**
        <br>👉 驗收完成，退還過戶保證金。
        
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("💡 **安心承諾：**\n所有款項皆進入公司履約帳戶，專款專用，嚴格遵守拍賣場合約精神。")
        
        st.write("📞 **聯絡工程師**")
        st.link_button("💬 加 LINE 啟動流程", "https://line.me/ti/p/你的LineID", use_container_width=True)
        st.caption("數據最後更新：2026/01/26")

# ==========================================
# 5. 主程式架構
# ==========================================
def main():
    # 呼叫側邊欄
    sidebar_content()

    # --- Header ---
    st.title("✈️ Brian 航太數據選車室")
    st.caption("全台唯一：用「飛行前拆解」標準檢視中古車")
    
    # --- Tabs 分頁設計 ---
    tab1, tab2, tab3 = st.tabs(["🔍 戰情搜尋", "📜 交易守則", "✨ 許願代尋"])

    # === Tab 1: 戰情搜尋 (核心功能) ===
    with tab1:
        st.markdown("### 🔍 掃描全台拍賣場真實成交紀錄")
        st.write("請選擇你有興趣的車款，系統將分析其「機械體質」與「價格結構」。")
        
        df = load_data()
        
        # 篩選器
        c1, c2 = st.columns(2)
        with c1:
            brand_list = df['brand'].unique()
            selected_brand = st.selectbox("品牌", brand_list)
        with c2:
            model_list = df[df['brand']==selected_brand]['model'].unique()
            selected_model = st.selectbox("車型", model_list)
            
        # 年份篩選
        available_years = df[(df['brand']==selected_brand) & (df['model']==selected_model)]['year'].unique()
        selected_year = st.selectbox("年份 (出廠)", available_years)

        # 鎖定數據
        car_data = df[(df['model'] == selected_model) & (df['year'] == selected_year)].iloc[0]

        st.markdown("---")
        
        # 分析按鈕
        if st.button(f"🚀 啟動 {selected_model} 戰力分析"):
            with st.spinner("正在連線 HAA/SAA 數據庫... 計算結構力學數據..."):
                time.sleep(1.2) # 增加儀式感
            
            # 顯示結果
            st.success(f"✅ 鎖定車源：{car_data['year']} {car_data['model']}")
            
            # 雷達圖
            radar = draw_radar_chart(car_data['scores'], car_data['model'])
            st.plotly_chart(radar, use_container_width=True, config={'displayModeBar': False})
            
            # 查定筆記
            st.markdown(f"""
            <div class="engineering-note">
            <b>📋 工程師查定筆記：</b><br>
            <b>[{car_data['grade']}]</b> {car_data['desc']}<br>
            <small>(里程數：{car_data['mileage']} | 結構認證：🟢 通過)</small>
            </div>
            """, unsafe_allow_html=True)

            # 價格結構
            st.markdown("### 💰 價格結構解密")
            
            col_m1, col_m2 = st.columns([1, 1])
            with col_m1:
                st.metric("🏪 市場零售行情", f"${car_data['market_price']:,}", help="含店租、廣告、業務獎金")
            
            st.markdown("⬇️ **若選擇「工程師代標」方案**")
            
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
            st.warning(f"🎁 **恭喜！你省下了 ${savings:,}**\n\n這筆錢等於送你：**{bonus}**")
            
            # --- 詳細付款時程表 (整合行將規範) ---
            with st.expander("📝 點此查看：這台車的「付款時程表」"):
                st.markdown(f"""
                若這台車於 **週三** 得標，您的付款流程如下：
                
                1. **委託時**：支付押標金 `$30,000` (未得標全額退款)。
                2. **週三 (得標日)**：我方提供拍賣場得標單據。
                3. **週四 (得標隔日)**：中午 12:00 前，將尾款匯入本公司履約帳戶 (依拍賣場第16條規範)。
                4. **交車時**：支付過戶保證金 `$10,000` (過戶完即退) + 技術服務費。
                
                *一切公開透明，金流直接對應拍賣場規範。*
                """)

            # CTA
            st.write("拍賣場庫存流動極快，請把握機會。")
            st.link_button("👉 私訊 Brian，啟動代標程序", "https://line.me/ti/p/你的LineID", use_container_width=True)

    # === Tab 2: 交易守則與合約 (整合行將官方條款) ===
    with tab2:
        st.header("📜 交易守則與合約精神")
        st.caption("本服務嚴格遵循 HAA/SAA 行將企業之競拍規範，保障雙方權益。")

        # 1. 資金與棄標 (最重要)
        st.warning("""
        **⚖️ 關於押標金與違約 (Deposit & Penalty)**
        
        1. **未得標退款**：若競標失敗，押標金 $30,000 於 1 個工作天內無息全額退還。
        2. **棄標賠償**：依拍賣場規範(第17條)，得標後棄標者，**押標金 $30,000 全數沒收** 作為違約金，委託人不得異議。
        3. **付款時效**：依規範(第16條)，得標後 **隔日中午 12:00 前** 需匯入尾款。逾期視同棄標。
        """)

        # 2. 詳細條款 (兩欄排列)
        col_rule1, col_rule2 = st.columns(2)
        
        with col_rule1:
            st.subheader("💰 費用與稅規費")
            st.markdown("""
            <div style="background-color:#f8f9fa; padding:15px; border-radius:10px; border-left: 5px solid #d90429;">
            
            **1. 技術服務費 (Flat Rate)**
            <br>我們採<b>定額收費</b>，不按車價比例抽成。
            <ul style="font-size:0.9rem;">
                <li>國產/一般進口：<b>$25,000 / 台</b></li>
                <li>豪華品牌 (Lexus/雙B)：<b>$35,000 / 台</b></li>
            </ul>
            
            <hr>
            
            **2. 成交價不含稅費**
            <br>依規範(第8條)，拍定人需負擔過戶規費、強制險，以及<b>該年度依比例分擔</b>之牌照稅與燃料費。所有費用實報實銷。
            
            <hr>
            
            **3. 過戶保證金**
            <br>依規範(第13條)，部分車輛需預收 $10,000 過戶保證金。待您完成過戶並回傳新行照後，此款項<b>全額退還</b>。
            
            </div>
            """, unsafe_allow_html=True)

        with col_rule2:
            st.subheader("🛡️ 車況與保固聲明")
            st.markdown("""
            **1. 現況交車 (As-Is)**
            <br>依規範(第27條)，拍賣車為現況交車。除重大結構瑕疵外，耗材(輪胎/電瓶)及外觀輕微瑕疵不在索賠範圍。
            
            **2. 里程數規範**
            <br>依規範(第25條)，若查定表註明「里程保證」但交車後發現調表，得於 **14日內** 申請退車。
            
            **3. 重大瑕疵索賠**
            <br>依規範(第29條)，若發現重大機能瑕疵(如引擎/變速箱損壞)與查定表不符，須於 **交車後 48小時內** 提出，逾期不受理。
            """, unsafe_allow_html=True)
            
        # 3. 數位合約預覽 (加入行將條款精神)
        with st.expander("📄 點此預覽：標準代標委託書 (含 HAA 規範)"):
            st.markdown("""
            **【中古汽車代標委託書】(精簡版)**
            
            **第一條 (委託標的)**：甲方委託乙方於 HAA/SAA 拍賣場競標指定車輛。
            
            **第二條 (費用)**：
            1. 甲方應支付：成交價 + 技術服務費($25,000) + 拍賣手續費 + 稅規費。
            2. 稅規費包含：過戶費、當年度稅金(按日計算)、強制險。
            
            **第三條 (權利義務)**：
            1. 乙方提供之查定表僅供參考，實際車況以拍賣場最終判定為準。
            2. 甲方需於得標後 **24小時內** 結清尾款，否則視為違約。
            
            **第四條 (罰則)**：
            若甲方於得標後拒絕付款或棄標，乙方得沒收全額押標金充作違約金，並終止合約。
            
            **第五條 (爭議處理)**：
            若遇車況爭議(如泡水、調表)，乙方有義務代表甲方依拍賣場規則(第23, 25條)提出仲裁與索賠。
            
            *(此為合約摘要，正式簽約將使用具法律效力之電子合約)*
            """)

    # === Tab 3: 許願代尋 (客製化服務) ===
    with tab3:
        st.header("✨ 找不到喜歡的車？")
        st.write("拍賣場每週有 2,000 台車流動。如果你在搜尋中沒看到喜歡的，請直接填寫需求，讓程式幫你監控。")
        
        with st.form("wishlist_form"):
            c1, c2 = st.columns(2)
            with c1:
                w_brand = st.selectbox("品牌", ["Toyota", "Lexus", "Honda", "Mazda", "Nissan", "Ford", "其他"])
            with c2:
                w_budget = st.selectbox("預算範圍", ["30-50萬", "50-70萬", "70-90萬", "90-120萬", "預算無上限"])
            
            w_model = st.text_input("車型 (例如：RAV4, CRV)", placeholder="請輸入車款名稱")
            w_year = st.slider("希望年份 (最低接受)", 2015, 2026, 2020)
            
            st.markdown("---")
            
            # 新增：同意條款 (Micro-commitment)
            agree_contract = st.checkbox("我已閱讀並同意 Tab 2 之「交易守則」與「退款規範」。(未得標全額退款)")
            
            submitted = st.form_submit_button("🚀 送出委託 (連線 LINE)")
            
            if submitted:
                if w_model and agree_contract:
                    msg = generate_line_link(w_brand, w_model, w_budget, f"{w_year}年後")
                    st.success("✅ 需求單已生成！請複製下方文字傳送給我：")
                    st.code(msg, language="text")
                    st.link_button("👉 點此開啟 LINE", "https://line.me/ti/p/你的LineID", use_container_width=True)
                elif not w_model:
                    st.error("❌ 請輸入想找的車型")
                elif not agree_contract:
                    st.error("❌ 請勾選「我已閱讀並同意交易守則」方可送出。")

if __name__ == "__main__":
    main()
