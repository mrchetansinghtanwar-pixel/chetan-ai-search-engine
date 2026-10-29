"""Run from this folder: python -m streamlit run app.py"""
from pathlib import Path
import tomllib
import streamlit as st
from agent import google_search, GeminiError
from providers import MODELS, list_models, chat_answer
from image_service import create_image, create_cloudflare_image
from utilities import show_tools
from speech_input import speech_input

st.set_page_config(page_title="Chetan AI • Search & chat", page_icon=":material/auto_awesome:", layout="centered", initial_sidebar_state="expanded")


st.html("""<style>
::selection{background:#6055d9;color:white}
.stApp{background:#020203;color:#e9e8f4}
.stApp:before,.stApp:after{content:"";position:fixed;top:0;bottom:0;width:7vw;pointer-events:none;z-index:0;background:repeating-linear-gradient(155deg,transparent 0%,#171347 16%,#655bdd 18%,#110f32 21%,#020205 28%,#353487 44%,#a89af5 48%,#24205d 54%,#090817 65%);opacity:.72}
.stApp:before{left:0}.stApp:after{right:0;transform:scaleX(-1)}
[data-testid="stHeader"]{background:transparent}
[data-testid="stMainBlockContainer"]{max-width:900px;padding-top:2rem;padding-bottom:7rem;position:relative}
[data-testid="stSidebar"]{background:#0c0c13;border-right:1px solid #252436}
.brand{font-size:17px;font-weight:600;letter-spacing:.5px;color:#b9b8cd;text-align:center;margin-bottom:18px}
.orb-stage{height:53vh;min-height:280px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:26px}
.orb{position:relative;width:190px;height:190px;border-radius:50%;overflow:hidden;background:radial-gradient(ellipse at 24% 72%,#ff403e 0%,#f82135 10%,transparent 36%),radial-gradient(ellipse at 73% 30%,#6846ff 0%,#3c13f6 18%,transparent 44%),radial-gradient(ellipse at 65% 77%,#00daed 0%,#006382 18%,transparent 42%),radial-gradient(ellipse at 30% 22%,#264997,transparent 38%),#080716;box-shadow:inset 0 0 13px #c6b2fb,inset 4px -5px 8px #96a3ca,0 0 2px 2px #675d89,0 0 40px #35267935;animation:breathe 7s ease-in-out infinite}
.orb:after{content:"";position:absolute;inset:4px;border-radius:50%;background:radial-gradient(ellipse at 50% 50%,#02020d99 8%,transparent 66%);border:1px solid #becbff66;box-shadow:inset -7px -3px 12px #d8d1ff55}
.orb-label{color:#7d7c90;font-size:13px;letter-spacing:1px}
@keyframes breathe{50%{transform:scale(1.045);filter:hue-rotate(18deg);box-shadow:inset 0 0 16px #c6b2fb,0 0 48px #4938a544}}
@media(prefers-reduced-motion:reduce){.orb{animation:none}}
[data-testid="stChatInput"]{border:1px solid #282632!important;border-radius:36px!important;background:#101017!important;box-shadow:0 5px 25px #000;max-width:680px;margin:auto}
[data-testid="stChatInput"] textarea{font-size:15px!important}
[data-testid="stChatInputSubmitButton"]{border-radius:50%!important;background:#554ce6!important;color:white!important}
[data-testid="stBottom"]>div{background:#020203}
[data-testid="stChatMessage"]{background:#101018;border:1px solid #242331;border-radius:22px}
[data-testid="stButton"] button{border-radius:18px}
button[kind="primary"]{background:#554ce6;border:0}
@media(max-width:600px){.stApp:before,.stApp:after{width:3vw}.orb{width:155px;height:155px}.orb-stage{height:46vh}}

/* Approved Canva composition */
.stApp{background:radial-gradient(ellipse at 56% 43%,#111329 0%,#06060d 31%,#030306 64%)}
.stApp:before{display:none}
.stApp:after{width:4vw;right:0;opacity:.6;background:linear-gradient(100deg,transparent 25%,#10122e 45%,#554488 55%,#151435 62%,#695bea 65%,#040408 74%);transform:skewX(-9deg)}
[data-testid="stSidebar"]{min-width:210px!important;width:210px!important;background:#090910;border-right:1px solid #191825}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.6rem}
[data-testid="stSidebar"] [data-testid="stButton"] button{min-height:34px;font-size:12px;text-align:left;background:#14131f;border:1px solid #252237;border-radius:9px}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{font-size:11px;color:#858198}
[data-testid="stMainBlockContainer"]{max-width:1100px;padding-top:1rem}
.brand{font-family:monospace;font-size:12px;letter-spacing:5px;color:#e3def3;margin:0 0 32px;text-align:center}
.orb-stage{height:48vh;min-height:260px;gap:32px;justify-content:flex-start;padding-top:24px}
.orb{width:225px;height:225px;background:linear-gradient(145deg,transparent 36%,#568cff55 39%,#7883ff99 42%,#5b55ed55 45%,transparent 51%),radial-gradient(ellipse at 30% 22%,#52bcdf 0%,transparent 30%),radial-gradient(ellipse at 72% 75%,#e41466 0%,#6d155a 20%,transparent 45%),radial-gradient(ellipse at 36% 65%,#415bff 0%,transparent 45%),radial-gradient(ellipse at 75% 25%,#733bc3,transparent 48%),#16445b;box-shadow:inset 0 0 18px #b2a8fc66,0 0 1px 1px #8e9ce3,0 0 65px #4755ba33}
.orb:after{border-color:#c4eaff55;box-shadow:inset 0 0 20px #10102688;background:radial-gradient(ellipse at 30% 24%,#bdeeff77,transparent 9%)}
.orb-label{font-size:12px;color:#ccc5e0;letter-spacing:0}
[data-testid="stChatInput"]{max-width:680px;background:#1d192c!important;border-color:#3a314e!important;border-radius:40px!important}
[data-testid="stChatInputSubmitButton"]{background:#9873f4!important}
[data-testid="stBottom"]>div{background:transparent}
@media(max-width:600px){.orb{width:175px;height:175px}.brand{margin-bottom:15px}.orb-stage{height:44vh}[data-testid="stMainBlockContainer"]{padding-top:1rem}}
</style>""")


