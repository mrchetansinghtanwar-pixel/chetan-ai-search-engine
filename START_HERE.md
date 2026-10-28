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
- app.py: Public app entry point; login required nahi hai.
- user_page.py: Orb design, Chat, automatic language aur tools.
- auth.py: Purana authentication code; app mein use nahi hota.
- pages/admin.py: Retired Admin Panel; account data nahi dikhata.
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

## Access
Login, Sign up aur Admin user management hata diye gaye hain. App seedha khulta hai.
Purana private database disk par preserved hai, app use nahi karta.

## Word / Excel to PDF
PDF tools includes Word to PDF (.docx) and Excel to PDF (.xlsx). Install LibreOffice on the app server. On Windows: `winget install --id TheDocumentFoundation.LibreOffice --exact`. On Debian/Ubuntu install `libreoffice-writer` and `libreoffice-calc`. Maximum upload 20 MB. Legacy DOC/XLS and macro-enabled formats are not supported. Excel print settings control pagination. Review complex layouts and fonts after export.

## Separate Gemini keys
Set GEMINI_CHAT_API_KEY, GEMINI_VOICE_API_KEY and GEMINI_IMAGE_API_KEY in local or Streamlit Cloud secrets. Each blank key falls back to GEMINI_API_KEY. GEMINI_VOICE_MODEL is optional and falls back to GEMINI_MODEL. Cloudflare uses its existing token. Multiple keys in one Google project do not increase its quota. Never commit actual keys.
