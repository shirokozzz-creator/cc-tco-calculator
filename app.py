import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# 1. UI 與系統設定
st.set_page_config(page_title="Naval Motors 資產防禦系統", layout="wide")
st.title("Naval Motors 總體持有成本 (TCO) 決策系統 v0.2")

# 2. 資料庫讀取引擎
@st.cache_data
def get_model_data(model_name):
    conn = sqlite3.connect("cars_time_series.db")
    query = f"SELECT 成交月份, 出廠年月, 車輛評價, 里程數, 得標價 FROM auctions_time_series WHERE 車系與車型 = '{model_name}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 3. 系統初始化與資料庫掃描
try:
    conn = sqlite3.connect("cars_time_series.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT 車系與車型 FROM auctions_time_series")
    models = [row[0] for row in cursor.fetchall()]
    conn.close()
except Exception as e:
    st.error(f"資料庫掛載失敗: {e}")
    st.stop()

# 4. 前端引流與參數輸入區 (側邊欄)
st.sidebar.header("1. 輸入目標車輛現況")
selected_model = st.sidebar.selectbox("評估車型", models, index=models.index('NX200') if 'NX200' in models else 0)
target_mileage = st.sidebar.number_input("目標車輛里程數 (km)", min_value=0, value=85000, step=5000)
dealer_price = st.sidebar.number_input("終端車商開價 (TWD)", min_value=100000, value=850000, step=10000)
is_hybrid = st.sidebar.toggle("此車為 Hybrid 油電混合車型")

st.sidebar.header("2. 財務工程參數")
loan_rate = st.sidebar.slider("預計車貸利率 (%)", 2.0, 16.0, 6.0, 0.5)

# 5. 撈取數據與基礎運算
df_car = get_model_data(selected_model)

if not df_car.empty:
    # 商業邏輯 A：計算合理零售樓地板
    median_auction = df_car['得標價'].median()
    retail_floor = median_auction * 1.10  # 加上 10% 合理管銷利潤
    
    st.subheader(f"🛡️ 模組一：定價黑箱解密 ({selected_model})")
    col1, col2, col3 = st.columns(3)
    col1.metric("系統批發底價中位數", f"${median_auction:,.0f}")
    col2.metric("合理零售樓地板價 (+10%)", f"${retail_floor:,.0f}")
    
    # 釣魚價防呆判定
    price_diff = dealer_price - retail_floor
    if dealer_price < retail_floor:
        col3.metric("價格溢價空間", f"${price_diff:,.0f}")
        st.error(f"⚠️ **高風險釣魚警示**：車商開價 ({dealer_price:,.0f}) 低於拍賣底價加合理利潤的樓地板。極大概率為假自售、調錶或重大事故隱瞞。期望值為負。")
    else:
        col3.metric("價格溢價空間", f"+${price_diff:,.0f}")
        st.success("✅ 開價位於合理套利空間之上，未觸發低價釣魚警示。")

    st.markdown("---")

    # 商業邏輯 B：TCO 總體持有成本與維修黑洞
    st.subheader("⚠️ 模組二：未來三年 TCO 物理衰變預測")
    battery_fund = 60000 if (is_hybrid and target_mileage > 100000) else 0
    routine_maintenance = 42000 # 三年常規保養估值
    
    tco_col1, tco_col2 = st.columns(2)
    with tco_col1:
        st.info(f"**預期大電池汰換準備金：** ${battery_fund:,.0f} TWD")
        if battery_fund > 0:
            st.caption("📌 工程邏輯：里程突破 10 萬公里，大電池進入高頻失效期，系統強制提列風險折現。")
    with tco_col2:
        st.info(f"**三年常規保養預估：** ${routine_maintenance:,.0f} TWD")
        
    st.markdown("---")
    
    # 商業邏輯 C：機會成本暴擊
    st.subheader("📉 模組三：貸款機會成本 (The Opportunity Cost)")
    # 簡化版 ETF 機會成本計算 (年化 7%，單利估算對比)
    etf_return = dealer_price * ((1 + 0.07)**3 - 1)
    
    st.warning(f"""
    如果您選擇全額現金或高利貸款購買此車，相較於將同等資金 ({dealer_price:,.0f} TWD) 投入年化報酬率 7% 的大盤 ETF (如 0050 或 VTI)：
    **三年後，您將產生高達 $ {etf_return:,.0f} TWD 的財富差距損失。**
    這才是這台車真正的隱藏持有成本。
    """)
    
    # 視覺化：模糊化歷史散佈圖
    st.markdown("---")
    st.subheader("📊 模組四：歷史拍賣散佈圖 (數據模糊化處理)")
    df_car['價格(萬)'] = df_car['得標價'] / 10000
    fig = px.scatter(df_car, x="里程數", y="價格(萬)", color="車輛評價", title="里程 vs 拍賣底價 (模糊化)")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("資料庫中無此車型數據。")
