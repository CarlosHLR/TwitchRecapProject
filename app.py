from flask import Flask

app = Flask(__name__)

@app.route('/oauth/callback')
def oauth_callback():
    # Aquí manejarías el código de autorización de OAuth y el intercambio de tokens
    return 'Redireccionamiento OAuth completado con éxito'

if __name__ == '__main__':
    app.run(port=8080)
