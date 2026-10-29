"""Bounded SSE streaming; credentials travel in headers to fixed API hosts."""
import json
import re
import time
import requests
from agent import GeminiError
from api_errors import error_message


def stream_chat(provider, key, model, history, language, temperature, max_tokens, on_text):
    if provider not in {'Gemini', 'OpenAI'} or not key.strip():
        raise GeminiError('Select a supported provider and enter its API key.')
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,120}', model):
        raise GeminiError('Select a valid model ID.')
    recent = [{'role': m['role'], 'content': m['content']} for m in history[-13:]]
    while recent and recent[0]['role'] != 'user':
        recent.pop(0)
    instruction = f'You are Chetan AI. Reply in {language}. Use Markdown and fenced code blocks. You have no web search in this request; never pretend to have searched.'
    limit = max(50, min(8192, int(max_tokens)))
    if provider == 'Gemini':
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse'
        headers = {'x-goog-api-key': key}
        payload = {'systemInstruction': {'parts': [{'text': instruction}]},
                   'contents': [{'role': 'model' if m['role'] == 'assistant' else 'user', 'parts': [{'text': m['content']}]} for m in recent],
                   'generationConfig': {'temperature': temperature, 'maxOutputTokens': limit}}
    else:
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {'Authorization': 'Bearer ' + key}
        payload = {'model': model, 'messages': [{'role': 'system', 'content': instruction}] + recent,
                   'max_completion_tokens': limit, 'stream': True, 'store': False}
        if model.startswith(('gpt-4.1', 'gpt-4o')):
            payload['temperature'] = temperature
    text, finish, started = '', None, time.monotonic()
    try:
        with requests.post(url, headers=headers, json=payload, timeout=(10, 60), stream=True, allow_redirects=False) as response:
            if response.status_code != 200:
                raise GeminiError(error_message(provider, response))
            event = []
            def consume(lines):
                nonlocal text, finish
                raw = '\n'.join(lines)
                if raw == '[DONE]':
                    return
                data = json.loads(raw)
                if 'error' in data:
                    raise GeminiError(f'{provider}: The response was interrupted. Please retry.')
                if provider == 'Gemini':
                    candidates = data.get('candidates') or [{}]
                    candidate = candidates[0]
                    delta = ''.join(p.get('text', '') for p in candidate.get('content', {}).get('parts', []) if not p.get('thought'))
                    finish = candidate.get('finishReason') or finish
                else:
                    choices = data.get('choices') or [{}]
                    delta = (choices[0].get('delta') or {}).get('content') or ''
                    finish = choices[0].get('finish_reason') or finish
                if not isinstance(delta, str):
                    raise ValueError
                text += delta
                if len(text) > 100000 or time.monotonic() - started > 180:
                    raise GeminiError('Response limit reached. Try a shorter question.')
                if delta:
                    on_text(text)
            for line in response.iter_lines(chunk_size=1024):
                line = line.decode('utf-8') if isinstance(line, bytes) else line
                if not line:
                    if event:
                        consume(event)
                        event = []
                elif line.startswith('data:'):
                    event.append(line[5:].lstrip())
            if event:
                consume(event)
        if not text.strip():
            raise GeminiError('No response text returned. Try another model or increase the token limit.')
        if not finish:
            raise GeminiError('Connection ended before the answer completed. Please retry.')
        warnings = ['Output limit reached; the response may be incomplete.'] if finish in {'length', 'MAX_TOKENS'} else []
        return {'content': text, 'sources': [], 'warnings': warnings}
    except requests.Timeout:
        raise GeminiError(f'{provider}: Request timed out. Please retry.') from None
    except requests.RequestException:
        raise GeminiError(f'{provider}: Network connection failed or stream interrupted.') from None
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise GeminiError(f'{provider}: Invalid streaming response. Please retry.') from None