def secret(name, default=""):
    # Read beside app.py, independent of the terminal working directory.
    local_file = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    if local_file.is_file():
        try:
            data = tomllib.loads(local_file.read_text(encoding="utf-8-sig"))
            return str(data.get(name, default)).strip()
        except (OSError, ValueError):
            st.error("Invalid secrets file format. Check quotation marks and setting names.")
            st.stop()
    try:
        return str(st.secrets.get(name, default)).strip()
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


def render_reply(message):
    st.markdown(message["content"])
    for warning in message.get("warnings", []):
        st.warning(warning)
    if message.get("sources"):
        with st.expander(f"Sources · {len(message['sources'])}"):
            for source in message["sources"]:
                st.link_button(source["title"], source["url"], icon=":material/open_in_new:")
                st.caption(source["snippet"])



workspace_options = ["Chat", "Chat with PDF", "Image Generator", "Voice", "PDF tools", "Text pad", "Calculator"]
if st.session_state.get("workspace_mode") == "Admin Panel":
    st.session_state.workspace_mode = "Chat"

st.session_state.setdefault("messages", [])
st.session_state.setdefault("last_error", "")
st.sidebar.title("Settings")
chat_provider = st.sidebar.selectbox("AI Provider", list(MODELS), key="chat_provider")
if chat_provider == "Meta / Llama (via Groq)":
    st.sidebar.caption("Use a Groq key. Llama model access depends on your Groq account.")
api_key = st.sidebar.text_input(f"{chat_provider} chat API key", type="password", key="chat_key_" + chat_provider).strip()
if api_key == "YOUR_GEMINI_API_KEY":
    api_key = ""
if st.sidebar.button("Refresh model list", disabled=not api_key):
    try:
        st.session_state["models_" + chat_provider] = list_models(chat_provider, api_key)
    except GeminiError as error:
        st.sidebar.error(str(error))
