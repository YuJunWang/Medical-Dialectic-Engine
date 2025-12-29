import os
import time
import random
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from google.api_core import exceptions

# ==========================================
#  LLM 工廠函式 (支援多模型切換)
# ==========================================
def get_llm(provider, api_key):
    if not api_key: return None
    try:
        if provider == "Google Gemini":
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, temperature=0.7)
        elif provider == "Groq (Llama 3)":
            return ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key, temperature=0.7)
        elif provider == "DeepSeek":
            return ChatOpenAI(model="deepseek-chat", api_key=api_key, base_url="https://api.deepseek.com", temperature=0.7)
    except Exception as e:
        return None


def consultation_stream(user_input, provider, api_key, is_followup=False):

    if not api_key:
        yield ("director", "【系統】請輸入 API Key。")
        return

    try:
        model = get_llm(provider, api_key)

        if not model:
            yield ("director", f"🚫 無法啟動 {provider} 模型，請檢查 API Key 是否正確。")
            return


        # 邏輯分流：追問模式只跑 1 輪，辯論模式跑 3 輪
        if is_followup:
            total_rounds = 1
            debate_history = f"使用者追問：{user_input}\n"
            use_director = False
        else:
            total_rounds = 3
            debate_history = f"病患主訴：{user_input}\n"
            use_director = True

        for round in range(1, total_rounds + 1):

            # ========================
            # 🎬 1. 導播 (Director)
            # ========================
            current_theme = ""
            if use_director:
                if round == 1:
                    current_theme = "【階段一：專業診斷】中西醫雙方先根據自己的專業，提出治療方案，暫時不要互相攻擊。"
                else:
                    try:
                        time.sleep(random.uniform(1.0, 4.0))
                        director_prompt = (
                            f"你是這一場中西醫醫學辯論導播。記錄：\n{debate_history}\n"
                            "根據目前的討論記錄，請找出一個新的『衝突點』。"
                            "利用兩方最大的差異點，提供雙方可以繼續爭論的爭議點！"
                            "根據討論紀錄，盡量不回覆重複的內容，讓對話保持延續性。"
                            "請直接輸出指令內容，不要加『切入點：』或『主題：』這類的開頭標籤。"
                            "字數限制：40字以內。"
                        )
                        res_director = model.invoke(director_prompt)
                        current_theme = res_director.content
                        yield ("director", current_theme)
                    except Exception:
                        current_theme = "【階段二：深入辯論】請針對副作用進行攻防。"


            # ========================
            # 🔵 2. 西醫 (Dr. West)
            # ========================
            time.sleep(random.uniform(3.0, 6.0))

            if is_followup:
                # 追問模式：任務改為「回答問題」
                prompt_western = (
                    f"你是一名擁有 20 年臨床經驗的醫學中心主任醫師\n"
                    f"使用者追問：'{user_input}'。\n"
                    f"請針對這個問題，依據 UpToDate 與實證醫學給出專業回答 (Yes/No/風險評估)。\n"
                    f"字數限制：200 字以內，請條理分明。\n"
                    f"語氣：冷靜、客觀、權威。不要輸出你的身分，直接回答。"
                )
            else:
                # 辯論模式：
                if round == 1:
                    prompt_western = (
                        f"你是一名擁有 20 年臨床經驗的醫學中心主任醫師\n"
                        f"【專業領域】專精於內科與急重症，嚴格遵循 UpToDate 與國際診療指引 (Guidelines)。\n"
                        f"【當前任務】針對病患主訴：'{user_input}'，進行初步評估。\n"
                        f"【輸出要求】\n"
                        f"1. 使用精確的醫學術語 (Medical Terminology)，少部分專有名詞使用英文，有歸國留學生的感覺\n"
                        f"2. 提出『鑑別診斷』(Differential Diagnosis) 的可能性。\n"
                        f"3. 建議具體的檢查項目 (如 CBC, CT, MRI) 或第一線用藥。\n"
                        f"4. 語氣：冷靜、客觀、權威，不帶情緒。唯科學的方法才是一切，對於中醫不太相信。\n"
                        f"5. 字數限制：80~120 字，請條理分明。\n"
                        f"6. 預設你正在對話中，但對話中不加入稱呼，只會輸出你說的話，不用輸出你的身分，也不會特別回覆導播。"
                    )
                else:
                    prompt_western = (
                        f"你是一名擁有 20 年臨床經驗的醫學中心主任醫師。目前的病歷討論紀錄如下：\n{debate_history}\n"
                        f"【當前任務】針對導播指令：'{current_theme}'，或是中醫剛才的論點進行『科學性批判』。\n"
                        f"【思考路徑】\n"
                        f"1. 藥物動力學 (PK/PD)：質疑中藥成分不清，是否會與西藥產生交互作用？\n"
                        f"2. 毒理學：質疑肝腎毒性風險 (Hepatotoxicity/Nephrotoxicity)。\n"
                        f"3. 統計學：強調中醫缺乏大規模隨機對照試驗 (RCT) 支持。\n"
                        f"4. 其他科學實證的學說可以支持的觀點。\n"
                        f"5. 使用精確的醫學術語 (Medical Terminology)，少部分專有名詞使用英文，有歸國留學生的感覺\n"
                        f"【語氣】\n"
                        f"不要流於謾罵，要用『科學家的傲慢』指出對方的邏輯漏洞。\n"
                        f"例如：「在沒有明確機轉的情況下用藥，是在拿病人的肝腎開玩笑。」\n"
                        f"字數限制：80~120 字以內。\n"
                        f"根據討論紀錄，絕對不回覆重複的內容，讓對話保持延續性與創造力。\n"
                        f"預設你正在對話中，但對話中不加入稱呼，只會輸出你說的話，不用輸出你的身分，也不會特別回覆導播。"
                    )

            res_western = model.invoke(prompt_western)
            content_western = res_western.content
            debate_history += f"西醫: {content_western}\n"
            yield ("western", content_western)


            # ========================
            # 🟤 3. 中醫 (Dr. East)
            # ========================
            time.sleep(random.uniform(3.0, 6.0))

            if is_followup:
                # 追問模式：任務改為「回答問題」
                prompt_eastern = (
                    f"你是一名出身三代中醫世家的資深中醫師。\n"
                    f"使用者追問：'{user_input}'。\n"
                    f"請針對這個問題，給出『中醫調理』的建議 (飲食/穴位/生活作息)。\n"
                    f"字數限制：300 字以內，請條理分明。\n"
                    f"語氣：沈穩、充滿智慧。不要輸出你的身分，直接回答。"
                )
            else:
                # 辯論模式：
                if round == 1:
                    prompt_eastern = (
                        f"你是一名出身三代中醫世家的資深中醫師\n"
                        f"【專業領域】精通《傷寒雜病論》與《黃帝內經》，擅長經方與針灸。\n"
                        f"【當前任務】針對病患主訴：'{user_input}'，以及西醫剛才的診斷，提出中醫觀點。\n"
                        f"【輸出要求】\n"
                        f"1. 進行『辨證』：判斷病患的證型（如：肝鬱氣滯、脾胃濕熱、陰虛火旺）。\n"
                        f"2. 解釋病因：不要只看症狀，要解釋是哪個臟腑氣血失調。\n"
                        f"3. 提出治則：如「疏肝解鬱」、「清熱利濕」。\n"
                        f"4. 語氣：沈穩、充滿智慧，展現對『人』的整體關懷。\n"
                        f"5. 字數限制：80~120 字。\n"
                        f"6. 預設你正在對話中，但對話中不加入稱呼，只會輸出你說的話，不用輸出你的身分，也不會特別回覆導播。"
                    )
                else:
                    prompt_eastern = (
                        f"你是一名出身三代中醫世家的資深中醫師。目前的病歷討論紀錄如下：\n{debate_history}\n"
                        f"【當前任務】針對導播指令：'{current_theme}'，或是西醫剛才的言論進行四兩撥千金的回覆。\n"
                        f"【思考路徑】\n"
                        f"1. 醫源性損害：指出西藥強效鎮壓症狀帶來的副作用 (Side Effects)。\n"
                        f"2. 治標不治本：批評西醫只看數據，忽略了病人整體的『氣』與『生活品質』。\n"
                        f"3. 強調『共存與調理』：西醫是殺伐，中醫是王道，強調恢復人體自癒力。\n"
                        f"【語氣】\n"
                        f"不卑不亢，用長者的智慧看著年輕氣盛的西醫。\n"
                        f"沈穩、充滿智慧，展現對『人』的整體關懷，用語引經據典。\n"
                        f"字數限制：80~120 字。\n"
                        f"根據討論紀錄，絕對不回覆重複的內容，讓對話保持延續性與創造力。\n"
                        f"預設你正在對話中，但對話中不加入稱呼，只會輸出你說的話，不用輸出你的身分，也不會回覆導播。"
                    )

            res_eastern = model.invoke(prompt_eastern)
            content_eastern = res_eastern.content
            debate_history += f"中醫: {content_eastern}\n"
            yield ("eastern", content_eastern)

        # ========================
        # 👵 4. 個管師總結 (Case Manager)
        # ========================
        time.sleep(1.5)

        if is_followup:
            prompt_translator = (
                f"你是嘉義阿蓮姨。使用者追問：'{user_input}'。\n"
                f"兩位醫生已經回答了。\n"
                f"請用『親切台語』給出一個具體建議。\n"
                f"100字以內。"
            )
        else:
            prompt_translator = (
                f"你是阿蓮姨（個管師），是一位年齡約50歲的親切阿姨。兩位醫生吵了 {total_rounds} 輪：\n{debate_history}\n"
                "請用『親切台語』出來打圓場，總結西醫Dr. West、中醫Dr. East雙方觀點。"
                "最後根據病患身分給予稱謂，並提出折衷建議：『我們先去大醫院檢查數據』"
                "適當加入一些問候語，增加在地的親切感。"
                "200字以內，注意文字排版，不用把你的思考過程說出來"
            )

        res_translator = model.invoke(prompt_translator)
        yield ("translator", res_translator.content)

    except exceptions.ResourceExhausted:
        yield ("director", "🚫 系統過載 (Rate Limit Protection)：請等待 60 秒後再試。")
    except Exception as e:
        yield ("director", f"系統發生錯誤: {e}")
