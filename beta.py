import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
import time

# ==========================================
# 0. 核心設定 (已修復深色模式 Bug)
# ==========================================
st.set_page_config(page_title="RAV4 世代戰情室 | 流量密碼生成器", page_icon="🚙", layout="centered")

st.markdown("""
    <style>
    .big-stat { font-size: 2em; font-weight: bold; }
    
    /* 修復重點：加入 color: #333333; 強制字體變深色 */
    .vs-box { 
        background-color: #f0f2f6; 
        padding: 20px; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        color: #333333; 
    }
    
    .script-box { 
        background-color: #e3f2fd; 
        padding: 20px; 
        border-left: 5px solid #2196f3; 
        font-family: "Microsoft JhengHei";
        color: #333333; /* 強制深色字 */
    }
    
    .stButton>button { width: 100%; border-radius: 8px; background-color: #d32f2f; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 邏輯核心
# ==========================================
def calculate_dilemma(gen5_price, gen6_est_price, wait_months):
    # 簡單的數學邏輯
    price_diff = gen6_est_price - gen5_price
    time_cost = wait_months * 1.5 # 假設一個月用車價值 1.5 萬
    
    return price_diff, time_cost

def generate_video_script(api_key, gen5_price, gen6_est_price, wait_months, verdict):
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        你現在是汽車自媒體創作者 Brian。請寫一個 30 秒的短影音腳本 (Tiktok/Reels 風格)。
        主題：到底該抄底買 RAV4 5代，還是等 6代？
        
        數據：
        - 5代現在買只要：{gen5_price} 萬 (末代優惠)
        - 6代預估售價：{gen6_est_price} 萬 (漲價)
        - 需等待時間：{wait_months} 個月
        - AI 結論：{verdict}
        
        腳本結構：
        1. 鉤子 (0-3秒)：用一句話抓住想買 RAV4 的人。
        2. 痛點 (3-15秒)：分析價差和等待成本。
        3. 爆點 (15-25秒)：揭露 AI 算出來的真相 (TCO)。
        4. 結尾 (25-30秒)：引導留言 (例如：想知道 6 代詳細規格？留言『想知道』)。
        
        語氣：犀利、快節奏、揭密感。
        """
        response = model.generate_content(prompt)
        return response.text
    except:
        return "⚠️ AI 連線忙碌中，請稍後再試。"

# ==========================================
# 2. UI 介面
# ==========================================
def main():
    # 嘗試從 Secrets 讀取 Key，如果沒有就顯示輸入框
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        key_status = "✅ AI 已連線"
    else:
        api_key = None
        key_status = "⚠️ 未連線"

    with st.sidebar:
        st.header(f"⚙️ 設定 ({key_status})")
        if not api_key:
            api_key = st.text_input("Google API Key", type="password")
            
        st.markdown("---")
        st.caption("設定你的預測模型")
        
        gen5_price = st.number_input("5代 RAV4 成交價 (萬)", 90, 140, 110)
        gen6_est_price = st.slider("預估 6代 上市價 (萬)", 110, 180, 135)
        wait_months = st.slider("預估等待月數", 1, 24, 6)

    st.title("🚙 RAV4 世代大對決 (5代 vs 6代)")
    st.markdown("### 拍片主題：現在抄底 5 代，還是苦等 6 代？")

    # 1. 視覺化對決
    col1, col2 = st.columns(2)
    with col1:
        st.info("📉 **5代 (末代王者)**")
        st.metric("目前行情", f"{gen5_price} 萬", "優惠折價中")
        
    with col2:
        st.error("🚀 **6代 (未來戰士)**")
        st.metric("預估售價", f"{gen6_est_price} 萬", f"漲 {gen6_est_price - gen5_price} 萬", delta_color="inverse")

    # 2. 計算結果
    price_diff, time_cost = calculate_dilemma(gen5_price, gen6_est_price, wait_months)
    total_cost_wait = (gen6_est_price - gen5_price) + time_cost
    
    if total_cost_wait > 30: 
        verdict = "現在買 5 代！這價差太大了，等 6 代是盤子。"
        verdict_color = "green"
    else:
        verdict = "絕對要等 6 代！5 代買了就變舊世代，虧死。"
        verdict_color = "red"

    st.markdown("---")
    st.subheader("📊 AI 殘酷試算 (TCO 分析)")
    
    # 這裡就是會顯示文字的框框
    st.markdown(f"""
    <div class='vs-box'>
        <h4>💰 為了等 6 代，你的隱形成本：</h4>
        <ul>
            <li><b>車價漲幅：</b>多付 <span style='color:red; font-weight:bold'>{int(price_diff)} 萬</span></li>
            <li><b>無車可用 {wait_months} 個月：</b>價值損失約 <span style='color:red; font-weight:bold'>{int(time_cost)} 萬</span> (租車/計程車費)</li>
            <li><b>總結代價：</b><span style='font-size:1.5em; font-weight:bold'>為了開新款，你要多噴 {int(total_cost_wait)} 萬！</span></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if verdict_color == "green":
        st.success(f"🏆 **AI 結論：{verdict}**")
    else:
        st.error(f"🏆 **AI 結論：{verdict}**")

    # 3. 生成腳本
    st.markdown("---")
    st.subheader("🎥 短影音腳本生成 (一鍵開拍)")
    
    if st.button("🎬 生成 Brian 的爆款腳本"):
        if not api_key:
            st.warning("請先在左側輸入 API Key")
        else:
            with st.spinner("🤖 馬斯克正在幫你想台詞..."):
                time.sleep(1)
                script = generate_video_script(api_key, gen5_price, gen6_est_price, wait_months, verdict)
                st.markdown(f"""<div class='script-box'>{script.replace(chr(10), '<br>')}</div>""", unsafe_allow_html=True)
                st.caption("💡 拍攝技巧：手機開啟錄影，切換前後鏡頭，手指著上面的數據念這段稿。")

if __name__ == "__main__":
    main()
