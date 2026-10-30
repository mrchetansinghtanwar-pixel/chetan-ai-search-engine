"""Public Google search widget, isolated from the app's BYOK fields."""
from html import escape
import json
import re
from urllib.parse import urlencode
import streamlit as st


def sync_home(state, chat_ready):
    """Switch only on readiness transitions; preserve deliberate tool navigation."""
    state.setdefault('workspace_mode', 'Web search')
    previous = state.get('chat_was_ready', False)
    if chat_ready and not previous and state['workspace_mode'] in {'Web search', 'Chat'}:
        state['workspace_mode'] = 'Chat'
    elif previous and not chat_ready and state['workspace_mode'] == 'Chat':
        state['workspace_mode'] = 'Web search'
    state['chat_was_ready'] = bool(chat_ready)


def search_document(pse_id, query):
    if not isinstance(pse_id, str) or not re.fullmatch(r'[A-Za-z0-9:_-]{5,160}', pse_id):
        raise ValueError('Invalid public search engine ID.')
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 500:
        raise ValueError('Enter a search query with 1–500 characters.')
    js_query = json.dumps(query).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    # A sandbox without allow-same-origin gives the Google widget an opaque origin.
    # Google code cannot read the parent app's
    # API-key widgets. Only the explicitly public PSE ID enters this document.
    html = '''<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Google web search</title>
<style>
body{margin:0;padding:6px;font-family:Arial,sans-serif;background:#fafbf9;color:#25332f}
.gsc-control-cse{background:transparent!important;border:0!important;padding:0!important}
.gsc-input-box{border:1px solid #93c5b9!important;border-radius:16px;padding:10px!important;background:white!important}
.gsc-search-button-v2{border:0!important;border-radius:14px!important;background:#208579!important;padding:20px!important}
.gsc-webResult.gsc-result{border-radius:12px;margin-top:8px}
#loading{font-size:14px;color:#64746e}
</style>
<script>window.__gcse={callback:function(){document.getElementById('loading').hidden=true;
google.search.cse.element.getElement('webresults').execute(''' + js_query + ''');}};</script>
<script async src="https://cse.google.com/cse.js?''' + urlencode({'cx': pse_id}) + '''"></script>
</head><body><p id="loading">Loading Google search… If it does not load, use the link below the search panel.</p>
<div class="gcse-searchresults-only" data-gname="webresults" data-enableHistory="false" data-autoSearchOnLoad="false"
data-linkTarget="_blank" data-mobileLayout="enabled" data-ivt="true"></div>
</body></html>'''
    return ('<style>body{margin:0}</style><iframe title="Google web search" '
            'sandbox="allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox" '
            'style="width:100%;height:550px;border:0" srcdoc="' + escape(html, quote=True) + '"></iframe>')


def web_search_ui(pse_id):
    st.html('<div class="welcome"><h1>chetan search</h1><p>Explore the web. Find your next idea.</p></div>')
    st.caption('Google web results · No API key required. Add a chat API key in the sidebar to open AI chat.')
    if not pse_id:
        st.info('The site owner needs to configure GOOGLE_PSE_ID in Streamlit Secrets to enable web search.')
        return
    with st.form('public_search_form'):
        query = st.text_input('Search the web', placeholder='Search anything on the web…', max_chars=500,
                              key='public_search_input')
        submitted = st.form_submit_button('Search', icon=':material/search:', type='primary', width='stretch')
    if submitted:
        from byok import redact
        st.session_state['public_search_query'] = redact(query.strip(), st.session_state)
        if not query.strip():
            st.info('Enter a search query first.')
    query = st.session_state.get('public_search_query', '')
    st.caption('Search queries go directly to Google. Google may display ads and apply its privacy and cookie policies.')
    if not query:
        return
    try:
        document = search_document(pse_id, query)
    except ValueError:
        st.error('The search engine configuration is invalid. Please contact the site owner.')
        return
    st.subheader('Web results')
    st.iframe(document, height=560, alt='Google search box and web results')
    st.link_button('Search not loading? Open Google search',
                   'https://cse.google.com/cse?' + urlencode({'cx': pse_id, 'q': query}),
                   icon=':material/open_in_new:')
