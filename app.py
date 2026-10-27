"""Run from this folder: python -m streamlit run app.py"""
from pathlib import Path
import tomllib
import streamlit as st
from agent import answer, google_search, GeminiError
from image_service import create_image, create_cloudflare_image

st.set_page_config(page_title="Chetan AI • Search & chat", page_icon=":material/auto_awesome:", layout="centered", initial_sidebar_state="collapsed")


st.html("""<style>
.stApp {background:radial-gradient(ellipse 440px 330px at 8% 12%,rgba(115,0,196,.24),transparent 75%),radial-gradient(ellipse 330px 230px at 35% 24%,rgba(204,0,177,.09),transparent 75%),#080709;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stMainBlockContainer"] {max-width:960px;padding-top:2rem;padding-bottom:2rem;}
.brand{font-size:24px;letter-spacing:-1px;font-weight:650;color:#fff;margin:0 0 24px;}
.brand-icon{color:#d6b5ff;font-size:34px;vertical-align:middle;margin-right:7px;}
.brand-ai{color:#b78bfa;margin-left:3px;}
.eyebrow{font-size:11px;letter-spacing:3px;color:#c49ce9;font-weight:600;margin-bottom:14px;}
.hero h1{font-size:clamp(34px,4.5vw,52px);line-height:1.09;letter-spacing:-2.4px;font-weight:650;color:#fff;margin:0 0 24px;}
.hero h1 span{background:linear-gradient(100deg,#c5a3ff,#edb4fa);background-clip:text;-webkit-background-clip:text;color:transparent;}
.hero p{font-size:18px;line-height:1.6;color:#aaa5b1;margin-bottom:18px;}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-color:#302633!important;border-radius:20px;}
[data-testid="stButton"] button{border-radius:12px;min-height:49px;transition:background .15s,border-color .15s;}
[data-testid="stButton"] button:hover{border-color:#a34ff0;background:#24132c;color:#fff;}
button[kind="primary"]{background:linear-gradient(100deg,#8138f5,#d017df);border:0;color:white;}
[data-testid="stChatInput"]{border:1px solid #614172;border-radius:20px;background:#151118;box-shadow:0 0 28px #a026d211;}
[data-testid="stBottom"]>div{background:#080709;}
[data-testid="stChatMessage"]{border:1px solid #29222f;border-radius:18px;background:#121015;}
[data-testid="stSidebar"]{background:#100d14;border-right:1px solid #2b2034;}
@media(max-width:600px){.brand{margin-bottom:32px}.hero h1{letter-spacing:-1.3px}.hero p{font-size:16px}}
</style>""")


def secret(name, default=""):
    # Read beside app.py, independent of the terminal working directory.
    local_file = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    if local_file.is_file():
        try:
            data = tomllib.loads(local_file.read_text(encoding="utf-8-sig"))
            return str(data.get(name, default)).strip()
        except (OSError, ValueError):
            st.error("Secrets file ka format sahi nahi hai. Quotes aur setting names check karein.")
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


st.session_state.setdefault("messages", [])
st.session_state.setdefault("last_error", "")
api_key = secret("GEMINI_API_KEY")
model = secret("GEMINI_MODEL", "gemini-flash-latest")
google_key, pse_id = secret("GOOGLE_API_KEY"), secret("GOOGLE_PSE_ID")
google_ready = bool(google_key and pse_id)

with st.sidebar:
    st.header(":material/auto_awesome: Chetan AI")
    st.caption("Aapka research aur writing companion")
    if st.button("Nayi chat", icon=":material/add:", width="stretch", type="primary"):
        st.session_state.messages = []
        st.session_state.last_error = ""
        st.rerun()
    st.divider()
    language = st.selectbox("Jawab ki bhasha", ["Hinglish", "Hindi", "English"])
    use_search = st.toggle("Google web search", value=False, disabled=not google_ready,
                           help="Assistant zaroorat par search karega. Maximum 3 searches per turn.")
    st.caption("Google configured" if google_ready else "Google optional hai — setup ke liye README dekhein.")
    st.caption("Gemini configured" if api_key else "Gemini key abhi add nahi hui.")
    st.divider()
    if st.session_state.messages:
        transcript = "\n\n".join(f"{m['role'].upper()}\n{m['content']}" for m in st.session_state.messages)
        st.download_button("Chat download", transcript, file_name="chetan-chat.txt",
                           mime="text/plain", icon=":material/download:", width="stretch")
    st.caption("Chat is browser session tak rehti hai. Refresh se reset ho sakti hai.")
    st.caption("Sawal Google Gemini ko bheje jaate hain. Search on hone par search query Google ko bhi jaati hai.")

