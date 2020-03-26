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

DATA_DIR                 = os.path.join(app.root_path, 'data')
SESSION_SECRET_KEY_FILE  = os.path.join(DATA_DIR, 'session_secret_key.txt')
IDENTITY_DIR             = os.path.join(DATA_DIR, 'identity')
DISPLAY_NAME_FILE        = os.path.join(IDENTITY_DIR, 'display_name.txt')
BIO_FILE                 = os.path.join(IDENTITY_DIR, 'bio.txt')
PUBLIC_SIGNING_KEY_FILE  = os.path.join(IDENTITY_DIR, 'public_signing_key.txt')
PRIVATE_SIGNING_KEY_FILE = os.path.join(IDENTITY_DIR, 'private_signing_key.txt')
AUTHENTICATION_DIR       = os.path.join(DATA_DIR, 'authentication')
PASSWORD_HASH_FILE       = os.path.join(AUTHENTICATION_DIR, 'password_hash.txt')
AUTH_TOKEN_DIR           = os.path.join(AUTHENTICATION_DIR, 'auth_tokens')
AUTH_STATE_DIR           = os.path.join(AUTHENTICATION_DIR, 'auth_state')
USER_CONTENT_DIR         = os.path.join(app.root_path, 'user_content')
PERMISSIONS_DIR          = os.path.join(DATA_DIR, 'permissions')


# The Session Secret Key is used to sign cookies.
with open(SESSION_SECRET_KEY_FILE, 'r') as f:
  app.secret_key = f.read().strip()


# Blade URL
with open(os.path.join(DATA_DIR, 'blade_url.txt'), 'r') as f:
  BLADE_URL = f.read().strip()


# Admin Servers
with open(os.path.join(DATA_DIR, 'admins.txt'), 'r') as f:
  ADMIN_SERVERS = f.read().split()


# The Blade root. Doesn't do anything interesting right now.
@app.route('/', methods = ['GET'])
def labrys_home():
  return render_template('main_page.html', admin_servers=ADMIN_SERVERS)



# The identity endpoint shows information about the owner of the blade, namely
# their display name, a short bio, and their avatar if they have one.
@app.route('/identity', methods = ['GET'])
def identity():

  with open(DISPLAY_NAME_FILE, 'r') as f:
    display_name = f.read()

  with open(BIO_FILE, 'r') as f:
    bio = f.read()

  avatar = None
  avatar_candidates =\
    [ f for f in os.listdir(IDENTITY_DIR)\
        if re.search('^avatar\.(png|PNG|jpg|JPG|jpeg|JPEG|gif|GIF)$', f) ]
  if avatar_candidates:
    avatar = "/identity/" + avatar_candidates[0]

  return render_template('identity.html',
                         display_name = display_name,
                         bio = bio,
                         avatar = avatar)



# The identity/<file> endpoint serves the content of the identity directory,
# which is usually the display name, bio, and avatar.
@app.route('/identity/<path:filename>', methods = ['GET'])
def identity_file(filename):
  return send_from_directory(IDENTITY_DIR, filename)



# The identity/deauthenticate endpoint provides a means for the blade owner to
# log out of the blade.
@app.route('/identity/deauthenticate', methods = ['GET'])
def identity_deauthenticate():
  session.pop('logged_in', None)
  return redirect('/')

# The identity/authenticate endpoint provides a means for the blade owner to
# identify themselves to the blade.
@app.route('/identity/authenticate', methods = ['GET','POST'])
def identity_authenticate():
  if request.method == 'GET':

    requester = request.args.get('requester')
    state = request.args.get('state')
    return_address = request.args.get('return_address')

    if requester is None and state is None and return_address is None:

        if 'logged_in' in session:
            return render_template('already_authenticated.html')
        else:
            return render_template('identity_authenticate.html')

    elif requester is not None and state is not None and return_address is not None:
        requester_no_slash = requester if requester[-1] != '/' else requester[:-1]
        redirect_url = requester_no_slash + '/login'

        if 'logged_in' in session:
            auth_token = auth.make_auth_token(AUTH_TOKEN_DIR, requester, state)
            return redirect(redirect_url + '?auth_token=' + auth_token + '&state=' + state + '&return_address=' + return_address)
        else:
            return render_template('identity_authenticate.html',
                                   requester = requester,
                                   state = state,
                                   return_address = return_address)
    else:
      return "bad request", 400

  elif request.method == 'POST':
    submitted_password = request.form['password']

    if submitted_password:

      with open(PASSWORD_HASH_FILE, 'r') as f:
        password_hash = f.read().strip()

      if passwords.check_password(submitted_password, password_hash):
        session['logged_in'] = 'logged_in'



        if 'requester' in request.form and 'state' in request.form and 'return_address' in request.form:
            requester = html.unescape(request.form['requester'])
            state = html.unescape(request.form['state'])
            return_address = html.unescape(request.form['return_address'])
            auth_token = auth.make_auth_token(AUTH_TOKEN_DIR,
                                              requester,
                                              state)
            requester_no_slash = requester if '/' != requester[-1] else requester[:-1]
            return redirect(requester_no_slash + '/login?auth_token=' + auth_token + '&return_address=' + return_address +  '&state=' + state)
        else:
            return redirect('#')

      else:
        return 'unauthorized', 401

    else:
      return 'bad request', 400



# The identity/verify endpoint is used to confirm that an auth token is valid.
@app.route('/identity/verify', methods = ['GET'])
def identity_verify():

  auth_token = request.args.get('auth_token')
  requester = request.args.get('requester')
  state = request.args.get('state')

  if auth_token and requester and state:

    if auth.check_auth_token(AUTH_TOKEN_DIR, auth_token, requester, state):
      result = ('ok', 200)
    else:
      result = ('unauthorized, 401')

    auth.delete_auth_token(AUTH_TOKEN_DIR, auth_token)

    return result

  else:
    return 'bad request', 400



# The identity/public_signing_key endpoint is used to get the verify key
# associated with the blade.
@app.route('/identity/public_signing_key', methods = ['GET'])
def identity_public_signing_key():

  with open(PUBLIC_SIGNING_KEY_FILE, 'r') as f:
    return f.read().strip()



# The identity/sign endpoint is used to get a signed value from the blade.
@app.route('/identity/sign', methods = ['GET'])
def identity_sign():
  message = request.args.get('message')
  if message:
    with open(PRIVATE_SIGNING_KEY_FILE, 'r') as f:
      signing_key = nacl.signing.SigningKey(f.read().encode(encoding='ascii'), encoder = nacl.encoding.Base64Encoder)
      signed = signing_key.sign(message.encode(encoding='ascii'))
      return base64.b64encode(signed.signature)
  else:
    return 'bad request', 400
