"""Run from this folder: python -m streamlit run app.py"""
from pathlib import Path
import tomllib
import streamlit as st
from agent import google_search, GeminiError
from providers import MODELS, list_models, chat_answer
from provider_detection import detect_provider
from byok import disconnect, expire_credentials, redact
from chat_stream import stream_chat
from image_service import create_image, create_cloudflare_image
from utilities import show_tools
from speech_input import speech_input
from web_search import sync_home, web_search_ui

st.set_page_config(page_title="Chetan AI • Search & chat", page_icon=":material/auto_awesome:", layout="centered", initial_sidebar_state="expanded")


st.html((Path(__file__).parent / "design.css").read_text(encoding="utf-8"))


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
    if message["role"] == "assistant":
        with st.expander("Copy response"):
            st.caption("Use the copy button in the top-right corner below.")
            st.code(message["content"], language=None, wrap_lines=True)
    for warning in message.get("warnings", []):
        st.warning(warning)
    if message.get("sources"):
        with st.expander(f"Sources · {len(message['sources'])}"):
            for source in message["sources"]:
                st.link_button(source["title"], source["url"], icon=":material/open_in_new:")
                st.caption(source["snippet"])



workspace_options = ["Web search", "Chat", "Chat with PDF", "Image Generator", "Voice", "PDF tools", "Text pad", "Calculator"]
if st.session_state.get("workspace_mode") == "Admin Panel":
    st.session_state.workspace_mode = "Chat"

if expire_credentials(st.session_state):
    st.info("Credentials cleared after 30 minutes without interaction. Enter your key again.")
st.session_state.setdefault("messages", [])
st.session_state.setdefault("last_error", "")
st.sidebar.title("Chetan AI")
st.sidebar.caption("SEARCH · CREATE · EXPLORE")
with st.sidebar.expander("Workspace", expanded=False):
    for tool_name in workspace_options:
        if st.button(tool_name, key="nav_" + tool_name, width="stretch"):
            st.session_state.workspace_mode = tool_name
            st.rerun()
st.sidebar.caption("Your key. Your quota. No sign-up required. AI usage is billed by your provider.")
with st.sidebar.expander("AI connection", expanded=True):
    provider_choice = st.selectbox("AI Provider", ["Auto detect"] + list(MODELS), key="chat_provider")
    automatic = provider_choice == "Auto detect"
    entered_key = st.text_input("Chat API key" if automatic else f"{provider_choice} chat API key", type="password",
                                key="chat_key_auto" if automatic else "chat_key_" + provider_choice).strip()
    chat_provider = detect_provider(entered_key) if automatic else provider_choice
    if automatic:
        st.caption("Detection reads the key format locally. It does not validate the key or contact providers.")
        if entered_key and chat_provider:
            st.caption(f"Detected: {chat_provider} · key validity and quota are checked by the provider.")
        elif entered_key:
            st.warning("Cannot identify this key format. Select its provider above and enter the key there. No request has been sent.")
    api_key = entered_key if chat_provider else ""
    if chat_provider == "Meta / Llama (via Groq)":
        st.caption("Use a Groq key. Llama model access depends on your Groq account.")
    if api_key == "YOUR_GEMINI_API_KEY":
        api_key = ""
    if st.button("Check API connection", disabled=not api_key):
        try:
            list_models(chat_provider, api_key)
            st.session_state['verified_provider'] = chat_provider
            st.success("Provider accepted the key. Model access and credits are checked on each request.")
        except GeminiError as error:
            st.session_state.pop('verified_provider', None)
            st.error(str(error))
    st.caption("Key entered · ready to request" if api_key else "Disconnected · enter your API key")
    st.button("Disconnect / Clear credentials", on_click=disconnect, args=(st.session_state,), width="stretch")
    if st.button("Refresh model list", disabled=not api_key):
        try:
            st.session_state["models_" + chat_provider] = list_models(chat_provider, api_key)
        except GeminiError as error:
            st.error(str(error))
    model_options = st.session_state.get("models_" + chat_provider, MODELS[chat_provider]) if chat_provider else []
    model = st.selectbox("AI model", model_options + ["Custom model ID"] if chat_provider else [],
                         key="model_" + (chat_provider or "auto"), disabled=not chat_provider,
                         placeholder="Enter a supported API key first")
    if model == "Custom model ID":
        model = st.text_input("Enter model ID", key="custom_model_" + chat_provider).strip()
    chat_ready = bool(api_key and model)
with st.sidebar.expander("Response settings", expanded=False):
    stream_enabled = st.toggle("Stream responses", value=True, help="Gemini/OpenAI chat streams when Google search is off. Search agents and other tools keep their existing response flow.")
    temperature = st.slider("Select Temperature", min_value=0.0, max_value=2.0, value=0.8, step=0.1)
    max_tokens = st.slider("Select Max Tokens", min_value=50, max_value=200, value=100)
    st.caption("Tokens limit response length, not daily API quota. A low limit can cut answers short. Temperature applies only to supported models.")
    st.caption("Switching providers sends the current conversation to the selected provider. Use Clear Chat for a fresh conversation.")
