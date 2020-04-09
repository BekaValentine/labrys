import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet
import datetime
from flask import *
import html
import nacl.encoding
import nacl.signing
import os
import random
import re
import requests
import sys
from tinydb import TinyDB, Query

# Labrys imports
from src.auth import *
from src.blade_identity import *
import src.passwords as passwords
import src.permissions as permissions
from src.timeline import *
from src.viewarguments import *

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
PERMISSIONS_GROUPS_DB = TinyDB(os.path.join(PERMISSIONS_DIR, 'groups.json'))
PERMISSIONS_BLADES_DB = TinyDB(os.path.join(PERMISSIONS_DIR, 'blades.json'))

INBOX_DB = TinyDB(os.path.join(DATA_DIR, 'inbox.json'))

OUTBOX_DB = TinyDB(os.path.join(DATA_DIR, 'outbox.json'))

FEED_DB = TinyDB(os.path.join(DATA_DIR, 'feed.json'))

SUBSCRIPTIONS_DB = TinyDB(os.path.join(DATA_DIR, 'subscriptions.json'))

TIMELINE_CACHE_DB = TinyDB(os.path.join(DATA_DIR, 'timeline_cache.json'))

KNOWN_BLADES_DB = TinyDB(os.path.join(DATA_DIR, 'known_blades.json'))
KNOWN_BLADES_AVATARS_DIR = os.path.join(DATA_DIR, 'known_blades_avatars')


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
@query_params(SignMessage)
def identity_sign(message):
    with open(PRIVATE_SIGNING_KEY_FILE, 'r') as f:
        signing_key = nacl.signing.SigningKey(f.read().encode(
            encoding='ascii'), encoder=nacl.encoding.Base64Encoder)
        signed = signing_key.sign(message.encode(encoding='ascii'))
        return base64.b64encode(signed.signature)


# The identity/deauthenticate endpoint provides a means for the blade owner to
# log out of the blade.
@app.route('/identity/deauthenticate', methods=['GET'])
def identity_deauthenticate():
    session.pop('authenticated', None)
    return redirect('/')


# The identity/authenticate endpoint provides a means for the blade owner to
# identify themselves to the blade.
@app.route('/identity/authenticate', methods=['POST'])
@request_body(Password)
def identity_authenticate_post(submitted_password):
    print(submitted_password)
    with open(PASSWORD_HASH_FILE, 'r') as f:
        password_hash = f.read().strip()

    if not passwords.check_password(submitted_password, password_hash):
        return 'unauthorized', 401

    session['authenticated'] = 'authenticated'

    return redirect('#')


# The /inbox endpoint is where incoming private message notifications go.
@app.route('/inbox', methods=['GET'])
@require_authentication
def inbox_get():
    return json.dumps(INBOX_DB.all()), 200


@app.route('/inbox', methods=['POST'])
@request_body(InboxMessage)
def inbox_post(sender_info):

    resp_data = dh_sessions.encrypted_client_request(
        PRIVATE_SIGNING_KEY_FILE,
        PUBLIC_SIGNING_KEY_FILE,
        sender_info['public_signing_key'],
        requests.get,
        sender_info['url'] + '/outbox')

    if resp_data:
        received_messages = json.loads(resp_data)

        for msg in received_messages:
            if not INBOX_DB.search(Query().origin_id == msg['id']):
                INBOX_DB.insert({
                    'id': ''.join([random.choice('0123456789abcdef')
                                   for i in range(30)]),
                    'origin_id': msg['id'],
                    'sender': sender_info['public_signing_key'],
                    'sent_datetime': msg['sent_datetime'],
                    'type': msg['type'],
                    'content': msg['content']
                })

    return 'ok', 200


@app.route('/inbox/<message_id>', methods=['DELETE'])
@require_authentication
def inbox_delete(message_id):

    INBOX_DB.remove(Query().id == message_id)

    return 'ok', 200


# The /outbox endpoint is where incoming private message notifications go.
@app.route('/outbox', methods=['GET'])
@many_header_params(BladeAuthorization)
def outbox_get(authorization):

    if authorization is None:
        return 'unauthorized', 401

    messages = []
    for msg in OUTBOX_DB.all():
        if msg['receiver_public_signing_key'] == authorization['public_signing_key']:

            messages += [msg]

    encrypted_messages = dh_sessions.encrypt_server_response(
        PRIVATE_SIGNING_KEY_FILE,
        PUBLIC_SIGNING_KEY_FILE,
        authorization,
        json.dumps(messages))

    return json.dumps(encrypted_messages), 200


