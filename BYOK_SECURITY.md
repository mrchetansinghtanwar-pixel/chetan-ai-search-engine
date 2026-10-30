# Chetan AI BYOK operation and limits

The existing entry point is `app.py`, which runs `user_page.py`. There is no
`project.py` in this repository. No replacement website or registration system was added.

## Credentials and billing

Each visitor supplies their own selected provider's key through a password widget.
Chat has no owner-key, environment-variable or secrets-file fallback. The visitor's
provider bills their account and applies its quotas; a subscription to a provider's
consumer chat product does not necessarily include API credits. Other AI tools retain
their separate session key inputs. The app does not persist entered keys to disk,
databases, browser local storage or cookies. It does not log request bodies, headers,
raw provider exceptions or response error bodies. Credentials are not cached or sent
to analytics. No LangSmith tracing is enabled. Streamlit usage telemetry is disabled.

Password widgets only mask the display. Their values exist in the browser's active
widget and Streamlit's per-session server memory, and in temporary HTTP request
objects. This design deliberately avoids a second credential vault or global cache.
Disconnect resets all explicit credential widgets, clears chat/PDF/voice state and
verification metadata. A 30-minute inactivity check clears credentials at the next
interaction; it is not a background memory wipe. Closing a tab does not guarantee
immediate server cleanup. Python strings, framework internals, network buffers and
hosting infrastructure may retain copies until reclaimed. We cannot promise secure
zeroization or protection against a compromised host, administrator or browser.

Sessions use independent Streamlit state. No application global or shared cache
contains user keys; automated tests exercise two independent sessions and disconnect.
Do not add debug state dumps, request tracing, global clients holding credentials,
or telemetry that captures forms. Known current keys are redacted from normal chat
text before storing/sending it; this is defense in depth, not a universal secret detector.
Do not paste secrets in chat, uploaded PDFs, image prompts or other content fields.

## Network and deployment

Gemini and OpenAI credentials are sent only as HTTPS headers to fixed provider hosts.
Streaming requests disable redirects and use connection/read timeouts. Google Search
uses its key header rather than a key URL parameter. Never enable HTTP wire logging.
Deploy only on the trusted HTTPS Streamlit Community Cloud URL or behind a properly
configured TLS proxy. Localhost HTTP is for local development. Keep XSRF protection
and CORS defaults enabled. No application can guarantee that hosting infrastructure
never records traffic; review hosting and provider policies before using sensitive keys.

`.streamlit/secrets.toml`, `.env*` and `private/` remain ignored by Git. Never put real
keys in the example secrets file or requirements. Previously disclosed credentials
must be revoked at their provider; adding gitignore does not remove historical leaks.
The owner still pays any hosting costs and independently configured services.

## Chat behavior

New sessions default to Auto detect. Detection uses local prefix hints for AIza
(Gemini), sk-proj-/sk-svcacct- (OpenAI), gsk_ (Groq), and sk-ant- (Claude).
These are format hints, not guaranteed or authenticated provider identities.
Generic sk- keys, proxy credentials, and unknown formats require explicit manual
provider selection. The app never tries a key against multiple services. Detection
does not make network requests. A detected key still needs provider access and quota.
The auto-entry widget is session-local and cleared by Disconnect like manual keys.
Image, voice and search credentials remain separate; no automatic key reuse was added.

The sidebar includes provider/model selection, session key status, Check API connection,
Refresh model list, Clear Chat, Disconnect and response controls. A successful model
listing confirms accepted credentials, not funded generation access. Live model lists
are account-dependent; model availability can change. Custom IDs must be supported by
the selected API. Existing additional providers and all PDF/image/voice tools remain.

Gemini and OpenAI stream ordinary chat. Google Search agents retain their bounded
tool-call flow and return completed responses; other providers and PDF answers use
the existing non-streaming flow. Stream errors remove the partial output and offer
manual retry, without automatically issuing another billable generation. Context is
bounded to the recent turns and session history to 40 messages. Copy response expands
a native Streamlit code block with its clipboard button; Markdown/code in the normal
answer remains formatted. A 100-token default may truncate answers, including model
reasoning; increase the configured limit if necessary.

API errors are classified into invalid keys, 401, 403, model unavailable, rate limits,
explicit exhausted credits/quota, network failures and timeouts. Generic 429 errors
cannot always distinguish a short-term limit from quota exhaustion; no raw provider
error is displayed. No live generation was performed with a user's private credentials
during automated tests. Mocked transport tests are not a production security audit.

Official API references:
- https://ai.google.dev/api/generate-content
- https://developers.openai.com/api/reference/resources/chat/subresources/completions/streaming-events