with st.sidebar.expander("AI settings", expanded=False):
    st.caption("Enter your own keys to enable AI features. Keys apply only to this session; blank fields keep the feature disabled.")
    voice_key = st.text_input("Gemini voice API key", type="password", key="credential_voice").strip()
    image_key = st.text_input("Gemini image API key", type="password", key="credential_image").strip()
    cf_override = st.text_input("Cloudflare image API token", type="password", key="credential_cloudflare").strip()
    cf_account_override = st.text_input("Cloudflare Account ID", key="credential_cf_account").strip()
    google_key = st.text_input("Google search API key", type="password", key="credential_search").strip()
    pse_id = st.text_input("Google Search Engine ID", type="password", key="credential_pse").strip()
    image_model = st.text_input("Gemini image model ID", value=secret("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")).strip()
    voice_model = st.text_input("Gemini voice model ID", value=secret("GEMINI_VOICE_MODEL") or "gemini-flash-latest").strip()
    st.caption("Temperature applies to Gemini, Groq and GPT-4.1/4o. Other models use their default.")
    st.caption("This limits response length, not daily API quota. Video generation and other research providers are not connected yet.")
google_ready = bool(google_key and pse_id)
with st.sidebar.expander("API key privacy"):
    st.caption("Password fields mask the display; keys still exist temporarily in this browser's widget and this session's server memory. They are not saved by the app to files, databases, cookies or local storage. Disconnect clears credential fields and chat/PDF state. Inactivity expires credentials on the next interaction after 30 minutes. This is not guaranteed memory erasure; the hosting operator controls the server. Use trusted HTTPS deployments and restricted, revocable keys.")

with st.sidebar:
    if st.button("Clear Chat", icon=":material/add:", width="stretch", type="primary"):
        st.session_state.messages = []
        st.session_state.last_error = ""
        st.rerun()
    st.divider()
    language_choice = st.selectbox("Response language", ["Auto", "English", "Hindi", "Hinglish"], key="reply_language")
    language = {"Auto": "the language of the user's latest message; detect it automatically (Hindi script for Hindi, English for English, Roman Hinglish for Roman Hindi)", "English": "English", "Hindi": "Hindi in Devanagari script", "Hinglish": "Roman Hinglish"}[language_choice]
    if language_choice == "Auto":
        st.caption("Auto: replies match the language of your question.")
    use_search = st.toggle("Search in AI answers", value=False, disabled=not google_ready,
                           help="The assistant searches when needed, up to 3 searches per turn.")
    st.caption("Google search tool configured" if google_ready else "AI search needs a separate Google API key. Web search works without one.")
    st.caption(f"{chat_provider} chat configured" if chat_ready else "Enter a chat key and select a model.")
    st.divider()
    if st.session_state.messages:
        transcript = "\n\n".join(f"{m['role'].upper()}\n{m['content']}" for m in st.session_state.messages)
        st.download_button("Download chat", transcript, file_name="chetan-chat.txt",
                           mime="text/plain", icon=":material/download:", width="stretch")
    st.caption("Your chat lasts for this browser session. Refreshing the page may reset it.")
    st.caption("Your questions are sent to the selected AI provider. When web search is enabled, search queries are also sent to Google.")

st.html('<div class="brand"><span class="brand-mark">✳</span>Chetan AI<span class="brand-note">Your everyday AI workspace</span></div>')
sync_home(st.session_state, chat_ready)
tool_left, tool_center, tool_right = st.columns([1, 2, 1])
with tool_center:
    mode = st.selectbox("Workspace / Tools", workspace_options, key="workspace_mode")
if mode == "Web search":
    web_search_ui(secret("GOOGLE_PSE_ID"))
    st.stop()
welcome_composer = None
if mode == "Chat" and not st.session_state.messages:
    st.html('<div class="welcome"><h1>chetan ai <span class="byok-badge">BYOK</span></h1><p>Where curiosity becomes clarity.</p></div>')
    welcome_composer = st.container(key="welcome_composer")
    def open_workspace(target):
        st.session_state.workspace_mode = target
    for col, label, target, icon in zip(st.columns(3), ["Ask your PDF", "Create an image", "Convert a file"], ["Chat with PDF", "Image Generator", "PDF tools"], [":material/description:", ":material/auto_awesome:", ":material/picture_as_pdf:"]):
        with col:
            st.button(label, icon=icon, width="stretch", on_click=open_workspace, args=(target,))
if mode == "Chat" and not chat_ready:
    st.caption("Connect your API key in the sidebar to start. Your key, your quota — no sign-up required.")

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
if welcome_composer is not None:
    with welcome_composer:
        prompt = st.chat_input("Ask anything…", max_chars=8000, disabled=not chat_ready or pending)
else:
    prompt = st.chat_input("Ask a follow-up…", max_chars=8000, disabled=not chat_ready or pending)

prompt = prompt or voice_prompt
if (prompt or retry) and chat_ready:
    if prompt:
        st.session_state.messages.append({"role": "user", "content": redact(prompt, st.session_state)})
        st.session_state.messages = st.session_state.messages[-40:]
    st.session_state.last_error = ""
    try:
        with st.spinner("Chetan AI is working…"):
            status = st.empty()
            search = (lambda query: google_search(query, google_key, pse_id)) if use_search else None
            if stream_enabled and chat_provider in {"Gemini", "OpenAI"} and not search:
                with st.chat_message("assistant"):
                    live = st.empty()
                    try:
                        result = stream_chat(chat_provider, api_key, model, st.session_state.messages, language, temperature, max_tokens,
                                             lambda text: live.markdown(redact(text, st.session_state)))
                    except Exception:
                        live.empty()
                        raise
            else:
                result = chat_answer(chat_provider, api_key, model, st.session_state.messages, language, search, status.caption, temperature=temperature, max_tokens=max_tokens)
            result['content'] = redact(result['content'], st.session_state)
            st.session_state.messages.append({"role": "assistant", **result})
    except GeminiError as error:
        st.session_state.last_error = str(error)
    except Exception:
        # Do not render raw exceptions: upstream request details may contain secrets.
        st.session_state.last_error = "The request failed. Check your configuration and try again."
    st.rerun()


