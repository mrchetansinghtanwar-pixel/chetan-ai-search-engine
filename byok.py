"""Session-local credential lifecycle. No global credential store or caching."""
import time
import re

CREDENTIAL_PREFIXES = ('chat_key_', 'credential_')

def disconnect(state):
    for name in list(state):
        if name.startswith(CREDENTIAL_PREFIXES):
            state[name] = ''
        elif name.startswith(('models_', 'verified_', 'qa_', 'speech_', 'public_search_')):
            del state[name]
    state['messages'] = []
    state['last_error'] = ''
    state.pop('credential_activity', None)

def expire_credentials(state, now=None):
    now = time.monotonic() if now is None else now
    last = state.get('credential_activity')
    if last is not None and now - last >= 1800:
        disconnect(state)
        return True
    state['credential_activity'] = now
    return False

def redact(text, state):
    for name in state:
        value = state[name]
        if name.startswith(CREDENTIAL_PREFIXES) and isinstance(value, str) and value:
            text = text.replace(value, '[credential removed]')
    return re.sub(r'(?:sk-(?:proj-)?[A-Za-z0-9_-]{16,}|AIza[A-Za-z0-9_-]{20,})', '[credential removed]', text)
