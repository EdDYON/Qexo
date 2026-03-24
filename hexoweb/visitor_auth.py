import json
import logging
import os
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse

import requests
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

QQ_AUTHORIZE_URL = 'https://graph.qq.com/oauth2.0/authorize'
QQ_ACCESS_TOKEN_URL = 'https://graph.qq.com/oauth2.0/token'
QQ_OPEN_ID_URL = 'https://graph.qq.com/oauth2.0/me'
QQ_USER_INFO_URL = 'https://graph.qq.com/user/get_user_info'

VISITOR_COOKIE_NAME = os.environ.get('VISITOR_AUTH_COOKIE_NAME', 'qexo_visitor_auth')
VISITOR_COOKIE_MAX_AGE = int(os.environ.get('VISITOR_AUTH_COOKIE_MAX_AGE', '2592000'))
VISITOR_COOKIE_SAMESITE = os.environ.get('VISITOR_AUTH_COOKIE_SAMESITE', 'None')
VISITOR_COOKIE_SECURE = os.environ.get('VISITOR_AUTH_COOKIE_SECURE', 'true').lower() == 'true'
VISITOR_COOKIE_DOMAIN = os.environ.get('VISITOR_AUTH_COOKIE_DOMAIN') or None
VISITOR_COOKIE_PATH = os.environ.get('VISITOR_AUTH_COOKIE_PATH', '/')


def _json_error(message: str, status_code: int = 400):
    return JsonResponse({'status': False, 'error': message}, status=status_code)



def _get_required_env(name: str) -> str:
    value = os.environ.get(name, '').strip()
    if not value:
        raise ValueError(f'Missing environment variable: {name}')
    return value



def _build_callback_url(request) -> str:
    configured = os.environ.get('QQ_REDIRECT_URI', '').strip()
    if configured:
        return configured
    return request.build_absolute_uri('/auth/qq/callback/')



def _sanitize_return_to(value: str, fallback: str) -> str:
    if not value:
        return fallback

    parsed = urlparse(value)
    if parsed.scheme in {'http', 'https'}:
        return value

    if value.startswith('/'):
        return value

    return fallback



def _build_result_url(target: str, status: str, reason: str | None = None) -> str:
    separator = '&' if '?' in target else '?'
    suffix = f'visitor_login={status}'
    if reason:
        suffix += f'&reason={reason}'
    return f'{target}{separator}{suffix}'



def _get_login_success_url() -> str:
    return os.environ.get('VISITOR_LOGIN_SUCCESS_URL', '/').strip() or '/'



def _load_access_token(payload: str) -> str:
    body = payload.strip()
    if body.startswith('callback('):
        raise ValueError(body)

    params = dict(item.split('=', 1) for item in body.split('&') if '=' in item)
    token = params.get('access_token')
    if not token:
        raise ValueError(body)
    return token



def _get_qq_user_profile(access_token: str) -> dict:
    app_id = _get_required_env('QQ_APP_ID')

    openid_response = requests.get(
        QQ_OPEN_ID_URL,
        params={'access_token': access_token, 'fmt': 'json'},
        timeout=10,
    )
    openid_response.raise_for_status()
    openid_data = openid_response.json()
    openid = openid_data.get('openid')
    if not openid:
        raise ValueError('QQ did not return openid')

    user_response = requests.get(
        QQ_USER_INFO_URL,
        params={
            'access_token': access_token,
            'oauth_consumer_key': app_id,
            'openid': openid,
            'fmt': 'json',
        },
        timeout=10,
    )
    user_response.raise_for_status()
    user_data = user_response.json()
    if user_data.get('ret') != 0:
        raise ValueError(user_data.get('msg') or 'QQ user info request failed')

    return {
        'provider': 'qq',
        'openid': openid,
        'nickname': user_data.get('nickname') or 'QQ 用户',
        'avatar': user_data.get('figureurl_qq_2') or user_data.get('figureurl_qq_1') or user_data.get('figureurl_2') or '',
        'gender': user_data.get('gender') or '',
        'province': user_data.get('province') or '',
        'city': user_data.get('city') or '',
        'year': user_data.get('year') or '',
        'login_at': datetime.now(timezone.utc).isoformat(),
    }



def qq_login_start(request):
    try:
        app_id = _get_required_env('QQ_APP_ID')
        callback_url = _build_callback_url(request)
    except ValueError as exc:
        logging.error(repr(exc))
        return _json_error(str(exc), 500)

    default_return_to = _get_login_success_url()
    return_to = _sanitize_return_to(request.GET.get('return_to', ''), default_return_to)
    state = os.urandom(16).hex()

    request.session['visitor_qq_state'] = state
    request.session['visitor_qq_return_to'] = return_to

    params = urlencode({
        'response_type': 'code',
        'client_id': app_id,
        'redirect_uri': callback_url,
        'state': state,
        'scope': 'get_user_info',
    })
    return redirect(f'{QQ_AUTHORIZE_URL}?{params}')



def qq_login_callback(request):
    default_return_to = _get_login_success_url()
    return_to = _sanitize_return_to(
        request.session.pop('visitor_qq_return_to', ''),
        default_return_to,
    )

    code = request.GET.get('code', '').strip()
    state = request.GET.get('state', '').strip()
    session_state = request.session.pop('visitor_qq_state', '')

    if not code or not state or state != session_state:
        return redirect(_build_result_url(return_to, 'failed', 'state'))

    try:
        token_response = requests.get(
            QQ_ACCESS_TOKEN_URL,
            params={
                'grant_type': 'authorization_code',
                'client_id': _get_required_env('QQ_APP_ID'),
                'client_secret': _get_required_env('QQ_APP_KEY'),
                'code': code,
                'redirect_uri': _build_callback_url(request),
                'fmt': 'json',
            },
            timeout=10,
        )
        token_response.raise_for_status()

        token_data = token_response.json() if 'application/json' in token_response.headers.get('Content-Type', '') else {}
        access_token = token_data.get('access_token') if token_data else _load_access_token(token_response.text)
        profile = _get_qq_user_profile(access_token)
    except Exception as exc:
        logging.error('QQ login failed: %s', repr(exc))
        return redirect(_build_result_url(return_to, 'failed', 'oauth'))

    response = redirect(_build_result_url(return_to, 'success'))
    response.set_signed_cookie(
        VISITOR_COOKIE_NAME,
        json.dumps(profile, ensure_ascii=False),
        salt='visitor-auth',
        max_age=VISITOR_COOKIE_MAX_AGE,
        secure=VISITOR_COOKIE_SECURE,
        httponly=True,
        samesite=VISITOR_COOKIE_SAMESITE,
        domain=VISITOR_COOKIE_DOMAIN,
        path=VISITOR_COOKIE_PATH,
    )
    return response



def visitor_me(request):
    try:
        payload = request.get_signed_cookie(VISITOR_COOKIE_NAME, salt='visitor-auth')
    except Exception:
        return JsonResponse({'status': True, 'authenticated': False, 'user': None})

    try:
        user = json.loads(payload)
    except json.JSONDecodeError:
        return JsonResponse({'status': True, 'authenticated': False, 'user': None})

    return JsonResponse({'status': True, 'authenticated': True, 'user': user})



@csrf_exempt
def visitor_logout(request):
    response = JsonResponse({'status': True, 'authenticated': False})
    response.delete_cookie(
        VISITOR_COOKIE_NAME,
        domain=VISITOR_COOKIE_DOMAIN,
        path=VISITOR_COOKIE_PATH,
        samesite=VISITOR_COOKIE_SAMESITE,
    )
    return response
