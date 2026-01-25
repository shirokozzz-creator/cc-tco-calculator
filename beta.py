import streamlit as st
import pandas as pd
import time
import math
import plotly.graph_objects as go # 引入新的繪圖神器

# ==========================================
# 0. 全域設定
# ==========================================
st.set_page_config(
    page_title="Brian 航太數據選車室", 
    page_icon="✈️", 
    layout="centered"
)

# CSS 美化：黑科技風格
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 12px; font-weight: bold; height: 3em; background-color: #FF4B4B; color: white;}
    div[data-testid="stMetricValue"] {font-size: 1.4rem !important;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 數據庫 + 五維戰力數據
# ==========================================
def load_data():
    # 我們不放圖了，我們放「分數」 (1-10分)
    # 評分維度：CP值(價格), 保值性, 安全性, 油耗, 空間
    data = [
        # --- RAV4 ---
        {
            "brand": "Toyota", "model": "RAV4 (汽油)", "year": "2023/11", 
            "spec": "黑色 | 28,000km", "market_price": 820000, "auction_price": 710000, 
            "scores": [9, 8, 9, 7, 9], # CP, 保值, 安全, 油耗, 空間
            "desc": "高CP值選擇，空間大，但油耗普通。"
        },
        {
            "brand": "Toyota", "model": "RAV4 (油電)", "year": "2022/05", 
            "spec": "白色 | 45,000km", "market_price": 920000, "auction_price": 800000, 
            "scores": [8, 9, 9, 10, 9], 
            "desc": "油耗表現無敵，高里程首選。"
        },

        # --- Corolla Cross ---
        {
            "brand": "Toyota", "model": "Corolla Cross (汽油)", "year": "2024/01", 
            "spec": "灰色 | 9,800km", "market_price": 760000, "auction_price": 660000, 
            "scores": [10, 9, 8, 8, 8], 
            "desc": "國民神車，性價比之王，閉眼買都不會錯。"
        },
        {
            "brand": "Toyota", "model": "Corolla Cross (油電)", "year": "2023/06", 
            "spec": "藍色 | 25,000km", "market_price": 830000, "auction_price": 725000, 
            "scores": [9, 9, 8, 10, 8], 
            "desc": "省油好開，市區代步無敵手。"
        },

        # --- Altis ---
        {
            "brand": "Toyota", "model": "Altis", "year": "2023/04", 
            "spec": "白色 | 18,000km", "market_price": 580000, "auction_price": 500000, 
            "scores": [10, 8, 8, 8, 6], 
            "desc": "除了空間小一點，這台車沒有缺點。"
        },

        # --- Yaris ---
        {
            "brand": "Toyota", "model": "Yaris", "year": "2023/02", 
            "spec": "黃色 | 15,000km", "market_price": 520000, "auction_price": 450000, 
            "scores": [9, 10, 6, 7, 5], 
            "desc": "絕版保值神車，比股票還穩。"
        }
    ]
    return pd.DataFrame(data)

# ==========================================
# 2. 核心技術：繪製雷達圖 (取代照片)
# ==========================================
def draw_radar_chart(scores, model_name):
    categories = ['價格優勢', '保值性', '安全性', '油耗表現', '空間機能']
    
    fig = go.Figure()

    # 畫出數據層
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name=model_name,
        line=dict(color='#FF4B4B', width=3),
        fillcolor='rgba(255, 75, 75, 0.3)'
    ))

    # 美化圖表 (移除多餘標籤，讓它看起來像儀表板)
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10], # 分數 0-10
                tickfont=dict(color='gray', size=8),
                linecolor='gray'
            ),
            angularaxis=dict(
                tickfont=dict(color='black', size=14, family="Arial Black"),
                rotation=90
            )
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=300, # 高度設定
        paper_bgcolor='rgba(0,0,0,0)', # 背景透明
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# ==========================================
# 3. 輔助函式
# ==========================================
def calculate_bonus(savings):
    if savings < 50000:
        return "💰 兩年份的加油金"
    elif savings < 150000:
        iphones = int(savings / 45000)
        return f"📱 {iphones} 支 iPhone 16 Pro Max"
    elif savings < 300000:
        return "✈️ 日本豪華雙人遊 (商務艙)"
    else:
        return "⌚️ 勞力士黑水鬼 (頭期款)"

# ==========================================
# 4. 主程式
# ==========================================
def main():
    # --- Header ---
    st.title("✈️ Brian 航太數據選車室")
    st.caption("資深航太工程師監製 | 拒絕美圖，只看數據戰力")
    
    with st.expander("💡 為什麼我們不放車子照片？"):
        st.markdown("""
        **因為照片會騙人，但數據不會。**
        車商用美肌濾鏡掩蓋缺點，我們用**雷達圖**還原車輛本質。
        我們要你看的是**「機械體質」**，而不是打蠟亮不亮。
        """)

    # --- Input Section ---
    st.markdown("---")
    st.subheader("🔍 啟動車輛戰力分析")
    
    df = load_data()
    
    # 選擇器
    col1, col2 = st.columns(2)
    with col1:
        selected_model = st.selectbox("選擇車型", df['model'].unique())
    with col2:
        available_years = df[df['model'] == selected_model]['year'].unique()
        selected_year = st.selectbox("選擇年份", available_years)

    car_data = df[(df['model'] == selected_model) & (df['year'] == selected_year)].iloc[0]
    
    # --- Analysis Engine ---
    if st.button(f"🚀 掃描 {selected_model} 綜合戰力"):
        with st.spinner("正在計算五維力學數據..."):
            time.sleep(0.8) 
            
        # 計算價格
        my_fee = 25000
        total_engineer_price = car_data['auction_price'] + my_fee
        savings = car_data['market_price'] - total_engineer_price
        bonus_text = calculate_bonus(savings)
        
        # --- 雷達圖展示區 (這是你的新武器) ---
        st.success(f"✅ 戰力分析完成：{car_data['year']} {car_data['model']}")
        
        # 呼叫畫圖函式
        radar_fig = draw_radar_chart(car_data['scores'], car_data['model'])
        st.plotly_chart(radar_fig, use_container_width=True, config={'displayModeBar': False})
        
        st.info(f"📌 **工程師點評：** {car_data['desc']}")

        # --- 價格分析 ---
        st.subheader("📊 價格結構分析")
        
        st.metric(label="🏪 市場零售行情", value=f"${car_data['market_price']:,}")
        
        st.markdown("⬇️ **工程師代標方案 (Cost Breakdown)**")
        
        c1, c2, c3 = st.columns([2, 0.5, 2])
        with c1:
            st.markdown(f"**拍賣場成交價**\n\n `${car_data['auction_price']:,}`")
            st.caption("實報實銷")
        with c2:
            st.markdown("### +")
        with c3:
            st.markdown(f"**Brian 技術費**\n\n `${my_fee:,}`")
            st.caption("透明代標")
            
        st.markdown("---")
        st.markdown(f"### 🚀 工程師入手總價：<span style='color:#d90429'>${total_engineer_price:,}</span>", unsafe_allow_html=True)
        st.success(f"🎉 **現省金額：${savings:,}** \n\n (這筆錢等於送你：{bonus_text})")

        # --- CTA ---
        st.markdown("### 🤔 喜歡這台車的「數據體質」？")
        st.write("如果你也認同買車看數據不看照片，歡迎索取詳細報價。")
        
        st.link_button(
            label="👉 私訊 Brian，索取「批發車源表」",
            url="https://line.me/ti/p/你的LineID", 
            use_container_width=True
        )

if __name__ == "__main__":
    main()
