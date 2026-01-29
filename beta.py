import streamlit as st
import pandas as pd
import time
import google.generativeai as genai
from PIL import Image

# 0. 設定頁面
st.set_page_config(page_title="Brian 航太數據室 | 真實 AI 掃描", page_icon="✈️")

# 1. 側邊欄：輸入鑰匙的地方
def sidebar_content():
    with st.sidebar:
        st.header("✈️ 設定控制台")
        # 這裡做一個輸入框，讓你貼上 API Key
        api_key = st.text_input("🔑 輸入 Google Gemini API Key", type="password")
        st.info("💡 請去 Google AI Studio 申請免費 Key")
        return api_key

# 2. AI 核心：呼叫 Google 大腦
def analyze_image_with_gemini(api_key, image, prompt):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash') 
        with st.spinner("🤖 正在連線 Google 大腦..."):
            response = model.generate_content([prompt, image])
            return response.text
    except Exception as e:
        return f"❌ 錯誤：{str(e)}"

# 3. 主程式
def main():
    user_api_key =AIzaSyDAJTvNaBDz7xtwcsI_TcpIkK9njco5B7M() # 取得你在側邊欄輸入的 Key
    st.title("🛡️ 真・AI 車況審計師")
    st.markdown("請上傳圖片，AI 會真的幫你看圖！")

    uploaded_file = st.file_uploader("📸 上傳圖片", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file and user_api_key:
        image = Image.open(uploaded_file)
        st.image(image, width=300)
        
        if st.button("🚀 啟動真實 AI 分析"):
            prompt = "你是一位專業車商。請告訴我這張圖片裡的車是什麼型號？有沒有明顯外觀瑕疵？它是高配還是低配？"
            result = analyze_image_with_gemini(user_api_key, image, prompt)
            st.success("分析完成！")
            st.write(result)
    
    elif uploaded_file and not user_api_key:
        st.warning("⚠️ 請在左邊側邊欄貼上 API Key 喔！")

if __name__ == "__main__":
    main()
