# oauth.py

import urllib.parse

TWITCH_CLIENT_ID = 'TWITCH_CLIENT_ID'
REDIRECT_URI = 'TU_URL_DE_REDIRECCION_OAUTH'
SCOPES = ['user:read:email']

AUTH_URL = 'https://id.twitch.tv/oauth2/authorize?' + urllib.parse.urlencode({
    'client_id': TWITCH_CLIENT_ID,
    'redirect_uri': REDIRECT_URI,
    'response_type': 'token',
    'scope': ' '.join(SCOPES)
})
