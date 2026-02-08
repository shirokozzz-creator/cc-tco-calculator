import streamlit as st
import pandas as pd
import os
import math
import altair as alt
import numpy as np
import csv
from datetime import datetime

# ==========================================
# 0. 全域設定 (必須放在第一行)
# ==========================================
st.set_page_config(page_title="Brian 的航太級車況實驗室", page_icon="✈️", layout="wide")

# ==========================================
# 🛠️ 共用工具函式 (存名單用 - 防彈版)
# ==========================================
def save_lead(email, model, note="Waitlist"):
    file_name = "leads_v2.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 如果檔案不存在，先建立標題列
    if not os.path.exists(file_name):
        with open(file_name, "w", newline="", encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "Model", "Email", "Status", "Note"])
            
    # 寫入資料
    with open(file_name, "a", newline="", encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, model, email, "Waitlist", note])

# ==========================================
# 🚗 功能 A：Toyota TCO 精算機 (摺疊衝擊版)
# ==========================================
def page_toyota_tco():
    # --- 1. 基礎數據庫 ---
    car_db = {
        "Corolla Cross": {
            "gas_price": 760000, "hybrid_price": 880000, "battery": 49000,
            "advice_gas": "適合年跑1萬公里以下，首選 2024 汽油版，租賃退役CP值最高。",
            "advice_hybrid": "適合通勤族，首選 2022 年式，低於 45 萬通常是營業車。",
        },
        "RAV4": {
            "gas_price": 950000, "hybrid_price": 1150000, "battery": 65000,
            "advice_gas": "首選 2.0 旗艦。2.5 油電稅金一年多繳 5千，非高里程不划算。",
            "advice_hybrid": "注意 2019-2020 車頂架漏水通病。建議找 2021 後出廠車型。",
        },
        "Altis": {
            "gas_price": 650000, "hybrid_price": 780000, "battery": 49000,
            "advice_gas": "強烈建議買 2019.3 後的 TNGA 世代 (12代)。操控性大升級。",
            "advice_hybrid": "極高機率買到計程車退役。若不懂看車，建議買汽油版最安全。",
        }
    }

    # --- 2. 航太級 FMEA 數據庫 ---
    car_fmea = {
        "Corolla Cross": [
            {
                "years": "2020~2022", 
                "part": "車頂架密封失效 (Roof Leak)",
                "s": 7, "o": 3, "d": 2, "cost": 6500, "target": "both",
                "eng_note": "【技術鑑定】應力集中導致防水墊片形變，引發流體滲漏風險。",
                "check_guide": "⚠️ 買車時請檢查：A柱與頂棚交接處是否有『黃褐色水痕』或『霉味』。"
            },
            {
                "years": "2020~2024", 
                "part": "K120 CVT 變速箱頓挫",
                "s": 3, "o": 2, "d": 1, "cost": 85000, "target": "gas",
                "eng_note": "【技術鑑定】Direct Shift CVT 啟動齒輪切換至鋼帶之過渡特性。",
                "check_guide": "⚠️ 試駕重點：低速 20-40km/h 收油再踩油門時，是否有明顯『拉扯感』。"
            }
        ],
        "RAV4": [
            {
                "years": "2019~2021", 
                "part": "車頂架嚴重漏水",
                "s": 7, "o": 5, "d": 2, "cost": 8000, "target": "both",
                "eng_note": "【技術鑑定】固定扣具密封圈疲勞失效，水分侵入 A/B 柱氣囊區域。",
                "check_guide": "⚠️ 買車必看：拆開後車廂備胎室，檢查底部是否有積水或鏽蝕痕跡。"
            },
            {
                "years": "2019~2022", 
                "part": "HV 高壓電纜接頭腐蝕",
                "s": 9, "o": 3, "d": 8, "cost": 65000, "target": "hybrid",
                "eng_note": "【技術鑑定】電化學腐蝕導致接頭阻抗過大，失效將觸發系統停機。",
                "check_guide": "⚠️ 頂高底盤檢查：橘色高壓電線連接馬達處，金屬編織網是否『發黑或綠粉』。"
            }
        ]
    }

    if 'submitted' not in st.session_state: st.session_state.submitted = False

    # --- 側邊欄參數 ---
    st.sidebar.header("⚙️ Toyota 參數設定")
    selected_model = st.sidebar.selectbox("請選擇車款", ["Corolla Cross", "RAV4", "Altis"])
    params = car_db[selected_model]
    
    gas_car_price = st.sidebar.number_input("⛽ 汽油版 - 入手價", value=params["gas_price"], step=10000)
    hybrid_car_price = st.sidebar.number_input("⚡ 油電版 - 入手價", value=params["hybrid_price"], step=10000)
    annual_km = st.sidebar.slider("年行駛里程 (km)", 5000, 60000, 15000) 
    years_to_keep = st.sidebar.slider("預計持有年分", 1, 15, 10)
    gas_price = st.sidebar.number_input("目前油價", value=31.0)
    battery_cost = st.sidebar.number_input("大電池更換預算", value=params["battery"])
    
    st.sidebar.markdown("---")
    force_risk = st.sidebar.checkbox("🚨 加入 FMEA 通病風險成本", value=True, help="依據航太 FMEA 邏輯，將通病發生機率 x 維修金額加入成本計算")

    # --- 管理員後台 ---
    with st.sidebar.expander("🕵️‍♂️ 管理員後台"):
        admin_pwd = st.text_input("輸入密碼", type="password", key="admin_check")
        target_file = "leads_v2.csv"
        if admin_pwd == "uc0088":  
            if os.path.exists(target_file):
                try:
                    df_leads = pd.read_csv(target_file, on_bad_lines='skip')
                    st.write(f"目前累積：{len(df_leads)} 筆")
                    csv_data = df_leads.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 下載 CSV", csv_data, "leads_v2.csv", "text/csv")
                except: st.error("讀取錯誤")
            else: st.warning("資料庫為空")

    # --- 主畫面 ---
    st.title(f"✈️ 航太工程師的 {selected_model} 購車精算機")
    st.caption("運用航太級 TCO 模型，幫您算出符合數學邏輯的最佳選擇。")

    # --- 🔥 FMEA 通病雷達 (摺疊衝擊版) ---
    fmea_cost_gas = 0
    fmea_cost_hybrid = 0

    if selected_model in car_fmea:
        # 計算一下總風險金額，放在標題吸引人點擊
        total_risk_preview = 0
        for i in car_fmea[selected_model]:
            total_risk_preview += i['cost']

        # 這裡就是你要的「摺疊」效果，預設 expanded=False (關閉)
        with st.expander(f"💣 【高風險預警】{selected_model} 潛在隱形虧損約 ${total_risk_preview:,} (點擊展開真相)", expanded=False):
            
            st.info("💡 根據航太維修數據分析，這年份的車可能有以下通病。")
            
            for issue in car_fmea[selected_model]:
                # 計算 RPN 與 成本
                rpn = issue['s'] * issue['o'] * issue['d']
                expected_cost = int(issue['cost'] * (issue['o'] / 10.0))
                
                if issue['target'] == 'both':
                    fmea_cost_gas += expected_cost
                    fmea_cost_hybrid += expected_cost
                elif issue['target'] == 'gas':
                    fmea_cost_gas += expected_cost
                elif issue['target'] == 'hybrid':
                    fmea_cost_hybrid += expected_cost

                # 視覺化卡片
                is_severe = rpn > 100 or issue['cost'] > 20000
                border_color = "#FF4B4B" if is_severe else "#FFA500"
                bg_color = "#FFE5E5" if is_severe else "#FFF8E1"
                prob_display = issue['o'] * 10 

                st.markdown(f"""
                <div style="border: 2px solid {border_color}; border-radius: 10px; background-color: {bg_color}; padding: 15px; margin-bottom: 15px;">
                    <h3 style="color: {border_color}; margin-top: 0;">⚠️ 可能損失金額：${issue['cost']:,}</h3>
                    <p><b>📛 通病項目：</b>{issue['part']} (年份: {issue['years']})</p>
                    <p><b>📊 體感發生率：</b>約 {prob_display}% (中獎機率)</p>
                    <hr style="border-top: 1px dashed {border_color};">
                    <p style="color: #D32F2F; font-weight: bold;">🔍 航太工程師教你怎麼檢查：</p>
                    <p>{issue['check_guide']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 專業數據也藏在裡面，變成第二層摺疊
            with st.expander("🛠️ 查看航太工程師 FMEA 原始數據 (Engineering Data)"):
                st.table(pd.DataFrame(car_fmea[selected_model]).drop(columns=['check_guide']))

        if force_risk:
            st.caption(f"💡 系統已自動將上述風險成本加入試算：汽油版 +${fmea_cost_gas:,} / 油電版 +${fmea_cost_hybrid:,}")

    # --- TCO 計算邏輯 ---
    def get_resale_value(initial_price, year, car_type):
        k = 0.096 if car_type == 'gas' else 0.104
        initial_drop = 0.82 if car_type == 'gas' else 0.80 
        if year <= 1: return initial_price * initial_drop
        else: return (initial_price * initial_drop) * math.exp(-k * (year - 1))

    chart_data_rows = []
    cross_point = None
    prev_diff = None
    prev_g_total = 0
    calc_range = years_to_keep + 3
    tax_gas = 17410 if selected_model == "RAV4" else 11920
    tax_hybrid = 22410 if selected_model == "RAV4" else 11920

    for y in range(0, calc_range):
        g_resale = get_resale_value(gas_car_price, y, 'gas')
        h_resale = get_resale_value(hybrid_car_price, y, 'hybrid')
        
        # 成本計算 (加入 FMEA 成本)
        risk_g = fmea_cost_gas if (force_risk and y > 0) else 0
        risk_h = fmea_cost_hybrid if (force_risk and y > 0) else 0

        g_total = (gas_car_price - g_resale) + ((annual_km * y / 12.0) * gas_price) + (tax_gas * y) + risk_g
        
        # 油電電池邏輯
        h_bat = battery_cost if ((annual_km * y > 160000) or (y > 8)) else 0
        h_total = (hybrid_car_price - h_resale) + ((annual_km * y / 21.0) * gas_price) + (tax_hybrid * y) + h_bat + risk_h
        
        chart_data_rows.append({"年份": y, "車型": "汽油版", "累積花費": int(g_total)})
        chart_data_rows.append({"年份": y, "車型": "油電版", "累積花費": int(h_total)})
        
        curr_diff = g_total - h_total
        if y > 0 and prev_diff is not None:
            if prev_diff < 0 and curr_diff >= 0:
                frac = abs(prev_diff) / (abs(prev_diff) + curr_diff)
                exact_year = (y - 1) + frac
                exact_cost = prev_g_total + (g_total - prev_g_total) * frac
                if exact_year <= years_to_keep:
                    cross_point = {"年份": exact_year, "花費": exact_cost}
        prev_diff = curr_diff; prev_g_total = g_total

    chart_df = pd.DataFrame(chart_data_rows)
    
    # 最終 TCO 計算
    total_km = annual_km * years_to_keep
    is_battery_included = (total_km > 160000 or years_to_keep > 8)
    
    final_risk_g = fmea_cost_gas if force_risk else 0
    final_risk_h = fmea_cost_hybrid if force_risk else 0

    g_resale_final = get_resale_value(gas_car_price, years_to_keep, 'gas')
    h_resale_final = get_resale_value(hybrid_car_price, years_to_keep, 'hybrid')
    
    tco_gas = (gas_car_price - g_resale_final) + ((total_km / 12.0) * gas_price) + (tax_gas * years_to_keep) + final_risk_g
    tco_hybrid = (hybrid_car_price - h_resale_final) + ((total_km / 21.0) * gas_price) + (tax_hybrid * years_to_keep) + (battery_cost if is_battery_included else 0) + final_risk_h
    
    diff = tco_gas - tco_hybrid

    # --- 戰情室 ---
    st.subheader("📊 決策戰情室")
    
    if diff > 0:
        winner = "油電版"
        amount = int(diff)
        st.success(f"🏆 **建議購買：{winner}！** 持有 {years_to_keep} 年省下 **${amount:,}**")
    else:
        winner = "汽油版"
        amount = int(abs(diff))
        st.info(f"🏆 **建議購買：{winner}！** 持有 {years_to_keep} 年省下 **${amount:,}**")

    col1, col2 = st.columns(2)
    col1.metric("⛽ 汽油版總成本", f"${int(tco_gas):,}", delta=f"含隱形虧損: ${final_risk_g}" if final_risk_g > 0 else None, delta_color="inverse")
    col2.metric("⚡ 油電版總成本", f"${int(tco_hybrid):,}", delta=f"含隱形虧損: ${final_risk_h}" if final_risk_h > 0 else None, delta_color="inverse")

    # --- 圖表 ---
    st.subheader(f"📈 {years_to_keep} 年持有成本曲線 (TCO)")
    base = alt.Chart(chart_df).encode(
        x=alt.X('年份', axis=alt.Axis(tickMinStep=1)), 
        y='累積花費', color=alt.Color('車型', scale=alt.Scale(domain=['汽油版', '油電版'], range=['#FF4B4B', '#0052CC']))
    )
    lines = base.mark_line(strokeWidth=3)
    if cross_point:
        pt = pd.DataFrame([cross_point])
        cross_layer = alt.Chart(pt).mark_point(color='red', size=200, shape='diamond').encode(x='年份', y='花費', tooltip=['年份', '花費'])
        st.altair_chart((lines + cross_layer).interactive(), use_container_width=True)
        st.caption(f"📍 黃金交叉點：第 {cross_point['年份']:.1f} 年，之後油電版開始回本。")
    else:
        st.altair_chart(lines.interactive(), use_container_width=True)
        st.caption("📍 此設定下無黃金交叉點。")

    # --- 服務公告區 ---
    st.markdown("---")
    st.warning("⚠️ **服務公告：目前諮詢量額滿，暫停即時報價**")

    if not st.session_state.submitted:
        st.markdown(f"""
        感謝支持！因工程師公務繁忙，目前 **暫停「即時鑑價」服務**。
        您留下的 Email 將加入 **「優先候補名單」**。
        待消化完畢後，我會優先將 **【{selected_model} 2026 Q1 獨家行情 + FMEA 避坑指南】** 寄給您。
        """)
        
        with st.form("waitlist_form"):
            email_input = st.text_input("輸入 Email 加入候補：", placeholder="name@example.com")
            submitted = st.form_submit_button("加入優先候補名單")
            
            if submitted:
                if "@" in email_input:
                    save_lead(email_input, selected_model)
                    st.session_state.submitted = True
                    st.session_state.user_email = email_input
                    st.rerun()
                else:
                    st.error("❌ Email 格式錯誤")
    else:
        st.success(f"✅ 已加入候補！一旦恢復服務，會通知您：{st.session_state.get('user_email', '')}")
        if st.button("🔄 重新輸入"):
            st.session_state.submitted = False
            st.rerun()

# ==========================================
# 💎 功能 B：Lexus ES300h 甜蜜點模型 (私用版)
# ==========================================
def page_es300h_private():
    st.title("💎 Lexus ES300h 最佳入手年份模型")
    st.caption("Designed for Engineers: Finding the Mathematical Sweet Spot")

    st.sidebar.header("💎 ES300h 參數模擬")
    current_year = 2026
    years_to_keep = st.sidebar.slider("預計持有年數", 1, 10, 5)
    annual_km = st.sidebar.slider("年行駛里程", 5000, 40000, 15000)
    battery_cost = st.sidebar.number_input("大電池成本", value=65000)
    basic_maintenance = st.sidebar.number_input("年均保養費", value=12000)

    market_data = {
        2025: 195, 2024: 168, 2023: 145, 2022: 128, 
        2021: 115, 2020: 102, 2019: 90, 2018: 75, 
        2017: 65, 2016: 58, 2015: 50
    }

    def calculate_tco(target_year):
        car_age = current_year - target_year
        buy_price = market_data.get(target_year, 0) * 10000
        if buy_price == 0: return None
        
        sell_price = buy_price * (0.90 ** years_to_keep) 
        depreciation_loss = buy_price - sell_price
        
        is_expired = (car_age + years_to_keep > 8) or ((annual_km * years_to_keep) + (car_age * 15000) > 160000)
        risk_cost = battery_cost if is_expired else 0
        
        total_cost = depreciation_loss + risk_cost + (basic_maintenance * years_to_keep)
        
        return {
            "年份": target_year, "車齡": car_age, "入手價": int(buy_price/10000),
            "年均成本": int(total_cost / years_to_keep),
            "狀態": "🔴 過保" if is_expired else "🟢 保固內"
        }

    results = []
    for y in range(2015, 2026):
        res = calculate_tco(y)
        if res: results.append(res)
    
    df = pd.DataFrame(results)
    sweet_spot = df.loc[df['年均成本'].idxmin()]

    st.success(f"🏆 **數據運算結論：最佳年份是 {sweet_spot['年份']} 年 (車齡 {sweet_spot['車齡']} 年)**")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📉 年均持有成本 (越低越好)")
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('年份:O'),
            y='年均成本:Q',
            color=alt.condition(alt.datum.年份 == int(sweet_spot['年份']), alt.value('#FF4B4B'), alt.value('#2E86C1')),
            tooltip=['年份', '入手價', '年均成本', '狀態']
        )
        st.altair_chart(chart, use_container_width=True)
    
    with col2:
        st.subheader("📋 數據表")
        st.dataframe(df[['年份', '入手價', '年均成本', '狀態']], hide_index=True)

    st.info("此頁面為內部研發用，截圖後可作為 Mobile01 菁英客群行銷素材。")

# ==========================================
# 🕹️ 主程式導航
# ==========================================
def main():
    st.sidebar.title("✈️ 實驗室導航")
    
    page = st.sidebar.radio(
        "請選擇功能模組：",
        ["🚗 Toyota 全車系 TCO 精算", "⚙️ 實驗室參數設定"] 
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Designed by Brian | Aerospace Engineer")

    if page == "🚗 Toyota 全車系 TCO 精算":
        page_toyota_tco()
        
    elif page == "⚙️ 實驗室參數設定":
        st.title("🔒 內部研發中")
        password = st.sidebar.text_input("🔑 請輸入權限金鑰", type="password")
        
        if password == "uc0088": 
            st.sidebar.success("身份驗證成功")
            page_es300h_private()
        else:
            st.warning("⚠️ 此區域僅限工程師內部訪問，請切換回公開頁面。")

if __name__ == "__main__":
    main()
