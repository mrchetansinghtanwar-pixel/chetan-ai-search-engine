# Chetan AI — Gemini edition

Complete Python Streamlit app: dark chat UI, real Gemini assistant, Hindi/Hinglish/English replies, optional Google search tool, sources, chat download aur retry.

## Jaldi shuru karein — Windows

Python 3.12 install karein. ZIP extract karke `chetan-ai-gemini` folder mein terminal kholein:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Ab `.streamlit/secrets.toml` editor mein kholein aur apni **nayi** key save karein:

```toml
GEMINI_API_KEY = "APNI_NAYI_GEMINI_KEY"
GEMINI_MODEL = "gemini-flash-latest"
GOOGLE_API_KEY = ""
GOOGLE_PSE_ID = ""
```

Chat mein share hui purani keys ko [AI Studio](https://aistudio.google.com/apikey) se revoke/delete karein. Is project mein koi real key ya aapka PSE ID include nahi hai. Nayi key chat mein bhejne ki zaroorat nahi.

Run:

```powershell
.venv\Scripts\python -m streamlit run app.py
```

Terminal mein diya local URL browser mein kholein, usually `http://localhost:8501`.

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Editor mein nayi key save karein
.venv/bin/python -m streamlit run app.py
```

## Gemini key aur free tier

1. [Google AI Studio](https://aistudio.google.com/apikey) par Google account se login karein.
2. Create API key choose karein aur project select/create karein.
3. Key sirf secrets file mein rakhein. App Gemini ke `generateContent` REST endpoint ko server se call karta hai.
4. [Pricing](https://ai.google.dev/gemini-api/docs/pricing) aur account quota check karein. Free tier limited hai aur model/account eligibility par depend karta hai; unlimited free service ka promise nahi hai.
5. `gemini-flash-latest` moving alias hai. Agar model unavailable ho to apne account ka supported generateContent/function-calling model ID `GEMINI_MODEL` mein set karein.

Is edition ko OpenAI key ki zaroorat nahi. Google search key aur Gemini key alag services ke liye hain; ek ko doosre ki jagah na use karein.

## Optional Google Programmable Search

Normal chat ke liye dono `GOOGLE_*` values blank rakhein. Search chahiye aur existing eligible Custom Search JSON API project hai to secrets mein Google API key aur apna private engine ID dalein; sidebar mein Google web search on karein.

[Google official notice](https://developers.google.com/custom-search/v1/overview): Custom Search JSON API naye customers ke liye closed hai; existing customers ko 1 January 2027 tak alternative par migrate karna hai. PSE ID hone se API eligibility guarantee nahi hoti. Engine ke configured scope ke results aayenge.

- [Cloud Console](https://console.cloud.google.com/) mein existing project API access, quota aur key restrictions check karein.
- [PSE control panel](https://programmablesearchengine.google.com/controlpanel/all) se engine ID copy karke sirf private secrets mein save karein.
- Gemini zaroorat par `google_search` function call karta hai; Python search execute karta hai aur snippets Gemini ko bhejta hai. Phir answer aur source buttons milte hain.
- Maximum 3 search queries aur 4 Gemini requests per turn. Raw errors/credentials UI mein print nahi hote.
- Search off hone par current web verification nahi hoti. App snippets padhta hai, full pages nahi.

[Gemini function calling documentation](https://ai.google.dev/gemini-api/docs/generate-content/function-calling)

## Deployment — Streamlit Community Cloud

1. GitHub repo mein `app.py`, `agent.py`, `requirements.txt`, `.gitignore`, `.streamlit/config.toml` aur README upload karein. Tests aur example secrets file bhi upload kar sakte hain.
2. **Real `.streamlit/secrets.toml` upload na karein.** Gitignore normal git commits mein madad karta hai; GitHub browser upload mein khud check karein.
3. [Streamlit Cloud](https://share.streamlit.io/) par Create app → repo/branch select → entrypoint `app.py`.
4. Advanced settings mein Python 3.12 aur Secrets box mein apna actual TOML save karein. Deploy karein.
5. Agar project subfolder mein hai, entrypoint ka poora relative path select karein aur theme file saath rakhein.
6. Pehle private access mein test karein. Public visitors owner ki quota use karte hain; is starter mein login/global rate limiter nahi hai. Public deployment ke liye access control aur quota limits configure karein.

[Official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)

## Files

- `app.py`: complete chat interface aur session handling.
- `agent.py`: Gemini REST requests, bounded tool loop, optional Google search.
- `.streamlit/config.toml`: navy/violet dark design.
- `.streamlit/secrets.toml.example`: empty credentials template.
- `requirements.txt`: tested dependency versions.
- `tests/test_app.py`: offline mocked tests.

## Privacy aur limits

Messages Google Gemini ko jaate hain; web search on hone par search query Google Search API ko bhi jaati hai. Free-tier data handling ke liye provider pricing/terms padhein. Credentials model context mein programmatically add nahi hote. Khud messages mein keys paste na karein.

Chat current browser session mein rehti hai, permanent database mein nahi. Refresh/reconnect se reset ho sakti hai. Model ko recent 6 complete exchanges plus current question tak ka context milta hai. Response complete hone par display hota hai; token streaming nahi hai. Tool-call model content aur signatures same turn mein preserve hote hain; older turns ka plain-text context retain hota hai.

## Errors ka solution

- Key missing: filename `secrets.toml` ho, `.txt` nahi. App folder se launch karein.
- 400/401/403: key validity, model, restrictions aur account eligibility check karein.
- 404: model ID available nahi; secrets mein valid ID set karein.
- 429: free quota/rate limit; wait karke retry ya account limits check karein.
- Google toggle disabled: optional Google key aur PSE ID dono required hain.
- Google failure: existing customer eligibility, API activation, quota/restrictions check karein.
- Timeout: internet/service status check karke Retry karein. Retry duplicate user message nahi banata.

## Tests

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

7 mocked tests pass: chat, search round trip/signatures, search budget, sanitized HTTP errors, blocked response, missing key, retry/reset. Real paid/free API requests tests mein nahi chalte. Live API verification apni private nayi key configure karne ke baad karein.
