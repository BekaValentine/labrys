import base64
from flask import *
import html
import nacl.encoding
import nacl.signing
import os
import re
import requests

# Labrys imports
import src.auth as auth
import src.passwords as passwords
import src.permissions as permissions

app = Flask(__name__)

DATA_DIR = os.path.join(app.root_path, 'data')

SECRETS_DIR = os.path.join(DATA_DIR, 'secrets')
SESSION_SECRET_KEY_FILE = os.path.join(SECRETS_DIR, 'session_secret_key.txt')
PRIVATE_SIGNING_KEY_FILE = os.path.join(SECRETS_DIR, 'private_signing_key.txt')
PASSWORD_HASH_FILE = os.path.join(SECRETS_DIR, 'password_hash.txt')

IDENTITY_DIR = os.path.join(DATA_DIR, 'identity')
DISPLAY_NAME_FILE = os.path.join(IDENTITY_DIR, 'display_name.txt')
BIO_FILE = os.path.join(IDENTITY_DIR, 'bio.txt')
PUBLIC_SIGNING_KEY_FILE = os.path.join(IDENTITY_DIR, 'public_signing_key.txt')

PERMISSIONS_DIR = os.path.join(DATA_DIR, 'permissions')


# The Session Secret Key is used to sign cookies.
with open(SESSION_SECRET_KEY_FILE, 'r') as f:
    app.secret_key = f.read().strip()


# Blade URL
with open(os.path.join(DATA_DIR, 'blade_url.txt'), 'r') as f:
    BLADE_URL = f.read().strip()


# The Blade root. Doesn't do anything interesting right now.
@app.route('/', methods=['GET'])
def labrys_home():
    return render_template('main_page.html')


# The identity/<file> endpoint serves the content of the identity directory,
# which is usually the display name, bio, and avatar.
@app.route('/identity/avatar', methods=['GET'])
def identity_avatar():
    avatar_candidates =\
        [f for f in os.listdir(IDENTITY_DIR)
         if re.search('^avatar\.(png|PNG|jpg|JPG|jpeg|JPEG|gif|GIF|svg|SVG)$', f)]
    if avatar_candidates:
        avatar_file_name = avatar_candidates[0]
        return send_from_directory(IDENTITY_DIR, avatar_file_name)
    else:
        return 'not found', 404


# Gets the display name
@app.route('/identity/display_name', methods=['GET'])
def identity_display_name():
    with open(DISPLAY_NAME_FILE, 'r') as f:
        return f.read()


# Gets the bio
@app.route('/identity/bio', methods=['GET'])
def identity_bio():
    with open(BIO_FILE, 'r') as f:
        return f.read()


# Gets the public signing key
@app.route('/identity/public_signing_key', methods=['GET'])
def identity_public_signing_key():
    with open(PUBLIC_SIGNING_KEY_FILE, 'r') as f:
        return f.read().strip()


# The identity/sign endpoint is used to get a signed value from the blade.
@app.route('/identity/sign', methods=['GET'])
def identity_sign():
    message = request.args.get('message')
    if message:
        with open(PRIVATE_SIGNING_KEY_FILE, 'r') as f:
            signing_key = nacl.signing.SigningKey(f.read().encode(
                encoding='ascii'), encoder=nacl.encoding.Base64Encoder)
            signed = signing_key.sign(message.encode(encoding='ascii'))
            return base64.b64encode(signed.signature)
    else:
        return 'bad request', 400


# The identity/deauthenticate endpoint provides a means for the blade owner to
# log out of the blade.
@app.route('/identity/deauthenticate', methods=['GET'])
def identity_deauthenticate():
    session.pop('authenticated', None)
    return redirect('/')


# The identity/authenticate endpoint provides a means for the blade owner to
# identify themselves to the blade.
@app.route('/identity/authenticate', methods=['GET'])
def identity_authenticate_get():
    if 'authenticated' in session:
        return render_template('already_authenticated.html')
    else:
        return render_template('identity_authenticate.html')


# The identity/authenticate endpoint provides a means for the blade owner to
# identify themselves to the blade.
@app.route('/identity/authenticate', methods=['POST'])
def identity_authenticate_post():
    submitted_password = request.form['password']

    if not submitted_password:
        return 'bad request', 400

    with open(PASSWORD_HASH_FILE, 'r') as f:
        password_hash = f.read().strip()

    if not passwords.check_password(submitted_password, password_hash):
        return 'unauthorized', 401

    session['authenticated'] = 'authenticated'

    return redirect('#')
