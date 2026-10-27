# Chetan AI - latest complete project

## Run in VS Code terminal

```powershell
cd E:\chetan-ai-search-engine
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8502
```

Browser: http://localhost:8502/
Agar app already chal raha hai, naya server launch karne ke bajaye browser refresh karein.

## Code files
- app.py: Users aur Admin pages ki navigation.
- user_page.py: Orb design, Chat, automatic language aur tools.
- auth.py: Sign up/Login aur admin access.
- pages/admin.py: Alag Admin Panel; users enable/disable.
- agent.py: Gemini chat and optional Google Search.
- image_service.py: Cloudflare FLUX and Gemini image generation.
- utilities.py: Hindi/English text-to-speech, PDF conversion, text pad, calculator.
- .streamlit/config.toml: theme.
- .streamlit/secrets.toml: your existing private credentials; do not share or commit.

Google Search optional hai. Image services ke quotas alag hain.
PDF export English/Roman Hinglish supports karta hai; scanned PDF OCR included nahi hai.
Voice text Google speech service ko bheja jaata hai.

## Private data
`.streamlit/secrets.toml` aur `private/` GitHub par upload nahi hote.
Users ka SQLite database local `private/users.sqlite3` mein hai.
Naye server par accounts/admin apne aap transfer nahi honge.
GitHub par code upload karna app ko online deploy karna nahi hai.
