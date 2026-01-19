
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="CC 購車精算機", page_icon="✈️")
st.title("✈️ 航太工程師的 CC 購車精算機")

# --- 初始化狀態 ---
if 'unlocked' not in st.session_state: st.session_state.unlocked = False

# --- 名單儲存功能 (存成 CSV) ---
def save_lead(email):
    file_name = "leads.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 如果檔案不存在，先寫入標題
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding='utf-8') as f:
            f.write("Time,Email\n")
    # 寫入資料
    with open(file_name, "a", encoding='utf-8') as f:
        f.write(f"{timestamp},{email}\n")

# --- 側邊欄參數 ---
st.sidebar.header("1. 設定參數")
gas_price = st.sidebar.number_input("汽油版入手價", value=760000)
hybrid_price = st.sidebar.number_input("油電版入手價", value=880000)
km = st.sidebar.slider("年里程 (km)", 5000, 50000, 15000)
year = st.sidebar.slider("預計持有年分", 1, 15, 10)

# --- 簡單計算邏輯 ---
# 這裡做一個簡單的成本試算，讓首頁有東西可以看
# 油耗假設: 汽油版 12km/L, 油電版 21km/L, 油價 31元
gas_fuel_cost = (km * year / 12) * 31
hybrid_fuel_cost = (km * year / 21) * 31
tax_diff = 11920 * year # 稅金相同，這裡僅作示意，可依需求調整

total_gas = gas_price + gas_fuel_cost + tax_diff
total_hybrid = hybrid_price + hybrid_fuel_cost + tax_diff + 49000 # 加一顆大電池錢

diff = total_gas - total_hybrid

# --- 顯示試算結果 ---
st.subheader("📊 初步試算結果")
col1, col2 = st.columns(2)
with col1:
    st.metric("汽油版總花費", f"${int(total_gas):,}")
with col2:
    st.metric("油電版總花費", f"${int(total_hybrid):,}")

if diff > 0:
    st.success(f"💡 建議選擇 **油電版**，預計省下 **${int(diff):,}**")
else:
    st.info(f"💡 建議選擇 **汽油版**，預計省下 **${int(abs(diff)):,}**")

st.markdown("---")

# ==========================================
# 🎯 核心功能：名單收集器 (自動販賣機)
# ==========================================
st.subheader("📉 2026 最新拍賣場成交行情")

# 誘餌預覽表格
preview_data = pd.DataFrame([
    {"年份": 2025, "動力": "油電", "成交價": "71.6萬", "備註": "極新車"},
    {"年份": 2024, "動力": "汽油", "成交價": "57.6萬", "備註": "折舊高"},
    {"年份": "...", "動力": "...", "成交價": "🔒", "備註": "VIP限定"},
])
st.table(preview_data)

if not st.session_state.unlocked:
    # --- 尚未解鎖狀態 ---
    st.warning("🔒 想查看完整的 400+ 筆真實成交行情？")
    st.markdown("這份 **Google Sheets 表格** 包含：")
    st.markdown("👉 **2026 Q1 最新拍賣價**")
    st.markdown("👉 **預估車行收購成本**")
    st.markdown("👉 **找代拍能省多少錢**")
    
    with st.form("unlock_form"):
        email_input = st.text_input("請輸入 Email 立即免費查看", placeholder="name@example.com")
        submit_btn = st.form_submit_button("🔓 立即解鎖", type="primary")
        
        if submit_btn:
            if "@" in email_input:
                st.session_state.unlocked = True
                save_lead(email_input) # 自動儲存名單
                st.rerun()
            else:
                st.error("請輸入正確的 Email 格式")

else:
    # --- 已解鎖狀態 ---
    st.success("✅ 解鎖成功！")
    
    st.markdown("### 👇 點擊下方按鈕，開啟完整行情表：")
    
    # 您的 Google Sheets 連結已經設定在這裡了
    google_sheet_url = "https://docs.google.com/spreadsheets/d/15q0bWKD8PTa01uDZjOQ_fOt5dOTUh0A1D_SrviYP8Lc/edit?gid=0#gid=0"
    
    st.link_button("📊 開啟完整 Google Sheets 行情表", google_sheet_url, type="primary")
    
    st.caption("建議將表格連結加入書籤，資料會不定期更新。")

st.markdown("---")
st.caption("Designed by Aerospace Engineer")
