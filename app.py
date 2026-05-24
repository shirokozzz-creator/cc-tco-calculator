import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.title("Naval Motors 數據庫連線測試 v0.1")

# 建立快取連線，避免網頁重複整理時重複讀取資料庫
@st.cache_data
def get_model_data(model_name):
    # 直接讀取根目錄下的 sqlite 資料庫
    conn = sqlite3.connect("cars_time_series.db")
    query = f"SELECT 成交月份, 出廠年月, 車輛評價, 里程數, 得標價 FROM auctions_time_series WHERE 車系與車型 = '{model_name}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 驗證機制：先撈取資料庫內有哪些現存車型
try:
    conn = sqlite3.connect("cars_time_series.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT 車系與車型 FROM auctions_time_series")
    models = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # 前端車型選擇器
    selected_model = st.selectbox("請選擇要評估的車型", models)
    
    if selected_model:
        # 撈取特定車型數據
        df_car = get_model_data(selected_model)
        
        st.subheader(f"{selected_model} 歷史行情數據量：{len(df_car)} 筆")
        
        # 繪製基本散佈圖
        fig = px.scatter(df_car, x="里程數", y="得標價", color="車輛評價",
                         title=f"{selected_model} 里程 vs 得標價分析")
        st.plotly_chart(fig)
        
        # 資料預覽
        st.dataframe(df_car.head(10))

except Exception as e:
    st.error(f"資料庫讀取失敗，錯誤訊息: {e}")
