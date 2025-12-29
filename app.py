import streamlit as st
import time
from agents import consultation_stream

# 1. 頁面設定
st.set_page_config(page_title="M.D.E. 中西醫觀點辯證引擎", page_icon="⚕️", layout="wide")

# CSS 優化 (深色字按鈕 + 換行)
st.markdown("""
<style>
    /* =============================================
       1. 主畫面按鈕樣式 (Big Cards)
       預設針對所有按鈕，設定成大卡片風格
       ============================================= */
    div.stButton > button {
        width: 300px;
        height: 90px;

        /* 文字排版 */
        white-space: normal !important;
        word-wrap: break-word !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        line-height: 1.5 !important;
        padding: 15px !important;

        /* 外觀設計 */
        border-radius: 15px;     /* 更圓潤 */
        border: 2px solid #e0e0e0;
        color: #2c3e50 !important; /* 深藍灰字體 */
        font-size: 18px !important;
        font-weight: 700 !important;
        background-color: #f8f9fa !important; /* 淺灰白底 */
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* 主畫面按鈕懸停特效 */
    div.stButton > button:hover {
        transform: translateY(-5px); /* 浮起效果 */
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-color: #4a90e2 !important;
        color: #4a90e2 !important;
    }

    /* =============================================
       2. 側邊欄按鈕特化 (Sidebar Reset Button)
       使用 CSS 選擇器鎖定 stSidebar 區域，覆蓋上面的設定
       ============================================= */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 200px;
        height: auto !important;       /* 還原高度，不要那麼高 */
        padding: 10px 20px !important; /* 標準內距 */
        font-size: 15px !important;    /* 字體縮小 */
        border-radius: 8px !important;

        /* 警示風格 */
        background-color: #ff4b4b !important; /* 紅色 */
        color: white !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 側邊欄按鈕懸停 */
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #d93434 !important; /* 深紅 */
        color: white !important;
        transform: none !important;    /* 不要浮動 */
    }

    /* =============================================
       3. 其他元件優化
       ============================================= */
    .stChatMessage { margin-bottom: 20px; }
    section[data-testid="stSidebar"] { background-color: #1e1e1e; }
    .stAlert { color: #000000 !important; }

    /* =============================================
       4. 修改 Toast (導播視窗) 的樣式
       ============================================= */
    div[data-testid="stToast"] {
        background-color: #ffe4e1 !important;
        border-left: 10px solid #8b0000 !important;
        color: #8a0000 !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
        opacity: 0.98 !important;
        width: 450px !important; /* 加寬 */
        padding: 20px !important; /* 增加內距 */

        /* --- 位置設定 --- */
        position: fixed !important; /* 脫離原本的容器，自由移動 */
        z-index: 9999 !important;   /* 確保浮在最上層 */

        /* 移到「螢幕正上方」 */
        left: 50% !important;
        transform: translateX(-50%) !important; /* 居中校正 */
        top: 20px !important;       /* 距離頂部 30px */
        bottom: auto !important;    /* 取消預設的底部定位 */
        right: auto !important;     /* 取消預設的右邊定位 */
    }

    /* 修改 Toast 裡面的圖示大小 */
    div[data-testid="stToast"] > div:first-child {
        font-size: 50px !important;
        margin-right: 6px !important;
}

</style>
""", unsafe_allow_html=True)

# 2. Callback Functions
def handle_case_click(case_text):
    st.session_state.history = []
    st.session_state.trigger_case = case_text
    st.session_state.active_context = case_text
    st.toast("🏥 病歷載入中... (Initialize Case)", icon="🔄")

def clear_history():
    st.session_state.history = []
    st.session_state.active_context = None
    st.toast("歷史紀錄已清除", icon="🗑️")

if "history" not in st.session_state:
    st.session_state.history = []
if "trigger_case" not in st.session_state:
    st.session_state.trigger_case = None
if "active_context" not in st.session_state:
    st.session_state.active_context = None

# 3. 側邊欄 (詳細技術說明)
with st.sidebar:
    st.title("⚕️ M.D.E.")
    st.caption("Medical Dialectic Engine")
    st.caption("v2.1.0 Multi-Model Edition")

    # 模型供應商選擇
    provider = st.selectbox(
        "🤖 選擇 AI 模型 (Provider)",
        ("Google Gemini", "Groq (Llama 3)", "DeepSeek")
    )

    # 動態調整輸入框標題
    api_key = st.text_input(f"輸入 {provider} API Key", type="password")

    st.button("🏥 下一位病人\n\n(System Reset)", on_click=clear_history)

    st.markdown("---")

    # 詳細的技術說明
    with st.expander("ℹ️ 系統核心架構", expanded=True):
        st.markdown("""
        本系統採用 **LangChain 多智能體 (Multi-Agent)** 協作架構，模擬跨領域醫療專家的觀點辯證與整合。

        **1. 核心引擎 (Core Engine)**
        * **Model:** Google Gemini 2.5 Flash、Groq (Llama 3)、DeepSeek
        * **Framework:** LangChain / LangGraph Concept

        **2. 智能體設計 (Agent Design)**
        * **AI Director (導播):** 負責動態生成辯論議題，控制對話節奏。
        * **Role-Playing Agents:** 模擬西醫 (EBM) 與中醫 (TCM) 的思考邏輯與語氣。

        **3. 推理策略 (Reasoning Strategy)**
        * **Adversarial Prompting:** 透過對抗式提示激發深度觀點。
        * **Chain-of-Thought (CoT):** 讓 AI 展示推理過程而非僅給出結論。
        * **Context-Awareness:** 具備多輪對話記憶與追問能力。
        """)

    st.markdown("---")
    st.warning("⚠️ **免責聲明 (Disclaimer)**\n\n本系統為技術概念驗證 (POC) 原型，生成內容僅供參考，**不具備**最終診斷效力。")

