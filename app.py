import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# ========== 配置区 ==========
# 这里换成你自己的 API Key（推荐用 DeepSeek 或通义千问）
API_KEY = "sk-xxxxxxxxxxxxxxxx"
BASE_URL = "https://api.deepseek.com/v1"  # DeepSeek 的地址
MODEL_NAME = "deepseek-chat"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ========== 页面标题 ==========
st.set_page_config(page_title="落地页 AI 诊断工具", page_icon="🔍")
st.title("🔍 落地页 AI 体验与转化率诊断工具")
st.caption("输入网页链接或上传截图，AI 帮你找出转化率杀手")

# ========== 侧边栏：输入区 ==========
with st.sidebar:
    st.header("📥 输入信息")
    input_type = st.radio("选择输入方式", ["网页链接", "上传截图"])

    url = ""
    uploaded_file = None

    if input_type == "网页链接":
        url = st.text_input("请输入网页 URL", placeholder="https://example.com")
    else:
        uploaded_file = st.file_uploader("上传页面截图", type=["png", "jpg", "jpeg"])

    st.subheader("📊 可选：填入页面数据")
    pv = st.number_input("PV（页面浏览量）", min_value=0, value=0)
    uv = st.number_input("UV（独立访客数）", min_value=0, value=0)
    bounce = st.number_input("跳出率（%）", min_value=0.0, max_value=100.0, value=0.0)

    analyze_btn = st.button("🚀 开始诊断", type="primary")


# ========== 抓取网页文本 ==========
def fetch_page_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        # 去掉脚本和样式
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:5000]  # 控制长度
    except Exception as e:
        return f"抓取失败：{e}"


# ========== 构造 Prompt ==========
def build_prompt(page_text, pv, uv, bounce):
    data_info = ""
    if pv or uv or bounce:
        data_info = f"""
        页面数据参考：
        - PV：{pv}
        - UV：{uv}
        - 跳出率：{bounce}%
        请结合这些数据判断页面问题。
        """

    return f"""
    你是一位资深的 UX 与转化率优化（CRO）专家。
    请对以下网页内容进行诊断，重点分析：
    1. 信息层级是否清晰，用户能否快速理解核心价值
    2. CTA（行动号召）按钮是否突出、文案是否有说服力
    3. 表单字段是否过多，是否影响转化
    4. 视觉动线是否符合 F 型阅读习惯
    5. 是否缺乏信任元素（如评价、资质、案例）
    6. 文案是否存在说服力不足的问题

    {data_info}

    请按以下格式输出：
    ### 一、整体评价（1-2句）
    ### 二、问题清单（按严重程度排序，每条包含：问题描述 + 严重程度 + 优化建议 + 预期收益）
    ### 三、优先改进建议（Top 3）

    网页内容如下：
    {page_text}
    """


# ========== 调用大模型 ==========
def analyze_with_ai(prompt):
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"AI 调用失败：{e}"


# ========== 主流程 ==========
if analyze_btn:
    if input_type == "网页链接" and not url:
        st.warning("请先输入网页 URL")
    elif input_type == "上传截图" and not uploaded_file:
        st.warning("请先上传截图")
    else:
        with st.spinner("AI 正在诊断中，请稍候..."):
            if input_type == "网页链接":
                page_text = fetch_page_text(url)
                st.info("✅ 网页内容抓取完成，正在调用 AI 分析...")
                prompt = build_prompt(page_text, pv, uv, bounce)
                result = analyze_with_ai(prompt)
            else:
                # 截图模式：这里先用文字提示，实际需接入多模态模型
                st.info("📷 截图模式：请确保已接入多模态模型（如通义千问-VL）")
                result = "截图分析功能需接入多模态大模型，可参考代码中的说明扩展。"

            st.markdown("## 📋 诊断报告")
            st.markdown(result)

            # 导出按钮
            st.download_button(
                label="📥 下载诊断报告",
                data=result,
                file_name="landing_page_report.md",
                mime="text/markdown",
            )