@app.route('/outbox', methods=['POST'])
@require_authentication
@request_body(OutboxMessage)
def outbox_post(message):
    message_id = ''.join([random.choice('0123456789abcdef')
                          for i in range(30)])

    message['id'] = message_id
    message['sent_datetime'] = datetime.datetime.utcnow().isoformat()

    OUTBOX_DB.insert(message)

    with open(PUBLIC_SIGNING_KEY_FILE, 'r') as f:
        public_signing_key = f.read().strip()

    resp = requests.post(message['receiver_url'] + '/inbox',
                         data=json.dumps({
                             'url': BLADE_URL,
                             'public_signing_key': public_signing_key
                         }))

    return 'ok', 200


@app.route('/outbox/<message_id>', methods=['DELETE'])
@require_authentication
def outbox_delete(message_id):

    OUTBOX_DB.remove(Query().id == message_id)

    return 'ok', 200


# The /feed endpoint provides the public broadcast messages from this blade.
@app.route('/feed', methods=['GET'])
@many_query_params(FeedOptions)
@many_header_params(BladeAuthorization)
def feed_get(authorization, last_seen):

    if last_seen:
        found = FEED_DB.search(Query().id == last_seen)
        if found:
            messages = FEED_DB.search((Query().publish_datetime >= found[0]['publish_datetime']) &
                                      (Query().id != last_seen))
        else:
            messages = FEED_DB.all()
    else:
        messages = FEED_DB.all()

    if authorization:
        messages = [msg for msg in messages if permissions.permitted_to_view_message(
            PERMISSIONS_GROUPS_DB, PERMISSIONS_BLADES_DB, authorization['public_signing_key'], msg['permissions_categories'])]

        for msg in messages:
            msg.pop('permissions_categories', None)

        encrypted_message = dh_sessions.encrypt_server_response(
            PRIVATE_SIGNING_KEY_FILE,
            PUBLIC_SIGNING_KEY_FILE,
            authorization,
            json.dumps(messages))

        return json.dumps(encrypted_message), 200

    else:

        messages = [msg for msg in messages if permissions.permitted_to_view_message(
            PERMISSIONS_GROUPS_DB, PERMISSIONS_BLADES_DB, None, msg['permissions_categories'])]

        for msg in messages:
            msg.pop('permissions_categories', None)

        return json.dumps({'messages': messages}), 200


@app.route('/feed', methods=['POST'])
@require_authentication
@request_body(FeedMessage)
def feed_post(message):
    message['id'] = ''.join([random.choice('0123456789abcdef')
                             for i in range(30)])
    message['publish_datetime'] = datetime.datetime.utcnow().isoformat()

    FEED_DB.insert(message)

    return 'ok', 200


@app.route('/feed/<message_id>', methods=['DELETE'])
@require_authentication
def feed_id_delete(message_id):
    FEED_DB.remove(Query().id == message_id)

    return 'ok', 200


@app.route('/subscriptions', methods=['GET'])
@require_authentication
def subscriptions_get():

    subs = SUBSCRIPTIONS_DB.all()

    for sub in subs:
        blade_identity = cached_blade_identity(
            KNOWN_BLADES_DB, sub['public_signing_key'])

        sub['display_name'] = blade_identity['display_name']
        sub['bio'] = blade_identity['bio']

    return json.dumps(subs)


@app.route('/subscriptions', methods=['POST'])
@require_authentication
@request_body(Subscription)
def subscriptions_post(blade_url):

    blade_identity = load_and_cache_blade_identity(
        KNOWN_BLADES_AVATARS_DIR, KNOWN_BLADES_DB, blade_url)

    if not SUBSCRIPTIONS_DB.search(Query().public_signing_key == blade_identity['public_signing_key']):

        SUBSCRIPTIONS_DB.insert({
            'id': encode_public_key(blade_identity['public_signing_key']),
            'url': blade_url,
            'public_signing_key': blade_identity['public_signing_key'],
            'last_seen': None
        })

    return 'ok', 200