model_options = st.session_state.get("models_" + chat_provider, MODELS[chat_provider])
model = st.sidebar.selectbox("AI model", model_options + ["Custom model ID"], key="model_" + chat_provider)
if model == "Custom model ID":
    model = st.sidebar.text_input("Enter model ID", key="custom_model_" + chat_provider).strip()
chat_ready = bool(api_key and model)
temperature = st.sidebar.slider("Select Temperature", min_value=0.0, max_value=2.0, value=0.8, step=0.1)
max_tokens = st.sidebar.slider("Select Max Tokens", min_value=50, max_value=200, value=100)
st.sidebar.caption("Tokens limit response length, not daily API quota. A low limit can cut answers short. Temperature applies only to supported models.")
st.sidebar.caption("Switching providers sends the current conversation to the selected provider. Use New chat for a fresh conversation.")
with st.sidebar.expander("AI settings", expanded=False):
    st.caption("Enter your own keys to enable AI features. Keys apply only to this session; blank fields keep the feature disabled.")
    voice_key = st.text_input("Gemini voice API key", type="password").strip()
    image_key = st.text_input("Gemini image API key", type="password").strip()
    cf_override = st.text_input("Cloudflare image API token", type="password").strip()
    cf_account_override = st.text_input("Cloudflare Account ID").strip()
    google_key = st.text_input("Google search API key", type="password").strip()
    pse_id = st.text_input("Google Search Engine ID", type="password").strip()
    image_model = st.text_input("Gemini image model ID", value=secret("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")).strip()
    voice_model = st.text_input("Gemini voice model ID", value=secret("GEMINI_VOICE_MODEL") or "gemini-flash-latest").strip()
    st.caption("Temperature applies to Gemini, Groq and GPT-4.1/4o. Other models use their default.")
    st.caption("This limits response length, not daily API quota. Video generation and other research providers are not connected yet.")
google_ready = bool(google_key and pse_id)

with st.sidebar:
    if st.button("New chat", icon=":material/add:", width="stretch", type="primary"):
        st.session_state.messages = []
        st.session_state.last_error = ""
        st.rerun()
    st.divider()
    language_choice = st.selectbox("Response language", ["Auto", "English", "Hindi", "Hinglish"], key="reply_language")
    language = {"Auto": "the language of the user's latest message; detect it automatically (Hindi script for Hindi, English for English, Roman Hinglish for Roman Hindi)", "English": "English", "Hindi": "Hindi in Devanagari script", "Hinglish": "Roman Hinglish"}[language_choice]
    if language_choice == "Auto":
        st.caption("Auto: replies match the language of your question.")
    use_search = st.toggle("Google web search", value=False, disabled=not google_ready,
                           help="The assistant searches when needed, up to 3 searches per turn.")
    st.caption("Google configured" if google_ready else "Google search is optional. See README for setup.")
    st.caption(f"{chat_provider} chat configured" if chat_ready else "Enter a chat key and select a model.")
    st.divider()
    for tool_name in workspace_options:
        if st.button(tool_name, key="nav_" + tool_name, width="stretch", type="secondary"):
            st.session_state.workspace_mode = tool_name
            st.rerun()
    if st.session_state.messages:
        transcript = "\n\n".join(f"{m['role'].upper()}\n{m['content']}" for m in st.session_state.messages)
        st.download_button("Download chat", transcript, file_name="chetan-chat.txt",
                           mime="text/plain", icon=":material/download:", width="stretch")
    st.caption("Your chat lasts for this browser session. Refreshing the page may reset it.")
    st.caption("Your questions are sent to the selected AI provider. When web search is enabled, search queries are also sent to Google.")

st.html('<div class="brand">CHETAN AI</div>')
tool_left, tool_center, tool_right = st.columns([2, 1.2, 2])
with tool_center:
    mode = st.selectbox("Workspace / Tools", workspace_options, key="workspace_mode")
