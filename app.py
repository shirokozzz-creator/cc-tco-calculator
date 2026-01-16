import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
import os  # <--- 引入作業系統工具

# --- 頁面設定 ---
st.set_page_config(page_title="Debug Mode", page_icon="🐞")

# =========== 🐞 抓兇手專區 (偵錯模式) ===========
st.error("👇 這是伺服器上真正的檔案列表 (請把下面這行複製給我)：")
files = os.listdir('.')
st.code(files)  # 這會顯示出一個列表，例如 ['app.py', 'TaipeiSans.ttf', ...]

# 檢查字型檔是否存在？
font_name = "TaipeiSans.ttf" # 這是我們想要的檔名
if font_name in files:
    st.success(f"✅ 成功找到 {font_name}！")
else:
    st.error(f"❌ 找不到 {font_name}。請看上面的列表，到底它的名字變成了什麼？")
# =================================================

st.title("🚙 CC 油電 vs. 汽油：TCO 分析報告")

# --- (以下是原本的程式碼，為了不讓您一直複製貼上，我們先測試字型就好) ---
# --- 如果字型檔搞定，我們再把完整的程式碼貼回來 ---

def create_pdf_test():
    pdf = FPDF()
    pdf.add_page()
    # 嘗試載入
    try:
        # 這裡我們用「列表裡找到的第一個 .ttf 檔案」來當作字型，避免檔名打錯
        ttf_files = [f for f in os.listdir('.') if f.endswith('.ttf') or f.endswith('.otf')]
        if ttf_files:
            real_font_name = ttf_files[0]
            st.info(f"💡 嘗試載入字型檔：{real_font_name}")
            pdf.add_font('TaipeiSans', '', real_font_name, uni=True)
            pdf.set_font('TaipeiSans', '', 16)
            pdf.cell(0, 10, '恭喜！字型載入成功！', ln=True, align='C')
            return pdf.output(dest='S').encode('latin-1')
        else:
            st.error("😱 伺服器裡完全沒有 .ttf 檔案！請確認 GitHub 上傳成功。")
            return None
    except Exception as e:
        st.error(f"❌ 載入失敗：{str(e)}")
        return None

if st.button("測試生成 PDF"):
    pdf_bytes = create_pdf_test()
    if pdf_bytes:
        st.download_button("下載測試 PDF", pdf_bytes, "test.pdf", "application/pdf")
