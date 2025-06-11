import os
import requests
import sqlite3
from flask import Flask, redirect, session, request, g
from datetime import datetime, timedelta
import urllib.parse

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Función para conectar a la base de datos SQLite
def conectar_db():
    return sqlite3.connect('clips.db')

# Función para obtener una conexión de la base de datos
def obtener_db():
    if 'db' not in g:
        g.db = conectar_db()
    return g.db

# Función para verificar y crear la tabla 'clips' si no existe
def verificar_tabla_clips():
    db = obtener_db()
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS clips (
                        id INTEGER PRIMARY KEY,
                        url TEXT NOT NULL
                        )''')
    db.commit()

@app.teardown_appcontext
def cerrar_db(error):
    if hasattr(g, 'db'):
        g.db.close()

TWITCH_CLIENT_ID = 'no9t3r7nrqj8mzdl8ipdi0hs3x8xn5'
TWITCH_CLIENT_SECRET = 'sxcorhhfsk59w85uwfdy05rjkn48ta'
REDIRECT_URI = 'https://d482-187-251-110-141.ngrok-free.app/redireccion_oauth'

# URL de autorización de Twitch
AUTH_URL = 'https://id.twitch.tv/oauth2/authorize?' + urllib.parse.urlencode({
    'client_id': TWITCH_CLIENT_ID,
    'redirect_uri': REDIRECT_URI,
    'response_type': 'code',
    'scope': 'user:read:email'  # Alcances que tu aplicación necesita
})

@app.route('/iniciar_sesion_con_twitch')
def iniciar_sesion_con_twitch():
    return redirect(AUTH_URL)

@app.route('/redireccion_oauth')
def redireccion_oauth():
    # Manejar la respuesta de autorización de Twitch
    if 'error' in request.args:
        return 'Hubo un error durante la autorización: {}'.format(request.args['error'])
    elif 'code' in request.args:
        # Guardar el código de autorización en la sesión para utilizarlo más tarde
        session['code'] = request.args['code']
        return redirect('/obtener_token_de_acceso')
    else:
        return 'Respuesta de autorización inválida'

@app.route('/obtener_token_de_acceso')
def obtener_token_de_acceso():
    
    # Intercambiar el código de autorización por un token de acceso
    if 'code' in session:
        code = session.pop('code')
        token_params = {
            'client_id': TWITCH_CLIENT_ID,
            'client_secret': TWITCH_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI
        }
        response = requests.post('https://id.twitch.tv/oauth2/token', params=token_params)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data['access_token']
            # Almacenar el token de acceso en la sesión o en una base de datos
            session['access_token'] = access_token
            return redirect('/obtener_clips')
        else:
            return 'Hubo un error al obtener el token de acceso: {}'.format(response.text)
    else:
        return 'No se encontró el código de autorización en la sesión'

@app.route('/')
def index():
    return '¡Hola, mundo!'

@app.route('/obtener_clips')
def obtener_clips():
    # Verificar y crear la tabla 'clips' al iniciar la aplicación
    verificar_tabla_clips()
    
    # Obtener la fecha actual y calcular la fecha hace 7 días
    ahora = datetime.now()
    hace_siete_dias = ahora - timedelta(days=7)
    fecha_desde = hace_siete_dias.strftime("%Y-%m-%dT%H:%M:%SZ")  # Formatear la fecha

    # URL de la API de Twitch para obtener clips
    API_URL = 'https://api.twitch.tv/helix/clips'
    
    # Parámetros de la solicitud para obtener los primeros 30 clips más populares de los últimos 7 días
    params = {
        'first': 100,
        'sort': 'views',
        'started_at': fecha_desde,
        'broadcaster_id': '135201683'  # ID del transmisor deseado
    }

    headers = {
        'Authorization': 'Bearer {}'.format(session.get('access_token')),
        'Client-ID': TWITCH_CLIENT_ID
    }
    
    # Realizar la solicitud a la API de Twitch para obtener clips públicos
    response = requests.get(API_URL, params=params, headers=headers)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        # Procesar la respuesta JSON y obtener los clips
        clips = response.json().get('data', [])
        
        # Insertar los enlaces de los clips en la base de datos SQLite
        db = obtener_db()
        for clip in clips:
            db.execute("INSERT INTO clips (url) VALUES (?)", (clip['url'],))
        
        # Confirmar los cambios en la base de datos
        db.commit()
        
        return 'Se han obtenido y almacenado correctamente {} clips'.format(len(clips))
    else:
        return 'Error al obtener los clips de Twitch: {}'.format(response.text)

if __name__ == "__main__":
    app.run(debug=True)
