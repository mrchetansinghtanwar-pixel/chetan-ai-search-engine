"""Local format hints only: never probe multiple services with a credential."""
import re


def detect_provider(key):
    """Return a provider hint, not proof that a credential is valid.

    Ambiguous legacy sk- keys, proxy keys and unfamiliar formats require
    manual selection. Provider APIs remain responsible for authentication.
    """
    if not isinstance(key, str):
        return None
    key = key.strip()
    for prefix, provider in (
        ('sk-ant-', 'Claude'),
        ('sk-proj-', 'OpenAI'),
        ('sk-svcacct-', 'OpenAI'),
        ('gsk_', 'Groq'),
        ('AIza', 'Gemini'),
    ):
        if key.startswith(prefix) and re.fullmatch(r'[A-Za-z0-9_-]{16,}', key[len(prefix):]):
            return provider
    return None
