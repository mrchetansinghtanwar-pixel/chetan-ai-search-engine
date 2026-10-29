"""Map provider failures to fixed messages; never display raw response bodies."""
def error_message(provider, response):
    try:
        data = response.json()
        error = data.get('error', {}) if isinstance(data, dict) else {}
        # Examine only for classification; never interpolate provider strings.
        details = str(error).lower()[:20000]
    except (ValueError, TypeError):
        details = ''
    status = response.status_code
    if any(marker in details for marker in ('api_key_invalid', 'invalid_api_key', 'api key not valid')):
        return f'{provider}: Invalid API key. Replace it in Settings.'
    if any(marker in details for marker in ('insufficient_quota', 'billing_hard_limit', 'credit balance', 'limit: 0')) or status == 402:
        return f'{provider}: Credits or quota exhausted. Check your own provider billing and quota.'
    reasons = {
        400: 'Invalid request. Check the model and supported settings.',
        401: 'Unauthorized (401). Check or replace your API key.',
        403: 'Access forbidden (403). Check key permissions, region and model access.',
        404: 'Model unavailable (404). Refresh the model list or choose another model.',
        429: 'Rate limit reached (429). Wait before retrying; check your provider quota.',
    }
    return f'{provider}: ' + reasons.get(status, 'Service temporarily unavailable. Please try again later.')