# 4. 主標題
col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("中西醫觀點辯證引擎")
    st.markdown("**協作模式：** `Evidence-Based Medicine` vs `Traditional Chinese Medicine` (AI Guided)")

# 5. 案例矩陣
st.markdown("### 📋 臨床案例模擬 (Clinical Case Simulation)")

col1, col2 = st.columns(2)
with col1:
    st.button("🧠 自律神經失調 (Insomnia)\n\n症狀：長期失眠 / 心悸 / 焦慮",
              on_click=handle_case_click,
              args=("65歲女性，長期失眠，半夜容易醒，心悸，容易緊張。不想吃安眠藥。",))

    st.button("🩸 原發性痛經 / 不孕 (Dysmenorrhea)\n\n症狀：劇烈腹痛 / 手腳冰冷",
              on_click=handle_case_click,
              args=("30歲女性，經痛嚴重，吃止痛藥沒效，手腳冰冷，備孕中。",))

with col2:
    st.button("🧴 異位性皮膚炎 (Atopic Dermatitis)\n\n症狀：反覆搔癢 / 類固醇疑慮",
              on_click=handle_case_click,
              args=("10歲男童，全身皮膚癢，抓到流血。擦類固醇會好，停藥復發，擔心副作用。",))

    st.button("🎗️ 腫瘤術後照護 (Post-op Care)\n\n症狀：化療虛弱 / 免疫低下",
              on_click=handle_case_click,
              args=("60歲男性，大腸癌術後化療中，虛弱腹瀉。詢問中醫支持療法。",))

# 6. 顯示歷史 (這裡只顯示「對話」，不顯示導播)
for item in st.session_state.history:
    if item["name"] != "🎬 導播 (AI Director)":
        with st.chat_message(item["avatar"]):
            st.write(f"**{item['name']}**")
            st.write(item["content"])

# 7. 輸入與執行
user_input = st.chat_input("請輸入病歷摘要，或針對上方病情進行「追問」...")
final_input_for_ui = None
final_input_for_ai = None
is_followup_mode = False

if st.session_state.trigger_case:
    final_input_for_ui = st.session_state.trigger_case
    final_input_for_ai = st.session_state.trigger_case
    st.session_state.trigger_case = None
    is_followup_mode = False

elif user_input:
    final_input_for_ui = user_input
    if st.session_state.active_context:
        final_input_for_ai = (
            f"【注意：這是一個追問】\n"
            f"原始病歷背景：{st.session_state.active_context}\n"
            f"使用者追問：{user_input}"
        )
        is_followup_mode = True
    else:
        final_input_for_ai = user_input
        st.session_state.active_context = user_input
        is_followup_mode = False

if final_input_for_ui:
    st.session_state.history.append({"name": "📋 主訴/追問", "avatar": "user", "content": final_input_for_ui})
    with st.chat_message("user"):
        st.write(final_input_for_ui)

    stream = consultation_stream(final_input_for_ai, provider, api_key, is_followup=is_followup_mode)

    try:
        for role, content in stream:

            # 導播訊息變成浮動氣泡 (Toast)
            if role == "director":
                # 顯示浮動通知，這會自動消失
                st.toast(f"🎬\n\n{content}", icon="📣")
                # 選擇性：如果你完全不想存入歷史，就不要 append
                # st.session_state.history.append(...) <- 這一行拿掉

            elif role == "western":
                with st.spinner("🔵 西醫 (Dr. West) 分析中..."):
                    time.sleep(0.5)
                st.session_state.history.append({"name": "🔵 西醫觀點 (Dr. West)", "avatar": "🔵", "content": content})
                with st.chat_message("🔵"):
                    st.write("**🔵 西醫觀點 (Dr. West):**")
                    st.write(content)

            elif role == "eastern":
                with st.spinner("🟤 中醫 (Dr. East) 分析中..."):
                    time.sleep(0.5)
                st.session_state.history.append({"name": "🟤 中醫觀點 (Dr. East)", "avatar": "🟤", "content": content})
                with st.chat_message("🟤"):
                    st.write("**🟤 中醫觀點 (Dr. East):**")
                    st.write(content)

            elif role == "translator":
                with st.spinner("👵 個管師建議..."):
                    time.sleep(0.5)
                st.session_state.history.append({"name": "👵 阿蓮姨aka在地化衛教 (Case Manager)", "avatar": "👵", "content": content})
                with st.chat_message("👵"):
                    st.write("**👵 阿蓮姨aka在地化衛教 (Case Manager):**")
                    st.success(content)

            elif role == "error":
                st.error(content)

    except Exception as e:
        st.error(f"System Error: {e}")