if mode == "Chat" and not st.session_state.messages:
    st.html('<div class="orb-stage"><div class="orb" role="img" aria-label="Colourful glowing AI orb"></div><div class="orb-label">Your idea. A new beginning.</div></div>')
if mode == "Chat" and not chat_ready:
    st.info("Select an AI provider and model, then enter its API key in the sidebar to start chatting.")

if mode == "Chat with PDF":
    from pdf_chat import pdf_chat_ui
    pdf_chat_ui(chat_provider, api_key, model, language, temperature, max_tokens)
    st.stop()
if mode in {"Voice", "PDF tools", "Text pad", "Calculator"}:
    show_tools(mode)
    st.stop()
if mode == "Image Generator":
    st.subheader("Turn your ideas into images")
    st.caption("Describe a logo, illustration or photo, then select Create image.")
    provider = st.selectbox("Image provider", ["Cloudflare · FLUX", "Gemini"])
    cf_token, cf_account = cf_override, cf_account_override
    image_ready = bool(cf_token and cf_account) if provider.startswith("Cloudflare") else bool(image_key)
    if not image_ready:
        st.info("Enter your Cloudflare API token and Account ID in AI settings." if provider.startswith("Cloudflare") else "Enter your Gemini image API key in AI settings.")
    with st.form("image_form"):
        image_prompt = st.text_area("Describe your image", placeholder="A modern Chetan AI logo, purple neon colours, black background…", max_chars=4000, height=120)
        c1, c2 = st.columns(2)
        with c1:
            image_style = st.selectbox("Style", ["Photorealistic", "Logo / minimal", "3D illustration", "Digital art", "Anime"])
        with c2:
            image_ratio = st.selectbox("Size", ["1:1"] if provider.startswith("Cloudflare") else ["1:1", "16:9", "9:16"])
        create = st.form_submit_button("Create image", type="primary", icon=":material/auto_awesome:", disabled=not image_ready, width="stretch")
    st.caption("Cloudflare has a limited free allowance. Check your usage dashboard. Gemini image billing is separate.")
    if create and image_ready:
        try:
            with st.spinner("Creating your image…"):
                if provider.startswith("Cloudflare"):
                    result = create_cloudflare_image(cf_token, cf_account, image_prompt, image_style)
                else:
                    result = create_image(image_key, image_model, image_prompt, image_style, image_ratio)
                st.session_state.image_result = result
        except GeminiError as error:
            st.error(str(error))
        except Exception:
            st.error("The image request failed. Please try again.")
    if st.session_state.get("image_result"):
        result = st.session_state.image_result
        st.caption("Last generated image · " + result["prompt"])
        for index, item in enumerate(result["images"]):
            st.image(item["data"], width="stretch")
            ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[item["mime"]]
            st.download_button("Download image", item["data"], file_name=f"chetan-ai-{index+1}.{ext}", mime=item["mime"], key=f"image_download_{index}")
        if result["notes"]:
            st.markdown(result["notes"])
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_reply(message)

pending = bool(st.session_state.messages and st.session_state.messages[-1]["role"] == "user")
retry = False
if st.session_state.last_error:
    st.error(st.session_state.last_error)
    retry = st.button("Try again", disabled=not chat_ready)
voice_prompt = speech_input(voice_key, voice_model, disabled=not voice_key or not chat_ready or pending)
prompt = st.chat_input("Type your question or idea here…", max_chars=8000, disabled=not chat_ready or pending)

prompt = prompt or voice_prompt
if (prompt or retry) and chat_ready:
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.last_error = ""
    try:
        with st.spinner("Chetan AI is working…"):
            status = st.empty()
            search = (lambda query: google_search(query, google_key, pse_id)) if use_search else None
            result = chat_answer(chat_provider, api_key, model, st.session_state.messages, language, search, status.caption, temperature=temperature, max_tokens=max_tokens)
            st.session_state.messages.append({"role": "assistant", **result})
    except GeminiError as error:
        st.session_state.last_error = str(error)
    except Exception:
        # Do not render raw exceptions: upstream request details may contain secrets.
        st.session_state.last_error = "The request failed. Check your configuration and try again."
    st.rerun()


