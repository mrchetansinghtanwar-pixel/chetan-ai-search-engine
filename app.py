import html
import streamlit as st
import streamlit.components.v1 as components

# Google Programmable Search Engine ID
PSE_ID = "51b2594163d2e4b56"

# Page configuration
st.set_page_config(
    page_title="Chetan AI Search",
    page_icon="🔎",
    layout="wide"
)

# Modern AI Background Design
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 15% 20%, #263c8c 0%, transparent 35%),
        radial-gradient(circle at 85% 75%, #642b91 0%, transparent 35%),
        linear-gradient(135deg, #080e22, #121c3d);
    color: white;
}

.block-container {
    max-width: 1100px;
    padding-top: 70px;
}

h1 {
    text-align: center;
    color: white !important;
    font-size: 48px !important;
    font-weight: 800 !important;
    text-shadow: 0 0 25px rgba(59,130,246,0.5);
}

h2, h3 {
    text-align: center;
    color: #cbd5e1 !important;
}

[data-testid="stHeader"] {
    background: transparent;
}

iframe {
    border-radius: 20px;
    box-shadow: 0 15px 50px rgba(0,0,0,0.35);
}
</style>
""", unsafe_allow_html=True)

# Website Heading
st.title("🔎 Chetan AI Search Engine")
st.subheader("Search with your own control!")

st.markdown("---")

# Google Search Engine
safe_id = html.escape(PSE_ID, quote=True)

search_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
body {{
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    background: #ffffff;
    border-radius: 20px;
}}
</style>

<script async
src="https://cse.google.com/cse.js?cx={safe_id}">
</script>

</head>
<body>
<div class="gcse-search"></div>
</body>
</html>
"""

components.html(
    search_html,
    height=650,
    scrolling=True
)

st.markdown("---")

st.markdown(
    "<p style='text-align:center;color:#cbd5e1;'>"
    "Powered by Google | Chetan AI Search Engine"
    "</p>",
    unsafe_allow_html=True
)