st.html("""<div class="brand"><span class="brand-icon">✳</span> chetan<span class="brand-ai">ai</span></div>
<div class="hero"><div class="eyebrow">YOUR EVERYDAY AI COMPANION</div>
<h1>Bade ideas.<br><span>Bas ek sawaal door.</span></h1>
<p>Likhiye, seekhiye aur naye ideas khojiye.<br>Aapka personal AI assistant, aapki bhasha mein.</p></div>""")
st.badge("Google search enabled" if use_search else "AI conversation", icon=":material/auto_awesome:")
if not api_key:
    st.info("Shuru karne ke liye `.streamlit/secrets.toml` mein GEMINI_API_KEY add karein. Setup README mein hai.")

mode = st.segmented_control("Workspace", ["Chat", "Image Generator"], default="Chat", key="workspace_mode")
if mode == "Image Generator":
    st.subheader("Apne ideas ko image banaiye")
    st.caption("Logo, illustration ya photo — describe karein aur create dabayein.")
    provider = st.selectbox("Image provider", ["Cloudflare · FLUX", "Gemini"])
    cf_token, cf_account = secret("CLOUDFLARE_API_TOKEN"), secret("CLOUDFLARE_ACCOUNT_ID")
    image_ready = bool(cf_token and cf_account) if provider.startswith("Cloudflare") else bool(api_key)
    if not image_ready:
        st.info("Cloudflare setup: .streamlit/secrets.toml mein CLOUDFLARE_API_TOKEN aur CLOUDFLARE_ACCOUNT_ID save karein." if provider.startswith("Cloudflare") else "Gemini key save karein.")
    with st.form("image_form"):
        image_prompt = st.text_area("Kaisi image chahiye?", placeholder="Ek modern Chetan AI logo, purple neon colours, black background…", max_chars=4000, height=120)
        c1, c2 = st.columns(2)
        with c1:
            image_style = st.selectbox("Style", ["Photorealistic", "Logo / minimal", "3D illustration", "Digital art", "Anime"])
        with c2:
            image_ratio = st.selectbox("Size", ["1:1"] if provider.startswith("Cloudflare") else ["1:1", "16:9", "9:16"])
        create = st.form_submit_button("Image banao", type="primary", icon=":material/auto_awesome:", disabled=not image_ready, width="stretch")
    st.caption("Cloudflare free allowance limited hai; account usage dashboard mein quota dekhein. Gemini images ki billing alag hai.")
    if create:
        try:
            with st.spinner("Aapki image ban rahi hai…"):
                if provider.startswith("Cloudflare"):
                    result = create_cloudflare_image(cf_token, cf_account, image_prompt, image_style)
                else:
                    result = create_image(api_key, secret("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image"), image_prompt, image_style, image_ratio)
                st.session_state.image_result = result
        except GeminiError as error:
            st.error(str(error))
        except Exception:
            st.error("Image request complete nahi hui. Dobara try karein.")
    if st.session_state.get("image_result"):
        result = st.session_state.image_result
        st.caption("Last generated image · " + result["prompt"])
        for index, item in enumerate(result["images"]):
            st.image(item["data"], width="stretch")
            ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[item["mime"]]
            st.download_button("Image download", item["data"], file_name=f"chetan-ai-{index+1}.{ext}", mime=item["mime"], key=f"image_download_{index}")
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
    retry = st.button("Dobara try karein", disabled=not api_key)
prompt = st.chat_input("Apna sawaal ya idea yahan likhiye…", max_chars=8000, disabled=not api_key or pending)
if not st.session_state.messages:
    with st.container(border=True):
        st.caption("EXPLORE THE POSSIBILITIES")
        st.subheader("Aaj kya banana hai?")
        for label, value in [
            ("AI ko simple bhasha mein samjhao", "AI kaise kaam karta hai? Simple Hinglish mein examples ke saath samjhao."),
            ("Ek professional email likho", "Meeting reschedule karne ke liye professional email draft likho."),
            ("Mera learning plan banao", "Python seekhne ke liye beginner-friendly 4 week learning plan banao.")]:
            if st.button(label, width="stretch", disabled=not api_key):
                prompt = value

if prompt or retry:
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.last_error = ""
    try:
        with st.spinner("Chetan AI kaam kar raha hai…"):
            status = st.empty()
            search = (lambda query: google_search(query, google_key, pse_id)) if use_search else None
            result = answer(api_key, model, st.session_state.messages, language, search, status.caption)
            st.session_state.messages.append({"role": "assistant", **result})
    except GeminiError as error:
        st.session_state.last_error = str(error)
    except Exception:
        # Do not render raw exceptions: upstream request details may contain secrets.
        st.session_state.last_error = "Request complete nahi hui. Configuration check karke retry karein."
    st.rerun()

st.caption("AI galti kar sakta hai. Zaroori jaankari sources se verify karein.")