@app.route('/subscriptions/<sub_id>', methods=['DELETE'])
@require_authentication
def subscription_delete(sub_id):

    public_signing_key = decode_public_key(sub_id)

    SUBSCRIPTIONS_DB.remove(Query().public_signing_key == public_signing_key)

    return 'ok', 200


@app.route('/permissions/groups', methods=['GET'])
@require_authentication
def permissions_groups_get():

    summaries = []

    for grp in PERMISSIONS_GROUPS_DB.all():
        summaries += [{
            'id': grp['id'],
            'name': grp['name'],
            'description': grp['description'],
            'member_count': len(grp['members'])
        }]

    return json.dumps(summaries)


@app.route('/permissions/groups', methods=['POST'])
@require_authentication
@request_body(PermissionsGroup)
def permissions_groups_post(grp):

    group_id = ''.join([random.choice('0123456789abcdef')
                        for i in range(30)])

    grp['id'] = group_id

    PERMISSIONS_GROUPS_DB.insert(grp)

    return 'ok', 200


@app.route('/permissions/groups/<group_id>', methods=['GET'])
@require_authentication
def permissions_groups_id_get(group_id):

    found = PERMISSIONS_GROUPS_DB.search(Query().id == group_id)

    if found:
        return json.dumps(found[0]), 200

    else:
        return 'not found', 404


@app.route('/permissions/groups/<group_id>', methods=['PUT'])
@require_authentication
@request_body(PermissionsGroup)
def permissions_groups_id_put(grp, group_id):

    if PERMISSIONS_GROUPS_DB.search(Query().id == group_id):
        PERMISSIONS_GROUPS_DB.update(grp, Query().id == group_id)

        return 'ok', 200

    else:

        return 'not found', 404


@app.route('/permissions/groups/<group_id>', methods=['DELETE'])
@require_authentication
def permissions_groups_id_delete(group_id):

    PERMISSIONS_GROUPS_DB.remove(Query().id == group_id)

    return 'ok', 200


@app.route('/permissions/blades', methods=['GET'])
@require_authentication
def permissions_blades_get():

    permissions_blades = PERMISSIONS_BLADES_DB.all()

    for perm_blade in permissions_blades:
        perm_blade['id'] = encode_public_key(perm_blade['public_signing_key'])

    return json.dumps(blades)


@app.route('/permissions/blades/<blade_id>', methods=['GET'])
@require_authentication
def permissions_blades_id_get(blade_id):

    public_signing_key = decode_public_key(blade_id)

    found = PERMISSIONS_BLADES_DB.search(
        Query().public_signing_key == public_signing_key)

    if found:
        return json.dumps(found[0]['permissions']), 200

    else:
        return 'not found', 404


@app.route('/permissions/blades/<blade_id>', methods=['PUT'])
@require_authentication
@request_body(PermissionsBlade)
def permissions_blades_id_put(perms, blade_id):

    public_signing_key = decode_public_key(blade_id)

    if PERMISSIONS_BLADES_DB.search(Query().public_signing_key == public_signing_key):
        PERMISSIONS_BLADES_DB.update(
            {'permissions': perms}, Query().public_signing_key == public_signing_key)

    else:
        PERMISSIONS_BLADES_DB.insert({
            'public_signing_key': public_signing_key,
            'permissions': perms
        })

    return 'ok', 200


@app.route('/permissions/blades/<blade_id>', methods=['DELETE'])
@require_authentication
def permissions_blades_id_delete(blade_id):

    public_signing_key = decode_public_key(blade_id)

    PERMISSIONS_BLADES_DB.remove(
        Query().public_signing_key == public_signing_key)

    return 'ok', 200


# The /timeline endpoint provides the current timeline for this blade.
@app.route('/timeline', methods=['GET'])
@require_authentication
def timeline_get():

    new_messages = update_subscriptions(
        PRIVATE_SIGNING_KEY_FILE, PUBLIC_SIGNING_KEY_FILE, SUBSCRIPTIONS_DB, TIMELINE_CACHE_DB)

    return json.dumps(new_messages), 200


if __name__ == '__main__':
    if '--port' in sys.argv:
        port = int(sys.argv[sys.argv.index('--port') + 1])
    else:
        port = 1337

    if '--url' in sys.argv:
        BLADE_URL = sys.argv[sys.argv.index('--url') + 1]

    app.run(port=port, debug=True)
